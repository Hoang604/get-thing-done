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
        f"Context usage is at {pct:.1f}% ({current_tokens} / {threshold_tokens} tokens). If this message denied a read/search tool call, that call is paused for this single step only and is already unlocked for your next response. Execute in order:\n"
        f"1. **Context-Usage Notice**: **When** 100% of the user's request is already completed on disk, omit any context notice and deliver your normal final response; otherwise, in this response only, state a one-sentence notice in the user's language reporting that context is at {pct:.1f}% ({current_tokens} / {threshold_tokens} tokens) and naming any files being saved in this step—never mentioning context usage or save status again and never estimating or inventing a percentage on any step that did not just receive a new hook budget message.\n"
        "2. **Persist Every Settled Change First**: **When** unwritten changes or uncompleted task steps remain, before dispatching any non-persistence tool call, inspect in your thoughts every change already determinable from context to any file whose creation or update is part of the current task under `<user_rules>`, and rule on each candidate change individually (holding other changes fixed and citing verified `file:line` facts in context) whether every codebase fact and `<user_rules>` check required to determine that change is already verified; when any change passes, dispatch only the `write_file`/`edit_file` calls for all passing changes in this step (emitting `<communication_model>`'s pre-edit rulings first if this is the task's first code edit)—never deferring a verified change until remaining files are read, never writing speculative edits that depend on unread facts, and never inventing scratch or summary files outside `<user_rules>`. *Completion criterion*: every already-verified change to an authorized task file is written to disk before any non-persistence tool call runs.\n"
        "3. **Continue Normal Task Execution**: **When** all changes passing Step 2 are on disk (immediately in this response if none passed, or on the very next step as soon as Step 2's `write_file`/`edit_file` calls return), advance or finish the request by the exact same task-completion and user-interaction conditions as an unwarned turn—silently dispatching the next required tool calls (including re-dispatching any read/search call paused for 1 step by this guard) whenever unblocked task work remains, ending the turn only when the task reaches a genuine completion or user-input boundary, and writing `<summary>` (or `Compaction Summary Protocol` headings) only when the harness explicitly prompts for a compaction summary while the conversation is still in context. *Completion criterion*: execution continues without stopping after a save or emitting a premature `<summary>` until either the user's request reaches a real completion/input boundary or subsequent tool calls trigger the harness's compaction prompt.\n"
        "</critical_instructions>"
    )


def build_subsequent_block_message(current_tokens: int, threshold_tokens: int) -> str:
    pct: float = compute_usage_percentage(
        current_tokens, threshold_tokens, fallback=95.0
    )
    return (
        f"DEFERRED FOR 1 STEP (context at {pct:.1f}%: {current_tokens} / {threshold_tokens} tokens): "
        "Paused for this single step alongside the context-budget instruction in this turn, and already unlocked for your next response—apply **Persist Every Settled Change First** and **Continue Normal Task Execution** there to re-dispatch this call right after any Step 2 writes return (or immediately in this response if none pass)."
    )


def build_premature_summary_continue_message(
    current_tokens: int, threshold_tokens: int
) -> str:
    pct: float = compute_usage_percentage(
        current_tokens, threshold_tokens, fallback=95.0
    )
    return (
        "<critical_instructions>\n"
        f"PREMATURE COMPACTION SUMMARY DETECTED (context is at {pct:.1f}%: {current_tokens} / {threshold_tokens} tokens — auto-compaction has NOT occurred and the harness has NOT prompted for `<summary>`).\n"
        "**When** resuming from this premature summary, apply **Persist Every Settled Change First** and **Continue Normal Task Execution** from the context-budget instruction earlier in this cycle immediately in this turn—never apologizing, explaining why `<summary>` was emitted, or outputting another summary or status recap.\n"
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
