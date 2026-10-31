#!/usr/bin/env python3
import json
import os
import re
import sys
from contextlib import contextmanager
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Iterator

try:
    import fcntl
except ImportError:
    fcntl = None

DEFAULT_COMPACT_THRESHOLD: int = 240_000
MAX_COMPACT_THRESHOLD: int = 250_000
MIN_AUTO_COMPACT_TOKENS: int = 160_000
COMPACT_DROP_RATIO: float = 0.65
CHARS_PER_TOKEN: float = 3.0
MAX_READ_FILE_LINES: int = 800
MAX_READ_FILE_BYTES: int = 46_080
GUARDED_COMMAND_RE: re.Pattern[str] = re.compile(r"\b(?:rg|grep|cat)\b")

DEFAULT_STATE_DIR: Path = Path(
    os.environ.get("AGY_COMPACT_STATE_DIR", "/tmp/agy_compact_state")
)
DEFAULT_THRESHOLDS_FILE: Path = Path(
    os.environ.get(
        "AGY_THRESHOLDS_FILE",
        str(Path.home() / ".gemini" / "config" / "compact_thresholds.json"),
    )
)


@dataclass(frozen=True)
class ModelThresholdEntry:
    compact_threshold: int
    max_safe_tokens: int
    last_auto_compact_tokens: int


@dataclass(frozen=True)
class ConversationTokenState:
    conversation_id: str
    model_id: str = ""
    last_turn: int = -1
    last_tokens: int = 0
    warned_in_cycle: bool = False
    warned_at_tokens: int = 0
    blocked_at_planner_turn: int = 0
    pending_turn_tokens: int = 0
    post_resumed_at_planner_turn: int = 0
    stop_resumed_at_planner_turn: int = 0
    post_planner_tokens: int = 0
    effective_tokens: int = 0
    has_premature_summary: bool = False
    compaction_count: int = 0
    last_compaction_turn: int = 0
    last_scanned_line: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "effective_tokens",
            compute_effective_tokens(
                self.last_tokens,
                self.pending_turn_tokens,
                self.post_planner_tokens,
            ),
        )


PREMATURE_SUMMARY_TAG_RE: re.Pattern[str] = re.compile(
    r"^[ \t]*</?summary>[ \t]*$|(?:^|\n)[ \t]*<summary>[ \t]*\r?\n[ \t]*(?:#{1,6}|\d+[\.\)]|[-*]|\*\*)",
    re.IGNORECASE | re.MULTILINE,
)
PREMATURE_SUMMARY_HEADING_RE: re.Pattern[str] = re.compile(
    r"^[ \t]*(?:#{1,6}[ \t]*(?:\d+[\.\)][ \t]*)?|(?:\d+[\.\)]|[-*])[ \t]+\*{0,2}|\*{2})"
    r"(?:Context for governing[ \t]+`?#?[ \t]*User Requests`?|Read-next working set|Settled state and open work)\b",
    re.IGNORECASE | re.MULTILINE,
)


@contextmanager
def conversation_state_lock(state_dir: Path, conv_id: str) -> Iterator[None]:
    clean_id: str = sanitize_id(conv_id)
    try:
        state_dir.mkdir(parents=True, exist_ok=True)
        lock_file: Path = state_dir / f"{clean_id}.lock"
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


def sanitize_id(raw_id: object) -> str:
    if not isinstance(raw_id, str) or not raw_id.strip():
        return "default"
    cleaned: str = re.sub(r"[^a-zA-Z0-9_\-]", "_", raw_id.strip())
    return cleaned if cleaned else "default"


def parse_non_negative_int(val: object, fallback: int = 0) -> int:
    if isinstance(val, int) and not isinstance(val, bool) and val >= 0:
        return val
    if isinstance(val, float) and val >= 0:
        return int(val)
    return fallback


def compute_effective_tokens(
    last_tokens: int,
    pending_turn_tokens: int,
    post_planner_tokens: int,
    incoming_tokens: int = 0,
) -> int:
    return (
        max(0, last_tokens)
        + max(0, pending_turn_tokens, post_planner_tokens)
        + max(0, incoming_tokens)
    )


