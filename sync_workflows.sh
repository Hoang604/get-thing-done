#!/bin/bash

# Resolve workspace directory relative to this script
WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="$WORKSPACE_DIR/.gemini/skills"
WORKFLOWS_DIR="$WORKSPACE_DIR/.gemini/config/global_workflows"

if [[ ! -d "$WORKFLOWS_DIR" ]]; then
    echo "Error: Workflows directory not found at $WORKFLOWS_DIR"
    exit 1
fi

echo "Syncing skills to existing workflows..."

for workflow_file in "$WORKFLOWS_DIR"/*.md; do
    # Skip if no md files found
    [[ -f "$workflow_file" ]] || continue

    filename=$(basename "$workflow_file")
    skill_name="${filename%.md}"
    skill_path="$SKILLS_DIR/$skill_name/SKILL.md"
    
    if [[ -f "$skill_path" ]]; then
        cp -f "$skill_path" "$workflow_file"
        echo "Updated: $filename"
    else
        echo "Warning: SKILL.md not found for $skill_name"
    fi
done

echo "Done."
