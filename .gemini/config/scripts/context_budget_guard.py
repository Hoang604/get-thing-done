#!/usr/bin/env python3
import json
import re
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
    is_compaction_step,
    resolve_transcript_file,
    save_conversation_state,
    sync_conversation_and_thresholds,
)

WARN_RATIO: float = 0.95
BLOCK_RATIO: float = 0.975
PHASE_MARKER_RE: re.Pattern[str] = re.compile(
    r"\b(boundary-plan|execute)\b", re.IGNORECASE
)
NON_CONTINUABLE_STOP_REASONS: frozenset[str] = frozenset(
    {
        "USER_CANCELED",
        "ERROR",
        "MAX_INVOCATIONS",
        "MAX_FORCED_INVOCATIONS",
        "MAX_TOKEN_BUDGET_EXCEEDED",
    }
)


def is_explicit_user_text(text: str) -> bool:
    stripped: str = text.strip()
    if not stripped:
        return False
    if (
        stripped == "/compact"
        or stripped.startswith("/compact ")
        or "<CONTEXT_SUMMARY>" in stripped
        or stripped.startswith("<SYSTEM_MESSAGE>")
    ):
        return False
    return True


def apply_phase_markers(current: bool, text: str) -> bool:
    state: bool = current
    for match in PHASE_MARKER_RE.finditer(text):
        state = match.group(1).lower() == "boundary-plan"
    return state


def is_boundary_plan_phase(transcript_path: str, last_user_input: str = "") -> bool:
    in_boundary_plan: bool = False
    target_file: Path | None = resolve_transcript_file(
        transcript_path, prefer_full=True
    )
    if target_file is not None:
        try:
            with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
                for raw_line in f:
                    line_str: str = raw_line.strip()
                    if not line_str:
                        continue
                    try:
                        step: object = json.loads(line_str)
                    except Exception:
                        continue
                    if not isinstance(step, dict):
                        continue
                    if (
                        step.get("type") != "USER_INPUT"
                        or step.get("source") == "SYSTEM"
                    ):
                        continue
                    if is_compaction_step(step):
                        continue
                    content_obj: object = step.get("content")
                    if not isinstance(content_obj, str) or not is_explicit_user_text(
                        content_obj
                    ):
                        continue
                    in_boundary_plan = apply_phase_markers(
                        in_boundary_plan, content_obj
                    )
        except Exception:
            pass

    if is_explicit_user_text(last_user_input):
        in_boundary_plan = apply_phase_markers(in_boundary_plan, last_user_input)

    return in_boundary_plan


def build_warning_message(
    current_tokens: int,
    threshold_tokens: int,
    boundary_plan_mode: bool = False,
) -> str:
    pct: float = compute_usage_percentage(
        current_tokens, threshold_tokens, fallback=90.0
    )
    step_2: str = (
        (
            "2. **Persist Settled Plan & Verbatim Open Investigations First**: **When** `implementation_plan.md` is not yet finalized under `boundary-plan`, before dispatching any `read_file`/`rg` or other non-persistence tool call, persist `<Artifact Directory>/implementation_plan.md` (`write_file` on first checkpoint, `edit_file` on subsequent checkpoints, `ArtifactMetadata` with `UserFacing: true`, and `RequestFeedback: false` while `## Open Investigations` remains non-empty) by ruling individually while holding other entries fixed:\n"
            "   - **Each section and milestone in scope**: Rule on it individually while holding other entries fixed: **when** `read_file` has inspected every code slice its `boundary-plan` Sections 1–4 fields depend on, write that entry immediately into the settled plan body with every required Sections 1–4 field populated literally from those reads—rather than summarizing it, guessing unread dependencies from `rg` previews, or deferring it to `## Open Investigations`; otherwise keep it out of the settled plan body.\n"
            "   - **Each already-inspected file needed by an unsettled entry & each remaining target**: Record each file individually in `## Open Investigations`: for every inspected slice, give its `#L<start>-L<end>` range and extract verbatim the source expressions and `file:line` coordinates required to compile any unsettled `boundary-plan` Sections 1–4 field referencing that slice—verified before saving by testing each entry as if the source file were deleted from disk, failing it wherever writing that unsettled field literally from the note alone would still require guessing or re-opening the file; pair each remaining `read_file`/`rg` target with the specific unsettled decision inspecting it resolves. Never group multiple files together or replace verbatim source facts with a prose description of what a file does.\n"
            "     *Anchor (`## Open Investigations` shape):*\n"
            "     ```markdown\n"
            "     - **Inspected (do not re-read):** `[parser.py](file:///src/parser.py#L12-L48)` — `parse(raw: str) -> Token` (`#L12`); raises `ParseError` if `not raw.strip()` (`#L18`); calls `tokenize(raw)` (`#L24`); retires `legacy_split` (`#L30-L42`)\n"
            "     - **Remaining:** `[runner.py](file:///src/runner.py)` (`rg \"parse\\(\"` callers) — resolves `Caller Coupling` and `Caller Audit`\n"
            "     ```\n"
            "   *Completion criterion*: every section or milestone whose Sections 1–4 slices are all inspected sits in `implementation_plan.md` with literal Sections 1–4 fields; every already-inspected file needed by unsettled entries appears individually in `## Open Investigations` with its `#L<start>-L<end>` range and passes the deleted-file check (zero grouped bullets or prose file summaries); and non-persistence tool calls run only after this save returns.\n"
        )
        if boundary_plan_mode
        else (
            "2. **Persist Every Settled Change First**: **When** unwritten changes or uncompleted task steps remain, before dispatching any non-persistence tool call, inspect in your thoughts every change already determinable from context to any file whose creation or update is part of the current task under `<user_rules>`, and rule on each candidate change individually (holding other changes fixed and citing verified `file:line` facts in context) whether every codebase fact and `<user_rules>` check required to determine that change is already verified; when any change passes, dispatch only the `write_file`/`edit_file` calls for all passing changes in this step (emitting `<communication_model>`'s pre-edit rulings first if this is the task's first code edit)—never deferring a verified change until remaining files are read, never writing speculative edits that depend on unread facts. *Completion criterion*: every already-verified change to an authorized task file is written to disk before any non-persistence tool call runs.\n"
        )
    )
    return (
        "<critical_instructions>\n"
        f"Context usage is at {pct:.1f}% ({current_tokens} / {threshold_tokens} tokens). If this message denied a read/search tool call, that call is paused for this single step only and is already unlocked for your next response. Execute in order:\n"
        f"1. **Context-Usage Notice**: **When** 100% of the user's request is already completed on disk, omit any context notice and deliver your normal final response; otherwise, in this response only, state a one-sentence notice in the user's language reporting that context is at {pct:.1f}% ({current_tokens} / {threshold_tokens} tokens) and naming any files being saved in this step—never mentioning context usage or save status again and never estimating or inventing a percentage on any step that did not just receive a new hook budget message.\n"
        f"{step_2}"
        "3. **Continue Normal Task Execution**: **When** all changes passing Step 2 are on disk (immediately in this response if none passed, or on the very next step as soon as Step 2's `write_file`/`edit_file` calls return), advance or finish the request by the exact same task-completion and user-interaction conditions as an unwarned turn—silently dispatching the next required tool calls (including re-dispatching any read/search call paused for 1 step by this guard) whenever unblocked task work remains, ending the turn only when the task reaches a genuine completion or user-input boundary, and writing `<summary>` (or `Compaction Summary Protocol` headings) only when the harness explicitly prompts for a compaction summary while the conversation is still in context. *Completion criterion*: execution continues without stopping after a save or emitting a premature `<summary>` until either the user's request reaches a real completion/input boundary or subsequent tool calls trigger the harness's compaction prompt.\n"
        "</critical_instructions>"
    )


