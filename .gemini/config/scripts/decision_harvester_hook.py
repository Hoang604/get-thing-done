#!/usr/bin/env python3
import hashlib
import json
import os
import re
import sys
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

try:
    import fcntl
except ImportError:
    fcntl = None

try:
    import yaml
except ImportError:
    yaml = None

SCRIPT_DIR: Path = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from compact_threshold_tracker import (
    COMPACT_DROP_RATIO,
    is_manual_compact_in_transcript,
    parse_non_negative_int,
    resolve_transcript_file,
    sanitize_id,
)

DEFAULT_STATE_DIR: Path = Path("/tmp/agy_decision_harvester_state")
DEFAULT_CONFIG_REL_PATH: str = ".gtd/config.yml"
ALT_CONFIG_REL_PATH: str = ".gtd/config.yaml"
DEFAULT_DECISIONS_REL_DIR: str = ".gtd/decisions"
DEFAULT_EVERY_N_MESSAGES: int = 10

MANAGED_BLOCK_START: str = "<!-- GTD-DECISIONS:START -->"
MANAGED_BLOCK_END: str = "<!-- GTD-DECISIONS:END -->"

FRONTMATTER_RE: re.Pattern[str] = re.compile(
    r"\A---\s*\r?\n(.*?)\r?\n---\s*(?:\r?\n|\Z)", re.DOTALL
)
SLOT_LINE_RE: re.Pattern[str] = re.compile(
    r"^[ \t]*\{\{([a-zA-Z0-9_]+)\}\}[ \t]*\r?\n?", re.MULTILINE
)
INLINE_SLOT_RE: re.Pattern[str] = re.compile(r"\{\{([a-zA-Z0-9_]+)\}\}")

FULL_SECTION_ORDER: tuple[str, ...] = (
    "header",
    "what_to_capture",
    "partitioning",
    "file_contract",
    "execution",
)

REMINDER_SECTION_ORDER: tuple[str, ...] = (
    "header",
    "reminder",
)


def default_full_sections(decisions_dir: str) -> dict[str, str]:
    clean_dir: str = decisions_dir.rstrip("/")
    return {
        "header": (
            "Apply the following decision-harvesting instruction alongside your current task "
            "without narrating the hook itself."
        ),
        "what_to_capture": (
            f"### 1. What to Capture into `{clean_dir}/`\n"
            "Synthesize every decision from the conversation that defines how the system works—"
            "what is valid or invalid behavior, structure, invariant, or responsibility in the system—"
            "so future turns working on the codebase remain bound by it. Leave out transient task "
            "commands and execution status that do not govern how the system works.\n"
            "{{extra_capture_rules}}"
        ),
        "partitioning": (
            f"### 2. One Independent Concern per File (`{clean_dir}/<topic>.md`)\n"
            f"Partition decisions across `{clean_dir}/<topic>.md` so each file governs a single "
            "independent area of the system: decisions that a future task must consult together "
            "when working on that area share a file, and decisions governing areas that can be "
            "changed independently sit in separate files.\n"
            f"- **When** a file for that area already exists in `{clean_dir}/`, update it in place: "
            "merge new decisions, promote entries whose status changed, and delete any entry "
            "superseded or rejected by the user's latest ruling.\n"
            f"- **When** the decision governs an area with no existing file, create a new "
            f"`{clean_dir}/<topic>.md` file named after that area.\n"
            "{{partition_hints}}"
        ),
        "file_contract": (
            "### 3. File Structure & Classification Contract\n"
            f"Format every `{clean_dir}/<topic>.md` file using this exact structure:\n\n"
            "```markdown\n"
            "---\n"
            'description: "When <observable task or codebase condition touching this area>, '
            'follow the confirmed decisions and check the unconfirmed directions in this file."\n'
            "---\n\n"
            "## Confirmed\n"
            "- <Decision statement and the rationale/invariant it enforces>\n\n"
            "## Unconfirmed\n"
            "- <Candidate decision or open architectural direction still under discussion>\n"
            "```\n\n"
            "- **`description` (YAML frontmatter)**: Write a single sentence beginning with "
            "`When [condition]...` naming the observable task or code area that triggers reading "
            "this file (a hook automatically syncs this `description` and file link into "
            "`GEMINI.md` / `AGENTS.md`).\n"
            "- **`## Confirmed`**: Place a decision here if and only if it is already in the "
            "codebase and the user confirmed it is right, OR it was discussed and the user "
            "approved implementing it in code.\n"
            "- **`## Unconfirmed`**: Place all other system-shaping points discussed in the "
            "conversation here until the user confirms them in code or approves them for "
            "implementation.\n"
            "{{extra_file_rules}}"
        ),
        "execution": (
            "### 4. Execution\n"
            f"Before finishing this turn, inspect `{clean_dir}/` and write or update the affected "
            f"`{clean_dir}/<topic>.md` file(s) so every system-shaping decision from the "
            "conversation so far is recorded under its current `Confirmed` or `Unconfirmed` status.\n"
            "{{extra_execution_rules}}"
        ),
    }


