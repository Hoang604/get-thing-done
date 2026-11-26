import json
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT_DIR: Path = Path(__file__).resolve().parent.parent / ".gemini" / "config" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_command_wait_hook import evaluate_run_command_wait

SCRIPT_PATH: Path = SCRIPT_DIR / "run_command_wait_hook.py"


class TestRunCommandWaitHook(unittest.TestCase):
    def test_non_daemon_overwrites_wait_and_defaults_notification_timeout(self) -> None:
        expected = {
            "decision": "allow",
            "overwrite": {
                "WaitMsBeforeAsync": 10000,
                "NotificationTimeoutSeconds": 60,
            },
        }
        for args in (
            {"CommandLine": "pytest", "WaitMsBeforeAsync": 500},
            {"CommandLine": "pytest", "IsDaemon": False},
            {"CommandLine": "pytest", "IsDaemon": "true", "WaitMsBeforeAsync": 500},
        ):
            with self.subTest(args=args):
                self.assertEqual(
                    evaluate_run_command_wait({"name": "run_command", "args": args}),
                    expected,
                )

    def test_non_daemon_with_matching_wait_only_overwrites_missing_timeout(self) -> None:
        res = evaluate_run_command_wait(
            {
                "name": "run_command",
                "args": {"CommandLine": "ls", "WaitMsBeforeAsync": 10000},
            }
        )
        self.assertEqual(
            res,
            {
                "decision": "allow",
                "overwrite": {"NotificationTimeoutSeconds": 60},
            },
        )

    def test_non_daemon_preserves_positive_notification_timeout(self) -> None:
        self.assertEqual(
            evaluate_run_command_wait(
                {
                    "name": "run_command",
                    "args": {
                        "CommandLine": "ls",
                        "WaitMsBeforeAsync": 10000,
                        "NotificationTimeoutSeconds": 1,
                    },
                }
            ),
            {"decision": "allow"},
        )
        self.assertEqual(
            evaluate_run_command_wait(
                {
                    "name": "run_command",
                    "args": {
                        "CommandLine": "pytest",
                        "WaitMsBeforeAsync": 500,
                        "NotificationTimeoutSeconds": 120,
                    },
                }
            ),
            {
                "decision": "allow",
                "overwrite": {"WaitMsBeforeAsync": 10000},
            },
        )

    def test_non_daemon_overwrites_invalid_wait_and_invalid_timeout_values(self) -> None:
        for invalid_wait in (10000.0, "10000"):
            with self.subTest(invalid_wait=invalid_wait):
                self.assertEqual(
                    evaluate_run_command_wait(
                        {
                            "name": "run_command",
                            "args": {
                                "CommandLine": "ls",
                                "WaitMsBeforeAsync": invalid_wait,
                                "NotificationTimeoutSeconds": 30,
                            },
                        }
                    ),
                    {
                        "decision": "allow",
                        "overwrite": {"WaitMsBeforeAsync": 10000},
                    },
                )

        for invalid_timeout in (None, True, False, 0, -5, 30.0, "60"):
            with self.subTest(invalid_timeout=invalid_timeout):
                self.assertEqual(
                    evaluate_run_command_wait(
                        {
                            "name": "run_command",
                            "args": {
                                "CommandLine": "ls",
                                "WaitMsBeforeAsync": 10000,
                                "NotificationTimeoutSeconds": invalid_timeout,
                            },
                        }
                    ),
                    {
                        "decision": "allow",
                        "overwrite": {"NotificationTimeoutSeconds": 60},
                    },
                )

    def test_daemon_normalizes_wait_and_never_injects_notification_timeout(self) -> None:
        for args in (
            {"CommandLine": "npm run dev", "IsDaemon": True, "WaitMsBeforeAsync": 10000},
            {"CommandLine": "npm run dev", "IsDaemon": True},
        ):
            with self.subTest(args=args):
                self.assertEqual(
                    evaluate_run_command_wait({"name": "run_command", "args": args}),
                    {
                        "decision": "allow",
                        "overwrite": {"WaitMsBeforeAsync": 500},
                    },
                )

        for args in (
            {"CommandLine": "npm run dev", "IsDaemon": True, "WaitMsBeforeAsync": 500},
            {
                "CommandLine": "npm run dev",
                "IsDaemon": True,
                "WaitMsBeforeAsync": 500,
                "NotificationTimeoutSeconds": 0,
            },
            {
                "CommandLine": "npm run dev",
                "IsDaemon": True,
                "WaitMsBeforeAsync": 500,
                "NotificationTimeoutSeconds": 30,
            },
        ):
            with self.subTest(args=args):
                self.assertEqual(
                    evaluate_run_command_wait({"name": "run_command", "args": args}),
                    {"decision": "allow"},
                )

    def test_e2e_non_daemon_defaults_notification_timeout_to_600(self) -> None:
        self.assertEqual(
            evaluate_run_command_wait(
                {
                    "name": "run_command",
                    "args": {
                        "CommandLine": "npm run test:e2e",
                        "WaitMsBeforeAsync": 500,
                    },
                }
            ),
            {
                "decision": "allow",
                "overwrite": {
                    "WaitMsBeforeAsync": 10000,
                    "NotificationTimeoutSeconds": 600,
                },
            },
        )
        self.assertEqual(
            evaluate_run_command_wait(
                {
                    "name": "run_command",
                    "args": {
                        "CommandLine": "pytest -m E2E",
                        "WaitMsBeforeAsync": 10000,
                    },
                }
            ),
            {
                "decision": "allow",
                "overwrite": {"NotificationTimeoutSeconds": 600},
            },
        )
        self.assertEqual(
            evaluate_run_command_wait(
                {
                    "name": "run_command",
                    "args": {
                        "CommandLine": "npx playwright test e2e",
                        "WaitMsBeforeAsync": 10000,
                        "NotificationTimeoutSeconds": 120,
                    },
                }
            ),
            {"decision": "allow"},
        )
        self.assertEqual(
            evaluate_run_command_wait(
                {
                    "name": "run_command",
                    "args": {
                        "CommandLine": "npm run dev:e2e-mock",
                        "IsDaemon": True,
                        "WaitMsBeforeAsync": 500,
                    },
                }
            ),
            {"decision": "allow"},
        )
        for args in (
            {"WaitMsBeforeAsync": 10000},
            {"CommandLine": 123, "WaitMsBeforeAsync": 10000},
        ):
            with self.subTest(args=args):
                self.assertEqual(
                    evaluate_run_command_wait({"name": "run_command", "args": args}),
                    {
                        "decision": "allow",
                        "overwrite": {"NotificationTimeoutSeconds": 60},
                    },
                )

    def test_non_run_command_and_invalid_tool_call_shapes_allow_unchanged(self) -> None:
        for tool_call in (
            {"name": "read_file", "args": {"Path": "/tmp/a.py"}},
            {"args": {"CommandLine": "ls"}},
            {"name": "run_command", "args": None},
            {"name": "run_command"},
        ):
            with self.subTest(tool_call=tool_call):
                self.assertEqual(
                    evaluate_run_command_wait(tool_call),
                    {"decision": "allow"},
                )

    def test_cli_stdin_stdout_contract(self) -> None:
        non_daemon_payload = {
            "toolCall": {
                "name": "run_command",
                "args": {
                    "CommandLine": "pytest",
                    "WaitMsBeforeAsync": 500,
                },
            }
        }
        non_daemon_proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            input=json.dumps(non_daemon_payload),
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(
            json.loads(non_daemon_proc.stdout),
            {
                "decision": "allow",
                "overwrite": {
                    "WaitMsBeforeAsync": 10000,
                    "NotificationTimeoutSeconds": 60,
                },
            },
        )

        daemon_payload = {
            "toolCall": {
                "name": "run_command",
                "args": {
                    "CommandLine": "npm run dev",
                    "IsDaemon": True,
                    "WaitMsBeforeAsync": 10000,
                },
            }
        }
        daemon_proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            input=json.dumps(daemon_payload),
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(
            json.loads(daemon_proc.stdout),
            {
                "decision": "allow",
                "overwrite": {"WaitMsBeforeAsync": 500},
            },
        )

        for raw_input in ("{not-json", "", "[1, 2]", "{}"):
            with self.subTest(raw_input=raw_input):
                proc = subprocess.run(
                    [sys.executable, str(SCRIPT_PATH)],
                    input=raw_input,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                self.assertEqual(json.loads(proc.stdout), {"decision": "allow"})


if __name__ == "__main__":
    unittest.main()
