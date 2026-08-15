import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Add script path to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent.parent / ".gemini" / "config" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from verify_recorder import VerifyRecorder
from verify_injector import VerifyInjector


class TestVerifyPipeline(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.patterns_path = os.path.join(self.temp_dir, "verify_patterns.json")
        patterns_data = {
            "runners": [
                {
                    "name": "pytest",
                    "command_regex": "^(uv\\s+run\\s+)?pytest(\\s+.*)?$",
                    "failure_signatures": ["FAILED", "ERROR"]
                },
                {
                    "name": "npm",
                    "command_regex": "^npm\\s+test(\\s+.*)?$",
                    "failure_signatures": ["FAIL", "ERR!"]
                }
            ]
        }
        with open(self.patterns_path, "w", encoding="utf-8") as f:
            json.dump(patterns_data, f)

        self.recorder = VerifyRecorder(patterns_file_path=self.patterns_path, cache_dir=self.temp_dir)
        self.injector = VerifyInjector(cache_dir=self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_recorder_ignores_non_verify_command(self):
        payload = {
            "conversationId": "conv-1",
            "toolCall": {"name": "run_command", "args": {"CommandLine": "git status"}},
            "error": "some error"
        }
        res = self.recorder.record_if_failed(payload)
        self.assertIsNone(res)
        incident_file = os.path.join(self.temp_dir, "agy_incident_conv-1.json")
        self.assertFalse(os.path.exists(incident_file))

    def test_recorder_ignores_successful_verify_command(self):
        payload = {
            "conversationId": "conv-2",
            "toolCall": {"name": "run_command", "args": {"CommandLine": "pytest tests/"}},
            "error": None
        }
        res = self.recorder.record_if_failed(payload)
        self.assertIsNone(res)
        incident_file = os.path.join(self.temp_dir, "agy_incident_conv-2.json")
        self.assertFalse(os.path.exists(incident_file))

    def test_recorder_and_injector_pipeline_flow(self):
        conv_id = "conv-test-3"
        # 1. Failed pytest command recorded
        payload = {
            "conversationId": conv_id,
            "stepIdx": 12,
            "toolCall": {"name": "run_command", "args": {"CommandLine": "uv run pytest"}},
            "error": "exit status 1"
        }
        incident_file = self.recorder.record_if_failed(payload)
        self.assertIsNotNone(incident_file)
        self.assertTrue(os.path.exists(incident_file))

        with open(incident_file, "r") as f:
            data = json.load(f)
        self.assertEqual(data["runnerName"], "pytest")
        self.assertFalse(data["acknowledged"])

        # 2. Injector generates instruction on next PreInvocation
        steps = self.injector.generate_instruction(conv_id)
        self.assertEqual(len(steps), 1)
        msg = steps[0]["ephemeralMessage"]
        self.assertIn("CRITICAL VERIFICATION FAILURE DETECTED", msg)
        self.assertIn("uv run pytest", msg)

        # 3. Cache marked as acknowledged
        with open(incident_file, "r") as f:
            data = json.load(f)
        self.assertTrue(data["acknowledged"])

        # 4. Subsequent PreInvocation yields empty injectSteps (no duplication)
        subsequent_steps = self.injector.generate_instruction(conv_id)
        self.assertEqual(len(subsequent_steps), 0)


if __name__ == "__main__":
    unittest.main()
