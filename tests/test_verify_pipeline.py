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


class TestVerifyPipelineMultiLanguage(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        patterns_source = SCRIPT_DIR / "verify_patterns.json"
        self.patterns_path = os.path.join(self.temp_dir, "verify_patterns.json")
        shutil.copyfile(patterns_source, self.patterns_path)

        self.recorder = VerifyRecorder(patterns_file_path=self.patterns_path, cache_dir=self.temp_dir)
        self.injector = VerifyInjector(cache_dir=self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_non_verify_commands_ignored(self):
        ignored = [
            "git status",
            "git commit -m 'fix: test'",
            "cat package.json",
            "ls -la",
            "curl http://localhost:3000",
            "echo 'running tests'",
        ]
        for cmd in ignored:
            payload = {
                "conversationId": "conv-test",
                "toolCall": {"name": "run_command", "args": {"CommandLine": cmd}},
                "error": "some exit status 1"
            }
            res = self.recorder.record_if_failed(payload)
            self.assertIsNone(res, f"Should ignore: {cmd}")

    def test_manifest_introspection_node(self):
        # Create a mock package.json with custom script names
        pkg_dir = os.path.join(self.temp_dir, "my-app")
        os.makedirs(pkg_dir, exist_ok=True)
        pkg_json = {
            "name": "my-app",
            "scripts": {
                "type-check": "tsc --noEmit",
                "ci-verify": "vitest run --coverage",
                "style-audit": "eslint . --max-warnings 0",
                "start-server": "node server.js"
            }
        }
        with open(os.path.join(pkg_dir, "package.json"), "w", encoding="utf-8") as f:
            json.dump(pkg_json, f)

        # 1. Custom script 'type-check' resolving to 'tsc'
        payload = {
            "conversationId": "conv-node-1",
            "toolCall": {"name": "run_command", "args": {"CommandLine": "pnpm run type-check", "Cwd": pkg_dir}},
            "error": "exit status 1"
        }
        res = self.recorder.record_if_failed(payload)
        self.assertIsNotNone(res)
        with open(res, "r") as f:
            data = json.load(f)
        self.assertEqual(data["ecosystem"], "node")
        self.assertIn("type-check", data["runnerName"])
        self.assertIn("tsc", data["runnerName"])

        # 2. Custom script 'ci-verify' resolving to 'vitest'
        payload = {
            "conversationId": "conv-node-2",
            "toolCall": {"name": "run_command", "args": {"CommandLine": "npm run ci-verify", "Cwd": pkg_dir}},
            "error": "exit status 1"
        }
        res = self.recorder.record_if_failed(payload)
        self.assertIsNotNone(res)

        # 3. Non-test script 'start-server' ignored
        payload = {
            "conversationId": "conv-node-3",
            "toolCall": {"name": "run_command", "args": {"CommandLine": "pnpm run start-server", "Cwd": pkg_dir}},
            "error": "exit status 1"
        }
        res = self.recorder.record_if_failed(payload)
        self.assertIsNone(res)

    def test_monorepo_filter_resolution(self):
        # Create monorepo package structure
        monorepo_dir = os.path.join(self.temp_dir, "monorepo")
        pkg_sub = os.path.join(monorepo_dir, "packages", "fe-store")
        os.makedirs(pkg_sub, exist_ok=True)
        pkg_json = {
            "name": "@vas/fe-store",
            "scripts": {
                "build": "next build",
                "type-check": "tsc --noEmit"
            }
        }
        with open(os.path.join(pkg_sub, "package.json"), "w", encoding="utf-8") as f:
            json.dump(pkg_json, f)

        payload = {
            "conversationId": "conv-monorepo",
            "toolCall": {
                "name": "run_command",
                "args": {
                    "CommandLine": "pnpm --filter @vas/fe-store run type-check",
                    "Cwd": monorepo_dir
                }
            },
            "error": "exit status 1"
        }
        res = self.recorder.record_if_failed(payload)
        self.assertIsNotNone(res)
        with open(res, "r") as f:
            data = json.load(f)
        self.assertEqual(data["ecosystem"], "node")
        self.assertIn("type-check", data["runnerName"])
        self.assertIn("tsc", data["runnerName"])

    def test_multi_language_support(self):
        test_cases = [
            # Python
            ("uv run pytest tests/", "python"),
            ("pytest -v", "python"),
            ("python3 -m unittest discover", "python"),
            ("mypy src/", "python"),
            ("ruff check .", "python"),
            # Rust
            ("cargo test --all", "rust"),
            ("cargo check", "rust"),
            ("cargo clippy --all-targets", "rust"),
            # Go
            ("go test ./...", "go"),
            ("go vet ./...", "go"),
            ("golangci-lint run", "go"),
            # Java
            ("mvn test", "java"),
            ("mvn verify", "java"),
            ("./gradlew check", "java"),
            ("gradle test", "java"),
        ]

        for cmd, expected_eco in test_cases:
            payload = {
                "conversationId": f"conv-{expected_eco}",
                "toolCall": {"name": "run_command", "args": {"CommandLine": cmd}},
                "error": "exit status 1"
            }
            res = self.recorder.record_if_failed(payload)
            self.assertIsNotNone(res, f"Failed to match command: {cmd}")
            with open(res, "r") as f:
                data = json.load(f)
            self.assertEqual(data["ecosystem"], expected_eco, f"Ecosystem mismatch for: {cmd}")

    def test_pipeline_injector_acknowledgement_flow(self):
        conv_id = "conv-ack-flow"
        payload = {
            "conversationId": conv_id,
            "stepIdx": 5,
            "toolCall": {"name": "run_command", "args": {"CommandLine": "cargo test"}},
            "error": "exit status 101"
        }
        self.recorder.record_if_failed(payload)

        # 1. First invocation -> injects instruction
        steps = self.injector.generate_instruction(conv_id)
        self.assertEqual(len(steps), 1)
        msg = steps[0]["ephemeralMessage"]
        self.assertIn("CRITICAL VERIFICATION FAILURE DETECTED", msg)
        self.assertIn("cargo test", msg)

        # 2. Second invocation -> deduplicated (empty)
        steps_2 = self.injector.generate_instruction(conv_id)
        self.assertEqual(len(steps_2), 0)


if __name__ == "__main__":
    unittest.main()
