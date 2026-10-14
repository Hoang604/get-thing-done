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
        self.statusline_root: Path = self.temp_dir / "statusline"
        self.state_dir: Path = self.temp_dir / "state"
        self.thresholds_file: Path = self.temp_dir / "compact_thresholds.json"
        self.transcript_file: Path = self.temp_dir / "transcript.jsonl"
        self.conv_id: str = "conv-test-123"

    def tearDown(self) -> None:
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _write_turn_snapshot(self, turn_num: int, total_tokens: int, model_id: str = "Gemini 4 Argon (High)") -> None:
        turn_dir: Path = self.statusline_root / self.conv_id / f"turn-{turn_num}"
        turn_dir.mkdir(parents=True, exist_ok=True)
        payload: dict[str, object] = {
            "conversation_id": self.conv_id,
            "model": {"id": model_id, "display_name": model_id},
            "context_window": {
                "total_input_tokens": total_tokens,
                "context_window_size": 1048576,
            },
        }
        text: str = json.dumps(payload)
        (turn_dir / "statusline_input.json").write_text(text, encoding="utf-8")
        (self.statusline_root / self.conv_id / "latest.json").write_text(text, encoding="utf-8")

    def test_learns_auto_compact_threshold_and_ignores_manual_compact(self) -> None:
        # 1. Manual compact at 135k tokens -> should NOT lower threshold from 200k
        self._write_turn_snapshot(1, 50_000)
        self._write_turn_snapshot(2, 135_000)
        self.transcript_file.write_text(
            json.dumps({"type": "USER_INPUT", "source": "USER_EXPLICIT", "content": "/compact"}) + "\n",
            encoding="utf-8",
        )
        self._write_turn_snapshot(3, 29_000)

        state, entry = sync_conversation_and_thresholds(
            conv_id=self.conv_id,
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(self.transcript_file),
            statusline_root=self.statusline_root,
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        self.assertEqual(entry.compact_threshold, DEFAULT_COMPACT_THRESHOLD)
        self.assertEqual(entry.last_auto_compact_tokens, 0)
        self.assertEqual(state.last_tokens, 29_000)

        # 2. Normal growth to 192k followed by auto-compact drop to 31k (without /compact)
        self.transcript_file.write_text(
            json.dumps({"type": "USER_INPUT", "source": "USER_EXPLICIT", "content": "continue reviewing files"}) + "\n",
            encoding="utf-8",
        )
        self._write_turn_snapshot(4, 170_000)
        self._write_turn_snapshot(5, 192_000)
        self._write_turn_snapshot(6, 31_000)

        state2, entry2 = sync_conversation_and_thresholds(
            conv_id=self.conv_id,
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(self.transcript_file),
            statusline_root=self.statusline_root,
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
        # Default threshold is 200,000 -> 90% is 180,000
        self._write_turn_snapshot(1, 150_000)
        res_below = evaluate_budget_guard(
            conv_id=self.conv_id,
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(self.transcript_file),
            statusline_root=self.statusline_root,
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        self.assertEqual(res_below, {"injectSteps": []})

        # Reach 182,000 (>= 90%) -> fires warning once
        self._write_turn_snapshot(2, 182_000)
        res_warn = evaluate_budget_guard(
            conv_id=self.conv_id,
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(self.transcript_file),
            statusline_root=self.statusline_root,
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

        # Next turn at 188,000 (still in same cycle) -> does NOT fire again (prevents deadlock)
        self._write_turn_snapshot(3, 188_000)
        res_second = evaluate_budget_guard(
            conv_id=self.conv_id,
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(self.transcript_file),
            statusline_root=self.statusline_root,
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        self.assertEqual(res_second, {"injectSteps": []})

        # Compaction occurs at 195,000 -> drops to 30,000; threshold becomes 195,000 (90% = 175,500)
        self._write_turn_snapshot(4, 195_000)
        self._write_turn_snapshot(5, 30_000)
        res_post_compact = evaluate_budget_guard(
            conv_id=self.conv_id,
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(self.transcript_file),
            statusline_root=self.statusline_root,
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        self.assertEqual(res_post_compact, {"injectSteps": []})

        # In the new cycle, reaching 176,000 (>= 90% of learned 195,000) fires warning again
        self._write_turn_snapshot(6, 176_000)
        res_new_cycle = evaluate_budget_guard(
            conv_id=self.conv_id,
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(self.transcript_file),
            statusline_root=self.statusline_root,
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        steps_new = res_new_cycle.get("injectSteps")
        assert isinstance(steps_new, list)
        self.assertEqual(len(steps_new), 1)


if __name__ == "__main__":
    unittest.main()
