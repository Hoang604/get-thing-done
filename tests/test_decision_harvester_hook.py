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
    build_full_prompt,
    build_reminder_prompt,
    evaluate_post_tool_use,
    evaluate_pre_invocation,
    load_harvester_config,
    load_harvester_state,
    resolve_workspace_root,
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

        cfg = load_harvester_config(self.workspace)
        expected_full: str = build_full_prompt(cfg)
        expected_reminder: str = build_reminder_prompt(cfg)
        self.assertNotEqual(expected_full, expected_reminder)

        # Message 3 (first N explicit user message): injects FULL prompt
        self._append_user_step("user message 3")
        self._append_planner_step(80_000)
        res_3 = evaluate_pre_invocation(
            conv_id=self.conv_id,
            transcript_path=str(self.transcript_file),
            workspace_root=self.workspace,
            state_dir=self.state_dir,
        )
        self.assertEqual(
            res_3,
            {"injectSteps": [{"ephemeralMessage": expected_full}]},
        )

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
        self.assertEqual(
            res_6,
            {"injectSteps": [{"ephemeralMessage": expected_reminder}]},
        )

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
        self.assertEqual(
            res_post_3,
            {"injectSteps": [{"ephemeralMessage": expected_full}]},
        )

    def test_prompt_section_replace_and_slot_inject(self) -> None:
        self._write_config(
            """enabled: true
every_n_messages: 1
prompt:
  replace:
    full:
      header: "CUSTOM HEADER: {{project_name}}"
      what_to_capture: "CAPTURE: {{extra_capture_rules}}"
      partitioning: ""
      file_contract: "CUSTOM CONTRACT"
  inject:
    project_name: "OrderEngine"
    extra_capture_rules: "Always record rounding invariants."
"""
        )

        res = evaluate_pre_invocation(
            conv_id=self.conv_id,
            transcript_path=str(self.transcript_file),
            workspace_root=self.workspace,
            state_dir=self.state_dir,
        )
        self.assertEqual(
            res,
            {
                "injectSteps": [
                    {
                        "ephemeralMessage": (
                            "<critical_instructions>\n"
                            "CUSTOM HEADER: OrderEngine\n\n"
                            "CAPTURE: Always record rounding invariants.\n\n"
                            "CUSTOM CONTRACT\n"
                            "</critical_instructions>"
                        )
                    }
                ]
            },
        )

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

    def test_pre_invocation_resolves_workspace_when_spawned_outside_project(
        self,
    ) -> None:
        self._write_config("enabled: true\nevery_n_messages: 2\n")
        unrelated_cwd: Path = self.temp_dir / "outside_cwd"
        unrelated_cwd.mkdir(parents=True, exist_ok=True)
        statusline_dir: Path = self.temp_dir / "statusline"

        # Case 1: Statusline turn directory provides workspace for PreInvocation payload
        turn_dir: Path = statusline_dir / self.conv_id / "turn-1"
        turn_dir.mkdir(parents=True, exist_ok=True)
        (turn_dir / "statusline_input.json").write_text(
            json.dumps(
                {
                    "conversation_id": self.conv_id,
                    "workspace": {
                        "project_dir": str(self.workspace),
                        "current_dir": str(self.workspace),
                    },
                }
            ),
            encoding="utf-8",
        )

        self._append_user_step("first message")
        self._append_planner_step(20_000)
        pre_payload: dict[str, object] = {
            "conversationId": self.conv_id,
            "transcriptPath": str(self.transcript_file),
        }
        resolved_1: Path = resolve_workspace_root(
            payload=pre_payload,
            fallback_root=unrelated_cwd,
            state_dir=self.state_dir,
            statusline_dir=statusline_dir,
        )
        self.assertEqual(resolved_1, self.workspace.resolve())

        res_1 = evaluate_pre_invocation(
            conv_id=self.conv_id,
            transcript_path=str(self.transcript_file),
            workspace_root=resolved_1,
            state_dir=self.state_dir,
        )
        self.assertEqual(res_1, {"injectSteps": []})
        saved_state = load_harvester_state(self.state_dir, self.conv_id)
        self.assertEqual(saved_state.messages_since_cycle_start, 1)
        self.assertEqual(saved_state.workspace_root, str(self.workspace.resolve()))

        # Case 2: Even if statusline directory is removed, persisted state resolves workspace
        shutil.rmtree(statusline_dir)
        self._append_user_step("second message")
        self._append_planner_step(30_000)
        resolved_2: Path = resolve_workspace_root(
            payload=pre_payload,
            fallback_root=unrelated_cwd,
            state_dir=self.state_dir,
            statusline_dir=statusline_dir,
        )
        self.assertEqual(resolved_2, self.workspace.resolve())

        res_2 = evaluate_pre_invocation(
            conv_id=self.conv_id,
            transcript_path=str(self.transcript_file),
            workspace_root=resolved_2,
            state_dir=self.state_dir,
        )
        expected_full: str = build_full_prompt(load_harvester_config(self.workspace))
        self.assertEqual(
            res_2,
            {"injectSteps": [{"ephemeralMessage": expected_full}]},
        )

        # Case 3: Brand-new conversation without statusline or state resolves from transcript tool_calls
        conv_from_transcript: str = "conv-transcript-only"
        nested_file: Path = self.workspace / "src" / "app.py"
        nested_file.parent.mkdir(parents=True, exist_ok=True)
        self._append_step(
            {
                "type": "PLANNER_RESPONSE",
                "source": "MODEL",
                "tool_calls": [
                    {
                        "name": "read_file",
                        "args": {"Path": str(nested_file)},
                    }
                ],
            }
        )
        resolved_3: Path = resolve_workspace_root(
            payload={
                "conversationId": conv_from_transcript,
                "transcriptPath": str(self.transcript_file),
            },
            fallback_root=unrelated_cwd,
            state_dir=self.state_dir,
            statusline_dir=statusline_dir,
        )
        self.assertEqual(resolved_3, self.workspace.resolve())


if __name__ == "__main__":
    unittest.main()
