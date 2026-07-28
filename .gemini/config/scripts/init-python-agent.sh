#!/bin/bash
set -e

TARGET_FILE="GEMINI.md"

TMP_FILE=$(mktemp)

cat << 'EOF' > "$TMP_FILE"
# Python: project standard

- When managing packages or running scripts, use `uv` (`uv run`, `uv add`).
- When creating source directories, add `__init__.py`.
- When using `src/` structure, set `extraPaths = ["."]` for `pyright` in `pyproject.toml`.
- When writing Python, import at module top.

EOF

if [ -f "$TARGET_FILE" ]; then
    cat "$TARGET_FILE" >> "$TMP_FILE"
    echo "Injecting rules to top of existing $TARGET_FILE..."
else
    echo "Creating new $TARGET_FILE..."
fi

mv "$TMP_FILE" "$TARGET_FILE"

echo "✓ Python rules injected into $PWD/$TARGET_FILE"

