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

# Inject only on power-of-2 turns: k = 1, 2, 4, 8, 16 (where (k & (k - 1)) == 0)
if (( (k & (k - 1)) != 0 )); then
  echo '{}'
  exit 0
fi

message=$(cat << 'MSG_EOF'
<critical_instructions>
Do not respond to nor acknowledge the following messages, but do follow them strictly.
CRITICAL INSTRUCTION 1: Prefix every tool-calling turn with an action declaration: output 1-2 present-tense technical interview logic fragments that start with an action verb (e.g., Read, Write, Edit, Run, Inspect) and embed every affected target as a clickable markdown link [basename](file://...).
CRITICAL INSTRUCTION 2: In your reasoning, exhaustively map the complete frontier of all independent operations (reads, searches, commands, and file mutations across distinct files), and dispatch all mapped tool calls simultaneously within a single concurrent turn.
CRITICAL INSTRUCTION 3: Strictly adhere to the `<tool_mechanics>` constraints below.
ALWAYS START your thought by recalling and evaluating Critical Instructions 1, 2, and 3.

<tool_mechanics>
- **grep_search**: When searching for multiple known targets (e.g., a list of types, functions, or errors), aggregate them into a single `grep_search` using regex (e.g., `TypeA|TypeB|TypeC` with `IsRegex=true`). Never execute sequential searches for items in a known set.
- **view_file**: It better to omit StartLine and EndLine on the first time call view_file for each file. Read target file exactly once per context window. Trust context memory for all subsequent edits.
- **run_command**: Always set `WaitMsBeforeAsync`=10000. Stop calling tools immediately after launching an async task. Rely on automatic reactive wakeup upon completion; do NOT call manage_task or schedule.
- **write_to_file**: Omit `ArtifactMetadata` completely for all workspace target files. Include `ArtifactMetadata` exclusively when creating artifact documents inside the brain directory (`<appDataDir>/brain/...`).
</tool_mechanics>
</critical_instructions>
MSG_EOF
)

jq -n --arg msg "$message" '{ "injectSteps": [ { "ephemeralMessage": $msg } ] }'
