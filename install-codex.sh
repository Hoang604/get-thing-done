#!/bin/bash
set -e

# Codex CLI Install Script
# Copies agents and skills from .codex/ to target location
#
# Usage:
#   ./install-codex.sh                    # Local install to ./.codex/
#   ./install-codex.sh --global           # Global install to ~/.codex/

GLOBAL_FLAG=""

for arg in "$@"; do
    if [ "$arg" = "--global" ]; then
        GLOBAL_FLAG="--global"
    fi
done

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ "$GLOBAL_FLAG" = "--global" ]; then
    CODEX_DIR="$HOME/.codex"
else
    CODEX_DIR="./.codex"
fi

SOURCE_CODEX="$SCRIPT_DIR/.codex"

echo "Installing Codex Framework..."
echo "  Target:  $CODEX_DIR"
echo ""

# Create target directory if it does not exist yet (as requested)
if [ ! -d "$CODEX_DIR" ]; then
    mkdir -p "$CODEX_DIR"
fi

mkdir -p "$CODEX_DIR/agents"
mkdir -p "$CODEX_DIR/skills"

# Copy agents
if [ -d "$SOURCE_CODEX/agents" ]; then
    echo "Copying agents..."
    cp -r "$SOURCE_CODEX/agents/"* "$CODEX_DIR/agents/" 2>/dev/null || true
    echo "  ✓ Agents copied"
fi

# Copy skills
if [ -d "$SOURCE_CODEX/skills" ]; then
    echo "Copying skills..."
    cp -r "$SOURCE_CODEX/skills/"* "$CODEX_DIR/skills/" 2>/dev/null || true
    echo "  ✓ Skills copied"
fi

CONFIG_FILE="$CODEX_DIR/config.toml"
echo "Updating $CONFIG_FILE..."

# Provide the base config to merge
if [ ! -f "$CONFIG_FILE" ]; then
    cat > "$CONFIG_FILE" << 'EOF'
[features]
multi_agent = true

[agents]
max_threads = 6
max_depth = 1

[agents.test_strategist]
description = "Designs and injects a phase-specific TDD task into PLAN.md from XML query context."
config_file = "agents/test_strategist.toml"

[agents.review_plan]
description = "Pre-execution risk analyzer for plan quality, architecture, and safety concerns."
config_file = "agents/review_plan.toml"

[agents.security]
description = "Security auditor for vulnerability patterns and boundary validation in scoped code."
config_file = "agents/security.toml"

[agents.performance]
description = "Performance auditor for bottlenecks, scaling risks, and resource pressure in scoped code."
config_file = "agents/performance.toml"

[agents.tech_debt]
description = "Technical debt auditor for maintainability risks and refactoring priorities."
config_file = "agents/tech_debt.toml"
EOF
    echo "  ✓ Generated config.toml"
else
    # Python script to safely merge TOML
    MERGE_SCRIPT="$SCRIPT_DIR/merge_codex_config.py"
    if [ -f "$MERGE_SCRIPT" ]; then
        python3 "$MERGE_SCRIPT" "$CONFIG_FILE"
    else
        echo "  ⚠ merge_codex_config.py not found at $MERGE_SCRIPT. Skipping config merge."
    fi

fi


echo ""
echo "✓ Installation complete!"
echo ""
