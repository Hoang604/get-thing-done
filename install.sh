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

mkdir -p "$HOME/.local/bin"
ln -sf "$TARGET_DIR/config/scripts/init-python-agent.sh" "$HOME/.local/bin/init-python-agent"

echo ""
echo "✓ Installation complete! (Copied: $file_count files, $dir_count directories)"
