#!/bin/bash
set -euo pipefail

if [ -f "GEMINI.md" ]; then
    TARGET_FILE="GEMINI.md"
elif [ -f "AGENTS.md" ]; then
    TARGET_FILE="AGENTS.md"
else
    TARGET_FILE="GEMINI.md"
fi

GTD_DIR=".gtd"
CONFIG_FILE="$GTD_DIR/config.yml"

OPTIONS=("Python (uv)" "TypeScript (pnpm)" "Rust (cargo)")
SELECTED=(0 0 0)
CURSOR=0

render_checkbox_menu() {
    echo "Select project language(s) (Up/Down or 1-3, Space to toggle, Enter to confirm):"
    for i in "${!OPTIONS[@]}"; do
        local mark=" "
        if [ "${SELECTED[$i]}" -eq 1 ]; then
            mark="x"
        fi
        local pointer="  "
        if [ "$i" -eq "$CURSOR" ]; then
            pointer="> "
        fi
        echo "${pointer}[${mark}] $((i + 1)). ${OPTIONS[$i]}"
    done
}

select_languages_interactive() {
    if [ ! -t 0 ]; then
        local line=""
        if IFS= read -r line; then
            for token in ${line//,/ }; do
                case "${token,,}" in
                    1|py|python) SELECTED[0]=1 ;;
                    2|ts|typescript) SELECTED[1]=1 ;;
                    3|rs|rust) SELECTED[2]=1 ;;
                esac
            done
        fi
        return
    fi

    render_checkbox_menu
    while true; do
        IFS= read -rsn1 key || break
        if [[ "$key" == $'\x1b' ]]; then
            IFS= read -rsn2 -t 0.05 rest || true
            case "$rest" in
                "[A") CURSOR=$(( (CURSOR - 1 + ${#OPTIONS[@]}) % ${#OPTIONS[@]} )) ;;
                "[B") CURSOR=$(( (CURSOR + 1) % ${#OPTIONS[@]} )) ;;
            esac
        elif [[ "$key" == " " ]]; then
            if [ "${SELECTED[$CURSOR]}" -eq 1 ]; then
                SELECTED[$CURSOR]=0
            else
                SELECTED[$CURSOR]=1
            fi
        elif [[ "$key" == "1" ]]; then
            SELECTED[0]=$(( 1 - SELECTED[0] ))
            CURSOR=0
        elif [[ "$key" == "2" ]]; then
            SELECTED[1]=$(( 1 - SELECTED[1] ))
            CURSOR=1
        elif [[ "$key" == "3" ]]; then
            SELECTED[2]=$(( 1 - SELECTED[2] ))
            CURSOR=2
        elif [[ "$key" == "k" || "$key" == "K" ]]; then
            CURSOR=$(( (CURSOR - 1 + ${#OPTIONS[@]}) % ${#OPTIONS[@]} ))
        elif [[ "$key" == "j" || "$key" == "J" ]]; then
            CURSOR=$(( (CURSOR + 1) % ${#OPTIONS[@]} ))
        elif [[ "$key" == "" ]]; then
            break
        fi

        printf "\033[4A\033[J"
        render_checkbox_menu
    done
    echo ""
}

select_languages_interactive

# Step 2: Ask whether this project allows writing automated tests
TEST_RAW=""
read -r -p "Does this project write automated tests? [Y/n]: " TEST_RAW || true
TEST_CLEAN="${TEST_RAW,,}"
TEST_CLEAN="${TEST_CLEAN// /}"

ALLOW_TESTS=1
if [[ "$TEST_CLEAN" == "n" || "$TEST_CLEAN" == "no" || "$TEST_CLEAN" == "false" || "$TEST_CLEAN" == "0" ]]; then
    ALLOW_TESTS=0
fi

BLOCKS=""

if [ "${SELECTED[0]}" -eq 1 ]; then
    BLOCKS+="# Python: project standard

- When installing packages or running anything in Python, always use \`uv\` (\`uv add\`, \`uv run\`, \`uv sync\`).
- When creating source directories, add \`__init__.py\`.
- When using \`src/\` structure, set \`extraPaths = [\".\"]\` for \`pyright\` in \`pyproject.toml\`.
- When writing Python, import at module top.

"
fi

if [ "${SELECTED[1]}" -eq 1 ]; then
    BLOCKS+="# TypeScript: project standard

- When installing packages or running anything in TypeScript/JavaScript, always use \`pnpm\` (\`pnpm add\`, \`pnpm run\`, \`pnpm exec\`, \`pnpm dlx\`).

"
fi

if [ "${SELECTED[2]}" -eq 1 ]; then
    if [ "$ALLOW_TESTS" -eq 1 ]; then
        BLOCKS+="# Rust: project standard

- When managing packages, building, testing, linting, or running anything in Rust, always use \`cargo\` (\`cargo add\`, \`cargo run\`, \`cargo test\`, \`cargo clippy\`).

"
    else
        BLOCKS+="# Rust: project standard

- When managing packages, building, linting, or running anything in Rust, always use \`cargo\` (\`cargo add\`, \`cargo run\`, \`cargo clippy\`).

"
    fi
fi

if [ "$ALLOW_TESTS" -eq 1 ]; then
    BLOCKS+="# Testing Standard

Every test you write must earn a **REAL** verdict under all four rules:

1. **Contract.** The test guards a rule that the code under test promises to whoever calls it or reads its output, and the rule holds for every valid input. State that promise in one sentence that quotes none of the test's literal values and leaves no room for an output that satisfies the sentence while breaking what a caller of that behavior relies on. If the only sentence you can write repeats the test's expected value, the test pins an outcome, not a contract.
2. **Kills a mutant.** A plausible edit to one product line (\`file:line\`, old → new) that breaks the rule in 1 must be carried by product logic to an assertion and turn it red, where no other REAL test in scope already kills it just as directly. Every part of the outcome that the rule in 1 determines for this test's input must be checked by an assertion, so that no plausible edit to a product line can violate the rule in 1 on this input and still leave the test green (a **surviving mutant**). If the values being compared travel from the test's setup to its assertion without passing through any product decision, no product mutant can reach that assertion.
3. **Survives refactors.** Every edit that keeps the contract leaves the test green. Each assertion may observe only what the contract promises. Anything else it observes is something a refactor is allowed to change.
4. **Reaches the product.** The test enters the product the same way its real callers do, starts from state the real path can produce, and gets the same outcome on every run in the tier where it is filed. Stand-ins are used only at out-of-process boundaries that cannot run locally in the test tier, and each stand-in implements the boundary's stateful contract rather than recording calls.

"
else
    BLOCKS+="# Testing Policy

- Do not write, generate, or run automated tests in this repository unless explicitly requested by the user.

"
fi

if [ -n "$BLOCKS" ]; then
    TMP_FILE=$(mktemp)
    printf "%s" "$BLOCKS" > "$TMP_FILE"
    if [ -f "$TARGET_FILE" ]; then
        cat "$TARGET_FILE" >> "$TMP_FILE"
        echo "Injecting rules to top of existing $TARGET_FILE..."
    else
        echo "Creating new $TARGET_FILE..."
    fi
    mv "$TMP_FILE" "$TARGET_FILE"
    echo "✓ Rules injected into $PWD/$TARGET_FILE"
fi

# Step 3: Initialize .gtd/config.yml with two prompts:
# 1. Enable decision harvester hook?
# 2. N messages interval (default: 10)
ENABLE_RAW=""
read -r -p "Enable GTD decision-harvesting hook in .gtd/config.yml? [Y/n]: " ENABLE_RAW || true
ENABLE_CLEAN="${ENABLE_RAW,,}"
ENABLE_CLEAN="${ENABLE_CLEAN// /}"

ENABLED_VAL="true"
if [[ "$ENABLE_CLEAN" == "n" || "$ENABLE_CLEAN" == "no" || "$ENABLE_CLEAN" == "false" || "$ENABLE_CLEAN" == "0" ]]; then
    ENABLED_VAL="false"
fi

N_RAW=""
read -r -p "Enter message interval N (default: 10): " N_RAW || true
N_CLEAN="${N_RAW// /}"
if [[ -z "$N_CLEAN" ]]; then
    N_VAL=10
elif [[ "$N_CLEAN" =~ ^[0-9]+$ ]] && [ "$N_CLEAN" -ge 1 ]; then
    N_VAL="$N_CLEAN"
else
    echo "Invalid interval '$N_RAW', falling back to default N = 10."
    N_VAL=10
fi

mkdir -p "$GTD_DIR/decisions"

cat << EOF > "$CONFIG_FILE"
enabled: $ENABLED_VAL
every_n_messages: $N_VAL
decisions_dir: ".gtd/decisions"

# Optional prompt customization:
# prompt:
#   replace:
#     full:
#       header: "..."
#       what_to_capture: "..."
#       partitioning: "..."
#       file_contract: "..."
#     reminder:
#       header: "..."
#       reminder: "..."
#   inject:
#     extra_capture_rules: ""
#     partition_hints: ""
#     extra_file_rules: ""
#     extra_reminder_rules: ""
EOF

echo "✓ Initialized $PWD/$CONFIG_FILE (enabled: $ENABLED_VAL, every_n_messages: $N_VAL)"