def compute_usage_percentage(
    tokens: int, threshold: int, fallback: float = 0.0
) -> float:
    if threshold <= 0:
        return fallback
    return (max(0, tokens) / threshold) * 100.0


def apply_incoming_tool_tokens(
    state: ConversationTokenState, incoming_tokens: int
) -> ConversationTokenState:
    accumulated: int = max(state.pending_turn_tokens, state.post_planner_tokens) + max(
        0, incoming_tokens
    )
    return replace(state, pending_turn_tokens=accumulated)


def estimate_read_file_tokens(args: dict[str, object]) -> int:
    filepath_obj: object = args.get("Path")
    if not isinstance(filepath_obj, str) or not os.path.isfile(filepath_obj):
        return 0
    try:
        with open(filepath_obj, "r", encoding="utf-8", errors="ignore") as f:
            lines: list[str] = f.readlines()
    except Exception:
        return 0

    total_lines: int = len(lines)
    if total_lines == 0:
        return 0

    start_raw: int = parse_non_negative_int(args.get("StartLine"), 1)
    start_line: int = max(1, start_raw)
    end_raw: int = parse_non_negative_int(args.get("EndLine"), total_lines)
    end_line: int = min(total_lines, max(start_line, end_raw))
    end_line = min(end_line, start_line + MAX_READ_FILE_LINES - 1)

    selected: list[str] = lines[start_line - 1 : end_line]
    raw_chars: int = sum(len(line) + 6 for line in selected)
    capped_chars: int = min(raw_chars, MAX_READ_FILE_BYTES)
    return int(capped_chars / CHARS_PER_TOKEN)


def is_guarded_run_command(args: dict[str, object]) -> bool:
    cmd_obj: object = args.get("CommandLine")
    if not isinstance(cmd_obj, str) or not cmd_obj.strip():
        return False
    return bool(GUARDED_COMMAND_RE.search(cmd_obj))


def estimate_cat_command_tokens(args: dict[str, object]) -> int:
    cmd_obj: object = args.get("CommandLine")
    if not isinstance(cmd_obj, str) or not re.search(r"\bcat\b", cmd_obj):
        return 0
    cwd_obj: object = args.get("Cwd")
    base_dir: Path = (
        Path(cwd_obj) if isinstance(cwd_obj, str) and cwd_obj.strip() else Path.cwd()
    )
    total_chars: int = 0
    for token in re.findall(r"[^\s|;&><\"']+", cmd_obj):
        if token in ("cat", "-") or token.startswith("-"):
            continue
        candidate: Path = Path(token) if os.path.isabs(token) else base_dir / token
        if candidate.is_file():
            try:
                total_chars += min(candidate.stat().st_size, MAX_READ_FILE_BYTES)
            except Exception:
                pass
    return int(total_chars / CHARS_PER_TOKEN)


def estimate_tool_call_tokens(tool_call: dict[str, object]) -> int | None:
    tool_name_obj: object = tool_call.get("name")
    tool_name: str = tool_name_obj if isinstance(tool_name_obj, str) else ""
    args_obj: object = tool_call.get("args")
    args: dict[str, object] = args_obj if isinstance(args_obj, dict) else {}

    if tool_name == "read_file":
        return estimate_read_file_tokens(args)
    if tool_name == "run_command" and is_guarded_run_command(args):
        return estimate_cat_command_tokens(args)
    return None


def extract_planner_input_tokens(step: dict[str, object]) -> int:
    if step.get("type") != "PLANNER_RESPONSE":
        return 0
    inp_tokens: int = parse_non_negative_int(step.get("input_tokens"), 0)
    cache_read_tokens: int = parse_non_negative_int(step.get("cache_read_tokens"), 0)
    return inp_tokens + cache_read_tokens


