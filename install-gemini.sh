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

# Copy hooks
if [ -d "$SOURCE_GEMINI/hooks" ]; then
    echo "Copying hooks..."
    mkdir -p "$GEMINI_DIR/hooks"
    cp -r "$SOURCE_GEMINI/hooks/"* "$GEMINI_DIR/hooks/"
    echo "  ✓ Hooks: $(ls -1 "$GEMINI_DIR/hooks/" 2>/dev/null | wc -l) files"
fi

# Copy GEMINI.md (thinking protocol)
if [ -f "$SCRIPT_DIR/GEMINI.md" ]; then
    if [ "$GLOBAL_FLAG" = "--global" ]; then
        GEMINI_MD_TARGET="$HOME/.gemini/GEMINI.md"
    else
        GEMINI_MD_TARGET="./GEMINI.md"
    fi
    echo "Copying GEMINI.md..."
    cp -f "$SCRIPT_DIR/GEMINI.md" "$GEMINI_MD_TARGET"
    echo "  ✓ GEMINI.md → $GEMINI_MD_TARGET"
fi

# Update settings.json with hooks configuration (only for global install)
if [ "$GLOBAL_FLAG" = "--global" ]; then
    SETTINGS_FILE="$GEMINI_DIR/settings.json"
    if [ -f "$SETTINGS_FILE" ]; then
        echo "Updating settings.json with hooks configuration..."
        # Use node to merge hooks config, preserving existing hooks
        node -e "
const fs = require('fs');
const settingsContent = fs.readFileSync('$SETTINGS_FILE', 'utf8');
const stripComments = (txt) => txt.replace(/\\\\\"|\"(?:\\\\\"|[^\"])*\"|(\/\/.*|\/\*[\s\\S]*?\*\/)/g, (m, g) => g ? \"\" : m);
const settings = JSON.parse(stripComments(settingsContent));

const newHook = {
    type: 'command',
    command: 'node ~/.gemini/hooks/before.js',
    name: 'Rules',
    description: 'Add rules to prevent gemini do stupid thing',
    timeout: 5000
};

// Initialize hooks structure if not exists
if (!settings.hooks) {
    settings.hooks = {};
}
if (!settings.hooks.BeforeAgent) {
    settings.hooks.BeforeAgent = [];
}

// Find or create the hooks array entry
let hooksEntry = settings.hooks.BeforeAgent.find(e => e.hooks);
if (!hooksEntry) {
    hooksEntry = { hooks: [] };
    settings.hooks.BeforeAgent.push(hooksEntry);
}

// Check if this hook already exists (by name)
const existingIndex = hooksEntry.hooks.findIndex(h => h.name === newHook.name);
if (existingIndex >= 0) {
    hooksEntry.hooks[existingIndex] = newHook;
} else {
    hooksEntry.hooks.push(newHook);
}

fs.writeFileSync('$SETTINGS_FILE', JSON.stringify(settings, null, 2) + '\n');
"
        echo "  ✓ Hooks configuration added to settings.json"
    else
        echo "  ⚠ settings.json not found at $SETTINGS_FILE, skipping hooks configuration"
    fi
fi

# Set environment variables to disable conflicting system prompt sections
BASHRC="$HOME/.bashrc"
ENV_VARS=(
    "export GEMINI_PROMPT_COREMANDATES=0"
    "export GEMINI_PROMPT_PRIMARYWORKFLOWS=0"
    "export GEMINI_PROMPT_OPERATIONALGUIDELINES=0"
)

echo "Configuring environment variables in $BASHRC..."
for var in "${ENV_VARS[@]}"; do
    if ! grep -qF "$var" "$BASHRC" 2>/dev/null; then
        echo "$var" >> "$BASHRC"
        echo "  ✓ Added: $var"
    else
        echo "  ○ Already set: $var"
    fi
done

echo ""
echo "✓ Installation complete!"
echo ""
echo "Installed to: $GEMINI_DIR"
echo "  /commands - Workflow commands (*.toml)"
echo "  /agents   - Sub-agents (*.md)"
echo "  /hooks    - BeforeAgent hook"
echo ""
echo "⚠  IMPORTANT: To apply environment changes, run:"
echo "     source ~/.bashrc"
echo "   Then restart gemini-cli for changes to take effect."
