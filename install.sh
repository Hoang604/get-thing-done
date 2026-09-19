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
chmod +x "$TARGET_DIR/config/scripts/view_file_guard.py"

mkdir -p "$HOME/.local/bin"
ln -sf "$TARGET_DIR/config/scripts/init-python-agent.sh" "$HOME/.local/bin/init-python-agent"

# Merge opencode config into ~/.config/opencode/opencode.json
OPENCODE_CFG_SRC="$TARGET_AGENTS_DIR/opencode.json"
OPENCODE_CFG_DIR="$HOME/.config/opencode"
OPENCODE_CFG_DST="$OPENCODE_CFG_DIR/opencode.json"

if [ -f "$OPENCODE_CFG_SRC" ]; then
    echo "  Source (opencode config): $OPENCODE_CFG_SRC"
    echo "  Target (opencode config): $OPENCODE_CFG_DST"
    mkdir -p "$OPENCODE_CFG_DIR"
    python3 - "$OPENCODE_CFG_SRC" "$OPENCODE_CFG_DST" <<'PYEOF'
import json
import os
import shutil
import sys

src, dst = sys.argv[1], sys.argv[2]

with open(src, encoding="utf-8") as f:
    incoming = json.load(f)

existing = {}
if os.path.exists(dst):
    try:
        with open(dst, encoding="utf-8") as f:
            existing = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError):
        backup = dst + ".bak"
        shutil.copy2(dst, backup)
        print(f"    Existing config not valid JSON, backed up to {backup}")

def deep_merge(base, override):
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result

merged = deep_merge(existing, incoming)
with open(dst, "w", encoding="utf-8") as f:
    json.dump(merged, f, indent=2, ensure_ascii=False)
    f.write("\n")
PYEOF
fi

# Install opencode plugins to ~/.config/opencode/plugins (auto-loaded, no config entry needed)
OPENCODE_PLUGINS_SRC="$TARGET_AGENTS_DIR/opencode/plugins"
OPENCODE_PLUGINS_DST="$HOME/.config/opencode/plugins"

if [ -d "$OPENCODE_PLUGINS_SRC" ]; then
    echo "  Source (opencode plugins): $OPENCODE_PLUGINS_SRC"
    echo "  Target (opencode plugins): $OPENCODE_PLUGINS_DST"
    mkdir -p "$OPENCODE_PLUGINS_DST"
    for f in "$OPENCODE_PLUGINS_SRC"/*.ts; do
        [ -e "$f" ] || continue
        cp "$f" "$OPENCODE_PLUGINS_DST/"
    done
fi

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