def _step_2_heading(boundary_plan_mode: bool) -> str:
    return (
        "Persist Settled Plan & Verbatim Open Investigations First"
        if boundary_plan_mode
        else "Persist Every Settled Change First"
    )


def build_subsequent_block_message(
    current_tokens: int,
    threshold_tokens: int,
    boundary_plan_mode: bool = False,
) -> str:
    pct: float = compute_usage_percentage(
        current_tokens, threshold_tokens, fallback=97.50
    )
    step_2_name: str = _step_2_heading(boundary_plan_mode)
    return (
        f"DEFERRED FOR 1 STEP (context at {pct:.1f}%: {current_tokens} / {threshold_tokens} tokens): "
        f"Paused for this single step alongside the context-budget instruction in this turn, and already unlocked for your next response—apply **{step_2_name}** and **Continue Normal Task Execution** there to re-dispatch this call right after any Step 2 writes return (or immediately in this response if none pass)."
    )


def build_premature_summary_continue_message(
    current_tokens: int,
    threshold_tokens: int,
    boundary_plan_mode: bool = False,
) -> str:
    pct: float = compute_usage_percentage(
        current_tokens, threshold_tokens, fallback=97.50
    )
    step_2_name: str = _step_2_heading(boundary_plan_mode)
    return (
        "<critical_instructions>\n"
        f"PREMATURE COMPACTION SUMMARY DETECTED (context is at {pct:.1f}%: {current_tokens} / {threshold_tokens} tokens — auto-compaction has NOT occurred and the harness has NOT prompted for `<summary>`).\n"
        f"**When** resuming from this premature summary, apply **{step_2_name}** and **Continue Normal Task Execution** from the context-budget instruction earlier in this cycle immediately in this turn—never apologizing, explaining why `<summary>` was emitted, or outputting another summary or status recap.\n"
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

        boundary_plan_mode: bool = is_boundary_plan_phase(transcript_path)
        if is_first_block_in_turn:
            reason_msg: str = build_warning_message(
                display_tokens,
                entry.compact_threshold,
                boundary_plan_mode=boundary_plan_mode,
            )
        else:
            reason_msg = build_subsequent_block_message(
                display_tokens,
                entry.compact_threshold,
                boundary_plan_mode=boundary_plan_mode,
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
    last_user_input: str = "",
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
            boundary_plan_mode: bool = is_boundary_plan_phase(
                transcript_path, last_user_input
            )
            msg: str = build_warning_message(
                effective_tokens,
                entry.compact_threshold,
                boundary_plan_mode=boundary_plan_mode,
            )
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
        boundary_plan_mode: bool = is_boundary_plan_phase(transcript_path)
        return build_premature_summary_continue_message(
            state.effective_tokens,
            entry.compact_threshold,
            boundary_plan_mode=boundary_plan_mode,
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

    last_user_obj: object = payload.get("lastUserInput")
    last_user_input: str = last_user_obj if isinstance(last_user_obj, str) else ""

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
        last_user_input=last_user_input,
    )
    print(json.dumps(result))


if __name__ == "__main__":
    main()
