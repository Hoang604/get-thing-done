#!/usr/bin/env python3
import json
import sys
from dataclasses import replace
from pathlib import Path

SCRIPT_DIR: Path = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from compact_threshold_tracker import (
    DEFAULT_STATE_DIR,
    DEFAULT_THRESHOLDS_FILE,
    ConversationTokenState,
    apply_incoming_tool_tokens,
    compute_usage_percentage,
    conversation_state_lock,
    estimate_tool_call_tokens,
    save_conversation_state,
    sync_conversation_and_thresholds,
)

WARN_RATIO: float = 0.90
BLOCK_RATIO: float = 0.95
NON_CONTINUABLE_STOP_REASONS: frozenset[str] = frozenset(
    {
        "USER_CANCELED",
        "ERROR",
        "MAX_INVOCATIONS",
        "MAX_FORCED_INVOCATIONS",
        "MAX_TOKEN_BUDGET_EXCEEDED",
    }
)


def build_warning_message(current_tokens: int, threshold_tokens: int) -> str:
    pct: float = compute_usage_percentage(
        current_tokens, threshold_tokens, fallback=90.0
    )
    return (
        "<critical_instructions>\n"
        f"Context usage is at {pct:.1f}% ({current_tokens} / {threshold_tokens} tokens). THIS IS A BUDGET WARNING, NOT A COMPACTION PROMPT.\n"
        "Auto-compaction triggers ONLY when your subsequent tool calls push tokens past 100% capacity mid-loop. Stopping tool calls or writing `<summary>` now freezes token growth below 100% and halts execution without compacting:\n"
        f"1. **One-Time Notification Only**: Notify the user at most ONCE in this entire pre-compaction cycle (in one sentence, in their language, right now) that context is at {pct:.1f}%. NEVER repeat, re-announce, or mention context percentage or save status again on any subsequent tool step or turn.\n"
        "2. **When context holds settled file edits or ledger/artifact updates not yet written to disk**: In your single one-sentence notice, state that you are saving `<file>` first before continuing `<next action>`; dispatch only those write/edit tool calls in this step, and on the very next step after they return, immediately and silently dispatch the tool calls for `<next action>` without repeating the context notice and without outputting `<summary>` or stopping.\n"
        "3. **When all settled changes are already on disk and further task steps remain**: After your single one-sentence notice (if not already sent), immediately dispatch the next tool calls for the current task step now and silently keep dispatching tool calls on every following step until the harness wipes the turn for compaction.\n"
        "4. **When all settled changes are already on disk and 100% of the task is finished**: Do not send a context warning or dispatch extra tool calls; deliver your normal final completion report and end your turn.\n"
        "5. **Strict Prohibition (applies to this step and all subsequent steps before compaction)**: Never repeat the context-usage notice a second time, never output `<summary>`, `Context for governing # User Requests`, `Read-next working set`, or `Settled state and open work` in chat, and never end your turn after a save or read batch to wait for compaction—`<summary>` is written only when the harness explicitly prompts for it after wiping the conversation.\n"
        "</critical_instructions>"
    )


def build_subsequent_block_message(current_tokens: int, threshold_tokens: int) -> str:
    pct: float = compute_usage_percentage(
        current_tokens, threshold_tokens, fallback=95.0
    )
    return (
        f"DEFERRED FOR 1 STEP (context at {pct:.1f}%: {current_tokens}/{threshold_tokens} tokens): "
        "This read/search call is paused for this single step so you can persist in-hand work to disk first. "
        "The budget guard unlocks on the very next step—immediately re-dispatch this call as soon as your persist tool call returns, without outputting `<summary>` or ending your turn."
    )


