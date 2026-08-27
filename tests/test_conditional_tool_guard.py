import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parent.parent / ".gemini" / "config" / "scripts" / "conditional_tool_guard.py"


class TestConditionalToolGuard(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.transcript_file = os.path.join(self.temp_dir, "transcript.jsonl")

    def tearDown(self):
        if os.path.exists(self.transcript_file):
            os.remove(self.transcript_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def _run_guard(self, payload: dict) -> dict:
        p = subprocess.Popen(
            [sys.executable, str(SCRIPT_PATH)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True
        )
        out, _ = p.communicate(json.dumps(payload))
        return json.loads(out)

    def test_manage_task_denied_when_not_in_user_prompt(self):
        with open(self.transcript_file, "w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "USER_INPUT", "content": "Please inspect background processes"}) + "\n")

        res = self._run_guard({
            "toolCall": {"name": "manage_task"},
            "transcriptPath": self.transcript_file
        })
        self.assertEqual(res.get("decision"), "deny")
        self.assertIn("manage_task", res.get("reason", ""))

    def test_manage_task_allowed_when_explicitly_in_user_prompt(self):
        with open(self.transcript_file, "w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "USER_INPUT", "content": "Please use manage_task to list tasks"}) + "\n")

        res = self._run_guard({
            "toolCall": {"name": "manage_task"},
            "transcriptPath": self.transcript_file
        })
        self.assertEqual(res.get("decision"), "allow")

    def test_schedule_denied_when_not_in_user_prompt(self):
        with open(self.transcript_file, "w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "USER_INPUT", "content": "Please use manage_task to list tasks"}) + "\n")

        res = self._run_guard({
            "toolCall": {"name": "schedule"},
            "transcriptPath": self.transcript_file
        })
        self.assertEqual(res.get("decision"), "deny")
        self.assertIn("schedule", res.get("reason", ""))

    def test_schedule_allowed_when_explicitly_in_user_prompt(self):
        with open(self.transcript_file, "w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "USER_INPUT", "content": "schedule a reminder in 10 minutes"}) + "\n")

        res = self._run_guard({
            "toolCall": {"name": "schedule"},
            "transcriptPath": self.transcript_file
        })
        self.assertEqual(res.get("decision"), "allow")

    def test_word_boundary_prevents_partial_match(self):
        with open(self.transcript_file, "w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "USER_INPUT", "content": "rescheduled the event and mismanage_tasks"}) + "\n")

        res_schedule = self._run_guard({
            "toolCall": {"name": "schedule"},
            "transcriptPath": self.transcript_file
        })
        self.assertEqual(res_schedule.get("decision"), "deny")

        res_manage = self._run_guard({
            "toolCall": {"name": "manage_task"},
            "transcriptPath": self.transcript_file
        })
        self.assertEqual(res_manage.get("decision"), "deny")


if __name__ == "__main__":
    unittest.main()
