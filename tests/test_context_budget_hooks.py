import json
import os
import shutil
import subprocess
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
    estimate_read_file_tokens,
    load_conversation_state,
    load_thresholds_db,
    sync_conversation_and_thresholds,
)
from context_budget_guard import (
    build_premature_summary_continue_message,
    build_subsequent_block_message,
    build_warning_message,
    detect_guard_mode,
    evaluate_budget_guard,
    evaluate_post_invocation_guard,
    evaluate_stop_guard,
    evaluate_tool_budget_guard,
)


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

        # Subsequent PreInvocation does NOT re-inject warning since PreToolUse already warned once in this cycle
        res_pre_inv = evaluate_budget_guard(
            conv_id=self.conv_id,
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(self.transcript_file),
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        self.assertEqual(res_pre_inv, {"injectSteps": []})

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

    def test_premature_summary_after_warning_forces_continuation_and_resets_after_compact(self) -> None:
        # 1. Before warning window (< 90%): even if summary heading is discussed in chat, hooks do not fire
        self._append_step(
            {
                "type": "PLANNER_RESPONSE",
                "source": "MODEL",
                "input_tokens": 20_000,
                "cache_read_tokens": 100_000,
                "output_tokens": 200,
                "content": "### 1. Context for governing `# User Requests`\n### 2. Read-next working set",
            }
        )
        self.assertEqual(
            evaluate_post_invocation_guard(
                conv_id=self.conv_id,
                fallback_model_name="Gemini 4 Argon (High)",
                transcript_path=str(self.transcript_file),
                state_dir=self.state_dir,
                thresholds_file=self.thresholds_file,
            ),
            {"injectSteps": []},
        )
        self.assertEqual(
            evaluate_stop_guard(
                conv_id=self.conv_id,
                fallback_model_name="Gemini 4 Argon (High)",
                transcript_path=str(self.transcript_file),
                termination_reason="NO_TOOL_CALL",
                state_dir=self.state_dir,
                thresholds_file=self.thresholds_file,
            ),
            {"decision": "allow"},
        )

        # 2. Cross 90% threshold (220,000 / 240,000) -> PreInvocation sends warning message
        self._append_planner_step(20_000, 200_000, output_tokens=150)
        warn_res = evaluate_budget_guard(
            conv_id=self.conv_id,
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(self.transcript_file),
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        warn_steps = warn_res.get("injectSteps")
        self.assertIsInstance(warn_steps, list)
        assert isinstance(warn_steps, list)
        self.assertEqual(len(warn_steps), 1)

        # 3. Normal non-summary response in warning window is NOT flagged as premature summary
        self._append_step(
            {
                "type": "PLANNER_RESPONSE",
                "source": "MODEL",
                "input_tokens": 25_000,
                "cache_read_tokens": 200_000,
                "output_tokens": 120,
                "content": "Context is at 93.8%, saving `report.md` before continuing.",
            }
        )
        self.assertEqual(
            evaluate_post_invocation_guard(
                conv_id=self.conv_id,
                fallback_model_name="Gemini 4 Argon (High)",
                transcript_path=str(self.transcript_file),
                state_dir=self.state_dir,
                thresholds_file=self.thresholds_file,
            ),
            {"injectSteps": []},
        )
        self.assertEqual(
            evaluate_stop_guard(
                conv_id=self.conv_id,
                fallback_model_name="Gemini 4 Argon (High)",
                transcript_path=str(self.transcript_file),
                termination_reason="NO_TOOL_CALL",
                state_dir=self.state_dir,
                thresholds_file=self.thresholds_file,
            ),
            {"decision": "allow"},
        )

        # 4. Agent outputs premature <summary> / standard headings before compaction and stops -> hooks force continue
        self._append_step(
            {
                "type": "PLANNER_RESPONSE",
                "source": "MODEL",
                "input_tokens": 35_000,
                "cache_read_tokens": 200_000,
                "output_tokens": 600,
                "content": (
                    "<summary>\n"
                    "### 1. Context for governing `# User Requests`\n"
                    "- Sync TS to Rust.\n\n"
                    "### 2. Read-next working set\n"
                    "- `rust/src/main.rs:1-120`\n\n"
                    "### 3. Settled state and open work\n"
                    "- Milestone 1 done.\n"
                    "</summary>"
                ),
            }
        )

        post_res = evaluate_post_invocation_guard(
            conv_id=self.conv_id,
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(self.transcript_file),
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        self.assertEqual(post_res.get("terminationBehavior"), "force_continue")
        post_steps = post_res.get("injectSteps")
        self.assertIsInstance(post_steps, list)
        assert isinstance(post_steps, list)
        self.assertEqual(len(post_steps), 1)

        # Repeated PostInvocation on the exact same planner step does not double-inject
        self.assertEqual(
            evaluate_post_invocation_guard(
                conv_id=self.conv_id,
                fallback_model_name="Gemini 4 Argon (High)",
                transcript_path=str(self.transcript_file),
                state_dir=self.state_dir,
                thresholds_file=self.thresholds_file,
            ),
            {"injectSteps": []},
        )

        # Stop hook also blocks stopping on NO_TOOL_CALL for that turn (and only once per planner step)
        stop_res = evaluate_stop_guard(
            conv_id=self.conv_id,
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(self.transcript_file),
            termination_reason="NO_TOOL_CALL",
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        self.assertEqual(stop_res.get("decision"), "continue")
        self.assertTrue(isinstance(stop_res.get("reason"), str) and len(str(stop_res.get("reason"))) > 0)
        self.assertEqual(
            evaluate_stop_guard(
                conv_id=self.conv_id,
                fallback_model_name="Gemini 4 Argon (High)",
                transcript_path=str(self.transcript_file),
                termination_reason="NO_TOOL_CALL",
                state_dir=self.state_dir,
                thresholds_file=self.thresholds_file,
            ),
            {"decision": "allow"},
        )

        # 5. Heading-only summary without <summary> tags on a subsequent pre-compact turn is also caught
        self._append_step(
            {
                "type": "PLANNER_RESPONSE",
                "source": "MODEL",
                "input_tokens": 38_000,
                "cache_read_tokens": 200_000,
                "output_tokens": 400,
                "content": (
                    "1. **Context for governing `# User Requests`**:\n"
                    "   - Finish audit.\n"
                    "2. **Read-next working set**:\n"
                    "   - `server/index.ts:1-80`\n"
                    "3. **Settled state and open work**:\n"
                    "   - Half complete."
                ),
            }
        )
        stop_heading_res = evaluate_stop_guard(
            conv_id=self.conv_id,
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(self.transcript_file),
            termination_reason="NO_TOOL_CALL",
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        self.assertEqual(stop_heading_res.get("decision"), "continue")

        # 6. Once CHECKPOINT / compaction occurs, hooks allow normal stop and do not fire
        self._append_step(
            {
                "type": "CHECKPOINT",
                "source": "SYSTEM",
                "content": "# Resuming from a compaction\n\n<summary>\n### 1. Context for governing `# User Requests`\n</summary>",
            }
        )
        self.assertEqual(
            evaluate_stop_guard(
                conv_id=self.conv_id,
                fallback_model_name="Gemini 4 Argon (High)",
                transcript_path=str(self.transcript_file),
                termination_reason="NO_TOOL_CALL",
                state_dir=self.state_dir,
                thresholds_file=self.thresholds_file,
            ),
            {"decision": "allow"},
        )

    def test_unified_state_persists_effective_tokens_and_compaction_count(self) -> None:
        # 1. Planner step with 120,000 input + 60,000 cache + 600 output + 3,000 chars tool output (1,000 tokens)
        self._append_planner_step(120_000, 60_000, output_tokens=600)
        self._append_step(
            {
                "type": "TOOL_RESPONSE",
                "source": "SYSTEM",
                "content": "a" * 3_000,
            }
        )
        state, entry = sync_conversation_and_thresholds(
            conv_id=self.conv_id,
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(self.transcript_file),
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        self.assertEqual(state.post_planner_tokens, 1_600)
        self.assertEqual(state.effective_tokens, 181_600)
        self.assertEqual(entry.compact_threshold, DEFAULT_COMPACT_THRESHOLD)
        self.assertEqual(state.compaction_count, 0)

        # Persisted JSON matches ConversationTokenState fields
        persisted = load_conversation_state(self.state_dir, self.conv_id)
        self.assertEqual(persisted.effective_tokens, 181_600)

        # 2. Compaction step followed by dropped planner step increments compaction_count once (not twice)
        self._append_step(
            {
                "type": "CHECKPOINT",
                "source": "SYSTEM",
                "content": "<CONTEXT_SUMMARY>compacted</CONTEXT_SUMMARY>",
            }
        )
        state_after_ckpt, _ = sync_conversation_and_thresholds(
            conv_id=self.conv_id,
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(self.transcript_file),
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        self.assertEqual(state_after_ckpt.compaction_count, 1)
        self.assertEqual(state_after_ckpt.post_planner_tokens, 0)

        self._append_planner_step(30_000, 0, output_tokens=300)
        state_after_drop, _ = sync_conversation_and_thresholds(
            conv_id=self.conv_id,
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(self.transcript_file),
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        self.assertEqual(state_after_drop.compaction_count, 1)
        self.assertEqual(state_after_drop.effective_tokens, 30_300)

        # 3. End-to-end check: critical_instructions.sh consumes the unified tracker output
        repo_root: Path = Path(__file__).resolve().parent.parent
        ci_script: Path = repo_root / ".gemini" / "config" / "scripts" / "critical_instructions.sh"
        ci_counter_file: Path = self.temp_dir / "ci_counter"
        env: dict[str, str] = {
            **os.environ,
            "AGY_COMPACT_STATE_DIR": str(self.state_dir),
            "AGY_THRESHOLDS_FILE": str(self.thresholds_file),
            "AGY_CI_COUNTER_FILE": str(ci_counter_file),
        }

        ci_res_1 = json.loads(
            subprocess.run(
                ["bash", str(ci_script)],
                input=json.dumps({"conversationId": self.conv_id}),
                text=True,
                capture_output=True,
                env=env,
                check=True,
            ).stdout
        )
        self.assertEqual(len(ci_res_1.get("injectSteps", [])), 1)

        # Turn 2 with +39,999 token growth (below 40k threshold) & same compaction_count does not re-inject
        self._append_planner_step(70_000, 0, output_tokens=299)
        sync_conversation_and_thresholds(
            conv_id=self.conv_id,
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(self.transcript_file),
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        ci_res_2 = json.loads(
            subprocess.run(
                ["bash", str(ci_script)],
                input=json.dumps({"conversationId": self.conv_id}),
                text=True,
                capture_output=True,
                env=env,
                check=True,
            ).stdout
        )
        self.assertEqual(ci_res_2.get("injectSteps"), [])

        # Turn 3 reaching exactly +40,000 token growth (30,300 -> 70,300) re-injects
        self._append_planner_step(70_000, 0, output_tokens=300)
        sync_conversation_and_thresholds(
            conv_id=self.conv_id,
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(self.transcript_file),
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        ci_res_growth = json.loads(
            subprocess.run(
                ["bash", str(ci_script)],
                input=json.dumps({"conversationId": self.conv_id}),
                text=True,
                capture_output=True,
                env=env,
                check=True,
            ).stdout
        )
        self.assertEqual(len(ci_res_growth.get("injectSteps", [])), 1)

        # When tracker records a new compaction (compaction_count=2), critical_instructions.sh immediately re-injects
        self._append_step({"type": "USER_INPUT", "source": "USER_EXPLICIT", "content": "/compact"})
        sync_conversation_and_thresholds(
            conv_id=self.conv_id,
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(self.transcript_file),
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        ci_res_3 = json.loads(
            subprocess.run(
                ["bash", str(ci_script)],
                input=json.dumps({"conversationId": self.conv_id}),
                text=True,
                capture_output=True,
                env=env,
                check=True,
            ).stdout
        )
        self.assertEqual(len(ci_res_3.get("injectSteps", [])), 1)

    def test_detect_guard_mode_tracks_plan_auditor_and_default_transitions(self) -> None:
        self.assertEqual(detect_guard_mode(str(self.transcript_file)), "default")
        self.assertEqual(
            detect_guard_mode("", last_user_input="/boundary-plan refactor"),
            "boundary-plan",
        )
        self.assertEqual(
            detect_guard_mode("", last_user_input="<CONTEXT_SUMMARY>boundary-plan</CONTEXT_SUMMARY>"),
            "default",
        )

        # Noise in planner/tool/system/checkpoint steps and word-interior matches do not switch phase
        self._append_step({"type": "PLANNER_RESPONSE", "source": "MODEL", "content": "Run boundary-plan and execute"})
        self._append_step({"type": "TOOL_RESPONSE", "source": "SYSTEM", "content": "boundary-plan execute"})
        self._append_step({"type": "USER_INPUT", "source": "SYSTEM", "content": "boundary-plan"})
        self._append_step({"type": "CHECKPOINT", "source": "SYSTEM", "content": "<CONTEXT_SUMMARY>boundary-plan</CONTEXT_SUMMARY>"})
        self.assertEqual(detect_guard_mode(str(self.transcript_file)), "default")

        # Real explicit user prompt with /boundary-plan activates plan phase
        self._append_step({"type": "USER_INPUT", "source": "USER_EXPLICIT", "content": "Use /boundary-plan on module X"})
        self.assertEqual(detect_guard_mode(str(self.transcript_file)), "boundary-plan")

        # Word-interior 'executed' and planner text mentioning 'execute' keep plan phase active
        self._append_step({"type": "USER_INPUT", "source": "USER_EXPLICIT", "content": "Baseline executed fine, continue"})
        self._append_step({"type": "PLANNER_RESPONSE", "source": "MODEL", "content": "Waiting to execute later"})
        self.assertEqual(detect_guard_mode(str(self.transcript_file)), "boundary-plan")

        # Explicit user 'execute' ends plan phase; subsequent SYSTEM_MESSAGE after USER_INPUT cannot switch to auditor
        self._append_step({"type": "USER_INPUT", "source": "USER_EXPLICIT", "content": "Approved, execute now"})
        self.assertEqual(detect_guard_mode(str(self.transcript_file)), "default")
        self._append_step(
            {
                "type": "SYSTEM_MESSAGE",
                "source": "SYSTEM",
                "content": (
                    "<SYSTEM_MESSAGE>\n"
                    "[Message] timestamp=2026-11-17T03:59:15Z sender=sub-1 priority=MESSAGE_PRIORITY_HIGH "
                    "content=Audit boundary implementation plan at plan.md with implementation ledger at ledger.md. "
                    "Execute your passive code inspection protocol and deliver audit_report_round_1.md.\n"
                    "</SYSTEM_MESSAGE>"
                ),
            }
        )
        self.assertEqual(detect_guard_mode(str(self.transcript_file)), "default")

        self._append_step({"type": "USER_INPUT", "source": "USER_EXPLICIT", "content": "Draft next task via @[boundary-plan]"})
        self.assertEqual(detect_guard_mode(str(self.transcript_file)), "boundary-plan")

        # Prefers transcript_full.jsonl over truncated transcript.jsonl when present
        full_file: Path = self.transcript_file.with_name("transcript_full.jsonl")
        full_file.write_text(
            json.dumps({"type": "USER_INPUT", "source": "USER_EXPLICIT", "content": "proceed with /execute"}) + "\n",
            encoding="utf-8",
        )
        self.assertEqual(detect_guard_mode(str(self.transcript_file)), "default")

        # Subagent transcript: SYSTEM_SDK hook step followed by opening SYSTEM [Message] activates boundary-auditor
        auditor_transcript: Path = self.temp_dir / "auditor_conv" / "transcript.jsonl"
        auditor_transcript.parent.mkdir(parents=True, exist_ok=True)
        auditor_directive: str = (
            "Audit boundary implementation plan at [implementation_plan.md](file:///tmp/plan.md) "
            "with implementation ledger at [implementation_ledger.md](file:///tmp/ledger.md). "
            "Execute your passive code inspection protocol and deliver audit_report_round_1.md."
        )
        with open(auditor_transcript, "w", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "type": "SYSTEM_MESSAGE",
                        "source": "SYSTEM_SDK",
                        "content": "<SYSTEM_MESSAGE><critical_instructions>hook</critical_instructions></SYSTEM_MESSAGE>",
                    }
                )
                + "\n"
            )
            f.write(
                json.dumps(
                    {
                        "type": "SYSTEM_MESSAGE",
                        "source": "SYSTEM",
                        "content": (
                            "The following is a <SYSTEM_MESSAGE> not actually sent by the user.\n\n"
                            "<SYSTEM_MESSAGE>\n"
                            "[Message] timestamp=2026-11-17T03:59:15Z sender=parent-1 priority=MESSAGE_PRIORITY_HIGH "
                            f"content={auditor_directive}\n"
                            "</SYSTEM_MESSAGE>"
                        ),
                    }
                )
                + "\n"
            )
            f.write(json.dumps({"type": "CHECKPOINT", "source": "SYSTEM", "content": "<CONTEXT_SUMMARY>x</CONTEXT_SUMMARY>"}) + "\n")
            f.write(
                json.dumps(
                    {
                        "type": "SYSTEM_MESSAGE",
                        "source": "SYSTEM",
                        "content": "<SYSTEM_MESSAGE>\n[Message] timestamp=2026-11-17T04:05:00Z sender=parent-1 priority=MESSAGE_PRIORITY_HIGH content=Proceed.\n</SYSTEM_MESSAGE>",
                    }
                )
                + "\n"
            )
        # Even if last_user_input echoes the directive containing 'Execute', auditor mode stays active
        self.assertEqual(detect_guard_mode(str(auditor_transcript), last_user_input=auditor_directive), "boundary-auditor")

        # Non-auditor subagent opening SYSTEM_MESSAGE stays default
        other_subagent_transcript: Path = self.temp_dir / "other_subagent_conv" / "transcript.jsonl"
        other_subagent_transcript.parent.mkdir(parents=True, exist_ok=True)
        other_subagent_transcript.write_text(
            json.dumps(
                {
                    "type": "SYSTEM_MESSAGE",
                    "source": "SYSTEM",
                    "content": "<SYSTEM_MESSAGE>\n[Message] timestamp=2026-11-17T03:59:15Z sender=parent-1 priority=MESSAGE_PRIORITY_HIGH content=Research files in src/\n</SYSTEM_MESSAGE>",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        self.assertEqual(detect_guard_mode(str(other_subagent_transcript)), "default")

    def test_guard_mode_routes_warning_block_and_premature_summary_branches(self) -> None:
        warnings = {
            mode: build_warning_message(460_000, 480_000, guard_mode=mode)
            for mode in ("default", "boundary-plan", "boundary-auditor")
        }
        self.assertEqual(len(set(warnings.values())), 3)
        sub_blocks = {
            mode: build_subsequent_block_message(470_000, 480_000, guard_mode=mode)
            for mode in ("default", "boundary-plan", "boundary-auditor")
        }
        self.assertEqual(len(set(sub_blocks.values())), 3)
        premature = {
            mode: build_premature_summary_continue_message(465_000, 480_000, guard_mode=mode)
            for mode in ("default", "boundary-plan", "boundary-auditor")
        }
        self.assertEqual(len(set(premature.values())), 3)

        # 1. PreInvocation CLI at >=95% with lastUserInput carrying boundary-plan emits plan warning branch
        self._append_planner_step(460_000, 0, output_tokens=200)
        guard_script: Path = (
            Path(__file__).resolve().parent.parent
            / ".gemini"
            / "config"
            / "scripts"
            / "context_budget_guard.py"
        )
        env: dict[str, str] = {
            **os.environ,
            "AGY_COMPACT_STATE_DIR": str(self.state_dir),
            "AGY_THRESHOLDS_FILE": str(self.thresholds_file),
        }
        cli_plan = json.loads(
            subprocess.run(
                ["python3", str(guard_script)],
                input=json.dumps(
                    {
                        "conversationId": "conv-cli-plan",
                        "modelName": "Gemini 4 Argon (High)",
                        "transcriptPath": str(self.transcript_file),
                        "lastUserInput": "/boundary-plan this module",
                    }
                ),
                text=True,
                capture_output=True,
                env=env,
                check=True,
            ).stdout
        )
        plan_msg: str = cli_plan["injectSteps"][0]["systemMessage"]["systemMessage"]
        self.assertEqual(
            plan_msg,
            build_warning_message(460_200, 480_000, guard_mode="boundary-plan"),
        )

        # 2. PreToolUse block at >=97.5% (1st and subsequent in same turn) emits plan branches while in plan phase
        transcript_plan: Path = self.temp_dir / "plan_transcript.jsonl"
        with open(transcript_plan, "w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "USER_INPUT", "source": "USER_EXPLICIT", "content": "/boundary-plan"}) + "\n")
            f.write(json.dumps({"type": "PLANNER_RESPONSE", "source": "MODEL", "input_tokens": 466_000, "cache_read_tokens": 0, "output_tokens": 200}) + "\n")

        target_file: Path = self.temp_dir / "big.ts"
        target_file.write_text("\n".join("x" * 54 for _ in range(200)) + "\n", encoding="utf-8")
        read_tokens: int = estimate_read_file_tokens({"Path": str(target_file)})
        tool_display_tokens: int = 466_200 + read_tokens

        deny_first = evaluate_tool_budget_guard(
            conv_id="conv-tool-plan",
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(transcript_plan),
            tool_call={"name": "read_file", "args": {"Path": str(target_file)}},
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        self.assertEqual(
            deny_first.get("reason"),
            build_warning_message(tool_display_tokens, 480_000, guard_mode="boundary-plan"),
        )

        deny_second = evaluate_tool_budget_guard(
            conv_id="conv-tool-plan",
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(transcript_plan),
            tool_call={"name": "read_file", "args": {"Path": str(target_file)}},
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        self.assertEqual(
            deny_second.get("reason"),
            build_subsequent_block_message(tool_display_tokens, 480_000, guard_mode="boundary-plan"),
        )

        # 3. Premature summary during boundary-plan phase emits plan continue variant
        with open(transcript_plan, "a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "type": "PLANNER_RESPONSE",
                        "source": "MODEL",
                        "input_tokens": 466_000,
                        "cache_read_tokens": 0,
                        "output_tokens": 300,
                        "content": "<summary>\npartial\n</summary>",
                    }
                )
                + "\n"
            )
        post_plan = evaluate_post_invocation_guard(
            conv_id="conv-tool-plan",
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(transcript_plan),
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        self.assertEqual(
            post_plan["injectSteps"][0]["systemMessage"]["systemMessage"],
            build_premature_summary_continue_message(466_300, 480_000, guard_mode="boundary-plan"),
        )
        stop_plan = evaluate_stop_guard(
            conv_id="conv-tool-plan",
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(transcript_plan),
            termination_reason="NO_TOOL_CALL",
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        self.assertEqual(
            stop_plan.get("reason"),
            build_premature_summary_continue_message(466_300, 480_000, guard_mode="boundary-plan"),
        )

        # 4. After user sends execute, PreInvocation reverts to default branch
        with open(transcript_plan, "a", encoding="utf-8") as f:
            f.write(json.dumps({"type": "USER_INPUT", "source": "USER_EXPLICIT", "content": "/execute"}) + "\n")
            f.write(json.dumps({"type": "PLANNER_RESPONSE", "source": "MODEL", "input_tokens": 466_000, "cache_read_tokens": 0, "output_tokens": 200}) + "\n")
        res_after_execute = evaluate_budget_guard(
            conv_id="conv-exec-after-plan",
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(transcript_plan),
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        self.assertEqual(
            res_after_execute["injectSteps"][0]["systemMessage"]["systemMessage"],
            build_warning_message(466_200, 480_000, guard_mode="default"),
        )

        # 5. Subagent opening SYSTEM_MESSAGE routes PreInvocation CLI, PreToolUse (1st & 2nd), PostInvocation, and Stop to boundary-auditor
        transcript_auditor: Path = self.temp_dir / "auditor_transcript.jsonl"
        auditor_prompt: str = (
            "Audit boundary implementation plan at [implementation_plan.md](file:///tmp/plan.md) "
            "with implementation ledger at [implementation_ledger.md](file:///tmp/ledger.md). "
            "Execute your passive code inspection protocol and deliver audit_report_round_1.md."
        )
        with open(transcript_auditor, "w", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "type": "SYSTEM_MESSAGE",
                        "source": "SYSTEM_SDK",
                        "content": "<SYSTEM_MESSAGE>hook</SYSTEM_MESSAGE>",
                    }
                )
                + "\n"
            )
            f.write(
                json.dumps(
                    {
                        "type": "SYSTEM_MESSAGE",
                        "source": "SYSTEM",
                        "content": (
                            "<SYSTEM_MESSAGE>\n"
                            "[Message] timestamp=2026-11-17T03:59:15Z sender=parent-1 priority=MESSAGE_PRIORITY_HIGH "
                            f"content={auditor_prompt}\n"
                            "</SYSTEM_MESSAGE>"
                        ),
                    }
                )
                + "\n"
            )
            f.write(json.dumps({"type": "PLANNER_RESPONSE", "source": "MODEL", "input_tokens": 460_000, "cache_read_tokens": 0, "output_tokens": 200}) + "\n")

        cli_auditor = json.loads(
            subprocess.run(
                ["python3", str(guard_script)],
                input=json.dumps(
                    {
                        "conversationId": "conv-cli-auditor",
                        "modelName": "Gemini 4 Argon (High)",
                        "transcriptPath": str(transcript_auditor),
                        "lastUserInput": auditor_prompt,
                    }
                ),
                text=True,
                capture_output=True,
                env=env,
                check=True,
            ).stdout
        )
        self.assertEqual(
            cli_auditor["injectSteps"][0]["systemMessage"]["systemMessage"],
            build_warning_message(460_200, 480_000, guard_mode="boundary-auditor"),
        )

        with open(transcript_auditor, "a", encoding="utf-8") as f:
            f.write(json.dumps({"type": "PLANNER_RESPONSE", "source": "MODEL", "input_tokens": 466_000, "cache_read_tokens": 0, "output_tokens": 200}) + "\n")

        auditor_deny_first = evaluate_tool_budget_guard(
            conv_id="conv-tool-auditor",
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(transcript_auditor),
            tool_call={"name": "read_file", "args": {"Path": str(target_file)}},
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        self.assertEqual(
            auditor_deny_first.get("reason"),
            build_warning_message(tool_display_tokens, 480_000, guard_mode="boundary-auditor"),
        )

        auditor_deny_second = evaluate_tool_budget_guard(
            conv_id="conv-tool-auditor",
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(transcript_auditor),
            tool_call={"name": "read_file", "args": {"Path": str(target_file)}},
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        self.assertEqual(
            auditor_deny_second.get("reason"),
            build_subsequent_block_message(tool_display_tokens, 480_000, guard_mode="boundary-auditor"),
        )

        with open(transcript_auditor, "a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "type": "PLANNER_RESPONSE",
                        "source": "MODEL",
                        "input_tokens": 466_000,
                        "cache_read_tokens": 0,
                        "output_tokens": 300,
                        "content": "<summary>\npartial\n</summary>",
                    }
                )
                + "\n"
            )

        auditor_post = evaluate_post_invocation_guard(
            conv_id="conv-tool-auditor",
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(transcript_auditor),
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        self.assertEqual(
            auditor_post["injectSteps"][0]["systemMessage"]["systemMessage"],
            build_premature_summary_continue_message(466_300, 480_000, guard_mode="boundary-auditor"),
        )

        auditor_stop = evaluate_stop_guard(
            conv_id="conv-tool-auditor",
            fallback_model_name="Gemini 4 Argon (High)",
            transcript_path=str(transcript_auditor),
            termination_reason="NO_TOOL_CALL",
            state_dir=self.state_dir,
            thresholds_file=self.thresholds_file,
        )
        self.assertEqual(
            auditor_stop.get("reason"),
            build_premature_summary_continue_message(466_300, 480_000, guard_mode="boundary-auditor"),
        )


if __name__ == "__main__":
    unittest.main()