def build_premature_summary_continue_message(
    current_tokens: int, threshold_tokens: int
) -> str:
    pct: float = compute_usage_percentage(
        current_tokens, threshold_tokens, fallback=95.0
    )
    return (
        "<critical_instructions>\n"
        f"PREMATURE COMPACTION SUMMARY DETECTED (context is at {pct:.1f}%: {current_tokens} / {threshold_tokens} tokens — auto-compaction has NOT occurred yet).\n"
        "The harness has NOT compacted the conversation and did NOT prompt you for a `<summary>`. Outputting `<summary>` (or `Context for governing # User Requests` / `Read-next working set` / `Settled state and open work`) in chat and stopping halts execution and prevents auto-compaction from triggering.\n"
        "Resume the current task immediately in this turn:\n"
        "1. Do NOT apologize, do NOT explain why you output `<summary>`, and do NOT output another summary or status recap.\n"
        "2. Immediately dispatch the concrete tool calls (`edit_file`, `write_file`, `read_file`, `run_command`, etc.) for the next uncompleted step of the task, and keep calling tools continuously until the harness triggers auto-compaction on its own (or deliver the final completion report only if 100% of the task is already finished on disk).\n"
        "</critical_instructions>"
    )


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

    incoming_tokens: int | None = estimate_tool_call_tokens(tool_call)
    if incoming_tokens is None:
        return {"decision": "allow"}

    with conversation_state_lock(state_dir, conv_id):
        state, entry = sync_conversation_and_thresholds(
            conv_id=conv_id,
            fallback_model_name=fallback_model_name,
            transcript_path=transcript_path,
            state_dir=state_dir,
            thresholds_file=thresholds_file,
        )

        current_planner_turn: int = max(state.last_turn, 1)
        projected_state: ConversationTokenState = apply_incoming_tool_tokens(
            state, incoming_tokens
        )
        block_threshold: int = int(entry.compact_threshold * BLOCK_RATIO)
        already_blocked_in_turn: bool = (
            state.blocked_at_planner_turn == current_planner_turn
        )
        already_reminded_in_cycle: bool = state.warned_in_cycle or (
            0 < state.blocked_at_planner_turn < current_planner_turn
        )

        if not already_blocked_in_turn and (
            already_reminded_in_cycle
            or projected_state.effective_tokens < block_threshold
        ):
            if projected_state != state:
                save_conversation_state(state_dir, projected_state)
            return {"decision": "allow"}

        is_first_block_in_turn: bool = not already_blocked_in_turn
        display_tokens: int = max(projected_state.effective_tokens, block_threshold)
        blocked_state: ConversationTokenState = replace(
            apply_incoming_tool_tokens(state, 0),
            warned_in_cycle=True,
            warned_at_tokens=state.warned_at_tokens or display_tokens,
            blocked_at_planner_turn=current_planner_turn,
        )
        save_conversation_state(state_dir, blocked_state)

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

        effective_tokens: int = state.effective_tokens
        warn_threshold: int = int(entry.compact_threshold * WARN_RATIO)

        if effective_tokens < warn_threshold and state.blocked_at_planner_turn == 0:
            if state.warned_in_cycle:
                save_conversation_state(
                    state_dir,
                    replace(
                        state,
                        warned_in_cycle=False,
                        warned_at_tokens=0,
                        post_resumed_at_planner_turn=0,
                        stop_resumed_at_planner_turn=0,
                    ),
                )
            return {"injectSteps": []}

        if not state.warned_in_cycle:
            updated_state: ConversationTokenState = replace(
                state,
                warned_in_cycle=True,
                warned_at_tokens=effective_tokens,
            )
            save_conversation_state(state_dir, updated_state)
            msg: str = build_warning_message(effective_tokens, entry.compact_threshold)
            return {"injectSteps": [{"systemMessage": {"systemMessage": msg}}]}

        return {"injectSteps": []}


