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

A test earns its place by one property: it turns **red** exactly when someone relying on the product would see a break. **When** writing or modifying tests, run both derivations below in order before writing any test code:

**Coverage derivation.** Before writing any test code, inspect each boundary declaration in scope across its interface and execution path to identify (1) every nominal promise it makes and (2) every assumption its nominal path relies on that nothing inside the boundary guarantees—each traced to the concrete line or seam where the boundary meets something outside its control. State the ruling on each identified item individually while holding the other items fixed (citing \`file:line\`; grouping declarations or items into a shared ruling is invalid): for a nominal promise, state the planned test promise; for an assumption, state either \`unreachable\` (citing the structural fact that prevents it from breaking) or \`reachable\` with the invariant the boundary must enforce when it breaks—citing either the guard (\`file:line\`) or \`unguarded\` (\`file:line\`). When any \`reachable\` item is ruled \`unguarded\`, include a failing test against that unguarded site (\`file:line\`) so the missing invariant stays red until implemented. Construct the planned test list strictly from these individual rulings.

**Per-test derivation.** Before writing any test code, evaluate each planned test individually while holding the other planned tests fixed (grouping tests into a shared ruling is invalid): state (1) the Rule 1 contract sentence, (2) the concrete stimulus/setup and assertions, (3) the killed mutant (\`file:line\` \`old → new\` or \`<file>::<symbol>\` \`planned behavior → broken mutation\`) or the unguarded \`file:line\` site turning the test red, (4) \`Surviving mutant\` after falsification against every promise-violating outcome and plausible mutation across the scope, (5) \`Refactor that turns it red\` after falsification against promise-preserving refactors, and (6) the Rule 4 reach path. Tighten or discard any planned test until both falsification verdicts are verified as \`none\`, then write test code strictly from the surviving items.

1. **Contract and tight assertion.** Derive the rule from what the product promises for one independent behavior—never backward from the test's assertions—and state that promise in one sentence that holds for every condition under which that behavior applies (not only nominal valid inputs) without quoting the test's literal values. Every concrete observable outcome that violates any part of that promise under the test's condition must turn an assertion red. If the only sentence you can write repeats the test's expected value, the test pins an outcome rather than a contract.
2. **Kills every plausible mutant or exposes an omitted guard.** Either cite a plausible mutation in the product's decision logic (\`file:line\` \`old → new\` for existing code, or \`<file>::<symbol>\` \`planned behavior → broken mutation\` for unwritten code) that breaks the Rule 1 promise, propagates through product logic to an assertion, and turns it red—and that no other REAL test in scope kills just as directly—or, when the product omits the required guard altogether, cite the unguarded site (\`file:line\`) where the current product already violates the Rule 1 promise and turns an assertion red until the guard is implemented. A value that reaches an assertion unchanged from setup without passing through a product decision kills zero mutants, and a green test on existing code cannot claim an omitted guard. Every plausible mutation of the product logic implementing the Rule 1 promise must be killed by this test or by another REAL test in scope covering the same rule; a test whose assertion or setup leaves any such mutation alive across the scope fails.
3. **Survives refactors.** Every product edit that preserves the Rule 1 promise must leave every assertion green. Each assertion may observe only properties whose change would violate that promise; anything a refactor can alter while preserving the Rule 1 promise fails this rule.
4. **Reaches the product.** Enter and observe the product strictly through declarations invoked by production callers outside the boundary, starting from any initial state that can reach the boundary from outside it (not only states produced by nominal execution). Replace a dependency only across a seam outside in-process logic when the real dependency cannot run or trigger required seam faults deterministically in that tier, using a stand-in that implements that seam's stateful contract—including its failure modes. Every test must produce the same outcome on every run in its test tier, coordinating concurrent interleavings explicitly at the boundary rather than relying on wall-clock timing. Verify behavior solely through observable boundary effects that a violation of the Rule 1 promise would alter—never through uncontracted call history.

**Whole-test verdict.** Evaluate each test as a single unit: a single assertion or setup dependency that fails any of the four rules disqualifies the entire test.

*Completion criterion*: every boundary declaration in scope has emitted individual, ungrouped coverage rulings for all of its nominal promises and external assumptions; every nominal and \`reachable\` ruling is covered by surviving tests constructed strictly from those rulings; and every written test has emitted all six per-test rulings above with \`Surviving mutant\` and \`Refactor that turns it red\` both verified as \`none\`.

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
    read -r -p "Enter message interval N (default: 5): " N_RAW || true
    N_CLEAN="${N_RAW// /}"
    if [[ -z "$N_CLEAN" ]]; then
        N_VAL=5
    elif [[ "$N_CLEAN" =~ ^[0-9]+$ ]] && [ "$N_CLEAN" -ge 1 ]; then
        N_VAL="$N_CLEAN"
    else
        echo "Invalid interval '$N_RAW', falling back to default N = 5."
        N_VAL=5
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
