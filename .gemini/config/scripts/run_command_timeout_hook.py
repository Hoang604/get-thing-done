#!/usr/bin/env python3
import json
import os
import re
import shlex
import subprocess
import sys
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Callable, Iterator

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

DEFAULT_STATE_DIR: Path = Path(
    os.environ.get("AGY_RUN_CMD_TIMEOUT_STATE_DIR", "/tmp/agy_run_cmd_timeout_state")
)
TIMEOUT_SECONDS: int = 300
DEFAULT_POLL_INTERVAL_SECONDS: float = 1.0

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

TASK_ID_RE: re.Pattern[str] = re.compile(
    r"(?:Task\s*ID|TaskId)\s*[:=]\s*([A-Za-z0-9_/\-]+)",
    re.IGNORECASE,
)

SHELL_BUILTINS: frozenset[str] = frozenset(
    {"cd", "export", "unset", "true", "false", "echo", "printf", "pwd"}
)


@dataclass(frozen=True)
class TrackedCommandTask:
    step_idx: int
    command_line: str
    tool_summary: str
    started_at: float
    notified: bool = False
    pending_inject: bool = False
    elapsed_at_trigger: int = 0
    task_id: str = ""


@dataclass(frozen=True)
class TimeoutHookState:
    conversation_id: str
    tasks: tuple[TrackedCommandTask, ...] = ()
    manage_task_authorized: bool = False


@contextmanager
def timeout_state_lock(state_dir: Path, conv_id: str) -> Iterator[None]:
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


def _parse_task(raw: object) -> TrackedCommandTask | None:
    if not isinstance(raw, dict):
        return None
    cmd_obj: object = raw.get("command_line")
    if not isinstance(cmd_obj, str) or not cmd_obj.strip():
        return None
    started_obj: object = raw.get("started_at")
    if not isinstance(started_obj, (int, float)) or isinstance(started_obj, bool):
        return None
    started_at: float = float(started_obj)
    if started_at <= 0:
        return None

    summary_obj: object = raw.get("tool_summary")
    tool_summary: str = summary_obj.strip() if isinstance(summary_obj, str) else ""
    task_id_obj: object = raw.get("task_id")
    task_id: str = task_id_obj.strip() if isinstance(task_id_obj, str) else ""

    return TrackedCommandTask(
        step_idx=parse_non_negative_int(raw.get("step_idx"), 0),
        command_line=cmd_obj.strip(),
        tool_summary=tool_summary,
        started_at=started_at,
        notified=raw.get("notified") is True,
        pending_inject=raw.get("pending_inject") is True,
        elapsed_at_trigger=parse_non_negative_int(raw.get("elapsed_at_trigger"), 0),
        task_id=task_id,
    )


def load_timeout_state(state_dir: Path, conv_id: str) -> TimeoutHookState:
    clean_id: str = sanitize_id(conv_id)
    state_file: Path = state_dir / f"{clean_id}.json"
    if not state_file.is_file():
        return TimeoutHookState(conversation_id=clean_id)
    try:
        raw: object = json.loads(
            state_file.read_text(encoding="utf-8", errors="ignore")
        )
    except Exception:
        return TimeoutHookState(conversation_id=clean_id)
    if not isinstance(raw, dict):
        return TimeoutHookState(conversation_id=clean_id)

    tasks_raw: object = raw.get("tasks")
    tasks: list[TrackedCommandTask] = []
    if isinstance(tasks_raw, list):
        for item in tasks_raw:
            parsed: TrackedCommandTask | None = _parse_task(item)
            if parsed is not None:
                tasks.append(parsed)

    return TimeoutHookState(
        conversation_id=clean_id,
        tasks=tuple(tasks),
        manage_task_authorized=raw.get("manage_task_authorized") is True,
    )


def save_timeout_state(state_dir: Path, state: TimeoutHookState) -> None:
    try:
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file: Path = state_dir / f"{state.conversation_id}.json"
        payload: dict[str, object] = {
            "conversation_id": state.conversation_id,
            "tasks": [asdict(t) for t in state.tasks],
            "manage_task_authorized": state.manage_task_authorized,
        }
        tmp_file: Path = state_file.with_suffix(".json.tmp")
        tmp_file.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        os.replace(tmp_file, state_file)
    except Exception:
        pass


