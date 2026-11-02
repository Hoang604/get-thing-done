import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR: Path = (
    Path(__file__).resolve().parent.parent / ".gemini" / "config" / "scripts"
)
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

SCRIPT_PATH: Path = SCRIPT_DIR / "loop_hook.py"
spec = importlib.util.spec_from_file_location("loop_hook", SCRIPT_PATH)
assert spec is not None and spec.loader is not None
loop_hook = importlib.util.module_from_spec(spec)
sys.modules["loop_hook"] = loop_hook
spec.loader.exec_module(loop_hook)


class TestLoopHook(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir: Path = Path(tempfile.mkdtemp())
        self.state_dir: Path = self.temp_dir / "state"
        self.transcript_file: Path = self.temp_dir / "transcript.jsonl"
        self.conv_id: str = "conv-loop-test"
        self.skill_path: str = (
            "/home/user/.gemini/antigravity-cli/skills/loop/SKILL.md"
        )

    def tearDown(self) -> None:
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _read_loop_skill_payload(
        self,
        last_user_input: str = "",
        start_line: int | None = None,
    ) -> dict[str, object]:
        args: dict[str, object] = {"Path": self.skill_path}
        if start_line is not None:
            args["StartLine"] = start_line
        payload: dict[str, object] = {
            "conversationId": self.conv_id,
            "transcriptPath": str(self.transcript_file),
            "toolCall": {
                "name": "read_file",
                "args": args,
            },
        }
        if last_user_input:
            payload["lastUserInput"] = last_user_input
        return payload

    def test_extract_iteration_cap_parses_double_dash_flag_and_defaults_to_three(
        self,
    ) -> None:
        self.assertEqual(
            loop_hook.extract_iteration_cap(
                "@[.gemini/antigravity-cli/skills/loop/SKILL.md] --5 sửa 2 file ở dòng 10"
            ),
            5,
        )
        self.assertEqual(
            loop_hook.extract_iteration_cap("--2 refactor module"),
            2,
        )
        self.assertEqual(
            loop_hook.extract_iteration_cap(
                "@[.gemini/antigravity-cli/skills/loop/SKILL.md] sửa 10 lỗi trong 4 file"
            ),
            3,
        )
        self.assertEqual(
            loop_hook.extract_iteration_cap("--0 invalid zero falls back"),
            3,
        )

    def test_full_n_iteration_lifecycle_waits_for_fully_idle_and_stops_after_n(
        self,
    ) -> None:
        # Activate skill with --3 (or default 3)
        post_res = loop_hook.evaluate_post_tool_use(
            self._read_loop_skill_payload(
                last_user_input="@[.gemini/antigravity-cli/skills/loop/SKILL.md] --2 tối ưu hóa hệ thống"
            ),
            state_dir=self.state_dir,
        )
        self.assertEqual(post_res, {})
        state = loop_hook.load_loop_state(self.state_dir, self.conv_id)
        self.assertTrue(state.active)
        self.assertEqual(state.target_passes, 2)
        self.assertEqual(state.current_pass, 1)
        self.assertFalse(state.pending_inject)

        # Mid-pass stop while background command/subagent is still running (fullyIdle=False)
        stop_not_idle = loop_hook.evaluate_stop(
            {
                "conversationId": self.conv_id,
                "terminationReason": "NO_TOOL_CALL",
                "fullyIdle": False,
            },
            state_dir=self.state_dir,
        )
        self.assertEqual(stop_not_idle, {"decision": "allow"})
        state_after_not_idle = loop_hook.load_loop_state(
            self.state_dir, self.conv_id
        )
        self.assertTrue(state_after_not_idle.active)
        self.assertEqual(state_after_not_idle.current_pass, 1)
        self.assertFalse(state_after_not_idle.pending_inject)

        # Reactive wakeup PreInvocation when background task finishes -> no userMessage injected yet
        pre_wakeup = loop_hook.evaluate_pre_invocation(
            {"conversationId": self.conv_id},
            state_dir=self.state_dir,
        )
        self.assertEqual(pre_wakeup, {"injectSteps": []})

        # Pass 1 finishes completely (fullyIdle=True) -> hook blocks stop and requests continuation
        stop_pass_1 = loop_hook.evaluate_stop(
            {
                "conversationId": self.conv_id,
                "terminationReason": "NO_TOOL_CALL",
                "fullyIdle": True,
            },
            state_dir=self.state_dir,
        )
        self.assertEqual(stop_pass_1, {"decision": "continue"})
        state_after_stop_1 = loop_hook.load_loop_state(
            self.state_dir, self.conv_id
        )
        self.assertTrue(state_after_stop_1.pending_inject)
        self.assertEqual(state_after_stop_1.current_pass, 1)

        # Next PreInvocation injects the commanding userMessage and advances current_pass to 2
        pre_pass_2 = loop_hook.evaluate_pre_invocation(
            {"conversationId": self.conv_id},
            state_dir=self.state_dir,
        )
        self.assertEqual(
            pre_pass_2,
            {
                "injectSteps": [
                    {
                        "userMessage": loop_hook.LOOP_CONTINUE_USER_MESSAGE,
                    }
                ]
            },
        )
        state_in_pass_2 = loop_hook.load_loop_state(self.state_dir, self.conv_id)
        self.assertTrue(state_in_pass_2.active)
        self.assertEqual(state_in_pass_2.current_pass, 2)
        self.assertFalse(state_in_pass_2.pending_inject)

        # Agent re-reads loop/SKILL.md during pass 2 -> must NOT reset current_pass back to 1
        loop_hook.evaluate_post_tool_use(
            self._read_loop_skill_payload(
                last_user_input=loop_hook.LOOP_CONTINUE_USER_MESSAGE
            ),
            state_dir=self.state_dir,
        )
        state_after_reread = loop_hook.load_loop_state(
            self.state_dir, self.conv_id
        )
        self.assertEqual(state_after_reread.current_pass, 2)
        self.assertEqual(state_after_reread.target_passes, 2)

        # Pass 2 finishes completely (fullyIdle=True) -> reached N=2, so allow stop and deactivate
        stop_pass_2 = loop_hook.evaluate_stop(
            {
                "conversationId": self.conv_id,
                "terminationReason": "NO_TOOL_CALL",
                "fullyIdle": True,
            },
            state_dir=self.state_dir,
        )
        self.assertEqual(stop_pass_2, {"decision": "allow"})
        final_state = loop_hook.load_loop_state(self.state_dir, self.conv_id)
        self.assertFalse(final_state.active)
        self.assertEqual(final_state.current_pass, 0)
        self.assertFalse(final_state.pending_inject)

    def test_extracts_n_from_transcript_when_last_user_input_omitted_and_clears_on_cancel(
        self,
    ) -> None:
        self.transcript_file.write_text(
            json.dumps(
                {
                    "type": "USER_INPUT",
                    "source": "USER_EXPLICIT",
                    "content": "@[.gemini/antigravity-cli/skills/loop/SKILL.md] --4 kiểm tra kỹ",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        loop_hook.evaluate_post_tool_use(
            self._read_loop_skill_payload(),
            state_dir=self.state_dir,
        )
        state = loop_hook.load_loop_state(self.state_dir, self.conv_id)
        self.assertTrue(state.active)
        self.assertEqual(state.target_passes, 4)
        self.assertEqual(state.current_pass, 1)

        # User cancellation clears active loop state immediately
        cancel_res = loop_hook.evaluate_stop(
            {
                "conversationId": self.conv_id,
                "terminationReason": "USER_CANCELED",
                "fullyIdle": True,
            },
            state_dir=self.state_dir,
        )
        self.assertEqual(cancel_res, {"decision": "allow"})
        canceled_state = loop_hook.load_loop_state(self.state_dir, self.conv_id)
        self.assertFalse(canceled_state.active)

    def test_superseding_explicit_user_message_deactivates_stale_loop(
        self,
    ) -> None:
        loop_hook.evaluate_post_tool_use(
            self._read_loop_skill_payload(
                last_user_input="@[.gemini/antigravity-cli/skills/loop/SKILL.md] --3 làm task A"
            ),
            state_dir=self.state_dir,
        )
        # User sends a new unrelated message while not in pending_inject
        pre_res = loop_hook.evaluate_pre_invocation(
            {
                "conversationId": self.conv_id,
                "lastUserInput": "chuyển sang câu hỏi khác không dùng loop",
            },
            state_dir=self.state_dir,
        )
        self.assertEqual(pre_res, {"injectSteps": []})
        state = loop_hook.load_loop_state(self.state_dir, self.conv_id)
        self.assertFalse(state.active)
        stop_res = loop_hook.evaluate_stop(
            {
                "conversationId": self.conv_id,
                "terminationReason": "NO_TOOL_CALL",
                "fullyIdle": True,
            },
            state_dir=self.state_dir,
        )
        self.assertEqual(stop_res, {"decision": "allow"})

    def test_cli_entrypoints_dispatch_modes_correctly(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "stop"],
            input=json.dumps(
                {
                    "conversationId": "cli-conv",
                    "terminationReason": "NO_TOOL_CALL",
                    "fullyIdle": True,
                }
            ),
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(json.loads(proc.stdout), {"decision": "allow"})


if __name__ == "__main__":
    unittest.main()
