#!/usr/bin/env python3
import json
import re
import sys
from dataclasses import replace
from pathlib import Path
from typing import Literal

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

GuardMode = Literal["default", "boundary-plan", "boundary-auditor"]

WARN_RATIO: float = 0.95
BLOCK_RATIO: float = 0.975
PHASE_MARKER_RE: re.Pattern[str] = re.compile(
    r"\b(boundary-plan|execute)\b", re.IGNORECASE
)
PLAN_ARTIFACT_NAME_RE: re.Pattern[str] = re.compile(
    r"^implementation_plan(?:_round_\d+)?\.md$"
)
SUBAGENT_MESSAGE_RE: re.Pattern[str] = re.compile(
    r"^\[Message\]\s+timestamp=\S+\s+sender=\S+\s+priority=\S+\s+content=(.*?)(?:\r?\n</SYSTEM_MESSAGE>\s*\Z|\Z)",
    re.DOTALL | re.MULTILINE,
)
AUDITOR_DIRECTIVE_RE: re.Pattern[str] = re.compile(
    r"^\s*Audit boundary implementation plan\b.*(?:\bpassive code inspection protocol\b|\baudit_report_round_\d+\.md\b)",
    re.IGNORECASE | re.DOTALL,
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


def apply_phase_markers(current: GuardMode, text: str) -> GuardMode:
    state: GuardMode = current
    for match in PHASE_MARKER_RE.finditer(text):
        state = (
            "boundary-plan"
            if match.group(1).lower() == "boundary-plan"
            else "default"
        )
    return state


def _extract_subagent_directive_text(content: str) -> str | None:
    match: re.Match[str] | None = SUBAGENT_MESSAGE_RE.search(content)
    if match is None:
        return None
    return match.group(1).strip()


def _unwrap_transcript_str(raw: object) -> str | None:
    """Decode JSON-quoted string arguments produced by compact transcript serialization."""
    if not isinstance(raw, str):
        return None
    if len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':
        try:
            decoded: object = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return raw
        return decoded if isinstance(decoded, str) else raw
    return raw


def _is_plan_artifact_path(path: str) -> bool:
    basename: str = path.replace("\\", "/").rsplit("/", 1)[-1]
    return bool(PLAN_ARTIFACT_NAME_RE.fullmatch(basename))


def _is_ignored_non_plan_path(path: str) -> bool:
    normalized: str = path.replace("\\", "/")
    basename: str = normalized.rsplit("/", 1)[-1]
    return basename == "implementation_ledger.md" or "/scratch/" in normalized


def _has_open_plan_markers(text: str) -> bool:
    return "## Open Investigations" in text or "[OPEN:" in text


def _is_plan_write_finalized(tool_name: str, path: str, args: dict[str, object]) -> bool:
    metadata_obj: object = args.get("ArtifactMetadata")
    if isinstance(metadata_obj, dict) and metadata_obj.get("RequestFeedback") is True:
        return True
    if tool_name == "write_file":
        content: str | None = _unwrap_transcript_str(args.get("Content"))
        if content is not None:
            return not _has_open_plan_markers(content)
    if tool_name == "edit_file":
        replacement: str | None = _unwrap_transcript_str(args.get("Replacement"))
        if replacement is not None and _has_open_plan_markers(replacement):
            return False
        plan_file: Path = Path(path)
        if plan_file.is_file():
            try:
                return not _has_open_plan_markers(
                    plan_file.read_text(encoding="utf-8", errors="ignore")
                )
            except Exception:
                return False
    return False


def _apply_planner_tool_calls(
    current: GuardMode,
    tool_calls_obj: object,
    allow_execute_exit: bool,
) -> tuple[GuardMode, bool]:
    if current == "boundary-auditor" or not isinstance(tool_calls_obj, list):
        return current, allow_execute_exit
    state: GuardMode = current
    can_exit_via_execute: bool = allow_execute_exit
    for tc in tool_calls_obj:
        if not isinstance(tc, dict):
            continue
        name_obj: object = tc.get("name")
        args_obj: object = tc.get("args")
        if not isinstance(name_obj, str) or not isinstance(args_obj, dict):
            continue
        if name_obj == "read_file":
            path_str: str | None = _unwrap_transcript_str(args_obj.get("Path"))
            if path_str is not None:
                norm: str = path_str.replace("\\", "/")
                if norm.endswith("/skills/boundary-plan/SKILL.md"):
                    state = "boundary-plan"
                    can_exit_via_execute = False
                elif norm.endswith("/skills/execute/SKILL.md"):
                    if state == "boundary-plan" and can_exit_via_execute:
                        state = "default"
                        can_exit_via_execute = False
        elif name_obj in ("write_file", "edit_file"):
            path_str = _unwrap_transcript_str(args_obj.get("Path"))
            if path_str is None or not path_str.strip():
                continue
            if _is_plan_artifact_path(path_str):
                if _is_plan_write_finalized(name_obj, path_str, args_obj):
                    state = "default"
                else:
                    state = "boundary-plan"
                can_exit_via_execute = False
            elif state == "boundary-plan" and not _is_ignored_non_plan_path(path_str):
                state = "default"
                can_exit_via_execute = False
        elif name_obj == "invoke_subagent" and state == "boundary-plan":
            if _unwrap_transcript_str(args_obj.get("TypeName")) == "boundary-auditor":
                state = "default"
                can_exit_via_execute = False
    return state, can_exit_via_execute


def detect_guard_mode(transcript_path: str, last_user_input: str = "") -> GuardMode:
    mode: GuardMode = "default"
    allow_execute_exit: bool = False
    saw_user_input: bool = False
    saw_opening_system_msg: bool = False
    last_transcript_user_input: str = ""
    system_directive_texts: list[str] = []
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
                    if is_compaction_step(step):
                        continue
                    step_type: object = step.get("type")
                    source: object = step.get("source")
                    if step_type == "PLANNER_RESPONSE":
                        mode, allow_execute_exit = _apply_planner_tool_calls(
                            mode, step.get("tool_calls"), allow_execute_exit
                        )
                        continue

                    content_obj: object = step.get("content")
                    if not isinstance(content_obj, str):
                        continue

                    if step_type == "SYSTEM_MESSAGE" and source == "SYSTEM":
                        directive_text: str | None = _extract_subagent_directive_text(
                            content_obj
                        )
                        if directive_text is not None:
                            system_directive_texts.append(directive_text)
                            if not saw_user_input and not saw_opening_system_msg:
                                saw_opening_system_msg = True
                                if AUDITOR_DIRECTIVE_RE.search(directive_text):
                                    mode = "boundary-auditor"
                        continue

                    if step_type == "USER_INPUT" and source != "SYSTEM":
                        saw_user_input = True
                        if is_explicit_user_text(content_obj):
                            last_transcript_user_input = content_obj.strip()
                            mode = apply_phase_markers(mode, content_obj)
                            if mode == "boundary-plan":
                                allow_execute_exit = not bool(
                                    PHASE_MARKER_RE.search(content_obj)
                                )
                            else:
                                allow_execute_exit = False
        except Exception:
            pass

    if mode != "boundary-auditor" and is_explicit_user_text(last_user_input):
        stripped_last_input: str = last_user_input.strip()
        is_echoed_directive: bool = (
            saw_opening_system_msg
            and not saw_user_input
            and any(
                stripped_last_input == d
                or (
                    "<truncated " in d
                    and len(d) >= 80
                    and stripped_last_input.startswith(d[:80])
                )
                for d in system_directive_texts
            )
        )
        is_already_recorded_user: bool = (
            saw_user_input and stripped_last_input == last_transcript_user_input
        )
        if not saw_user_input and AUDITOR_DIRECTIVE_RE.search(last_user_input):
            mode = "boundary-auditor"
        elif not is_echoed_directive and not is_already_recorded_user:
            mode = apply_phase_markers(mode, last_user_input)

    return mode


_STEP_2_SPEC: dict[GuardMode, tuple[str, str]] = {
    "boundary-plan": (
        "Persist Settled Plan Parts & Open Targets First",
        (
            "2. **Persist Settled Plan Parts & Open Targets First**: **When** the implementation plan is not yet finalized under `boundary-plan`, before dispatching any `read_file`/`rg` or other non-persistence tool call, persist the implementation plan in `<Artifact Directory>` (`write_file` on first checkpoint, `edit_file` on subsequent checkpoints, `ArtifactMetadata` with `UserFacing: true`, and `RequestFeedback: false` while any `[OPEN]` marker or `## Open Investigations` item remains):\n"
            "   - **Each independent plan unit in scope**: Evaluate each unit—a plan-level section, an individual `Canonical Knowledge Rulings` entry, a milestone's Tier 1 block, its `Module & Edge Derivation`, its `Seam Derivation` paired with `Literal Contracts`, or an individual line in `Caller & Sink Audit`, `Retired Forms`, or `File Manifest`—individually while holding the rest fixed (`Seam Derivation` and `Literal Contracts` depend on the boundary's implementation and external production boundary callers, whereas test files and pass-through callers govern only their own lines). Whenever all upstream decisions and `read_file` slices a unit depends on are inspected, write that unit literally into its place in the plan body; whenever any slice a unit depends on remains uninspected, mark that missing part `[OPEN: <what remains>]` inline inside a started milestone (or omit an unstarted unit from settled sections) and list its remaining `read_file`/`rg` targets in `## Open Investigations`.\n"
            "   - **`## Open Investigations` content**: Record in `## Open Investigations` solely what uninspected `[OPEN]` parts still need: pair each remaining `read_file`/`rg` target with the exact `[OPEN]` plan unit it resolves, and retain an `Inspected (do not re-read)` entry (with `#L<start>-L<end>` and verbatim source facts passing the deleted-file check—verified as if the source file were deleted from disk) only for already-inspected slices whose facts are still needed to finish an `[OPEN]` unit rather than repeating facts already written into the settled plan body. Keep one slice/target per bullet (no grouped files or prose file summaries).\n"
            "     *Anchor (partial milestone + `## Open Investigations` shape):*\n"
            "     ```markdown\n"
            "     - **Caller & Sink Audit:**\n"
            "       - Ingress: `ApiHandler.create` at [api.py](file:///src/api.py#L40) -> Milestone 2\n"
            "       - `[OPEN: inspect remaining callers in runner.py]`\n"
            "     #### File Manifest\n"
            "     - `[MODIFY]` [parser.py](file:///src/parser.py#L12-L48)\n"
            "     - `[OPEN: test_parser.py line range]`\n"
            "\n"
            "     ## Open Investigations\n"
            "     - **Inspected (do not re-read):** `[parser.py](file:///src/parser.py#L12-L48)` — `parse(raw: str) -> Token` (`#L12`); raises `ParseError` if `not raw.strip()` (`#L18`) *(kept only if an `[OPEN]` unit still needs these details)*\n"
            "     - **Remaining:** `[runner.py](file:///src/runner.py)` (`rg \"parse\\(\"` callers) — resolves Milestone 1 `Caller & Sink Audit`; `[test_parser.py](file:///tests/test_parser.py)` — resolves Milestone 1 `File Manifest` test line range\n"
            "     ```\n"
            "   *Completion criterion*: every independent plan unit whose own upstream decisions and `read_file` slices are inspected sits literally in the implementation plan (without waiting on unread sibling items or test files); every still-uninspected part inside a started milestone carries an inline `[OPEN: ...]` marker; `## Open Investigations` lists each remaining target paired with its `[OPEN]` unit plus `Inspected (do not re-read)` entries (one slice per bullet with `#L<start>-L<end>`, passing the deleted-file check) strictly for slices still needed by an `[OPEN]` unit; and non-persistence tool calls run only after this save returns.\n"
        ),
    ),
    "boundary-auditor": (
        "Persist Settled Audit Judgments First",
        (
            "2. **Persist Settled Audit Judgments First**: **When** the round's audit report is not yet finalized across the entire audit scope, before dispatching any `read_file`/`rg` or other non-persistence tool call, persist settled findings immediately to `<appDataDir>/brain/<subagent-id>/audit_report_round_<N>.md` (`write_file`, passing `Overwrite: true` on subsequent checkpoints) by ruling individually on each table item (`M-xx`, `B-xx`, `S-xx`, `I-xx`, `R-xx`, `A-xx`), each `Changed Code Coverage` file, and each discovered discrepancy while holding other items fixed: **when** every code slice and `rg` search that item's verdict depends on (`PASS`/`FAIL`/`CLEAN`/`RESIDUE`, all-planes `None` in `Changed Code Coverage`, or a deterministic `F-xx` root cause) has been inspected, write that settled row or `F-xx` entry directly into the report tables and `### Findings`; **when** required reads or searches for an item remain uninspected, omit that row (and mark a `Changed Code Coverage` file `PENDING` alongside any already-confirmed `F-xx` until all planes covering it settle) rather than guessing or writing `## Open Investigations` into the report. Set every `Audit Verdict` status and `Final Delivery Gate` to `PENDING` until full audit coverage is reached, never emit the `Completed:` reply line on a checkpoint, and run remaining non-persistence tool calls only after this save returns. *Completion criterion*: every audit item whose required files and `rg` searches are inspected sits in `audit_report_round_<N>.md`, `Audit Verdict` stays `PENDING`, and non-persistence tool calls run only after this save returns.\n"
        ),
    ),
    "default": (
        "Persist Every Settled Change First",
        (
            "2. **Persist Every Settled Change First**: **When** unwritten changes or uncompleted task steps remain, before dispatching any non-persistence tool call, inspect in your thoughts every change already determinable from context to any file whose creation or update is part of the current task under `<user_rules>`, and rule on each candidate change individually (holding other changes fixed and citing verified `file:line` facts in context) whether every codebase fact and `<user_rules>` check required to determine that change is already verified; when any change passes, dispatch only the `write_file`/`edit_file` calls for all passing changes in this step (emitting `<communication_model>`'s pre-edit rulings first if this is the task's first code edit)—never deferring a verified change until remaining files are read, never writing speculative edits that depend on unread facts. *Completion criterion*: every already-verified change to an authorized task file is written to disk before any non-persistence tool call runs.\n"
        ),
    ),
}


def build_warning_message(
    current_tokens: int,
    threshold_tokens: int,
    guard_mode: GuardMode = "default",
) -> str:
    pct: float = compute_usage_percentage(
        current_tokens, threshold_tokens, fallback=90.0
    )
    _, step_2 = _STEP_2_SPEC[guard_mode]
    return (
        "<critical_instructions>\n"
        f"Context usage is at {pct:.1f}% ({current_tokens} / {threshold_tokens} tokens). If this message denied a read/search tool call, that call is paused for this single step only and is already unlocked for your next response. Execute in order:\n"
        f"1. **Context-Usage Notice**: **When** 100% of the user's request is already completed on disk, omit any context notice and deliver your normal final response; otherwise, in this response only, state a one-sentence notice in the user's language reporting that context is at {pct:.1f}% ({current_tokens} / {threshold_tokens} tokens) and naming any files being saved in this step—never mentioning context usage or save status again and never estimating or inventing a percentage on any step that did not just receive a new hook budget message.\n"
        f"{step_2}"
        "3. **Continue Normal Task Execution**: **When** all changes passing Step 2 are on disk (immediately in this response if none passed, or on the very next step as soon as Step 2's `write_file`/`edit_file` calls return), advance or finish the request by the exact same task-completion and user-interaction conditions as an unwarned turn—silently dispatching the next required tool calls (including re-dispatching any read/search call paused for 1 step by this guard) whenever unblocked task work remains, ending the turn only when the task reaches a genuine completion or user-input boundary, and writing `<summary>` (or `Compaction Summary Protocol` headings) only when the harness explicitly prompts for a compaction summary while the conversation is still in context. *Completion criterion*: execution continues without stopping after a save or emitting a premature `<summary>` until either the user's request reaches a real completion/input boundary or subsequent tool calls trigger the harness's compaction prompt.\n"
        "</critical_instructions>"
    )


def _step_2_heading(guard_mode: GuardMode) -> str:
    return _STEP_2_SPEC[guard_mode][0]


def build_subsequent_block_message(
    current_tokens: int,
    threshold_tokens: int,
    guard_mode: GuardMode = "default",
) -> str:
    pct: float = compute_usage_percentage(
        current_tokens, threshold_tokens, fallback=97.50
    )
    step_2_name: str = _step_2_heading(guard_mode)
    return (
        f"DEFERRED FOR 1 STEP (context at {pct:.1f}%: {current_tokens} / {threshold_tokens} tokens): "
        f"Paused for this single step alongside the context-budget instruction in this turn, and already unlocked for your next response—apply **{step_2_name}** and **Continue Normal Task Execution** there to re-dispatch this call right after any Step 2 writes return (or immediately in this response if none pass)."
    )


def build_premature_summary_continue_message(
    current_tokens: int,
    threshold_tokens: int,
    guard_mode: GuardMode = "default",
) -> str:
    pct: float = compute_usage_percentage(
        current_tokens, threshold_tokens, fallback=97.50
    )
    step_2_name: str = _step_2_heading(guard_mode)
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

        guard_mode: GuardMode = detect_guard_mode(transcript_path)
        if is_first_block_in_turn:
            reason_msg: str = build_warning_message(
                display_tokens,
                entry.compact_threshold,
                guard_mode=guard_mode,
            )
        else:
            reason_msg = build_subsequent_block_message(
                display_tokens,
                entry.compact_threshold,
                guard_mode=guard_mode,
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
            guard_mode: GuardMode = detect_guard_mode(
                transcript_path, last_user_input
            )
            msg: str = build_warning_message(
                effective_tokens,
                entry.compact_threshold,
                guard_mode=guard_mode,
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
        guard_mode: GuardMode = detect_guard_mode(transcript_path)
        return build_premature_summary_continue_message(
            state.effective_tokens,
            entry.compact_threshold,
            guard_mode=guard_mode,
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
