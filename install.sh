#!/bin/bash
set -e

# GTD Framework Install Script (Always Global)
# Copies everything in .gemini/ to ~/.gemini/ and .agents/ to ~/.agents/

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_DIR="$SCRIPT_DIR/.gemini"
TARGET_DIR="$HOME/.gemini"
SRC_AGENTS_DIR="$SCRIPT_DIR/.agents"
TARGET_AGENTS_DIR="$HOME/.agents"

if [ ! -d "$SRC_DIR" ]; then
    echo "Error: Source directory $SRC_DIR not found." >&2
    exit 1
fi

echo "Installing GTD Framework (Global)..."
echo "  Source (.gemini): $SRC_DIR"
echo "  Target (.gemini): $TARGET_DIR"

# Count source files and directories
file_count=$(find "$SRC_DIR" -type f | wc -l)
dir_count=$(find "$SRC_DIR" -mindepth 1 -type d | wc -l)

# Create target directory
mkdir -p "$TARGET_DIR"

# Copy all contents including hidden files, maintaining structure
cp -r "$SRC_DIR/." "$TARGET_DIR/"

# Copy .agents directory if present
if [ -d "$SRC_AGENTS_DIR" ]; then
    echo "  Source (.agents): $SRC_AGENTS_DIR"
    echo "  Target (.agents): $TARGET_AGENTS_DIR"
    agents_file_count=$(find "$SRC_AGENTS_DIR" -type f | wc -l)
    agents_dir_count=$(find "$SRC_AGENTS_DIR" -mindepth 1 -type d | wc -l)
    mkdir -p "$TARGET_AGENTS_DIR"
    cp -r "$SRC_AGENTS_DIR/." "$TARGET_AGENTS_DIR/"
    file_count=$((file_count + agents_file_count))
    dir_count=$((dir_count + agents_dir_count))
fi

# Make scripts executable
chmod +x "$TARGET_DIR/antigravity-cli/statusline.sh"
chmod +x "$TARGET_DIR/config/scripts/track_turn.sh"
chmod +x "$TARGET_DIR/config/scripts/critical_instructions.sh"
chmod +x "$TARGET_DIR/config/scripts/init-python-agent.sh"
chmod +x "$TARGET_DIR/config/scripts/verify_recorder.py"
chmod +x "$TARGET_DIR/config/scripts/verify_injector.py"
chmod +x "$TARGET_DIR/config/scripts/conditional_tool_guard.py"

mkdir -p "$HOME/.local/bin"
ln -sf "$TARGET_DIR/config/scripts/init-python-agent.sh" "$HOME/.local/bin/init-python-agent"

# Configure statusLine in ~/.gemini/antigravity-cli/settings.json if not present
SETTINGS_FILE="$TARGET_DIR/antigravity-cli/settings.json"
python3 - <<EOF
import os
import re

settings_file = os.path.expanduser("$SETTINGS_FILE")
os.makedirs(os.path.dirname(settings_file), exist_ok=True)

status_block_comma = '''  "statusLine": {
    "type": "command",
    "command": "~/.gemini/antigravity-cli/statusline.sh"
  },
'''

status_block_single = '''  "statusLine": {
    "type": "command",
    "command": "~/.gemini/antigravity-cli/statusline.sh"
  }
'''

if not os.path.exists(settings_file):
    with open(settings_file, "w", encoding="utf-8") as f:
        f.write("{\n" + status_block_single + "}\n")
else:
    with open(settings_file, "r", encoding="utf-8") as f:
        content = f.read()

    if not re.search(r'"statusLine"\s*:', content):
        first_brace = content.find("{")
        if first_brace == -1:
            new_content = "{\n" + status_block_single + "}\n"
        else:
            rest = content[first_brace + 1:].strip()
            if rest == "" or rest == "}":
                new_content = content[:first_brace + 1] + "\n" + status_block_single + "}\n"
            else:
                new_content = content[:first_brace + 1] + "\n" + status_block_comma + content[first_brace + 1:]
        with open(settings_file, "w", encoding="utf-8") as f:
            f.write(new_content)
EOF

echo ""
echo "✓ Installation complete! (Copied: $file_count files, $dir_count directories)"
