#!/usr/bin/env python3
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

RTK_TIMEOUT_SECONDS: float = 4.0
EXCLUDED_RTK_SUBCOMMANDS_RE: re.Pattern[str] = re.compile(
    r"\brtk\s+(?=(?:rg|grep|fd|find)\b)"
)


def strip_excluded_rtk_rewrites(command_line: str) -> str:
    return EXCLUDED_RTK_SUBCOMMANDS_RE.sub("", command_line)


def resolve_rtk_binary() -> str:
    found: str | None = shutil.which("rtk")
    if found:
        return found
    for candidate in (
        Path.home() / ".local" / "bin" / "rtk",
        Path.home() / ".cargo" / "bin" / "rtk",
    ):
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return ""


def rewrite_command_with_rtk(command_line: str, rtk_bin: str) -> str:
    if not rtk_bin or not command_line.strip():
        return command_line
    try:
        completed: subprocess.CompletedProcess[str] = subprocess.run(
            [rtk_bin, "rewrite", command_line],
            capture_output=True,
            text=True,
            timeout=RTK_TIMEOUT_SECONDS,
            check=False,
        )
    except Exception:
        return command_line

    if completed.returncode in (0, 3):
        rewritten: str = strip_excluded_rtk_rewrites(completed.stdout.strip())
        if rewritten:
            return rewritten
    return command_line


def evaluate_rtk_rewrite(
    tool_call: dict[str, object], rtk_bin: str = ""
) -> dict[str, object]:
    if tool_call.get("name") != "run_command":
        return {"decision": "allow"}

    args_obj: object = tool_call.get("args")
    if not isinstance(args_obj, dict):
        return {"decision": "allow"}

    cmd_obj: object = args_obj.get("CommandLine")
    if not isinstance(cmd_obj, str) or not cmd_obj.strip():
        return {"decision": "allow"}

    effective_bin: str = rtk_bin if rtk_bin else resolve_rtk_binary()
    if not effective_bin:
        return {"decision": "allow"}

    rewritten_cmd: str = rewrite_command_with_rtk(cmd_obj, effective_bin)
    if rewritten_cmd == cmd_obj:
        return {"decision": "allow"}

    return {
        "decision": "allow",
        "overwrite": {
            "CommandLine": rewritten_cmd,
        },
    }


def main() -> None:
    try:
        raw_input: str = sys.stdin.read()
        payload: object = json.loads(raw_input) if raw_input.strip() else {}
    except Exception:
        print(json.dumps({"decision": "allow"}))
        return

    if not isinstance(payload, dict):
        print(json.dumps({"decision": "allow"}))
        return

    tool_call_obj: object = payload.get("toolCall")
    if not isinstance(tool_call_obj, dict):
        print(json.dumps({"decision": "allow"}))
        return

    result: dict[str, object] = evaluate_rtk_rewrite(tool_call_obj)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
