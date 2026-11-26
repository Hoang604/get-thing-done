#!/usr/bin/env python3
import json
import sys
from typing import TypeGuard

SYNC_WAIT_MS: int = 10000
DAEMON_WAIT_MS: int = 500
DEFAULT_NOTIFICATION_TIMEOUT_SECONDS: int = 60
E2E_NOTIFICATION_TIMEOUT_SECONDS: int = 600


def _is_int(value: object) -> TypeGuard[int]:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_e2e_command(command_line: object) -> bool:
    return isinstance(command_line, str) and "e2e" in command_line.lower()


def evaluate_run_command_wait(tool_call: dict[str, object]) -> dict[str, object]:
    """Normalize run_command WaitMsBeforeAsync and default NotificationTimeoutSeconds for non-daemons."""
    if tool_call.get("name") != "run_command":
        return {"decision": "allow"}

    args_obj: object = tool_call.get("args")
    if not isinstance(args_obj, dict):
        return {"decision": "allow"}

    is_daemon: bool = args_obj.get("IsDaemon") is True
    target_wait: int = DAEMON_WAIT_MS if is_daemon else SYNC_WAIT_MS
    overwrite: dict[str, int] = {}

    current_wait: object = args_obj.get("WaitMsBeforeAsync")
    if not (_is_int(current_wait) and current_wait == target_wait):
        overwrite["WaitMsBeforeAsync"] = target_wait

    if not is_daemon:
        current_timeout: object = args_obj.get("NotificationTimeoutSeconds")
        if not (_is_int(current_timeout) and current_timeout > 0):
            overwrite["NotificationTimeoutSeconds"] = (
                E2E_NOTIFICATION_TIMEOUT_SECONDS
                if _is_e2e_command(args_obj.get("CommandLine"))
                else DEFAULT_NOTIFICATION_TIMEOUT_SECONDS
            )

    if not overwrite:
        return {"decision": "allow"}

    return {
        "decision": "allow",
        "overwrite": overwrite,
    }


def main() -> None:
    try:
        raw_input: str = sys.stdin.read()
        payload: object = json.loads(raw_input) if raw_input.strip() else {}
    except Exception:
        print(json.dumps({"decision": "allow"}))
        return

    if not isinstance(payload, dict):
        print(json.dumps({"decision": "allow"}))
        return

    tool_call_obj: object = payload.get("toolCall")
    if not isinstance(tool_call_obj, dict):
        print(json.dumps({"decision": "allow"}))
        return

    result: dict[str, object] = evaluate_run_command_wait(tool_call_obj)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
