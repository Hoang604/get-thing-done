#!/bin/bash
# .gtd/scripts/generate-index.sh

TARGET_DIR=$1
if [ -z "$TARGET_DIR" ]; then
  echo "Usage: $0 <directory>"
  exit 1
fi

INDEX_FILE="$TARGET_DIR/index.md"
# Ensure the directory exists
mkdir -p "$TARGET_DIR"

# Get relative path for the footer
REL_PATH=$(echo "$INDEX_FILE" | sed 's|^\./||')

# Start with an empty file
> "$INDEX_FILE"

# Find all .md files, sort them to be deterministic
# We use -maxdepth 1 to only get files in the current directory
# We exclude index.md
find "$TARGET_DIR" -maxdepth 1 -name "*.md" ! -name "index.md" | sort | while read -r file; do
  filename=$(basename "$file")
  echo "<!-- Imported from: ./$filename -->" >> "$INDEX_FILE"
  cat "$file" >> "$INDEX_FILE"
  # Ensure we are on a new line for the end tag
  if [ -n "$(tail -c1 "$INDEX_FILE")" ]; then
    echo "" >> "$INDEX_FILE"
  fi
  echo "<!-- End of import from: ./$filename -->" >> "$INDEX_FILE"
done