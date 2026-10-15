#!/usr/bin/env python3
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_COMPACT_THRESHOLD: int = 240_000
MIN_AUTO_COMPACT_TOKENS: int = 160_000
COMPACT_DROP_RATIO: float = 0.65

DEFAULT_STATE_DIR: Path = Path("/tmp/agy_compact_state")
DEFAULT_THRESHOLDS_FILE: Path = Path.home() / ".gemini" / "config" / "compact_thresholds.json"


@dataclass(frozen=True)
class StatuslineSnapshot:
    turn_num: int
    total_input_tokens: int
    model_id: str


@dataclass(frozen=True)
class ModelThresholdEntry:
    compact_threshold: int
    max_safe_tokens: int
    last_auto_compact_tokens: int


@dataclass(frozen=True)
class ConversationTokenState:
    conversation_id: str
    model_id: str
    last_turn: int
    last_tokens: int
    warned_in_cycle: bool
    warned_at_tokens: int


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


def compute_effective_threshold(max_safe_tokens: int, last_auto_compact_tokens: int) -> int:
    base: int = last_auto_compact_tokens if last_auto_compact_tokens >= MIN_AUTO_COMPACT_TOKENS else DEFAULT_COMPACT_THRESHOLD
    return max(base, max_safe_tokens, MIN_AUTO_COMPACT_TOKENS)


def load_thresholds_db(thresholds_file: Path) -> dict[str, ModelThresholdEntry]:
    if not thresholds_file.is_file():
        return {}
    try:
        raw: object = json.loads(thresholds_file.read_text(encoding="utf-8", errors="ignore"))
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
            max_safe: int = parse_non_negative_int(v.get("max_safe_tokens"), 0)
            last_auto: int = parse_non_negative_int(v.get("last_auto_compact_tokens"), 0)
            result[k] = ModelThresholdEntry(
                compact_threshold=compute_effective_threshold(max_safe, last_auto),
                max_safe_tokens=max_safe,
                last_auto_compact_tokens=last_auto,
            )
    return result


def save_thresholds_db(thresholds_file: Path, db: dict[str, ModelThresholdEntry]) -> None:
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
        tmp_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        os.replace(tmp_file, thresholds_file)
    except Exception:
        pass


