import json
import os
import shutil
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
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

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

    def test_allowed_when_md_file_read_contains_keyword(self):
        skill_file = os.path.join(self.temp_dir, "SKILL.md")
        with open(skill_file, "w", encoding="utf-8") as f:
            f.write("# Skill\nIn the same turn, call `schedule` with: 300s\n")

        with open(self.transcript_file, "w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "USER_INPUT", "content": "run the audit skill"}) + "\n")
            f.write(json.dumps({
                "type": "PLANNER_RESPONSE",
                "tool_calls": [{"name": "view_file", "args": {"AbsolutePath": skill_file}}]
            }) + "\n")

        res = self._run_guard({
            "toolCall": {"name": "schedule"},
            "transcriptPath": self.transcript_file
        })
        self.assertEqual(res.get("decision"), "allow")

    def test_denied_when_non_md_file_read_contains_keyword(self):
        code_file = os.path.join(self.temp_dir, "job.py")
        with open(code_file, "w", encoding="utf-8") as f:
            f.write("def schedule_job(): pass\n# schedule task here\n")

        with open(self.transcript_file, "w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "USER_INPUT", "content": "inspect job runner"}) + "\n")
            f.write(json.dumps({
                "type": "PLANNER_RESPONSE",
                "tool_calls": [{"name": "view_file", "args": {"AbsolutePath": code_file}}]
            }) + "\n")

        res = self._run_guard({
            "toolCall": {"name": "schedule"},
            "transcriptPath": self.transcript_file
        })
        self.assertEqual(res.get("decision"), "deny")

    def test_denied_when_md_file_read_in_previous_turn_only(self):
        skill_file = os.path.join(self.temp_dir, "old_skill.md")
        with open(skill_file, "w", encoding="utf-8") as f:
            f.write("# Instructions\nPlease call `schedule` for budget.\n")

        # Turn 1: user asked, skill read
        # Turn 2: user asks unrelated task
        with open(self.transcript_file, "w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "USER_INPUT", "content": "turn 1 request"}) + "\n")
            f.write(json.dumps({
                "type": "PLANNER_RESPONSE",
                "tool_calls": [{"name": "view_file", "args": {"AbsolutePath": skill_file}}]
            }) + "\n")
            f.write(json.dumps({"type": "USER_INPUT", "content": "turn 2: check git status now"}) + "\n")

        res = self._run_guard({
            "toolCall": {"name": "schedule"},
            "transcriptPath": self.transcript_file
        })
        self.assertEqual(res.get("decision"), "deny")

    def test_allowed_when_user_prompt_references_md_file_with_keyword(self):
        doc_file = os.path.join(self.temp_dir, "guide.md")
        with open(doc_file, "w", encoding="utf-8") as f:
            f.write("Always use manage_task to monitor jobs.")

        with open(self.transcript_file, "w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "USER_INPUT", "content": f"Follow instructions in @{doc_file}"}) + "\n")

        res = self._run_guard({
            "toolCall": {"name": "manage_task"},
            "transcriptPath": self.transcript_file
        })
        self.assertEqual(res.get("decision"), "allow")


if __name__ == "__main__":
    unittest.main()
