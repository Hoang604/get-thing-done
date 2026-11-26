#!/bin/bash
# Claude Code UserPromptSubmit hook: injects the parallel-dispatch instruction
# as additional context on every user prompt.

cat > /dev/null

message=$(cat << 'EOF'
<critical_instructions>
Apply the following operational constraints silently; do not narrate them unless explicitly asked.
**When** planning tool calls, exhaustively map the complete frontier of all independent operations (searches, confirmed reads, commands, and file mutations across distinct files) whose parameters and need are already established by facts in context, and dispatch all mapped calls simultaneously in one turn. Defer a call to a subsequent turn if and only if its arguments—or, for a read/mutating call, its relevance or target span—still depend on the outcome of an in-flight call; never pad a batch with speculative reads alongside a search or confirmed target.
<tool_mechanics>
- **Read**:
  - **When** a known pattern or field projection answers the question without reading skipped lines, reduce the file outside context via `Grep` or `Bash` (`rg` for text, `jq`/`python3` for structured data); otherwise use `Read`—anchoring the start line via `Grep`/`rg` first whenever you need only a localized part of a file at unknown lines whose rest is unrelated, rather than guessing line ranges.
  - **When** the facts a planned read would fetch are already present or determinable from active context and nothing since has made what context holds absent or stale against the source, read only the strictly unshown span (or skip the call when none remains).
  - **When** reading a source in successive chunks, stop advancing once the slice already seen shows the remaining portion lies outside the target scope or repeats the same noise—if the question is still open, tighten the query filter or filter outside context via `Bash`/`Grep` instead of pulling more raw chunks.
  - **When** tracing an effect, start at its direct trigger or observation site—verifying concrete inputs and state there—and follow only data or call edges confirmed by that evidence, covering every confirmed source rather than reading speculatively across unrelated layers or neighboring files.
</tool_mechanics>
</critical_instructions>
EOF
)

jq -n --arg msg "$message" '{ "hookSpecificOutput": { "hookEventName": "UserPromptSubmit", "additionalContext": $msg } }'
