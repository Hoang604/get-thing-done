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

STATE_DIR="${AGY_COMPACT_STATE_DIR:-/tmp/agy_compact_state}"
COUNTER_FILE="${AGY_CI_COUNTER_FILE:-/tmp/agy_ci_turn_${CLEAN_CONV_ID}}"
STATE_FILE="${STATE_DIR}/${CLEAN_CONV_ID}.json"

INITIALIZED=0
LAST_INJECT_TOKENS=0
LAST_INJECT_COMPACT_COUNT=0
if [ -f "$COUNTER_FILE" ]; then
  read -r INITIALIZED LAST_INJECT_TOKENS LAST_INJECT_COMPACT_COUNT < "$COUNTER_FILE"
  [[ "$INITIALIZED" =~ ^[0-9]+$ ]] || INITIALIZED=0
  [[ "$LAST_INJECT_TOKENS" =~ ^[0-9]+$ ]] || LAST_INJECT_TOKENS=0
  [[ "$LAST_INJECT_COMPACT_COUNT" =~ ^[0-9]+$ ]] || LAST_INJECT_COMPACT_COUNT=0
fi

CUR_TOKENS=0
COMPACT_COUNT=0
if [ -f "$STATE_FILE" ]; then
  read -r CUR_TOKENS COMPACT_COUNT < <(
    jq -r '[(.effective_tokens // 0), (.compaction_count // 0)] | @tsv' "$STATE_FILE" 2>/dev/null || echo "0 0"
  )
  [[ "$CUR_TOKENS" =~ ^[0-9]+$ ]] || CUR_TOKENS=0
  [[ "$COMPACT_COUNT" =~ ^[0-9]+$ ]] || COMPACT_COUNT=0
fi

# Backfill baseline token count on first report or reset baseline when post-compaction tokens drop
if (( (LAST_INJECT_TOKENS == 0 || CUR_TOKENS < LAST_INJECT_TOKENS) && CUR_TOKENS > 0 )); then
  LAST_INJECT_TOKENS=$CUR_TOKENS
fi

# Compaction state comes directly from compact_threshold_tracker.py
COMPACT_DROP=0
if (( COMPACT_COUNT > LAST_INJECT_COMPACT_COUNT )); then
  COMPACT_DROP=1
fi


header="<critical_instructions>
Apply the following operational constraints silently; do not narrate them unless explicitly asked."

ci_2="For any tool call, exhaustively map the complete frontier of all independent operations on all known targets (reads, searches, commands, and file mutations across or within files) whose parameters are knowable from current context, and dispatch all mapped tool calls simultaneously within a single concurrent turn. Deferral of an action to a subsequent turn is permitted if and only if its arguments strictly require the runtime return value of an in-flight tool call."

ci_3=$(cat << 'EOF'
<tool_mechanics>
- **run_command**: **When** a command goes async and remaining work depends on its result, end the turn immediately and rely on reactive wakeup rather than polling. **When** searching files or paths via shell, use `rg` and `fd` instead of `grep`, `find`, or `ls`:
  - **`rg`**: Pass `-n` whenever reading matched lines (omit `-n` with `-l`). **When** searching multiple known patterns in the same scope, combine them into one call using regex alternation (`'A|B'`). **When** locating a definition whose body you also need to read, pass `-A N` (`N >= 30`) to read it in one pass instead of `rg` then `read_file`. **When** match count is unknown, cap output with `-m` or `| head -n` so broad matches do not flood context.
  - **`fd`**: Specify `-t f` (appending `-X wc -l` when sizing files before reading) or `-t d`, and pass `-H` when targets may live inside dot-directories (`fd` skips hidden paths by default).
  - **Scope narrowing**: **When** target directories, file types, or duplicate/generated paths to exclude are known from context, pass explicit paths and `-g`/`-t` filters rather than scanning the workspace root.
</tool_mechanics>
EOF
)

footer="</critical_instructions>"

# Inject instructions as a persistent systemMessage on first turn, after >=40k token growth, or after compaction
if (( INITIALIZED == 0 || CUR_TOKENS - LAST_INJECT_TOKENS >= 40000 || COMPACT_DROP == 1 )); then
  INITIALIZED=1
  LAST_INJECT_TOKENS=$CUR_TOKENS
  LAST_INJECT_COMPACT_COUNT=$COMPACT_COUNT
  echo "$INITIALIZED $LAST_INJECT_TOKENS $LAST_INJECT_COMPACT_COUNT" > "$COUNTER_FILE"
  message="${header}
${ci_2}
${ci_3}
${footer}"
  jq -n --arg msg "$message" '{ "injectSteps": [ { "systemMessage": { "systemMessage": $msg } } ] }'
else
  echo "$INITIALIZED $LAST_INJECT_TOKENS $LAST_INJECT_COMPACT_COUNT" > "$COUNTER_FILE"
  jq -n '{ "injectSteps": [] }'
fi
