#!/bin/bash

# Resolve workspace directory relative to this script
WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$WORKSPACE_DIR/.gemini/antigravity-cli/skills"
DEST_DIR="$WORKSPACE_DIR/.gemini/config/skills"

if [[ ! -d "$SRC_DIR" ]]; then
    echo "Error: Source skills directory not found at $SRC_DIR"
    exit 1
fi

mkdir -p "$DEST_DIR"

echo "Syncing $SRC_DIR to $DEST_DIR..."

cp -rf "$SRC_DIR/." "$DEST_DIR/"

echo "Done."