def default_reminder_sections(decisions_dir: str) -> dict[str, str]:
    clean_dir: str = decisions_dir.rstrip("/")
    return {
        "header": (
            "Apply the following decision-harvesting instruction alongside your current task "
            "without narrating the hook itself."
        ),
        "reminder": (
            "Sync any new or updated system-shaping decisions from the conversation since the "
            f"last sync into `{clean_dir}/<topic>.md` (maintaining one independent concern per file, "
            "the `When ...` frontmatter `description`, and `## Confirmed` vs. `## Unconfirmed` "
            "status, promoting or removing prior entries as the user's rulings changed).\n"
            "{{extra_reminder_rules}}"
        ),
    }


@dataclass(frozen=True)
class DecisionHarvesterConfig:
    enabled: bool = False
    every_n_messages: int = DEFAULT_EVERY_N_MESSAGES
    decisions_dir: str = DEFAULT_DECISIONS_REL_DIR
    replace_full: dict[str, str] = field(default_factory=dict)
    replace_reminder: dict[str, str] = field(default_factory=dict)
    inject_slots: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class DecisionHarvesterState:
    conversation_id: str
    messages_since_cycle_start: int = 0
    injected_in_cycle: bool = False
    last_planner_turn: int = -1
    last_input_tokens: int = 0
    decisions_fingerprint: str = ""


@dataclass(frozen=True)
class DecisionFileEntry:
    rel_path: str
    description: str


@contextmanager
def harvester_state_lock(state_dir: Path, lock_name: str) -> Iterator[None]:
    clean_name: str = sanitize_id(lock_name)
    try:
        state_dir.mkdir(parents=True, exist_ok=True)
        lock_file: Path = state_dir / f"{clean_name}.lock"
        with open(lock_file, "a", encoding="utf-8") as f:
            if fcntl is not None:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                if fcntl is not None:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except Exception:
        yield


def _parse_simple_yaml_mapping(text: str) -> dict[str, object]:
    if yaml is not None:
        try:
            loaded: object = yaml.safe_load(text)
            if isinstance(loaded, dict):
                return {str(k): v for k, v in loaded.items()}
        except Exception:
            pass

    result: dict[str, object] = {}
    for raw_line in text.splitlines():
        stripped: str = raw_line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, raw_val = stripped.split(":", 1)
        clean_key: str = key.strip()
        clean_val: str = raw_val.strip().strip("\"'")
        if not clean_key:
            continue
        if clean_val.lower() == "true":
            result[clean_key] = True
        elif clean_val.lower() == "false":
            result[clean_key] = False
        elif clean_val.isdigit():
            result[clean_key] = int(clean_val)
        else:
            result[clean_key] = clean_val
    return result


def _extract_str_dict(raw: object) -> dict[str, str]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, str] = {}
    for k, v in raw.items():
        if isinstance(k, str) and isinstance(v, (str, int, float, bool)):
            out[k] = str(v)
    return out


