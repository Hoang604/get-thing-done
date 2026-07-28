#!/bin/bash
set -e

# GTD Framework Install Script (Always Global)
# Copies everything in .gemini/ to ~/.gemini/

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_DIR="$SCRIPT_DIR/.gemini"
TARGET_DIR="$HOME/.gemini"

if [ ! -d "$SRC_DIR" ]; then
    echo "Error: Source directory $SRC_DIR not found." >&2
    exit 1
fi

echo "Installing GTD Framework (Global)..."
echo "  Source: $SRC_DIR"
echo "  Target: $TARGET_DIR"

# Count source files and directories
file_count=$(find "$SRC_DIR" -type f | wc -l)
dir_count=$(find "$SRC_DIR" -mindepth 1 -type d | wc -l)

# Create target directory
mkdir -p "$TARGET_DIR"

# Copy all contents including hidden files, maintaining structure
cp -r "$SRC_DIR/." "$TARGET_DIR/"

# Make scripts executable
chmod +x "$TARGET_DIR/antigravity-cli/statusline.sh"
chmod +x "$TARGET_DIR/config/scripts/track_turn.sh"
chmod +x "$TARGET_DIR/config/scripts/init-python-agent.sh"

mkdir -p "$HOME/.local/bin"
ln -sf "$TARGET_DIR/config/scripts/init-python-agent.sh" "$HOME/.local/bin/init-python-agent"

echo ""
echo "✓ Installation complete! (Copied: $file_count files, $dir_count directories)"
