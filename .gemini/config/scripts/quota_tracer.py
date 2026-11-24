#!/usr/bin/env python3
"""Persistent Gemini quota-to-USD tracer and diagnostic CLI (`quota-trace`)."""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import sqlite3
import statistics
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Sequence

DEFAULT_DB_PATH: Path = Path.home() / ".gemini" / "quota_trace.sqlite3"
GEMINI_BUCKETS: tuple[str, str] = ("gemini-5h", "gemini-weekly")
FRACTION_EPSILON: float = 1e-9
RESET_TIME_JITTER_SECONDS: float = 120.0
SUBAGENT_LOG_INTERVAL_SECONDS: float = 30.0


@dataclass(frozen=True)
class ModelPricing:
    canonical_name: str
    input_per_m: float
    cache_read_per_m: float
    output_per_m: float


# Single canonical USD/1M-token pricing table for Gemini models (Standard API tier).
_GEMINI_PRICING_RULES: tuple[tuple[tuple[str, ...], ModelPricing], ...] = (
    (
        ("3.1 pro", "gemini-3.1-pro"),
        ModelPricing("Gemini 3.1 Pro", 2.00, 0.50, 12.00),
    ),
    (
        ("3.5 flash", "gemini-3.5-flash"),
        ModelPricing("Gemini 3.5 Flash", 1.50, 0.15, 9.00),
    ),
    (
        ("3.7 flash", "gemini-3.7-flash"),
        ModelPricing("Gemini 3.7 Flash", 0.75, 0.075, 3.50),
    ),
    (
        ("4 hydrogen", "gemini-4-hydrogen"),
        ModelPricing("Gemini 4 Hydrogen", 1.50, 0.075, 7.50),
    ),
    (
        ("4 argon", "gemini-4-argon"),
        ModelPricing("Gemini 4 Argon", 2.00, 0.10, 10.00),
    ),
    (
        ("4 carbon", "gemini-4-carbon"),
        ModelPricing("Gemini 4 Carbon", 2.00, 0.10, 10.00),
    ),
    (
        ("4 neon", "gemini-4-neon"),
        ModelPricing("Gemini 4 Neon", 3.00, 0.15, 15.00),
    ),
)

_NON_GEMINI_MARKERS: tuple[str, ...] = ("claude", "gpt-", "o1", "o3", "o4", "codex")


@dataclass(frozen=True)
class QuotaReading:
    bucket: str
    remaining_fraction: float
    # Absent when the upstream quota payload omits an ISO reset timestamp.
    reset_time: str | None
    # Absent when the upstream quota payload omits remaining reset seconds.
    reset_in_seconds: int | None


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int
    cache_read_tokens: int
    cache_create_tokens: int
    output_tokens: int

    @property
    def total_tokens(self) -> int:
        return (
            self.input_tokens
            + self.cache_read_tokens
            + self.cache_create_tokens
            + self.output_tokens
        )

    @property
    def usage_sig(self) -> str:
        if self.cache_create_tokens > 0:
            return (
                f"{self.input_tokens}:{self.cache_create_tokens}:"
                f"{self.cache_read_tokens}:{self.output_tokens}"
            )
        return f"{self.input_tokens}:{self.cache_read_tokens}:{self.output_tokens}"


@dataclass(frozen=True)
class IngestPayload:
    ts: float
    email: str
    # Empty when the CLI payload omits plan_tier.
    plan_tier: str
    conversation_id: str
    model_name: str
    model_family: str
    # Empty when the CLI payload omits model.effort.
    effort: str
    exceeds_200k: bool
    running_subagents: int
    # Absent when current_usage is not populated in the statusline tick.
    usage: TokenUsage | None
    quotas: tuple[QuotaReading, ...]


@dataclass(frozen=True)
class QuotaInterval:
    email: str
    plan_tier: str
    bucket: str
    window_reset_time: str
    start_ts: float
    end_ts: float
    start_fraction: float
    end_fraction: float
    delta_pct: float
    step_count: int
    conversation_ids: tuple[str, ...]
    model_label: str
    effort_label: str
    exceeds_200k_label: str
    input_tokens: int
    cache_read_tokens: int
    cache_create_tokens: int
    output_tokens: int
    total_tokens: int
    # None when any Gemini step in the interval uses a model without pricing.
    cost_usd: float | None
    # None when cost_usd is None.
    usd_per_pct: float | None
    tokens_per_pct: float
    cache_ratio: float
    output_ratio: float
    quota_zone: str
    confounders: tuple[str, ...]
    unpriced_models: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return len(self.confounders) == 0


@dataclass(frozen=True)
class DistributionStats:
    count: int
    min_val: float
    p10: float
    median: float
    mean: float
    p90: float
    max_val: float
    # None when count < 2 or mean == 0.
    cv_pct: float | None


@dataclass(frozen=True)
class FactorRow:
    label: str
    count: int
    median_usd_per_pct: float
    p10_usd_per_pct: float
    p90_usd_per_pct: float
    median_tokens_per_pct: float
    total_delta_pct: float
    total_cost_usd: float


@dataclass(frozen=True)
class WindowReconciliation:
    window_reset_time: str
    first_ts: float
    last_ts: float
    start_fraction: float
    end_fraction: float
    total_delta_pct: float
    total_cost_usd: float
    total_tokens: int
    clean_intervals: int
    confounded_intervals: int
    unpriced_intervals: int
    # None when total_delta_pct <= 0.
    window_usd_per_pct: float | None


@dataclass(frozen=True)
class AnomalyRecord:
    kind: str
    ts: float
    bucket: str
    model_label: str
    delta_pct: float
    # None when interval has an unpriced model.
    cost_usd: float | None
    # None when cost_usd is None.
    usd_per_pct: float | None
    detail: str


@dataclass(frozen=True)
class QuantizationSummary:
    sample_count: int
    # None when sample_count == 0.
    min_delta_pct: float | None
    # None when sample_count == 0.
    median_delta_pct: float | None
    distinct_rounded_steps: int
    top_steps: tuple[tuple[float, int], ...]


@dataclass(frozen=True)
class BucketReport:
    email: str
    plan_tier: str
    bucket: str
    total_intervals: int
    clean_intervals: int
    confounded_intervals: int
    unpriced_intervals: int
    analyzed_intervals: int
    # None when no priced intervals exist in the analyzed set.
    usd_per_pct_stats: DistributionStats | None
    # None when no intervals exist in the analyzed set.
    tokens_per_pct_stats: DistributionStats | None
    factor_breakdowns: dict[str, tuple[FactorRow, ...]]
    windows: tuple[WindowReconciliation, ...]
    anomalies: tuple[AnomalyRecord, ...]
    quantization: QuantizationSummary


def classify_model_family(model_name: str) -> str:
    lowered: str = model_name.strip().lower()
    if not lowered:
        return "other"
    for marker in _NON_GEMINI_MARKERS:
        if marker in lowered:
            return "other"
    if "gemini" in lowered:
        return "gemini"
    for patterns, _ in _GEMINI_PRICING_RULES:
        if any(pat in lowered for pat in patterns):
            return "gemini"
    return "other"


