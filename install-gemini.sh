#!/bin/bash
set -e

# GTD Framework - Gemini CLI Install Script
# Copies commands, agents, and skills from .gemini/ to target location
#
# Usage:
#   ./install-gemini.sh                    # Local install to ./.gemini/
#   ./install-gemini.sh --global           # Global install to ~/.gemini/

GLOBAL_FLAG="${1:-}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ "$GLOBAL_FLAG" = "--global" ]; then
    GEMINI_DIR="$HOME/.gemini"
else
    GEMINI_DIR="./.gemini"
fi

SOURCE_GEMINI="$SCRIPT_DIR/.gemini"

echo "Installing GTD Framework for Gemini CLI..."
echo "  Source:  $SOURCE_GEMINI"
echo "  Target:  $GEMINI_DIR"
echo ""

# Check source exists
if [ ! -d "$SOURCE_GEMINI" ]; then
    echo "Error: Source .gemini directory not found at $SOURCE_GEMINI"
    exit 1
fi

# Create target directories
mkdir -p "$GEMINI_DIR/commands"
mkdir -p "$GEMINI_DIR/agents"
mkdir -p "$GEMINI_DIR/skills"

# Copy commands
if [ -d "$SOURCE_GEMINI/commands" ]; then
    echo "Copying commands..."
    cp -r "$SOURCE_GEMINI/commands/"* "$GEMINI_DIR/commands/"
    echo "  ✓ Commands: $(ls -1 "$GEMINI_DIR/commands/"*.toml 2>/dev/null | wc -l) files"
fi

# Copy agents
if [ -d "$SOURCE_GEMINI/agents" ]; then
    echo "Copying agents..."
    cp -r "$SOURCE_GEMINI/agents/"* "$GEMINI_DIR/agents/"
    echo "  ✓ Agents: $(ls -1 "$GEMINI_DIR/agents/"*.md 2>/dev/null | wc -l) files"
fi

# Copy skills
if [ -d "$SOURCE_GEMINI/skills" ]; then
    echo "Copying skills..."
    cp -r "$SOURCE_GEMINI/skills/"* "$GEMINI_DIR/skills/"
    echo "  ✓ Skills: $(ls -1 "$GEMINI_DIR/skills/" 2>/dev/null | wc -l) directories"
fi

echo ""
echo "✓ Installation complete!"
echo ""
echo "Installed to: $GEMINI_DIR"
echo "  /commands - Workflow commands (*.toml)"
echo "  /agents   - Sub-agents (*.md)"
echo "  /skills   - Research skills"