def load_harvester_config(workspace_root: Path) -> DecisionHarvesterConfig:
    cfg_path: Path = workspace_root / DEFAULT_CONFIG_REL_PATH
    if not cfg_path.is_file():
        alt_path: Path = workspace_root / ALT_CONFIG_REL_PATH
        if alt_path.is_file():
            cfg_path = alt_path
        else:
            return DecisionHarvesterConfig(enabled=False)

    try:
        raw_text: str = cfg_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return DecisionHarvesterConfig(enabled=False)

    parsed: dict[str, object] = _parse_simple_yaml_mapping(raw_text)
    enabled_raw: object = parsed.get("enabled")
    enabled: bool = enabled_raw is True

    n_raw: object = parsed.get(
        "every_n_messages",
        parsed.get("interval", parsed.get("n_messages", DEFAULT_EVERY_N_MESSAGES)),
    )
    every_n: int = parse_non_negative_int(n_raw, DEFAULT_EVERY_N_MESSAGES)
    if every_n < 1:
        every_n = DEFAULT_EVERY_N_MESSAGES

    decisions_dir_raw: object = parsed.get("decisions_dir")
    decisions_dir: str = (
        decisions_dir_raw.strip()
        if isinstance(decisions_dir_raw, str) and decisions_dir_raw.strip()
        else DEFAULT_DECISIONS_REL_DIR
    )

    replace_full: dict[str, str] = _extract_str_dict(parsed.get("replace_full"))
    replace_reminder: dict[str, str] = _extract_str_dict(parsed.get("replace_reminder"))
    inject_slots: dict[str, str] = _extract_str_dict(parsed.get("inject"))

    prompt_obj: object = parsed.get("prompt")
    if isinstance(prompt_obj, dict):
        replace_obj: object = prompt_obj.get("replace")
        if isinstance(replace_obj, dict):
            replace_full.update(_extract_str_dict(replace_obj.get("full")))
            replace_reminder.update(_extract_str_dict(replace_obj.get("reminder")))
        inject_slots.update(_extract_str_dict(prompt_obj.get("inject")))

    return DecisionHarvesterConfig(
        enabled=enabled,
        every_n_messages=every_n,
        decisions_dir=decisions_dir,
        replace_full=replace_full,
        replace_reminder=replace_reminder,
        inject_slots=inject_slots,
    )


def _apply_slots(text: str, slots: dict[str, str]) -> str:
    def replace_line_slot(match: re.Match[str]) -> str:
        slot_name: str = match.group(1)
        val: str = slots.get(slot_name, "").strip()
        if not val:
            return ""
        newline: str = "\n" if match.group(0).endswith("\n") else ""
        return f"{val}{newline}"

    after_line_slots: str = SLOT_LINE_RE.sub(replace_line_slot, text)

    def replace_inline_slot(match: re.Match[str]) -> str:
        slot_name: str = match.group(1)
        return slots.get(slot_name, "").strip()

    return INLINE_SLOT_RE.sub(replace_inline_slot, after_line_slots).strip()


def build_full_prompt(config: DecisionHarvesterConfig) -> str:
    sections: dict[str, str] = default_full_sections(config.decisions_dir)
    assembled_parts: list[str] = []

    for sec_name in FULL_SECTION_ORDER:
        raw_section: str = (
            config.replace_full[sec_name]
            if sec_name in config.replace_full
            else sections[sec_name]
        )
        rendered: str = _apply_slots(raw_section, config.inject_slots)
        if rendered:
            assembled_parts.append(rendered)

    for extra_sec_name, extra_sec_body in config.replace_full.items():
        if extra_sec_name not in FULL_SECTION_ORDER:
            rendered_extra: str = _apply_slots(extra_sec_body, config.inject_slots)
            if rendered_extra:
                assembled_parts.append(rendered_extra)

    body: str = "\n\n".join(assembled_parts)
    return f"<critical_instructions>\n{body}\n</critical_instructions>"


