#!/bin/bash
set -e

# GTD Framework - Gemini CLI Install Script
# Converts workflows to TOML commands with inlined skills
#
# Usage:
#   ./install-gemini.sh                    # Local install to ./.gemini/commands
#   ./install-gemini.sh --global           # Global install to ~/.gemini/commands

GLOBAL_FLAG="${1:-}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ "$GLOBAL_FLAG" = "--global" ]; then
    GEMINI_DIR="$HOME/.gemini"
else
    GEMINI_DIR="./.gemini"
fi

COMMANDS_DIR="$GEMINI_DIR/commands"
SKILLS_DIR="$GEMINI_DIR/skills"

echo "Installing GTD Framework for Gemini CLI..."
echo "  Commands: $COMMANDS_DIR"
echo "  Skills:   $SKILLS_DIR"

# Create target directories
mkdir -p "$COMMANDS_DIR"
mkdir -p "$SKILLS_DIR"

# Copy skills if they exist
if [ -d "$SCRIPT_DIR/skills" ]; then
    echo "Copying skills..."
    cp -r "$SCRIPT_DIR/skills/"* "$SKILLS_DIR/"
    echo "  ✓ Skills copied"
fi

# Function to convert workflow to TOML command
convert_workflow() {
    local workflow_file="$1"
    local output_file="$2"
    
    # Extract description from YAML frontmatter
    local description
    description=$(grep "^description:" "$workflow_file" | head -n 1 | sed 's/^description: *//' | tr -d '"'"'")
    
    # Extract body content (after YAML frontmatter)
    local body
    body=$(awk 'BEGIN{found=0} /^---$/{found++; if(found==2) next} found>=2{print}' "$workflow_file")
    
    # Escape triple quotes in body for TOML
    body=$(echo "$body" | sed 's/"""/\\"""/g')
    
    # Write TOML file
    cat > "$output_file" << EOF
description="$description"
prompt="""
$body
"""
EOF
    
    echo "  ✓ $(basename "$workflow_file" .md).toml"
}

# Convert all workflows
for workflow in "$SCRIPT_DIR/workflows/"*.md; do
    if [ -f "$workflow" ]; then
        filename=$(basename "$workflow" .md)
        convert_workflow "$workflow" "$COMMANDS_DIR/${filename}.toml"
    fi
done

echo ""
echo "✓ Installation complete!"
echo "  Commands installed: $(ls -1 "$COMMANDS_DIR"/*.toml 2>/dev/null | wc -l)"
