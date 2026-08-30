#!/usr/bin/env python3
import json
import os
import re
import sys
from pathlib import Path

try:
    import fcntl
except ImportError:
    fcntl = None

CACHE_DIR: Path = Path("/tmp/antigravity_reads")

BINARY_EXTENSIONS: set[str] = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".bmp",
    ".ico",
    ".tiff",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".xz",
    ".7z",
    ".rar",
    ".mp3",
    ".mp4",
    ".wav",
    ".avi",
    ".mov",
    ".mkv",
    ".flac",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".bin",
    ".pyc",
    ".o",
    ".a",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".class",
    ".jar",
    ".wasm",
    ".sqlite",
    ".db",
    ".parquet",
}


def is_binary_file(filepath: str) -> bool:
    ext: str = os.path.splitext(filepath)[1].lower()
    if ext in BINARY_EXTENSIONS:
        return True
    try:
        with open(filepath, "rb") as f:
            sample: bytes = f.read(1024)
            return b"\x00" in sample
    except Exception:
        return False


def count_file_lines(filepath: str) -> int:
    try:
        with open(filepath, "rb") as f:
            lines: int = 0
            last_byte: bytes = b""
            while True:
                chunk: bytes = f.read(65536)
                if not chunk:
                    break
                lines += chunk.count(b"\n")
                last_byte = chunk[-1:]
            if lines == 0 and os.path.getsize(filepath) > 0:
                return 1
            if lines > 0 and last_byte != b"\n":
                lines += 1
            return lines
    except Exception:
        return 0


def get_seen_files(session_cache: Path) -> set[str]:
    if not session_cache.exists():
        return set()
    try:
        with open(session_cache, "r", encoding="utf-8", errors="ignore") as f:
            if fcntl is not None:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                content: str = f.read()
                return set(content.splitlines())
            finally:
                if fcntl is not None:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except Exception:
        return set()


def mark_file_seen(session_cache: Path, canonical_path: str) -> None:
    try:
        with open(session_cache, "a", encoding="utf-8") as f:
            if fcntl is not None:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                f.write(canonical_path + "\n")
                f.flush()
            finally:
                if fcntl is not None:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except Exception:
        pass


def sanitize_conversation_id(raw_id: object) -> str:
    if not isinstance(raw_id, str) or not raw_id.strip():
        return "default"
    sanitized: str = re.sub(r"[^a-zA-Z0-9_\-]", "_", raw_id.strip())
    return sanitized if sanitized else "default"


def parse_line_num(val: object) -> int | None:
    if isinstance(val, int) and not isinstance(val, bool):
        return val
    if isinstance(val, str) and val.isdigit():
        return int(val)
    return None


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
    if not isinstance(tool_call, dict) or tool_call.get("name") != "view_file":
        print(json.dumps({"decision": "allow"}))
        return

    args = tool_call.get("args")
    if not isinstance(args, dict):
        print(json.dumps({"decision": "allow"}))
        return

    filepath_obj = args.get("AbsolutePath")
    if not isinstance(filepath_obj, str) or not os.path.exists(filepath_obj) or not os.path.isfile(filepath_obj):
        print(json.dumps({"decision": "allow"}))
        return

    conv_id: str = sanitize_conversation_id(payload.get("conversationId"))
    canonical_path: str = os.path.realpath(filepath_obj)

    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        session_cache: Path = CACHE_DIR / f"{conv_id}.txt"

        seen_files: set[str] = get_seen_files(session_cache)

        # If already read in this session -> allow exact slice without tampering
        if canonical_path in seen_files:
            print(json.dumps({"decision": "allow"}))
            return

        # Do not modify arguments for binary files
        if is_binary_file(canonical_path):
            mark_file_seen(session_cache, canonical_path)
            print(json.dumps({"decision": "allow"}))
            return

        # First read in this session: record path into cache
        mark_file_seen(session_cache, canonical_path)

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
        start_val: int | None = parse_line_num(args.get("StartLine"))
        end_val: int | None = parse_line_num(args.get("EndLine"))

        if start_val is not None and end_val is not None and 1 <= start_val <= end_val:
            if (end_val - start_val) < 200:
                expanded_start: int = max(1, start_val - 50)
                expanded_end: int = min(total_lines, max(end_val + 50, expanded_start + 400))
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
