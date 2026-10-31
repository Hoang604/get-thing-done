import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent / ".gemini" / "config" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

SCRIPT_PATH = SCRIPT_DIR / "worktree_isolation_guard.py"
spec = importlib.util.spec_from_file_location("worktree_isolation_guard", SCRIPT_PATH)
assert spec is not None and spec.loader is not None
guard = importlib.util.module_from_spec(spec)
sys.modules["worktree_isolation_guard"] = guard
spec.loader.exec_module(guard)


class TestWorktreeIsolationGuard(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.state_dir = self.root / "state"
        self.main_repo = self.root / "repo"
        self.main_repo.mkdir(parents=True)
        (self.main_repo / "src").mkdir()
        (self.main_repo / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")

        self.worktree_dir = self.main_repo / ".worktrees" / "feat-auth"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_unbound_conversation_allows_main_repo_tools_and_commands(self) -> None:
        edit_res = guard.evaluate_pre_tool_use(
            {
                "conversationId": "conv-normal",
                "workspacePaths": [str(self.main_repo)],
                "toolCall": {
                    "name": "edit_file",
                    "args": {"Path": str(self.main_repo / "src" / "app.py")},
                },
            },
            state_dir=self.state_dir,
        )
        cmd_res = guard.evaluate_pre_tool_use(
            {
                "conversationId": "conv-normal",
                "workspacePaths": [str(self.main_repo)],
                "toolCall": {
                    "name": "run_command",
                    "args": {"CommandLine": "python3 -m unittest"},
                },
            },
            state_dir=self.state_dir,
        )
        self.assertEqual(edit_res, {"decision": "allow"})
        self.assertEqual(cmd_res, {"decision": "allow"})

    def test_post_worktree_add_locks_only_target_conversation_and_enforces_boundaries(
        self,
    ) -> None:
        # Simulate git worktree add creating the directory on disk
        self.worktree_dir.mkdir(parents=True)

        guard.handle_post_tool_use(
            {
                "conversationId": "conv-wt",
                "workspacePaths": [str(self.main_repo)],
                "toolCall": {
                    "name": "run_command",
                    "args": {
                        "CommandLine": (
                            f'WORKTREE_PATH="{self.worktree_dir}" && '
                            'git worktree add "$WORKTREE_PATH" -b feat-auth'
                        )
                    },
                },
            },
            state_dir=self.state_dir,
        )

        # Unrelated conversation remains unaffected
        other_res = guard.evaluate_pre_tool_use(
            {
                "conversationId": "conv-other",
                "workspacePaths": [str(self.main_repo)],
                "toolCall": {
                    "name": "edit_file",
                    "args": {"Path": str(self.main_repo / "src" / "app.py")},
                },
            },
            state_dir=self.state_dir,
        )
        self.assertEqual(other_res, {"decision": "allow"})

        # Bound conversation: editing main repo file is denied with worktree suggestion
        deny_edit = guard.evaluate_pre_tool_use(
            {
                "conversationId": "conv-wt",
                "workspacePaths": [str(self.main_repo)],
                "toolCall": {
                    "name": "edit_file",
                    "args": {"Path": str(self.main_repo / "src" / "app.py")},
                },
            },
            state_dir=self.state_dir,
        )
        self.assertEqual(deny_edit.get("decision"), "deny")
        self.assertIn(
            str(self.worktree_dir / "src" / "app.py"),
            str(deny_edit.get("reason")),
        )

        # Bound conversation: editing inside worktree is allowed
        allow_edit = guard.evaluate_pre_tool_use(
            {
                "conversationId": "conv-wt",
                "workspacePaths": [str(self.main_repo)],
                "toolCall": {
                    "name": "edit_file",
                    "args": {"Path": str(self.worktree_dir / "src" / "app.py")},
                },
            },
            state_dir=self.state_dir,
        )
        self.assertEqual(allow_edit, {"decision": "allow"})

        # Bound conversation: reading skills under .gemini in main repo is allowed, but editing is denied
        skill_in_main = (
            self.main_repo / ".gemini" / "config" / "skills" / "execute" / "SKILL.md"
        )
        allow_skill_read = guard.evaluate_pre_tool_use(
            {
                "conversationId": "conv-wt",
                "workspacePaths": [str(self.main_repo)],
                "toolCall": {
                    "name": "read_file",
                    "args": {"Path": str(skill_in_main)},
                },
            },
            state_dir=self.state_dir,
        )
        deny_skill_edit = guard.evaluate_pre_tool_use(
            {
                "conversationId": "conv-wt",
                "workspacePaths": [str(self.main_repo)],
                "toolCall": {
                    "name": "edit_file",
                    "args": {"Path": str(skill_in_main)},
                },
            },
            state_dir=self.state_dir,
        )
        self.assertEqual(allow_skill_read, {"decision": "allow"})
        self.assertEqual(deny_skill_edit.get("decision"), "deny")

    def test_run_command_requires_worktree_entry_and_blocks_main_repo_path_leaks(
        self,
    ) -> None:
        self.worktree_dir.mkdir(parents=True)
        guard.save_isolation_state(
            self.state_dir,
            guard.WorktreeIsolationState(
                conversation_id="conv-cmd",
                main_root=str(self.main_repo.resolve()),
                worktree_path=str(self.worktree_dir.resolve()),
            ),
        )

        # Command without cd into worktree is denied
        no_cd = guard.evaluate_pre_tool_use(
            {
                "conversationId": "conv-cmd",
                "toolCall": {
                    "name": "run_command",
                    "args": {"CommandLine": "pytest"},
                },
            },
            state_dir=self.state_dir,
        )
        self.assertEqual(no_cd.get("decision"), "deny")
        self.assertIn(f'cd "{self.worktree_dir.resolve()}"', str(no_cd.get("reason")))

        # Command with cd into worktree but referencing main repo file is denied
        leaked_path = guard.evaluate_pre_tool_use(
            {
                "conversationId": "conv-cmd",
                "toolCall": {
                    "name": "run_command",
                    "args": {
                        "CommandLine": (
                            f'cd "{self.worktree_dir}" && '
                            f"pytest {self.main_repo / 'src' / 'app.py'}"
                        )
                    },
                },
            },
            state_dir=self.state_dir,
        )
        self.assertEqual(leaked_path.get("decision"), "deny")
        self.assertIn(
            str(self.worktree_dir.resolve() / "src" / "app.py"),
            str(leaked_path.get("reason")),
        )

        # Command entering worktree and staying inside worktree is allowed
        valid_cmd = guard.evaluate_pre_tool_use(
            {
                "conversationId": "conv-cmd",
                "toolCall": {
                    "name": "run_command",
                    "args": {
                        "CommandLine": f'cd "{self.worktree_dir}" && pytest tests/'
                    },
                },
            },
            state_dir=self.state_dir,
        )
        self.assertEqual(valid_cmd, {"decision": "allow"})

    def test_unlocks_on_finishing_skill_read_or_worktree_removal(self) -> None:
        self.worktree_dir.mkdir(parents=True)
        guard.save_isolation_state(
            self.state_dir,
            guard.WorktreeIsolationState(
                conversation_id="conv-finish",
                main_root=str(self.main_repo.resolve()),
                worktree_path=str(self.worktree_dir.resolve()),
            ),
        )

        # Reading finishing-a-development-branch/SKILL.md releases the lock
        guard.handle_post_tool_use(
            {
                "conversationId": "conv-finish",
                "toolCall": {
                    "name": "read_file",
                    "args": {
                        "Path": "/home/user/.gemini/antigravity-cli/skills/finishing-a-development-branch/SKILL.md"
                    },
                },
            },
            state_dir=self.state_dir,
        )
        self.assertIsNone(guard.load_isolation_state(self.state_dir, "conv-finish"))

        # Re-lock and verify git worktree remove also releases the lock
        guard.save_isolation_state(
            self.state_dir,
            guard.WorktreeIsolationState(
                conversation_id="conv-finish",
                main_root=str(self.main_repo.resolve()),
                worktree_path=str(self.worktree_dir.resolve()),
            ),
        )
        allow_remove = guard.evaluate_pre_tool_use(
            {
                "conversationId": "conv-finish",
                "toolCall": {
                    "name": "run_command",
                    "args": {
                        "CommandLine": f'git worktree remove "{self.worktree_dir}"'
                    },
                },
            },
            state_dir=self.state_dir,
        )
        self.assertEqual(allow_remove, {"decision": "allow"})

        guard.handle_post_tool_use(
            {
                "conversationId": "conv-finish",
                "workspacePaths": [str(self.main_repo)],
                "toolCall": {
                    "name": "run_command",
                    "args": {
                        "CommandLine": f'git worktree remove "{self.worktree_dir}"'
                    },
                },
            },
            state_dir=self.state_dir,
        )
        self.assertIsNone(guard.load_isolation_state(self.state_dir, "conv-finish"))


if __name__ == "__main__":
    unittest.main()
