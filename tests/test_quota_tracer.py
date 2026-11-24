import csv
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent
    / ".gemini"
    / "config"
    / "scripts"
    / "quota_tracer.py"
)
spec = importlib.util.spec_from_file_location("quota_tracer", SCRIPT_PATH)
assert spec is not None and spec.loader is not None
quota_tracer = importlib.util.module_from_spec(spec)
sys.modules["quota_tracer"] = quota_tracer
spec.loader.exec_module(quota_tracer)


def _make_payload(
    *,
    email: str = "alice@example.com",
    plan_tier: str = "Google AI Ultra",
    conv_id: str = "conv-1",
    model_name: str = "Gemini 4 Neon (High)",
    effort: str = "high",
    in_tok: int = 0,
    cache_read: int = 0,
    cache_create: int = 0,
    out_tok: int = 0,
    exceeds_200k: bool = False,
    q5h: float | None = None,
    q5h_reset: str = "2026-11-22T12:00:00Z",
    qwk: float | None = None,
    qwk_reset: str = "2026-11-29T12:00:00Z",
    q3p_5h: float | None = None,
    running_subagents: int = 0,
) -> dict[str, object]:
    quota: dict[str, object] = {}
    if q5h is not None:
        quota["gemini-5h"] = {
            "remaining_fraction": q5h,
            "reset_time": q5h_reset,
            "reset_in_seconds": 3600,
        }
    if qwk is not None:
        quota["gemini-weekly"] = {
            "remaining_fraction": qwk,
            "reset_time": qwk_reset,
            "reset_in_seconds": 86400,
        }
    if q3p_5h is not None:
        quota["3p-5h"] = {
            "remaining_fraction": q3p_5h,
            "reset_time": q5h_reset,
            "reset_in_seconds": 3600,
        }
    subagents = [
        {"name": f"sub-{i}", "status": "running"} for i in range(running_subagents)
    ]
    return {
        "email": email,
        "plan_tier": plan_tier,
        "conversation_id": conv_id,
        "model": {"id": model_name, "display_name": model_name, "effort": effort},
        "exceeds_200k_tokens": exceeds_200k,
        "context_window": {
            "current_usage": {
                "input_tokens": in_tok,
                "cache_read_input_tokens": cache_read,
                "cache_creation_input_tokens": cache_create,
                "output_tokens": out_tok,
            }
        },
        "quota": quota,
        "subagents": subagents,
    }


