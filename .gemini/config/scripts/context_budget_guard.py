#!/usr/bin/env python3
import json
import os
import re
import sys
from pathlib import Path

SCRIPT_DIR: Path = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from compact_threshold_tracker import (
    CHARS_PER_TOKEN,
    DEFAULT_STATE_DIR,
    DEFAULT_THRESHOLDS_FILE,
    ConversationTokenState,
    ModelThresholdEntry,
    conversation_state_lock,
    measure_post_planner_transcript_tokens,
    parse_non_negative_int,
    save_conversation_state,
    sync_conversation_and_thresholds,
)

WARN_RATIO: float = 0.90
BLOCK_RATIO: float = 0.95
MAX_READ_FILE_LINES: int = 800
MAX_READ_FILE_BYTES: int = 46_080
GUARDED_COMMAND_RE: re.Pattern[str] = re.compile(r"\b(?:rg|grep|cat)\b")


def build_warning_message(current_tokens: int, threshold_tokens: int) -> str:
    pct: float = (
        (current_tokens / threshold_tokens) * 100.0 if threshold_tokens > 0 else 90.0
    )
    return (
        "<critical_instructions>\n"
        f"Context usage is at {pct:.1f}% ({current_tokens} / {threshold_tokens} tokens).\n"
        "Keep calling tools continuously in this turn until the harness triggers auto-compaction on its own—ending your turn or waiting for compaction halts execution:\n"
        "1. **When** context holds settled file edits or ledger/artifact updates not yet written to disk: state in one sentence which file you are writing now, dispatch only those write/edit tool calls in this step, and in the very next step after they return, immediately dispatch your next read/search/verification tool calls without ending your turn.\n"
        "2. **When** all settled changes are already on disk: dispatch the next tool calls for the current task step immediately in this step.\n"
        "3. **Guardrail**: Do NOT output a compaction `<summary>`, a `Read-next working set`, or a remaining-work recap in chat—the `<summary>` is generated only when the harness explicitly prompts for compaction after wiping the turn.\n"
        "</critical_instructions>"
    )


def build_subsequent_block_message(current_tokens: int, threshold_tokens: int) -> str:
    pct: float = (
        (current_tokens / threshold_tokens) * 100.0 if threshold_tokens > 0 else 95.0
    )
    return (
        f"DEFERRED FOR 1 STEP (context at {pct:.1f}%: {current_tokens}/{threshold_tokens} tokens): "
        "This read/search call is paused for this single step so you can persist in-hand work to disk first. "
        "The budget guard unlocks on the very next step—re-dispatch this call immediately after your persist tool call returns, without ending your turn."
    )


def estimate_read_file_tokens(args: dict[str, object]) -> int:
    filepath_obj: object = args.get("Path")
    if not isinstance(filepath_obj, str) or not os.path.isfile(filepath_obj):
        return 0
    try:
        with open(filepath_obj, "r", encoding="utf-8", errors="ignore") as f:
            lines: list[str] = f.readlines()
    except Exception:
        return 0

    total_lines: int = len(lines)
    if total_lines == 0:
        return 0

    start_raw: int = parse_non_negative_int(args.get("StartLine"), 1)
    start_line: int = max(1, start_raw)
    end_raw: int = parse_non_negative_int(args.get("EndLine"), total_lines)
    end_line: int = min(total_lines, max(start_line, end_raw))
    end_line = min(end_line, start_line + MAX_READ_FILE_LINES - 1)

    selected: list[str] = lines[start_line - 1 : end_line]
    raw_chars: int = sum(len(line) + 6 for line in selected)
    capped_chars: int = min(raw_chars, MAX_READ_FILE_BYTES)
    return int(capped_chars / CHARS_PER_TOKEN)


def is_guarded_run_command(args: dict[str, object]) -> bool:
    cmd_obj: object = args.get("CommandLine")
    if not isinstance(cmd_obj, str) or not cmd_obj.strip():
        return False
    return bool(GUARDED_COMMAND_RE.search(cmd_obj))