def is_manage_task_authorized_for_conversation(
    conv_id: str,
    state_dir: Path | None = None,
) -> bool:
    if not conv_id or not conv_id.strip():
        return False
    effective_dir: Path = (
        state_dir
        if state_dir is not None
        else Path(
            os.environ.get("AGY_RUN_CMD_TIMEOUT_STATE_DIR", str(DEFAULT_STATE_DIR))
        )
    )
    state: TimeoutHookState = load_timeout_state(effective_dir, conv_id)
    if state.manage_task_authorized:
        return True
    return any(t.notified or t.pending_inject for t in state.tasks)


def is_background_intended(args: dict[str, object]) -> bool:
    return args.get("IsDaemon") is True


def format_elapsed_duration(elapsed_seconds: int) -> str:
    safe_seconds: int = max(0, int(elapsed_seconds))
    minutes: int = safe_seconds // 60
    rem_seconds: int = safe_seconds % 60
    if minutes > 0 and rem_seconds > 0:
        return f"{minutes} phút {rem_seconds} giây ({safe_seconds} giây)"
    if minutes > 0:
        return f"{minutes} phút ({safe_seconds} giây)"
    return f"{safe_seconds} giây"


def build_timeout_user_message(
    task: TrackedCommandTask,
    elapsed_seconds: int,
) -> str:
    duration_str: str = format_elapsed_duration(elapsed_seconds)
    details: list[str] = [f"`{task.command_line}`"]
    if task.tool_summary:
        details.append(f"mô tả: `{task.tool_summary}`")
    if task.task_id:
        details.append(f"TaskId: `{task.task_id}`")
    cmd_desc: str = ", ".join(details)
    return (
        f"Lệnh `run_command` ({cmd_desc}) không được chủ định cho chạy ngầm nhưng đã chạy "
        f"{duration_str} mà chưa xong. Hãy dùng `manage_task` kiểm tra tình hình task ngay lập tức: "
        "nếu việc task chạy lâu như vậy là chủ ý của bạn thì để yên cho task chạy tiếp, "
        "không thì phải có phương án xử lý phù hợp."
    )


def _extract_latest_task_id_from_transcript(transcript_path: str) -> str:
    target_file: Path | None = resolve_transcript_file(
        transcript_path, prefer_full=True
    )
    if target_file is None:
        return ""
    try:
        with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
            raw_lines: list[str] = f.readlines()
    except Exception:
        return ""

    for raw_line in reversed(raw_lines[-20:]):
        tid_match: re.Match[str] | None = TASK_ID_RE.search(raw_line)
        if tid_match is not None:
            return tid_match.group(1)
    return ""


def _command_match_needles(command_line: str) -> tuple[str, ...]:
    clean_cmd: str = command_line.strip()
    if not clean_cmd:
        return ()
    needles: list[str] = [clean_cmd]
    try:
        unquoted_full: str = " ".join(shlex.split(clean_cmd))
        if unquoted_full and unquoted_full not in needles:
            needles.append(unquoted_full)
    except ValueError:
        pass

    for raw_seg in re.split(r"&&|\|\||;|\|", clean_cmd):
        seg: str = raw_seg.strip()
        if not seg:
            continue
        try:
            tokens: list[str] = shlex.split(seg)
        except ValueError:
            tokens = seg.split()
        while tokens and "=" in tokens[0] and not tokens[0].startswith("-"):
            tokens.pop(0)
        if not tokens or tokens[0] in SHELL_BUILTINS:
            continue
        unquoted_seg: str = " ".join(tokens)
        if unquoted_seg and unquoted_seg not in needles:
            needles.append(unquoted_seg)
        if seg not in needles:
            needles.append(seg)

    return tuple(needles)


