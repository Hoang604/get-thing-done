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


header="<critical_instructions>
Apply the following operational constraints silently; do not narrate them unless explicitly asked."

ci_1="During execution, whenever there is a specific prediction about the code before checking it, state it directly as a plain sentence; if not, shut up. Once there are enough results to confirm if the prediction is right or wrong, put out a message so the user can follow before continuing."

ci_2="For any tool call, exhaustively map the complete frontier of all independent operations on all known targets (reads, searches, commands, and file mutations across distinct files) whose parameters are knowable from current context, and dispatch all mapped tool calls simultaneously within a single concurrent turn. Deferral of an action to a subsequent turn is permitted if and only if its arguments strictly require the runtime return value of an in-flight tool call"

ci_3=$(cat << 'EOF'
Strictly adhere to the `<tool_mechanics>` constraints below.

<tool_mechanics>
- **run_command**: Always set `WaitMsBeforeAsync`=10000. Stop calling tools immediately after launching an async task. Rely on automatic reactive wakeup upon completion. For search, prefer `rg` and `fd` over `grep_search` and `list_dir`:
  - **`rg`**: Always pass `-n` and regex alternation (`'A|B'`). Bound output with `-A`, `-B`, `-C`, or `| head -n`.
  - **`fd`**: Always specify `-t f` or `-t d`. Use `-e`, `-d`, and `-H` as appropriate.
  - **Generative Scoping**: Deduce paths, language filters (`-t`), and flags dynamically from target structure.
- **view_file**: It better to omit StartLine and EndLine on the first time call view_file for each file. If you want read a slice LN:M, read L(N-20):(M+30), one re-read cost more than 50 lines at the start. If you are plan to call replace_file_content more than two chunk in the same file, read the entire file.
- **write_to_file**: Omit `ArtifactMetadata` completely for all workspace target files. Include `ArtifactMetadata` exclusively when creating artifact documents inside the brain directory (`<appDataDir>/brain/...`).
- **replace_file_content**: When performing multiple edits on the same file, always execute replacements in bottom-to-top order (descending line numbers: highest lines first) to prevent line number drift from invalidating subsequent `StartLine`/`EndLine` ranges.
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
