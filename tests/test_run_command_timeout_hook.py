import importlib.util
import json
import os
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

SCRIPT_PATH: Path = SCRIPT_DIR / "run_command_timeout_hook.py"
spec = importlib.util.spec_from_file_location("run_command_timeout_hook", SCRIPT_PATH)
assert spec is not None and spec.loader is not None
timeout_hook = importlib.util.module_from_spec(spec)
sys.modules["run_command_timeout_hook"] = timeout_hook
spec.loader.exec_module(timeout_hook)


class TestRunCommandTimeoutHook(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir: Path = Path(tempfile.mkdtemp())
        self.state_dir: Path = self.temp_dir / "state"
        self.transcript_file: Path = self.temp_dir / "transcript.jsonl"
        self.conv_id: str = "conv-timeout-test"

    def tearDown(self) -> None:
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _run_cmd_payload(
        self,
        command_line: str = "python3 -m unittest",
        wait_ms: int = 10000,
        is_daemon: bool = False,
        tool_summary: str = "Run unit tests",
        step_idx: int = 10,
    ) -> dict[str, object]:
        return {
            "conversationId": self.conv_id,
            "transcriptPath": str(self.transcript_file),
            "stepIdx": step_idx,
            "toolCall": {
                "name": "run_command",
                "args": {
                    "CommandLine": command_line,
                    "WaitMsBeforeAsync": wait_ms,
                    "IsDaemon": is_daemon,
                    "toolSummary": tool_summary,
                },
            },
        }

    def test_ignores_only_is_daemon_true_commands(self) -> None:
        daemon_payload = self._run_cmd_payload(
            command_line="npm run dev",
            is_daemon=True,
            step_idx=1,
        )
        pre_res = timeout_hook.evaluate_pre_tool_use(
            daemon_payload,
            state_dir=self.state_dir,
            now_fn=lambda: 1000.0,
        )
        self.assertEqual(pre_res, {"decision": "allow"})
        state = timeout_hook.load_timeout_state(self.state_dir, self.conv_id)
        self.assertEqual(state.tasks, ())

    def test_post_tool_use_removes_completed_command_from_tracking(self) -> None:
        payload = self._run_cmd_payload(
            command_line="rg -n 'def ' src/",
            wait_ms=10000,
            step_idx=11,
        )
        timeout_hook.evaluate_pre_tool_use(
            payload,
            state_dir=self.state_dir,
            now_fn=lambda: 100.0,
        )
        self.assertEqual(
            len(timeout_hook.load_timeout_state(self.state_dir, self.conv_id).tasks),
            1,
        )

        # Command finishes and PostToolUse fires -> task is removed
        timeout_hook.evaluate_post_tool_use(
            payload,
            state_dir=self.state_dir,
        )
        state = timeout_hook.load_timeout_state(self.state_dir, self.conv_id)
        self.assertEqual(state.tasks, ())

        pre_inv = timeout_hook.evaluate_pre_invocation(
            {"conversationId": self.conv_id},
            state_dir=self.state_dir,
            now_fn=lambda: 500.0,
        )
        self.assertEqual(pre_inv, {"injectSteps": []})

    def test_non_background_command_exceeding_five_minutes_injects_user_message_once_and_leaves_alone_after(
        self,
    ) -> None:
        self.transcript_file.write_text(
            json.dumps(
                {
                    "type": "TOOL_RESPONSE",
                    "content": "Tool is running as a background task with task id: conv-timeout-test/task-99",
                }
            )
            + "\n",
            encoding="utf-8",
        )

        payload = self._run_cmd_payload(
            command_line="pytest tests/integration",
            wait_ms=10000,
            tool_summary="Integration test suite",
            step_idx=15,
        )
        # PreToolUse fires when command starts; PostToolUse does NOT fire while backgrounded
        timeout_hook.evaluate_pre_tool_use(
            payload,
            state_dir=self.state_dir,
            now_fn=lambda: 1000.0,
        )

        current_time: list[float] = [1012.0]

        def fake_sleep(seconds: float) -> None:
            current_time[0] += seconds

        stop_res = timeout_hook.evaluate_stop(
            {
                "conversationId": self.conv_id,
                "transcriptPath": str(self.transcript_file),
                "terminationReason": "NO_TOOL_CALL",
                "fullyIdle": False,
            },
            state_dir=self.state_dir,
            now_fn=lambda: current_time[0],
            sleep_fn=fake_sleep,
            is_alive_fn=lambda _: True,
            poll_interval=100.0,
        )
        self.assertEqual(stop_res, {"decision": "continue"})
        self.assertGreaterEqual(current_time[0], 1300.0)
        self.assertTrue(
            timeout_hook.is_manage_task_authorized_for_conversation(
                self.conv_id, state_dir=self.state_dir
            )
        )

        pre_inv = timeout_hook.evaluate_pre_invocation(
            {
                "conversationId": self.conv_id,
                "transcriptPath": str(self.transcript_file),
            },
            state_dir=self.state_dir,
            now_fn=lambda: 1305.0,
        )
        inject_steps = pre_inv.get("injectSteps")
        self.assertIsInstance(inject_steps, list)
        assert isinstance(inject_steps, list)
        self.assertEqual(len(inject_steps), 1)
        user_msg = inject_steps[0].get("userMessage", "")
        self.assertIn("manage_task", user_msg)
        self.assertIn("pytest tests/integration", user_msg)
        self.assertIn("conv-timeout-test/task-99", user_msg)
        self.assertIn("5 phút 5 giây (305 giây)", user_msg)
        self.assertIn("chủ ý", user_msg)
        self.assertIn("để yên", user_msg)

        # If model decides to leave the task running and stops again (fullyIdle=False),
        # hook leaves it alone and does NOT re-trigger for the same task
        stop_again = timeout_hook.evaluate_stop(
            {
                "conversationId": self.conv_id,
                "transcriptPath": str(self.transcript_file),
                "terminationReason": "NO_TOOL_CALL",
                "fullyIdle": False,
            },
            state_dir=self.state_dir,
            now_fn=lambda: 1400.0,
            sleep_fn=fake_sleep,
            is_alive_fn=lambda _: True,
        )
        self.assertEqual(stop_again, {"decision": "allow"})

        pre_inv_again = timeout_hook.evaluate_pre_invocation(
            {
                "conversationId": self.conv_id,
                "transcriptPath": str(self.transcript_file),
            },
            state_dir=self.state_dir,
            now_fn=lambda: 1450.0,
        )
        self.assertEqual(pre_inv_again, {"injectSteps": []})

        # Once background command finishes, PostToolUse removes it from state
        timeout_hook.evaluate_post_tool_use(
            payload,
            state_dir=self.state_dir,
        )
        final_state = timeout_hook.load_timeout_state(self.state_dir, self.conv_id)
        self.assertEqual(final_state.tasks, ())
        self.assertFalse(final_state.manage_task_authorized)

    def test_stop_releases_early_when_background_process_exits_before_five_minutes(
        self,
    ) -> None:
        payload = self._run_cmd_payload(
            command_line="python3 build.py",
            wait_ms=10000,
            step_idx=20,
        )
        timeout_hook.evaluate_pre_tool_use(
            payload,
            state_dir=self.state_dir,
            now_fn=lambda: 2000.0,
        )

        current_time: list[float] = [2012.0]

        def fake_sleep(seconds: float) -> None:
            current_time[0] += seconds

        stop_res = timeout_hook.evaluate_stop(
            {
                "conversationId": self.conv_id,
                "terminationReason": "NO_TOOL_CALL",
                "fullyIdle": False,
            },
            state_dir=self.state_dir,
            now_fn=lambda: current_time[0],
            sleep_fn=fake_sleep,
            is_alive_fn=lambda _: current_time[0] < 2040.0,
            poll_interval=10.0,
        )
        self.assertEqual(stop_res, {"decision": "allow"})
        self.assertLess(current_time[0], 2300.0)
        state = timeout_hook.load_timeout_state(self.state_dir, self.conv_id)
        self.assertEqual(state.tasks, ())

    def test_cli_modes_and_env_state_dir(self) -> None:
        env = os.environ.copy()
        env["AGY_RUN_CMD_TIMEOUT_STATE_DIR"] = str(self.state_dir)

        proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "pre_tool_use"],
            input=json.dumps(self._run_cmd_payload(command_line="pytest -k slow")),
            text=True,
            capture_output=True,
            env=env,
            check=True,
        )
        self.assertEqual(json.loads(proc.stdout), {"decision": "allow"})

    def test_command_match_needles_matches_shell_unquoted_ps_args(self) -> None:
        cmd = 'python3 -c "import time; time.sleep(330)"'
        needles = timeout_hook._command_match_needles(cmd)
        ps_args = "/usr/bin/python3 -c import time; time.sleep(330)"
        self.assertTrue(any(n in ps_args for n in needles))


if __name__ == "__main__":
    unittest.main()
