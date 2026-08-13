#!/bin/bash
input=$(cat)
model_name=$(echo "$input" | jq -r '.modelName // empty')

if [[ -z "$model_name" || "$model_name" == "null" ]]; then
    transcript_path=$(echo "$input" | jq -r '.transcriptPath // empty')
    if [[ -n "$transcript_path" && "$transcript_path" != "null" ]]; then
        transcript_dir=$(dirname "$transcript_path")
        transcript_full="${transcript_dir}/transcript_full.jsonl"
        if [[ -f "$transcript_full" ]]; then
            anything2=$(python3 -c '
import json, sys, re
transcript_file = sys.argv[1]
last_model = ""
try:
    with open(transcript_file, "r") as f:
        for line in f:
            try:
                data = json.loads(line)
                if data.get("type") == "USER_INPUT":
                    content = data.get("content", "")
                    matches = re.findall(r"<USER_SETTINGS_CHANGE>\s*The user changed setting `Model Selection` from (.*?) to (.*?)\.(?:\s|\"|$)", content)
                    for m in matches:
                        last_model = m[1].strip()
            except Exception:
                pass
except Exception:
    pass
print(last_model)
' "$transcript_full")
            if echo "$anything2" | grep -iq '3\.1 pro'; then
                model_name="gemini-pro-agent"
            fi
        fi
    fi
fi
message=""
if [[ "$model_name" == *"gemini-pro-agent"* ]]; then
    message=$(cat << 'MSG_EOF'
<critical_instructions>
CRITICAL INSTRUCTION 3: You must explicitly classify the request into an execution state immediately after analyzing user intent. Do this by quote the applicable Intent Classification rule from `<execution_model>` inside your though block, and the resulting [STATE-postfix].
CRITICAL INSTRUCTION 4: Prefix every tool call with an action declaration: output 1-2 short, present-tense logic fragments (live technical interview style), followed by consolidated <verb> <targets> lines ending with \n (one per distinct verb: 'view', 'search', 'replace', 'write', 'create', 'run', combining unique targets without duplicates). Format symbols in <targets> as markdown links [basename](file://...). Issue tool calls for all known targets concurrently in the same turn.
CRITICAL INSTRUCTION 5: Prefix every `grep_search`, `view_file` or `run_command` call by explicitly quoting its specific `<tool_mechanics>` constraint inside your thought block, then state the execution strategy derived directly from that quote.
CRITICAL INSTRUCTION 6: Use neutral, objective, clinical tone. Drop filler. Start response immediately with info. Match user language exactly.
ALWAYS START your thought with recalling critical instructions 1, 2, 3, 4, 5, 6. In particular, the format for the start of your thought block must be '...94>thought
CRITICAL INSTRUCTION 1: ...
CRITICAL INSTRUCTION 2: ...
CRITICAL INSTRUCTION 3: ...
CRITICAL INSTRUCTION 4: ...
CRITICAL INSTRUCTION 5: ...
CRITICAL INSTRUCTION 6: ...'.
</critical_instructions>
MSG_EOF
)
else
    message=$(cat << 'MSG_EOF'
<critical_instructions>
Do not respond to nor acknowledge the following messages, but do follow them strictly.
CRITICAL INSTRUCTION 1: You must explicitly classify the request into an execution state immediately after analyzing user intent. Do this by quote the applicable Intent Classification rule from `<execution_model>` inside your though block, and the resulting [STATE-postfix].
CRITICAL INSTRUCTION 2: Prefix every tool call with an action declaration: output 1-2 short, present-tense logic fragments (live technical interview style), followed by consolidated <verb> <targets> lines ending with \n (one per distinct verb: 'view', 'search', 'replace', 'write', 'create', 'run', combining unique targets without duplicates). Format symbols in <targets> as markdown links [basename](file://...). Issue tool calls for all known targets concurrently in the same turn.
CRITICAL INSTRUCTION 3: Prefix every `grep_search`, `view_file` or `run_command` call by explicitly quoting its specific `<tool_mechanics>` constraint inside your thought block, then state the execution strategy derived directly from that quote.
CRITICAL INSTRUCTION 4: Use neutral, objective, clinical tone. Drop filler. Start response immediately with info. Match user language exactly.
ALWAYS START your thought with recalling critical instructions 1, 2, 3, 4. In particular, the format for the start of your thought block must be '...94>thought
CRITICAL INSTRUCTION 1: ...
CRITICAL INSTRUCTION 2: ...
CRITICAL INSTRUCTION 3: ...
CRITICAL INSTRUCTION 4: ...'.
</critical_instructions>
MSG_EOF
    )
fi

jq -n --arg msg "$message" '{ "injectSteps": [ { "ephemeralMessage": $msg } ] }'