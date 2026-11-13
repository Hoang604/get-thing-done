#!/usr/bin/env python3
import json
import sys

SYNC_WAIT_MS: int = 10000
DAEMON_WAIT_MS: int = 500


def evaluate_run_command_wait(tool_call: dict[str, object]) -> dict[str, object]:
    """Normalize run_command WaitMsBeforeAsync to 500 for daemons and 10000 otherwise."""
    if tool_call.get("name") != "run_command":
        return {"decision": "allow"}

    args_obj: object = tool_call.get("args")
    if not isinstance(args_obj, dict):
        return {"decision": "allow"}

    target_wait: int = (
        DAEMON_WAIT_MS if args_obj.get("IsDaemon") is True else SYNC_WAIT_MS
    )
    current_wait: object = args_obj.get("WaitMsBeforeAsync")
    if (
        isinstance(current_wait, int)
        and not isinstance(current_wait, bool)
        and current_wait == target_wait
    ):
        return {"decision": "allow"}

    return {
        "decision": "allow",
        "overwrite": {
            "WaitMsBeforeAsync": target_wait,
        },
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
