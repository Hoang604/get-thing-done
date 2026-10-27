import json
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT_DIR: Path = Path(__file__).resolve().parent.parent / ".gemini" / "config" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from read_file_widener import evaluate_read_file_widener

SCRIPT_PATH: Path = SCRIPT_DIR / "read_file_widener.py"


class TestReadFileWidener(unittest.TestCase):
    def test_full_file_read_is_not_modified(self) -> None:
        res = evaluate_read_file_widener(
            {"name": "read_file", "args": {"Path": "/tmp/a.py"}}
        )
        self.assertEqual(res, {"decision": "allow"})

    def test_slice_read_widens_by_minus_10_and_plus_10(self) -> None:
        res = evaluate_read_file_widener(
            {
                "name": "read_file",
                "args": {"Path": "/tmp/a.py", "StartLine": 50, "EndLine": 100},
            }
        )
        self.assertEqual(
            res,
            {
                "decision": "allow",
                "overwrite": {"StartLine": 40, "EndLine": 110},
            },
        )

    def test_start_line_clamps_at_1_and_omits_unchanged_key(self) -> None:
        res_clamped = evaluate_read_file_widener(
            {
                "name": "read_file",
                "args": {"Path": "/tmp/a.py", "StartLine": 5, "EndLine": 20},
            }
        )
        self.assertEqual(
            res_clamped,
            {
                "decision": "allow",
                "overwrite": {"StartLine": 1, "EndLine": 30},
            },
        )

        res_already_one = evaluate_read_file_widener(
            {
                "name": "read_file",
                "args": {"Path": "/tmp/a.py", "StartLine": 1, "EndLine": 20},
            }
        )
        self.assertEqual(
            res_already_one,
            {
                "decision": "allow",
                "overwrite": {"EndLine": 30},
            },
        )

    def test_respects_800_line_per_read_cap(self) -> None:
        res = evaluate_read_file_widener(
            {
                "name": "read_file",
                "args": {"Path": "/tmp/a.py", "StartLine": 15, "EndLine": 800},
            }
        )
        self.assertEqual(
            res,
            {
                "decision": "allow",
                "overwrite": {"StartLine": 5, "EndLine": 804},
            },
        )

    def test_cli_stdin_stdout_contract(self) -> None:
        payload = {
            "toolCall": {
                "name": "read_file",
                "args": {"Path": "/tmp/a.py", "StartLine": 30, "EndLine": 40},
            }
        }
        proc = subprocess.Popen(
            [sys.executable, str(SCRIPT_PATH)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
        )
        out, _ = proc.communicate(json.dumps(payload))
        self.assertEqual(
            json.loads(out),
            {
                "decision": "allow",
                "overwrite": {"StartLine": 20, "EndLine": 50},
            },
        )


if __name__ == "__main__":
    unittest.main()