def build_reminder_prompt(config: DecisionHarvesterConfig) -> str:
    sections: dict[str, str] = default_reminder_sections(config.decisions_dir)
    assembled_parts: list[str] = []

    for sec_name in REMINDER_SECTION_ORDER:
        raw_section: str = (
            config.replace_reminder[sec_name]
            if sec_name in config.replace_reminder
            else sections[sec_name]
        )
        rendered: str = _apply_slots(raw_section, config.inject_slots)
        if rendered:
            assembled_parts.append(rendered)

    for extra_sec_name, extra_sec_body in config.replace_reminder.items():
        if extra_sec_name not in REMINDER_SECTION_ORDER:
            rendered_extra: str = _apply_slots(extra_sec_body, config.inject_slots)
            if rendered_extra:
                assembled_parts.append(rendered_extra)

    body: str = "\n\n".join(assembled_parts)
    return f"<critical_instructions>\n{body}\n</critical_instructions>"


def extract_decision_description(md_file: Path) -> str | None:
    if not md_file.is_file():
        return None
    try:
        head_text: str = md_file.read_text(encoding="utf-8", errors="ignore")[:8192]
    except Exception:
        return None

    fm_match: re.Match[str] | None = FRONTMATTER_RE.match(head_text)
    if fm_match is None:
        return None

    fm_dict: dict[str, object] = _parse_simple_yaml_mapping(fm_match.group(1))
    desc_raw: object = fm_dict.get("description")
    if isinstance(desc_raw, str) and desc_raw.strip():
        return " ".join(desc_raw.strip().splitlines()).strip()
    return None


def collect_decision_entries(
    workspace_root: Path, decisions_rel_dir: str = DEFAULT_DECISIONS_REL_DIR
) -> list[DecisionFileEntry]:
    decisions_dir: Path = workspace_root / decisions_rel_dir
    if not decisions_dir.is_dir():
        return []

    entries: list[DecisionFileEntry] = []
    for md_file in sorted(decisions_dir.glob("*.md")):
        if not md_file.is_file():
            continue
        desc: str | None = extract_decision_description(md_file)
        if desc is None:
            continue
        rel_path: str = md_file.relative_to(workspace_root).as_posix()
        entries.append(DecisionFileEntry(rel_path=rel_path, description=desc))
    return entries


def compute_decisions_fingerprint(
    workspace_root: Path, decisions_rel_dir: str = DEFAULT_DECISIONS_REL_DIR
) -> str:
    decisions_dir: Path = workspace_root / decisions_rel_dir
    hasher = hashlib.sha256()
    if decisions_dir.is_dir():
        for md_file in sorted(decisions_dir.glob("*.md")):
            if not md_file.is_file():
                continue
            try:
                stat = md_file.stat()
                desc: str = extract_decision_description(md_file) or ""
                hasher.update(
                    f"{md_file.name}:{stat.st_mtime_ns}:{stat.st_size}:{desc}\n".encode(
                        "utf-8"
                    )
                )
            except Exception:
                continue
    return hasher.hexdigest()


def resolve_target_rules_file(workspace_root: Path) -> Path:
    gemini_md: Path = workspace_root / "GEMINI.md"
    if gemini_md.is_file():
        return gemini_md
    agents_md: Path = workspace_root / "AGENTS.md"
    if agents_md.is_file():
        return agents_md
    return gemini_md


def render_managed_decisions_block(entries: list[DecisionFileEntry]) -> str:
    lines: list[str] = [
        MANAGED_BLOCK_START,
        "## System Decisions",
        "",
    ]
    for entry in entries:
        lines.append(f"- [`{entry.rel_path}`]({entry.rel_path}): {entry.description}")
    lines.append(MANAGED_BLOCK_END)
    return "\n".join(lines)


