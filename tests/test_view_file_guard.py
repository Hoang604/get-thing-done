import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH: Path = (
    Path(__file__).resolve().parent.parent
    / ".gemini"
    / "config"
    / "scripts"
    / "view_file_guard.py"
)


class TestViewFileGuard(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir: str = tempfile.mkdtemp()
        self.cache_dir: str = os.path.join(self.temp_dir, "cache")
        os.makedirs(self.cache_dir, exist_ok=True)

    def tearDown(self) -> None:
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _run_guard(self, payload: dict[str, object], cache_dir: str) -> dict[str, object]:
        env = dict(os.environ)
        cmd = [
            sys.executable,
            "-c",
            f"""
import sys
from pathlib import Path
import view_file_guard

view_file_guard.CACHE_DIR = Path({json.dumps(cache_dir)})
view_file_guard.main()
""",
        ]
        p = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(SCRIPT_PATH.parent),
            env=env,
        )
        out, err = p.communicate(json.dumps(payload))
        self.assertEqual(p.returncode, 0, f"Guard failed: {err}")
        result: dict[str, object] = json.loads(out)
        return result

    def test_first_read_small_file_overwrites_full_range(self) -> None:
        test_file: str = os.path.join(self.temp_dir, "small.py")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("\n".join(f"line {i}" for i in range(1, 101)))

        payload: dict[str, object] = {
            "conversationId": "conv-test-1",
            "toolCall": {
                "name": "view_file",
                "args": {
                    "AbsolutePath": test_file,
                    "StartLine": 20,
                    "EndLine": 30,
                },
            },
        }

        res = self._run_guard(payload, self.cache_dir)
        self.assertEqual(res.get("decision"), "allow")
        overwrite = res.get("overwrite")
        self.assertIsInstance(overwrite, dict)
        if isinstance(overwrite, dict):
            self.assertEqual(overwrite.get("StartLine"), 1)
            self.assertEqual(overwrite.get("EndLine"), 100)

    def test_subsequent_read_preserves_exact_slice(self) -> None:
        test_file: str = os.path.join(self.temp_dir, "small.py")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("\n".join(f"line {i}" for i in range(1, 101)))

        payload: dict[str, object] = {
            "conversationId": "conv-test-2",
            "toolCall": {
                "name": "view_file",
                "args": {
                    "AbsolutePath": test_file,
                    "StartLine": 20,
                    "EndLine": 30,
                },
            },
        }

        # First read expands
        res1 = self._run_guard(payload, self.cache_dir)
        self.assertIn("overwrite", res1)

        # Second read in same conversation keeps original slice
        res2 = self._run_guard(payload, self.cache_dir)
        self.assertEqual(res2.get("decision"), "allow")
        self.assertNotIn("overwrite", res2)

    def test_first_read_large_file_expands_narrow_slice(self) -> None:
        large_file: str = os.path.join(self.temp_dir, "large.py")
        with open(large_file, "w", encoding="utf-8") as f:
            f.write("\n".join(f"line {i}" for i in range(1, 1201)))

        payload: dict[str, object] = {
            "conversationId": "conv-test-3",
            "toolCall": {
                "name": "view_file",
                "args": {
                    "AbsolutePath": large_file,
                    "StartLine": 300,
                    "EndLine": 320,
                },
            },
        }

        res = self._run_guard(payload, self.cache_dir)
        self.assertEqual(res.get("decision"), "allow")
        overwrite = res.get("overwrite")
        self.assertIsInstance(overwrite, dict)
        if isinstance(overwrite, dict):
            self.assertEqual(overwrite.get("StartLine"), 250)
            self.assertEqual(overwrite.get("EndLine"), 650)


if __name__ == "__main__":
    unittest.main()