def is_command_process_alive(command_line: str) -> bool:
    needles: tuple[str, ...] = _command_match_needles(command_line)
    if not needles:
        return False
    self_pid: int = os.getpid()
    try:
        completed: subprocess.CompletedProcess[str] = subprocess.run(
            ["ps", "-eo", "pid=,stat=,args="],
            capture_output=True,
            text=True,
            timeout=2.0,
            check=False,
        )
    except Exception:
        return False
    if completed.returncode != 0:
        return False

    for raw_line in completed.stdout.splitlines():
        parts: list[str] = raw_line.strip().split(None, 2)
        if len(parts) < 3:
            continue
        pid_str, stat_str, args_str = parts
        if not pid_str.isdigit() or int(pid_str) == self_pid:
            continue
        if stat_str.upper().startswith("Z"):
            continue
        if "run_command_timeout_hook.py" in args_str:
            continue
        if any(needle in args_str for needle in needles):
            return True
    return False


def is_task_process_alive(task: TrackedCommandTask) -> bool:
    return is_command_process_alive(task.command_line)


def evaluate_pre_tool_use(
    payload: dict[str, object],
    state_dir: Path = DEFAULT_STATE_DIR,
    now_fn: Callable[[], float] = time.time,
) -> dict[str, object]:
    conv_id_obj: object = payload.get("conversationId")
    conv_id: str = conv_id_obj.strip() if isinstance(conv_id_obj, str) else ""
    if not conv_id:
        return {"decision": "allow"}

    tool_call_obj: object = payload.get("toolCall")
    if not isinstance(tool_call_obj, dict):
        return {"decision": "allow"}
    if tool_call_obj.get("name") != "run_command":
        return {"decision": "allow"}

    args_obj: object = tool_call_obj.get("args")
    args: dict[str, object] = args_obj if isinstance(args_obj, dict) else {}
    if is_background_intended(args):
        return {"decision": "allow"}

    cmd_obj: object = args.get("CommandLine")
    cmd: str = cmd_obj.strip() if isinstance(cmd_obj, str) else ""
    if not cmd:
        return {"decision": "allow"}

    summary_obj: object = args.get("toolSummary")
    tool_summary: str = summary_obj.strip() if isinstance(summary_obj, str) else ""
    step_idx: int = parse_non_negative_int(payload.get("stepIdx"), 0)
    now: float = now_fn()

    with timeout_state_lock(state_dir, conv_id):
        state: TimeoutHookState = load_timeout_state(state_dir, conv_id)
        kept_tasks: list[TrackedCommandTask] = [
            t
            for t in state.tasks
            if not (step_idx > 0 and t.step_idx == step_idx)
        ]
        kept_tasks.append(
            TrackedCommandTask(
                step_idx=step_idx,
                command_line=cmd,
                tool_summary=tool_summary,
                started_at=now,
            )
        )
        save_timeout_state(
            state_dir,
            replace(state, tasks=tuple(kept_tasks)),
        )

    return {"decision": "allow"}


def evaluate_post_tool_use(
    payload: dict[str, object],
    state_dir: Path = DEFAULT_STATE_DIR,
) -> dict[str, object]:
    conv_id_obj: object = payload.get("conversationId")
    conv_id: str = conv_id_obj.strip() if isinstance(conv_id_obj, str) else ""
    if not conv_id:
        return {}

    tool_call_obj: object = payload.get("toolCall")
    if not isinstance(tool_call_obj, dict) or tool_call_obj.get("name") != "run_command":
        return {}

    args_obj: object = tool_call_obj.get("args")
    args: dict[str, object] = args_obj if isinstance(args_obj, dict) else {}
    step_idx: int = parse_non_negative_int(payload.get("stepIdx"), 0)
    cmd_obj: object = args.get("CommandLine")
    cmd: str = cmd_obj.strip() if isinstance(cmd_obj, str) else ""

    with timeout_state_lock(state_dir, conv_id):
        state: TimeoutHookState = load_timeout_state(state_dir, conv_id)
        if not state.tasks:
            return {}

        removed: bool = False
        remaining: list[TrackedCommandTask] = []
        for task in reversed(state.tasks):
            if not removed and (
                (step_idx > 0 and task.step_idx == step_idx)
                or (step_idx == 0 and task.command_line == cmd)
                or task.command_line == cmd
            ):
                removed = True
                continue
            remaining.append(task)
        remaining.reverse()

        save_timeout_state(
            state_dir,
            replace(
                state,
                tasks=tuple(remaining),
                manage_task_authorized=(
                    state.manage_task_authorized if remaining else False
                ),
            ),
        )

    return {}


