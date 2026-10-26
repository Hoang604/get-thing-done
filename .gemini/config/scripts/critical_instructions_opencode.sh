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

ci_1="Whenever you hold a belief about the existing code that would change your plan if it were wrong, say it once before the first tool call as an expectation, then the check; the code is the subject of every sentence. Until it is settled, only call tools, including for anything that comes up along the way. When it is settled, say what you found before continuing. Otherwise, just call the tool. Before the first code edit of the task, say what you are about to change."

ci_2="For any tool call, exhaustively map the complete frontier of all independent operations on all known targets (reads, searches, commands, and file mutations across or within files) whose parameters are knowable from current context, and dispatch all mapped tool calls simultaneously within a single concurrent turn. Deferral of an action to a subsequent turn is permitted if and only if its arguments strictly require the runtime return value of an in-flight tool call."

ci_3=$(cat << 'EOF'
Strictly adhere to the `<tool_mechanics>` constraints below.

<tool_mechanics>
- **grep**: When searching for multiple known targets (e.g., a list of types, functions, or errors), aggregate them into a single `grep` call using regex (e.g., `TypeA|TypeB|TypeC`). Never execute sequential searches for items in a known set.
</tool_mechanics>
EOF
)

footer="</critical_instructions>"

# Alternate turns: inject full instructions on odd turns, turn off completely on even turns
if (( T % 2 == 1 )); then
  message="${header}
${ci_1}
${ci_2}
${ci_3}
${footer}"
  jq -n --arg msg "$message" '{ "injectSteps": [ { "ephemeralMessage": $msg } ] }'
else
  jq -n '{ "injectSteps": [] }'
fi
