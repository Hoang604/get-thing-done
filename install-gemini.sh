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
    TARGET_DIR="$HOME/.gemini/commands"
else
    TARGET_DIR="./.gemini/commands"
fi

echo "Installing GTD Framework for Gemini CLI..."
echo "  Target: $TARGET_DIR"

# Create target directory
mkdir -p "$TARGET_DIR"

# Function to read skill file content (after YAML frontmatter)
read_skill() {
    local skill_path="$1"
    awk 'BEGIN{found=0} /^---$/{found++; if(found==2) next} found>=2{print}' "$skill_path"
}

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
    
    # Collect skills to inline
    local skills_to_add=""
    
    # Check for investigate skill
    if echo "$body" | grep -q "{{SKILLS_ROOT}}/investigate/SKILL.md"; then
        if [ -f "$SCRIPT_DIR/skills/investigate/SKILL.md" ]; then
            skills_to_add="$skills_to_add

---
# Skill: Investigate (The Archaeologist)
$(read_skill "$SCRIPT_DIR/skills/investigate/SKILL.md")"
        fi
        # Remove the reference line
        body=$(echo "$body" | sed 's|> Read and apply `{{SKILLS_ROOT}}/investigate/SKILL.md`.*|> Apply the Investigate skill documented at the end of this prompt.|g')
    fi
    
    # Check for code skill
    if echo "$body" | grep -q "{{SKILLS_ROOT}}/code/SKILL.md"; then
        if [ -f "$SCRIPT_DIR/skills/code/SKILL.md" ]; then
            skills_to_add="$skills_to_add

---
# Skill: Code (The Runtime Realist)
$(read_skill "$SCRIPT_DIR/skills/code/SKILL.md")"
        fi
        # Remove the reference line
        body=$(echo "$body" | sed 's|> Read and apply `{{SKILLS_ROOT}}/code/SKILL.md`.*|> Apply the Code skill documented at the end of this prompt.|g')
    fi
    
    # Escape triple quotes in body for TOML
    body=$(echo "$body" | sed 's/"""/\\"""/g')
    skills_to_add=$(echo "$skills_to_add" | sed 's/"""/\\"""/g')
    
    # Write TOML file
    cat > "$output_file" << EOF
description="$description"
prompt="""
$body
$skills_to_add
"""
EOF
    
    echo "  ✓ $(basename "$workflow_file" .md).toml"
}

# Convert all workflows
for workflow in "$SCRIPT_DIR/workflows/"*.md; do
    if [ -f "$workflow" ]; then
        filename=$(basename "$workflow" .md)
        convert_workflow "$workflow" "$TARGET_DIR/${filename}.toml"
    fi
done

echo ""
echo "✓ Installation complete!"
echo "  Commands installed: $(ls -1 "$TARGET_DIR"/*.toml 2>/dev/null | wc -l)"
