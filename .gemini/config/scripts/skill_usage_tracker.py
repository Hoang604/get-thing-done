#!/usr/bin/env python3
import json
import os
import re
import sys
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterator, Sequence

try:
    import fcntl
except ImportError:
    fcntl = None

SCRIPT_DIR: Path = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from compact_threshold_tracker import (
    conversation_state_lock,
    resolve_transcript_file,
    sanitize_id,
)

DEFAULT_USAGE_FILE: Path = Path.home() / ".gemini" / "skill_usage.md"
DEFAULT_STATE_DIR: Path = Path("/tmp/agy_skill_usage_state")
FRONTMATTER_RE: re.Pattern[str] = re.compile(
    r"\A---\s*\r?\n(.*?)\r?\n---\s*(?:\r?\n|\Z)", re.DOTALL
)
NAME_LINE_RE: re.Pattern[str] = re.compile(r"^name:\s*(.+?)\s*$", re.MULTILINE)
TABLE_ROW_RE: re.Pattern[str] = re.compile(
    r"^\|\s*`([^`]+)`\s*\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|$"
)
SLASH_COMMAND_RE: re.Pattern[str] = re.compile(
    r"^\s*/([A-Za-z0-9][A-Za-z0-9_.:-]*)(?=\s|$)"
)

SKILL_DIR_REL_CANDIDATES: tuple[Path, ...] = (
    Path(".gemini/antigravity-cli/skills"),
    Path(".gemini/config/skills"),
    Path(".gemini/skills"),
    Path(".agents/skills"),
    Path(".agent/skills"),
    Path(".claude/skills"),
)
GLOBAL_BUILTIN_SKILL_RELS: tuple[Path, ...] = (
    Path(".gemini/antigravity-cli/builtin/skills"),
    Path(".gemini/antigravity/builtin/skills"),
    Path(".gemini/antigravity-ide/builtin/skills"),
)
PLUGIN_SKILL_GLOBS: tuple[str, ...] = (
    ".gemini/config/plugins/*/skills",
    ".gemini/antigravity-cli/plugins/*/skills",
)


@dataclass(frozen=True)
class SkillUsageEntry:
    skill_name: str
    count: int
    last_used: str


@dataclass(frozen=True)
class SkillTurnState:
    conversation_id: str
    turn_key: str = ""
    recorded_skills: tuple[str, ...] = ()
    user_turn_count: int = 0
    last_user_input: str = ""


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


def _append_unique_dir(roots: list[Path], seen: set[Path], candidate: Path) -> None:
    if not candidate.is_dir():
        return
    try:
        resolved: Path = candidate.resolve()
    except Exception:
        resolved = candidate
    if resolved not in seen:
        seen.add(resolved)
        roots.append(candidate)


def collect_skill_roots(
    payload: dict[str, object], home_dir: Path | None = None
) -> list[Path]:
    roots: list[Path] = []
    seen: set[Path] = set()

    base_dirs: list[Path] = []
    ws_paths_obj: object = payload.get("workspacePaths")
    if isinstance(ws_paths_obj, list):
        for item in ws_paths_obj:
            if isinstance(item, str) and item.strip():
                base_dirs.append(Path(os.path.expanduser(item.strip())))
    for key in ("workspacePath", "cwd"):
        val: object = payload.get(key)
        if isinstance(val, str) and val.strip():
            base_dirs.append(Path(os.path.expanduser(val.strip())))

    for ws_dir in base_dirs:
        for rel in SKILL_DIR_REL_CANDIDATES:
            _append_unique_dir(roots, seen, ws_dir / rel)
        for glob_pat in PLUGIN_SKILL_GLOBS:
            for match_dir in sorted(ws_dir.glob(glob_pat)):
                _append_unique_dir(roots, seen, match_dir)

    home_root: Path = home_dir if home_dir is not None else Path.home()
    for rel in (*SKILL_DIR_REL_CANDIDATES, *GLOBAL_BUILTIN_SKILL_RELS):
        _append_unique_dir(roots, seen, home_root / rel)
    for glob_pat in PLUGIN_SKILL_GLOBS:
        for match_dir in sorted(home_root.glob(glob_pat)):
            _append_unique_dir(roots, seen, match_dir)

    return roots


def resolve_slash_skill_name(
    user_input: str, skill_roots: Sequence[Path]
) -> str | None:
    if not user_input:
        return None
    match: re.Match[str] | None = SLASH_COMMAND_RE.match(user_input)
    if match is None:
        return None
    command_name: str = match.group(1)

    for root in skill_roots:
        skill_file: Path = root / command_name / "SKILL.md"
        if skill_file.is_file():
            frontmatter_name: str | None = extract_skill_name_from_frontmatter(
                skill_file
            )
            return frontmatter_name if frontmatter_name is not None else command_name

    for root in skill_roots:
        if not root.is_dir():
            continue
        try:
            children: list[Path] = sorted(root.iterdir())
        except Exception:
            continue
        for child in children:
            if not child.is_dir():
                continue
            skill_file = child / "SKILL.md"
            if skill_file.is_file() and (
                extract_skill_name_from_frontmatter(skill_file) == command_name
            ):
                return command_name

    return None


