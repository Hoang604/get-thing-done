import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR: Path = (
    Path(__file__).resolve().parent.parent / ".gemini" / "config" / "scripts"
)
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from decision_harvester_hook import (
    MANAGED_BLOCK_END,
    MANAGED_BLOCK_START,
    evaluate_post_tool_use,
    evaluate_pre_invocation,
    sync_decisions_index,
)


class TestDecisionHarvesterHook(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir: Path = Path(tempfile.mkdtemp())
        self.workspace: Path = self.temp_dir / "workspace"
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.state_dir: Path = self.temp_dir / "state"
        self.transcript_file: Path = self.temp_dir / "transcript.jsonl"
        self.conv_id: str = "conv-harvester-test"

    def tearDown(self) -> None:
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _write_config(self, content: str) -> Path:
        cfg_file: Path = self.workspace / ".gtd" / "config.yml"
        cfg_file.parent.mkdir(parents=True, exist_ok=True)
        cfg_file.write_text(content, encoding="utf-8")
        return cfg_file

    def _append_step(self, step: dict[str, object]) -> None:
        with open(self.transcript_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(step) + "\n")

    def _append_planner_step(
        self, input_tokens: int, cache_read_tokens: int = 0
    ) -> None:
        self._append_step(
            {
                "type": "PLANNER_RESPONSE",
                "source": "MODEL",
                "input_tokens": input_tokens,
                "cache_read_tokens": cache_read_tokens,
                "output_tokens": 150,
            }
        )

    def _append_user_step(
        self, content: str = "user decision message", source: str = "USER_EXPLICIT"
    ) -> None:
        self._append_step(
            {
                "type": "USER_INPUT",
                "source": source,
                "content": content,
            }
        )

    def test_disabled_when_no_config_or_enabled_false(self) -> None:
        res_no_cfg = evaluate_pre_invocation(
            conv_id=self.conv_id,
            transcript_path=str(self.transcript_file),
            workspace_root=self.workspace,
            state_dir=self.state_dir,
        )
        self.assertEqual(res_no_cfg, {"injectSteps": []})

        self._write_config("enabled: false\nevery_n_messages: 1\n")
        res_disabled = evaluate_pre_invocation(
            conv_id=self.conv_id,
            transcript_path=str(self.transcript_file),
            workspace_root=self.workspace,
            state_dir=self.state_dir,
        )
        self.assertEqual(res_disabled, {"injectSteps": []})

    def test_full_prompt_at_first_n_then_reminder_then_resets_after_compact(
        self,
    ) -> None:
        self._write_config("enabled: true\nevery_n_messages: 3\n")

        # Messages 1 and 2: no injection
        for idx in range(2):
            self._append_user_step(f"user message {idx + 1}")
            self._append_planner_step(50_000)
            res = evaluate_pre_invocation(
                conv_id=self.conv_id,
                transcript_path=str(self.transcript_file),
                workspace_root=self.workspace,
                state_dir=self.state_dir,
            )
            self.assertEqual(res, {"injectSteps": []})

        # Reactive wakeup from background task / subagent (source == SYSTEM) before message 3:
        # Must NOT count as message 3 and must NOT trigger injection!
        self._append_user_step(
            "[Message] Subagent completed background work", source="SYSTEM"
        )
        self._append_planner_step(65_000)
        res_sys_wakeup = evaluate_pre_invocation(
            conv_id=self.conv_id,
            transcript_path=str(self.transcript_file),
            workspace_root=self.workspace,
            state_dir=self.state_dir,
        )
        self.assertEqual(res_sys_wakeup, {"injectSteps": []})

        # Message 3 (first N explicit user message): injects FULL prompt
        self._append_user_step("user message 3")
        self._append_planner_step(80_000)
        res_3 = evaluate_pre_invocation(
            conv_id=self.conv_id,
            transcript_path=str(self.transcript_file),
            workspace_root=self.workspace,
            state_dir=self.state_dir,
        )
        steps_3 = res_3.get("injectSteps")
        assert isinstance(steps_3, list)
        self.assertEqual(len(steps_3), 1)
        msg_3 = steps_3[0].get("ephemeralMessage")
        assert isinstance(msg_3, str)
        self.assertIn(
            "### 1. Goal: Persist System-Shaping Decisions into `.gtd/decisions/`",
            msg_3,
        )
        self.assertIn("1. **Invariants & Rules**:", msg_3)
        self.assertIn("## Confirmed", msg_3)
        self.assertIn("## Unconfirmed", msg_3)
        self.assertNotIn("{{", msg_3)

        # Reactive wakeup right after message 3 (when counter is still 3):
        # Must NOT re-inject on system wakeup!
        self._append_user_step(
            "[Message] Background task finished", source="SYSTEM"
        )
        self._append_planner_step(95_000)
        res_sys_after_3 = evaluate_pre_invocation(
            conv_id=self.conv_id,
            transcript_path=str(self.transcript_file),
            workspace_root=self.workspace,
            state_dir=self.state_dir,
        )
        self.assertEqual(res_sys_after_3, {"injectSteps": []})

        # Messages 4 and 5: no injection
        for idx in range(2):
            self._append_user_step(f"user message {idx + 4}")
            self._append_planner_step(110_000)
            res = evaluate_pre_invocation(
                conv_id=self.conv_id,
                transcript_path=str(self.transcript_file),
                workspace_root=self.workspace,
                state_dir=self.state_dir,
            )
            self.assertEqual(res, {"injectSteps": []})

        # Message 6 (2N in same cycle): injects SHORT REMINDER prompt
        self._append_user_step("user message 6")
        self._append_planner_step(140_000)
        res_6 = evaluate_pre_invocation(
            conv_id=self.conv_id,
            transcript_path=str(self.transcript_file),
            workspace_root=self.workspace,
            state_dir=self.state_dir,
        )
        steps_6 = res_6.get("injectSteps")
        assert isinstance(steps_6, list)
        self.assertEqual(len(steps_6), 1)
        msg_6 = steps_6[0].get("ephemeralMessage")
        assert isinstance(msg_6, str)
        self.assertIn(
            "Before ending this turn, update `.gtd/decisions/<topic>.md` with any system-shaping decisions added or changed since the last sync.",
            msg_6,
        )
        self.assertNotIn("### 1. Goal: Persist System-Shaping Decisions", msg_6)

        # Compaction occurs (tokens drop from 140,000 -> 25,000): cycle resets!
        # Message 1 after compact:
        self._append_planner_step(25_000)
        self._append_user_step("post-compact user message 1")
        res_post_1 = evaluate_pre_invocation(
            conv_id=self.conv_id,
            transcript_path=str(self.transcript_file),
            workspace_root=self.workspace,
            state_dir=self.state_dir,
        )
        self.assertEqual(res_post_1, {"injectSteps": []})

        # Message 2 after compact:
        self._append_user_step("post-compact user message 2")
        self._append_planner_step(35_000)
        res_post_2 = evaluate_pre_invocation(
            conv_id=self.conv_id,
            transcript_path=str(self.transcript_file),
            workspace_root=self.workspace,
            state_dir=self.state_dir,
        )
        self.assertEqual(res_post_2, {"injectSteps": []})

        # Message 3 after compact (first N in new cycle): injects FULL prompt again!
        self._append_user_step("post-compact user message 3")
        self._append_planner_step(45_000)
        res_post_3 = evaluate_pre_invocation(
            conv_id=self.conv_id,
            transcript_path=str(self.transcript_file),
            workspace_root=self.workspace,
            state_dir=self.state_dir,
        )
        steps_post_3 = res_post_3.get("injectSteps")
        assert isinstance(steps_post_3, list)
        self.assertEqual(len(steps_post_3), 1)
        msg_post_3 = steps_post_3[0].get("ephemeralMessage")
        assert isinstance(msg_post_3, str)
        self.assertIn(
            "### 1. Goal: Persist System-Shaping Decisions into `.gtd/decisions/`",
            msg_post_3,
        )

    def test_prompt_section_replace_and_slot_inject(self) -> None:
        self._write_config(
            """enabled: true
every_n_messages: 1
prompt:
  replace:
    full:
      header: "CUSTOM HEADER: {{project_name}}"
      file_contract: "CUSTOM FILE CONTRACT"
  inject:
    project_name: "OrderEngine"
    extra_capture_rules: "- Always record currency rounding invariants."
"""
        )

        res = evaluate_pre_invocation(
            conv_id=self.conv_id,
            transcript_path=str(self.transcript_file),
            workspace_root=self.workspace,
            state_dir=self.state_dir,
        )
        steps = res.get("injectSteps")
        assert isinstance(steps, list)
        msg = steps[0].get("ephemeralMessage")
        assert isinstance(msg, str)
        self.assertIn("CUSTOM HEADER: OrderEngine", msg)
        self.assertIn("- Always record currency rounding invariants.", msg)
        self.assertIn("CUSTOM FILE CONTRACT", msg)
        self.assertNotIn("## Unconfirmed", msg)
        self.assertNotIn("{{", msg)

    def test_sync_decisions_index_target_priority_and_live_updates(self) -> None:
        self._write_config("enabled: true\nevery_n_messages: 5\n")
        decisions_dir: Path = self.workspace / ".gtd" / "decisions"
        decisions_dir.mkdir(parents=True, exist_ok=True)

        auth_file: Path = decisions_dir / "auth-session.md"
        auth_file.write_text(
            '---\ndescription: "When modifying authentication or session tokens, follow the confirmed decisions in this file."\n---\n\n## Confirmed\n- Use HttpOnly cookies.\n\n## Unconfirmed\n',
            encoding="utf-8",
        )

        # Case 1: Neither GEMINI.md nor AGENTS.md exists -> creates GEMINI.md
        payload: dict[str, object] = {
            "conversationId": self.conv_id,
            "toolCall": {
                "name": "write_file",
                "args": {"Path": str(auth_file)},
            },
        }
        evaluate_post_tool_use(
            payload=payload,
            workspace_root=self.workspace,
            state_dir=self.state_dir,
        )
        gemini_md: Path = self.workspace / "GEMINI.md"
        self.assertTrue(gemini_md.is_file())
        content_1: str = gemini_md.read_text(encoding="utf-8")
        self.assertIn(MANAGED_BLOCK_START, content_1)
        self.assertIn(
            "- [`.gtd/decisions/auth-session.md`](.gtd/decisions/auth-session.md): When modifying authentication or session tokens, follow the confirmed decisions in this file.",
            content_1,
        )
        self.assertIn(MANAGED_BLOCK_END, content_1)

        # Case 2: If GEMINI.md does not exist but AGENTS.md exists -> updates AGENTS.md
        gemini_md.unlink()
        agents_md: Path = self.workspace / "AGENTS.md"
        agents_md.write_text("# Existing Agents Rules\n", encoding="utf-8")

        billing_file: Path = decisions_dir / "billing.md"
        billing_file.write_text(
            '---\ndescription: "When touching invoice calculation, follow this file."\n---\n\n## Confirmed\n- Store amounts in integer cents.\n',
            encoding="utf-8",
        )
        sync_decisions_index(self.workspace)
        self.assertFalse(gemini_md.is_file())
        agents_content: str = agents_md.read_text(encoding="utf-8")
        self.assertIn("# Existing Agents Rules", agents_content)
        self.assertIn("`.gtd/decisions/auth-session.md`", agents_content)
        self.assertIn("`.gtd/decisions/billing.md`", agents_content)

        # Case 3: Manual edit of description in IDE is detected on next PreInvocation
        billing_file.write_text(
            '---\ndescription: "When touching invoice or tax calculation, follow this updated file."\n---\n\n## Confirmed\n- Store amounts in integer cents.\n',
            encoding="utf-8",
        )
        evaluate_pre_invocation(
            conv_id=self.conv_id,
            transcript_path=str(self.transcript_file),
            workspace_root=self.workspace,
            state_dir=self.state_dir,
        )
        updated_agents_content: str = agents_md.read_text(encoding="utf-8")
        self.assertIn(
            "When touching invoice or tax calculation, follow this updated file.",
            updated_agents_content,
        )


if __name__ == "__main__":
    unittest.main()
