#!/usr/bin/env python3
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

LOG_FILE = "/tmp/agy_verify_hooks.log"


def log_line(status: str, command: str, detail: str = "") -> None:
    try:
        ts = datetime.now().strftime("%H:%M:%S")
        cmd_clean = command.strip().replace("\n", " ")
        cmd_short = (cmd_clean[:65] + "...") if len(cmd_clean) > 65 else cmd_clean
        line = f"[{ts}] [{status:<5}] {cmd_short} {detail}".rstrip() + "\n"
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass


class ManifestResolver:
    """Resolves package manifest (package.json) scripts to inspect underlying binaries."""

    def __init__(self, root_dir: Optional[str] = None) -> None:
        self.root_dir = root_dir or os.getcwd()
        self._pkg_cache: Dict[str, Dict[str, Any]] = {}

    def _read_json(self, file_path: Path) -> Optional[Dict[str, Any]]:
        str_path = str(file_path.resolve())
        if str_path in self._pkg_cache:
            return self._pkg_cache[str_path]
        try:
            if file_path.is_file():
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._pkg_cache[str_path] = data
                    return data
        except Exception:
            pass
        return None

    def find_package_json(self, cwd: str, filter_target: Optional[str] = None) -> Optional[Dict[str, Any]]:
        cwd_path = Path(cwd)

        if filter_target:
            clean_target = filter_target.strip().strip("'\"")
            target_path = (cwd_path / clean_target).resolve()
            target_pkg = target_path / "package.json"
            if target_pkg.is_file():
                data = self._read_json(target_pkg)
                if data:
                    return data

            search_roots = [cwd_path, Path(self.root_dir)]
            for s_root in search_roots:
                for cand in s_root.glob("**/package.json"):
                    if "node_modules" in cand.parts:
                        continue
                    data = self._read_json(cand)
                    if data and data.get("name") == clean_target:
                        return data

        direct_pkg = cwd_path / "package.json"
        if direct_pkg.is_file():
            data = self._read_json(direct_pkg)
            if data:
                return data

        curr = cwd_path
        while curr != curr.parent:
            pkg = curr / "package.json"
            if pkg.is_file():
                data = self._read_json(pkg)
                if data:
                    return data
            if (curr / ".git").exists():
                break
            curr = curr.parent

        return None

    def resolve_script_command(self, script_name: str, cwd: str, filter_target: Optional[str] = None) -> Optional[str]:
        pkg = self.find_package_json(cwd, filter_target)
        if pkg:
            scripts = pkg.get("scripts", {})
            if isinstance(scripts, dict) and script_name in scripts:
                return str(scripts[script_name])
        return None


