#!/bin/bash
# Claude Code UserPromptSubmit hook: injects the parallel-dispatch instruction
# as additional context on every user prompt.

cat > /dev/null

message="<critical_instructions>
Apply the following operational constraints silently; do not narrate them unless explicitly asked.
For any tool call, exhaustively map the complete frontier of all independent operations on all known targets (reads, searches, commands, and file mutations across distinct files) whose parameters are knowable from current context, and dispatch all mapped tool calls simultaneously within a single concurrent turn. Deferral of an action to a subsequent turn is permitted if and only if its arguments strictly require the runtime return value of an in-flight tool call.
</critical_instructions>"

jq -n --arg msg "$message" '{ "hookSpecificOutput": { "hookEventName": "UserPromptSubmit", "additionalContext": $msg } }'