def _turn_state_file(state_dir: Path, clean_conv_id: str) -> Path:
    return state_dir / f"{clean_conv_id}.json"


def load_turn_state(state_dir: Path, clean_conv_id: str) -> SkillTurnState:
    state_file: Path = _turn_state_file(state_dir, clean_conv_id)
    if not state_file.is_file():
        return SkillTurnState(conversation_id=clean_conv_id)
    try:
        raw: object = json.loads(
            state_file.read_text(encoding="utf-8", errors="ignore")
        )
    except Exception:
        return SkillTurnState(conversation_id=clean_conv_id)

    if not isinstance(raw, dict):
        return SkillTurnState(conversation_id=clean_conv_id)

    turn_key_obj: object = raw.get("turn_key")
    turn_key: str = turn_key_obj if isinstance(turn_key_obj, str) else ""

    recorded_obj: object = raw.get("recorded_skills")
    recorded_skills: tuple[str, ...] = (
        tuple(
            item.strip()
            for item in recorded_obj
            if isinstance(item, str) and item.strip()
        )
        if isinstance(recorded_obj, list)
        else ()
    )

    turn_count_obj: object = raw.get("user_turn_count")
    user_turn_count: int = (
        turn_count_obj
        if isinstance(turn_count_obj, int)
        and not isinstance(turn_count_obj, bool)
        and turn_count_obj >= 0
        else 0
    )

    last_input_obj: object = raw.get("last_user_input")
    last_user_input: str = last_input_obj if isinstance(last_input_obj, str) else ""

    return SkillTurnState(
        conversation_id=clean_conv_id,
        turn_key=turn_key,
        recorded_skills=recorded_skills,
        user_turn_count=user_turn_count,
        last_user_input=last_user_input,
    )


def save_turn_state(state_dir: Path, state: SkillTurnState) -> None:
    try:
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file: Path = _turn_state_file(state_dir, state.conversation_id)
        payload: dict[str, object] = asdict(state)
        payload["recorded_skills"] = list(state.recorded_skills)
        tmp_file: Path = state_file.with_suffix(".json.tmp")
        tmp_file.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        os.replace(tmp_file, state_file)
    except Exception:
        pass


def resolve_current_user_turn(transcript_path: str) -> tuple[str | None, int]:
    target_file: Path | None = resolve_transcript_file(
        transcript_path, prefer_full=False
    )
    if target_file is None:
        return None, 0

    try:
        with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
            lines: list[str] = f.readlines()
    except Exception:
        return None, 0

    user_turn_count: int = 0
    latest_explicit: tuple[int, dict[str, object]] | None = None
    latest_non_system: tuple[int, dict[str, object]] | None = None

    for line_idx, raw_line in enumerate(lines, 1):
        line_str: str = raw_line.strip()
        if not line_str:
            continue
        try:
            step: object = json.loads(line_str)
        except Exception:
            continue
        if not isinstance(step, dict):
            continue
        if step.get("type") != "USER_INPUT":
            continue
        source: object = step.get("source")
        if source == "SYSTEM":
            continue
        user_turn_count += 1
        latest_non_system = (line_idx, step)
        if source == "USER_EXPLICIT":
            latest_explicit = (line_idx, step)

    chosen: tuple[int, dict[str, object]] | None = (
        latest_explicit if latest_explicit is not None else latest_non_system
    )
    if chosen is None:
        return None, 0

    chosen_line, chosen_step = chosen
    step_idx_obj: object = chosen_step.get("step_index")
    base_key: str = (
        f"step:{step_idx_obj}"
        if isinstance(step_idx_obj, int) and not isinstance(step_idx_obj, bool)
        else f"line:{chosen_line}"
    )
    created_at_obj: object = chosen_step.get("created_at")
    turn_key: str = (
        f"{base_key}:{created_at_obj.strip()}"
        if isinstance(created_at_obj, str) and created_at_obj.strip()
        else base_key
    )
    return turn_key, user_turn_count


