import json
import os
import stat
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

from rtk_rewrite_hook import evaluate_rtk_rewrite

SCRIPT_PATH: Path = SCRIPT_DIR / "rtk_rewrite_hook.py"


class TestRtkRewriteHook(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.fake_rtk = Path(self.temp_dir.name) / "rtk"
        self.fake_rtk.write_text(
            "#!/bin/sh\n"
            'if [ "$1" = "rewrite" ]; then\n'
            '  case "$2" in\n'
            '    "git status")\n'
            '      echo "rtk git status"\n'
            "      exit 0\n"
            "      ;;\n"
            '    "git log -n 5")\n'
            '      echo "rtk git log -n 5"\n'
            "      exit 3\n"
            "      ;;\n"
            '    "rg -n foo src/")\n'
            '      echo "rtk rg -n foo src/"\n'
            "      exit 0\n"
            "      ;;\n"
            '    "rg -n foo src/ && git status")\n'
            '      echo "rtk rg -n foo src/ && rtk git status"\n'
            "      exit 0\n"
            "      ;;\n"
            '    "echo hello")\n'
            "      exit 1\n"
            "      ;;\n"
            '    "rm -rf /")\n'
            "      exit 2\n"
            "      ;;\n"
            "  esac\n"
            "fi\n"
            "exit 1\n",
            encoding="utf-8",
        )
        self.fake_rtk.chmod(self.fake_rtk.stat().st_mode | stat.S_IEXEC)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_rewrites_when_rtk_exits_0(self) -> None:
        res = evaluate_rtk_rewrite(
            {"name": "run_command", "args": {"CommandLine": "git status"}},
            rtk_bin=str(self.fake_rtk),
        )
        self.assertEqual(
            res,
            {
                "decision": "allow",
                "overwrite": {"CommandLine": "rtk git status"},
            },
        )

    def test_rewrites_when_rtk_exits_3(self) -> None:
        res = evaluate_rtk_rewrite(
            {"name": "run_command", "args": {"CommandLine": "git log -n 5"}},
            rtk_bin=str(self.fake_rtk),
        )
        self.assertEqual(
            res,
            {
                "decision": "allow",
                "overwrite": {"CommandLine": "rtk git log -n 5"},
            },
        )

    def test_passes_through_when_rtk_exits_1_or_2(self) -> None:
        for cmd in ("echo hello", "rm -rf /"):
            res = evaluate_rtk_rewrite(
                {"name": "run_command", "args": {"CommandLine": cmd}},
                rtk_bin=str(self.fake_rtk),
            )
            self.assertEqual(res, {"decision": "allow"})

    def test_excludes_rg_from_rtk_wrapping(self) -> None:
        res_single = evaluate_rtk_rewrite(
            {"name": "run_command", "args": {"CommandLine": "rg -n foo src/"}},
            rtk_bin=str(self.fake_rtk),
        )
        self.assertEqual(res_single, {"decision": "allow"})

        res_compound = evaluate_rtk_rewrite(
            {
                "name": "run_command",
                "args": {"CommandLine": "rg -n foo src/ && git status"},
            },
            rtk_bin=str(self.fake_rtk),
        )
        self.assertEqual(
            res_compound,
            {
                "decision": "allow",
                "overwrite": {"CommandLine": "rg -n foo src/ && rtk git status"},
            },
        )

    def test_passes_through_for_other_tools_or_missing_binary(self) -> None:
        res_other_tool = evaluate_rtk_rewrite(
            {"name": "read_file", "args": {"Path": "/tmp/a.py"}},
            rtk_bin=str(self.fake_rtk),
        )
        self.assertEqual(res_other_tool, {"decision": "allow"})

        res_missing_bin = evaluate_rtk_rewrite(
            {"name": "run_command", "args": {"CommandLine": "git status"}},
            rtk_bin="/nonexistent/rtk",
        )
        self.assertEqual(res_missing_bin, {"decision": "allow"})

    def test_cli_stdin_stdout_contract(self) -> None:
        payload = {
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "git status"},
            }
        }
        env = dict(os.environ)
        env["PATH"] = f"{self.temp_dir.name}:{env.get('PATH', '')}"
        proc = subprocess.Popen(
            [sys.executable, str(SCRIPT_PATH)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            env=env,
        )
        out, _ = proc.communicate(json.dumps(payload))
        self.assertEqual(
            json.loads(out),
            {
                "decision": "allow",
                "overwrite": {"CommandLine": "rtk git status"},
            },
        )


if __name__ == "__main__":
    unittest.main()
