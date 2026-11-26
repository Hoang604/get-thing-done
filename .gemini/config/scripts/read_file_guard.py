#!/usr/bin/env python3
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

SCRIPT_DIR: Path = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from compact_threshold_tracker import (
    DEFAULT_STATE_DIR as COMPACT_STATE_DIR,
    conversation_state_lock,
    extract_planner_input_tokens,
    is_compaction_step,
    is_compaction_token_drop,
    load_conversation_state,
    resolve_transcript_file,
    sanitize_id,
)

DEFAULT_STATE_DIR: Path = Path(
    os.environ.get("AGY_READ_FILE_GUARD_STATE_DIR", "/tmp/agy_read_file_guard_state")
)

JSON_SPILL_MIN_BYTES: int = 10_240
JSON_SPILL_SINGLE_LINE_CHARS: int = 4_000
JSON_SPILL_MAX_PRETTY_LINES: int = 80
JSON_SPILL_FEW_LINES_THRESHOLD: int = 20
JSON_PARSE_MAX_BYTES: int = 2_000_000

MAX_READ_FILE_LINES: int = 800
MAX_READ_FILE_BYTES: int = 46_080
READ_FILE_HEADER_MARGIN_BYTES: int = 1_024
MAX_TRACKED_FILE_BYTES: int = 10_000_000
MIN_EDGE_TRIM_LINES: int = 5

SPILL_OUTPUT_RE: re.Pattern[str] = re.compile(
    r"/(?:\.system_generated)/steps/[^/]+/output\.txt$"
)
JSON_FALLBACK_START_RE: re.Pattern[str] = re.compile(
    r'^(?:\{\s*"|\[\s*(?:\{|"|true|false|null|-?\d))'
)
NON_TEXT_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".bmp",
        ".ico",
        ".pdf",
        ".mp3",
        ".wav",
        ".ogg",
        ".flac",
        ".m4a",
        ".mp4",
        ".webm",
        ".mov",
        ".avi",
        ".mkv",
        ".zip",
        ".gz",
        ".tar",
        ".wasm",
        ".pb",
    }
)


@dataclass(frozen=True)
class _FileFingerprint:
    mtime_ns: int
    size: int
    sha256: str


@dataclass(frozen=True)
class _TextSnapshot:
    fingerprint: _FileFingerprint
    raw_lines: tuple[bytes, ...]


@dataclass
class _TrackedFileEntry:
    fingerprint: _FileFingerprint
    ranges: list[tuple[int, int]]


@dataclass
class _GuardState:
    compaction_count: int
    transcript_mtime_ns: int
    transcript_size: int
    transcript_compactions: int
    files: dict[str, _TrackedFileEntry]
    unblocked_files: list[str]


def _parse_int(val: object) -> int | None:
    if isinstance(val, int) and not isinstance(val, bool):
        return val
    if isinstance(val, float) and val.is_integer():
        return int(val)
    return None


def _parse_positive_int(val: object) -> int | None:
    parsed: int | None = _parse_int(val)
    return parsed if parsed is not None and parsed >= 1 else None


def _parse_non_negative_int(val: object) -> int | None:
    parsed: int | None = _parse_int(val)
    return parsed if parsed is not None and parsed >= 0 else None


def _resolve_target_path(raw_path: str, payload: dict[str, object]) -> Path:
    expanded: Path = Path(os.path.expanduser(raw_path.strip()))
    if expanded.is_absolute():
        return expanded.resolve()
    ws_paths: object = payload.get("workspacePaths")
    if isinstance(ws_paths, list):
        for item in ws_paths:
            if isinstance(item, str) and item.strip():
                return (Path(os.path.expanduser(item.strip())) / expanded).resolve()
    for key in ("workspacePath", "cwd"):
        val: object = payload.get(key)
        if isinstance(val, str) and val.strip():
            return (Path(os.path.expanduser(val.strip())) / expanded).resolve()
    return expanded.resolve()


def _is_spill_output_path(path_str: str) -> bool:
    normalized: str = path_str.replace("\\", "/")
    return bool(SPILL_OUTPUT_RE.search(normalized))


