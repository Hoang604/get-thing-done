#!/bin/bash
set -euo pipefail

input=$(cat)
event=$(jq -r '.hook_event_name // empty' <<<"$input")
tracker="$(dirname "$0")/critical_instructions_tracker.py"

emit_context() {
  local context="$1"
  jq -n --arg event "$event" --arg msg "$context" '{hookSpecificOutput:{hookEventName:$event,additionalContext:$msg}}'
}

case "$event" in
  PostModelRequest)
    python3 "$tracker" record <<<"$input" >/dev/null
    exit 0
    ;;
  PreToolUse)
    decision=$(python3 "$tracker" before-tool <<<"$input")
    action=$(jq -r '.action' <<<"$decision")
    case "$action" in
      deny)
        pct=$(jq -r '.percentage' <<<"$decision")
        current=$(jq -r '.current_tokens' <<<"$decision")
        limit=$(jq -r '.limit' <<<"$decision")
        message="DEFERRED FOR 1 STEP (context at ${pct}%: ${current}/${limit} tokens): This read/search call is paused for this single step so you can persist in-hand work to disk first. The budget guard unlocks on the very next step—immediately re-dispatch this call as soon as your persist tool call returns, without outputting \`<summary>\` or ending your turn."
        jq -n --arg msg "$message" '{hookSpecificOutput:{permissionDecision:"deny",permissionDecisionReason:$msg,additionalContext:$msg}}'
        exit 0
        ;;
      warn)
        pct=$(jq -r '.percentage' <<<"$decision")
        current=$(jq -r '.current_tokens' <<<"$decision")
        limit=$(jq -r '.limit' <<<"$decision")
        message=$(cat <<EOF
<critical_instructions>
Context usage is at ${pct}% (${current} / ${limit} tokens). THIS IS A BUDGET WARNING, NOT A COMPACTION PROMPT.
Auto-compaction triggers ONLY when your subsequent tool calls push tokens past 100% capacity mid-loop. Stopping tool calls or writing \`<summary>\` now freezes token growth below 100% and halts execution without compacting:
1. **One-Time Notification Only**: Notify the user at most ONCE in this entire pre-compaction cycle (in one sentence, in their language, right now) that context is at ${pct}%. NEVER repeat, re-announce, or mention context percentage or save status again on any subsequent tool step or turn.
2. **When context holds settled file edits or ledger/artifact updates not yet written to disk**: In your single one-sentence notice, state that you are saving \`<file>\` first before continuing \`<next action>\`; dispatch only those write/edit tool calls in this step, and on the very next step after they return, immediately and silently dispatch the tool calls for \`<next action>\` without repeating the context notice and without outputting \`<summary>\` or stopping.
3. **When all settled changes are already on disk and further task steps remain**: After your single one-sentence notice (if not already sent), immediately dispatch the next tool calls for the current task step now and silently keep dispatching tool calls on every following step until the harness wipes the turn for compaction.
4. **When all settled changes are already on disk and 100% of the task is finished**: Do not send a context warning or dispatch extra tool calls; deliver your normal final completion report and end your turn.
5. **Strict Prohibition (applies to this step and all subsequent steps before compaction)**: Never repeat the context-usage notice a second time, never output \`<summary>\`, \`Context for governing # User Requests\`, \`Read-next working set\`, or \`Settled state and open work\` in chat, and never end your turn after a save or read batch to wait for compaction—\`<summary>\` is written only when the harness explicitly prompts for it after wiping the conversation.
</critical_instructions>
EOF
)
        emit_context "$message"
        exit 0
        ;;
      growth)
        ;;
      *)
        exit 0
        ;;
    esac
    ;;
  PostToolUse)
    action=$(python3 "$tracker" after-tool <<<"$input")
    [[ "$action" == "inject" ]] || exit 0
    ;;
  SessionStart)
    [[ $(jq -r '.source // empty' <<<"$input") == "compact" ]] || exit 0
    python3 "$tracker" compact <<<"$input" >/dev/null
    ;;
  UserPromptSubmit)
    python3 "$tracker" prompt <<<"$input" >/dev/null
    ;;
  *)
    exit 0
    ;;
esac

message=$(cat <<'EOF'
<critical_instructions>
Apply the following operational constraints silently; do not narrate them unless explicitly asked.

For any tool call, exhaustively map the complete frontier of all independent operations on all known targets (reads, searches, commands, and file mutations across or within files) whose parameters are knowable from current context, and dispatch all mapped tool calls simultaneously within a single concurrent turn. Deferral of an action to a subsequent turn is permitted if and only if its arguments strictly require the runtime return value of an in-flight tool call.

<tool_mechanics>
- **Commands**: For a synchronous `exec_command`, set `yield_time_ms`=30000; when starting a background process or intentionally backgrounded job, set `yield_time_ms`=500. When a command returns a session ID and remaining work depends on its result, end the turn and rely on the reactive wakeup rather than polling. When searching files or paths via shell, use `rg` and `fd` instead of `grep`, `find`, or `ls`:
  - **`rg`**: Pass `-n` whenever reading matched lines (omit `-n` with `-l`). **When** searching multiple known patterns in the same scope, combine them into one call using regex alternation (`'A|B'`). **When** locating a definition whose body you also need to read, pass `-A N` (`N >= 30`) to read it in one pass instead of `rg` then `read_file`. **When** match count is unknown, cap output with `-m` or `| head -n` so broad matches do not flood context.
  - **`fd`**: Specify `-t f` (appending `-X wc -l` when sizing files before reading) or `-t d`, and pass `-H` when targets may live inside dot-directories (`fd` skips hidden paths by default).
  - **Scope narrowing**: **When** target directories, file types, or duplicate/generated paths to exclude are known from context, pass explicit paths and `-g`/`-t` filters rather than scanning the workspace root.
</tool_mechanics>
</critical_instructions>
EOF
)

jq -n --arg event "$event" --arg msg "$message" '{
  "hookSpecificOutput": {
    "hookEventName": $event,
    "additionalContext": $msg
  }
}'
