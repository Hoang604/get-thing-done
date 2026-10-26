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
    rm -rf "$DEST_SKILLS_CFG"/* "$DEST_SKILLS_AGENTS"/*
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
    rm -rf "$DEST_AGENTS_CFG"/* "$DEST_AGENTS_AGENTS"/*
    cp -rf "$SRC_AGENTS/." "$DEST_AGENTS_CFG/"
    cp -rf "$SRC_AGENTS/." "$DEST_AGENTS_AGENTS/"
fi

# 3. Sync shared instruction blocks: .gemini/GEMINI.md -> .agents/AGENTS.md
SRC_GEMINI_MD="$WORKSPACE_DIR/.gemini/GEMINI.md"
DEST_AGENTS_MD="$WORKSPACE_DIR/.agents/AGENTS.md"

if [[ -f "$SRC_GEMINI_MD" ]]; then
    echo "Syncing instructions: $SRC_GEMINI_MD -> $DEST_AGENTS_MD..."
    python3 - "$SRC_GEMINI_MD" "$DEST_AGENTS_MD" <<'PYEOF'
import re
import sys
from pathlib import Path

src_path = Path(sys.argv[1])
dst_path = Path(sys.argv[2])
text = src_path.read_text(encoding="utf-8")

TAGS = [
    "harness_injection",
    "communication_model",
    "reasoning_from_principles",
    "challenge_response",
    "type_safety_policy",
    "invariant_policy",
    "engineering_policy",
]

blocks: list[str] = []
for tag in TAGS:
    m = re.search(rf"<{tag}>.*?</{tag}>", text, flags=re.DOTALL)
    if m:
        blocks.append(m.group(0))

dst_path.parent.mkdir(parents=True, exist_ok=True)
dst_path.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
PYEOF
fi

echo "Done."