def is_compaction_token_drop(prev_tokens: int, cur_tokens: int) -> bool:
    return (
        prev_tokens > 0
        and cur_tokens > 0
        and cur_tokens < int(prev_tokens * COMPACT_DROP_RATIO)
    )


def is_compaction_step(step: dict[str, object]) -> bool:
    step_type: object = step.get("type")
    if step_type == "CHECKPOINT":
        return True
    content_obj: object = step.get("content")
    if isinstance(content_obj, str):
        stripped: str = content_obj.strip()
        if (
            "<CONTEXT_SUMMARY>" in stripped
            or stripped == "/compact"
            or stripped.startswith("/compact ")
        ):
            return True
    return False


def compute_effective_threshold(
    max_safe_tokens: int, last_auto_compact_tokens: int
) -> int:
    clamped_safe: int = min(max_safe_tokens, MAX_COMPACT_THRESHOLD)
    clamped_auto: int = (
        min(last_auto_compact_tokens, MAX_COMPACT_THRESHOLD)
        if last_auto_compact_tokens > 0
        else 0
    )
    base: int = (
        clamped_auto
        if clamped_auto >= MIN_AUTO_COMPACT_TOKENS
        else DEFAULT_COMPACT_THRESHOLD
    )
    return min(max(base, clamped_safe, MIN_AUTO_COMPACT_TOKENS), MAX_COMPACT_THRESHOLD)


def load_thresholds_db(thresholds_file: Path) -> dict[str, ModelThresholdEntry]:
    if not thresholds_file.is_file():
        return {}
    try:
        raw: object = json.loads(
            thresholds_file.read_text(encoding="utf-8", errors="ignore")
        )
    except Exception:
        return {}

    if not isinstance(raw, dict):
        return {}

    models_obj: object = raw.get("models")
    if not isinstance(models_obj, dict):
        return {}

    result: dict[str, ModelThresholdEntry] = {}
    for k, v in models_obj.items():
        if isinstance(k, str) and isinstance(v, dict):
            max_safe: int = min(
                parse_non_negative_int(v.get("max_safe_tokens"), 0),
                MAX_COMPACT_THRESHOLD,
            )
            last_auto: int = min(
                parse_non_negative_int(v.get("last_auto_compact_tokens"), 0),
                MAX_COMPACT_THRESHOLD,
            )
            result[k] = ModelThresholdEntry(
                compact_threshold=compute_effective_threshold(max_safe, last_auto),
                max_safe_tokens=max_safe,
                last_auto_compact_tokens=last_auto,
            )
    return result


def save_thresholds_db(
    thresholds_file: Path, db: dict[str, ModelThresholdEntry]
) -> None:
    try:
        thresholds_file.parent.mkdir(parents=True, exist_ok=True)
        models_dict: dict[str, dict[str, int]] = {}
        for k, entry in sorted(db.items()):
            models_dict[k] = {
                "compact_threshold": entry.compact_threshold,
                "max_safe_tokens": entry.max_safe_tokens,
                "last_auto_compact_tokens": entry.last_auto_compact_tokens,
            }
        payload: dict[str, object] = {
            "default_threshold": DEFAULT_COMPACT_THRESHOLD,
            "models": models_dict,
        }
        tmp_file: Path = thresholds_file.with_suffix(".json.tmp")
        tmp_file.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        os.replace(tmp_file, thresholds_file)
    except Exception:
        pass