def sync_decisions_index(
    workspace_root: Path, decisions_rel_dir: str = DEFAULT_DECISIONS_REL_DIR
) -> Path | None:
    entries: list[DecisionFileEntry] = collect_decision_entries(
        workspace_root, decisions_rel_dir
    )
    target_file: Path = resolve_target_rules_file(workspace_root)
    existing_exists: bool = target_file.is_file()

    if not entries and not existing_exists:
        return None

    existing_content: str = ""
    if existing_exists:
        try:
            existing_content = target_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return None

    block_pattern: re.Pattern[str] = re.compile(
        re.escape(MANAGED_BLOCK_START) + r".*?" + re.escape(MANAGED_BLOCK_END),
        re.DOTALL,
    )
    has_existing_block: bool = bool(block_pattern.search(existing_content))

    if not entries:
        if not has_existing_block:
            return None
        new_content: str = block_pattern.sub("", existing_content).rstrip() + "\n"
        if new_content == "\n":
            new_content = ""
    else:
        rendered_block: str = render_managed_decisions_block(entries)
        if has_existing_block:
            new_content = block_pattern.sub(
                lambda _: rendered_block, existing_content, count=1
            )
        elif existing_content.strip():
            new_content = existing_content.rstrip() + "\n\n" + rendered_block + "\n"
        else:
            new_content = rendered_block + "\n"

    if new_content != existing_content or not existing_exists:
        try:
            target_file.parent.mkdir(parents=True, exist_ok=True)
            tmp_file: Path = target_file.with_suffix(target_file.suffix + ".tmp")
            tmp_file.write_text(new_content, encoding="utf-8")
            os.replace(tmp_file, target_file)
        except Exception:
            return None

    return target_file


def load_harvester_state(state_dir: Path, conv_id: str) -> DecisionHarvesterState:
    clean_id: str = sanitize_id(conv_id)
    state_file: Path = state_dir / f"{clean_id}.json"
    if not state_file.is_file():
        return DecisionHarvesterState(conversation_id=clean_id)
    try:
        raw: object = json.loads(
            state_file.read_text(encoding="utf-8", errors="ignore")
        )
    except Exception:
        return DecisionHarvesterState(conversation_id=clean_id)

    if not isinstance(raw, dict):
        return DecisionHarvesterState(conversation_id=clean_id)

    msgs: int = parse_non_negative_int(raw.get("messages_since_cycle_start"), 0)
    injected_raw: object = raw.get("injected_in_cycle")
    injected: bool = injected_raw is True
    last_turn_raw: object = raw.get("last_planner_turn")
    last_turn: int = (
        last_turn_raw
        if isinstance(last_turn_raw, int) and not isinstance(last_turn_raw, bool)
        else -1
    )
    last_tokens: int = parse_non_negative_int(raw.get("last_input_tokens"), 0)
    fp_raw: object = raw.get("decisions_fingerprint")
    fp: str = fp_raw if isinstance(fp_raw, str) else ""

    return DecisionHarvesterState(
        conversation_id=clean_id,
        messages_since_cycle_start=msgs,
        injected_in_cycle=injected,
        last_planner_turn=last_turn,
        last_input_tokens=last_tokens,
        decisions_fingerprint=fp,
    )


def save_harvester_state(state_dir: Path, state: DecisionHarvesterState) -> None:
    try:
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file: Path = state_dir / f"{state.conversation_id}.json"
        payload: dict[str, object] = {
            "conversation_id": state.conversation_id,
            "messages_since_cycle_start": state.messages_since_cycle_start,
            "injected_in_cycle": state.injected_in_cycle,
            "last_planner_turn": state.last_planner_turn,
            "last_input_tokens": state.last_input_tokens,
            "decisions_fingerprint": state.decisions_fingerprint,
        }
        tmp_file: Path = state_file.with_suffix(".json.tmp")
        tmp_file.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        os.replace(tmp_file, state_file)
    except Exception:
        pass