def _check_premature_summary_continuation(
    conv_id: str,
    fallback_model_name: str,
    transcript_path: str,
    resumed_field: str,
    state_dir: Path,
    thresholds_file: Path,
) -> str | None:
    if not conv_id.strip():
        return None
    with conversation_state_lock(state_dir, conv_id):
        state, entry = sync_conversation_and_thresholds(
            conv_id=conv_id,
            fallback_model_name=fallback_model_name,
            transcript_path=transcript_path,
            state_dir=state_dir,
            thresholds_file=thresholds_file,
        )
        in_warning_window: bool = (
            state.warned_in_cycle or state.blocked_at_planner_turn > 0
        )
        resumed_turn: int = getattr(state, resumed_field, 0)
        if (
            not in_warning_window
            or not state.has_premature_summary
            or state.last_turn <= 0
            or resumed_turn == state.last_turn
        ):
            return None

        save_conversation_state(
            state_dir,
            replace(
                state,
                warned_in_cycle=True,
                warned_at_tokens=state.warned_at_tokens or state.effective_tokens,
                **{resumed_field: state.last_turn},
            ),
        )
        return build_premature_summary_continue_message(
            state.effective_tokens, entry.compact_threshold
        )


def evaluate_post_invocation_guard(
    conv_id: str,
    fallback_model_name: str,
    transcript_path: str,
    state_dir: Path = DEFAULT_STATE_DIR,
    thresholds_file: Path = DEFAULT_THRESHOLDS_FILE,
) -> dict[str, object]:
    msg: str | None = _check_premature_summary_continuation(
        conv_id,
        fallback_model_name,
        transcript_path,
        "post_resumed_at_planner_turn",
        state_dir,
        thresholds_file,
    )
    if msg is None:
        return {"injectSteps": []}
    return {
        "injectSteps": [{"systemMessage": {"systemMessage": msg}}],
        "terminationBehavior": "force_continue",
    }


def evaluate_stop_guard(
    conv_id: str,
    fallback_model_name: str,
    transcript_path: str,
    termination_reason: str = "NO_TOOL_CALL",
    state_dir: Path = DEFAULT_STATE_DIR,
    thresholds_file: Path = DEFAULT_THRESHOLDS_FILE,
) -> dict[str, object]:
    if termination_reason.strip().upper() in NON_CONTINUABLE_STOP_REASONS:
        return {"decision": "allow"}
    msg: str | None = _check_premature_summary_continuation(
        conv_id,
        fallback_model_name,
        transcript_path,
        "stop_resumed_at_planner_turn",
        state_dir,
        thresholds_file,
    )
    if msg is None:
        return {"decision": "allow"}
    return {"decision": "continue", "reason": msg}


def main() -> None:
    mode: str = sys.argv[1].strip().lower() if len(sys.argv) > 1 else ""
    try:
        raw_input: str = sys.stdin.read()
        payload: object = json.loads(raw_input) if raw_input.strip() else {}
    except Exception:
        if mode == "stop":
            print(json.dumps({"decision": "allow"}))
        else:
            print(json.dumps({"injectSteps": []}))
        return

    if not isinstance(payload, dict):
        if mode == "stop":
            print(json.dumps({"decision": "allow"}))
        else:
            print(json.dumps({"injectSteps": []}))
        return

    conv_id_obj: object = payload.get("conversationId")
    conv_id: str = conv_id_obj if isinstance(conv_id_obj, str) else ""

    model_obj: object = payload.get("modelName")
    model_name: str = model_obj if isinstance(model_obj, str) else ""

    transcript_obj: object = payload.get("transcriptPath")
    transcript_path: str = transcript_obj if isinstance(transcript_obj, str) else ""

    if mode in ("post_invocation", "post"):
        post_result: dict[str, object] = evaluate_post_invocation_guard(
            conv_id=conv_id,
            fallback_model_name=model_name,
            transcript_path=transcript_path,
        )
        print(json.dumps(post_result))
        return

    term_reason_obj: object = payload.get("terminationReason")
    if mode == "stop" or isinstance(term_reason_obj, str):
        term_reason: str = (
            term_reason_obj if isinstance(term_reason_obj, str) else "NO_TOOL_CALL"
        )
        stop_result: dict[str, object] = evaluate_stop_guard(
            conv_id=conv_id,
            fallback_model_name=model_name,
            transcript_path=transcript_path,
            termination_reason=term_reason,
        )
        print(json.dumps(stop_result))
        return

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
