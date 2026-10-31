#!/bin/bash
set -euo pipefail

EVENT="${1:-post_invocation}"
PAYLOAD=$(cat)
NOW=$(date +%s)

CONV_ID=$(echo "$PAYLOAD" | jq -r '.conversationId // empty')
INV_NUM=$(echo "$PAYLOAD" | jq -r '.initialNumSteps // empty')

if [ -n "$CONV_ID" ] && [ -n "$INV_NUM" ]; then
    echo "$INV_NUM" > "/tmp/agy_turn_${CONV_ID}"
fi

if [ -n "$CONV_ID" ]; then
    RUN_FILE="/tmp/agy_cumulative_${CONV_ID}.run"
    RUN_ACTIVE=0
    RUN_START_TS=0
    RUN_LAST_ELAPSED=0
    RUN_AWAITING_ASK=0

    if [ -f "$RUN_FILE" ]; then
        {
            read -r RUN_ACTIVE || true
            read -r RUN_START_TS || true
            read -r RUN_LAST_ELAPSED || true
            read -r RUN_AWAITING_ASK || true
        } < "$RUN_FILE"
        RUN_ACTIVE=${RUN_ACTIVE:-0}
        RUN_START_TS=${RUN_START_TS:-0}
        RUN_LAST_ELAPSED=${RUN_LAST_ELAPSED:-0}
        RUN_AWAITING_ASK=${RUN_AWAITING_ASK:-0}
    fi

    case "$EVENT" in
        pre_invocation)
            if [ "$RUN_ACTIVE" -eq 0 ] 2>/dev/null; then
                RUN_ACTIVE=1
                RUN_START_TS="$NOW"
                RUN_LAST_ELAPSED=0
                RUN_AWAITING_ASK=0
                printf "%s\n%s\n%s\n%s\n" "$RUN_ACTIVE" "$RUN_START_TS" "$RUN_LAST_ELAPSED" "$RUN_AWAITING_ASK" > "$RUN_FILE"
            fi
            ;;
        pre_ask)
            if [ "$RUN_ACTIVE" -eq 1 ] && [ "$RUN_START_TS" -gt 0 ] 2>/dev/null; then
                RUN_LAST_ELAPSED=$((NOW - RUN_START_TS))
                [ "$RUN_LAST_ELAPSED" -lt 0 ] && RUN_LAST_ELAPSED=0
            fi
            RUN_ACTIVE=0
            RUN_AWAITING_ASK=1
            printf "%s\n%s\n%s\n%s\n" "$RUN_ACTIVE" "$RUN_START_TS" "$RUN_LAST_ELAPSED" "$RUN_AWAITING_ASK" > "$RUN_FILE"
            echo '{"decision": "allow"}'
            exit 0
            ;;
        post_ask)
            RUN_ACTIVE=1
            RUN_START_TS="$NOW"
            RUN_LAST_ELAPSED=0
            RUN_AWAITING_ASK=0
            printf "%s\n%s\n%s\n%s\n" "$RUN_ACTIVE" "$RUN_START_TS" "$RUN_LAST_ELAPSED" "$RUN_AWAITING_ASK" > "$RUN_FILE"
            ;;
        stop)
            FULLY_IDLE=$(echo "$PAYLOAD" | jq -r '.fullyIdle // false')
            if [ "$FULLY_IDLE" = "true" ]; then
                if [ "$RUN_ACTIVE" -eq 1 ] && [ "$RUN_START_TS" -gt 0 ] 2>/dev/null; then
                    RUN_LAST_ELAPSED=$((NOW - RUN_START_TS))
                    [ "$RUN_LAST_ELAPSED" -lt 0 ] && RUN_LAST_ELAPSED=0
                fi
                RUN_ACTIVE=0
                RUN_AWAITING_ASK=0
                printf "%s\n%s\n%s\n%s\n" "$RUN_ACTIVE" "$RUN_START_TS" "$RUN_LAST_ELAPSED" "$RUN_AWAITING_ASK" > "$RUN_FILE"
            fi
            echo '{"decision": "allow"}'
            exit 0
            ;;
    esac
fi

echo "{}"
