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
    def test_non_daemon_run_command_overwrites_wait_to_10000(self) -> None:
        res_with_smaller_wait = evaluate_run_command_wait(
            {
                "name": "run_command",
                "args": {
                    "CommandLine": "pytest",
                    "WaitMsBeforeAsync": 500,
                },
            }
        )
        self.assertEqual(
            res_with_smaller_wait,
            {
                "decision": "allow",
                "overwrite": {"WaitMsBeforeAsync": 10000},
            },
        )

        res_missing_wait = evaluate_run_command_wait(
            {
                "name": "run_command",
                "args": {
                    "CommandLine": "pytest",
                    "IsDaemon": False,
                },
            }
        )
        self.assertEqual(
            res_missing_wait,
            {
                "decision": "allow",
                "overwrite": {"WaitMsBeforeAsync": 10000},
            },
        )

    def test_daemon_run_command_overwrites_wait_to_500(self) -> None:
        res_with_larger_wait = evaluate_run_command_wait(
            {
                "name": "run_command",
                "args": {
                    "CommandLine": "npm run dev",
                    "IsDaemon": True,
                    "WaitMsBeforeAsync": 10000,
                },
            }
        )
        self.assertEqual(
            res_with_larger_wait,
            {
                "decision": "allow",
                "overwrite": {"WaitMsBeforeAsync": 500},
            },
        )

        res_missing_wait = evaluate_run_command_wait(
            {
                "name": "run_command",
                "args": {
                    "CommandLine": "npm run dev",
                    "IsDaemon": True,
                },
            }
        )
        self.assertEqual(
            res_missing_wait,
            {
                "decision": "allow",
                "overwrite": {"WaitMsBeforeAsync": 500},
            },
        )

    def test_matching_wait_non_run_command_and_non_int_types(self) -> None:
        self.assertEqual(
            evaluate_run_command_wait(
                {
                    "name": "run_command",
                    "args": {"CommandLine": "ls", "WaitMsBeforeAsync": 10000},
                }
            ),
            {"decision": "allow"},
        )
        self.assertEqual(
            evaluate_run_command_wait(
                {
                    "name": "run_command",
                    "args": {
                        "CommandLine": "npm run dev",
                        "IsDaemon": True,
                        "WaitMsBeforeAsync": 500,
                    },
                }
            ),
            {"decision": "allow"},
        )
        self.assertEqual(
            evaluate_run_command_wait(
                {"name": "read_file", "args": {"Path": "/tmp/a.py"}}
            ),
            {"decision": "allow"},
        )
        self.assertEqual(
            evaluate_run_command_wait(
                {
                    "name": "run_command",
                    "args": {"CommandLine": "ls", "WaitMsBeforeAsync": "10000"},
                }
            ),
            {
                "decision": "allow",
                "overwrite": {"WaitMsBeforeAsync": 10000},
            },
        )

    def test_cli_stdin_stdout_contract(self) -> None:
        payload = {
            "toolCall": {
                "name": "run_command",
                "args": {
                    "CommandLine": "npm run dev",
                    "IsDaemon": True,
                    "WaitMsBeforeAsync": 10000,
                },
            }
        }
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(
            json.loads(proc.stdout),
            {
                "decision": "allow",
                "overwrite": {"WaitMsBeforeAsync": 500},
            },
        )

        malformed = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            input="{not-json",
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(json.loads(malformed.stdout), {"decision": "allow"})


if __name__ == "__main__":
    unittest.main()
