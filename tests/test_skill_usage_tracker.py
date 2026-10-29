import importlib.util
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


if __name__ == "__main__":
    unittest.main()
