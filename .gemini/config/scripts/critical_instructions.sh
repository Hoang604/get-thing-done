#!/bin/bash
input=$(cat)

# Extract conversationId to track turns per session
CONV_ID=$(echo "$input" | jq -r '.conversationId // empty')
if [ -z "$CONV_ID" ]; then
  CONV_ID="default"
fi

COUNTER_FILE="/tmp/agy_ci_turn_${CONV_ID}"

# Increment turn counter T (starts at 1)
if [ -f "$COUNTER_FILE" ]; then
  T=$(($(cat "$COUNTER_FILE") + 1))
else
  T=1
fi
echo "$T" > "$COUNTER_FILE"

# Position k within the 16-turn cycle: k in [1..16]
k=$(( (T - 1) % 16 + 1 ))

header="<critical_instructions>
Apply the following operational constraints silently; do not narrate them unless explicitly asked."

ci_1="Prefix every tool-calling turn with an action declaration: output 1-2 present-tense technical interview logic fragments that start with an action verb (e.g., Read, Write, Edit, Run, Inspect) and embed affected target as a clickable markdown link [basename](file://...)."

ci_2="For any tool call, exhaustively map the complete frontier of all independent operations on all known targets (reads, searches, commands, and file mutations across distinct files) whose parameters are knowable from current context, and dispatch all mapped tool calls simultaneously within a single concurrent turn. Deferral of an action to a subsequent turn is permitted if and only if its arguments strictly require the runtime return value of an in-flight tool call"

ci_3=$(cat << 'EOF'
Strictly adhere to the `<tool_mechanics>` constraints below.

<tool_mechanics>
- **grep_search**: When searching for multiple known targets (e.g., a list of types, functions, or errors), aggregate them into a single `grep_search` using regex (e.g., `TypeA|TypeB|TypeC` with `IsRegex=true`). Never execute sequential searches for items in a known set.
- **view_file**: It better to omit StartLine and EndLine on the first time call view_file for each file. If you want read a slice LN:M, read L(N-10):(M+30), one re-read cost more than 50 lines at the start.
- **run_command**: Always set `WaitMsBeforeAsync`=10000. Stop calling tools immediately after launching an async task. Rely on automatic reactive wakeup upon completion;
- **write_to_file**: Omit `ArtifactMetadata` completely for all workspace target files. Include `ArtifactMetadata` exclusively when creating artifact documents inside the brain directory (`<appDataDir>/brain/...`).
- **replace_file_content**: When performing multiple edits on the same file, always execute replacements in bottom-to-top order (descending line numbers: highest lines first) to prevent line number drift from invalidating subsequent `StartLine`/`EndLine` ranges.
</tool_mechanics>
EOF
)

footer="</critical_instructions>"

# Power-of-2 turns: k = 1, 2, 4, 8, 16 (where (k & (k - 1)) == 0)
# ci_2 and ci_3 are always injected on every turn.
# ci_1 is injected only on power-of-2 turns.
if (( (k & (k - 1)) == 0 )); then
  message="${header}
${ci_1}
${ci_2}
${ci_3}
${footer}"
else
  message="${header}
${ci_2}
${ci_3}
${footer}"
fi

jq -n --arg msg "$message" '{ "injectSteps": [ { "ephemeralMessage": $msg } ] }'