def load_conversation_state(state_dir: Path, conv_id: str) -> ConversationTokenState:
    state_file: Path = state_dir / f"{conv_id}.json"
    if not state_file.is_file():
        return ConversationTokenState(
            conversation_id=conv_id,
            model_id="",
            last_turn=-1,
            last_tokens=0,
            warned_in_cycle=False,
            warned_at_tokens=0,
        )
    try:
        raw: object = json.loads(state_file.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return ConversationTokenState(
            conversation_id=conv_id,
            model_id="",
            last_turn=-1,
            last_tokens=0,
            warned_in_cycle=False,
            warned_at_tokens=0,
        )

    if not isinstance(raw, dict):
        return ConversationTokenState(
            conversation_id=conv_id,
            model_id="",
            last_turn=-1,
            last_tokens=0,
            warned_in_cycle=False,
            warned_at_tokens=0,
        )

    model_id_raw: object = raw.get("model_id")
    model_id: str = model_id_raw if isinstance(model_id_raw, str) else ""
    last_turn_raw: object = raw.get("last_turn")
    last_turn: int = last_turn_raw if isinstance(last_turn_raw, int) and not isinstance(last_turn_raw, bool) else -1
    last_tokens: int = parse_non_negative_int(raw.get("last_tokens"), 0)
    warned_raw: object = raw.get("warned_in_cycle")
    warned: bool = warned_raw if isinstance(warned_raw, bool) else False
    warned_at: int = parse_non_negative_int(raw.get("warned_at_tokens"), 0)

    return ConversationTokenState(
        conversation_id=conv_id,
        model_id=model_id,
        last_turn=last_turn,
        last_tokens=last_tokens,
        warned_in_cycle=warned,
        warned_at_tokens=warned_at,
    )


def save_conversation_state(state_dir: Path, state: ConversationTokenState) -> None:
    try:
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file: Path = state_dir / f"{state.conversation_id}.json"
        payload: dict[str, object] = {
            "conversation_id": state.conversation_id,
            "model_id": state.model_id,
            "last_turn": state.last_turn,
            "last_tokens": state.last_tokens,
            "warned_in_cycle": state.warned_in_cycle,
            "warned_at_tokens": state.warned_at_tokens,
        }
        tmp_file: Path = state_file.with_suffix(".json.tmp")
        tmp_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        os.replace(tmp_file, state_file)
    except Exception:
        pass


def resolve_transcript_file(transcript_path: str) -> Path | None:
    if not transcript_path or not transcript_path.strip():
        return None
    raw: str = transcript_path.strip()
    candidates: list[str] = [raw]
    if "/.gemini/antigravity/" in raw:
        candidates.append(raw.replace("/.gemini/antigravity/", "/.gemini/antigravity-cli/"))
    elif "/.gemini/antigravity-cli/" in raw:
        candidates.append(raw.replace("/.gemini/antigravity-cli/", "/.gemini/antigravity/"))

    for cand in candidates:
        p: Path = Path(cand)
        if p.is_file():
            return p
        compact_p: Path = p.with_name("transcript.jsonl")
        if compact_p.is_file():
            return compact_p
        full_p: Path = p.with_name("transcript_full.jsonl")
        if full_p.is_file():
            return full_p
    return None


def is_manual_compact_in_transcript(transcript_path: str) -> bool:
    target_file: Path | None = resolve_transcript_file(transcript_path)
    if target_file is None:
        return False
    try:
        with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
            lines: list[str] = f.readlines()
    except Exception:
        return False

    for line in reversed(lines[-30:]):
        line_str: str = line.strip()
        if not line_str:
            continue
        try:
            step: object = json.loads(line_str)
        except Exception:
            continue
        if not isinstance(step, dict):
            continue
        if step.get("type") == "USER_INPUT" and step.get("source") != "SYSTEM":
            content: object = step.get("content")
            if isinstance(content, str):
                stripped: str = content.strip()
                return stripped == "/compact" or stripped.startswith("/compact ")
    return False


def collect_transcript_snapshots(
    transcript_path: str,
    fallback_model_name: str,
    after_turn: int,
) -> list[StatuslineSnapshot]:
    target_file: Path | None = resolve_transcript_file(transcript_path)
    if target_file is None:
        return []

    try:
        with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
            lines: list[str] = f.readlines()
    except Exception:
        return []

    snapshots: list[StatuslineSnapshot] = []
    model_str: str = fallback_model_name.strip()

    for line_idx, raw_line in enumerate(lines, 1):
        if line_idx <= after_turn:
            continue
        line_str: str = raw_line.strip()
        if not line_str:
            continue
        try:
            step: object = json.loads(line_str)
        except Exception:
            continue
        if not isinstance(step, dict) or step.get("type") != "PLANNER_RESPONSE":
            continue

        inp_tokens: int = parse_non_negative_int(step.get("input_tokens"), 0)
        cache_read_tokens: int = parse_non_negative_int(step.get("cache_read_tokens"), 0)
        total_in: int = inp_tokens + cache_read_tokens
        if total_in > 0:
            snapshots.append(
                StatuslineSnapshot(
                    turn_num=line_idx,
                    total_input_tokens=total_in,
                    model_id=model_str,
                )
            )

    return snapshots


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

    snapshots: list[StatuslineSnapshot] = collect_transcript_snapshots(
        transcript_path=transcript_path,
        fallback_model_name=fallback_model_name,
        after_turn=state.last_turn,
    )

    cur_model: str = resolve_model_key(db, state.model_id or fallback_model_name or "default")
    prev_tokens: int = state.last_tokens
    prev_turn: int = state.last_turn
    warned_in_cycle: bool = state.warned_in_cycle
    warned_at_tokens: int = state.warned_at_tokens
    db_dirty: bool = False

    for idx, snap in enumerate(snapshots):
        if snap.model_id:
            cur_model = resolve_model_key(db, snap.model_id)

        entry: ModelThresholdEntry = db.get(
            cur_model,
            ModelThresholdEntry(
                compact_threshold=DEFAULT_COMPACT_THRESHOLD,
                max_safe_tokens=0,
                last_auto_compact_tokens=0,
            ),
        )

        cur_tokens: int = snap.total_input_tokens
        if prev_tokens > 0 and cur_tokens < int(prev_tokens * COMPACT_DROP_RATIO):
            # Compaction drop detected: reset 90% warning flag for the new post-compact cycle
            warned_in_cycle = False
            warned_at_tokens = 0

            is_latest_transition: bool = idx == len(snapshots) - 1
            manual_compact: bool = is_manual_compact_in_transcript(transcript_path) if is_latest_transition else False

            if prev_tokens >= MIN_AUTO_COMPACT_TOKENS and not manual_compact:
                new_last_auto: int = prev_tokens
                new_threshold: int = compute_effective_threshold(entry.max_safe_tokens, new_last_auto)
                db[cur_model] = ModelThresholdEntry(
                    compact_threshold=new_threshold,
                    max_safe_tokens=entry.max_safe_tokens,
                    last_auto_compact_tokens=new_last_auto,
                )
                db_dirty = True
        else:
            # Normal non-compacting progression: prev_tokens survived without auto-compact
            candidate_safe: int = max(entry.max_safe_tokens, prev_tokens)
            if candidate_safe > entry.max_safe_tokens or cur_model not in db:
                new_threshold = compute_effective_threshold(candidate_safe, entry.last_auto_compact_tokens)
                db[cur_model] = ModelThresholdEntry(
                    compact_threshold=new_threshold,
                    max_safe_tokens=candidate_safe,
                    last_auto_compact_tokens=entry.last_auto_compact_tokens,
                )
                db_dirty = True

        prev_tokens = cur_tokens
        prev_turn = max(prev_turn, snap.turn_num)

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

    new_state: ConversationTokenState = ConversationTokenState(
        conversation_id=clean_conv_id,
        model_id=cur_model,
        last_turn=prev_turn,
        last_tokens=prev_tokens,
        warned_in_cycle=warned_in_cycle,
        warned_at_tokens=warned_at_tokens,
    )
    if new_state != state:
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

    sync_conversation_and_thresholds(
        conv_id=conv_id,
        fallback_model_name=model_name,
        transcript_path=transcript_path,
    )
    print(json.dumps({}))


if __name__ == "__main__":
    main()
