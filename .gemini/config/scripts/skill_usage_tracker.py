#!/usr/bin/env python3
import json
import os
import re
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterator

try:
    import fcntl
except ImportError:
    fcntl = None

DEFAULT_USAGE_FILE: Path = Path.home() / ".gemini" / "skill_usage.md"
FRONTMATTER_RE: re.Pattern[str] = re.compile(
    r"\A---\s*\r?\n(.*?)\r?\n---\s*(?:\r?\n|\Z)", re.DOTALL
)
NAME_LINE_RE: re.Pattern[str] = re.compile(r"^name:\s*(.+?)\s*$", re.MULTILINE)
TABLE_ROW_RE: re.Pattern[str] = re.compile(
    r"^\|\s*`([^`]+)`\s*\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|$"
)


@dataclass(frozen=True)
class SkillUsageEntry:
    skill_name: str
    count: int
    last_used: str


@contextmanager
def usage_file_lock(usage_file: Path) -> Iterator[None]:
    try:
        usage_file.parent.mkdir(parents=True, exist_ok=True)
        lock_path: Path = usage_file.with_suffix(usage_file.suffix + ".lock")
        with open(lock_path, "a", encoding="utf-8") as lock_handle:
            if fcntl is not None:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                if fcntl is not None:
                    fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
    except Exception:
        yield


def parse_positive_int(val: object) -> int | None:
    if isinstance(val, int) and not isinstance(val, bool) and val >= 1:
        return val
    if isinstance(val, float) and val >= 1:
        return int(val)
    return None


def is_continuation_read(args: dict[str, object]) -> bool:
    start_line: int | None = parse_positive_int(args.get("StartLine"))
    if start_line is not None and start_line > 1:
        return True
    byte_offset: int | None = parse_positive_int(args.get("ByteOffset"))
    if byte_offset is not None and byte_offset > 0:
        return True
    return False


def extract_skill_name_from_frontmatter(skill_file: Path) -> str | None:
    if not skill_file.is_file():
        return None
    try:
        head_text: str = skill_file.read_text(encoding="utf-8", errors="ignore")[:4096]
    except Exception:
        return None
    fm_match: re.Match[str] | None = FRONTMATTER_RE.match(head_text)
    if fm_match is None:
        return None
    name_match: re.Match[str] | None = NAME_LINE_RE.search(fm_match.group(1))
    if name_match is None:
        return None
    raw_name: str = name_match.group(1).strip().strip("\"'")
    return raw_name if raw_name else None


def resolve_skill_name(raw_path: str) -> str | None:
    if not raw_path or not raw_path.strip():
        return None
    expanded_path: Path = Path(os.path.expanduser(raw_path.strip()))
    if expanded_path.name != "SKILL.md":
        return None
    parent_parts: tuple[str, ...] = expanded_path.parent.parts
    if "skills" not in parent_parts:
        return None
    skill_dir_name: str = expanded_path.parent.name.strip()
    if not skill_dir_name or skill_dir_name == "skills":
        return None
    frontmatter_name: str | None = extract_skill_name_from_frontmatter(expanded_path)
    return frontmatter_name if frontmatter_name is not None else skill_dir_name


def extract_invoked_skill(payload: dict[str, object]) -> str | None:
    error_val: object = payload.get("error")
    if isinstance(error_val, str) and error_val.strip():
        return None

    tool_call_obj: object = payload.get("toolCall")
    if not isinstance(tool_call_obj, dict):
        return None

    tool_name_obj: object = tool_call_obj.get("name")
    if tool_name_obj != "read_file":
        return None

    args_obj: object = tool_call_obj.get("args")
    if not isinstance(args_obj, dict):
        return None

    if is_continuation_read(args_obj):
        return None

    path_obj: object = args_obj.get("Path")
    if not isinstance(path_obj, str):
        return None

    return resolve_skill_name(path_obj)


def load_skill_usage(usage_file: Path) -> dict[str, SkillUsageEntry]:
    if not usage_file.is_file():
        return {}
    try:
        content: str = usage_file.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return {}

    entries: dict[str, SkillUsageEntry] = {}
    for raw_line in content.splitlines():
        match: re.Match[str] | None = TABLE_ROW_RE.match(raw_line.strip())
        if match is None:
            continue
        skill_name: str = match.group(1).strip()
        count: int = int(match.group(2))
        last_used: str = match.group(3).strip()
        if skill_name:
            entries[skill_name] = SkillUsageEntry(
                skill_name=skill_name,
                count=count,
                last_used=last_used,
            )
    return entries


def render_skill_usage_markdown(entries: dict[str, SkillUsageEntry]) -> str:
    sorted_entries: list[SkillUsageEntry] = sorted(
        entries.values(),
        key=lambda item: (-item.count, item.skill_name),
    )
    total_uses: int = sum(item.count for item in sorted_entries)
    lines: list[str] = [
        "# Skill Usage Statistics",
        "",
        f"Total skill activations: **{total_uses}**",
        "",
        "| Skill | Uses | Last Used |",
        "| :--- | ---: | :--- |",
    ]
    for entry in sorted_entries:
        lines.append(f"| `{entry.skill_name}` | {entry.count} | {entry.last_used} |")
    lines.append("")
    return "\n".join(lines)


def record_skill_usage(
    skill_name: str,
    usage_file: Path = DEFAULT_USAGE_FILE,
    now_str: str | None = None,
) -> None:
    timestamp: str = (
        now_str
        if now_str is not None
        else datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
    )
    with usage_file_lock(usage_file):
        entries: dict[str, SkillUsageEntry] = load_skill_usage(usage_file)
        prev: SkillUsageEntry | None = entries.get(skill_name)
        new_count: int = (prev.count if prev is not None else 0) + 1
        entries[skill_name] = SkillUsageEntry(
            skill_name=skill_name,
            count=new_count,
            last_used=timestamp,
        )
        markdown: str = render_skill_usage_markdown(entries)
        try:
            usage_file.parent.mkdir(parents=True, exist_ok=True)
            tmp_file: Path = usage_file.with_suffix(".md.tmp")
            tmp_file.write_text(markdown, encoding="utf-8")
            os.replace(tmp_file, usage_file)
        except Exception:
            pass


def main() -> None:
    try:
        raw_input: str = sys.stdin.read()
        payload: object = json.loads(raw_input) if raw_input.strip() else {}
    except Exception:
        print(json.dumps({}))
        return

    if not isinstance(payload, dict):
        print(json.dumps({}))
        return

    skill_name: str | None = extract_invoked_skill(payload)
    if skill_name is not None:
        record_skill_usage(skill_name)

    print(json.dumps({}))


if __name__ == "__main__":
    main()
