import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR: Path = Path(__file__).resolve().parent.parent / ".gemini" / "config" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from read_file_guard import evaluate_post_tool_use, evaluate_pre_tool_use

SCRIPT_PATH: Path = SCRIPT_DIR / "read_file_guard.py"


class TestReadFileGuard(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root: Path = Path(self._tmp.name)
        self.state_dir: Path = self.root / "guard_state"
        self.compact_dir: Path = self.root / "compact_state"
        self.conv_id: str = "conv-test-read-guard"
        self.transcript: Path = self.root / "transcript.jsonl"
        self.transcript.write_text("", encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _make_lines_file(self, rel_path: str, count: int, pad: int = 0) -> Path:
        file_path: Path = self.root / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        suffix: str = "x" * pad
        content: str = "".join(f"line-{i:04d}{suffix}\n" for i in range(1, count + 1))
        file_path.write_text(content, encoding="utf-8")
        return file_path

    def _pre(
        self,
        args: dict[str, object],
        tool_name: str = "read_file",
        conv_id: str | None = None,
        transcript: Path | None = None,
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "conversationId": self.conv_id if conv_id is None else conv_id,
            "transcriptPath": str(self.transcript if transcript is None else transcript),
            "toolCall": {"name": tool_name, "args": args},
        }
        return evaluate_pre_tool_use(
            payload, state_dir=self.state_dir, compact_state_dir=self.compact_dir
        )

    def _post(
        self,
        args: dict[str, object],
        tool_name: str = "read_file",
        error: str = "",
        conv_id: str | None = None,
        transcript: Path | None = None,
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "conversationId": self.conv_id if conv_id is None else conv_id,
            "transcriptPath": str(self.transcript if transcript is None else transcript),
            "toolCall": {"name": tool_name, "args": args},
        }
        if error:
            payload["error"] = error
        return evaluate_post_tool_use(
            payload, state_dir=self.state_dir, compact_state_dir=self.compact_dir
        )

    def test_json_spill_blocks_large_single_line_wide_and_byte_offset_reads(self) -> None:
        single_line: Path = self.root / ".system_generated" / "steps" / "42" / "output.txt"
        single_line.parent.mkdir(parents=True, exist_ok=True)
        single_line.write_text(
            json.dumps({"items": [{"msg": "v" * 200} for _ in range(80)]}),
            encoding="utf-8",
        )
        self.assertGreater(single_line.stat().st_size, 10_240)

        pretty: Path = self.root / ".system_generated" / "steps" / "43" / "output.txt"
        pretty.parent.mkdir(parents=True, exist_ok=True)
        pretty.write_text(
            json.dumps({f"k{i}": "v" * 120 for i in range(120)}, indent=2),
            encoding="utf-8",
        )
        self.assertGreater(pretty.stat().st_size, 10_240)

        for args in (
            {"Path": str(single_line)},
            {"Path": str(single_line), "StartLine": 1, "EndLine": 1},
            {"Path": str(pretty)},
            {"Path": str(pretty), "StartLine": 1, "EndLine": 81},
            {"Path": str(pretty), "StartLine": 1, "EndLine": 20, "ByteOffset": 100},
        ):
            with self.subTest(args=args):
                res = self._pre(args)
                self.assertEqual(res.get("decision"), "deny")

    def test_json_spill_allows_non_json_small_narrow_pretty_and_repo_json(self) -> None:
        bracket_log: Path = self.root / ".system_generated" / "steps" / "1" / "output.txt"
        bracket_log.parent.mkdir(parents=True, exist_ok=True)
        bracket_log.write_text(
            "".join(f"[2026-11-26] INFO event={i} {'a' * 120}\n" for i in range(120)),
            encoding="utf-8",
        )
        self.assertGreater(bracket_log.stat().st_size, 10_240)

        small_json: Path = self.root / ".system_generated" / "steps" / "2" / "output.txt"
        small_json.parent.mkdir(parents=True, exist_ok=True)
        payload_prefix: str = '{"pad":"'
        payload_suffix: str = '"}'
        exact_10k: str = payload_prefix + ("a" * (10_240 - len(payload_prefix) - len(payload_suffix))) + payload_suffix
        small_json.write_text(exact_10k, encoding="utf-8")
        self.assertEqual(small_json.stat().st_size, 10_240)

        pretty: Path = self.root / ".system_generated" / "steps" / "3" / "output.txt"
        pretty.parent.mkdir(parents=True, exist_ok=True)
        pretty.write_text(
            json.dumps({f"k{i}": "v" * 120 for i in range(120)}, indent=2),
            encoding="utf-8",
        )

        repo_json: Path = self.root / "data.json"
        repo_json.write_text(
            json.dumps({"items": [{"msg": "v" * 200} for _ in range(80)]}),
            encoding="utf-8",
        )

        for args in (
            {"Path": str(bracket_log)},
            {"Path": str(small_json)},
            {"Path": str(pretty), "StartLine": 1, "EndLine": 80},
            {"Path": str(repo_json)},
        ):
            with self.subTest(args=args):
                self.assertEqual(self._pre(args), {"decision": "allow"})

    def test_full_duplicate_and_merged_adjacent_reads_are_denied(self) -> None:
        f: Path = self._make_lines_file("src/a.py", 150)
        self._post({"Path": str(f), "StartLine": 1, "EndLine": 50})
        self._post({"Path": str(f), "StartLine": 51, "EndLine": 100})

        self.assertEqual(
            self._pre({"Path": str(f), "StartLine": 1, "EndLine": 100}).get("decision"),
            "deny",
        )
        self.assertEqual(
            self._pre({"Path": str(f), "StartLine": 25, "EndLine": 75}).get("decision"),
            "deny",
        )
        self.assertEqual(
            self._pre({"Path": str(f), "StartLine": 101, "EndLine": 120}),
            {"decision": "allow"},
        )

    def test_partial_edge_overlap_trims_when_at_least_5_lines_and_allows_under_5(self) -> None:
        f: Path = self._make_lines_file("src/b.py", 300)
        self._post({"Path": str(f), "StartLine": 100, "EndLine": 200})

        self.assertEqual(
            self._pre({"Path": str(f), "StartLine": 197, "EndLine": 250}),
            {"decision": "allow"},
        )
        self.assertEqual(
            self._pre({"Path": str(f), "StartLine": 196, "EndLine": 250}),
            {"decision": "allow", "overwrite": {"StartLine": 201}},
        )
        self.assertEqual(
            self._pre({"Path": str(f), "StartLine": 50, "EndLine": 103}),
            {"decision": "allow"},
        )
        self.assertEqual(
            self._pre({"Path": str(f), "StartLine": 50, "EndLine": 104}),
            {"decision": "allow", "overwrite": {"EndLine": 99}},
        )

        f2: Path = self._make_lines_file("src/both.py", 100)
        self._post({"Path": str(f2), "StartLine": 1, "EndLine": 20})
        self._post({"Path": str(f2), "StartLine": 80, "EndLine": 100})
        self.assertEqual(
            self._pre({"Path": str(f2)}),
            {"decision": "allow", "overwrite": {"StartLine": 21, "EndLine": 79}},
        )

    def test_middle_donut_overlap_preserves_both_unread_sides_and_only_trims_outer_edges(self) -> None:
        f: Path = self._make_lines_file("src/donut.py", 120)
        self._post({"Path": str(f), "StartLine": 40, "EndLine": 60})

        self.assertEqual(
            self._pre({"Path": str(f), "StartLine": 1, "EndLine": 100}),
            {"decision": "allow"},
        )

        self._post({"Path": str(f), "StartLine": 1, "EndLine": 10})
        self.assertEqual(
            self._pre({"Path": str(f), "StartLine": 1, "EndLine": 100}),
            {"decision": "allow", "overwrite": {"StartLine": 11}},
        )

    def test_disk_modification_invalidates_recorded_ranges(self) -> None:
        f: Path = self._make_lines_file("src/changed.py", 30)
        self._post({"Path": str(f), "StartLine": 1, "EndLine": 20})
        self.assertEqual(
            self._pre({"Path": str(f), "StartLine": 1, "EndLine": 20}).get("decision"),
            "deny",
        )

        st_before: os.stat_result = f.stat()
        old_text: str = f.read_text(encoding="utf-8")
        new_text: str = old_text.replace("line-0001", "edit-0001", 1)
        self.assertEqual(len(new_text.encode("utf-8")), len(old_text.encode("utf-8")))
        f.write_text(new_text, encoding="utf-8")
        os.utime(f, ns=(st_before.st_atime_ns, st_before.st_mtime_ns))

        self.assertEqual(
            self._pre({"Path": str(f), "StartLine": 1, "EndLine": 20}),
            {"decision": "allow"},
        )

    def test_compaction_resets_recorded_ranges_and_unblocked_files(self) -> None:
        fa: Path = self._make_lines_file("src/a.py", 40)
        fb: Path = self._make_lines_file("src/b.py", 40)
        self._post({"Path": str(fa), "StartLine": 1, "EndLine": 30})
        self._post({"Path": str(fb)}, tool_name="edit_file", error="target not found")
        self._post({"Path": str(fb), "StartLine": 1, "EndLine": 20})

        self.assertEqual(
            self._pre({"Path": str(fa), "StartLine": 1, "EndLine": 30}).get("decision"),
            "deny",
        )
        self.assertEqual(
            self._pre({"Path": str(fb), "StartLine": 1, "EndLine": 20}),
            {"decision": "allow"},
        )

        with open(self.transcript, "a", encoding="utf-8") as handle:
            handle.write(json.dumps({"type": "CHECKPOINT", "content": "<CONTEXT_SUMMARY>"}) + "\n")

        self.assertEqual(
            self._pre({"Path": str(fa), "StartLine": 1, "EndLine": 30}),
            {"decision": "allow"},
        )
        self._post({"Path": str(fb), "StartLine": 1, "EndLine": 20})
        self.assertEqual(
            self._pre({"Path": str(fb), "StartLine": 1, "EndLine": 20}).get("decision"),
            "deny",
        )

    def test_edit_failure_unblocks_only_that_file_while_edit_success_clears_ranges_only(self) -> None:
        fa: Path = self._make_lines_file("src/a.py", 50)
        fb: Path = self._make_lines_file("src/b.py", 50)
        self._post({"Path": str(fa), "StartLine": 1, "EndLine": 40})
        self._post({"Path": str(fb), "StartLine": 1, "EndLine": 40})

        self._post({"Path": str(fa)}, tool_name="edit_file", error="target mismatch")
        self.assertEqual(
            self._pre({"Path": str(fa), "StartLine": 1, "EndLine": 40}),
            {"decision": "allow"},
        )
        self._post({"Path": str(fa), "StartLine": 1, "EndLine": 40})
        self.assertEqual(
            self._pre({"Path": str(fa), "StartLine": 1, "EndLine": 40}),
            {"decision": "allow"},
        )
        self.assertEqual(
            self._pre({"Path": str(fb), "StartLine": 1, "EndLine": 40}).get("decision"),
            "deny",
        )

        self._post({"Path": str(fb)}, tool_name="edit_file")
        self.assertEqual(
            self._pre({"Path": str(fb), "StartLine": 1, "EndLine": 40}),
            {"decision": "allow"},
        )
        self._post({"Path": str(fb), "StartLine": 1, "EndLine": 40})
        self.assertEqual(
            self._pre({"Path": str(fb), "StartLine": 1, "EndLine": 40}).get("decision"),
            "deny",
        )

    def test_post_tool_use_respects_800_line_and_46kb_truncation_and_skips_errors(self) -> None:
        short_f: Path = self._make_lines_file("src/short.py", 30)
        self._post({"Path": str(short_f), "StartLine": 1, "EndLine": 20}, error="denied")
        self.assertEqual(
            self._pre({"Path": str(short_f), "StartLine": 1, "EndLine": 20}),
            {"decision": "allow"},
        )
        self._post({"Path": str(short_f), "StartLine": 1, "EndLine": 20, "ByteOffset": 100})
        self.assertEqual(
            self._pre({"Path": str(short_f), "StartLine": 1, "EndLine": 20}),
            {"decision": "allow"},
        )

        long_f: Path = self._make_lines_file("src/long.py", 1000)
        self._post({"Path": str(long_f)})
        self.assertEqual(
            self._pre({"Path": str(long_f), "StartLine": 1, "EndLine": 800}).get("decision"),
            "deny",
        )
        self.assertEqual(
            self._pre({"Path": str(long_f), "StartLine": 801, "EndLine": 1000}),
            {"decision": "allow"},
        )

        wide_f: Path = self._make_lines_file("src/wide.py", 300, pad=290)
        self._post({"Path": str(wide_f)})
        self.assertEqual(
            self._pre({"Path": str(wide_f), "StartLine": 1, "EndLine": 100}).get("decision"),
            "deny",
        )
        self.assertEqual(
            self._pre({"Path": str(wide_f), "StartLine": 200, "EndLine": 300}),
            {"decision": "allow"},
        )

    def test_non_text_non_read_and_edge_inputs_fail_open(self) -> None:
        text_f: Path = self._make_lines_file("src/edge.py", 20)
        self._post({"Path": str(text_f), "StartLine": 1, "EndLine": 20})

        empty_f: Path = self.root / "src" / "empty.py"
        empty_f.write_text("", encoding="utf-8")

        bin_f: Path = self.root / "src" / "blob.txt"
        bin_f.write_bytes(b"hello\x00world\n")

        img_f: Path = self.root / "src" / "pic.png"
        img_f.write_bytes(b"not-real-png-bytes\n")

        self._post({"Path": str(bin_f)})
        self._post({"Path": str(img_f)})
        self._post({"Path": str(empty_f)})
        self._post({"Path": str(self.root / "missing.py")})

        for tool_name, args, cid in (
            ("run_command", {"CommandLine": "ls"}, self.conv_id),
            ("read_file", {"Path": str(text_f), "StartLine": 1, "EndLine": 20}, ""),
            ("read_file", {"Path": str(text_f), "ByteOffset": 50}, self.conv_id),
            ("read_file", {"Path": str(text_f), "StartLine": 25, "EndLine": 30}, self.conv_id),
            ("read_file", {"Path": str(bin_f)}, self.conv_id),
            ("read_file", {"Path": str(img_f)}, self.conv_id),
            ("read_file", {"Path": str(empty_f)}, self.conv_id),
            ("read_file", {"Path": str(self.root / "missing.py")}, self.conv_id),
        ):
            with self.subTest(tool_name=tool_name, args=args, cid=cid):
                self.assertEqual(
                    self._pre(args, tool_name=tool_name, conv_id=cid),
                    {"decision": "allow"},
                )

        # bool StartLine/EndLine must not be treated as int 1
        bool_f: Path = self._make_lines_file("src/bool.py", 20)
        self._post({"Path": str(bool_f), "StartLine": 1, "EndLine": 5})
        self.assertEqual(
            self._pre({"Path": str(bool_f), "StartLine": True, "EndLine": 20}),
            {"decision": "allow", "overwrite": {"StartLine": 6}},
        )

    def test_cli_stdin_stdout_contract(self) -> None:
        f: Path = self._make_lines_file("src/cli.py", 60)
        env: dict[str, str] = {
            **os.environ,
            "AGY_READ_FILE_GUARD_STATE_DIR": str(self.state_dir),
            "AGY_COMPACT_STATE_DIR": str(self.compact_dir),
        }

        read_payload = {
            "conversationId": self.conv_id,
            "transcriptPath": str(self.transcript),
            "toolCall": {
                "name": "read_file",
                "args": {"Path": str(f), "StartLine": 1, "EndLine": 50},
            },
        }
        post_proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "post"],
            input=json.dumps(read_payload),
            capture_output=True,
            text=True,
            env=env,
            check=True,
        )
        self.assertEqual(json.loads(post_proc.stdout), {})

        deny_proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "pre"],
            input=json.dumps(read_payload),
            capture_output=True,
            text=True,
            env=env,
            check=True,
        )
        self.assertEqual(json.loads(deny_proc.stdout).get("decision"), "deny")

        edit_fail_payload = {
            "conversationId": self.conv_id,
            "transcriptPath": str(self.transcript),
            "toolCall": {"name": "edit_file", "args": {"Path": str(f)}},
            "error": "target not found",
        }
        subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "post"],
            input=json.dumps(edit_fail_payload),
            capture_output=True,
            text=True,
            env=env,
            check=True,
        )
        allow_proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "pre"],
            input=json.dumps(read_payload),
            capture_output=True,
            text=True,
            env=env,
            check=True,
        )
        self.assertEqual(json.loads(allow_proc.stdout), {"decision": "allow"})

        for mode, expected in (("pre", {"decision": "allow"}), ("post", {})):
            for raw in ("{bad", "[1]"):
                with self.subTest(mode=mode, raw=raw):
                    proc = subprocess.run(
                        [sys.executable, str(SCRIPT_PATH), mode],
                        input=raw,
                        capture_output=True,
                        text=True,
                        env=env,
                        check=True,
                    )
                    self.assertEqual(json.loads(proc.stdout), expected)


if __name__ == "__main__":
    unittest.main()
