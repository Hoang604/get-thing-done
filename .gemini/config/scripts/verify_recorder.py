#!/usr/bin/env python3
import json
import os
import re
import sys
import time
from typing import Any, Dict, List, Optional


class VerifyRecorder:
    """Evaluates executed tool output from PostToolUse and persists incident state."""

    def __init__(self, patterns_file_path: Optional[str] = None, cache_dir: str = "/tmp") -> None:
        if patterns_file_path is None:
            patterns_file_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "verify_patterns.json"
            )
        self.patterns_file_path = patterns_file_path
        self.cache_dir = cache_dir
        self.runners = self._load_runners()

    def _load_runners(self) -> List[Dict[str, Any]]:
        try:
            if os.path.exists(self.patterns_file_path):
                with open(self.patterns_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("runners", [])
        except Exception:
            pass
        return []

    def match_runner(self, command: str) -> Optional[Dict[str, Any]]:
        """Matches a command string against configured runners regex."""
        if not command:
            return None
        trimmed_cmd = command.strip()
        for runner in self.runners:
            pattern = runner.get("command_regex", "")
            if pattern and re.search(pattern, trimmed_cmd, re.IGNORECASE):
                return runner
        return None

    def _extract_command(self, payload: Dict[str, Any]) -> str:
        tool_call = payload.get("toolCall")
        if isinstance(tool_call, dict):
            args = tool_call.get("args", {})
            if isinstance(args, dict):
                cmd = args.get("CommandLine") or args.get("command") or ""
                if cmd:
                    return str(cmd)

        # Fallback: check transcript if toolCall is omitted from PostToolUse payload
        transcript_path = payload.get("transcriptPath")
        if transcript_path and os.path.exists(transcript_path):
            try:
                # Read last few lines to find the run_command step
                with open(transcript_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    for line in reversed(lines[-10:]):
                        try:
                            entry = json.loads(line)
                            tool_calls = entry.get("tool_calls", [])
                            for tc in tool_calls:
                                if tc.get("name") == "run_command":
                                    cmd = tc.get("args", {}).get("CommandLine", "")
                                    if cmd:
                                        return str(cmd)
                        except Exception:
                            continue
            except Exception:
                pass
        return ""

    def _is_failed(self, payload: Dict[str, Any], runner: Dict[str, Any]) -> bool:
        # Check explicit error field
        error_msg = str(payload.get("error") or "")
        if error_msg:
            return True

        # Check step status / exit code from transcript if available
        transcript_path = payload.get("transcriptPath")
        if transcript_path and os.path.exists(transcript_path):
            try:
                with open(transcript_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    for line in reversed(lines[-10:]):
                        try:
                            entry = json.loads(line)
                            if entry.get("status") == "ERROR":
                                return True
                            content = str(entry.get("content") or "")
                            for sig in runner.get("failure_signatures", []):
                                if sig in content:
                                    return True
                        except Exception:
                            continue
            except Exception:
                pass

        return False

    def record_if_failed(self, payload: Dict[str, Any]) -> Optional[str]:
        conv_id = payload.get("conversationId")
        if not conv_id:
            return None

        command = self._extract_command(payload)
        if not command:
            return None

        runner = self.match_runner(command)
        if not runner:
            return None

        if not self._is_failed(payload, runner):
            return None

        incident = {
            "conversationId": conv_id,
            "stepIdx": payload.get("stepIdx", 0),
            "command": command,
            "runnerName": runner.get("name", "unknown"),
            "error": str(payload.get("error") or "Verification command failed"),
            "acknowledged": False,
            "timestamp": time.time(),
        }

        incident_path = os.path.join(self.cache_dir, f"agy_incident_{conv_id}.json")
        try:
            with open(incident_path, "w", encoding="utf-8") as f:
                json.dump(incident, f, indent=2)
            return incident_path
        except Exception:
            return None


def main() -> None:
    try:
        raw_input = sys.stdin.read()
        if raw_input.strip():
            payload = json.loads(raw_input)
            recorder = VerifyRecorder()
            recorder.record_if_failed(payload)
    except Exception:
        pass
    # PostToolUse expects empty JSON
    print("{}")


if __name__ == "__main__":
    main()