def _is_json_document(raw_text: str, size_bytes: int) -> bool:
    stripped: str = raw_text.lstrip()
    if not stripped or stripped[0] not in ("{", "["):
        return False
    if size_bytes <= JSON_PARSE_MAX_BYTES:
        try:
            parsed: object = json.loads(stripped)
        except (json.JSONDecodeError, ValueError):
            return False
        return isinstance(parsed, (dict, list))
    return bool(JSON_FALLBACK_START_RE.match(stripped[:256]))


def _check_json_spill(
    target: Path,
    args: dict[str, object],
) -> dict[str, object] | None:
    if not _is_spill_output_path(str(target)) or not target.is_file():
        return None
    try:
        st: os.stat_result = target.stat()
    except OSError:
        return None
    if st.st_size <= JSON_SPILL_MIN_BYTES:
        return None

    try:
        if st.st_size <= JSON_PARSE_MAX_BYTES:
            raw_text: str = target.read_text(encoding="utf-8", errors="ignore")
        else:
            with open(target, "r", encoding="utf-8", errors="ignore") as f:
                raw_text = f.read(65_536)
    except OSError:
        return None

    if not _is_json_document(raw_text, st.st_size):
        return None

    byte_offset: int | None = _parse_non_negative_int(args.get("ByteOffset"))
    if byte_offset is not None and byte_offset > 0:
        return {
            "decision": "deny",
            "reason": f"Blocked: {st.st_size:,}B JSON spill. Filter via run_command (jq/python3).",
        }

    lines: list[str] = raw_text.splitlines()
    has_huge_line: bool = any(
        len(line) > JSON_SPILL_SINGLE_LINE_CHARS for line in lines
    )
    unsuitable_for_line_slice: bool = (
        st.st_size > JSON_PARSE_MAX_BYTES
        or has_huge_line
        or len(lines) <= JSON_SPILL_FEW_LINES_THRESHOLD
    )
    if unsuitable_for_line_slice:
        return {
            "decision": "deny",
            "reason": f"Blocked: {st.st_size:,}B JSON spill. Filter via run_command (jq/python3).",
        }

    start_line: int | None = _parse_positive_int(args.get("StartLine"))
    end_line: int | None = _parse_positive_int(args.get("EndLine"))
    if (
        start_line is None
        or end_line is None
        or (end_line - start_line + 1) > JSON_SPILL_MAX_PRETTY_LINES
    ):
        return {
            "decision": "deny",
            "reason": (
                f"Blocked: {st.st_size:,}B JSON spill ({len(lines)}L). "
                f"Filter via run_command (jq/python3) or slice <= {JSON_SPILL_MAX_PRETTY_LINES} lines."
            ),
        }
    return None


def _read_text_snapshot(target: Path) -> _TextSnapshot | None:
    if target.suffix.lower() in NON_TEXT_EXTENSIONS or not target.is_file():
        return None
    try:
        st: os.stat_result = target.stat()
    except OSError:
        return None
    if st.st_size <= 0 or st.st_size > MAX_TRACKED_FILE_BYTES:
        return None
    try:
        raw_bytes: bytes = target.read_bytes()
    except OSError:
        return None
    if b"\x00" in raw_bytes[:8192]:
        return None
    raw_lines: tuple[bytes, ...] = tuple(raw_bytes.splitlines(keepends=True))
    if not raw_lines:
        return None
    fp: _FileFingerprint = _FileFingerprint(
        mtime_ns=st.st_mtime_ns,
        size=st.st_size,
        sha256=hashlib.sha256(raw_bytes).hexdigest(),
    )
    return _TextSnapshot(fingerprint=fp, raw_lines=raw_lines)


def _merge_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if not intervals:
        return []
    ordered: list[tuple[int, int]] = sorted(intervals)
    merged: list[tuple[int, int]] = [ordered[0]]
    for start, end in ordered[1:]:
        prev_start, prev_end = merged[-1]
        if start <= prev_end + 1:
            merged[-1] = (prev_start, max(prev_end, end))
        else:
            merged.append((start, end))
    return merged