def detect_compaction_in_transcript(
    transcript_path: str,
    last_planner_turn: int,
    last_input_tokens: int,
) -> tuple[bool, int, int]:
    """Return (compacted_since_last_turn, new_last_planner_turn, new_last_input_tokens)."""
    target_file: Path | None = resolve_transcript_file(transcript_path)
    if target_file is None:
        return False, last_planner_turn, last_input_tokens

    try:
        with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
            lines: list[str] = f.readlines()
    except Exception:
        return False, last_planner_turn, last_input_tokens

    compacted: bool = False
    cur_turn: int = last_planner_turn
    cur_tokens: int = last_input_tokens

    for line_idx, raw_line in enumerate(lines, 1):
        if line_idx <= last_planner_turn:
            continue
        line_str: str = raw_line.strip()
        if not line_str:
            continue
        try:
            step: object = json.loads(line_str)
        except Exception:
            continue
        if not isinstance(step, dict):
            continue

        step_type: object = step.get("type")
        content_obj: object = step.get("content")
        if isinstance(content_obj, str):
            stripped_content: str = content_obj.strip()
            if (
                "<CONTEXT_SUMMARY>" in stripped_content
                or stripped_content == "/compact"
                or stripped_content.startswith("/compact ")
            ):
                compacted = True

        if step_type == "PLANNER_RESPONSE":
            inp_tok: int = parse_non_negative_int(step.get("input_tokens"), 0)
            cache_tok: int = parse_non_negative_int(step.get("cache_read_tokens"), 0)
            total_in: int = inp_tok + cache_tok
            if total_in > 0:
                if cur_tokens > 0 and total_in < int(cur_tokens * COMPACT_DROP_RATIO):
                    compacted = True
                cur_tokens = total_in
                cur_turn = max(cur_turn, line_idx)

    if not compacted and last_planner_turn >= 0 and is_manual_compact_in_transcript(transcript_path):
        compacted = True

    return compacted, cur_turn, cur_tokens


def resolve_workspace_root(
    payload: dict[str, object], fallback_root: Path | None = None
) -> Path:
    base: Path = fallback_root if fallback_root is not None else Path.cwd()
    candidates: list[Path] = []

    for key in ("workspacePath", "cwd"):
        val: object = payload.get(key)
        if isinstance(val, str) and val.strip():
            candidates.append(Path(os.path.expanduser(val.strip())))

    tool_call_obj: object = payload.get("toolCall")
    if isinstance(tool_call_obj, dict):
        args_obj: object = tool_call_obj.get("args")
        if isinstance(args_obj, dict):
            for arg_key in ("Path", "Cwd"):
                arg_val: object = args_obj.get(arg_key)
                if isinstance(arg_val, str) and arg_val.strip():
                    p: Path = Path(os.path.expanduser(arg_val.strip()))
                    candidates.append(p if p.is_dir() else p.parent)

    candidates.append(base)

    for start_path in candidates:
        curr: Path = start_path.resolve()
        for ancestor in (curr, *curr.parents):
            if (ancestor / ".gtd").is_dir():
                return ancestor
    return base.resolve()


