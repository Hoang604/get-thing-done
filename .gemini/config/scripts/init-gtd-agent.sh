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

A test earns a **REAL** verdict only when it satisfies all 4 criteria below. **When** writing or modifying tests, before writing any test code, derive the test suite directly from the product code under consideration by explicitly outputting the 4 items below for each behavioral commitment (with \`file:line\` coordinates), discard any item that fails any criterion, and write test code strictly from the surviving items:

1. **Contract**: State in one sentence the rule that the code at \`file:line\` promises to its callers or output readers across every valid input without quoting the test's literal values; discard if it only repeats a fixed expected value or pins static wording (pinning outcome).
2. **Kills a mutant**: Specify each plausible edit to a product line (\`file:line\`, \`old → new\`) that breaks the rule in 1 and propagates to the output without already being killed directly by another REAL test in scope, covering every part of the outcome determined by the rule in 1 so no **surviving mutant** escapes; skip writing the test if no such mutant exists.
3. **Survives refactors**: Pinpoint the exact part of the outcome promised by the contract in 1 for assertions so every edit preserving the contract leaves the test green; never assert internal details or static wording that a refactor is allowed to change.
4. **Reaches the product**: Specify the entrypoint entering product code identically to how real callers invoke it with initial state produced by the real flow, and when crossing an out-of-process boundary specify a stateful stand-in (stateful contract) rather than a call-counting mock.

"
else
    BLOCKS+="# Testing Policy

- Do not write, generate, or run automated tests in this repository unless explicitly requested by the user.

"
fi

MANAGED_BLOCK_START="<!-- GTD-INIT:START -->"
MANAGED_BLOCK_END="<!-- GTD-INIT:END -->"

if [ -n "$BLOCKS" ]; then
    GTD_INIT_BLOCKS="$BLOCKS" python3 - "$TARGET_FILE" "$MANAGED_BLOCK_START" "$MANAGED_BLOCK_END" <<'PYEOF'
import os
import re
import sys
from pathlib import Path

target_path = Path(sys.argv[1])
start_marker = sys.argv[2]
end_marker = sys.argv[3]
inner = os.environ["GTD_INIT_BLOCKS"].strip()
managed_block = f"{start_marker}\n{inner}\n{end_marker}"

pattern = re.compile(
    re.escape(start_marker) + r".*?" + re.escape(end_marker),
    re.DOTALL,
)

if target_path.is_file():
    existing = target_path.read_text(encoding="utf-8")
    if pattern.search(existing):
        updated = pattern.sub(lambda _: managed_block, existing, count=1)
        action = "Replaced existing GTD init block in"
    elif existing.strip():
        updated = f"{managed_block}\n\n{existing.lstrip()}"
        action = "Injected GTD init block to top of"
    else:
        updated = f"{managed_block}\n"
        action = "Injected GTD init block into"
else:
    updated = f"{managed_block}\n"
    action = "Created"

tmp_path = target_path.with_suffix(target_path.suffix + ".tmp")
tmp_path.write_text(updated, encoding="utf-8")
os.replace(tmp_path, target_path)
print(f"✓ {action} {target_path.resolve()}")
PYEOF
fi

ALT_CONFIG_FILE="$GTD_DIR/config.yaml"
if [ -f "$CONFIG_FILE" ]; then
    echo "✓ Keeping existing $PWD/$CONFIG_FILE"
elif [ -f "$ALT_CONFIG_FILE" ]; then
    echo "✓ Keeping existing $PWD/$ALT_CONFIG_FILE"
else
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
fi
