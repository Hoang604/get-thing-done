#!/usr/bin/env python3
import json
import sys
from pathlib import Path

SCRIPT_DIR: Path = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from compact_threshold_tracker import (
    DEFAULT_STATE_DIR,
    DEFAULT_THRESHOLDS_FILE,
    ConversationTokenState,
    ModelThresholdEntry,
    save_conversation_state,
    sync_conversation_and_thresholds,
)

WARN_RATIO: float = 0.90


def build_warning_message(current_tokens: int, threshold_tokens: int) -> str:
    pct: float = (
        (current_tokens / threshold_tokens) * 100.0 if threshold_tokens > 0 else 90.0
    )
    return (
        "<critical_instructions>\n"
        f"Context usage has reached {pct:.1f}% of the compaction threshold ({current_tokens} / {threshold_tokens} tokens)—volatile context in memory is about to be wiped by compaction.\n"
        "Persist what is already in hand to safe ground before reaching for more (this overrides concurrent-frontier batching across phases and silent application for this turn):\n"
        "1. **Notify the user**: Before calling tools in this turn, tell the user clearly (in their language) that context is nearly full and state what work already in hand you are securing now before continuing.\n"
        "2. **When** context already holds settled inputs and design for any pending changes or actions (independent of unread files): dispatch only those ready actions in this turn to persist them, deferring all tool calls that gather context for untouched work—and any verification whose outcome depends on unupdated members of a coupled batch—to subsequent turns.\n"
        "3. **When** no action is ready to persist yet: dispatch only the calls needed to settle the belief or batch currently open in context so its findings can be recorded as settled observations, rather than opening new untouched items.\n"
        "</critical_instructions>"
    )


def evaluate_budget_guard(
    conv_id: str,
    fallback_model_name: str,
    transcript_path: str,
    state_dir: Path = DEFAULT_STATE_DIR,
    thresholds_file: Path = DEFAULT_THRESHOLDS_FILE,
) -> dict[str, object]:
    if not conv_id.strip():
        return {"injectSteps": []}

    state, entry = sync_conversation_and_thresholds(
        conv_id=conv_id,
        fallback_model_name=fallback_model_name,
        transcript_path=transcript_path,
        state_dir=state_dir,
        thresholds_file=thresholds_file,
    )

    warn_threshold: int = int(entry.compact_threshold * WARN_RATIO)
    if state.last_tokens < warn_threshold:
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
                ),
            )
        return {"injectSteps": []}

    if not state.warned_in_cycle:
        updated_state: ConversationTokenState = ConversationTokenState(
            conversation_id=state.conversation_id,
            model_id=state.model_id,
            last_turn=state.last_turn,
            last_tokens=state.last_tokens,
            warned_in_cycle=True,
            warned_at_tokens=state.last_tokens,
        )
        save_conversation_state(state_dir, updated_state)
        msg: str = build_warning_message(state.last_tokens, entry.compact_threshold)
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

    result: dict[str, object] = evaluate_budget_guard(
        conv_id=conv_id,
        fallback_model_name=model_name,
        transcript_path=transcript_path,
    )
    print(json.dumps(result))


if __name__ == "__main__":
    main()
