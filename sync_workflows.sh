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

# 3. Sync OpenCode subagents: .gemini/antigravity-cli/agents -> .agents/opencode/agents
#    Converts Gemini agent frontmatter to OpenCode V2 (mode + permissions); bodies unchanged.
DEST_AGENTS_OPENCODE="$WORKSPACE_DIR/.agents/opencode/agents"

if [[ -d "$SRC_AGENTS" ]]; then
    mkdir -p "$DEST_AGENTS_OPENCODE"
    echo "Syncing agents: $SRC_AGENTS -> $DEST_AGENTS_OPENCODE (OpenCode V2 frontmatter)..."
    rm -rf "$DEST_AGENTS_OPENCODE"/*
    python3 - "$SRC_AGENTS" "$DEST_AGENTS_OPENCODE" <<'PYEOF'
import json
import sys
from pathlib import Path

src_dir = Path(sys.argv[1])
dst_dir = Path(sys.argv[2])

# Gemini tool -> OpenCode V2 permission allows. read_file needs the discovery
# companions glob+grep; write_file targets <appDataDir>/brain reports outside
# the workspace, hence external_directory.
TOOL_ALLOWS = {
    "read_file": ("read", "glob", "grep"),
    "grep_search": ("grep",),
    "run_command": ("shell",),
    "write_file": ("edit", "external_directory"),
    "edit_file": ("edit", "external_directory"),
}
ALLOW_ORDER = ("read", "glob", "grep", "shell", "edit", "external_directory")
REQUIRED_KEYS = ("name", "description", "tools", "subagent", "mainAgent")
SCALAR_EXPECTED = {
    "subagent": ("true", "only subagent: true converts"),
    "mainAgent": ("false", "only mainAgent: false converts"),
    "model": ("inherit", "only model: inherit converts; V2 subagents inherit the parent model when model is unset"),
    "commandExecutionPolicy": ("sandbox", "only commandExecutionPolicy: sandbox converts; V2 has no equivalent field"),
}


def convert(path: Path) -> str:
    lines = path.read_text(encoding="utf-8").split("\n")
    if not lines or lines[0].strip() != "---":
        raise ValueError("frontmatter must open with ---")
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        raise ValueError("frontmatter must close with ---")

    description: str | None = None
    tools: list[str] = []
    seen: set[str] = set()
    list_key: str | None = None
    for line in lines[1:end]:
        if not line.strip():
            continue
        stripped = line.lstrip()
        if stripped.startswith("- "):
            if list_key != "tools":
                raise ValueError(f"list item outside tools: {stripped!r}")
            tools.append(stripped[2:].strip())
            continue
        key, sep, value = line.partition(":")
        if not sep:
            raise ValueError(f"malformed frontmatter line: {line.strip()!r}")
        key, value = key.strip(), value.strip()
        list_key = None
        seen.add(key)
        if key == "name":
            if value != path.stem:
                raise ValueError(f"name {value!r} does not match filename stem {path.stem!r}")
        elif key == "description":
            if not value:
                raise ValueError("empty description")
            description = value
        elif key == "tools":
            if value:
                raise ValueError("tools must be a list")
            list_key = "tools"
        elif key in SCALAR_EXPECTED:
            expected, reason = SCALAR_EXPECTED[key]
            if value != expected:
                raise ValueError(f"{key}={value!r}: {reason}")
        else:
            raise ValueError(f"unknown frontmatter key: {key!r}")

    missing = [key for key in REQUIRED_KEYS if key not in seen]
    if missing:
        raise ValueError(f"missing required keys: {', '.join(missing)}")
    if not tools:
        raise ValueError("empty tools list")
    unknown_tools = [tool for tool in tools if tool not in TOOL_ALLOWS]
    if unknown_tools:
        raise ValueError(f"unknown tools: {', '.join(unknown_tools)}")

    allows = {action for tool in tools for action in TOOL_ALLOWS[tool]}
    frontmatter = [
        f"description: {json.dumps(description, ensure_ascii=False)}",
        "mode: subagent",
        "permissions:",
        '  - action: "*"',
        '    resource: "*"',
        "    effect: deny",
    ]
    for action in ALLOW_ORDER:
        if action in allows:
            frontmatter += [
                f"  - action: {action}",
                '    resource: "*"',
                "    effect: allow",
            ]
    body = "\n".join(lines[end + 1 :])
    return "---\n" + "\n".join(frontmatter) + "\n---\n" + body


errors: list[str] = []
converted = 0
for agent_path in sorted(src_dir.glob("*.md")):
    try:
        (dst_dir / agent_path.name).write_text(convert(agent_path), encoding="utf-8")
        converted += 1
    except ValueError as error:
        errors.append(f"{agent_path.name}: {error}")

if errors:
    for error in errors:
        print(f"  error: {error}", file=sys.stderr)
    sys.exit(1)
print(f"    Converted {converted} agents")
PYEOF
fi

# 4. Sync shared instruction blocks: .gemini/GEMINI.md -> .agents/AGENTS.md
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
    "challenge_response",
    "type_safety_policy",
    "engineering_policy",
    "security_policy",
    "runtime_policy",
    "command_execution",
]

blocks: list[str] = []
for tag in TAGS:
    m = re.search(rf"(?m)^<{tag}>[ \t]*\n.*?\n^</{tag}>[ \t]*$", text, flags=re.DOTALL)
    if m:
        blocks.append(m.group(0))

dst_path.parent.mkdir(parents=True, exist_ok=True)
dst_path.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
PYEOF
fi

# 5. Sync Plugins: .gemini/config/plugins -> .agents/plugins
SRC_PLUGINS="$WORKSPACE_DIR/.gemini/config/plugins"
DEST_PLUGINS_AGENTS="$WORKSPACE_DIR/.agents/plugins"

if [[ -d "$SRC_PLUGINS" ]]; then
    mkdir -p "$DEST_PLUGINS_AGENTS"
    echo "Syncing plugins: $SRC_PLUGINS -> $DEST_PLUGINS_AGENTS..."
    rm -rf "$DEST_PLUGINS_AGENTS"/*
    cp -rf "$SRC_PLUGINS/." "$DEST_PLUGINS_AGENTS/"
fi

echo "Done."