def _subtract_intervals(
    req: tuple[int, int], covered: list[tuple[int, int]]
) -> list[tuple[int, int]]:
    req_start, req_end = req
    if req_start > req_end:
        return []
    unread: list[tuple[int, int]] = []
    cursor: int = req_start
    for cov_start, cov_end in _merge_intervals(covered):
        if cov_end < cursor:
            continue
        if cov_start > req_end:
            break
        if cov_start > cursor:
            unread.append((cursor, min(req_end, cov_start - 1)))
        cursor = max(cursor, cov_end + 1)
        if cursor > req_end:
            break
    if cursor <= req_end:
        unread.append((cursor, req_end))
    return unread


def _compute_returned_range(
    snapshot: _TextSnapshot,
    start_line: int | None,
    end_line: int | None,
) -> tuple[int, int] | None:
    total_lines: int = len(snapshot.raw_lines)
    eff_start: int = max(1, start_line if start_line is not None else 1)
    if eff_start > total_lines:
        return None
    eff_end: int = min(
        total_lines,
        max(eff_start, end_line if end_line is not None else total_lines),
        eff_start + MAX_READ_FILE_LINES - 1,
    )
    byte_budget: int = MAX_READ_FILE_BYTES - READ_FILE_HEADER_MARGIN_BYTES
    acc_bytes: int = 0
    safe_end: int = eff_start - 1
    for lineno in range(eff_start, eff_end + 1):
        prefix_len: int = len(f"{lineno}: ".encode("ascii"))
        line_len: int = len(snapshot.raw_lines[lineno - 1]) + prefix_len
        if acc_bytes + line_len > byte_budget:
            break
        acc_bytes += line_len
        safe_end = lineno
    if safe_end < eff_start:
        return None
    return (eff_start, safe_end)


def _count_transcript_compactions(transcript_file: Path) -> int:
    compactions: int = 0
    prev_tokens: int = 0
    prev_turn: int = -1
    last_compaction_turn: int = 0
    try:
        with open(transcript_file, "r", encoding="utf-8", errors="ignore") as f:
            for line_idx, raw_line in enumerate(f, 1):
                line_str: str = raw_line.strip()
                if not line_str:
                    continue
                try:
                    step: object = json.loads(line_str)
                except Exception:
                    continue
                if not isinstance(step, dict):
                    continue
                if is_compaction_step(step):
                    if last_compaction_turn == 0 or last_compaction_turn <= prev_turn:
                        compactions += 1
                    last_compaction_turn = line_idx
                    continue
                cur_tokens: int = extract_planner_input_tokens(step)
                if cur_tokens <= 0:
                    continue
                compacted_before: bool = (
                    last_compaction_turn > 0 and last_compaction_turn > prev_turn
                )
                token_drop: bool = is_compaction_token_drop(prev_tokens, cur_tokens)
                if token_drop and not compacted_before:
                    compactions += 1
                    last_compaction_turn = line_idx
                prev_tokens = cur_tokens
                prev_turn = line_idx
    except OSError:
        return 0
    return compactions


def _state_file_path(state_dir: Path, clean_conv_id: str) -> Path:
    return state_dir / f"{clean_conv_id}.json"