def lookup_gemini_pricing(model_name: str) -> ModelPricing | None:
    lowered: str = model_name.strip().lower()
    if not lowered:
        return None
    for patterns, pricing in _GEMINI_PRICING_RULES:
        if any(pat in lowered for pat in patterns):
            return pricing
    return None


def compute_step_cost_usd(
    model_name: str,
    input_tokens: int,
    cache_read_tokens: int,
    output_tokens: int,
) -> float | None:
    pricing: ModelPricing | None = lookup_gemini_pricing(model_name)
    if pricing is None:
        return None
    return (
        input_tokens * pricing.input_per_m
        + cache_read_tokens * pricing.cache_read_per_m
        + output_tokens * pricing.output_per_m
    ) / 1_000_000.0


def _parse_non_negative_int(val: object) -> int | None:
    if isinstance(val, bool):
        return None
    if isinstance(val, int) and val >= 0:
        return val
    if isinstance(val, float) and math.isfinite(val) and val >= 0 and val.is_integer():
        return int(val)
    return None


def _parse_fraction(val: object) -> float | None:
    if isinstance(val, bool):
        return None
    if isinstance(val, (int, float)) and math.isfinite(val):
        fval: float = float(val)
        if 0.0 <= fval <= 1.0:
            return fval
    return None


def _parse_iso_epoch(raw: str | None) -> float | None:
    if raw is None or not raw.strip():
        return None
    text: str = raw.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt: datetime = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def parse_ingest_payload(raw_obj: object, now_ts: float | None = None) -> IngestPayload:
    if not isinstance(raw_obj, dict):
        raise ValueError("statusline payload must be a JSON object")

    ts: float = now_ts if now_ts is not None else time.time()

    email_obj: object = raw_obj.get("email")
    if not isinstance(email_obj, str) or not email_obj.strip():
        user_obj: object = raw_obj.get("user")
        if isinstance(user_obj, dict):
            email_obj = user_obj.get("email")
    if not isinstance(email_obj, str) or not email_obj.strip():
        raise ValueError("missing required email")
    email: str = email_obj.strip()

    conv_obj: object = raw_obj.get("conversation_id")
    if not isinstance(conv_obj, str) or not conv_obj.strip():
        raise ValueError("missing required conversation_id")
    conversation_id: str = conv_obj.strip()

    plan_tier_obj: object = raw_obj.get("plan_tier")
    plan_tier: str = (
        plan_tier_obj.strip() if isinstance(plan_tier_obj, str) else ""
    )

    model_name: str = ""
    effort: str = ""
    model_obj: object = raw_obj.get("model")
    if isinstance(model_obj, dict):
        dn: object = model_obj.get("display_name")
        mid: object = model_obj.get("id")
        if isinstance(dn, str) and dn.strip():
            model_name = dn.strip()
        elif isinstance(mid, str) and mid.strip():
            model_name = mid.strip()
        eff: object = model_obj.get("effort")
        if isinstance(eff, str) and eff.strip():
            effort = eff.strip().lower()

    exceeds_200k_obj: object = raw_obj.get("exceeds_200k_tokens")
    exceeds_200k: bool = exceeds_200k_obj is True

    running_subagents: int = 0
    subagents_obj: object = raw_obj.get("subagents")
    if isinstance(subagents_obj, list):
        for item in subagents_obj:
            if isinstance(item, dict) and item.get("status") == "running":
                running_subagents += 1

    usage: TokenUsage | None = None
    ctx_obj: object = raw_obj.get("context_window")
    if isinstance(ctx_obj, dict):
        cu_obj: object = ctx_obj.get("current_usage")
        if isinstance(cu_obj, dict):
            in_tok: int | None = _parse_non_negative_int(cu_obj.get("input_tokens", 0))
            out_tok: int | None = _parse_non_negative_int(cu_obj.get("output_tokens", 0))
            cr_tok: int | None = _parse_non_negative_int(
                cu_obj.get("cache_read_input_tokens", 0)
            )
            cc_tok: int | None = _parse_non_negative_int(
                cu_obj.get("cache_creation_input_tokens", 0)
            )
            if None in (in_tok, out_tok, cr_tok, cc_tok):
                raise ValueError("invalid non-negative integer in current_usage")
            assert (
                in_tok is not None
                and out_tok is not None
                and cr_tok is not None
                and cc_tok is not None
            )
            usage = TokenUsage(
                input_tokens=in_tok,
                cache_read_tokens=cr_tok,
                cache_create_tokens=cc_tok,
                output_tokens=out_tok,
            )

    quotas: list[QuotaReading] = []
    quota_root: object = raw_obj.get("quota")
    if not isinstance(quota_root, dict):
        quota_root = raw_obj.get("quotas")
    if isinstance(quota_root, dict):
        for bucket in GEMINI_BUCKETS:
            entry: object = quota_root.get(bucket)
            if not isinstance(entry, dict):
                continue
            frac: float | None = _parse_fraction(entry.get("remaining_fraction"))
            if frac is None:
                continue
            rt_obj: object = entry.get("reset_time")
            rt: str | None = (
                rt_obj.strip() if isinstance(rt_obj, str) and rt_obj.strip() else None
            )
            rs_obj: object = entry.get("reset_in_seconds")
            rs: int | None = _parse_non_negative_int(rs_obj)
            quotas.append(
                QuotaReading(
                    bucket=bucket,
                    remaining_fraction=frac,
                    reset_time=rt,
                    reset_in_seconds=rs,
                )
            )

    return IngestPayload(
        ts=ts,
        email=email,
        plan_tier=plan_tier,
        conversation_id=conversation_id,
        model_name=model_name,
        model_family=classify_model_family(model_name),
        effort=effort,
        exceeds_200k=exceeds_200k,
        running_subagents=running_subagents,
        usage=usage,
        quotas=tuple(quotas),
    )


