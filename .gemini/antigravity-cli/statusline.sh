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

RAW_INPUT=$(cat)

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
  read -r Q5H_FRAC
  read -r Q5H_RESET
  read -r QWK_FRAC
  read -r QWK_RESET
  read -r EMAIL
  read -r DUMMY
} <<< "$(
  echo "$RAW_INPUT" | jq -r '
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
    (.quota["gemini-5h"].remaining_fraction // .quota["3p-5h"].remaining_fraction // .quotas["gemini-5h"].remaining_fraction // ."gemini-5h".remaining_fraction // ""),
    (.quota["gemini-5h"].reset_in_seconds // .quota["3p-5h"].reset_in_seconds // .quotas["gemini-5h"].reset_in_seconds // ."gemini-5h".reset_in_seconds // ""),
    (.quota["gemini-weekly"].remaining_fraction // .quota["3p-weekly"].remaining_fraction // .quotas["gemini-weekly"].remaining_fraction // ."gemini-weekly".remaining_fraction // ""),
    (.quota["gemini-weekly"].reset_in_seconds // .quota["3p-weekly"].reset_in_seconds // .quotas["gemini-weekly"].reset_in_seconds // ."gemini-weekly".reset_in_seconds // ""),
    (.email // .user.email // ""),
    "EOF"
  ' 2>/dev/null || printf "idle\n0\n\nfalse\n\n80\n0\n0\n0\n0\n\n\n\n\n\n\nEOF\n"
)"

# ─── Write Raw Input to tmp/conversation_id/turn-<x>/statusline_input.json ───
if [ -n "$CONV_ID" ]; then
  TURN_VAL=$(cat "/tmp/agy_turn_${CONV_ID}" 2>/dev/null || echo "0")
  SAVE_DIR="/tmp/agy_statusline/${CONV_ID}/turn-${TURN_VAL}"
  mkdir -p "$SAVE_DIR" 2>/dev/null || true
  printf "%s\n" "$RAW_INPUT" > "${SAVE_DIR}/statusline_input.json" 2>/dev/null || true
fi

# ─── Helper Formatters ───────────────────────────────────────────────────────
format_duration() {
  local s="${1:-}"
  if [ -z "$s" ] || [ "$s" = "null" ]; then
    echo ""
    return
  fi
  local sec=${s%.*}
  if [ "$sec" -le 0 ] 2>/dev/null; then
    echo ""
    return
  fi
  local d=$((sec / 86400))
  local rem=$((sec % 86400))
  local h=$((rem / 3600))
  local rem2=$((rem % 3600))
  local m=$((rem2 / 60))

  if [ "$d" -gt 0 ]; then
    if [ "$h" -gt 0 ]; then
      echo "${d}d ${h}h"
    else
      echo "${d}d"
    fi
  elif [ "$h" -gt 0 ]; then
    if [ "$m" -gt 0 ]; then
      echo "${h}h ${m}m"
    else
      echo "${h}h"
    fi
  else
    echo "${m}m"
  fi
}

format_quota() {
  local name="$1"
  local frac="$2"
  local sec="$3"
  local mode="${4:-medium}"
  if [ -z "$frac" ] || [ "$frac" = "null" ]; then
    echo ""
    return
  fi
  local pct_val
  pct_val=$(awk -v f="$frac" 'BEGIN { printf "%d", (f * 100) + 0.5 }' 2>/dev/null || echo "")
  if [ -z "$pct_val" ]; then
    echo ""
    return
  fi

  local q_color
  if [ "$pct_val" -ge 50 ]; then
    q_color="$FG_BRIGHT_GREEN"
  elif [ "$pct_val" -ge 20 ]; then
    q_color="$FG_BRIGHT_YELLOW"
  else
    q_color="$FG_BRIGHT_RED"
  fi

  local label="$name"
  if [ "$mode" = "large" ]; then
    if [ "$name" = "5h" ]; then
      label="5h limit"
    elif [ "$name" = "wk" ]; then
      label="week limit"
    fi
  fi

  local dur=""
  if [ "$mode" != "narrow" ]; then
    dur=$(format_duration "$sec")
  fi

  if [ -n "$dur" ]; then
    echo "${FG_WHITE}${label}:${R} ${q_color}${B}${pct_val}%${R} ${FG_GRAY}(${dur})${R}"
  else
    echo "${FG_WHITE}${label}:${R} ${q_color}${B}${pct_val}%${R}"
  fi
}

format_compact_num() {
  local n="${1:-0}"
  awk -v n="$n" 'BEGIN {
    if (n >= 1000000) {
      printf "%.2fM", n / 1000000
    } else if (n >= 1000) {
      if (n >= 100000) {
        printf "%.0fk", n / 1000
      } else {
        printf "%.1fk", n / 1000
      }
    } else {
      printf "%d", n
    }
  }' | sed 's/\.0*k/k/;s/\.00*M/M/'
}

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
  if [ "$COLS" -lt 85 ]; then
    SHORT_MODEL=$(echo "$MODEL" | sed 's/^Gemini //;s/ (High)//;s/ (Low)//;s/ (Medium)//')
    M="${FG_GRAY} ╱ ${FG_BRIGHT_MAGENTA}${I}${SHORT_MODEL}${R}"
  else
    M="${FG_GRAY} ╱ ${FG_BRIGHT_MAGENTA}${I}${MODEL}${R}"
  fi
fi

# ─── Separators ──────────────────────────────────────────────────────────────
DOT="${FG_GRAY} · ${R}"
SEP="${FG_GRAY} | ${R}"

# ─── Quotas ──────────────────────────────────────────────────────────────────
if [ "$COLS" -ge 120 ]; then
  Q_MODE="large"
elif [ "$COLS" -ge 85 ]; then
  Q_MODE="medium"
else
  Q_MODE="narrow"
fi

Q_5H=$(format_quota "5h" "$Q5H_FRAC" "$Q5H_RESET" "$Q_MODE")
Q_WK=$(format_quota "wk" "$QWK_FRAC" "$QWK_RESET" "$Q_MODE")

QUOTA_BLOCK=""
if [ -n "$Q_5H" ] && [ -n "$Q_WK" ]; then
  QUOTA_BLOCK="${DOT}${Q_5H}${SEP}${Q_WK}"
elif [ -n "$Q_5H" ]; then
  QUOTA_BLOCK="${DOT}${Q_5H}"
elif [ -n "$Q_WK" ]; then
  QUOTA_BLOCK="${DOT}${Q_WK}"
fi

# ─── Email ───────────────────────────────────────────────────────────────────
E=""
if [ -n "$EMAIL" ]; then
  E="${DOT}${FG_GRAY}email: ${R}${FG_CYAN}${EMAIL}${R}"
fi

# ─── Context Bar ─────────────────────────────────────────────────────────────
if [ "$COLS" -lt 85 ]; then
  BAR_LEN=8
else
  BAR_LEN=15
fi

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
        *"3.8 Flash"*)
            PRICE_IN=1.50
            PRICE_CACHE=0.15
            PRICE_OUT=7.00
            ;;
        *"3.7 Flash"*)
            PRICE_IN=0.75
            PRICE_CACHE=0.075
            PRICE_OUT=3.5
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

IN_COMPACT=$(format_compact_num "$CUMULATIVE_IN")
CACHE_COMPACT=$(format_compact_num "$CUMULATIVE_CACHE")
OUT_COMPACT=$(format_compact_num "$CUMULATIVE_OUT")

if [ "$COLS" -ge 120 ]; then
  IN_FMT="${FG_GRAY}total input ${NUM_COLOR}${IN_COMPACT}${R}"
  CACHE_FMT="${FG_GRAY}cache hit ${NUM_COLOR}${CACHE_COMPACT}${R}"
  OUT_FMT="${FG_GRAY}output ${NUM_COLOR}${OUT_COMPACT}${R}"
  COST_FMT=$(echo "$CUMULATIVE_COST" | sed 's/\([0-9]*\.[0-9]*[1-9]\)0*/\1/;s/\.0*$//')
  COST_STR="${FG_GRAY}estimate cost: ${R}${FG_BRIGHT_GREEN}${B}\$${COST_FMT}${R}"
elif [ "$COLS" -ge 85 ]; then
  IN_FMT="${NUM_COLOR}${IN_COMPACT}${R} ${FG_GRAY}in${R}"
  CACHE_FMT="${NUM_COLOR}${CACHE_COMPACT}${R} ${FG_GRAY}cache${R}"
  OUT_FMT="${NUM_COLOR}${OUT_COMPACT}${R} ${FG_GRAY}out${R}"
  COST_FMT=$(echo "$CUMULATIVE_COST" | sed 's/\([0-9]*\.[0-9]*[1-9]\)0*/\1/;s/\.0*$//')
  COST_STR="${FG_GRAY}est: ${R}${FG_BRIGHT_GREEN}${B}\$${COST_FMT}${R}"
else
  IN_FMT="${NUM_COLOR}${IN_COMPACT}${R} ${FG_GRAY}in${R}"
  CACHE_FMT="${NUM_COLOR}${CACHE_COMPACT}${R} ${FG_GRAY}cache${R}"
  OUT_FMT="${NUM_COLOR}${OUT_COMPACT}${R} ${FG_GRAY}out${R}"
  COST_ROUND=$(awk -v c="$CUMULATIVE_COST" 'BEGIN { printf "%.2f", c }')
  COST_STR="${FG_BRIGHT_GREEN}${B}\$${COST_ROUND}${R}"
fi

# ─── Output (Adaptive 2-Line Layout) ─────────────────────────────────────────
LINE1="${S}${M}${V}${QUOTA_BLOCK}${E}"

if [ "$COLS" -lt 80 ]; then
  LINE2=" ${CTX}${DOT}${IN_FMT}${SEP}${CACHE_FMT}${DOT}${COST_STR}"
else
  LINE2=" ${CTX}${DOT}${IN_FMT}${SEP}${CACHE_FMT}${SEP}${OUT_FMT}${DOT}${COST_STR}"
fi

echo -e "${FG_GRAY}╭─${R} ${LINE1}"
echo -e "${FG_GRAY}╰─${R}${LINE2}"
