#!/usr/bin/env python3
"""Track per-session Codex token usage and checkpoint injection intervals."""

import fcntl
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

GROWTH_INTERVAL = 40_000


def read_event():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("hook input must be valid JSON") from exc
    if not isinstance(event, dict):
        raise ValueError("hook input must be a JSON object")
    session_id = event.get("session_id")
    if not isinstance(session_id, str) or not session_id.strip():
        raise ValueError("hook input must include a non-empty session_id")
    return event, session_id


def token_count(event):
    usage = event.get("token_usage")
    if usage is None:
        return None
    if not isinstance(usage, dict):
        raise ValueError("token_usage must be an object or null")
    total = usage.get("total_tokens")
    if not isinstance(total, int) or isinstance(total, bool) or total < 0:
        raise ValueError("token_usage.total_tokens must be a non-negative integer")
    return total


def state_paths(session_id):
    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()
    state_dir = codex_home / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    name = hashlib.sha256(session_id.encode("utf-8")).hexdigest()
    return state_dir / f"critical_instructions_{name}.json", state_dir / f"critical_instructions_{name}.lock"


def load_state(path):
    try:
        with path.open(encoding="utf-8") as stream:
            state = json.load(stream)
    except FileNotFoundError:
        return {"tool_count": 0, "current_tokens": None, "last_injected_tokens": None,
                "last_warning_turn": None, "last_denied_turn": None, "warned_in_cycle": False}
    if not isinstance(state, dict):
        raise ValueError(f"tracker state is not a JSON object: {path}")
    return state


def save_state(path, state):
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(state, stream, separators=(",", ":"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def configured_limit():
    raw = os.environ.get("CODEX_AUTO_COMPACT_TOKEN_LIMIT")
    if raw is not None:
        try:
            value = int(raw)
        except ValueError as exc:
            raise ValueError("CODEX_AUTO_COMPACT_TOKEN_LIMIT must be a positive integer") from exc
        if value <= 0:
            raise ValueError("CODEX_AUTO_COMPACT_TOKEN_LIMIT must be a positive integer")
        return value

    config_path = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser() / "config.toml"
    try:
        import tomllib
    except ImportError:
        return None
    try:
        with config_path.open("rb") as stream:
            config = tomllib.load(stream)
    except FileNotFoundError:
        return None
    value = config.get("model_auto_compact_token_limit")
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"model_auto_compact_token_limit in {config_path} must be a positive integer")
    scope = config.get("model_auto_compact_token_limit_scope", "total")
    if scope not in ("total", "body_after_prefix"):
        raise ValueError(f"model_auto_compact_token_limit_scope in {config_path} is invalid")
    if scope == "body_after_prefix":
        return None
    return value


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in {"record", "before-tool", "after-tool", "prompt", "compact"}:
        raise ValueError("usage: critical_instructions_tracker.py {record|before-tool|after-tool|prompt|compact}")
    operation = sys.argv[1]
    event, session_id = read_event()
    state_path, lock_path = state_paths(session_id)
    with lock_path.open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        state = load_state(state_path)
        result = ""

        if operation == "record":
            status = event.get("status")
            if status not in ("completed", "failed", "cancelled"):
                raise ValueError("PostModelRequest input must include a valid status")
            usage_tokens = token_count(event)
            if usage_tokens is not None and status == "completed":
                previous = state.get("current_tokens")
                if isinstance(previous, int) and usage_tokens < previous:
                    state["last_injected_tokens"] = None
                    state["last_warning_turn"] = None
                    state["last_denied_turn"] = None
                    state["warned_in_cycle"] = False
                state["current_tokens"] = usage_tokens

        elif operation == "prompt":
            current = state.get("current_tokens")
            if isinstance(current, int) and not isinstance(current, bool):
                state["last_injected_tokens"] = current
            state["last_warning_turn"] = None
            state["last_denied_turn"] = None

        elif operation == "before-tool":
            result = {"action": "none"}
            turn_id = event.get("turn_id")
            if not isinstance(turn_id, str) or not turn_id:
                raise ValueError("PreToolUse input must include a non-empty turn_id")
            current = state.get("current_tokens")
            last_injected = state.get("last_injected_tokens")
            growth_due = isinstance(current, int) and (
                not isinstance(last_injected, int) or current - last_injected >= GROWTH_INTERVAL
            )
            limit = configured_limit()
            ratio = current / limit if limit and isinstance(current, int) else 0
            if isinstance(current, int) and ratio >= 0.95 and state.get("last_denied_turn") != turn_id:
                state["last_denied_turn"] = turn_id
                state["last_warning_turn"] = turn_id
                state["warned_in_cycle"] = True
                state["last_injected_tokens"] = current
                result = {"action": "deny", "current_tokens": current, "limit": limit,
                          "percentage": f"{ratio * 100:.1f}"}
            elif (isinstance(current, int) and ratio >= 0.90
                  and not state.get("warned_in_cycle", False)):
                state["last_warning_turn"] = turn_id
                state["warned_in_cycle"] = True
                state["last_injected_tokens"] = current
                result = {"action": "warn", "current_tokens": current, "limit": limit,
                          "percentage": f"{ratio * 100:.1f}"}
            elif growth_due:
                state["last_injected_tokens"] = current
                result = {"action": "growth"}

        elif operation == "after-tool":
            count = state.get("tool_count", 0)
            if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                raise ValueError("tracker tool_count state must be a non-negative integer")
            count += 1
            state["tool_count"] = count % 10
            if count % 10 == 0:
                current = state.get("current_tokens")
                if isinstance(current, int):
                    state["last_injected_tokens"] = current
                result = "inject"

        elif operation == "compact":
            state.update({"tool_count": 0, "current_tokens": None, "last_injected_tokens": None,
                          "last_warning_turn": None, "last_denied_turn": None,
                          "warned_in_cycle": False})

        save_state(state_path, state)
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
    if operation == "before-tool":
        print(json.dumps(result))
    else:
        print(result)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        print(f"critical instructions tracker: {exc}", file=sys.stderr)
        sys.exit(2)
