#!/bin/bash
set -euo pipefail

# ─── ANSI Helpers (Standard 16-color palette only) ───────────────────────────
R="\033[0m"         # Reset
B="\033[1m"         # Bold
I="\033[3m"         # Italic

FG_RED="\033[31m"
FG_YELLOW="\033[33m"
FG_BLUE="\033[34m"
FG_MAGENTA="\033[35m"
FG_CYAN="\033[36m"
FG_WHITE="\033[37m"
FG_GRAY="\033[90m"
FG_BRIGHT_RED="\033[91m"
FG_BRIGHT_GREEN="\033[92m"
FG_BRIGHT_YELLOW="\033[93m"
FG_BRIGHT_BLUE="\033[94m"
FG_BRIGHT_MAGENTA="\033[95m"
FG_BRIGHT_CYAN="\033[96m"
FG_BRIGHT_WHITE="\033[97m"

NUM_COLOR="${FG_BRIGHT_WHITE}${B}"

# ─── Parse JSON from stdin ───────────────────────────────────────────────────
{
  read -r STATE
  read -r USED_PCT
  read -r VCS_BRANCH
  read -r VCS_DIRTY
  read -r MODEL
  read -r COLS
  read -r DISPLAY_IN_TOKENS
  read -r COST_IN_TOKENS
  read -r OUT_TOKENS
  read -r CACHE_TOKENS
  read -r CONV_ID
  read -r DUMMY
} <<< "$(
  jq -r '
    (.agent_state // "idle"),
    (.context_window.used_percentage // 0),
    (.vcs.branch // ""),
    (.vcs.dirty // false),
    (.model.display_name // ""),
    (.terminal_width // 80),
    (.context_window.total_input_tokens // 0),
    (.context_window.current_usage.input_tokens // 0),
    (.context_window.current_usage.output_tokens // 0),
    (.context_window.current_usage.cache_read_input_tokens // 0),
    (.conversation_id // ""),
    "EOF"
  ' 2>/dev/null || printf "idle\n0\n\nfalse\n\n80\n0\n0\n0\n0\n\nEOF\n"
)"

# ─── Computed Values ─────────────────────────────────────────────────────────
PCT_FMT=$(LC_NUMERIC=C printf "%.1f" "$USED_PCT")
PCT_INT=${USED_PCT%.*}; PCT_INT=${PCT_INT:-0}

# ─── State Indicator ─────────────────────────────────────────────────────────
case "$STATE" in
  idle)     S="${FG_BRIGHT_GREEN}${B}● READY${R}" ;;
  thinking) S="${FG_BRIGHT_YELLOW}${B}◆ THINKING${R}" ;;
  working)  S="${FG_BRIGHT_CYAN}${B}⚙ WORKING${R}" ;;
  tool_use) S="${FG_BRIGHT_MAGENTA}${B}🔧 TOOL${R}" ;;
  *)        S="${FG_WHITE}${B}⏳ $(echo "$STATE" | tr '[:lower:]' '[:upper:]')${R}" ;;
esac

# ─── VCS Branch ──────────────────────────────────────────────────────────────
V=""
if [ -n "$VCS_BRANCH" ]; then
  if [ "$VCS_DIRTY" = "true" ]; then
    V="${FG_GRAY} ╱ ${FG_BRIGHT_RED}${VCS_BRANCH}${FG_BRIGHT_YELLOW}*${R}"
  else
    V="${FG_GRAY} ╱ ${FG_BRIGHT_BLUE}${VCS_BRANCH}${R}"
  fi
fi

# ─── Model ───────────────────────────────────────────────────────────────────
M=""
if [ -n "$MODEL" ]; then
  M="${FG_GRAY} ╱ ${FG_BRIGHT_MAGENTA}${I}${MODEL}${R}"
fi

# ─── Context Bar (15 segments) ───────────────────────────────────────────────
BAR_LEN=15
FILLED=$((PCT_INT * BAR_LEN / 100))
REMAINDER=$(( (PCT_INT * BAR_LEN) % 100 ))

if [ "$PCT_INT" -ge 90 ]; then
  BAR_COLOR="$FG_BRIGHT_RED"
elif [ "$PCT_INT" -ge 60 ]; then
  BAR_COLOR="$FG_BRIGHT_YELLOW"
else
  BAR_COLOR="$FG_BRIGHT_WHITE"
fi

BAR=""
for ((i = 0; i < BAR_LEN; i++)); do
  if [ "$i" -lt "$FILLED" ]; then
    BAR="${BAR}█"
  elif [ "$i" -eq "$FILLED" ]; then
    if [ "$REMAINDER" -ge 75 ]; then
      BAR="${BAR}▓"
    elif [ "$REMAINDER" -ge 50 ]; then
      BAR="${BAR}▒"
    elif [ "$REMAINDER" -ge 25 ]; then
      BAR="${BAR}░"
    else
      BAR="${BAR}·"
    fi
  else
    BAR="${BAR}·"
  fi
done

# ─── Stats ───────────────────────────────────────────────────────────────────
CTX="${FG_GRAY}ctx ${BAR_COLOR}${BAR} ${NUM_COLOR}${PCT_FMT}%${R}"

CUMULATIVE_IN=0
CUMULATIVE_CACHE=0
CUMULATIVE_OUT=0
CUMULATIVE_COST="0.0000"

if [ -n "$CONV_ID" ]; then
  STATE_FILE="/tmp/agy_cumulative_${CONV_ID}"
  TURN_ID=$(cat "/tmp/agy_turn_${CONV_ID}" 2>/dev/null || echo "-1")
  LAST_TURN=$(cat "${STATE_FILE}.turn" 2>/dev/null || echo "-1")
  CUMULATIVE_IN=$(cat "${STATE_FILE}.sum" 2>/dev/null || echo "0")
  CUMULATIVE_CACHE=$(cat "${STATE_FILE}.cache" 2>/dev/null || echo "0")
  CUMULATIVE_OUT=$(cat "${STATE_FILE}.out" 2>/dev/null || echo "0")
  CUMULATIVE_COST=$(cat "${STATE_FILE}.cost" 2>/dev/null || echo "0.0000")

  if [ "$TURN_ID" != "$LAST_TURN" ] && [ "$TURN_ID" != "-1" ]; then
      CUMULATIVE_IN=$((CUMULATIVE_IN + DISPLAY_IN_TOKENS))
      CUMULATIVE_CACHE=$((CUMULATIVE_CACHE + CACHE_TOKENS))
      CUMULATIVE_OUT=$((CUMULATIVE_OUT + OUT_TOKENS))
      
      PRICE_IN=0
      PRICE_CACHE=0
      PRICE_OUT=0
      
      case "$MODEL" in
        *"3.1 Pro"*)
            PRICE_IN=2.00
            PRICE_CACHE=0.50
            PRICE_OUT=12.00
            ;;
        *"3.5 Flash"*)
            PRICE_IN=1.50
            PRICE_CACHE=0.15
            PRICE_OUT=9.00
            ;;
        *"3.6 Flash"*)
            PRICE_IN=1.50
            PRICE_CACHE=0.15
            PRICE_OUT=7.00
            ;;
        *"Claude Sonnet 4.6"*)
            PRICE_IN=3.00
            PRICE_CACHE=0.30
            PRICE_OUT=15.00
            ;;
        *"Claude Opus 4.6"*)
            PRICE_IN=5.00
            PRICE_CACHE=0.50
            PRICE_OUT=25.00
            ;;
        *)
            PRICE_IN=0
            PRICE_CACHE=0
            PRICE_OUT=0
            ;;
      esac

      CUMULATIVE_COST=$(awk -v old="$CUMULATIVE_COST" -v i="$COST_IN_TOKENS" -v pi="$PRICE_IN" \
                            -v c="$CACHE_TOKENS" -v pc="$PRICE_CACHE" -v o="$OUT_TOKENS" -v po="$PRICE_OUT" \
                            'BEGIN { printf "%.4f", old + (i * pi + c * pc + o * po) / 1000000 }')

      echo "$TURN_ID" > "${STATE_FILE}.turn"
      echo "$CUMULATIVE_IN" > "${STATE_FILE}.sum"
      echo "$CUMULATIVE_CACHE" > "${STATE_FILE}.cache"
      echo "$CUMULATIVE_OUT" > "${STATE_FILE}.out"
      echo "$CUMULATIVE_COST" > "${STATE_FILE}.cost"
  fi
