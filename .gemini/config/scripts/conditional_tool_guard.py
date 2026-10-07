#!/usr/bin/env python3
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Set


def extract_md_paths_from_text(text: str) -> Set[str]:
    paths: Set[str] = set()
    matches = re.findall(
        r'(?:@[/.~]?[^\s<>"\'`:]+\.md|(?:/[^\s<>"\'`:]+|[.~]/[^\s<>"\'`:]+|[a-zA-Z0-9_\-\./]+)\.md)\b',
        text,
        re.IGNORECASE,
    )
    for m in matches:
        clean = m.lstrip("@").strip()
        if clean.lower().endswith(".md"):
            paths.add(clean)
    return paths


def extract_viewed_md_files(step: Dict[str, Any]) -> Set[str]:
    md_files: Set[str] = set()

    tool_calls = step.get("tool_calls")
    if isinstance(tool_calls, list):
        for tc in tool_calls:
            if isinstance(tc, dict) and tc.get("name") == "view_file":
                args = tc.get("args")
                if isinstance(args, dict):
                    filepath = args.get("AbsolutePath") or args.get("targetFile") or args.get("path")
                    if isinstance(filepath, str) and filepath.strip().lower().endswith(".md"):
                        md_files.add(filepath.strip())

    tc = step.get("toolCall")
    if isinstance(tc, dict) and tc.get("name") == "view_file":
        args = tc.get("args")
        if isinstance(args, dict):
            filepath = args.get("AbsolutePath") or args.get("targetFile") or args.get("path")
            if isinstance(filepath, str) and filepath.strip().lower().endswith(".md"):
                md_files.add(filepath.strip())

    return md_files


def file_contains_pattern(filepath: str, pattern: re.Pattern) -> bool:
    try:
        resolved = Path(filepath).expanduser().resolve()
        if not resolved.is_file() or not resolved.name.lower().endswith(".md"):
            return False
        with open(resolved, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read(1024 * 1024)
            return bool(pattern.search(content))
    except Exception:
        return False


def is_tool_allowed(tool_name: str, transcript_path: str) -> bool:
    if not tool_name or tool_name not in ("manage_task", "schedule"):
        return False

    pattern = re.compile(rf"\b{re.escape(tool_name)}\b", re.IGNORECASE)

    if not transcript_path or not os.path.exists(transcript_path):
        return False

    steps: List[Dict[str, Any]] = []
    try:
        with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    steps.append(json.loads(line))
                except Exception:
                    continue
    except Exception:
        return False

    if not steps:
        return False

    # Find the latest direct user input
    last_user_idx = -1
    for idx in range(len(steps) - 1, -1, -1):
        step = steps[idx]
        if step.get("type") == "USER_INPUT":
            if step.get("source") == "USER_EXPLICIT":
                last_user_idx = idx
                break

    if last_user_idx == -1:
        for idx in range(len(steps) - 1, -1, -1):
            step = steps[idx]
            if step.get("type") == "USER_INPUT" and step.get("source") != "SYSTEM":
                last_user_idx = idx
                break

    if last_user_idx == -1:
        return False

    # 1. Check user input content directly
    latest_user_text = str(steps[last_user_idx].get("content") or "")
    if pattern.search(latest_user_text):
        return True

    # 2. Collect .md files read or referenced from latest_user_idx to end
    md_files_to_check: Set[str] = extract_md_paths_from_text(latest_user_text)

    for step in steps[last_user_idx:]:
        md_files_to_check.update(extract_viewed_md_files(step))

    # 3. Scan collected .md files
    for filepath in md_files_to_check:
        if file_contains_pattern(filepath, pattern):
            return True

    return False


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        print(json.dumps({"decision": "deny", "reason": "Failed to parse hook payload."}))
        return

    tool_name = payload.get("toolCall", {}).get("name", "")
    transcript_path = payload.get("transcriptPath", "")

    if is_tool_allowed(tool_name, transcript_path):
        print(json.dumps({"decision": "allow"}))
    else:
        print(json.dumps({
            "decision": "deny",
            "reason": (
                f"BLOCKED: Tool '{tool_name}' execution is prohibited because "
                "asynchronous tasks are automatically handled via reactive wakeup upon completion. "
                "Do NOT poll, manage tasks, or schedule timers. Stop calling tools to allow background "
                "tasks to finish. (This tool is only permitted when explicitly requested by the user "
                f"or specified in an active .md instruction file via '\\b{tool_name}\\b')."
            )
        }))


if __name__ == "__main__":
    main()