def _load_guard_state(state_dir: Path, clean_conv_id: str) -> _GuardState:
    path: Path = _state_file_path(state_dir, clean_conv_id)
    if not path.is_file():
        return _GuardState(0, 0, 0, 0, {}, [])
    try:
        raw: object = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return _GuardState(0, 0, 0, 0, {}, [])
    if not isinstance(raw, dict):
        return _GuardState(0, 0, 0, 0, {}, [])

    compaction_count: int = _parse_non_negative_int(raw.get("compaction_count")) or 0
    t_mtime: int = _parse_non_negative_int(raw.get("transcript_mtime_ns")) or 0
    t_size: int = _parse_non_negative_int(raw.get("transcript_size")) or 0
    t_comp: int = _parse_non_negative_int(raw.get("transcript_compactions")) or 0

    files: dict[str, _TrackedFileEntry] = {}
    files_obj: object = raw.get("files")
    if isinstance(files_obj, dict):
        for path_key, entry_obj in files_obj.items():
            if not isinstance(path_key, str) or not isinstance(entry_obj, dict):
                continue
            mtime_val: int | None = _parse_non_negative_int(entry_obj.get("mtime_ns"))
            size_val: int | None = _parse_non_negative_int(entry_obj.get("size"))
            sha_val: object = entry_obj.get("sha256")
            ranges_obj: object = entry_obj.get("ranges")
            if (
                mtime_val is None
                or size_val is None
                or not isinstance(sha_val, str)
                or not isinstance(ranges_obj, list)
            ):
                continue
            parsed_ranges: list[tuple[int, int]] = []
            for item in ranges_obj:
                if isinstance(item, list) and len(item) == 2:
                    s_val: int | None = _parse_positive_int(item[0])
                    e_val: int | None = _parse_positive_int(item[1])
                    if s_val is not None and e_val is not None and s_val <= e_val:
                        parsed_ranges.append((s_val, e_val))
            if parsed_ranges:
                files[path_key] = _TrackedFileEntry(
                    fingerprint=_FileFingerprint(mtime_val, size_val, sha_val),
                    ranges=_merge_intervals(parsed_ranges),
                )

    unblocked: list[str] = []
    unblocked_obj: object = raw.get("unblocked_files")
    if isinstance(unblocked_obj, list):
        for item in unblocked_obj:
            if isinstance(item, str) and item and item not in unblocked:
                unblocked.append(item)

    return _GuardState(
        compaction_count=compaction_count,
        transcript_mtime_ns=t_mtime,
        transcript_size=t_size,
        transcript_compactions=t_comp,
        files=files,
        unblocked_files=unblocked,
    )


def _save_guard_state(
    state_dir: Path, clean_conv_id: str, state: _GuardState
) -> None:
    try:
        state_dir.mkdir(parents=True, exist_ok=True)
        target: Path = _state_file_path(state_dir, clean_conv_id)
        files_payload: dict[str, dict[str, object]] = {}
        for path_key, entry in state.files.items():
            files_payload[path_key] = {
                "mtime_ns": entry.fingerprint.mtime_ns,
                "size": entry.fingerprint.size,
                "sha256": entry.fingerprint.sha256,
                "ranges": [[s, e] for s, e in entry.ranges],
            }
        payload: dict[str, object] = {
            "compaction_count": state.compaction_count,
            "transcript_mtime_ns": state.transcript_mtime_ns,
            "transcript_size": state.transcript_size,
            "transcript_compactions": state.transcript_compactions,
            "files": files_payload,
            "unblocked_files": state.unblocked_files,
        }
        tmp_file: Path = target.with_suffix(".json.tmp")
        tmp_file.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        os.replace(tmp_file, target)
    except OSError:
        pass


def _sync_compaction_cycle(
    state: _GuardState,
    clean_conv_id: str,
    transcript_path: str,
    compact_state_dir: Path,
) -> bool:
    dirty: bool = False
    compact_state_count: int = load_conversation_state(
        compact_state_dir, clean_conv_id
    ).compaction_count

    transcript_compactions: int = state.transcript_compactions
    t_file: Path | None = resolve_transcript_file(transcript_path, prefer_full=False)
    if t_file is not None:
        st: os.stat_result | None = None
        try:
            st = t_file.stat()
        except OSError:
            st = None
        if st is not None and (
            st.st_mtime_ns != state.transcript_mtime_ns
            or st.st_size != state.transcript_size
        ):
            transcript_compactions = _count_transcript_compactions(t_file)
            state.transcript_mtime_ns = st.st_mtime_ns
            state.transcript_size = st.st_size
            state.transcript_compactions = transcript_compactions
            dirty = True

    effective_compactions: int = max(compact_state_count, transcript_compactions)
    if effective_compactions != state.compaction_count:
        state.compaction_count = effective_compactions
        state.files.clear()
        state.unblocked_files.clear()
        dirty = True
    return dirty


