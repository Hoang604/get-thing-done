#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

LOG_FILE = "/tmp/agy_verify_hooks.log"


def log_line(status: str, command: str, detail: str = "") -> None:
    try:
        ts = datetime.now().strftime("%H:%M:%S")
        cmd_clean = command.strip().replace("\n", " ")
        cmd_short = (cmd_clean[:65] + "...") if len(cmd_clean) > 65 else cmd_clean
        line = f"[{ts}] [{status:<5}] {cmd_short} {detail}".rstrip() + "\n"
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass


class VerifyInjector:
    """Inspects pending incidents for the conversation and generates ephemeral instructions."""

    def __init__(self, cache_dir: str = "/tmp") -> None:
        self.cache_dir = cache_dir

    def generate_instruction(self, conversation_id: str) -> List[Dict[str, Any]]:
        if not conversation_id:
            return []

        incident_path = os.path.join(self.cache_dir, f"agy_incident_{conversation_id}.json")
        if not os.path.exists(incident_path):
            return []

        try:
            with open(incident_path, "r", encoding="utf-8") as f:
                incident = json.load(f)
        except Exception:
            return []

        if incident.get("acknowledged", False):
            try:
                os.remove(incident_path)
            except Exception:
                pass
            return []

        # Mark as acknowledged and delete to consume incident
        incident["acknowledged"] = True
        try:
            os.remove(incident_path)
        except Exception:
            try:
                with open(incident_path, "w", encoding="utf-8") as f:
                    json.dump(incident, f, indent=2)
            except Exception:
                pass

        command = incident.get("command", "verification command")
        error = incident.get("error", "failed")

        message = (
            "<critical_instructions>\n"
            f"Command `{command}` failed ({error}).\n\n"
            "In your visible response before mutating code, report:\n"
            "1. What failed (test name, assertion, or error output).\n"
            "2. Root cause or Hypothesis (Confidence: High/Low):\n"
            "   - If straightforward (e.g. syntax, typo, missing import): state exact root cause directly (Confidence: High).\n"
            "   - If complex or non-obvious: state hypothesis with confidence level (High/Low) and explore before applying fixes.\n"
            "3. Proposed fix / next action.\n\n"
            "Then proceed with the fix or exploration.\n"
            "</critical_instructions>"
        )

        log_line("GUARD", command, "-> Đã tiêm chỉ thị yêu cầu Agent giải trình lỗi")
        return [{"ephemeralMessage": message}]


def main() -> None:
    inject_steps: List[Dict[str, Any]] = []
    try:
        raw_input = sys.stdin.read()
        if raw_input.strip():
            payload = json.loads(raw_input)
            conv_id = payload.get("conversationId", "")
            injector = VerifyInjector()
            inject_steps = injector.generate_instruction(conv_id)
    except Exception:
        inject_steps = []

    print(json.dumps({"injectSteps": inject_steps}))


if __name__ == "__main__":
    main()
