#!/bin/bash
set -e

# Resolve workspace directory relative to this script
WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 1. Sync Skills
SRC_SKILLS="$WORKSPACE_DIR/.gemini/antigravity-cli/skills"
DEST_SKILLS_CFG="$WORKSPACE_DIR/.gemini/config/skills"
DEST_SKILLS_AGENTS="$WORKSPACE_DIR/.agents/skills"

if [[ -d "$SRC_SKILLS" ]]; then
    mkdir -p "$DEST_SKILLS_CFG" "$DEST_SKILLS_AGENTS"
    echo "Syncing skills: $SRC_SKILLS -> $DEST_SKILLS_CFG & $DEST_SKILLS_AGENTS..."
    cp -rf "$SRC_SKILLS/." "$DEST_SKILLS_CFG/"
    cp -rf "$SRC_SKILLS/." "$DEST_SKILLS_AGENTS/"
else
    echo "Warning: Source skills directory not found at $SRC_SKILLS"
fi

# 2. Sync Custom Subagents
SRC_AGENTS="$WORKSPACE_DIR/.gemini/antigravity-cli/agents"
DEST_AGENTS_CFG="$WORKSPACE_DIR/.gemini/config/agents"
DEST_AGENTS_AGENTS="$WORKSPACE_DIR/.agents/agents"

if [[ -d "$SRC_AGENTS" ]]; then
    mkdir -p "$DEST_AGENTS_CFG" "$DEST_AGENTS_AGENTS"
    echo "Syncing agents: $SRC_AGENTS -> $DEST_AGENTS_CFG & $DEST_AGENTS_AGENTS..."
    cp -rf "$SRC_AGENTS/." "$DEST_AGENTS_CFG/"
    cp -rf "$SRC_AGENTS/." "$DEST_AGENTS_AGENTS/"
fi

echo "Done."

