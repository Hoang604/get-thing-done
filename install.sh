#!/bin/bash
set -e

# GTD Framework Install Script
# Usage:
#   ./install.sh <target_dir>           # Local install
#   ./install.sh <target_dir> --global  # Global install

if [ "$1" = "--global" ]; then
    TARGET_DIR="$HOME/.gemini/antigravity"
    GLOBAL_FLAG="--global"
else
    TARGET_DIR="${1:-$HOME/.gemini/antigravity}"
    GLOBAL_FLAG="${2:-}"
fi

# Expand tilde if present
if [[ "$TARGET_DIR" == "~"* ]]; then
    TARGET_DIR="${TARGET_DIR/#\~/$HOME}"
fi

if [ "$TARGET_DIR" = "$HOME/.gemini/antigravity" ]; then
    GLOBAL_FLAG="--global"
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ "$GLOBAL_FLAG" = "--global" ]; then
    # Global install: skills → skills, workflows → global_workflows
    SKILLS_DIR="$TARGET_DIR/skills"
    WORKFLOWS_DIR="$TARGET_DIR/global_workflows"
else
    # Local install: skills → skills, workflows → workflows
    SKILLS_DIR="$TARGET_DIR/skills"
    WORKFLOWS_DIR="$TARGET_DIR/workflows"
fi

echo "Installing GTD Framework..."
echo "  Skills:    $SKILLS_DIR"
echo "  Workflows: $WORKFLOWS_DIR"

# Create directories
mkdir -p "$SKILLS_DIR"
mkdir -p "$WORKFLOWS_DIR"

# Copy skills
cp -r "$SCRIPT_DIR/skills/"* "$SKILLS_DIR/"
skills_count=$(( $(find "$SCRIPT_DIR/skills" -type f 2>/dev/null | wc -l) ))

# Copy workflows
cp -r "$SCRIPT_DIR/workflows/"* "$WORKFLOWS_DIR/"
workflows_count=$(( $(find "$SCRIPT_DIR/workflows" -type f 2>/dev/null | wc -l) ))

# Copy GEMINI.md
if [ "$GLOBAL_FLAG" = "--global" ]; then
    mkdir -p "$HOME/.gemini"
    cp "$SCRIPT_DIR/GEMINI.md" "$HOME/.gemini/GEMINI.md"
    echo "  GEMINI.md: $HOME/.gemini/GEMINI.md"
else
    cp "$SCRIPT_DIR/GEMINI.md" "$TARGET_DIR/GEMINI.md"
    echo "  GEMINI.md: $TARGET_DIR/GEMINI.md"
fi
agents_count=1

total_copied=$((skills_count + workflows_count + agents_count))

echo ""
echo "✓ Installation complete! (Copied: $skills_count skills, $workflows_count workflows, $agents_count GEMINI.md, Total: $total_copied)"
