#!/usr/bin/env python3
import json
import os
import sys
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional

LOG_FILE = "/tmp/agy_verify_hooks.log"


def log_event(tag: str, msg: str, data: Any = None) -> None:
    try:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] [verify_injector:{os.getpid()}] [{tag}] {msg}\n")
            if data is not None:
                if isinstance(data, (dict, list)):
                    f.write(f"  DATA: {json.dumps(data, ensure_ascii=False)}\n")
                else:
                    f.write(f"  DATA: {str(data)}\n")
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
            # Clean up acknowledged incident file to prevent redundant reads
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
        runner_name = incident.get("runnerName", "test runner")
        error = incident.get("error", "")

        message = (
            "<critical_instructions>\n"
            f"CRITICAL VERIFICATION FAILURE DETECTED (Runner: {runner_name})\n"
            f"Failed Command: `{command}`\n"
            f"Error Status: {error}\n\n"
            "MANDATORY PROTOCOL BEFORE MUTATING CODE:\n"
            "1. You MUST explicitly state what failed (failing tests, assertions, or syntax/type errors).\n"
            "2. You MUST provide the causal root-cause analysis explaining WHY it failed before applying fixes.\n"
            "3. Do NOT execute speculative code modifications without presenting this breakdown.\n"
            "</critical_instructions>"
        )

        log_event("INSTRUCTION_INJECTED", f"Injected guardrail for conv '{conversation_id}' (Command: '{command}')")
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
    except Exception as e:
        log_event("FATAL_ERR", f"Unhandled error: {e}\n{traceback.format_exc()}")
        inject_steps = []

    print(json.dumps({"injectSteps": inject_steps}))


if __name__ == "__main__":
    main()
