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
    load_thresholds_db,
    sync_conversation_and_thresholds,
)
from context_budget_guard import evaluate_budget_guard


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
        first_step = steps[0]
        assert isinstance(first_step, dict)
        msg_text = str(first_step.get("ephemeralMessage", ""))
        self.assertIn("<critical_instructions>", msg_text)
        self.assertIn("Persist what is already in hand to safe ground", msg_text)
        self.assertIn("Notify the user", msg_text)

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


if __name__ == "__main__":
    unittest.main()

