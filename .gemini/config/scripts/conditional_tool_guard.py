#!/usr/bin/env python3
import json
import re
import sys

def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        print(json.dumps({"decision": "deny", "reason": "Failed to parse hook payload."}))
        return

    tool_name = payload.get("toolCall", {}).get("name", "")
    transcript_path = payload.get("transcriptPath", "")

    latest_user_text = ""
    if transcript_path:
        try:
            with open(transcript_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    step = json.loads(line)
                    if step.get("type") == "USER_INPUT":
                        latest_user_text = step.get("content", "")
        except Exception:
            pass

    # Check word boundary matching per tool
    is_allowed = False
    if tool_name == "manage_task" and re.search(r"\bmanage_task\b", latest_user_text):
        is_allowed = True
    elif tool_name == "schedule" and re.search(r"\bschedule\b", latest_user_text):
        is_allowed = True

    if is_allowed:
        print(json.dumps({"decision": "allow"}))
    else:
        print(json.dumps({
            "decision": "deny",
            "reason": (
                f"BLOCKED: Tool '{tool_name}' execution is prohibited because "
                "asynchronous tasks are automatically handled via reactive wakeup upon completion. "
                "Do NOT poll, manage tasks, or schedule timers. Stop calling tools to allow background "
                "tasks to finish. (This tool is only permitted when explicitly requested by the user "
                f"via '\\b{tool_name}\\b')."
            )
        }))

if __name__ == "__main__":
    main()
