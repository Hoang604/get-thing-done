#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

CACHE_DIR: Path = Path("/tmp/antigravity_reads")


def count_file_lines(filepath: str) -> int:
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def main() -> None:
    try:
        raw_payload: str = sys.stdin.read()
        if not raw_payload.strip():
            print(json.dumps({"decision": "allow"}))
            return
        payload: dict[str, object] = json.loads(raw_payload)
    except Exception:
        print(json.dumps({"decision": "allow"}))
        return

    tool_call = payload.get("toolCall")
    if not isinstance(tool_call, dict):
        print(json.dumps({"decision": "allow"}))
        return

    args = tool_call.get("args")
    if not isinstance(args, dict):
        print(json.dumps({"decision": "allow"}))
        return

    filepath_obj = args.get("AbsolutePath")
    if not isinstance(filepath_obj, str) or not os.path.exists(filepath_obj):
        print(json.dumps({"decision": "allow"}))
        return

    conv_id_obj = payload.get("conversationId")
    conv_id: str = str(conv_id_obj) if conv_id_obj else "default"

    canonical_path: str = os.path.realpath(filepath_obj)

    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        session_cache: Path = CACHE_DIR / f"{conv_id}.txt"

        seen_files: set[str] = set()
        if session_cache.exists():
            seen_files = set(session_cache.read_text(encoding="utf-8").splitlines())

        # If already read in this session -> allow exact slice without tampering
        if canonical_path in seen_files:
            print(json.dumps({"decision": "allow"}))
            return

        # First read in this session: record path into cache
        with open(session_cache, "a", encoding="utf-8") as f:
            f.write(canonical_path + "\n")

        total_lines: int = count_file_lines(canonical_path)

        # Standard file: if it fits within the 800-line tool window, read full file
        if 0 < total_lines <= 800:
            print(
                json.dumps({
                    "decision": "allow",
                    "overwrite": {
                        "StartLine": 1,
                        "EndLine": total_lines,
                    },
                })
            )
            return

        # Large file (> 800 lines): expand narrow slices (< 200 lines)
        start_obj = args.get("StartLine")
        end_obj = args.get("EndLine")

        if isinstance(start_obj, int) and isinstance(end_obj, int):
            if (end_obj - start_obj) < 200:
                expanded_start: int = max(1, start_obj - 50)
                expanded_end: int = min(total_lines, expanded_start + 400)
                print(
                    json.dumps({
                        "decision": "allow",
                        "overwrite": {
                            "StartLine": expanded_start,
                            "EndLine": expanded_end,
                        },
                    })
                )
                return

        print(json.dumps({"decision": "allow"}))

    except Exception:
        print(json.dumps({"decision": "allow"}))


if __name__ == "__main__":
    main()
