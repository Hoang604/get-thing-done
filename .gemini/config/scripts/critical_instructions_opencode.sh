#!/bin/bash
input=$(cat)

# Extract conversationId to track turns per session
CONV_ID=$(echo "$input" | jq -r '.conversationId // empty')
if [ -z "$CONV_ID" ]; then
  CONV_ID="default"
fi

COUNTER_FILE="/tmp/agy_ci_turn_opencode_${CONV_ID}"

# Increment turn counter T (starts at 1)
if [ -f "$COUNTER_FILE" ]; then
  T=$(($(cat "$COUNTER_FILE") + 1))
else
  T=1
fi
echo "$T" > "$COUNTER_FILE"

header="<critical_instructions>
Apply the following operational constraints silently; do not narrate them unless explicitly asked."

ci_parallel="For any tool call, exhaustively map the complete frontier of all independent operations on all known targets (reads, searches, commands, and file mutations across distinct files) whose parameters are knowable from current context, and dispatch all mapped tool calls simultaneously within a single concurrent turn. Deferral of an action to a subsequent turn is permitted if and only if its arguments strictly require the runtime return value of an in-flight tool call."

ci_mechanics=$(cat << 'EOF'
Strictly adhere to the `<tool_mechanics>` constraints below.

<tool_mechanics>
- **grep**: When searching for multiple known targets (e.g., a list of types, functions, or errors), aggregate them into a single `grep` call using regex (e.g., `TypeA|TypeB|TypeC`). Never execute sequential searches for items in a known set.
</tool_mechanics>
EOF
)

footer="</critical_instructions>"

message="${header}
${ci_parallel}
${ci_mechanics}
${footer}"

jq -n --arg msg "$message" '{ "injectSteps": [ { "ephemeralMessage": $msg } ] }'
