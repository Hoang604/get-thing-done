import json
import shutil
import tempfile
import unittest
from pathlib import Path
import sys

SCRIPT_DIR: Path = Path(__file__).resolve().parent.parent / ".gemini" / "config" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from compact_threshold_tracker import (
    DEFAULT_COMPACT_THRESHOLD,
    MAX_COMPACT_THRESHOLD,
    load_thresholds_db,
    sync_conversation_and_thresholds,
)
from context_budget_guard import evaluate_budget_guard, evaluate_tool_budget_guard


class TestContextBudgetHooks(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir: Path = Path(tempfile.mkdtemp())
        self.state_dir: Path = self.temp_dir / "state"
        self.thresholds_file: Path = self.temp_dir / "compact_thresholds.json"
        self.transcript_file: Path = self.temp_dir / "transcript.jsonl"
        self.conv_id: str = "conv-test-123"

    def tearDown(self) -> None:
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _append_step(self, step: dict[str, object]) -> None:
        with open(self.transcript_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(step) + "\n")

    def _append_planner_step(
        self,
        input_tokens: int,
        cache_read_tokens: int = 0,
        output_tokens: int = 200,
    ) -> None:
        self._append_step(
            {
                "type": "PLANNER_RESPONSE",
                "source": "MODEL",
                "input_tokens": input_tokens,
                "cache_read_tokens": cache_read_tokens,
                "output_tokens": output_tokens,
            }
        )

    def test_learns_auto_compact_threshold_and_ignores_manual_compact(self) -> None:
        # 1. Manual compact at 135k tokens -> should NOT lower threshold from 240k
        self._append_planner_step(50_000)
        self._append_planner_step(15_000, 120_000)
        self._append_step({"type": "USER_INPUT", "source": "USER_EXPLICIT", "content": "/compact"})
        self._append_planner_step(29_000)

        state, entry = sync_conversation_and_thresholds(
            conv_id=self.conv_id,
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(self.transcript_file),
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        self.assertEqual(entry.compact_threshold, DEFAULT_COMPACT_THRESHOLD)
        self.assertEqual(entry.last_auto_compact_tokens, 0)
        self.assertEqual(state.last_tokens, 29_000)

        # 2. Normal growth to 192k followed by auto-compact drop to 31k (without /compact)
        self._append_step({"type": "USER_INPUT", "source": "USER_EXPLICIT", "content": "continue reviewing files"})
        self._append_planner_step(20_000, 150_000)
        self._append_planner_step(22_000, 170_000)
        self._append_planner_step(31_000, 0)

        state2, entry2 = sync_conversation_and_thresholds(
            conv_id=self.conv_id,
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(self.transcript_file),
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        self.assertEqual(entry2.last_auto_compact_tokens, 192_000)
        self.assertEqual(entry2.compact_threshold, 192_000)
        self.assertEqual(entry2.max_safe_tokens, 170_000)
        self.assertFalse(state2.warned_in_cycle)

        db = load_thresholds_db(self.thresholds_file)
        self.assertIn("Gemini 4 Argon (High)", db)
        self.assertEqual(db["Gemini 4 Argon (High)"].compact_threshold, 192_000)

        # 3. Overshoot before auto-compact (e.g. 238k -> 338k spike -> 35k compact) caps at MAX_COMPACT_THRESHOLD (245k)
        self._append_planner_step(38_000, 200_000)
        self._append_planner_step(100_000, 238_000)
        self._append_planner_step(35_000, 0)

        _, entry3 = sync_conversation_and_thresholds(
            conv_id=self.conv_id,
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(self.transcript_file),
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        self.assertEqual(entry3.compact_threshold, MAX_COMPACT_THRESHOLD)
        self.assertEqual(entry3.last_auto_compact_tokens, MAX_COMPACT_THRESHOLD)
        self.assertEqual(entry3.max_safe_tokens, 238_000)

    def test_budget_guard_fires_once_at_90_percent_and_resets_after_compact(self) -> None:
        # Default threshold is 240,000 -> 90% is 216,000
        self._append_planner_step(30_000, 150_000)
        res_below = evaluate_budget_guard(
            conv_id=self.conv_id,
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(self.transcript_file),
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        self.assertEqual(res_below, {"injectSteps": []})

        # Reach 218,000 (>= 90% of 240,000) -> fires warning once
        self._append_planner_step(18_000, 200_000)
        res_warn = evaluate_budget_guard(
            conv_id=self.conv_id,
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(self.transcript_file),
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        steps = res_warn.get("injectSteps")
        self.assertIsInstance(steps, list)
        assert isinstance(steps, list)
        self.assertEqual(len(steps), 1)

        # Next turn at 225,000 (cache miss: input_tokens=225,000, cache_read_tokens=0) -> does NOT fire again
        self._append_planner_step(225_000, 0)
        res_second = evaluate_budget_guard(
            conv_id=self.conv_id,
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(self.transcript_file),
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        self.assertEqual(res_second, {"injectSteps": []})

        # Compaction occurs at 230,000 -> drops to 30,000; threshold becomes 230,000 (90% = 207,000)
        self._append_planner_step(5_000, 225_000)
        self._append_planner_step(30_000, 0)
        res_post_compact = evaluate_budget_guard(
            conv_id=self.conv_id,
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(self.transcript_file),
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        self.assertEqual(res_post_compact, {"injectSteps": []})

        # In the new cycle, reaching 208,000 (>= 90% of learned 230,000) with slug modelName fires warning again
        self._append_planner_step(8_000, 200_000)
        res_new_cycle = evaluate_budget_guard(
            conv_id=self.conv_id,
            fallback_model_name="gemini-4-argon-high",
            transcript_path=str(self.transcript_file),
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        steps_new = res_new_cycle.get("injectSteps")
        assert isinstance(steps_new, list)
        self.assertEqual(len(steps_new), 1)

    def test_pre_tool_use_blocks_at_95_percent_and_allows_next_turn(self) -> None:
        # Default threshold = 240,000 -> 95% block threshold = 228,000
        # Start turn at 220,000 input tokens + 200 output tokens
        self._append_planner_step(20_000, 200_000, output_tokens=200)

        target_file: Path = self.temp_dir / "chunk.ts"
        # 200 lines * ~60 chars/line = ~12,000 chars -> ~4,000 tokens at 3.0 chars/token
        target_file.write_text("\n".join("x" * 54 for _ in range(200)) + "\n", encoding="utf-8")

        # 1st read_file: ~220,200 + ~4,000 = ~224,200 (< 228,000) -> allowed
        res1 = evaluate_tool_budget_guard(
            conv_id=self.conv_id,
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(self.transcript_file),
            tool_call={"name": "read_file", "args": {"Path": str(target_file)}},
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        self.assertEqual(res1, {"decision": "allow"})

        # 2nd read_file in same turn: ~224,200 + ~4,000 = ~228,200 (>= 228,000) -> DENIED
        res2 = evaluate_tool_budget_guard(
            conv_id=self.conv_id,
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(self.transcript_file),
            tool_call={"name": "read_file", "args": {"Path": str(target_file)}},
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        self.assertEqual(res2.get("decision"), "deny")

        # 3rd tool (read_file) and 4th tool (run_command rg/grep/cat) in same turn -> DENIED
        res3 = evaluate_tool_budget_guard(
            conv_id=self.conv_id,
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(self.transcript_file),
            tool_call={"name": "read_file", "args": {"Path": str(target_file)}},
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        self.assertEqual(res3.get("decision"), "deny")

        res4 = evaluate_tool_budget_guard(
            conv_id=self.conv_id,
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(self.transcript_file),
            tool_call={"name": "run_command", "args": {"CommandLine": "rg 'pattern' src/"}},
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        self.assertEqual(res4.get("decision"), "deny")

        # Non-guarded run_command (e.g. pytest / unittest) is still allowed
        res_other_cmd = evaluate_tool_budget_guard(
            conv_id=self.conv_id,
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(self.transcript_file),
            tool_call={"name": "run_command", "args": {"CommandLine": "python3 -m unittest"}},
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        self.assertEqual(res_other_cmd, {"decision": "allow"})

        # Subsequent PreInvocation injects the full ephemeralMessage once and clears blocked_in_last_turn
        res_pre_inv = evaluate_budget_guard(
            conv_id=self.conv_id,
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(self.transcript_file),
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        steps = res_pre_inv.get("injectSteps")
        assert isinstance(steps, list)
        self.assertEqual(len(steps), 1)

        # Next turn (after agent wrote file, still at 232,000 >= 95% and NOT compacted yet):
        # calling read_file and rg must be ALLOWED instead of deadlocking
        self._append_planner_step(32_000, 200_000, output_tokens=200)
        res_next_turn_read = evaluate_tool_budget_guard(
            conv_id=self.conv_id,
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(self.transcript_file),
            tool_call={"name": "read_file", "args": {"Path": str(target_file)}},
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        self.assertEqual(res_next_turn_read, {"decision": "allow"})

        res_next_turn_rg = evaluate_tool_budget_guard(
            conv_id=self.conv_id,
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(self.transcript_file),
            tool_call={"name": "run_command", "args": {"CommandLine": "rg 'pattern' src/"}},
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        self.assertEqual(res_next_turn_rg, {"decision": "allow"})


if __name__ == "__main__":
    unittest.main()

