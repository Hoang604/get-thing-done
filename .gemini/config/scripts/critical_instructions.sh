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
    jq -r '[(.last_tokens // 0), (.compaction_count // 0)] | @tsv' "$STATE_FILE" 2>/dev/null || echo "0 0"
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

ci_2="**When** planning tool calls, exhaustively map the complete frontier of all independent operations (searches, confirmed reads, commands, and file mutations across or within files) whose parameters and need are already established by facts in context, and dispatch all mapped calls simultaneously in one turn. Defer a call to a subsequent turn if and only if its arguments—or, for a read/mutating call, its relevance or target span—still depend on the outcome of an in-flight call; never pad a batch with speculative reads alongside a search or confirmed target."

ci_3=$(cat << 'EOF'
<tool_mechanics>
- **read_file**:
  - **When** a known pattern or field projection answers the question without reading skipped lines, reduce the file outside context via `run_command` (`rg` for text, `jq`/`python3` for structured data); otherwise use `read_file`—anchoring the start line via `rg` first whenever you need only a localized part of a file at unknown lines whose rest is unrelated, rather than guessing line ranges.
  - **When** the facts a planned read would fetch are already present or determinable from active context and nothing since has made what context holds absent or stale against the source, read only the strictly unshown span (or skip the call when none remains).
  - **When** reading a source in successive chunks, stop advancing once the slice already seen shows the remaining portion lies outside the target scope or repeats the same noise—if the question is still open, tighten the query filter or filter outside context via `run_command` instead of pulling more raw chunks.
  - **When** tracing an effect, start at its direct trigger or observation site—verifying concrete inputs and state there—and follow only data or call edges confirmed by that evidence, covering every confirmed source rather than reading speculatively across unrelated layers or neighboring files.
- **run_command**: **When** a command goes async and remaining work depends on its result, end the turn immediately and rely on reactive wakeup rather than polling. **When** searching files or paths via shell, use `rg` and `fd` instead of `grep`, `find`, or `ls`:
  - **`rg`**: Pass `-n` whenever reading matched lines (omit `-n` with `-l`) and `--hidden` when targets may live inside dot-directories (`rg` skips hidden paths by default). **When** searching multiple known patterns in the same scope, combine them into one call using regex alternation (`'A|B'`). **When** locating a unique definition in a narrowed scope whose body you also need, pass `-A N` to read it in one pass instead of `rg` then `read_file`. **When** match count is unknown, cap output with `-m` or `| head -n` so broad matches do not flood context.
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
