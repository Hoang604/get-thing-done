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

SCRIPT_DIR: Path = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from compact_threshold_tracker import (
    parse_non_negative_int,
    resolve_transcript_file,
    sanitize_id,
)
from skill_usage_tracker import extract_invoked_skill

DEFAULT_STATE_DIR: Path = Path("/tmp/agy_loop_state")
DEFAULT_ITERATIONS: int = 3
LOOP_SKILL_NAME: str = "loop"
ITERATION_FLAG_RE: re.Pattern[str] = re.compile(r"(?:^|\s)--([1-9]\d*)\b")

LOOP_CONTINUE_USER_MESSAGE: str = (
    "Làm lại từ đầu theo @[.gemini/antigravity-cli/skills/loop/SKILL.md] một lượt nữa. "
    "Cấm dùng lại kết quả đọc từ lượt trước hay bỏ qua bất kỳ node nào vì nghĩ đã sửa xong: "
    "mở lại loop_dag.md, đi từ root xuống leaf, gọi rg và read_file đọc lại toàn bộ code trên đĩa ở từng node, "
    "soi từng dòng đối chiếu với yêu cầu của tôi và nguyên lý trong skill, "
    "sửa sạch mọi chỗ còn lệch hoặc còn residue rồi chạy test kiểm chứng lại."
)

NON_CONTINUABLE_STOP_REASONS: frozenset[str] = frozenset(
    {
        "USER_CANCELED",
        "ERROR",
        "MAX_INVOCATIONS",
        "MAX_FORCED_INVOCATIONS",
        "MAX_TOKEN_BUDGET_EXCEEDED",
        "TERMINAL_STEP_TYPE",
        "TERMINAL_CUSTOM_HOOK",
    }
)


@dataclass(frozen=True)
class LoopState:
    conversation_id: str
    active: bool = False
    target_passes: int = DEFAULT_ITERATIONS
    current_pass: int = 0
    pending_inject: bool = False
    trigger_user_input: str = ""


@contextmanager
def loop_state_lock(state_dir: Path, conv_id: str) -> Iterator[None]:
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


def load_loop_state(state_dir: Path, conv_id: str) -> LoopState:
    clean_id: str = sanitize_id(conv_id)
    state_file: Path = state_dir / f"{clean_id}.json"
    if not state_file.is_file():
        return LoopState(conversation_id=clean_id)
    try:
        raw: object = json.loads(
            state_file.read_text(encoding="utf-8", errors="ignore")
        )
    except Exception:
        return LoopState(conversation_id=clean_id)

    if not isinstance(raw, dict):
        return LoopState(conversation_id=clean_id)

    active: bool = raw.get("active") is True
    target_passes: int = parse_non_negative_int(
        raw.get("target_passes"), DEFAULT_ITERATIONS
    )
    if target_passes < 1:
        target_passes = DEFAULT_ITERATIONS
    current_pass: int = parse_non_negative_int(raw.get("current_pass"), 0)
    pending_inject: bool = raw.get("pending_inject") is True
    trigger_raw: object = raw.get("trigger_user_input")
    trigger_user_input: str = trigger_raw if isinstance(trigger_raw, str) else ""

    return LoopState(
        conversation_id=clean_id,
        active=active,
        target_passes=target_passes,
        current_pass=current_pass,
        pending_inject=pending_inject,
        trigger_user_input=trigger_user_input,
    )


def save_loop_state(state_dir: Path, state: LoopState) -> None:
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


def extract_iteration_cap(user_text: str) -> int:
    if not user_text:
        return DEFAULT_ITERATIONS
    match: re.Match[str] | None = ITERATION_FLAG_RE.search(user_text)
    if match is None:
        return DEFAULT_ITERATIONS
    return int(match.group(1))


def resolve_latest_explicit_user_input(
    payload: dict[str, object],
) -> str:
    last_user_obj: object = payload.get("lastUserInput")
    if isinstance(last_user_obj, str):
        stripped_last: str = last_user_obj.strip()
        if stripped_last and stripped_last != LOOP_CONTINUE_USER_MESSAGE:
            return stripped_last

    transcript_obj: object = payload.get("transcriptPath")
    transcript_path: str = transcript_obj if isinstance(transcript_obj, str) else ""
    target_file: Path | None = resolve_transcript_file(transcript_path)
    if target_file is None:
        return ""

    try:
        with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
            lines: list[str] = f.readlines()
    except Exception:
        return ""

    for raw_line in reversed(lines):
        line_str: str = raw_line.strip()
        if not line_str:
            continue
        try:
            step: object = json.loads(line_str)
        except Exception:
            continue
        if not isinstance(step, dict):
            continue
        if step.get("type") != "USER_INPUT" or step.get("source") == "SYSTEM":
            continue
        content_obj: object = step.get("content")
        if not isinstance(content_obj, str):
            continue
        stripped_content: str = content_obj.strip()
        if (
            not stripped_content
            or stripped_content == LOOP_CONTINUE_USER_MESSAGE
            or stripped_content.startswith("<SYSTEM_MESSAGE>")
            or "<CONTEXT_SUMMARY>" in stripped_content
        ):
            continue
        return stripped_content

    return ""