class TestQuotaTracer(unittest.TestCase):
    def test_entry_validation_and_gemini_bucket_filtering(self) -> None:
        with self.assertRaises(ValueError):
            quota_tracer.parse_ingest_payload("not-a-dict", now_ts=100.0)
        with self.assertRaises(ValueError):
            quota_tracer.parse_ingest_payload({"conversation_id": "c1"}, now_ts=100.0)
        with self.assertRaises(ValueError):
            quota_tracer.parse_ingest_payload({"email": "a@b.com"}, now_ts=100.0)
        with self.assertRaises(ValueError):
            quota_tracer.parse_ingest_payload(
                _make_payload(in_tok=-5, q5h=0.9), now_ts=100.0
            )

        parsed = quota_tracer.parse_ingest_payload(
            _make_payload(
                model_name="Gemini 4 Neon (High)",
                in_tok=100_000,
                cache_read=50_000,
                out_tok=10_000,
                q5h=0.95,
                qwk=0.80,
                q3p_5h=0.90,
            ),
            now_ts=100.0,
        )
        self.assertEqual(parsed.model_family, "gemini")
        self.assertEqual(
            [q.bucket for q in parsed.quotas], ["gemini-5h", "gemini-weekly"]
        )
        self.assertIsNotNone(parsed.usage)
        assert parsed.usage is not None
        self.assertEqual(parsed.usage.total_tokens, 160_000)

        claude_parsed = quota_tracer.parse_ingest_payload(
            _make_payload(model_name="Claude Opus 4.6", q5h=0.95), now_ts=101.0
        )
        self.assertEqual(claude_parsed.model_family, "other")

    def test_dedup_lagged_quota_non_gemini_exclusion_and_reset_split(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db = Path(tmp_dir) / "trace.sqlite3"
            # Tick 1: initial baseline quota = 1.00
            quota_tracer.ingest_payload(
                quota_tracer.parse_ingest_payload(_make_payload(q5h=1.00), now_ts=100.0),
                db_path=db,
            )
            # Tick 2: Gemini 4 Neon step (1M input = $3.00, 1M cache = $0.15, 0.2M output = $3.00 -> $6.15), quota still 1.00 (lagged)
            step1 = _make_payload(
                in_tok=1_000_000, cache_read=1_000_000, out_tok=200_000, q5h=1.00
            )
            quota_tracer.ingest_payload(
                quota_tracer.parse_ingest_payload(step1, now_ts=110.0), db_path=db
            )
            # Tick 3: identical statusline tick must be deduplicated
            self.assertFalse(
                quota_tracer.ingest_payload(
                    quota_tracer.parse_ingest_payload(step1, now_ts=111.0), db_path=db
                )
            )
            # Tick 4: non-Gemini Claude step on same email must be excluded from Gemini USD
            quota_tracer.ingest_payload(
                quota_tracer.parse_ingest_payload(
                    _make_payload(
                        conv_id="conv-claude",
                        model_name="Claude Opus 4.6",
                        in_tok=500_000,
                        out_tok=100_000,
                        q5h=1.00,
                    ),
                    now_ts=115.0,
                ),
                db_path=db,
            )
            # Tick 5: quota drops by 1.0% (1.00 -> 0.99)
            quota_tracer.ingest_payload(
                quota_tracer.parse_ingest_payload(
                    _make_payload(
                        in_tok=1_000_000,
                        cache_read=1_000_000,
                        out_tok=200_000,
                        q5h=0.99,
                    ),
                    now_ts=120.0,
                ),
                db_path=db,
            )
            # Tick 6: quota resets upward to 1.00 in new window
            quota_tracer.ingest_payload(
                quota_tracer.parse_ingest_payload(
                    _make_payload(
                        q5h=1.00, q5h_reset="2026-11-22T17:00:00Z"
                    ),
                    now_ts=200.0,
                ),
                db_path=db,
            )
            # Tick 7: new window step + same-tick drop of 2.0% ($3.00 / 2.0% = $1.50/1%)
            quota_tracer.ingest_payload(
                quota_tracer.parse_ingest_payload(
                    _make_payload(
                        in_tok=1_000_000,
                        out_tok=0,
                        q5h=0.98,
                        q5h_reset="2026-11-22T17:00:00Z",
                    ),
                    now_ts=210.0,
                ),
                db_path=db,
            )

            intervals, windows_map = quota_tracer.build_intervals(
                db_path=db, buckets=("gemini-5h",)
            )
            self.assertEqual(len(intervals), 2)
            self.assertEqual(len(windows_map[("alice@example.com", "Google AI Ultra", "gemini-5h")]), 2)

            first, second = intervals[0], intervals[1]
            self.assertTrue(first.is_clean)
            self.assertAlmostEqual(first.delta_pct, 1.0, places=6)
            self.assertEqual(first.total_tokens, 2_200_000)
            self.assertAlmostEqual(first.cost_usd, 6.15, places=6)
            self.assertAlmostEqual(first.usd_per_pct, 6.15, places=6)

            self.assertTrue(second.is_clean)
            self.assertAlmostEqual(second.delta_pct, 2.0, places=6)
            self.assertAlmostEqual(second.cost_usd, 3.00, places=6)
            self.assertAlmostEqual(second.usd_per_pct, 1.50, places=6)

    def test_confounder_tagging_and_clean_default_filtering(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db = Path(tmp_dir) / "trace.sqlite3"
            # Baseline
            quota_tracer.ingest_payload(
                quota_tracer.parse_ingest_payload(_make_payload(q5h=1.00), now_ts=100.0),
                db_path=db,
            )
            # Interval 1 (clean): $3.00 / 1% = $3.00
            quota_tracer.ingest_payload(
                quota_tracer.parse_ingest_payload(
                    _make_payload(conv_id="c1", in_tok=1_000_000, q5h=0.99),
                    now_ts=110.0,
                ),
                db_path=db,
            )
            # Interval 2 (subagent ran mid-interval and finished before drop tick):
            quota_tracer.ingest_payload(
                quota_tracer.parse_ingest_payload(
                    _make_payload(conv_id="c1", running_subagents=1, q5h=0.99),
                    now_ts=115.0,
                ),
                db_path=db,
            )
            quota_tracer.ingest_payload(
                quota_tracer.parse_ingest_payload(
                    _make_payload(
                        conv_id="c1", in_tok=200_000, running_subagents=0, q5h=0.97
                    ),
                    now_ts=120.0,
                ),
                db_path=db,
            )
            # Interval 3 (concurrent conversations c1 + c2 on same email):
            quota_tracer.ingest_payload(
                quota_tracer.parse_ingest_payload(
                    _make_payload(conv_id="c1", in_tok=300_000, q5h=0.97),
                    now_ts=125.0,
                ),
                db_path=db,
            )
            quota_tracer.ingest_payload(
                quota_tracer.parse_ingest_payload(
                    _make_payload(conv_id="c2", in_tok=300_000, q5h=0.95),
                    now_ts=130.0,
                ),
                db_path=db,
            )
            # Interval 4 (zero observed CLI usage -> external drop):
            quota_tracer.ingest_payload(
                quota_tracer.parse_ingest_payload(
                    _make_payload(conv_id="c2", in_tok=300_000, q5h=0.94),
                    now_ts=140.0,
                ),
                db_path=db,
            )

            reports_clean, intervals = quota_tracer.build_reports(
                db_path=db, buckets=("gemini-5h",), include_confounded=False
            )
            self.assertEqual(len(intervals), 4)
            self.assertTrue(intervals[0].is_clean)
            self.assertIn("subagent_active", intervals[1].confounders)
            self.assertIn("concurrent_conversations", intervals[2].confounders)
            self.assertIn("zero_observed_usage", intervals[3].confounders)

            rep = reports_clean[0]
            self.assertEqual(rep.clean_intervals, 1)
            self.assertEqual(rep.confounded_intervals, 3)
            self.assertIsNotNone(rep.usd_per_pct_stats)
            assert rep.usd_per_pct_stats is not None
            self.assertEqual(rep.usd_per_pct_stats.count, 1)
            self.assertAlmostEqual(rep.usd_per_pct_stats.median, 3.00, places=6)
            self.assertAlmostEqual(rep.windows[0].total_delta_pct, 6.0, places=6)
            self.assertTrue(
                any(a.kind == "zero_usd_drop" for a in rep.anomalies)
            )

            reports_all, _ = quota_tracer.build_reports(
                db_path=db, buckets=("gemini-5h",), include_confounded=True
            )
            assert reports_all[0].usd_per_pct_stats is not None
            self.assertEqual(reports_all[0].usd_per_pct_stats.count, 4)

    def test_unpriced_gemini_model_isolated_and_raw_tokens_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db = Path(tmp_dir) / "trace.sqlite3"
            quota_tracer.ingest_payload(
                quota_tracer.parse_ingest_payload(_make_payload(q5h=1.00), now_ts=100.0),
                db_path=db,
            )
            # Priced interval: Gemini 4 Carbon ($2/1M input) -> $2.00 / 1% = $2.00
            quota_tracer.ingest_payload(
                quota_tracer.parse_ingest_payload(
                    _make_payload(
                        model_name="Gemini 4 Carbon (High)", in_tok=1_000_000, q5h=0.99
                    ),
                    now_ts=110.0,
                ),
                db_path=db,
            )
            # Unpriced future Gemini model: must NOT pollute $/1% as $0.00
            quota_tracer.ingest_payload(
                quota_tracer.parse_ingest_payload(
                    _make_payload(
                        model_name="Gemini 4 Krypton (High)",
                        in_tok=500_000,
                        out_tok=50_000,
                        q5h=0.98,
                    ),
                    now_ts=120.0,
                ),
                db_path=db,
            )

            reports, intervals = quota_tracer.build_reports(
                db_path=db, buckets=("gemini-5h",), include_confounded=True
            )
            unpriced_iv = intervals[1]
            self.assertIsNone(unpriced_iv.cost_usd)
            self.assertIsNone(unpriced_iv.usd_per_pct)
            self.assertEqual(unpriced_iv.total_tokens, 550_000)
            self.assertIn("unpriced_model", unpriced_iv.confounders)

            rep = reports[0]
            self.assertEqual(rep.unpriced_intervals, 1)
            assert rep.usd_per_pct_stats is not None
            self.assertEqual(rep.usd_per_pct_stats.count, 1)
            self.assertAlmostEqual(rep.usd_per_pct_stats.median, 2.00, places=6)
            self.assertTrue(
                any(a.kind == "unpriced_model" for a in rep.anomalies)
            )

    def test_multi_account_breakdowns_outliers_and_cli_export_clear(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db = Path(tmp_dir) / "trace.sqlite3"
            # Account A: 3 baseline intervals (~$3/1%) + 1 extreme outlier ($15/1%)
            quota_tracer.ingest_payload(
                quota_tracer.parse_ingest_payload(
                    _make_payload(email="a@example.com", q5h=1.00), now_ts=100.0
                ),
                db_path=db,
            )
            for idx, (in_tok, ex200k, frac) in enumerate(
                [
                    (1_000_000, False, 0.99),  # $3 / 1% = $3
                    (1_000_001, False, 0.98),  # ~$3 / 1% = $3
                    (1_000_002, False, 0.97),  # ~$3 / 1% = $3
                    (5_000_000, True, 0.96),   # $15 / 1% = $15 (high outlier)
                ],
                1,
            ):
                quota_tracer.ingest_payload(
                    quota_tracer.parse_ingest_payload(
                        _make_payload(
                            email="a@example.com",
                            in_tok=in_tok,
                            exceeds_200k=ex200k,
                            q5h=frac,
                        ),
                        now_ts=100.0 + idx * 10.0,
                    ),
                    db_path=db,
                )

            # Account B on different email with Gemini 4 Hydrogen ($1.50/1M input)
            quota_tracer.ingest_payload(
                quota_tracer.parse_ingest_payload(
                    _make_payload(
                        email="b@example.com",
                        plan_tier="Google AI Pro",
                        model_name="Gemini 4 Hydrogen (Low)",
                        effort="low",
                        q5h=1.00,
                    ),
                    now_ts=200.0,
                ),
                db_path=db,
            )
            quota_tracer.ingest_payload(
                quota_tracer.parse_ingest_payload(
                    _make_payload(
                        email="b@example.com",
                        plan_tier="Google AI Pro",
                        model_name="Gemini 4 Hydrogen (Low)",
                        effort="low",
                        in_tok=1_000_000,
                        q5h=0.99,
                    ),
                    now_ts=210.0,
                ),
                db_path=db,
            )

            json_out = Path(tmp_dir) / "out.json"
            rc = quota_tracer.main(
                [
                    "report",
                    "--db",
                    str(db),
                    "--email",
                    "a@example.com",
                    "--window",
                    "5h",
                    "--export",
                    "json",
                    "--export-path",
                    str(json_out),
                ]
            )
            self.assertEqual(rc, 0)
            exported = json.loads(json_out.read_text(encoding="utf-8"))
            self.assertEqual(len(exported["reports"]), 1)
            rep_a = exported["reports"][0]
            self.assertEqual(rep_a["email"], "a@example.com")
            self.assertAlmostEqual(rep_a["quantization"]["min_delta_pct"], 1.0, places=5)
            self.assertTrue(
                any(a["kind"] == "outlier_high" for a in rep_a["anomalies"])
            )
            ex_rows = {
                r["label"]: r for r in rep_a["factor_breakdowns"]["Context >200k"]
            }
            self.assertAlmostEqual(ex_rows["no"]["median_usd_per_pct"], 3.0, places=4)
            self.assertAlmostEqual(ex_rows["yes"]["median_usd_per_pct"], 15.0, places=4)

            csv_out = Path(tmp_dir) / "out.csv"
            rc_csv = quota_tracer.main(
                [
                    "report",
                    "--db",
                    str(db),
                    "--model",
                    "Hydrogen",
                    "--export",
                    "csv",
                    "--export-path",
                    str(csv_out),
                ]
            )
            self.assertEqual(rc_csv, 0)
            rows = list(csv.DictReader(io.StringIO(csv_out.read_text(encoding="utf-8"))))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["email"], "b@example.com")
            self.assertAlmostEqual(float(rows[0]["usd_per_pct"]), 1.5, places=5)

            rc_clear = quota_tracer.main(["clear", "--db", str(db)])
            self.assertEqual(rc_clear, 0)
            self.assertFalse(db.exists())

    def test_stale_higher_poll_within_same_reset_window_does_not_split_or_double_count(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db = Path(tmp_dir) / "trace.sqlite3"
            rt = "2026-11-22T14:35:00Z"
            quota_tracer.ingest_payload(
                quota_tracer.parse_ingest_payload(
                    _make_payload(conv_id="c1", q5h=0.985, q5h_reset=rt), now_ts=100.0
                ),
                db_path=db,
            )
            quota_tracer.ingest_payload(
                quota_tracer.parse_ingest_payload(
                    _make_payload(
                        conv_id="c1", in_tok=1_000_000, q5h=0.980, q5h_reset=rt
                    ),
                    now_ts=110.0,
                ),
                db_path=db,
            )
            # Stale poll from concurrent terminal c2 reports older higher fraction 0.983
            quota_tracer.ingest_payload(
                quota_tracer.parse_ingest_payload(
                    _make_payload(conv_id="c2", q5h=0.983, q5h_reset=rt), now_ts=115.0
                ),
                db_path=db,
            )
            # Next real monotonic drop below 0.980 to 0.975
            quota_tracer.ingest_payload(
                quota_tracer.parse_ingest_payload(
                    _make_payload(
                        conv_id="c1", in_tok=1_000_001, q5h=0.975, q5h_reset=rt
                    ),
                    now_ts=120.0,
                ),
                db_path=db,
            )

            intervals, windows_map = quota_tracer.build_intervals(
                db_path=db, buckets=("gemini-5h",)
            )
            wins = windows_map[("alice@example.com", "Google AI Ultra", "gemini-5h")]
            self.assertEqual(len(wins), 1)
            self.assertAlmostEqual(wins[0].total_delta_pct, 1.0, places=6)
            self.assertEqual(len(intervals), 2)
            self.assertAlmostEqual(intervals[0].delta_pct, 0.5, places=6)
            self.assertAlmostEqual(intervals[1].delta_pct, 0.5, places=6)
            self.assertIn("concurrent_conversations", intervals[1].confounders)


if __name__ == "__main__":
    unittest.main()
