import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent
    / ".gemini"
    / "config"
    / "scripts"
    / "skill_usage_tracker.py"
)
spec = importlib.util.spec_from_file_location("skill_usage_tracker", SCRIPT_PATH)
assert spec is not None and spec.loader is not None
skill_usage_tracker = importlib.util.module_from_spec(spec)
sys.modules["skill_usage_tracker"] = skill_usage_tracker
spec.loader.exec_module(skill_usage_tracker)


class TestSkillUsageTracker(unittest.TestCase):
    def test_extract_invoked_skill_reads_frontmatter_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            skill_dir = Path(tmp_dir) / "skills" / "antigravity_guide"
            skill_dir.mkdir(parents=True)
            skill_file = skill_dir / "SKILL.md"
            skill_file.write_text(
                "---\nname: antigravity-guide\ndescription: test\n---\n# Guide\n",
                encoding="utf-8",
            )
            payload: dict[str, object] = {
                "toolCall": {
                    "name": "read_file",
                    "args": {"Path": str(skill_file)},
                }
            }
            self.assertEqual(
                skill_usage_tracker.extract_invoked_skill(payload),
                "antigravity-guide",
            )

    def test_extract_invoked_skill_falls_back_to_folder_name(self) -> None:
        payload: dict[str, object] = {
            "toolCall": {
                "name": "read_file",
                "args": {
                    "Path": "/nonexistent/.gemini/antigravity-cli/skills/boundary-plan/SKILL.md"
                },
            }
        }
        self.assertEqual(
            skill_usage_tracker.extract_invoked_skill(payload),
            "boundary-plan",
        )

    def test_ignores_continuation_reads_and_errors_and_non_skill_files(self) -> None:
        base_path = "/home/user/.gemini/antigravity-cli/skills/execute/SKILL.md"
        cont_payload: dict[str, object] = {
            "toolCall": {
                "name": "read_file",
                "args": {"Path": base_path, "StartLine": 100, "EndLine": 200},
            }
        }
        self.assertIsNone(skill_usage_tracker.extract_invoked_skill(cont_payload))

        err_payload: dict[str, object] = {
            "error": "file not found",
            "toolCall": {
                "name": "read_file",
                "args": {"Path": base_path},
            },
        }
        self.assertIsNone(skill_usage_tracker.extract_invoked_skill(err_payload))

        other_file_payload: dict[str, object] = {
            "toolCall": {
                "name": "read_file",
                "args": {
                    "Path": "/home/user/.gemini/antigravity-cli/skills/execute/references/detail.md"
                },
            }
        }
        self.assertIsNone(skill_usage_tracker.extract_invoked_skill(other_file_payload))

    def test_record_and_load_skill_usage_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            usage_md = Path(tmp_dir) / "skill_usage.md"
            skill_usage_tracker.record_skill_usage(
                "execute", usage_file=usage_md, now_str="2026-10-29 10:00:00"
            )
            skill_usage_tracker.record_skill_usage(
                "boundary-plan", usage_file=usage_md, now_str="2026-10-29 10:05:00"
            )
            skill_usage_tracker.record_skill_usage(
                "execute", usage_file=usage_md, now_str="2026-10-29 11:00:00"
            )

            entries = skill_usage_tracker.load_skill_usage(usage_md)
            self.assertEqual(entries["execute"].count, 2)
            self.assertEqual(entries["execute"].last_used, "2026-10-29 11:00:00")
            self.assertEqual(entries["boundary-plan"].count, 1)

            text = usage_md.read_text(encoding="utf-8")
            self.assertIn("Total skill activations: **3**", text)
            lines = [line for line in text.splitlines() if line.startswith("| `")]
            self.assertEqual(
                lines,
                [
                    "| `execute` | 2 | 2026-10-29 11:00:00 |",
                    "| `boundary-plan` | 1 | 2026-10-29 10:05:00 |",
                ],
            )

    def test_pre_invocation_counts_slash_skill_and_ignores_non_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            workspace = root / "workspace"
            home_dir = root / "home"
            usage_md = root / "skill_usage.md"
            state_dir = root / "state"
            transcript = root / "transcript.jsonl"

            ws_skill = workspace / ".gemini" / "antigravity-cli" / "skills" / "boundary-plan" / "SKILL.md"
            ws_skill.parent.mkdir(parents=True)
            ws_skill.write_text("---\nname: boundary-plan\n---\n", encoding="utf-8")

            builtin_skill = home_dir / ".gemini" / "antigravity-cli" / "builtin" / "skills" / "native_swarm" / "SKILL.md"
            builtin_skill.parent.mkdir(parents=True)
            builtin_skill.write_text("---\nname: swarm\n---\n", encoding="utf-8")

            steps = [
                ("/boundary-plan viết plan", "step-1"),
                ("/swarm chia việc", "step-2"),
                ("/compact", "step-3"),
                ("/home/user/SKILL.md đọc file", "step-4"),
                ("hãy đọc /boundary-plan ở giữa câu", "step-5"),
            ]
            for idx, (prompt, ts) in enumerate(steps, 1):
                with open(transcript, "a", encoding="utf-8") as f:
                    f.write(
                        json.dumps(
                            {
                                "step_index": idx,
                                "type": "USER_INPUT",
                                "source": "USER_EXPLICIT",
                                "created_at": ts,
                                "content": prompt,
                            }
                        )
                        + "\n"
                    )
                res = skill_usage_tracker.evaluate_pre_invocation(
                    {
                        "conversationId": "conv-slash",
                        "workspacePaths": [str(workspace)],
                        "transcriptPath": str(transcript),
                        "lastUserInput": prompt,
                    },
                    usage_file=usage_md,
                    state_dir=state_dir,
                    home_dir=home_dir,
                    now_str="2026-11-13 12:00:00",
                )
                self.assertEqual(res, {"injectSteps": []})

            entries = skill_usage_tracker.load_skill_usage(usage_md)
            self.assertEqual(set(entries.keys()), {"boundary-plan", "swarm"})
            self.assertEqual(entries["boundary-plan"].count, 1)
            self.assertEqual(entries["swarm"].count, 1)

    def test_deduplicates_within_turn_and_counts_new_user_turn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            workspace = root / "workspace"
            home_dir = root / "home"
            usage_md = root / "skill_usage.md"
            state_dir = root / "state"
            transcript = root / "transcript.jsonl"

            bp_skill = workspace / ".gemini" / "antigravity-cli" / "skills" / "boundary-plan" / "SKILL.md"
            bp_skill.parent.mkdir(parents=True)
            bp_skill.write_text("---\nname: boundary-plan\n---\n", encoding="utf-8")

            exec_skill = workspace / ".gemini" / "antigravity-cli" / "skills" / "execute" / "SKILL.md"
            exec_skill.parent.mkdir(parents=True)
            exec_skill.write_text("---\nname: execute\n---\n", encoding="utf-8")

            def append_step(step: dict[str, object]) -> None:
                with open(transcript, "a", encoding="utf-8") as f:
                    f.write(json.dumps(step) + "\n")

            # Turn 1: /boundary-plan
            append_step(
                {
                    "step_index": 1,
                    "type": "USER_INPUT",
                    "source": "USER_EXPLICIT",
                    "created_at": "t1",
                    "content": "/boundary-plan bước 1",
                }
            )
            pre_payload_t1: dict[str, object] = {
                "conversationId": "conv-dedup",
                "workspacePaths": [str(workspace)],
                "transcriptPath": str(transcript),
                "lastUserInput": "/boundary-plan bước 1",
            }
            skill_usage_tracker.evaluate_pre_invocation(
                pre_payload_t1, usage_file=usage_md, state_dir=state_dir, home_dir=home_dir
            )
            # Second PreInvocation in same turn must not double-count
            append_step({"step_index": 2, "type": "PLANNER_RESPONSE", "source": "MODEL"})
            skill_usage_tracker.evaluate_pre_invocation(
                pre_payload_t1, usage_file=usage_md, state_dir=state_dir, home_dir=home_dir
            )
            # Reactive SYSTEM wakeup with stale lastUserInput must not double-count
            append_step(
                {
                    "step_index": 3,
                    "type": "USER_INPUT",
                    "source": "SYSTEM",
                    "created_at": "t1-sys",
                    "content": "[Message] Subagent finished",
                }
            )
            skill_usage_tracker.evaluate_pre_invocation(
                pre_payload_t1, usage_file=usage_md, state_dir=state_dir, home_dir=home_dir
            )
            # PostToolUse reading the SAME skill in the same turn must not double-count
            skill_usage_tracker.evaluate_post_tool_use(
                {
                    "conversationId": "conv-dedup",
                    "transcriptPath": str(transcript),
                    "toolCall": {"name": "read_file", "args": {"Path": str(bp_skill)}},
                },
                usage_file=usage_md,
                state_dir=state_dir,
            )
            # PostToolUse reading a DIFFERENT skill in the same turn counts +1
            skill_usage_tracker.evaluate_post_tool_use(
                {
                    "conversationId": "conv-dedup",
                    "transcriptPath": str(transcript),
                    "toolCall": {"name": "read_file", "args": {"Path": str(exec_skill)}},
                },
                usage_file=usage_md,
                state_dir=state_dir,
            )

            entries = skill_usage_tracker.load_skill_usage(usage_md)
            self.assertEqual(entries["boundary-plan"].count, 1)
            self.assertEqual(entries["execute"].count, 1)

            # Turn 2: New USER_EXPLICIT with exact same slash text counts +1
            append_step(
                {
                    "step_index": 4,
                    "type": "USER_INPUT",
                    "source": "USER_EXPLICIT",
                    "created_at": "t2",
                    "content": "/boundary-plan bước 1",
                }
            )
            skill_usage_tracker.evaluate_pre_invocation(
                pre_payload_t1, usage_file=usage_md, state_dir=state_dir, home_dir=home_dir
            )
            entries_after_t2 = skill_usage_tracker.load_skill_usage(usage_md)
            self.assertEqual(entries_after_t2["boundary-plan"].count, 2)

    def test_mode_detection_and_hooks_json_registration(self) -> None:
        self.assertTrue(skill_usage_tracker.is_pre_invocation_mode("pre_invocation", None))
        self.assertFalse(skill_usage_tracker.is_pre_invocation_mode("post_tool_use", None))
        self.assertTrue(
            skill_usage_tracker.is_pre_invocation_mode(
                "", {"hookEventName": "PreInvocation"}
            )
        )
        self.assertFalse(
            skill_usage_tracker.is_pre_invocation_mode(
                "", {"toolCall": {"name": "read_file"}}
            )
        )

        hooks_path = (
            Path(__file__).resolve().parent.parent
            / ".gemini"
            / "config"
            / "hooks.json"
        )
        hooks_cfg = json.loads(hooks_path.read_text(encoding="utf-8"))
        tracker_cfg = hooks_cfg["skill-usage-tracker"]
        self.assertIn("PreInvocation", tracker_cfg)
        self.assertIn("PostToolUse", tracker_cfg)


if __name__ == "__main__":
    unittest.main()
