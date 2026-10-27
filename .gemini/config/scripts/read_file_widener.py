#!/usr/bin/env python3
import json
import sys

PAD_BEFORE: int = 10
PAD_AFTER: int = 10
MAX_READ_FILE_LINES: int = 800


def parse_positive_int(val: object) -> int | None:
    if isinstance(val, int) and not isinstance(val, bool) and val >= 1:
        return val
    if isinstance(val, float) and val >= 1:
        return int(val)
    return None


def evaluate_read_file_widener(tool_call: dict[str, object]) -> dict[str, object]:
    tool_name_obj: object = tool_call.get("name")
    if tool_name_obj != "read_file":
        return {"decision": "allow"}

    args_obj: object = tool_call.get("args")
    if not isinstance(args_obj, dict):
        return {"decision": "allow"}

    start_line: int | None = parse_positive_int(args_obj.get("StartLine"))
    end_line: int | None = parse_positive_int(args_obj.get("EndLine"))

    if start_line is None and end_line is None:
        return {"decision": "allow"}

    overwrite: dict[str, int] = {}
    effective_start: int = 1

    if start_line is not None:
        new_start: int = max(1, start_line - PAD_BEFORE)
        effective_start = new_start
        if new_start != start_line:
            overwrite["StartLine"] = new_start

    if end_line is not None:
        base_end: int = max(effective_start, end_line)
        max_allowed_end: int = max(
            base_end, effective_start + MAX_READ_FILE_LINES - 1
        )
        new_end: int = min(base_end + PAD_AFTER, max_allowed_end)
        if new_end != end_line:
            overwrite["EndLine"] = new_end

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

    result: dict[str, object] = evaluate_read_file_widener(tool_call_obj)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
