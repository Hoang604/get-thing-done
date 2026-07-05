#!/bin/bash
set -euo pipefail

PAYLOAD=$(cat)

CONV_ID=$(echo "$PAYLOAD" | jq -r '.conversationId // empty')
INV_NUM=$(echo "$PAYLOAD" | jq -r '.initialNumSteps // empty')

if [ -n "$CONV_ID" ] && [ -n "$INV_NUM" ]; then
    echo "$INV_NUM" > "/tmp/agy_turn_${CONV_ID}"
fi

echo "{}"