def evaluate_pre_invocation(
    conv_id: str,
    transcript_path: str,
    workspace_root: Path,
    state_dir: Path = DEFAULT_STATE_DIR,
) -> dict[str, object]:
    config: DecisionHarvesterConfig = load_harvester_config(workspace_root)
    if not config.enabled:
        return {"injectSteps": []}

    clean_conv_id: str = sanitize_id(conv_id or "default")
    with harvester_state_lock(state_dir, clean_conv_id):
        state: DecisionHarvesterState = load_harvester_state(state_dir, clean_conv_id)

        current_fp: str = compute_decisions_fingerprint(
            workspace_root, config.decisions_dir
        )
        target_rules_file: Path = resolve_target_rules_file(workspace_root)
        target_missing_block: bool = bool(
            collect_decision_entries(workspace_root, config.decisions_dir)
        ) and (
            not target_rules_file.is_file()
            or MANAGED_BLOCK_START
            not in target_rules_file.read_text(encoding="utf-8", errors="ignore")
        )

        if current_fp != state.decisions_fingerprint or target_missing_block:
            sync_decisions_index(workspace_root, config.decisions_dir)

        compacted, new_turn, new_tokens = detect_compaction_in_transcript(
            transcript_path=transcript_path,
            last_planner_turn=state.last_planner_turn,
            last_input_tokens=state.last_input_tokens,
        )

        msgs: int = 0 if compacted else state.messages_since_cycle_start
        injected_in_cycle: bool = False if compacted else state.injected_in_cycle

        msgs += 1
        inject_steps: list[dict[str, str]] = []

        if msgs >= config.every_n_messages and (msgs % config.every_n_messages == 0):
            if not injected_in_cycle:
                prompt_msg: str = build_full_prompt(config)
                injected_in_cycle = True
            else:
                prompt_msg = build_reminder_prompt(config)
            inject_steps.append({"ephemeralMessage": prompt_msg})

        updated_state = DecisionHarvesterState(
            conversation_id=clean_conv_id,
            messages_since_cycle_start=msgs,
            injected_in_cycle=injected_in_cycle,
            last_planner_turn=new_turn,
            last_input_tokens=new_tokens,
            decisions_fingerprint=current_fp,
        )
        save_harvester_state(state_dir, updated_state)
        return {"injectSteps": inject_steps}


def evaluate_post_tool_use(
    payload: dict[str, object],
    workspace_root: Path,
    state_dir: Path = DEFAULT_STATE_DIR,
) -> dict[str, object]:
    error_val: object = payload.get("error")
    if isinstance(error_val, str) and error_val.strip():
        return {}

    config: DecisionHarvesterConfig = load_harvester_config(workspace_root)
    decisions_dir: Path = workspace_root / config.decisions_dir
    if not config.enabled and not decisions_dir.is_dir():
        return {}

    conv_id_obj: object = payload.get("conversationId")
    clean_conv_id: str = sanitize_id(
        conv_id_obj if isinstance(conv_id_obj, str) else "default"
    )

    with harvester_state_lock(state_dir, clean_conv_id):
        state: DecisionHarvesterState = load_harvester_state(state_dir, clean_conv_id)
        current_fp: str = compute_decisions_fingerprint(
            workspace_root, config.decisions_dir
        )

        should_sync: bool = current_fp != state.decisions_fingerprint
        if not should_sync:
            tool_call_obj: object = payload.get("toolCall")
            if isinstance(tool_call_obj, dict):
                args_obj: object = tool_call_obj.get("args")
                if isinstance(args_obj, dict):
                    path_obj: object = args_obj.get("Path")
                    if isinstance(path_obj, str) and config.decisions_dir in path_obj:
                        should_sync = True

        if should_sync:
            sync_decisions_index(workspace_root, config.decisions_dir)
            updated_state = DecisionHarvesterState(
                conversation_id=state.conversation_id,
                messages_since_cycle_start=state.messages_since_cycle_start,
                injected_in_cycle=state.injected_in_cycle,
                last_planner_turn=state.last_planner_turn,
                last_input_tokens=state.last_input_tokens,
                decisions_fingerprint=current_fp,
            )
            save_harvester_state(state_dir, updated_state)

    return {}


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

    workspace_root: Path = resolve_workspace_root(payload)
    tool_call_obj: object = payload.get("toolCall")

    if isinstance(tool_call_obj, dict):
        post_res: dict[str, object] = evaluate_post_tool_use(
            payload=payload,
            workspace_root=workspace_root,
        )
        print(json.dumps(post_res))
        return

    conv_id_obj: object = payload.get("conversationId")
    conv_id: str = conv_id_obj if isinstance(conv_id_obj, str) else "default"
    transcript_obj: object = payload.get("transcriptPath")
    transcript_path: str = transcript_obj if isinstance(transcript_obj, str) else ""

    pre_res: dict[str, object] = evaluate_pre_invocation(
        conv_id=conv_id,
        transcript_path=transcript_path,
        workspace_root=workspace_root,
    )
    print(json.dumps(pre_res))


if __name__ == "__main__":
    main()
