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
    sanitize_id,
)

DEFAULT_STATE_DIR: Path = Path("/tmp/agy_loop_state")
DEFAULT_ITERATIONS: int = 3
LOOP_COMMAND_RE: re.Pattern[str] = re.compile(r"^/loop\b")
ITERATION_FLAG_RE: re.Pattern[str] = re.compile(r"(?:^|\s)--([1-9]\d*)\b")
SKILL_REL_CANDIDATES: tuple[Path, ...] = (
    Path(".gemini/antigravity-cli/skills/loop/SKILL.md"),
    Path(".gemini/config/skills/loop/SKILL.md"),
    Path(".agents/skills/loop/SKILL.md"),
)


def resolve_loop_skill_path(payload: dict[str, object]) -> str:
    ws_obj: object = payload.get("workspacePaths")
    if isinstance(ws_obj, list):
        for item in ws_obj:
            if not isinstance(item, str) or not item.strip():
                continue
            ws_root: Path = Path(os.path.expanduser(item.strip()))
            for rel_path in SKILL_REL_CANDIDATES:
                candidate: Path = ws_root / rel_path
                if candidate.is_file():
                    return str(candidate.resolve())

    gemini_root: Path = SCRIPT_DIR.parent.parent
    for rel_sub in (
        Path("antigravity-cli/skills/loop/SKILL.md"),
        Path("config/skills/loop/SKILL.md"),
    ):
        script_candidate: Path = gemini_root / rel_sub
        if script_candidate.is_file():
            return str(script_candidate.resolve())

    home_dir: Path = Path.home()
    for rel_path in SKILL_REL_CANDIDATES:
        home_candidate: Path = home_dir / rel_path
        if home_candidate.is_file():
            return str(home_candidate.resolve())

    return str(home_dir / ".gemini/antigravity-cli/skills/loop/SKILL.md")


def build_continue_user_message(payload: dict[str, object]) -> str:
    skill_path: str = resolve_loop_skill_path(payload)
    return (
        f"Làm lại từ đầu theo @[{skill_path}] một lượt nữa. "
        "Cấm dùng lại kết quả đọc từ lượt trước hay bỏ qua bất kỳ node nào vì nghĩ đã sửa xong: "
        "mở lại loop_dag.md, đi từ root xuống leaf, gọi rg và read_file đọc lại toàn bộ code trên đĩa ở từng node, "
        "soi từng dòng đối chiếu với yêu cầu của tôi và nguyên lý trong skill, "
        "sửa sạch mọi chỗ còn lệch hoặc còn residue."
    )

NON_CONTINUABLE_STOP_REASONS: frozenset[str] = frozenset(
    {
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

    return LoopState(
        conversation_id=clean_id,
        active=active,
        target_passes=target_passes,
        current_pass=current_pass,
        pending_inject=pending_inject,
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


def is_loop_invocation(user_text: str) -> bool:
    if not user_text:
        return False
    return LOOP_COMMAND_RE.search(user_text) is not None


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

        if term_reason == "USER_CANCELED":
            if state.pending_inject:
                save_loop_state(
                    state_dir,
                    replace(state, pending_inject=False),
                )
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

    with loop_state_lock(state_dir, conv_id):
        state: LoopState = load_loop_state(state_dir, conv_id)
        if state.active:
            if not state.pending_inject:
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
                        "userMessage": build_continue_user_message(payload),
                    }
                ]
            }

        last_user_obj: object = payload.get("lastUserInput")
        user_input: str = (
            last_user_obj.strip() if isinstance(last_user_obj, str) else ""
        )
        if not is_loop_invocation(user_input):
            return {"injectSteps": []}

        target_passes: int = extract_iteration_cap(user_input)
        save_loop_state(
            state_dir,
            LoopState(
                conversation_id=state.conversation_id,
                active=True,
                target_passes=target_passes,
                current_pass=1,
                pending_inject=False,
            ),
        )
        return {"injectSteps": []}


def main() -> None:
    mode: str = sys.argv[1].strip().lower() if len(sys.argv) > 1 else ""
    try:
        raw_input: str = sys.stdin.read()
        payload: object = json.loads(raw_input) if raw_input.strip() else {}
    except Exception:
        if mode == "stop":
            print(json.dumps({"decision": "allow"}))
        else:
            print(json.dumps({"injectSteps": []}))
        return

    if not isinstance(payload, dict):
        if mode == "stop":
            print(json.dumps({"decision": "allow"}))
        else:
            print(json.dumps({"injectSteps": []}))
        return

    if mode == "stop" or "terminationReason" in payload or "fullyIdle" in payload:
        print(json.dumps(evaluate_stop(payload)))
        return

    print(json.dumps(evaluate_pre_invocation(payload)))


if __name__ == "__main__":
    main()
