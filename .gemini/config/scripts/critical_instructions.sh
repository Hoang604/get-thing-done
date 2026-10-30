#!/bin/bash
input=$(cat)

# Extract conversationId to track turns per session
CONV_ID=$(echo "$input" | jq -r '.conversationId // empty')
if [ -z "$CONV_ID" ]; then
  CONV_ID="default"
fi

CLEAN_CONV_ID=$(printf '%s' "$CONV_ID" | sed 's/[^a-zA-Z0-9_-]/_/g')
if [ -z "$CLEAN_CONV_ID" ]; then
  CLEAN_CONV_ID="default"
fi

COUNTER_FILE="/tmp/agy_ci_turn_${CLEAN_CONV_ID}"
STATE_FILE="/tmp/agy_compact_state/${CLEAN_CONV_ID}.json"

T=0
LAST_INJECT_T=0
LAST_INJECT_TOKENS=0
if [ -f "$COUNTER_FILE" ]; then
  read -r T LAST_INJECT_T LAST_INJECT_TOKENS < "$COUNTER_FILE"
  [[ "$T" =~ ^[0-9]+$ ]] || T=0
  [[ "$LAST_INJECT_T" =~ ^[0-9]+$ ]] || LAST_INJECT_T=0
  [[ "$LAST_INJECT_TOKENS" =~ ^[0-9]+$ ]] || LAST_INJECT_TOKENS=0
fi
T=$((T + 1))

LAST_TOKENS=0
PENDING_TOKENS=0
if [ -f "$STATE_FILE" ]; then
  read -r LAST_TOKENS PENDING_TOKENS < <(
    jq -r '[(.last_tokens // 0 | floor), (.pending_turn_tokens // 0 | floor)] | @tsv' "$STATE_FILE" 2>/dev/null || echo "0 0"
  )
  [[ "$LAST_TOKENS" =~ ^[0-9]+$ ]] || LAST_TOKENS=0
  [[ "$PENDING_TOKENS" =~ ^[0-9]+$ ]] || PENDING_TOKENS=0
fi
CUR_TOKENS=$((LAST_TOKENS + PENDING_TOKENS))

# Backfill baseline token count once the first PLANNER_RESPONSE reports input tokens
if (( LAST_INJECT_TOKENS == 0 && LAST_TOKENS > 0 )); then
  LAST_INJECT_TOKENS=$LAST_TOKENS
fi

# Detect context compaction drop (< 65% of last injected token count)
COMPACT_DROP=0
if (( LAST_INJECT_TOKENS > 0 && CUR_TOKENS > 0 && CUR_TOKENS * 100 < LAST_INJECT_TOKENS * 65 )); then
  COMPACT_DROP=1
fi


header="<critical_instructions>
Apply the following operational constraints silently; do not narrate them unless explicitly asked."

ci_1="Whenever you hold a belief about the existing code that would change your plan if it were wrong, say it once before the first tool call as an expectation, then the check; the code is the subject of every sentence. Until it is settled, only call tools, including for anything that comes up along the way. When it is settled, say what you found before continuing. Otherwise, just call the tool. Before the first code edit of the task, say what you are about to change."

ci_2="For any tool call, exhaustively map the complete frontier of all independent operations on all known targets (reads, searches, commands, and file mutations across or within files) whose parameters are knowable from current context, and dispatch all mapped tool calls simultaneously within a single concurrent turn. Deferral of an action to a subsequent turn is permitted if and only if its arguments strictly require the runtime return value of an in-flight tool call."

ci_3=$(cat << 'EOF'
Strictly adhere to the `<tool_mechanics>` constraints below.

<tool_mechanics>
- **run_command**: Always set `WaitMsBeforeAsync`=10000. Stop calling tools immediately after launching an async task. Rely on automatic reactive wakeup upon completion. For search, prefer `rg` and `fd` over `grep`, `find`, and `ls`:
  - **`rg`**: Always pass `-n` and regex alternation (`'A|B'`). For symbol, function definitions, prefer extract the body directly in a single pass using `-A N` with N >= 30 over rg + read_file. Bound output with `-A`, `-B`, `-C`, or `| head -n`.
  - **`fd`**: Always specify `-t f` (append `-X wc -l` to get line counts) or `-t d`. Use `-e`, `-d`, and `-H` as appropriate.
  - **Generative Scoping**: Deduce paths, language filters (`-t`), and flags dynamically from target structure.
</tool_mechanics>
EOF
)

footer="</critical_instructions>"

# Inject instructions as a persistent systemMessage at T=1, after 5 turns, after >=30k token growth, or after compaction
if (( T == 1 || LAST_INJECT_T == 0 || T - LAST_INJECT_T >= 5 || CUR_TOKENS - LAST_INJECT_TOKENS >= 30000 || COMPACT_DROP == 1 )); then
  LAST_INJECT_T=$T
  LAST_INJECT_TOKENS=$CUR_TOKENS
  echo "$T $LAST_INJECT_T $LAST_INJECT_TOKENS" > "$COUNTER_FILE"
  message="${header}
${ci_1}
${ci_2}
${ci_3}
${footer}"
  jq -n --arg msg "$message" '{ "injectSteps": [ { "systemMessage": { "systemMessage": $msg } } ] }'
else
  echo "$T $LAST_INJECT_T $LAST_INJECT_TOKENS" > "$COUNTER_FILE"
  jq -n '{ "injectSteps": [] }'
fi