def evaluate_stop(
    payload: dict[str, object],
    state_dir: Path = DEFAULT_STATE_DIR,
    now_fn: Callable[[], float] = time.time,
    sleep_fn: Callable[[float], None] = time.sleep,
    is_alive_fn: Callable[[TrackedCommandTask], bool] = is_task_process_alive,
    poll_interval: float = DEFAULT_POLL_INTERVAL_SECONDS,
    timeout_seconds: int = TIMEOUT_SECONDS,
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
    transcript_obj: object = payload.get("transcriptPath")
    transcript_path: str = transcript_obj if isinstance(transcript_obj, str) else ""

    with timeout_state_lock(state_dir, conv_id):
        state: TimeoutHookState = load_timeout_state(state_dir, conv_id)
        if not state.tasks:
            return {"decision": "allow"}

        if term_reason in NON_CONTINUABLE_STOP_REASONS or fully_idle:
            save_timeout_state(
                state_dir,
                replace(state, tasks=(), manage_task_authorized=False),
            )
            return {"decision": "allow"}

    while True:
        with timeout_state_lock(state_dir, conv_id):
            state = load_timeout_state(state_dir, conv_id)
            if not state.tasks:
                return {"decision": "allow"}

            latest_tid: str = _extract_latest_task_id_from_transcript(transcript_path)
            alive_unnotified: list[TrackedCommandTask] = []
            now: float = now_fn()
            triggered: bool = False
            next_tasks: list[TrackedCommandTask] = []

            for task in state.tasks:
                if latest_tid and not task.task_id:
                    task = replace(task, task_id=latest_tid)
                if task.notified:
                    next_tasks.append(task)
                    continue
                elapsed: float = max(0.0, now - task.started_at)
                if task.pending_inject or elapsed >= timeout_seconds:
                    triggered = True
                    next_tasks.append(
                        replace(
                            task,
                            pending_inject=True,
                            elapsed_at_trigger=max(
                                task.elapsed_at_trigger, int(elapsed), timeout_seconds
                            ),
                        )
                    )
                elif is_alive_fn(task):
                    alive_unnotified.append(task)
                    next_tasks.append(task)

            save_timeout_state(
                state_dir,
                replace(
                    state,
                    tasks=tuple(next_tasks),
                    manage_task_authorized=state.manage_task_authorized or triggered,
                ),
            )

            if triggered:
                return {"decision": "continue"}
            if not alive_unnotified:
                return {"decision": "allow"}

            earliest_deadline: float = min(
                t.started_at + timeout_seconds for t in alive_unnotified
            )
            wait_for: float = max(
                0.01, min(poll_interval, earliest_deadline - now)
            )

        sleep_fn(wait_for)


def evaluate_post_invocation(
    payload: dict[str, object],
    state_dir: Path = DEFAULT_STATE_DIR,
    now_fn: Callable[[], float] = time.time,
    timeout_seconds: int = TIMEOUT_SECONDS,
) -> dict[str, object]:
    conv_id_obj: object = payload.get("conversationId")
    conv_id: str = conv_id_obj.strip() if isinstance(conv_id_obj, str) else ""
    if not conv_id:
        return {"injectSteps": []}

    now: float = now_fn()

    with timeout_state_lock(state_dir, conv_id):
        state: TimeoutHookState = load_timeout_state(state_dir, conv_id)
        if not state.tasks:
            return {"injectSteps": []}

        triggered: bool = False
        updated: list[TrackedCommandTask] = []
        for task in state.tasks:
            if task.notified:
                updated.append(task)
                continue
            elapsed: float = max(0.0, now - task.started_at)
            if task.pending_inject or elapsed >= timeout_seconds:
                triggered = True
                updated.append(
                    replace(
                        task,
                        pending_inject=True,
                        elapsed_at_trigger=max(
                            task.elapsed_at_trigger, int(elapsed), timeout_seconds
                        ),
                    )
                )
            else:
                updated.append(task)

        save_timeout_state(
            state_dir,
            replace(
                state,
                tasks=tuple(updated),
                manage_task_authorized=state.manage_task_authorized or triggered,
            ),
        )
        if triggered:
            return {
                "injectSteps": [],
                "terminationBehavior": "force_continue",
            }

    return {"injectSteps": []}


def evaluate_pre_invocation(
    payload: dict[str, object],
    state_dir: Path = DEFAULT_STATE_DIR,
    now_fn: Callable[[], float] = time.time,
    timeout_seconds: int = TIMEOUT_SECONDS,
) -> dict[str, object]:
    conv_id_obj: object = payload.get("conversationId")
    conv_id: str = conv_id_obj.strip() if isinstance(conv_id_obj, str) else ""
    if not conv_id:
        return {"injectSteps": []}

    transcript_obj: object = payload.get("transcriptPath")
    transcript_path: str = transcript_obj if isinstance(transcript_obj, str) else ""
    now: float = now_fn()

    with timeout_state_lock(state_dir, conv_id):
        state: TimeoutHookState = load_timeout_state(state_dir, conv_id)
        if not state.tasks:
            return {"injectSteps": []}

        latest_tid: str = _extract_latest_task_id_from_transcript(transcript_path)
        injected_messages: list[dict[str, str]] = []
        updated_tasks: list[TrackedCommandTask] = []

        for task in state.tasks:
            if latest_tid and not task.task_id:
                task = replace(task, task_id=latest_tid)
            if task.notified:
                updated_tasks.append(task)
                continue
            elapsed: float = max(0.0, now - task.started_at)
            if task.pending_inject or elapsed >= timeout_seconds:
                effective_elapsed: int = max(
                    task.elapsed_at_trigger, int(elapsed), timeout_seconds
                )
                msg: str = build_timeout_user_message(task, effective_elapsed)
                injected_messages.append({"userMessage": msg})
                updated_tasks.append(
                    replace(
                        task,
                        notified=True,
                        pending_inject=False,
                        elapsed_at_trigger=effective_elapsed,
                    )
                )
            else:
                updated_tasks.append(task)

        save_timeout_state(
            state_dir,
            replace(
                state,
                tasks=tuple(updated_tasks),
                manage_task_authorized=(
                    state.manage_task_authorized or bool(injected_messages)
                ),
            ),
        )
        return {"injectSteps": injected_messages}


def main() -> None:
    mode: str = sys.argv[1].strip().lower() if len(sys.argv) > 1 else ""
    try:
        raw_input: str = sys.stdin.read()
        payload: object = json.loads(raw_input) if raw_input.strip() else {}
    except Exception:
        if mode in ("pre_tool_use", "pre_tool", "stop"):
            print(json.dumps({"decision": "allow"}))
        elif mode in ("pre_invocation", "pre", "post_invocation"):
            print(json.dumps({"injectSteps": []}))
        else:
            print(json.dumps({}))
        return

    if not isinstance(payload, dict):
        if mode in ("pre_tool_use", "pre_tool", "stop"):
            print(json.dumps({"decision": "allow"}))
        elif mode in ("pre_invocation", "pre", "post_invocation"):
            print(json.dumps({"injectSteps": []}))
        else:
            print(json.dumps({}))
        return

    if mode in ("pre_tool_use", "pre_tool"):
        print(json.dumps(evaluate_pre_tool_use(payload)))
        return

    if mode in ("post_tool_use", "post_tool"):
        print(json.dumps(evaluate_post_tool_use(payload)))
        return

    if mode == "stop" or "terminationReason" in payload or "fullyIdle" in payload:
        print(json.dumps(evaluate_stop(payload)))
        return

    if mode == "post_invocation":
        print(json.dumps(evaluate_post_invocation(payload)))
        return

    print(json.dumps(evaluate_pre_invocation(payload)))


if __name__ == "__main__":
    main()