def estimate_cat_command_tokens(args: dict[str, object]) -> int:
    cmd_obj: object = args.get("CommandLine")
    if not isinstance(cmd_obj, str) or not re.search(r"\bcat\b", cmd_obj):
        return 0
    cwd_obj: object = args.get("Cwd")
    base_dir: Path = (
        Path(cwd_obj) if isinstance(cwd_obj, str) and cwd_obj.strip() else Path.cwd()
    )
    total_chars: int = 0
    for token in re.findall(r"[^\s|;&><\"']+", cmd_obj):
        if token in ("cat", "-") or token.startswith("-"):
            continue
        candidate: Path = Path(token) if os.path.isabs(token) else base_dir / token
        if candidate.is_file():
            try:
                total_chars += min(candidate.stat().st_size, MAX_READ_FILE_BYTES)
            except Exception:
                pass
    return int(total_chars / CHARS_PER_TOKEN)


def evaluate_tool_budget_guard(
    conv_id: str,
    fallback_model_name: str,
    transcript_path: str,
    tool_call: dict[str, object],
    state_dir: Path = DEFAULT_STATE_DIR,
    thresholds_file: Path = DEFAULT_THRESHOLDS_FILE,
) -> dict[str, object]:
    if not conv_id.strip():
        return {"decision": "allow"}

    tool_name_obj: object = tool_call.get("name")
    tool_name: str = tool_name_obj if isinstance(tool_name_obj, str) else ""
    args_obj: object = tool_call.get("args")
    args: dict[str, object] = args_obj if isinstance(args_obj, dict) else {}

    if tool_name == "read_file":
        incoming_tokens: int = estimate_read_file_tokens(args)
    elif tool_name == "run_command" and is_guarded_run_command(args):
        incoming_tokens = estimate_cat_command_tokens(args)
    else:
        return {"decision": "allow"}

    with conversation_state_lock(state_dir, conv_id):
        state, entry = sync_conversation_and_thresholds(
            conv_id=conv_id,
            fallback_model_name=fallback_model_name,
            transcript_path=transcript_path,
            state_dir=state_dir,
            thresholds_file=thresholds_file,
        )

        planner_line, post_planner_tokens = measure_post_planner_transcript_tokens(
            transcript_path
        )
        current_planner_turn: int = max(state.last_turn, planner_line, 1)
        accumulated_turn_tokens: int = max(
            state.pending_turn_tokens, post_planner_tokens
        )
        projected_tokens: int = (
            state.last_tokens + accumulated_turn_tokens + incoming_tokens
        )
        block_threshold: int = int(entry.compact_threshold * BLOCK_RATIO)
        already_blocked_in_turn: bool = (
            state.blocked_at_planner_turn == current_planner_turn
        )
        already_reminded_in_cycle: bool = state.warned_in_cycle or (
            0 < state.blocked_at_planner_turn < current_planner_turn
        )

        if not already_blocked_in_turn and (
            already_reminded_in_cycle or projected_tokens < block_threshold
        ):
            if accumulated_turn_tokens + incoming_tokens != state.pending_turn_tokens:
                save_conversation_state(
                    state_dir,
                    ConversationTokenState(
                        conversation_id=state.conversation_id,
                        model_id=state.model_id,
                        last_turn=state.last_turn,
                        last_tokens=state.last_tokens,
                        warned_in_cycle=state.warned_in_cycle,
                        warned_at_tokens=state.warned_at_tokens,
                        blocked_at_planner_turn=state.blocked_at_planner_turn,
                        pending_turn_tokens=accumulated_turn_tokens + incoming_tokens,
                        blocked_in_last_turn=state.blocked_in_last_turn,
                    ),
                )
            return {"decision": "allow"}

        is_first_block_in_turn: bool = not already_blocked_in_turn
        display_tokens: int = max(projected_tokens, block_threshold)
        save_conversation_state(
            state_dir,
            ConversationTokenState(
                conversation_id=state.conversation_id,
                model_id=state.model_id,
                last_turn=state.last_turn,
                last_tokens=state.last_tokens,
                warned_in_cycle=state.warned_in_cycle,
                warned_at_tokens=state.warned_at_tokens,
                blocked_at_planner_turn=current_planner_turn,
                pending_turn_tokens=accumulated_turn_tokens,
                blocked_in_last_turn=True,
            ),
        )

        if is_first_block_in_turn:
            reason_msg: str = build_warning_message(
                display_tokens, entry.compact_threshold
            )
        else:
            reason_msg = build_subsequent_block_message(
                display_tokens, entry.compact_threshold
            )

        return {
            "decision": "deny",
            "reason": reason_msg,
        }


