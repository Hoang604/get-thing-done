#!/bin/bash
set -e

# GTD Framework - Gemini CLI Install Script
# Copies commands, agents, and skills from .gemini/ to target location
#
# Usage:
#   ./install-gemini.sh                    # Local install to ./.gemini/
#   ./install-gemini.sh --global           # Global install to ~/.gemini/
#   ./install-gemini.sh --global --replace_systemmd  # Set up new system instructions

GLOBAL_FLAG=""
REPLACE_SYSTEM_MD=""
AGGRESSIVE_FLAG=""

for arg in "$@"; do
    if [ "$arg" = "--global" ]; then
        GLOBAL_FLAG="--global"
    elif [ "$arg" = "--replace_systemmd" ]; then
        REPLACE_SYSTEM_MD="true"
    elif [ "$arg" = "--aggressive" ]; then
        AGGRESSIVE_FLAG="true"
    fi
done

if [ "$REPLACE_SYSTEM_MD" = "true" ] && [ "$GLOBAL_FLAG" != "--global" ]; then
    echo "Error: --replace_systemmd can only be used with --global"
    exit 1
fi

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
    if [ "$GLOBAL_FLAG" = "--global" ]; then
        mkdir -p "$GEMINI_DIR/hooks/state"
    fi
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
    if [ "$REPLACE_SYSTEM_MD" = "true" ]; then
        echo "Replacing gemini-cli-system.md..."
        if [ -f "$SCRIPT_DIR/gemini-cli-system.md" ]; then
            cp -f "$SCRIPT_DIR/gemini-cli-system.md" "$GEMINI_DIR/gemini-cli-system.md"
            echo "  ✓ gemini-cli-system.md → $GEMINI_DIR/gemini-cli-system.md"

            # Update ~/.bashrc
            BASHRC_FILE="$HOME/.bashrc"
            EXPORT_LINE='export GEMINI_SYSTEM_MD="$HOME/.gemini/gemini-cli-system.md"'
            
            if [ -f "$BASHRC_FILE" ] && ! grep -qF "$EXPORT_LINE" "$BASHRC_FILE" 2>/dev/null; then
                echo "" >> "$BASHRC_FILE"
                echo "$EXPORT_LINE" >> "$BASHRC_FILE"
                echo "  ✓ Added GEMINI_SYSTEM_MD to ~/.bashrc"
                echo "  ⚠ Please run 'source ~/.bashrc' or restart your terminal."
            else
                echo "  ✓ GEMINI_SYSTEM_MD already in ~/.bashrc"
            fi
        else
            echo "  ⚠ gemini-cli-system.md not found in $SCRIPT_DIR, skipping"
        fi
    fi

    SETTINGS_FILE="$GEMINI_DIR/settings.json"
    if [ ! -f "$SETTINGS_FILE" ]; then
        echo "{}" > "$SETTINGS_FILE"
    fi

    if [ -f "$SETTINGS_FILE" ]; then
        echo "Updating settings.json with hooks configuration..."
        # Use node to merge hooks config, preserving existing hooks
        node -e "
const fs = require('fs');
const settingsContent = fs.readFileSync('$SETTINGS_FILE', 'utf8');
const stripComments = (txt) => txt.replace(/\\\\\"|\"(?:\\\\\"|[^\"])*\"|(\/\/.*|\/\*[\s\\S]*?\*\/)/g, (m, g) => g ? \"\" : m);
const settings = JSON.parse(stripComments(settingsContent));

const hookDefinitions = [
    {
        event: 'BeforeAgent',
        matcher: null,
        hook: {
            type: 'command',
            command: 'node ~/.gemini/hooks/before.js',
            name: 'Rules',
            description: 'Inject concise behavioral rules before each turn',
            timeout: 5000
        }
    },
    {
        event: 'AfterTool',
        matcher: '*',
        hook: {
            type: 'command',
            command: 'node ~/.gemini/hooks/after-tool.js',
            name: 'AcknowledgeTool',
            description: 'Record tool usage and require an acknowledgement on the next reply',
            timeout: 5000
        }
    }
];

if ('$AGGRESSIVE_FLAG' === 'true') {
    hookDefinitions.push({
        event: 'AfterAgent',
        matcher: null,
        hook: {
            type: 'command',
            command: 'node ~/.gemini/hooks/after-agent.js',
            name: 'ValidateAcknowledgement',
            description: 'Reject post-tool replies that skip Findings and Next action',
            timeout: 5000
        }
    });
} else if (settings.hooks && settings.hooks['AfterAgent']) {
    settings.hooks['AfterAgent'] = settings.hooks['AfterAgent'].map(entry => {
        if (Array.isArray(entry.hooks)) {
            entry.hooks = entry.hooks.filter(h => h.name !== 'ValidateAcknowledgement');
        }
        return entry;
    }).filter(entry => !Array.isArray(entry.hooks) || entry.hooks.length > 0);
    
    if (settings.hooks['AfterAgent'].length === 0) {
        delete settings.hooks['AfterAgent'];
    }
}

// Initialize hooks structure if not exists
if (!settings.hooks) {
    settings.hooks = {};
}

for (const definition of hookDefinitions) {
    if (!settings.hooks[definition.event]) {
        settings.hooks[definition.event] = [];
    }

    let hooksEntry = settings.hooks[definition.event].find((entry) => {
        const matcher = Object.prototype.hasOwnProperty.call(entry, 'matcher') ? entry.matcher : null;
        return matcher === definition.matcher && Array.isArray(entry.hooks);
    });

    if (!hooksEntry) {
        hooksEntry = definition.matcher === null
            ? { hooks: [] }
            : { matcher: definition.matcher, hooks: [] };
        settings.hooks[definition.event].push(hooksEntry);
    }

    const existingIndex = hooksEntry.hooks.findIndex((hook) => hook.name === definition.hook.name);
    if (existingIndex >= 0) {
        hooksEntry.hooks[existingIndex] = definition.hook;
    } else {
        hooksEntry.hooks.push(definition.hook);
    }
}

// Update context.fileName if replace_systemmd is true
if ('$REPLACE_SYSTEM_MD' === 'true') {
    if (!settings.context) {
        settings.context = {};
    }
    settings.context.fileName = ['.gtd/CODEBASE.md', '.gtd/codebase/architecture.md', '.gtd/codebase/entrypoints.md', '.gtd/codebase/patterns.md', '.gtd/codebase/open-questions.md', '.gtd/codebase/domains/index.md', '.gtd/codebase/infra/index.md'];
}

fs.writeFileSync('$SETTINGS_FILE', JSON.stringify(settings, null, 2) + '\n');
"
        echo "  ✓ Hooks configuration added to settings.json"
        echo "  ✓ Hook state directory ready at $GEMINI_DIR/hooks/state"
    else
        echo "  ⚠ settings.json not found at $SETTINGS_FILE, skipping hooks configuration"
    fi
fi

echo ""
echo "✓ Installation complete!"
echo ""
echo "Installed to: $GEMINI_DIR"
echo "  /commands - Workflow commands (*.toml)"
echo "  /agents   - Sub-agents (*.md)"
echo "  /hooks    - BeforeAgent, AfterTool, and AfterAgent hooks"
echo ""
