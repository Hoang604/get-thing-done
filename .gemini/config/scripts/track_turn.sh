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
    LOCK_FILE="${RUN_FILE}.lock"
    ASK_FILE="/tmp/agy_ask_${CONV_ID}"

    TARGET_PHASE=""
    case "$EVENT" in
        pre_invocation)
            echo "0" > "$ASK_FILE" 2>/dev/null || true
            TARGET_PHASE="RUNNING"
            ;;
        pre_ask)
            echo "1" > "$ASK_FILE" 2>/dev/null || true
            TARGET_PHASE="PAUSED"
            ;;
        post_ask)
            echo "0" > "$ASK_FILE" 2>/dev/null || true
            TARGET_PHASE="RUNNING"
            ;;
        stop)
            FULLY_IDLE=$(echo "$PAYLOAD" | jq -r '.fullyIdle // false')
            if [ "$FULLY_IDLE" = "true" ]; then
                echo "0" > "$ASK_FILE" 2>/dev/null || true
                TARGET_PHASE="IDLE"
            fi
            ;;
    esac

    if [ -n "$TARGET_PHASE" ]; then
        (
            flock -x 9 2>/dev/null || true
            PHASE="IDLE"
            ACCUM_SEC=0
            SINCE_TS=0
            NEEDS_WRITE=0

            if [ -f "$RUN_FILE" ]; then
                {
                    read -r L1 || true
                    read -r L2 || true
                    read -r L3 || true
                    read -r L4 || true
                } < "$RUN_FILE"
                case "${L1:-}" in
                    IDLE|RUNNING|PAUSED)
                        PHASE="$L1"
                        ACCUM_SEC="${L2:-0}"
                        SINCE_TS="${L3:-0}"
                        ;;
                    1)
                        PHASE="RUNNING"
                        ACCUM_SEC=0
                        SINCE_TS="${L2:-0}"
                        NEEDS_WRITE=1
                        ;;
                    0)
                        if [ "${L4:-0}" = "1" ]; then
                            PHASE="PAUSED"
                        else
                            PHASE="IDLE"
                        fi
                        ACCUM_SEC="${L3:-0}"
                        SINCE_TS=0
                        NEEDS_WRITE=1
                        ;;
                esac
            fi

            [[ "$ACCUM_SEC" =~ ^[0-9]+$ ]] || ACCUM_SEC=0
            [[ "$SINCE_TS" =~ ^[0-9]+$ ]] || SINCE_TS=0

            if [ "$PHASE" != "$TARGET_PHASE" ]; then
                case "${PHASE}:${TARGET_PHASE}" in
                    IDLE:RUNNING)
                        ACCUM_SEC=0
                        SINCE_TS="$NOW"
                        ;;
                    IDLE:PAUSED)
                        ACCUM_SEC=0
                        SINCE_TS=0
                        ;;
                    RUNNING:PAUSED|RUNNING:IDLE)
                        if [ "$SINCE_TS" -gt 0 ] && [ "$NOW" -gt "$SINCE_TS" ]; then
                            ACCUM_SEC=$((ACCUM_SEC + NOW - SINCE_TS))
                        fi
                        SINCE_TS=0
                        ;;
                    PAUSED:RUNNING)
                        SINCE_TS="$NOW"
                        ;;
                    PAUSED:IDLE)
                        SINCE_TS=0
                        ;;
                esac
                PHASE="$TARGET_PHASE"
                NEEDS_WRITE=1
            elif [ "$PHASE" = "RUNNING" ] && [ "$SINCE_TS" -le 0 ]; then
                SINCE_TS="$NOW"
                NEEDS_WRITE=1
            fi

            if [ "$NEEDS_WRITE" -eq 1 ]; then
                printf "%s\n%s\n%s\n" "$PHASE" "$ACCUM_SEC" "$SINCE_TS" > "$RUN_FILE" 2>/dev/null || true
            fi
        ) 9>"$LOCK_FILE" 2>/dev/null || true
    fi

    if [ "$EVENT" = "pre_ask" ] || [ "$EVENT" = "stop" ]; then
        echo '{"decision": "allow"}'
        exit 0
    fi
fi

echo "{}"