def evaluate_post_tool_use(
    payload: dict[str, object],
    state_dir: Path = DEFAULT_STATE_DIR,
) -> dict[str, object]:
    conv_id_obj: object = payload.get("conversationId")
    conv_id: str = conv_id_obj.strip() if isinstance(conv_id_obj, str) else ""
    if not conv_id:
        return {}

    invoked_skill: str | None = extract_invoked_skill(payload)
    if invoked_skill != LOOP_SKILL_NAME:
        return {}

    user_input: str = resolve_latest_explicit_user_input(payload)
    with loop_state_lock(state_dir, conv_id):
        state: LoopState = load_loop_state(state_dir, conv_id)
        if state.active and (
            not user_input or user_input == state.trigger_user_input
        ):
            return {}

        target_passes: int = extract_iteration_cap(user_input)
        new_state: LoopState = LoopState(
            conversation_id=state.conversation_id,
            active=True,
            target_passes=target_passes,
            current_pass=1,
            pending_inject=False,
            trigger_user_input=user_input,
        )
        save_loop_state(state_dir, new_state)
    return {}


def evaluate_stop(
    payload: dict[str, object],
    state_dir: Path = DEFAULT_STATE_DIR,
) -> dict[str, object]:
    conv_id_obj: object = payload.get("conversationId")
    conv_id: str = conv_id_obj.strip() if isinstance(conv_id_obj, str) else ""
    if not conv_id:
        return {"decision": "allow"}

    term_reason_obj: object = payload.get("terminationReason")
    term_reason: str = (
        term_reason_obj.strip().upper()
        if isinstance(term_reason_obj, str) and term_reason_obj.strip()
        else "NO_TOOL_CALL"
    )
    fully_idle: bool = payload.get("fullyIdle") is True

    with loop_state_lock(state_dir, conv_id):
        state: LoopState = load_loop_state(state_dir, conv_id)
        if not state.active:
            return {"decision": "allow"}

        if term_reason in NON_CONTINUABLE_STOP_REASONS:
            save_loop_state(
                state_dir,
                replace(
                    state,
                    active=False,
                    current_pass=0,
                    pending_inject=False,
                ),
            )
            return {"decision": "allow"}

        if not fully_idle:
            return {"decision": "allow"}

        if state.current_pass < state.target_passes:
            save_loop_state(
                state_dir,
                replace(state, pending_inject=True),
            )
            return {"decision": "continue"}

        save_loop_state(
            state_dir,
            replace(
                state,
                active=False,
                current_pass=0,
                pending_inject=False,
            ),
        )
        return {"decision": "allow"}


def evaluate_pre_invocation(
    payload: dict[str, object],
    state_dir: Path = DEFAULT_STATE_DIR,
) -> dict[str, object]:
    conv_id_obj: object = payload.get("conversationId")
    conv_id: str = conv_id_obj.strip() if isinstance(conv_id_obj, str) else ""
    if not conv_id:
        return {"injectSteps": []}

    user_input: str = resolve_latest_explicit_user_input(payload)
    with loop_state_lock(state_dir, conv_id):
        state: LoopState = load_loop_state(state_dir, conv_id)
        if not state.active:
            return {"injectSteps": []}

        if not state.pending_inject:
            if user_input and user_input != state.trigger_user_input:
                save_loop_state(
                    state_dir,
                    replace(
                        state,
                        active=False,
                        current_pass=0,
                        pending_inject=False,
                    ),
                )
            return {"injectSteps": []}

        next_pass: int = state.current_pass + 1
        save_loop_state(
            state_dir,
            replace(
                state,
                current_pass=next_pass,
                pending_inject=False,
            ),
        )
        return {
            "injectSteps": [
                {
                    "userMessage": LOOP_CONTINUE_USER_MESSAGE,
                }
            ]
        }


def main() -> None:
    mode: str = sys.argv[1].strip().lower() if len(sys.argv) > 1 else ""
    try:
        raw_input: str = sys.stdin.read()
        payload: object = json.loads(raw_input) if raw_input.strip() else {}
    except Exception:
        if mode == "stop":
            print(json.dumps({"decision": "allow"}))
        elif mode in ("pre_invocation", "pre"):
            print(json.dumps({"injectSteps": []}))
        else:
            print(json.dumps({}))
        return

    if not isinstance(payload, dict):
        if mode == "stop":
            print(json.dumps({"decision": "allow"}))
        elif mode in ("pre_invocation", "pre"):
            print(json.dumps({"injectSteps": []}))
        else:
            print(json.dumps({}))
        return

    if mode == "stop" or "terminationReason" in payload or "fullyIdle" in payload:
        print(json.dumps(evaluate_stop(payload)))
        return

    if mode in ("post_tool_use", "post_tool") or "toolCall" in payload:
        print(json.dumps(evaluate_post_tool_use(payload)))
        return

    print(json.dumps(evaluate_pre_invocation(payload)))


if __name__ == "__main__":
    main()
