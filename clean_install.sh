#!/bin/bash
set -e

# GTD Framework Clean Install Script
# 1. Syncs source skills & agents inside the repo (wiping stale repo target copies)
# 2. Removes all existing skills & agents in ~/.gemini and ~/.agents
# 3. Runs install.sh to sync the current repo to global targets

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_GEMINI="$HOME/.gemini"
TARGET_AGENTS="$HOME/.agents"

echo "=== Step 1: Syncing workspace skills & agents from SSoT ==="
"$SCRIPT_DIR/sync_workflows.sh"

echo ""
echo "=== Step 2: Cleaning existing skills & agents in target directories ==="
CLEAN_PATHS=(
    "$TARGET_GEMINI/antigravity-cli/skills"
    "$TARGET_GEMINI/antigravity-cli/agents"
    "$TARGET_GEMINI/config/skills"
    "$TARGET_GEMINI/config/agents"
    "$TARGET_AGENTS/skills"
    "$TARGET_AGENTS/agents"
)

for dir in "${CLEAN_PATHS[@]}"; do
    if [ -d "$dir" ]; then
        echo "  Removing: $dir"
        rm -rf "$dir"
    fi
done

echo ""
echo "=== Step 3: Installing current repository ==="
"$SCRIPT_DIR/install.sh"
