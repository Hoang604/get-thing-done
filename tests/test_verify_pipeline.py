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


class TestVerifyPipelineDeterministic(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        patterns_source = SCRIPT_DIR / "verify_patterns.json"
        self.patterns_path = os.path.join(self.temp_dir, "verify_patterns.json")
        shutil.copyfile(patterns_source, self.patterns_path)

        self.recorder = VerifyRecorder(patterns_file_path=self.patterns_path, cache_dir=self.temp_dir)
        self.injector = VerifyInjector(cache_dir=self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_deterministic_exit_code_zero_with_error_words_passes(self):
        """Commands that output words like 'error' or 'fail' but exit with code 0 must NOT be marked as failed."""
        transcript_file = os.path.join(self.temp_dir, "transcript.jsonl")
        step_idx = 100
        step_entry = {
            "step_index": step_idx,
            "type": "RUN_COMMAND",
            "status": "DONE",
            "content": "The command exited with code 0.\nOutput:\n[WARN] 0 error found. Compiled with 2 warnings (failed assertions: 0)."
        }
        with open(transcript_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(step_entry) + "\n")

        payload = {
            "conversationId": "conv-zero-pass",
            "stepIdx": step_idx,
            "transcriptPath": transcript_file,
            "toolCall": {"name": "run_command", "args": {"CommandLine": "pnpm --filter @vas/fe-store run build"}},
            "error": None
        }
        res = self.recorder.record_if_failed(payload)
        self.assertIsNone(res, "Command with exit code 0 must not trigger failure incident")

    def test_deterministic_async_task_running_passes(self):
        """Async background task in RUNNING state must not trigger failure."""
        transcript_file = os.path.join(self.temp_dir, "transcript_async.jsonl")
        step_idx = 101
        step_entry = {
            "step_index": step_idx,
            "type": "RUN_COMMAND",
            "status": "RUNNING",
            "content": "Tool is running as a background task with task id: task-101"
        }
        with open(transcript_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(step_entry) + "\n")

        payload = {
            "conversationId": "conv-async-running",
            "stepIdx": step_idx,
            "transcriptPath": transcript_file,
            "toolCall": {"name": "run_command", "args": {"CommandLine": "pnpm --filter @vas/fe-store run build"}},
            "error": None
        }
        res = self.recorder.record_if_failed(payload)
        self.assertIsNone(res, "Async task in RUNNING state must not be captured as failure")

    def test_deterministic_exit_code_nonzero_captured(self):
        """Commands that exit with non-zero exit code must be captured as failure."""
        transcript_file = os.path.join(self.temp_dir, "transcript_fail.jsonl")
        step_idx = 102
        step_entry = {
            "step_index": step_idx,
            "type": "RUN_COMMAND",
            "status": "DONE",
            "content": "The command exited with code 1.\nOutput:\nType error in src/index.ts"
        }
        with open(transcript_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(step_entry) + "\n")

        payload = {
            "conversationId": "conv-nonzero-fail",
            "stepIdx": step_idx,
            "transcriptPath": transcript_file,
            "toolCall": {"name": "run_command", "args": {"CommandLine": "pnpm --filter @vas/fe-store run build"}},
            "error": "exit status 1"
        }
        res = self.recorder.record_if_failed(payload)
        self.assertIsNotNone(res, "Command with exit code 1 must be captured as failure")

    def test_manifest_introspection_and_clean_injector_flow(self):
        pkg_dir = os.path.join(self.temp_dir, "my-app")
        os.makedirs(pkg_dir, exist_ok=True)
        pkg_json = {
            "name": "my-app",
            "scripts": {
                "type-check": "tsc --noEmit",
                "ci-verify": "vitest run --coverage"
            }
        }
        with open(os.path.join(pkg_dir, "package.json"), "w", encoding="utf-8") as f:
            json.dump(pkg_json, f)

        conv_id = "conv-manifest-det"
        payload = {
            "conversationId": conv_id,
            "stepIdx": 200,
            "toolCall": {"name": "run_command", "args": {"CommandLine": "pnpm run type-check", "Cwd": pkg_dir}},
            "error": "exit status 2"
        }
        incident_file = self.recorder.record_if_failed(payload)
        self.assertIsNotNone(incident_file)
        self.assertTrue(os.path.exists(incident_file))

        # First injector call -> returns instruction & deletes file
        steps = self.injector.generate_instruction(conv_id)
        self.assertEqual(len(steps), 1)
        self.assertIn("CRITICAL VERIFICATION FAILURE DETECTED", steps[0]["ephemeralMessage"])
        self.assertFalse(os.path.exists(incident_file))

        # Subsequent call -> returns empty
        steps_2 = self.injector.generate_instruction(conv_id)
        self.assertEqual(len(steps_2), 0)


if __name__ == "__main__":
    unittest.main()
