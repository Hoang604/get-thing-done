#!/bin/bash
set -e

# GTD Framework Install Script
# Usage:
#   ./install.sh <target_dir>           # Local install
#   ./install.sh <target_dir> --global  # Global install

TARGET_DIR="${1:-}"
GLOBAL_FLAG="${2:-}"

if [ -z "$TARGET_DIR" ]; then
    echo "Usage: ./install.sh <target_dir> [--global]"
    echo ""
    echo "Examples:"
    echo "  ./install.sh ./.agent              # Local project install"
    echo "  ./install.sh ~/.gemini/antigravity --global  # Global install"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ "$GLOBAL_FLAG" = "--global" ]; then
    # Global install: skills → global_skills, workflows → global_workflows
    SKILLS_DIR="$TARGET_DIR/global_skills"
    WORKFLOWS_DIR="$TARGET_DIR/global_workflows"
    # Use absolute path for SKILLS_ROOT
    SKILLS_ROOT="$(cd "$TARGET_DIR" 2>/dev/null && pwd)/global_skills"
else
    # Local install: skills → skills, workflows → workflows
    SKILLS_DIR="$TARGET_DIR/skills"
    WORKFLOWS_DIR="$TARGET_DIR/workflows"
    # Use relative path for SKILLS_ROOT
    SKILLS_ROOT="$TARGET_DIR/skills"
fi

echo "Installing GTD Framework..."
echo "  Skills:    $SKILLS_DIR"
echo "  Workflows: $WORKFLOWS_DIR"
echo "  SKILLS_ROOT: $SKILLS_ROOT"

# Create directories
mkdir -p "$SKILLS_DIR"
mkdir -p "$WORKFLOWS_DIR"

# Copy skills
cp -r "$SCRIPT_DIR/skills/"* "$SKILLS_DIR/"

# Copy workflows and patch SKILLS_ROOT placeholder
for file in "$SCRIPT_DIR/workflows/"*.md; do
    filename=$(basename "$file")
    sed "s|{{SKILLS_ROOT}}|$SKILLS_ROOT|g" "$file" > "$WORKFLOWS_DIR/$filename"
done

echo ""
echo "✓ Installation complete!"