def load_conversation_state(state_dir: Path, conv_id: str) -> ConversationTokenState:
    state_file: Path = state_dir / f"{conv_id}.json"
    if not state_file.is_file():
        return ConversationTokenState(conversation_id=conv_id)
    try:
        raw: object = json.loads(
            state_file.read_text(encoding="utf-8", errors="ignore")
        )
    except Exception:
        return ConversationTokenState(conversation_id=conv_id)
    if not isinstance(raw, dict):
        return ConversationTokenState(conversation_id=conv_id)

    model_id_raw: object = raw.get("model_id")
    last_turn_raw: object = raw.get("last_turn")
    return ConversationTokenState(
        conversation_id=conv_id,
        model_id=model_id_raw if isinstance(model_id_raw, str) else "",
        last_turn=(
            last_turn_raw
            if isinstance(last_turn_raw, int) and not isinstance(last_turn_raw, bool)
            else -1
        ),
        last_tokens=parse_non_negative_int(raw.get("last_tokens"), 0),
        warned_in_cycle=raw.get("warned_in_cycle") is True,
        warned_at_tokens=parse_non_negative_int(raw.get("warned_at_tokens"), 0),
        blocked_at_planner_turn=parse_non_negative_int(
            raw.get("blocked_at_planner_turn"), 0
        ),
        pending_turn_tokens=parse_non_negative_int(raw.get("pending_turn_tokens"), 0),
        post_resumed_at_planner_turn=parse_non_negative_int(
            raw.get("post_resumed_at_planner_turn"), 0
        ),
        stop_resumed_at_planner_turn=parse_non_negative_int(
            raw.get("stop_resumed_at_planner_turn"), 0
        ),
        post_planner_tokens=parse_non_negative_int(raw.get("post_planner_tokens"), 0),
        has_premature_summary=raw.get("has_premature_summary") is True,
        compaction_count=parse_non_negative_int(raw.get("compaction_count"), 0),
        last_compaction_turn=parse_non_negative_int(raw.get("last_compaction_turn"), 0),
        last_scanned_line=parse_non_negative_int(raw.get("last_scanned_line"), 0),
    )