def evaluate_pre_tool_use(
    payload: dict[str, object],
    state_dir: Path = DEFAULT_STATE_DIR,
    compact_state_dir: Path = COMPACT_STATE_DIR,
) -> dict[str, object]:
    tool_call_obj: object = payload.get("toolCall")
    if not isinstance(tool_call_obj, dict) or tool_call_obj.get("name") != "read_file":
        return {"decision": "allow"}

    args_obj: object = tool_call_obj.get("args")
    if not isinstance(args_obj, dict):
        return {"decision": "allow"}

    path_obj: object = args_obj.get("Path")
    if not isinstance(path_obj, str) or not path_obj.strip():
        return {"decision": "allow"}

    target: Path = _resolve_target_path(path_obj, payload)

    spill_decision: dict[str, object] | None = _check_json_spill(target, args_obj)
    if spill_decision is not None:
        return spill_decision

    byte_offset: int | None = _parse_non_negative_int(args_obj.get("ByteOffset"))
    if byte_offset is not None and byte_offset > 0:
        return {"decision": "allow"}

    conv_id_obj: object = payload.get("conversationId")
    if not isinstance(conv_id_obj, str) or not conv_id_obj.strip():
        return {"decision": "allow"}
    clean_conv_id: str = sanitize_id(conv_id_obj)

    transcript_obj: object = payload.get("transcriptPath")
    transcript_path: str = transcript_obj if isinstance(transcript_obj, str) else ""

    snapshot: _TextSnapshot | None = _read_text_snapshot(target)
    if snapshot is None:
        return {"decision": "allow"}

    total_lines: int = len(snapshot.raw_lines)
    start_line: int | None = _parse_positive_int(args_obj.get("StartLine"))
    end_line: int | None = _parse_positive_int(args_obj.get("EndLine"))
    req_start: int = max(1, start_line if start_line is not None else 1)
    if req_start > total_lines:
        return {"decision": "allow"}
    req_end: int = min(
        total_lines,
        max(req_start, end_line if end_line is not None else total_lines),
        req_start + MAX_READ_FILE_LINES - 1,
    )

    path_key: str = str(target)
    with conversation_state_lock(state_dir, clean_conv_id):
        state: _GuardState = _load_guard_state(state_dir, clean_conv_id)
        dirty: bool = _sync_compaction_cycle(
            state, clean_conv_id, transcript_path, compact_state_dir
        )

        if path_key in state.unblocked_files:
            if dirty:
                _save_guard_state(state_dir, clean_conv_id, state)
            return {"decision": "allow"}

        entry: _TrackedFileEntry | None = state.files.get(path_key)
        if entry is None:
            if dirty:
                _save_guard_state(state_dir, clean_conv_id, state)
            return {"decision": "allow"}

        if entry.fingerprint != snapshot.fingerprint:
            del state.files[path_key]
            _save_guard_state(state_dir, clean_conv_id, state)
            return {"decision": "allow"}

        if dirty:
            _save_guard_state(state_dir, clean_conv_id, state)

        unread: list[tuple[int, int]] = _subtract_intervals(
            (req_start, req_end), entry.ranges
        )
        if not unread:
            return {
                "decision": "deny",
                "reason": f"Blocked: L{req_start}-L{req_end} already in context (unchanged).",
            }

        new_start: int = unread[0][0]
        new_end: int = unread[-1][1]
        trimmed_lines: int = (new_start - req_start) + (req_end - new_end)
        if trimmed_lines < MIN_EDGE_TRIM_LINES:
            return {"decision": "allow"}

        overwrite: dict[str, int] = {}
        if new_start > req_start:
            overwrite["StartLine"] = new_start
        if new_end < req_end:
            overwrite["EndLine"] = new_end
        return {
            "decision": "allow",
            "overwrite": overwrite,
        }


