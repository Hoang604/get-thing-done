#!/bin/bash
input=$(cat)
message=$(cat << 'MSG_EOF'
<critical_instructions>
Do not respond to nor acknowledge the following messages, but do follow them strictly.
CRITICAL INSTRUCTION 1: Prefix every tool-calling turn with an action declaration: output 1-2 present-tense technical interview logic fragments that embed every affected target as a clickable markdown link [basename](file://...).
CRITICAL INSTRUCTION 2: In your reasoning, exhaustively map the complete frontier of all independent operations (reads, searches, commands, and file mutations across distinct files), and dispatch all mapped tool calls simultaneously within a single concurrent turn.
CRITICAL INSTRUCTION 3: Prefix every `grep_search`, `view_file` or `run_command` call by explicitly quoting its specific `<tool_mechanics>` constraint inside your thought block, then state the execution strategy derived directly from that quote.
ALWAYS START your thought by recalling and evaluating Critical Instructions 1, 2, and 3.
</critical_instructions>
MSG_EOF
)

jq -n --arg msg "$message" '{ "injectSteps": [ { "ephemeralMessage": $msg } ] }'