class VerifyRecorder:
    """Evaluates executed tool output from PostToolUse via Manifest Introspection and Deterministic Exit Code checks."""

    def __init__(self, patterns_file_path: Optional[str] = None, cache_dir: str = "/tmp") -> None:
        if patterns_file_path is None:
            patterns_file_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "verify_patterns.json"
            )
        self.patterns_file_path = patterns_file_path
        self.cache_dir = cache_dir
        self.config = self._load_config()
        self.resolver = ManifestResolver()

    def _load_config(self) -> Dict[str, Any]:
        try:
            if os.path.exists(self.patterns_file_path):
                with open(self.patterns_file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {"core_binaries": {}}

    def _parse_pm_tokens(self, args_str: str) -> Tuple[Optional[str], str]:
        tokens = args_str.strip().split()
        filter_target = None
        script_name = ""
        skip_next = False

        for i, token in enumerate(tokens):
            if skip_next:
                skip_next = False
                continue
            if token in ("--filter", "-F", "--prefix", "-C", "--workspace", "-w"):
                if i + 1 < len(tokens):
                    filter_target = tokens[i + 1]
                    skip_next = True
                continue
            if token.startswith("--filter=") or token.startswith("--prefix=") or token.startswith("-C="):
                filter_target = token.split("=", 1)[1]
                continue
            if token.startswith("-"):
                continue
            if token.lower() == "run":
                continue
            script_name = token
            break

        return filter_target, script_name

    def match_command(self, command: str, cwd: str = "") -> Optional[Tuple[str, str]]:
        if not command:
            return None
        cmd = command.strip()

        core_binaries = self.config.get("core_binaries", {})

        # 1. Direct Python verifiers & tools
        python_binaries = core_binaries.get("python", ["pytest", "unittest", "mypy", "pyright", "ruff", "flake8", "alembic", "tox", "nox"])
        for py_bin in python_binaries:
            if re.search(rf"\b{re.escape(py_bin)}\b", cmd, re.IGNORECASE):
                if re.search(rf"(^|/|\s|run\s+|-m\s+){re.escape(py_bin)}(\s+|$)", cmd, re.IGNORECASE):
                    return ("python", f"Python tool ({py_bin})")

        # 2. Direct Rust verifiers & tools
        rust_binaries = core_binaries.get("rust", ["cargo test", "cargo check", "cargo clippy", "cargo build", "sqlx", "diesel"])
        for r_bin in rust_binaries:
            if r_bin.startswith("cargo "):
                sub = r_bin.replace("cargo ", "")
                if re.search(rf"\bcargo(\s+.*)?\s+{re.escape(sub)}(\s+.*)?$", cmd, re.IGNORECASE):
                    return ("rust", f"Rust tool ({r_bin})")
            else:
                if re.search(rf"\b{re.escape(r_bin)}\b", cmd, re.IGNORECASE):
                    return ("rust", f"Rust tool ({r_bin})")

        # 3. Direct Go verifiers & tools
        go_binaries = core_binaries.get("go", ["go test", "go vet", "golangci-lint", "go build", "sqlc", "buf", "mockgen"])
        for g_bin in go_binaries:
            if g_bin.startswith("go "):
                sub = g_bin.replace("go ", "")
                if re.search(rf"\bgo(\s+.*)?\s+{re.escape(sub)}(\s+.*)?$", cmd, re.IGNORECASE):
                    return ("go", f"Go tool ({g_bin})")
            else:
                if re.search(rf"\b{re.escape(g_bin)}\b", cmd, re.IGNORECASE):
                    return ("go", f"Go tool ({g_bin})")

        # 4. Direct Java verifiers & tools
        if re.search(r"\b(mvn|gradle|\./gradlew|gradlew)\b", cmd, re.IGNORECASE):
            if re.search(r"\b(test|verify|check|compile|build)\b", cmd, re.IGNORECASE):
                return ("java", "Java build/test tool")

        # 5. Direct Node standalone binaries & generators
        node_binaries = core_binaries.get("node", [
            "tsc", "vitest", "jest", "mocha", "eslint", "biome", "cypress", "playwright",
            "turbo", "graphql-codegen", "openapi-typescript", "openapi-ts", "prisma", "buf", "protoc"
        ])
        for n_bin in node_binaries:
            if re.search(rf"(^|/|\s|npx\s+){re.escape(n_bin)}(\s+|$)", cmd, re.IGNORECASE):
                return ("node", f"Node tool ({n_bin})")

        # 6. Node Package Manager Wrappers (npm, pnpm, yarn, bun, turbo) -> Manifest Introspection
        pm_match = re.search(r"^(npx\s+)?(npm|pnpm|yarn|bun|turbo)\b(?P<args>.*)$", cmd, re.IGNORECASE)
        if pm_match:
            args_str = pm_match.group("args").strip()
            filter_target, script_name = self._parse_pm_tokens(args_str)

            if script_name:
                expanded_cmd = self.resolver.resolve_script_command(
                    script_name, cwd=cwd or os.getcwd(), filter_target=filter_target
                )
                if expanded_cmd:
                    for n_bin in node_binaries:
                        if re.search(rf"\b{re.escape(n_bin)}\b", expanded_cmd, re.IGNORECASE):
                            return ("node", f"Node script '{script_name}' -> ({n_bin})")

                keywords = [
                    "test", "build", "check", "lint", "verify", "validate", "type",
                    "codegen", "generate", "gen", "schema", "compile", "audit"
                ]
                check_target = f"{script_name} {expanded_cmd or ''}".lower()
                if any(kw in check_target for kw in keywords):
                    return ("node", f"Node verification/generator script ({script_name})")

        # 7. Generic script check
        if re.search(r"(^|/)((verify|validate|test|check|lint|build|codegen|gen)[a-zA-Z0-9_-]*\.(sh|py|js|ts)|make\s+(test|check|verify|generate|codegen))", cmd, re.IGNORECASE):
            return ("generic", "Generic verification/generator runner")

        return None

    def _extract_command_and_cwd(self, payload: Dict[str, Any]) -> Tuple[str, str]:
        cmd = ""
        cwd = ""
        tool_call = payload.get("toolCall")
        if isinstance(tool_call, dict):
            args = tool_call.get("args", {})
            if isinstance(args, dict):
                cmd = str(args.get("CommandLine") or args.get("command") or "")
                cwd = str(args.get("Cwd") or "")

        if not cmd:
            transcript_path = payload.get("transcriptPath")
            step_idx = payload.get("stepIdx")
            if transcript_path and os.path.exists(transcript_path):
                try:
                    with open(transcript_path, "r", encoding="utf-8") as f:
                        for line in f:
                            try:
                                entry = json.loads(line)
                                if step_idx is not None and entry.get("step_index") == step_idx:
                                    for tc in entry.get("tool_calls", []):
                                        if tc.get("name") == "run_command":
                                            t_args = tc.get("args", {})
                                            cmd = str(t_args.get("CommandLine") or "")
                                            cwd = str(t_args.get("Cwd") or "")
                                            break
                            except Exception:
                                continue
                except Exception:
                    pass
        return cmd, cwd

    def _evaluate_status(self, payload: Dict[str, Any]) -> Tuple[str, int, str]:
        """
        Returns (state, exit_code, detail_msg)
        state in ('PASS', 'FAIL', 'ASYNC', 'UNKNOWN')
        """
        raw_error = payload.get("error")
        if raw_error is not None and str(raw_error).strip():
            err_str = str(raw_error).strip().lower()
            if "exit status 0" in err_str:
                return "PASS", 0, "(exit: 0)"
            match_err_code = re.search(r"exit status ([0-9]+)", err_str)
            code = int(match_err_code.group(1)) if match_err_code else 1
            return "FAIL", code, f"(exit: {code})"

        transcript_path = payload.get("transcriptPath")
        step_idx = payload.get("stepIdx")

        if transcript_path and os.path.exists(transcript_path) and step_idx is not None:
            try:
                with open(transcript_path, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            if entry.get("step_index") == step_idx:
                                content = str(entry.get("content") or "")

                                if "Tool is running as a background task" in content or entry.get("status") == "RUNNING":
                                    return "ASYNC", 0, "-> Đang chạy ngầm, chờ kết quả"

                                if re.search(r"The command exited with code 0\b", content):
                                    return "PASS", 0, "(exit: 0)"

                                match_nonzero = re.search(r"The command exited with code ([1-9][0-9]*)", content)
                                if match_nonzero:
                                    code = int(match_nonzero.group(1))
                                    return "FAIL", code, f"(exit: {code})"

                                if entry.get("status") == "ERROR":
                                    return "FAIL", 1, "(status: ERROR)"
                        except Exception:
                            continue
            except Exception:
                pass

        return "PASS", 0, "(exit: 0)"

    def record_if_failed(self, payload: Dict[str, Any]) -> Optional[str]:
        conv_id = payload.get("conversationId")
        if not conv_id:
            return None

        command, cwd = self._extract_command_and_cwd(payload)
        if not command:
            return None

        matched = self.match_command(command, cwd=cwd)
        if not matched:
            return None

        ecosystem, runner_desc = matched
        state, exit_code, detail = self._evaluate_status(payload)

        if state == "ASYNC":
            log_line("ASYNC", command, detail)
            return None

        if state == "PASS":
            log_line("PASS", command, f"{detail} -> Thành công, không chặn")
            return None

        # State is FAIL
        log_line("FAIL", command, f"{detail} -> Đã bắt lỗi & kích hoạt hook")

        incident = {
            "conversationId": conv_id,
            "stepIdx": payload.get("stepIdx", 0),
            "command": command,
            "runnerName": runner_desc,
            "ecosystem": ecosystem,
            "error": f"exit status {exit_code}",
            "acknowledged": False,
            "timestamp": time.time(),
        }

        incident_path = os.path.join(self.cache_dir, f"agy_incident_{conv_id}.json")
        try:
            with open(incident_path, "w", encoding="utf-8") as f:
                json.dump(incident, f, indent=2)
            return incident_path
        except Exception:
            return None


def main() -> None:
    try:
        raw_input = sys.stdin.read()
        if raw_input.strip():
            payload = json.loads(raw_input)
            recorder = VerifyRecorder()
            recorder.record_if_failed(payload)
    except Exception:
        pass
    print("{}")


if __name__ == "__main__":
    main()