def evaluate_post_tool_use(
    payload: dict[str, object],
    state_dir: Path = DEFAULT_STATE_DIR,
    compact_state_dir: Path = COMPACT_STATE_DIR,
) -> dict[str, object]:
    conv_id_obj: object = payload.get("conversationId")
    if not isinstance(conv_id_obj, str) or not conv_id_obj.strip():
        return {}
    clean_conv_id: str = sanitize_id(conv_id_obj)

    tool_call_obj: object = payload.get("toolCall")
    if not isinstance(tool_call_obj, dict):
        return {}
    tool_name_obj: object = tool_call_obj.get("name")
    tool_name: str = tool_name_obj if isinstance(tool_name_obj, str) else ""
    if tool_name not in ("read_file", "edit_file", "write_file"):
        return {}

    args_obj: object = tool_call_obj.get("args")
    if not isinstance(args_obj, dict):
        return {}
    path_obj: object = args_obj.get("Path")
    if not isinstance(path_obj, str) or not path_obj.strip():
        return {}

    target: Path = _resolve_target_path(path_obj, payload)
    path_key: str = str(target)

    error_obj: object = payload.get("error")
    has_error: bool = isinstance(error_obj, str) and bool(error_obj.strip())

    transcript_obj: object = payload.get("transcriptPath")
    transcript_path: str = transcript_obj if isinstance(transcript_obj, str) else ""

    with conversation_state_lock(state_dir, clean_conv_id):
        state: _GuardState = _load_guard_state(state_dir, clean_conv_id)
        dirty: bool = _sync_compaction_cycle(
            state, clean_conv_id, transcript_path, compact_state_dir
        )

        if tool_name in ("edit_file", "write_file"):
            if path_key in state.files:
                del state.files[path_key]
                dirty = True
            if tool_name == "edit_file" and has_error:
                if path_key not in state.unblocked_files:
                    state.unblocked_files.append(path_key)
                    dirty = True
            if dirty:
                _save_guard_state(state_dir, clean_conv_id, state)
            return {}

        if has_error:
            if dirty:
                _save_guard_state(state_dir, clean_conv_id, state)
            return {}

        byte_offset: int | None = _parse_non_negative_int(args_obj.get("ByteOffset"))
        if byte_offset is not None and byte_offset > 0:
            if dirty:
                _save_guard_state(state_dir, clean_conv_id, state)
            return {}

        if path_key in state.unblocked_files:
            if dirty:
                _save_guard_state(state_dir, clean_conv_id, state)
            return {}

        snapshot: _TextSnapshot | None = _read_text_snapshot(target)
        if snapshot is None:
            if dirty:
                _save_guard_state(state_dir, clean_conv_id, state)
            return {}

        returned_range: tuple[int, int] | None = _compute_returned_range(
            snapshot,
            _parse_positive_int(args_obj.get("StartLine")),
            _parse_positive_int(args_obj.get("EndLine")),
        )
        if returned_range is None:
            if dirty:
                _save_guard_state(state_dir, clean_conv_id, state)
            return {}

        prev_entry: _TrackedFileEntry | None = state.files.get(path_key)
        if prev_entry is not None and prev_entry.fingerprint == snapshot.fingerprint:
            merged: list[tuple[int, int]] = _merge_intervals(
                [*prev_entry.ranges, returned_range]
            )
        else:
            merged = [returned_range]

        state.files[path_key] = _TrackedFileEntry(
            fingerprint=snapshot.fingerprint,
            ranges=merged,
        )
        _save_guard_state(state_dir, clean_conv_id, state)
        return {}


def main() -> None:
    mode: str = sys.argv[1].strip().lower() if len(sys.argv) > 1 else "pre"
    try:
        raw_input: str = sys.stdin.read()
        payload: object = json.loads(raw_input) if raw_input.strip() else {}
    except Exception:
        print(json.dumps({} if mode == "post" else {"decision": "allow"}))
        return

    if not isinstance(payload, dict):
        print(json.dumps({} if mode == "post" else {"decision": "allow"}))
        return

    if mode == "post":
        print(json.dumps(evaluate_post_tool_use(payload)))
    else:
        print(json.dumps(evaluate_pre_tool_use(payload)))


if __name__ == "__main__":
    main()