def evaluate_pre_invocation(
    payload: dict[str, object],
    usage_file: Path = DEFAULT_USAGE_FILE,
    state_dir: Path = DEFAULT_STATE_DIR,
    home_dir: Path | None = None,
    skill_roots: Sequence[Path] | None = None,
    now_str: str | None = None,
) -> dict[str, object]:
    last_user_obj: object = payload.get("lastUserInput")
    if not isinstance(last_user_obj, str) or not last_user_obj.strip():
        return {"injectSteps": []}

    roots: Sequence[Path] = (
        skill_roots
        if skill_roots is not None
        else collect_skill_roots(payload, home_dir=home_dir)
    )
    skill_name: str | None = resolve_slash_skill_name(last_user_obj, roots)
    if skill_name is None:
        return {"injectSteps": []}

    clean_conv_id: str = sanitize_id(payload.get("conversationId"))
    transcript_obj: object = payload.get("transcriptPath")
    transcript_path: str = transcript_obj if isinstance(transcript_obj, str) else ""
    normalized_input: str = last_user_obj.strip()

    with conversation_state_lock(state_dir, clean_conv_id):
        state: SkillTurnState = load_turn_state(state_dir, clean_conv_id)
        transcript_turn_key, user_count = resolve_current_user_turn(transcript_path)

        if transcript_turn_key is not None:
            if (
                state.turn_key == f"no_transcript:{normalized_input}"
                and user_count == 1
                and skill_name in state.recorded_skills
            ):
                save_turn_state(
                    state_dir,
                    SkillTurnState(
                        conversation_id=clean_conv_id,
                        turn_key=transcript_turn_key,
                        recorded_skills=state.recorded_skills,
                        user_turn_count=user_count,
                        last_user_input=normalized_input,
                    ),
                )
                return {"injectSteps": []}
            effective_turn_key: str = transcript_turn_key
        else:
            effective_turn_key = f"no_transcript:{normalized_input}"

        recorded: list[str] = (
            list(state.recorded_skills) if state.turn_key == effective_turn_key else []
        )
        if skill_name not in recorded:
            record_skill_usage(skill_name, usage_file=usage_file, now_str=now_str)
            recorded.append(skill_name)

        save_turn_state(
            state_dir,
            SkillTurnState(
                conversation_id=clean_conv_id,
                turn_key=effective_turn_key,
                recorded_skills=tuple(recorded),
                user_turn_count=user_count,
                last_user_input=normalized_input,
            ),
        )

    return {"injectSteps": []}


def evaluate_post_tool_use(
    payload: dict[str, object],
    usage_file: Path = DEFAULT_USAGE_FILE,
    state_dir: Path = DEFAULT_STATE_DIR,
    now_str: str | None = None,
) -> dict[str, object]:
    skill_name: str | None = extract_invoked_skill(payload)
    if skill_name is None:
        return {}

    conv_id_obj: object = payload.get("conversationId")
    if not isinstance(conv_id_obj, str) or not conv_id_obj.strip():
        record_skill_usage(skill_name, usage_file=usage_file, now_str=now_str)
        return {}

    clean_conv_id: str = sanitize_id(conv_id_obj)
    transcript_obj: object = payload.get("transcriptPath")
    transcript_path: str = transcript_obj if isinstance(transcript_obj, str) else ""

    with conversation_state_lock(state_dir, clean_conv_id):
        state: SkillTurnState = load_turn_state(state_dir, clean_conv_id)
        transcript_turn_key, user_count = resolve_current_user_turn(transcript_path)

        if transcript_turn_key is not None:
            recorded: list[str] = (
                list(state.recorded_skills)
                if state.turn_key == transcript_turn_key
                else []
            )
            if skill_name in recorded:
                return {}
            record_skill_usage(skill_name, usage_file=usage_file, now_str=now_str)
            recorded.append(skill_name)
            save_turn_state(
                state_dir,
                SkillTurnState(
                    conversation_id=clean_conv_id,
                    turn_key=transcript_turn_key,
                    recorded_skills=tuple(recorded),
                    user_turn_count=user_count,
                    last_user_input=state.last_user_input,
                ),
            )
            return {}

        last_user_obj: object = payload.get("lastUserInput")
        norm_input: str = (
            last_user_obj.strip() if isinstance(last_user_obj, str) else ""
        )
        if (
            norm_input
            and state.turn_key == f"no_transcript:{norm_input}"
            and skill_name in state.recorded_skills
        ):
            return {}

        record_skill_usage(skill_name, usage_file=usage_file, now_str=now_str)

    return {}


def is_pre_invocation_mode(mode_arg: str, payload: object) -> bool:
    if mode_arg in ("pre", "pre_invocation"):
        return True
    if mode_arg in ("post", "post_tool_use"):
        return False
    if isinstance(payload, dict):
        hook_event: object = payload.get("hookEventName")
        if hook_event == "PreInvocation":
            return True
        if hook_event == "PostToolUse":
            return False
        if "toolCall" not in payload:
            return True
    return False


def main() -> None:
    mode_arg: str = sys.argv[1].strip().lower() if len(sys.argv) > 1 else ""
    try:
        raw_input: str = sys.stdin.read()
        payload: object = json.loads(raw_input) if raw_input.strip() else {}
    except Exception:
        print(
            json.dumps(
                {"injectSteps": []}
                if is_pre_invocation_mode(mode_arg, None)
                else {}
            )
        )
        return

    if not isinstance(payload, dict):
        print(
            json.dumps(
                {"injectSteps": []}
                if is_pre_invocation_mode(mode_arg, None)
                else {}
            )
        )
        return

    if is_pre_invocation_mode(mode_arg, payload):
        print(json.dumps(evaluate_pre_invocation(payload)))
        return

    print(json.dumps(evaluate_post_tool_use(payload)))


if __name__ == "__main__":
    main()
