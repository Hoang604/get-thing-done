#!/usr/bin/env python3
import json
import os
import sys
from typing import Dict, List, Optional

CACHE_DIR = "/tmp"


def _get_state_path(conversation_id: str) -> str:
    safe_id = conversation_id.replace("/", "_") if conversation_id else "default"
    return os.path.join(CACHE_DIR, f"agy_mutation_history_{safe_id}.json")


def _read_state(state_path: str) -> Dict[str, object]:
    if os.path.exists(state_path):
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
    return {"history": [], "warn": None}


def _write_state(state_path: str, state: Dict[str, object]) -> None:
    try:
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f)
    except Exception:
        pass


def handle_post_tool(payload: Dict[str, object]) -> None:
    conv_id = str(payload.get("conversationId") or "default")
    tool_call = payload.get("toolCall")
    if not isinstance(tool_call, dict):
        print(json.dumps({}))
        return

    tool_name = str(tool_call.get("name") or "")
    args = tool_call.get("args")
    if not isinstance(args, dict):
        print(json.dumps({}))
        return

    target_file = str(args.get("TargetFile") or "")
    if not target_file:
        print(json.dumps({}))
        return

    state_path = _get_state_path(conv_id)
    state = _read_state(state_path)

    raw_history = state.get("history")
    history: List[Dict[str, str]] = []
    if isinstance(raw_history, list):
        for item in raw_history:
            if isinstance(item, dict):
                history.append({
                    "target": str(item.get("target") or ""),
                    "tool": str(item.get("tool") or "")
                })

    history.append({
        "target": target_file,
        "tool": tool_name
    })

    # Keep window of recent mutation events
    history = history[-6:]
    state["history"] = history

    # Evaluate streak heuristics
    warn: Optional[Dict[str, str]] = None

    # Heuristic 1: Intra-file micro-edits (same file modified in 2+ consecutive single-hunk turns)
    if len(history) >= 2 and history[-1]["target"] == history[-2]["target"] and history[-1]["tool"] == "replace_file_content":
        warn = {
            "type": "INTRA_FILE",
            "file": target_file
        }
    # Heuristic 2: Inter-file sequential drift (2+ consecutive single-file mutations across separate turns)
    elif len(history) >= 2 and all(item["tool"] in ("replace_file_content", "write_to_file") for item in history[-2:]):
        warn = {
            "type": "SEQUENTIAL_DRIFT",
            "file": target_file
        }

    if warn:
        state["warn"] = warn

    _write_state(state_path, state)
    print(json.dumps({}))


def handle_pre_invocation(payload: Dict[str, object]) -> None:
    conv_id = str(payload.get("conversationId") or "default")
    state_path = _get_state_path(conv_id)
    state = _read_state(state_path)

    raw_warn = state.get("warn")
    if not isinstance(raw_warn, dict):
        print(json.dumps({"injectSteps": []}))
        return

    warn_type = str(raw_warn.get("type") or "")
    warn_file = str(raw_warn.get("file") or "")
    base_name = os.path.basename(warn_file) if warn_file else "target file"

    # Consume warning flag so it triggers strictly once per streak
    state["warn"] = None
    _write_state(state_path, state)

    if warn_type == "INTRA_FILE":
        message = (
            "<critical_instructions>\n"
            f"ANTI-PATTERN DETECTED: Consecutive single-hunk edits on `{base_name}` across separate turns.\n"
            "Synthesize all remaining modifications for this file in working memory and apply them atomically in a single turn using `multi_replace_file_content`.\n"
            "</critical_instructions>"
        )
    elif warn_type == "SEQUENTIAL_DRIFT":
        message = (
            "<critical_instructions>\n"
            "ANTI-PATTERN DETECTED: Un-batched sequential single-file mutations across separate turns.\n"
            "Synthesize the full frontier of affected files in working memory and dispatch all independent file mutations concurrently in a single turn.\n"
            "</critical_instructions>"
        )
    else:
        print(json.dumps({"injectSteps": []}))
        return

    print(json.dumps({"injectSteps": [{"ephemeralMessage": message}]}))


def main() -> None:
    try:
        raw_input = sys.stdin.read()
        payload: Dict[str, object] = json.loads(raw_input) if raw_input.strip() else {}
    except Exception:
        payload = {}

    event = ""
    for idx, arg in enumerate(sys.argv):
        if arg == "--event" and idx + 1 < len(sys.argv):
            event = sys.argv[idx + 1]

    if event == "post_tool":
        handle_post_tool(payload)
    elif event == "pre_invocation":
        handle_pre_invocation(payload)
    else:
        print(json.dumps({}))


if __name__ == "__main__":
    main()
