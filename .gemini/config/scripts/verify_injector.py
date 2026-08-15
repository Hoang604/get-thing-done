#!/usr/bin/env python3
import json
import os
import re
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

LOG_FILE = "/tmp/agy_verify_hooks.log"

try:
    from verify_recorder import VerifyMatcher, log_line
except ImportError:
    from .verify_recorder import VerifyMatcher, log_line


class VerifyInjector:
    """
    Inspects pending sync incidents and completed async background tasks in PreInvocation.
    Emits ephemeral instructions with hypothesis and confidence level criteria across all failure types.
    """

    def __init__(self, cache_dir: str = "/tmp", patterns_file_path: Optional[str] = None) -> None:
        self.cache_dir = cache_dir
        self.matcher = VerifyMatcher(patterns_file_path)

    def _get_processed_tasks(self, conversation_id: str) -> Set[str]:
        tasks_file = os.path.join(self.cache_dir, f"agy_processed_tasks_{conversation_id}.json")
        if os.path.exists(tasks_file):
            try:
                with open(tasks_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return set(data)
            except Exception:
                pass
        return set()

    def _save_processed_tasks(self, conversation_id: str, tasks: Set[str]) -> None:
        tasks_file = os.path.join(self.cache_dir, f"agy_processed_tasks_{conversation_id}.json")
        try:
            with open(tasks_file, "w", encoding="utf-8") as f:
                json.dump(list(tasks), f)
        except Exception:
            pass

    def _build_instruction_message(self, command: str, error: str) -> str:
        return (
            "<critical_instructions>\n"
            f"VERIFICATION FAILURE: Command `{command}` failed ({error}).\n\n"
            "MANDATORY REPORTING PROTOCOL:\n"
            "Regardless of whether this is a TEST, TYPE-CHECK, BUILD, LINT, or CODEGEN failure, "
            "you MUST output a report in your VISIBLE RESPONSE before making any file changes:\n\n"
            "1. **Failure Scope**:\n"
            "   - For Type/Lint/Build: Exact file, line number, and compiler error message (e.g. TS error, ESLint rule, build error).\n"
            "   - For Test: Failing test case, assertion, or runtime exception.\n"
            "2. **Root Cause or Hypothesis** (Confidence: High/Low):\n"
            "   - Obvious errors (type mismatch, missing import, syntax, typo): State exact root cause directly (Confidence: High).\n"
            "   - Non-obvious/complex errors: State hypothesis with confidence level (High/Low) and plan to explore.\n"
            "3. **Proposed Fix / Next Action**.\n\n"
            "After outputting this breakdown, proceed with the fix or exploration.\n"
            "</critical_instructions>"
        )

    def _check_async_task_completions(self, payload: Dict[str, Any]) -> Optional[Tuple[str, str, int]]:
        """
        Inspects transcript for recently completed background tasks.
        Returns (command, runner_name, exit_code) if a failed verification task completed.
        """
        transcript_path = payload.get("transcriptPath")
        conv_id = payload.get("conversationId", "")
        if not transcript_path or not os.path.exists(transcript_path) or not conv_id:
            return None

        processed_tasks = self._get_processed_tasks(conv_id)
        task_descriptions: Dict[str, str] = {}
        completed_tasks: List[Tuple[str, int]] = []

        try:
            with open(transcript_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines[-30:]:
                    try:
                        entry = json.loads(line)
                        content = str(entry.get("content") or "")

                        task_launch = re.search(r"Task id:\s*([^\s\n]+)", content, re.IGNORECASE)
                        task_desc = re.search(r"Task Description:\s*([^\n]+)", content, re.IGNORECASE)
                        if task_launch and task_desc:
                            t_id = task_launch.group(1).strip()
                            task_descriptions[t_id] = task_desc.group(1).strip()

                        task_finish = re.search(r'Task id "([^"]+)" finished with result:', content)
                        if task_finish:
                            finished_id = task_finish.group(1).strip()
                            if finished_id not in processed_tasks:
                                match_code = re.search(r"The command exited with code ([0-9]+)", content)
                                if match_code:
                                    code = int(match_code.group(1))
                                    completed_tasks.append((finished_id, code))
                    except Exception:
                        continue
        except Exception:
            return None

        for t_id, exit_code in completed_tasks:
            processed_tasks.add(t_id)
            self._save_processed_tasks(conv_id, processed_tasks)

            cmd = task_descriptions.get(t_id, "")
            if not cmd:
                cmd_match = re.search(r"task-.*", t_id)
                cmd = cmd_match.group(0) if cmd_match else t_id

            matched = self.matcher.match_command(cmd)
            if not matched:
                continue

            ecosystem, runner_desc = matched
            if exit_code == 0:
                log_line("PASS", cmd, "(exit: 0) -> Thành công, không chặn")
            else:
                log_line("FAIL", cmd, f"(exit: {exit_code}) -> Đã bắt lỗi async & kích hoạt hook")
                return (cmd, runner_desc, exit_code)

        return None

    def generate_instruction(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        conv_id = payload.get("conversationId", "")
        if not conv_id:
            return []

        # 1. Check sync incident file
        incident_path = os.path.join(self.cache_dir, f"agy_incident_{conv_id}.json")
        if os.path.exists(incident_path):
            try:
                with open(incident_path, "r", encoding="utf-8") as f:
                    incident = json.load(f)
                try:
                    os.remove(incident_path)
                except Exception:
                    pass

                if not incident.get("acknowledged", False):
                    command = incident.get("command", "verification command")
                    error = incident.get("error", "failed")
                    message = self._build_instruction_message(command, error)
                    log_line("GUARD", command, "-> Đã tiêm chỉ thị yêu cầu Agent giải trình lỗi")
                    return [{"ephemeralMessage": message}]
            except Exception:
                pass

        # 2. Check async background task completions from transcript
        async_result = self._check_async_task_completions(payload)
        if async_result:
            cmd, runner_desc, exit_code = async_result
            error_str = f"exit status {exit_code}"
            message = self._build_instruction_message(cmd, error_str)
            log_line("GUARD", cmd, "-> Đã tiêm chỉ thị yêu cầu Agent giải trình lỗi (Async Task)")
            return [{"ephemeralMessage": message}]

        return []


def main() -> None:
    inject_steps: List[Dict[str, Any]] = []
    try:
        raw_input = sys.stdin.read()
        if raw_input.strip():
            payload = json.loads(raw_input)
            injector = VerifyInjector()
            inject_steps = injector.generate_instruction(payload)
    except Exception:
        inject_steps = []

    print(json.dumps({"injectSteps": inject_steps}))


if __name__ == "__main__":
    main()