fi

IN_TOKENS_FMT=$(echo "$CUMULATIVE_IN" | sed ':a;s/\B[0-9]\{3\}\>/,&/;ta')
CACHE_TOKENS_FMT=$(echo "$CUMULATIVE_CACHE" | sed ':a;s/\B[0-9]\{3\}\>/,&/;ta')
OUT_TOKENS_FMT=$(echo "$CUMULATIVE_OUT" | sed ':a;s/\B[0-9]\{3\}\>/,&/;ta')

SEP="${FG_GRAY} | ${R}"
IN_FMT="${FG_GRAY}total input ${NUM_COLOR}${IN_TOKENS_FMT}${R}"
CACHE_FMT="${FG_GRAY}cache hit ${NUM_COLOR}${CACHE_TOKENS_FMT}${R}"
OUT_FMT="${FG_GRAY}output ${NUM_COLOR}${OUT_TOKENS_FMT}${R}"

COST_FMT=$(echo "$CUMULATIVE_COST" | sed 's/\([0-9]*\.[0-9]*[1-9]\)0*/\1/;s/\.0*$//')
COST_STR="${FG_BRIGHT_GREEN}${B}\$${COST_FMT}${R}"

# ─── Separators ──────────────────────────────────────────────────────────────
DOT="${FG_GRAY} · ${R}"

# ─── Output ──────────────────────────────────────────────────────────────────
LINE1="${S}${M}${V}"
LINE2=" ${CTX}${DOT}${IN_FMT}${SEP}${CACHE_FMT}${SEP}${OUT_FMT}${DOT}estimate cost: ${COST_STR}"

if [ "$COLS" -ge 120 ]; then
  echo -e "${LINE1}${FG_GRAY}  │  ${R}${LINE2}"
elif [ "$COLS" -ge 80 ]; then
  echo -e "${FG_GRAY}╭─${R} ${LINE1}"
  echo -e "${FG_GRAY}╰─${R}${LINE2}"
else
  echo -e "${S}${M}"
  echo -e "${CTX}${DOT}${IN_FMT}${SEP}${CACHE_FMT}${SEP}${OUT_FMT}${DOT}estimate cost: ${COST_STR}"
fi