def evaluate_budget_guard(
    conv_id: str,
    fallback_model_name: str,
    transcript_path: str,
    state_dir: Path = DEFAULT_STATE_DIR,
    thresholds_file: Path = DEFAULT_THRESHOLDS_FILE,
) -> dict[str, object]:
    if not conv_id.strip():
        return {"injectSteps": []}

    with conversation_state_lock(state_dir, conv_id):
        state, entry = sync_conversation_and_thresholds(
            conv_id=conv_id,
            fallback_model_name=fallback_model_name,
            transcript_path=transcript_path,
            state_dir=state_dir,
            thresholds_file=thresholds_file,
        )

        _, post_planner_tokens = measure_post_planner_transcript_tokens(transcript_path)
        effective_tokens: int = state.last_tokens + max(
            state.pending_turn_tokens, post_planner_tokens
        )
        warn_threshold: int = int(entry.compact_threshold * WARN_RATIO)

        if effective_tokens < warn_threshold and not state.blocked_in_last_turn:
            if state.warned_in_cycle:
                save_conversation_state(
                    state_dir,
                    ConversationTokenState(
                        conversation_id=state.conversation_id,
                        model_id=state.model_id,
                        last_turn=state.last_turn,
                        last_tokens=state.last_tokens,
                        warned_in_cycle=False,
                        warned_at_tokens=0,
                        blocked_at_planner_turn=state.blocked_at_planner_turn,
                        pending_turn_tokens=state.pending_turn_tokens,
                        blocked_in_last_turn=False,
                    ),
                )
            return {"injectSteps": []}

        if state.blocked_in_last_turn or not state.warned_in_cycle:
            updated_state: ConversationTokenState = ConversationTokenState(
                conversation_id=state.conversation_id,
                model_id=state.model_id,
                last_turn=state.last_turn,
                last_tokens=state.last_tokens,
                warned_in_cycle=True,
                warned_at_tokens=effective_tokens,
                blocked_at_planner_turn=state.blocked_at_planner_turn,
                pending_turn_tokens=state.pending_turn_tokens,
                blocked_in_last_turn=False,
            )
            save_conversation_state(state_dir, updated_state)
            msg: str = build_warning_message(effective_tokens, entry.compact_threshold)
            return {"injectSteps": [{"ephemeralMessage": msg}]}

        return {"injectSteps": []}


def main() -> None:
    try:
        raw_input: str = sys.stdin.read()
        payload: object = json.loads(raw_input) if raw_input.strip() else {}
    except Exception:
        print(json.dumps({"injectSteps": []}))
        return

    if not isinstance(payload, dict):
        print(json.dumps({"injectSteps": []}))
        return

    conv_id_obj: object = payload.get("conversationId")
    conv_id: str = conv_id_obj if isinstance(conv_id_obj, str) else ""

    model_obj: object = payload.get("modelName")
    model_name: str = model_obj if isinstance(model_obj, str) else ""

    transcript_obj: object = payload.get("transcriptPath")
    transcript_path: str = transcript_obj if isinstance(transcript_obj, str) else ""

    tool_call_obj: object = payload.get("toolCall")
    if isinstance(tool_call_obj, dict):
        tool_result: dict[str, object] = evaluate_tool_budget_guard(
            conv_id=conv_id,
            fallback_model_name=model_name,
            transcript_path=transcript_path,
            tool_call=tool_call_obj,
        )
        print(json.dumps(tool_result))
        return

    result: dict[str, object] = evaluate_budget_guard(
        conv_id=conv_id,
        fallback_model_name=model_name,
        transcript_path=transcript_path,
    )
    print(json.dumps(result))


if __name__ == "__main__":
    main()