def _connect_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn: sqlite3.Connection = sqlite3.connect(str(db_path), timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS usage_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL NOT NULL,
            email TEXT NOT NULL,
            plan_tier TEXT NOT NULL,
            conversation_id TEXT NOT NULL,
            model_name TEXT NOT NULL,
            model_family TEXT NOT NULL,
            effort TEXT NOT NULL,
            input_tokens INTEGER NOT NULL,
            cache_read_tokens INTEGER NOT NULL,
            cache_create_tokens INTEGER NOT NULL,
            output_tokens INTEGER NOT NULL,
            exceeds_200k INTEGER NOT NULL,
            running_subagents INTEGER NOT NULL,
            usage_sig TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_usage_email_ts
            ON usage_steps(email, ts);

        CREATE TABLE IF NOT EXISTS quota_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL NOT NULL,
            email TEXT NOT NULL,
            plan_tier TEXT NOT NULL,
            bucket TEXT NOT NULL,
            remaining_fraction REAL NOT NULL,
            reset_time TEXT,
            reset_in_seconds INTEGER,
            conversation_id TEXT NOT NULL,
            running_subagents INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_quota_acct_bucket_ts
            ON quota_snapshots(email, plan_tier, bucket, ts, id);

        CREATE TABLE IF NOT EXISTS subagent_ticks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL NOT NULL,
            email TEXT NOT NULL,
            conversation_id TEXT NOT NULL,
            running_subagents INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_subagent_email_ts
            ON subagent_ticks(email, ts);

        CREATE TABLE IF NOT EXISTS conv_cursors (
            conversation_id TEXT PRIMARY KEY,
            last_usage_sig TEXT NOT NULL,
            last_running_subagents INTEGER NOT NULL,
            last_subagent_log_ts REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS quota_cursors (
            email TEXT NOT NULL,
            plan_tier TEXT NOT NULL,
            bucket TEXT NOT NULL,
            last_fraction REAL NOT NULL,
            last_reset_time TEXT,
            PRIMARY KEY (email, plan_tier, bucket)
        );
        """
    )
    return conn


def _reset_time_changed(prev_rt: str | None, curr_rt: str | None) -> bool:
    if prev_rt is None or curr_rt is None:
        return False
    if prev_rt == curr_rt:
        return False
    prev_ep: float | None = _parse_iso_epoch(prev_rt)
    curr_ep: float | None = _parse_iso_epoch(curr_rt)
    if prev_ep is None or curr_ep is None:
        return prev_rt != curr_rt
    return abs(curr_ep - prev_ep) > RESET_TIME_JITTER_SECONDS


def ingest_payload(payload: IngestPayload, db_path: Path = DEFAULT_DB_PATH) -> bool:
    """Persist new usage steps, quota changes, and subagent activity; return True if any row was inserted."""
    inserted: bool = False
    conn: sqlite3.Connection = _connect_db(db_path)
    try:
        with conn:
            cur_row: sqlite3.Row | None = conn.execute(
                "SELECT last_usage_sig, last_running_subagents, last_subagent_log_ts "
                "FROM conv_cursors WHERE conversation_id = ?",
                (payload.conversation_id,),
            ).fetchone()
            last_sig: str = str(cur_row["last_usage_sig"]) if cur_row else ""
            last_sub: int = int(cur_row["last_running_subagents"]) if cur_row else 0
            last_sub_ts: float = (
                float(cur_row["last_subagent_log_ts"]) if cur_row else 0.0
            )

            new_sig: str = last_sig
            if (
                payload.usage is not None
                and payload.usage.total_tokens > 0
                and payload.usage.usage_sig != last_sig
            ):
                conn.execute(
                    """
                    INSERT INTO usage_steps (
                        ts, email, plan_tier, conversation_id, model_name,
                        model_family, effort, input_tokens, cache_read_tokens,
                        cache_create_tokens, output_tokens, exceeds_200k,
                        running_subagents, usage_sig
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        payload.ts,
                        payload.email,
                        payload.plan_tier,
                        payload.conversation_id,
                        payload.model_name,
                        payload.model_family,
                        payload.effort,
                        payload.usage.input_tokens,
                        payload.usage.cache_read_tokens,
                        payload.usage.cache_create_tokens,
                        payload.usage.output_tokens,
                        1 if payload.exceeds_200k else 0,
                        payload.running_subagents,
                        payload.usage.usage_sig,
                    ),
                )
                new_sig = payload.usage.usage_sig
                inserted = True

            new_sub_ts: float = last_sub_ts
            if payload.running_subagents > 0 and (
                last_sub == 0
                or (payload.ts - last_sub_ts) >= SUBAGENT_LOG_INTERVAL_SECONDS
            ):
                conn.execute(
                    "INSERT INTO subagent_ticks (ts, email, conversation_id, running_subagents) "
                    "VALUES (?, ?, ?, ?)",
                    (
                        payload.ts,
                        payload.email,
                        payload.conversation_id,
                        payload.running_subagents,
                    ),
                )
                new_sub_ts = payload.ts
                inserted = True

            if (
                cur_row is None
                or new_sig != last_sig
                or payload.running_subagents != last_sub
                or new_sub_ts != last_sub_ts
            ):
                conn.execute(
                    """
                    INSERT INTO conv_cursors (
                        conversation_id, last_usage_sig, last_running_subagents, last_subagent_log_ts
                    ) VALUES (?, ?, ?, ?)
                    ON CONFLICT(conversation_id) DO UPDATE SET
                        last_usage_sig = excluded.last_usage_sig,
                        last_running_subagents = excluded.last_running_subagents,
                        last_subagent_log_ts = excluded.last_subagent_log_ts
                    """,
                    (
                        payload.conversation_id,
                        new_sig,
                        payload.running_subagents,
                        new_sub_ts,
                    ),
                )

            for q in payload.quotas:
                q_row: sqlite3.Row | None = conn.execute(
                    "SELECT last_fraction, last_reset_time FROM quota_cursors "
                    "WHERE email = ? AND plan_tier = ? AND bucket = ?",
                    (payload.email, payload.plan_tier, q.bucket),
                ).fetchone()

                should_record: bool = False
                if q_row is None:
                    should_record = True
                else:
                    prev_frac: float = float(q_row["last_fraction"])
                    prev_rt: str | None = (
                        str(q_row["last_reset_time"])
                        if q_row["last_reset_time"] is not None
                        else None
                    )
                    if (
                        abs(q.remaining_fraction - prev_frac) > FRACTION_EPSILON
                        or _reset_time_changed(prev_rt, q.reset_time)
                    ):
                        should_record = True

                if should_record:
                    conn.execute(
                        """
                        INSERT INTO quota_snapshots (
                            ts, email, plan_tier, bucket, remaining_fraction,
                            reset_time, reset_in_seconds, conversation_id, running_subagents
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            payload.ts,
                            payload.email,
                            payload.plan_tier,
                            q.bucket,
                            q.remaining_fraction,
                            q.reset_time,
                            q.reset_in_seconds,
                            payload.conversation_id,
                            payload.running_subagents,
                        ),
                    )
                    conn.execute(
                        """
                        INSERT INTO quota_cursors (
                            email, plan_tier, bucket, last_fraction, last_reset_time
                        ) VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(email, plan_tier, bucket) DO UPDATE SET
                            last_fraction = excluded.last_fraction,
                            last_reset_time = excluded.last_reset_time
                        """,
                        (
                            payload.email,
                            payload.plan_tier,
                            q.bucket,
                            q.remaining_fraction,
                            q.reset_time,
                        ),
                    )
                    inserted = True
    finally:
        conn.close()
    return inserted


def _quota_zone_label(start_fraction: float) -> str:
    pct: float = start_fraction * 100.0
    if pct >= 80.0:
        return "80-100%"
    if pct >= 50.0:
        return "50-80%"
    if pct >= 20.0:
        return "20-50%"
    return "0-20%"


def _cache_ratio_bucket(ratio: float) -> str:
    pct: float = ratio * 100.0
    if pct <= 0.0:
        return "0%"
    if pct < 50.0:
        return "1-50%"
    if pct < 85.0:
        return "50-85%"
    return "85-100%"


def _output_ratio_bucket(ratio: float) -> str:
    pct: float = ratio * 100.0
    if pct < 5.0:
        return "<5%"
    if pct < 20.0:
        return "5-20%"
    if pct < 50.0:
        return "20-50%"
    return ">=50%"


def _percentile(sorted_vals: Sequence[float], p: float) -> float:
    n: int = len(sorted_vals)
    if n == 1:
        return sorted_vals[0]
    pos: float = (n - 1) * p
    lo: int = math.floor(pos)
    hi: int = math.ceil(pos)
    if lo == hi:
        return sorted_vals[lo]
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (pos - lo)


def _compute_distribution(values: Sequence[float]) -> DistributionStats | None:
    if not values:
        return None
    ordered: list[float] = sorted(values)
    mean_v: float = statistics.fmean(ordered)
    cv: float | None = None
    if len(ordered) >= 2 and mean_v > 0.0:
        cv = (statistics.stdev(ordered) / mean_v) * 100.0
    return DistributionStats(
        count=len(ordered),
        min_val=ordered[0],
        p10=_percentile(ordered, 0.10),
        median=_percentile(ordered, 0.50),
        mean=mean_v,
        p90=_percentile(ordered, 0.90),
        max_val=ordered[-1],
        cv_pct=cv,
    )


def _window_key(reset_time: str | None, fallback_ts: float) -> str:
    if reset_time is not None and reset_time.strip():
        ep: float | None = _parse_iso_epoch(reset_time)
        if ep is not None:
            # Bucket to 5-minute precision so minor server reset_time jitter stays in one window.
            rounded: int = int(round(ep / 300.0) * 300)
            return datetime.fromtimestamp(rounded, tz=timezone.utc).strftime(
                "%Y-%m-%dT%H:%MZ"
            )
        return reset_time.strip()
    return datetime.fromtimestamp(fallback_ts, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%MZ"
    )


def build_intervals(
    db_path: Path = DEFAULT_DB_PATH,
    email_filter: str | None = None,
    buckets: Sequence[str] = GEMINI_BUCKETS,
    since_ts: float | None = None,
) -> tuple[list[QuotaInterval], dict[tuple[str, str, str], list[WindowReconciliation]]]:
    if not db_path.is_file():
        return [], {}

    conn: sqlite3.Connection = _connect_db(db_path)
    try:
        bucket_placeholders: str = ",".join("?" for _ in buckets)
        params: list[object] = list(buckets)
        where_clauses: list[str] = [f"bucket IN ({bucket_placeholders})"]
        if email_filter is not None:
            where_clauses.append("email = ?")
            params.append(email_filter)
        if since_ts is not None:
            where_clauses.append("ts >= ?")
            params.append(since_ts)

        snaps: list[sqlite3.Row] = conn.execute(
            f"SELECT * FROM quota_snapshots WHERE {' AND '.join(where_clauses)} "
            "ORDER BY email, plan_tier, bucket, ts, id",
            params,
        ).fetchall()

        step_clauses: list[str] = ["model_family = 'gemini'"]
        step_params: list[object] = []
        if email_filter is not None:
            step_clauses.append("email = ?")
            step_params.append(email_filter)
        if since_ts is not None:
            step_clauses.append("ts >= ?")
            step_params.append(since_ts)
        steps_rows: list[sqlite3.Row] = conn.execute(
            f"SELECT * FROM usage_steps WHERE {' AND '.join(step_clauses)} ORDER BY ts, id",
            step_params,
        ).fetchall()

        sub_clauses: list[str] = []
        sub_params: list[object] = []
        if email_filter is not None:
            sub_clauses.append("email = ?")
            sub_params.append(email_filter)
        if since_ts is not None:
            sub_clauses.append("ts >= ?")
            sub_params.append(since_ts)
        sub_where: str = f"WHERE {' AND '.join(sub_clauses)}" if sub_clauses else ""
        sub_rows: list[sqlite3.Row] = conn.execute(
            f"SELECT ts, email FROM subagent_ticks {sub_where} ORDER BY ts",
            sub_params,
        ).fetchall()
    finally:
        conn.close()

    steps_by_email: dict[str, list[sqlite3.Row]] = {}
    for row in steps_rows:
        steps_by_email.setdefault(str(row["email"]), []).append(row)

    subs_by_email: dict[str, list[float]] = {}
    for row in sub_rows:
        subs_by_email.setdefault(str(row["email"]), []).append(float(row["ts"]))

    grouped_snaps: dict[tuple[str, str, str], list[sqlite3.Row]] = {}
    for row in snaps:
        key: tuple[str, str, str] = (
            str(row["email"]),
            str(row["plan_tier"]),
            str(row["bucket"]),
        )
        grouped_snaps.setdefault(key, []).append(row)

    all_intervals: list[QuotaInterval] = []
    windows_map: dict[tuple[str, str, str], list[WindowReconciliation]] = {}

    for (email, plan_tier, bucket), group in grouped_snaps.items():
        email_steps: list[sqlite3.Row] = steps_by_email.get(email, [])
        email_subs: list[float] = subs_by_email.get(email, [])

        # Group snapshots into continuous reset windows, then track monotonic drops inside each window.
        win_start_idx: int = 0
        win_min_f: float = float(group[0]["remaining_fraction"]) if group else 1.0
        window_spans: list[tuple[int, int]] = []
        for idx in range(1, len(group)):
            prev_s: sqlite3.Row = group[idx - 1]
            curr_s: sqlite3.Row = group[idx]
            curr_f: float = float(curr_s["remaining_fraction"])
            prev_rt: str | None = (
                str(prev_s["reset_time"]) if prev_s["reset_time"] is not None else None
            )
            curr_rt: str | None = (
                str(curr_s["reset_time"]) if curr_s["reset_time"] is not None else None
            )
            rt_changed: bool = _reset_time_changed(prev_rt, curr_rt)
            no_rt_reset: bool = (
                (prev_rt is None or curr_rt is None)
                and curr_f > win_min_f + 0.05
            )
            if rt_changed or no_rt_reset:
                window_spans.append((win_start_idx, idx - 1))
                win_start_idx = idx
                win_min_f = curr_f
            elif curr_f < win_min_f:
                win_min_f = curr_f
        if group:
            window_spans.append((win_start_idx, len(group) - 1))

        win_reconciliations: list[WindowReconciliation] = []
        for w_lo, w_hi in window_spans:
            first_snap: sqlite3.Row = group[w_lo]
            last_snap: sqlite3.Row = group[w_hi]
            w_key: str = _window_key(
                str(last_snap["reset_time"])
                if last_snap["reset_time"] is not None
                else None,
                float(first_snap["ts"]),
            )
            win_intervals: list[QuotaInterval] = []

            anchor_snap: sqlite3.Row = first_snap
            anchor_f: float = float(anchor_snap["remaining_fraction"])
            stale_conv_ids: set[str] = set()

            for i in range(w_lo + 1, w_hi + 1):
                curr_s = group[i]
                curr_f = float(curr_s["remaining_fraction"])
                if curr_f > anchor_f + FRACTION_EPSILON:
                    # Stale out-of-order quota poll within the same reset window; do not double-count.
                    stale_conv_ids.add(str(curr_s["conversation_id"]))
                    continue
                delta_f: float = anchor_f - curr_f
                if delta_f <= FRACTION_EPSILON:
                    continue
                delta_pct: float = delta_f * 100.0
                start_ts: float = float(anchor_snap["ts"])
                end_ts: float = float(curr_s["ts"])

                iv_steps: list[sqlite3.Row] = [
                    s for s in email_steps if start_ts < float(s["ts"]) <= end_ts
                ]
                sub_in_range: bool = any(start_ts <= t <= end_ts for t in email_subs)

                confounders: list[str] = []
                if not iv_steps:
                    confounders.append("zero_observed_usage")

                conv_ids: tuple[str, ...] = tuple(
                    sorted({str(s["conversation_id"]) for s in iv_steps})
                )
                all_active_convs: set[str] = set(conv_ids) | stale_conv_ids
                if len(all_active_convs) > 1:
                    confounders.append("concurrent_conversations")

                if (
                    sub_in_range
                    or int(curr_s["running_subagents"]) > 0
                    or any(int(s["running_subagents"]) > 0 for s in iv_steps)
                ):
                    confounders.append("subagent_active")

                in_tok: int = sum(int(s["input_tokens"]) for s in iv_steps)
                cr_tok: int = sum(int(s["cache_read_tokens"]) for s in iv_steps)
                cc_tok: int = sum(int(s["cache_create_tokens"]) for s in iv_steps)
                out_tok: int = sum(int(s["output_tokens"]) for s in iv_steps)
                total_tok: int = in_tok + cr_tok + cc_tok + out_tok

                unpriced: set[str] = set()
                cost_acc: float = 0.0
                for s in iv_steps:
                    m_name: str = str(s["model_name"])
                    step_cost: float | None = compute_step_cost_usd(
                        m_name,
                        int(s["input_tokens"]),
                        int(s["cache_read_tokens"]),
                        int(s["output_tokens"]),
                    )
                    if step_cost is None:
                        unpriced.add(m_name or "<unknown>")
                    else:
                        cost_acc += step_cost

                if unpriced:
                    confounders.append("unpriced_model")
                    cost_usd: float | None = None
                    usd_per_pct: float | None = None
                else:
                    cost_usd = cost_acc
                    usd_per_pct = cost_acc / delta_pct

                models_set: set[str] = {
                    (
                        pricing.canonical_name
                        if (pricing := lookup_gemini_pricing(str(s["model_name"])))
                        is not None
                        else str(s["model_name"]) or "<unknown>"
                    )
                    for s in iv_steps
                }
                if not models_set:
                    model_label: str = "<none>"
                elif len(models_set) == 1:
                    model_label = next(iter(models_set))
                else:
                    model_label = "<mixed>"

                efforts_set: set[str] = {
                    (str(s["effort"]) or "<unspecified>") for s in iv_steps
                }
                if not efforts_set:
                    effort_label: str = "<none>"
                elif len(efforts_set) == 1:
                    effort_label = next(iter(efforts_set))
                else:
                    effort_label = "<mixed>"

                ex_vals: set[int] = {int(s["exceeds_200k"]) for s in iv_steps}
                if not ex_vals:
                    ex_label: str = "<none>"
                elif ex_vals == {1}:
                    ex_label = "yes"
                elif ex_vals == {0}:
                    ex_label = "no"
                else:
                    ex_label = "mixed"

                in_denom: int = in_tok + cr_tok + cc_tok
                cache_ratio: float = (cr_tok / in_denom) if in_denom > 0 else 0.0
                output_ratio: float = (out_tok / total_tok) if total_tok > 0 else 0.0

                interval = QuotaInterval(
                    email=email,
                    plan_tier=plan_tier,
                    bucket=bucket,
                    window_reset_time=w_key,
                    start_ts=start_ts,
                    end_ts=end_ts,
                    start_fraction=anchor_f,
                    end_fraction=curr_f,
                    delta_pct=delta_pct,
                    step_count=len(iv_steps),
                    conversation_ids=conv_ids,
                    model_label=model_label,
                    effort_label=effort_label,
                    exceeds_200k_label=ex_label,
                    input_tokens=in_tok,
                    cache_read_tokens=cr_tok,
                    cache_create_tokens=cc_tok,
                    output_tokens=out_tok,
                    total_tokens=total_tok,
                    cost_usd=cost_usd,
                    usd_per_pct=usd_per_pct,
                    tokens_per_pct=total_tok / delta_pct,
                    cache_ratio=cache_ratio,
                    output_ratio=output_ratio,
                    quota_zone=_quota_zone_label(anchor_f),
                    confounders=tuple(confounders),
                    unpriced_models=tuple(sorted(unpriced)),
                )
                win_intervals.append(interval)
                all_intervals.append(interval)
                anchor_snap = curr_s
                anchor_f = curr_f
                stale_conv_ids.clear()

            total_w_delta: float = (
                float(first_snap["remaining_fraction"]) - anchor_f
            ) * 100.0
            if total_w_delta > FRACTION_EPSILON * 100.0 or win_intervals:
                priced_cost: float = sum(
                    iv.cost_usd for iv in win_intervals if iv.cost_usd is not None
                )
                total_w_tokens: int = sum(iv.total_tokens for iv in win_intervals)
                clean_cnt: int = sum(1 for iv in win_intervals if iv.is_clean)
                unpriced_cnt: int = sum(
                    1 for iv in win_intervals if "unpriced_model" in iv.confounders
                )
                conf_cnt: int = len(win_intervals) - clean_cnt
                win_usd_per_pct: float | None = (
                    (priced_cost / total_w_delta) if total_w_delta > 0.0 else None
                )
                win_reconciliations.append(
                    WindowReconciliation(
                        window_reset_time=w_key,
                        first_ts=float(first_snap["ts"]),
                        last_ts=float(anchor_snap["ts"]),
                        start_fraction=float(first_snap["remaining_fraction"]),
                        end_fraction=anchor_f,
                        total_delta_pct=max(0.0, total_w_delta),
                        total_cost_usd=priced_cost,
                        total_tokens=total_w_tokens,
                        clean_intervals=clean_cnt,
                        confounded_intervals=conf_cnt,
                        unpriced_intervals=unpriced_cnt,
                        window_usd_per_pct=win_usd_per_pct,
                    )
                )

        windows_map[(email, plan_tier, bucket)] = win_reconciliations

    return all_intervals, windows_map


def _build_factor_rows(
    intervals: Sequence[QuotaInterval], key_fn: Callable[[QuotaInterval], str]
) -> tuple[FactorRow, ...]:
    grouped: dict[str, list[QuotaInterval]] = {}
    for iv in intervals:
        if iv.usd_per_pct is None or iv.cost_usd is None:
            continue
        label: str = key_fn(iv)
        grouped.setdefault(label, []).append(iv)

    rows: list[FactorRow] = []
    for label, items in sorted(
        grouped.items(), key=lambda pair: (-len(pair[1]), pair[0])
    ):
        usd_vals: list[float] = sorted(
            iv.usd_per_pct for iv in items if iv.usd_per_pct is not None
        )
        tok_vals: list[float] = sorted(iv.tokens_per_pct for iv in items)
        rows.append(
            FactorRow(
                label=label,
                count=len(items),
                median_usd_per_pct=_percentile(usd_vals, 0.50),
                p10_usd_per_pct=_percentile(usd_vals, 0.10),
                p90_usd_per_pct=_percentile(usd_vals, 0.90),
                median_tokens_per_pct=_percentile(tok_vals, 0.50),
                total_delta_pct=sum(iv.delta_pct for iv in items),
                total_cost_usd=sum(
                    iv.cost_usd for iv in items if iv.cost_usd is not None
                ),
            )
        )
    return tuple(rows)


def _compute_quantization(intervals: Sequence[QuotaInterval]) -> QuantizationSummary:
    deltas: list[float] = sorted(iv.delta_pct for iv in intervals if iv.delta_pct > 0.0)
    if not deltas:
        return QuantizationSummary(
            sample_count=0,
            min_delta_pct=None,
            median_delta_pct=None,
            distinct_rounded_steps=0,
            top_steps=(),
        )
    freq: dict[float, int] = {}
    for d in deltas:
        key: float = round(d, 4)
        freq[key] = freq.get(key, 0) + 1
    top: tuple[tuple[float, int], ...] = tuple(
        sorted(freq.items(), key=lambda item: (-item[1], item[0]))[:5]
    )
    return QuantizationSummary(
        sample_count=len(deltas),
        min_delta_pct=deltas[0],
        median_delta_pct=_percentile(deltas, 0.50),
        distinct_rounded_steps=len(freq),
        top_steps=top,
    )


def _detect_anomalies(
    all_bucket_intervals: Sequence[QuotaInterval],
    analyzed_priced: Sequence[QuotaInterval],
    usd_stats: DistributionStats | None,
) -> tuple[AnomalyRecord, ...]:
    anomalies: list[AnomalyRecord] = []

    for iv in all_bucket_intervals:
        if "zero_observed_usage" in iv.confounders:
            anomalies.append(
                AnomalyRecord(
                    kind="zero_usd_drop",
                    ts=iv.end_ts,
                    bucket=iv.bucket,
                    model_label=iv.model_label,
                    delta_pct=iv.delta_pct,
                    cost_usd=iv.cost_usd,
                    usd_per_pct=iv.usd_per_pct,
                    detail="Quota dropped with 0 observed CLI tokens (external client/IDE or missed tick)",
                )
            )
        if "unpriced_model" in iv.confounders:
            anomalies.append(
                AnomalyRecord(
                    kind="unpriced_model",
                    ts=iv.end_ts,
                    bucket=iv.bucket,
                    model_label=",".join(iv.unpriced_models),
                    delta_pct=iv.delta_pct,
                    cost_usd=None,
                    usd_per_pct=None,
                    detail="Excluded from $/1% stats until model pricing is added",
                )
            )

    if usd_stats is not None and len(analyzed_priced) >= 3 and usd_stats.median > 0.0:
        ordered_vals: list[float] = sorted(
            iv.usd_per_pct for iv in analyzed_priced if iv.usd_per_pct is not None
        )
        q1: float = _percentile(ordered_vals, 0.25)
        q3: float = _percentile(ordered_vals, 0.75)
        iqr: float = q3 - q1
        low_bound: float = min(usd_stats.median * 0.5, q1 - 1.5 * iqr)
        high_bound: float = max(usd_stats.median * 2.0, q3 + 1.5 * iqr)

        for iv in analyzed_priced:
            if iv.usd_per_pct is None:
                continue
            if iv.usd_per_pct < low_bound or iv.usd_per_pct > high_bound:
                direction: str = "high" if iv.usd_per_pct > high_bound else "low"
                anomalies.append(
                    AnomalyRecord(
                        kind=f"outlier_{direction}",
                        ts=iv.end_ts,
                        bucket=iv.bucket,
                        model_label=iv.model_label,
                        delta_pct=iv.delta_pct,
                        cost_usd=iv.cost_usd,
                        usd_per_pct=iv.usd_per_pct,
                        detail=(
                            f"$/1%={iv.usd_per_pct:.4f} vs median={usd_stats.median:.4f} "
                            f"(effort={iv.effort_label}, >200k={iv.exceeds_200k_label}, "
                            f"cache={iv.cache_ratio * 100:.0f}%, out={iv.output_ratio * 100:.0f}%)"
                        ),
                    )
                )

    return tuple(sorted(anomalies, key=lambda a: a.ts))


def build_reports(
    db_path: Path = DEFAULT_DB_PATH,
    email_filter: str | None = None,
    model_filter: str | None = None,
    buckets: Sequence[str] = GEMINI_BUCKETS,
    since_ts: float | None = None,
    include_confounded: bool = False,
) -> tuple[list[BucketReport], list[QuotaInterval]]:
    intervals, windows_map = build_intervals(
        db_path=db_path,
        email_filter=email_filter,
        buckets=buckets,
        since_ts=since_ts,
    )
    if model_filter is not None:
        mf_lower: str = model_filter.strip().lower()
        intervals = [
            iv
            for iv in intervals
            if mf_lower in iv.model_label.lower()
            or any(mf_lower in um.lower() for um in iv.unpriced_models)
        ]

    by_key: dict[tuple[str, str, str], list[QuotaInterval]] = {}
    for iv in intervals:
        by_key.setdefault((iv.email, iv.plan_tier, iv.bucket), []).append(iv)
    for key in windows_map:
        if model_filter is None:
            by_key.setdefault(key, [])

    reports: list[BucketReport] = []
    for (email, plan_tier, bucket), bucket_ivs in sorted(by_key.items()):
        clean_ivs: list[QuotaInterval] = [iv for iv in bucket_ivs if iv.is_clean]
        unpriced_ivs: list[QuotaInterval] = [
            iv for iv in bucket_ivs if "unpriced_model" in iv.confounders
        ]
        analyzed: list[QuotaInterval] = (
            [iv for iv in bucket_ivs if "unpriced_model" not in iv.confounders]
            if include_confounded
            else clean_ivs
        )
        analyzed_priced: list[QuotaInterval] = [
            iv
            for iv in analyzed
            if iv.usd_per_pct is not None and iv.cost_usd is not None
        ]

        usd_stats: DistributionStats | None = _compute_distribution(
            [iv.usd_per_pct for iv in analyzed_priced if iv.usd_per_pct is not None]
        )
        tok_stats: DistributionStats | None = _compute_distribution(
            [iv.tokens_per_pct for iv in analyzed]
        )

        breakdowns: dict[str, tuple[FactorRow, ...]] = {
            "Model": _build_factor_rows(analyzed_priced, lambda iv: iv.model_label),
            "Effort": _build_factor_rows(analyzed_priced, lambda iv: iv.effort_label),
            "Context >200k": _build_factor_rows(
                analyzed_priced, lambda iv: iv.exceeds_200k_label
            ),
            "Cache Hit Ratio": _build_factor_rows(
                analyzed_priced, lambda iv: _cache_ratio_bucket(iv.cache_ratio)
            ),
            "Output/Total Ratio": _build_factor_rows(
                analyzed_priced, lambda iv: _output_ratio_bucket(iv.output_ratio)
            ),
            "Quota Remaining Zone": _build_factor_rows(
                analyzed_priced, lambda iv: iv.quota_zone
            ),
        }

        anomalies: tuple[AnomalyRecord, ...] = _detect_anomalies(
            bucket_ivs, analyzed_priced, usd_stats
        )
        quant: QuantizationSummary = _compute_quantization(bucket_ivs)

        reports.append(
            BucketReport(
                email=email,
                plan_tier=plan_tier,
                bucket=bucket,
                total_intervals=len(bucket_ivs),
                clean_intervals=len(clean_ivs),
                confounded_intervals=len(bucket_ivs) - len(clean_ivs),
                unpriced_intervals=len(unpriced_ivs),
                analyzed_intervals=len(analyzed_priced),
                usd_per_pct_stats=usd_stats,
                tokens_per_pct_stats=tok_stats,
                factor_breakdowns=breakdowns,
                windows=tuple(windows_map.get((email, plan_tier, bucket), [])),
                anomalies=anomalies,
                quantization=quant,
            )
        )

    return reports, intervals


def _stability_label(cv_pct: float | None) -> str:
    if cv_pct is None:
        return "insufficient samples (n<2)"
    if cv_pct < 15.0:
        return f"stable (CV={cv_pct:.1f}%)"
    if cv_pct < 35.0:
        return f"moderate variance (CV={cv_pct:.1f}%)"
    return f"high variance / non-linear (CV={cv_pct:.1f}%)"


def _fmt_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> list[str]:
    widths: list[int] = [len(h) for h in headers]
    for r in rows:
        for idx, cell in enumerate(r):
            widths[idx] = max(widths[idx], len(cell))
    header_line: str = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    sep_line: str = "-+-".join("-" * w for w in widths)
    out: list[str] = [header_line, sep_line]
    for r in rows:
        out.append(" | ".join(cell.ljust(widths[i]) for i, cell in enumerate(r)))
    return out


def render_text_report(
    reports: Sequence[BucketReport], include_confounded: bool = False
) -> str:
    if not reports:
        return "No Gemini quota trace data found matching the filters."

    lines: list[str] = []
    mode_str: str = "ALL priced intervals (incl. confounded)" if include_confounded else "CLEAN intervals only"
    lines.append(f"Gemini Quota-to-USD Trace Report [{mode_str}]")
    lines.append("=" * 72)

    for rep in reports:
        tier_part: str = f" ({rep.plan_tier})" if rep.plan_tier else ""
        lines.append("")
        lines.append(f"Account: {rep.email}{tier_part}  |  Bucket: {rep.bucket}")
        lines.append(
            f"Intervals: total={rep.total_intervals}, clean={rep.clean_intervals}, "
            f"confounded={rep.confounded_intervals}, unpriced={rep.unpriced_intervals}"
        )

        if rep.usd_per_pct_stats is not None:
            u: DistributionStats = rep.usd_per_pct_stats
            lines.append(
                f"  $/1% quota  (n={u.count}): median=${u.median:.4f} | mean=${u.mean:.4f} | "
                f"p10-p90=${u.p10:.4f}-${u.p90:.4f} | min-max=${u.min_val:.4f}-${u.max_val:.4f} | "
                f"{_stability_label(u.cv_pct)}"
            )
            lines.append(
                f"  Implied 100% bucket value (from median): ~${u.median * 100:.2f}"
            )
        else:
            lines.append("  $/1% quota: no priced intervals available yet.")

        if rep.tokens_per_pct_stats is not None:
            t: DistributionStats = rep.tokens_per_pct_stats
            lines.append(
                f"  tokens/1%   (n={t.count}): median={t.median:,.0f} | "
                f"p10-p90={t.p10:,.0f}-{t.p90:,.0f} | min-max={t.min_val:,.0f}-{t.max_val:,.0f}"
            )

        q: QuantizationSummary = rep.quantization
        if q.sample_count > 0 and q.min_delta_pct is not None and q.median_delta_pct is not None:
            top_str: str = ", ".join(f"{step:.4f}% (x{cnt})" for step, cnt in q.top_steps)
            lines.append(
                f"  Step granularity: min Δ={q.min_delta_pct:.4f}% | median Δ={q.median_delta_pct:.4f}% | "
                f"distinct={q.distinct_rounded_steps}/{q.sample_count} | top: {top_str}"
            )

        for factor_name, factor_rows in rep.factor_breakdowns.items():
            if not factor_rows:
                continue
            lines.append(f"\n  Breakdown by {factor_name}:")
            tbl_rows: list[list[str]] = [
                [
                    r.label,
                    str(r.count),
                    f"${r.median_usd_per_pct:.4f}",
                    f"${r.p10_usd_per_pct:.4f}-${r.p90_usd_per_pct:.4f}",
                    f"{r.median_tokens_per_pct:,.0f}",
                    f"{r.total_delta_pct:.3f}%",
                    f"${r.total_cost_usd:.4f}",
                ]
                for r in factor_rows
            ]
            for tl in _fmt_table(
                ["Group", "n", "Med $/1%", "p10-p90 $/1%", "Med tok/1%", "Σ Δ%", "Σ USD"],
                tbl_rows,
            ):
                lines.append("    " + tl)

        if rep.windows:
            lines.append("\n  Window Reconciliation (all observed CLI spend vs total quota drop):")
            w_rows: list[list[str]] = [
                [
                    w.window_reset_time,
                    f"{w.start_fraction * 100:.2f}%->{w.end_fraction * 100:.2f}%",
                    f"{w.total_delta_pct:.3f}%",
                    f"${w.total_cost_usd:.4f}",
                    f"${w.window_usd_per_pct:.4f}" if w.window_usd_per_pct is not None else "n/a",
                    f"{w.clean_intervals}/{w.confounded_intervals}",
                ]
                for w in rep.windows[-10:]
            ]
            for tl in _fmt_table(
                ["Window Reset", "Quota", "Σ Δ%", "Σ CLI USD", "Win $/1%", "Clean/Conf"],
                w_rows,
            ):
                lines.append("    " + tl)

        if rep.anomalies:
            lines.append(f"\n  Anomalies ({len(rep.anomalies)}):")
            for a in rep.anomalies[-10:]:
                ts_s: str = datetime.fromtimestamp(a.ts, tz=timezone.utc).strftime(
                    "%Y-%m-%d %H:%M:%S UTC"
                )
                lines.append(
                    f"    - [{a.kind}] {ts_s} | {a.model_label} | Δ={a.delta_pct:.4f}% | {a.detail}"
                )

    return "\n".join(lines)


def export_intervals(
    intervals: Sequence[QuotaInterval],
    reports: Sequence[BucketReport],
    fmt: str,
) -> str:
    if fmt == "json":
        payload: dict[str, object] = {
            "reports": [asdict(r) for r in reports],
            "intervals": [asdict(iv) for iv in intervals],
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)
    if fmt == "csv":
        buf = io.StringIO()
        fieldnames: list[str] = [
            "email",
            "plan_tier",
            "bucket",
            "window_reset_time",
            "start_ts",
            "end_ts",
            "start_fraction",
            "end_fraction",
            "delta_pct",
            "step_count",
            "model_label",
            "effort_label",
            "exceeds_200k_label",
            "input_tokens",
            "cache_read_tokens",
            "cache_create_tokens",
            "output_tokens",
            "total_tokens",
            "cost_usd",
            "usd_per_pct",
            "tokens_per_pct",
            "cache_ratio",
            "output_ratio",
            "quota_zone",
            "is_clean",
            "confounders",
            "unpriced_models",
        ]
        writer = csv.DictWriter(buf, fieldnames=fieldnames)
        writer.writeheader()
        for iv in intervals:
            writer.writerow(
                {
                    "email": iv.email,
                    "plan_tier": iv.plan_tier,
                    "bucket": iv.bucket,
                    "window_reset_time": iv.window_reset_time,
                    "start_ts": f"{iv.start_ts:.3f}",
                    "end_ts": f"{iv.end_ts:.3f}",
                    "start_fraction": f"{iv.start_fraction:.7f}",
                    "end_fraction": f"{iv.end_fraction:.7f}",
                    "delta_pct": f"{iv.delta_pct:.6f}",
                    "step_count": iv.step_count,
                    "model_label": iv.model_label,
                    "effort_label": iv.effort_label,
                    "exceeds_200k_label": iv.exceeds_200k_label,
                    "input_tokens": iv.input_tokens,
                    "cache_read_tokens": iv.cache_read_tokens,
                    "cache_create_tokens": iv.cache_create_tokens,
                    "output_tokens": iv.output_tokens,
                    "total_tokens": iv.total_tokens,
                    "cost_usd": f"{iv.cost_usd:.6f}" if iv.cost_usd is not None else "",
                    "usd_per_pct": (
                        f"{iv.usd_per_pct:.6f}" if iv.usd_per_pct is not None else ""
                    ),
                    "tokens_per_pct": f"{iv.tokens_per_pct:.2f}",
                    "cache_ratio": f"{iv.cache_ratio:.4f}",
                    "output_ratio": f"{iv.output_ratio:.4f}",
                    "quota_zone": iv.quota_zone,
                    "is_clean": "true" if iv.is_clean else "false",
                    "confounders": ";".join(iv.confounders),
                    "unpriced_models": ";".join(iv.unpriced_models),
                }
            )
        return buf.getvalue()
    raise ValueError(f"unsupported export format: {fmt}")


def parse_since_arg(raw: str, now_ts: float | None = None) -> float:
    text: str = raw.strip().lower()
    now: float = now_ts if now_ts is not None else time.time()
    if text.endswith("h") and text[:-1].isdigit():
        return now - int(text[:-1]) * 3600.0
    if text.endswith("d") and text[:-1].isdigit():
        return now - int(text[:-1]) * 86400.0
    if text.endswith("w") and text[:-1].isdigit():
        return now - int(text[:-1]) * 7 * 86400.0
    try:
        dt: datetime = datetime.fromisoformat(raw.strip())
    except ValueError as exc:
        raise ValueError(
            f"invalid --since value '{raw}' (use e.g. 24h, 7d, 2w, or YYYY-MM-DD)"
        ) from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def clear_trace_data(db_path: Path = DEFAULT_DB_PATH) -> None:
    if db_path.is_file():
        db_path.unlink()
    for suffix in ("-wal", "-shm"):
        sidecar: Path = Path(f"{db_path}{suffix}")
        if sidecar.is_file():
            sidecar.unlink()


def _cmd_ingest(db_path: Path) -> int:
    try:
        raw_text: str = sys.stdin.read()
        if not raw_text.strip():
            return 0
        raw_obj: object = json.loads(raw_text)
        payload: IngestPayload = parse_ingest_payload(raw_obj)
        ingest_payload(payload, db_path=db_path)
    except Exception:
        # Passive background ingestion must never disrupt statusline rendering.
        return 0
    return 0


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="quota-trace",
        description="Analyze Gemini 5h/weekly quota burn vs API token USD.",
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="report",
        choices=("report", "ingest", "clear"),
        help="Subcommand: report (default), ingest (stdin JSON), or clear (delete trace DB).",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"SQLite trace database path (default: {DEFAULT_DB_PATH}).",
    )
    parser.add_argument(
        "--window",
        choices=("5h", "weekly", "both"),
        default="both",
        help="Quota bucket window to report (default: both).",
    )
    parser.add_argument("--model", type=str, default=None, help="Filter by model substring.")
    parser.add_argument("--email", type=str, default=None, help="Filter by account email.")
    parser.add_argument(
        "--since",
        type=str,
        default=None,
        help="Filter start time (e.g. 24h, 7d, 2w, or YYYY-MM-DD).",
    )
    parser.add_argument(
        "--include-confounded",
        action="store_true",
        help="Include confounded intervals in $/1%% statistics and factor breakdowns.",
    )
    parser.add_argument(
        "--export",
        choices=("json", "csv"),
        default=None,
        help="Export raw intervals and report as json or csv.",
    )
    parser.add_argument(
        "--export-path",
        type=Path,
        default=None,
        help="Write --export output to file instead of stdout.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser: argparse.ArgumentParser = _build_arg_parser()
    args: argparse.Namespace = parser.parse_args(argv)

    if args.command == "ingest":
        return _cmd_ingest(args.db)

    if args.command == "clear":
        clear_trace_data(args.db)
        print(f"Cleared quota trace database at {args.db}")
        return 0

    since_ts: float | None = (
        parse_since_arg(args.since) if args.since is not None else None
    )
    if args.window == "5h":
        selected_buckets: tuple[str, ...] = ("gemini-5h",)
    elif args.window == "weekly":
        selected_buckets = ("gemini-weekly",)
    else:
        selected_buckets = GEMINI_BUCKETS

    reports, intervals = build_reports(
        db_path=args.db,
        email_filter=args.email,
        model_filter=args.model,
        buckets=selected_buckets,
        since_ts=since_ts,
        include_confounded=args.include_confounded,
    )

    if args.export is not None:
        exported: str = export_intervals(intervals, reports, args.export)
        if args.export_path is not None:
            args.export_path.parent.mkdir(parents=True, exist_ok=True)
            args.export_path.write_text(exported, encoding="utf-8")
            print(f"Exported {len(intervals)} intervals to {args.export_path}")
        else:
            print(exported)
        return 0

    print(render_text_report(reports, include_confounded=args.include_confounded))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