def save_conversation_state(state_dir: Path, state: ConversationTokenState) -> None:
    try:
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file: Path = state_dir / f"{state.conversation_id}.json"
        tmp_file: Path = state_file.with_suffix(".json.tmp")
        tmp_file.write_text(
            json.dumps(asdict(state), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        os.replace(tmp_file, state_file)
    except Exception:
        pass


def resolve_transcript_file(
    transcript_path: str, prefer_full: bool = False
) -> Path | None:
    if not transcript_path or not transcript_path.strip():
        return None
    raw: str = transcript_path.strip()
    candidates: list[str] = [raw]
    if "/.gemini/antigravity/" in raw:
        candidates.append(
            raw.replace("/.gemini/antigravity/", "/.gemini/antigravity-cli/")
        )
    elif "/.gemini/antigravity-cli/" in raw:
        candidates.append(
            raw.replace("/.gemini/antigravity-cli/", "/.gemini/antigravity/")
        )

    for cand in candidates:
        p: Path = Path(cand)
        if prefer_full:
            full_p: Path = p.with_name("transcript_full.jsonl")
            if full_p.is_file():
                return full_p
            if p.is_file():
                return p
            compact_p: Path = p.with_name("transcript.jsonl")
            if compact_p.is_file():
                return compact_p
        else:
            if p.is_file():
                return p
            compact_p = p.with_name("transcript.jsonl")
            if compact_p.is_file():
                return compact_p
            full_p = p.with_name("transcript_full.jsonl")
            if full_p.is_file():
                return full_p
    return None


def is_premature_summary_text(text: str) -> bool:
    if not text or not text.strip():
        return False
    return bool(
        PREMATURE_SUMMARY_TAG_RE.search(text)
        or PREMATURE_SUMMARY_HEADING_RE.search(text)
    )


def model_slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")


def resolve_model_key(db: dict[str, ModelThresholdEntry], raw_model: str) -> str:
    cleaned: str = raw_model.strip() or "default"
    if cleaned in db:
        return cleaned
    target_slug: str = model_slug(cleaned)
    if target_slug:
        for existing_key in db:
            if model_slug(existing_key) == target_slug:
                return existing_key
    return cleaned


def sync_conversation_and_thresholds(
    conv_id: str,
    fallback_model_name: str,
    transcript_path: str,
    state_dir: Path = DEFAULT_STATE_DIR,
    thresholds_file: Path = DEFAULT_THRESHOLDS_FILE,
) -> tuple[ConversationTokenState, ModelThresholdEntry]:
    clean_conv_id: str = sanitize_id(conv_id)
    state: ConversationTokenState = load_conversation_state(state_dir, clean_conv_id)
    db: dict[str, ModelThresholdEntry] = load_thresholds_db(thresholds_file)

    cur_model: str = resolve_model_key(
        db, state.model_id or fallback_model_name or "default"
    )
    prev_tokens: int = state.last_tokens
    prev_turn: int = state.last_turn
    warned_in_cycle: bool = state.warned_in_cycle
    warned_at_tokens: int = state.warned_at_tokens
    blocked_at_planner_turn: int = state.blocked_at_planner_turn
    pending_turn_tokens: int = state.pending_turn_tokens
    post_resumed_at_planner_turn: int = state.post_resumed_at_planner_turn
    stop_resumed_at_planner_turn: int = state.stop_resumed_at_planner_turn
    compaction_count: int = state.compaction_count
    last_compaction_turn: int = state.last_compaction_turn
    start_after: int = max(state.last_turn, state.last_scanned_line, 0)
    scan_from: int = max(0, state.last_turn - 1) if state.last_turn > 0 else 0
    last_scanned_line: int = start_after
    planner_out_tokens: int = 0
    post_chars: int = 0
    has_premature_summary: bool = state.has_premature_summary
    db_dirty: bool = False

    target_file: Path | None = resolve_transcript_file(
        transcript_path, prefer_full=True
    )
    lines: list[str] = []
    if target_file is not None:
        try:
            with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception:
            lines = []

    saw_manual_compact: bool = False
    model_str: str = fallback_model_name.strip()

    for line_idx, raw_line in enumerate(lines, 1):
        if line_idx <= scan_from:
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
        cur_tokens: int = extract_planner_input_tokens(step)
        content_obj: object = step.get("content")
        error_obj: object = step.get("error")

        if step_type == "PLANNER_RESPONSE" and cur_tokens > 0:
            planner_out_tokens = parse_non_negative_int(step.get("output_tokens"), 0)
            post_chars = 0
            has_premature_summary = is_premature_summary_text(
                content_obj if isinstance(content_obj, str) else ""
            )
        elif prev_turn > 0 or line_idx > start_after:
            if is_compaction_step(step):
                planner_out_tokens = 0
                post_chars = 0
                has_premature_summary = False
            else:
                if step_type == "USER_INPUT" and step.get("source") != "SYSTEM":
                    has_premature_summary = False
                if isinstance(content_obj, str):
                    post_chars += len(content_obj)
                if isinstance(error_obj, str):
                    post_chars += len(error_obj)

        if line_idx <= start_after:
            continue
        last_scanned_line = max(last_scanned_line, line_idx)

        if is_compaction_step(step):
            warned_in_cycle = False
            warned_at_tokens = 0
            blocked_at_planner_turn = 0
            post_resumed_at_planner_turn = 0
            stop_resumed_at_planner_turn = 0
            pending_turn_tokens = 0
            if last_compaction_turn <= prev_turn:
                compaction_count += 1
            last_compaction_turn = line_idx
            if (
                step_type == "USER_INPUT"
                and step.get("source") != "SYSTEM"
                and isinstance(content_obj, str)
                and (
                    content_obj.strip() == "/compact"
                    or content_obj.strip().startswith("/compact ")
                )
            ):
                saw_manual_compact = True
            continue

        if cur_tokens <= 0:
            continue

        if model_str:
            cur_model = resolve_model_key(db, model_str)

        entry: ModelThresholdEntry = db.get(
            cur_model,
            ModelThresholdEntry(
                compact_threshold=DEFAULT_COMPACT_THRESHOLD,
                max_safe_tokens=0,
                last_auto_compact_tokens=0,
            ),
        )

        pending_turn_tokens = 0
        compacted_before_planner: bool = (
            last_compaction_turn > 0 and last_compaction_turn > prev_turn
        )
        token_drop: bool = is_compaction_token_drop(prev_tokens, cur_tokens)

        if token_drop or compacted_before_planner:
            warned_in_cycle = False
            warned_at_tokens = 0
            blocked_at_planner_turn = 0
            post_resumed_at_planner_turn = 0
            stop_resumed_at_planner_turn = 0
            if not compacted_before_planner:
                compaction_count += 1
            last_compaction_turn = line_idx

            if (
                token_drop
                and prev_tokens >= MIN_AUTO_COMPACT_TOKENS
                and not saw_manual_compact
            ):
                new_last_auto: int = min(prev_tokens, MAX_COMPACT_THRESHOLD)
                new_threshold: int = compute_effective_threshold(
                    entry.max_safe_tokens, new_last_auto
                )
                db[cur_model] = ModelThresholdEntry(
                    compact_threshold=new_threshold,
                    max_safe_tokens=entry.max_safe_tokens,
                    last_auto_compact_tokens=new_last_auto,
                )
                db_dirty = True
            saw_manual_compact = False
        else:
            candidate_safe: int = min(
                max(entry.max_safe_tokens, prev_tokens), MAX_COMPACT_THRESHOLD
            )
            if candidate_safe > entry.max_safe_tokens or cur_model not in db:
                new_threshold = compute_effective_threshold(
                    candidate_safe, entry.last_auto_compact_tokens
                )
                db[cur_model] = ModelThresholdEntry(
                    compact_threshold=new_threshold,
                    max_safe_tokens=candidate_safe,
                    last_auto_compact_tokens=entry.last_auto_compact_tokens,
                )
                db_dirty = True

        prev_tokens = cur_tokens
        prev_turn = max(prev_turn, line_idx)

    final_entry: ModelThresholdEntry = db.get(
        cur_model,
        ModelThresholdEntry(
            compact_threshold=DEFAULT_COMPACT_THRESHOLD,
            max_safe_tokens=0,
            last_auto_compact_tokens=0,
        ),
    )

    if db_dirty:
        save_thresholds_db(thresholds_file, db)

    post_planner_tokens: int = (
        0
        if (last_compaction_turn > 0 and last_compaction_turn > prev_turn)
        else (
            planner_out_tokens + int(post_chars / CHARS_PER_TOKEN)
            if prev_turn > 0
            else 0
        )
    )

    new_state: ConversationTokenState = ConversationTokenState(
        conversation_id=clean_conv_id,
        model_id=cur_model,
        last_turn=prev_turn,
        last_tokens=prev_tokens,
        warned_in_cycle=warned_in_cycle,
        warned_at_tokens=warned_at_tokens,
        blocked_at_planner_turn=blocked_at_planner_turn,
        pending_turn_tokens=pending_turn_tokens,
        post_resumed_at_planner_turn=post_resumed_at_planner_turn,
        stop_resumed_at_planner_turn=stop_resumed_at_planner_turn,
        post_planner_tokens=post_planner_tokens,
        has_premature_summary=has_premature_summary,
        compaction_count=compaction_count,
        last_compaction_turn=last_compaction_turn,
        last_scanned_line=max(last_scanned_line, prev_turn),
    )
    if new_state != state or not (state_dir / f"{clean_conv_id}.json").is_file():
        save_conversation_state(state_dir, new_state)

    return new_state, final_entry


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

    conv_id_obj: object = payload.get("conversationId")
    conv_id: str = conv_id_obj if isinstance(conv_id_obj, str) else ""
    if not conv_id:
        print(json.dumps({}))
        return

    model_obj: object = payload.get("modelName")
    model_name: str = model_obj if isinstance(model_obj, str) else ""

    transcript_obj: object = payload.get("transcriptPath")
    transcript_path: str = transcript_obj if isinstance(transcript_obj, str) else ""

    with conversation_state_lock(DEFAULT_STATE_DIR, conv_id):
        sync_conversation_and_thresholds(
            conv_id=conv_id,
            fallback_model_name=model_name,
            transcript_path=transcript_path,
        )
    print(json.dumps({}))


if __name__ == "__main__":
    main()
