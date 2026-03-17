import sys
import re
import os

if len(sys.argv) < 2:
    print(
        "Usage: python merge_codex_config.py <path_to_config.toml> [path_to_source_config.toml]")
    sys.exit(1)

config_path = sys.argv[1]
source_config_path = sys.argv[2] if len(sys.argv) >= 3 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    ".codex",
    "config.toml",
)

try:
    with open(config_path, 'r', encoding='utf-8') as f:
        config_content = f.read()
except FileNotFoundError:
    config_content = ''

try:
    with open(source_config_path, 'r', encoding='utf-8') as f:
        source_content = f.read()
except FileNotFoundError:
    print(f"Error: source config not found at {source_config_path}")
    sys.exit(1)

print('  Merge processing for config.toml')

SECTION_PATTERN = re.compile(
    r'(?ms)^\[(?P<name>[^\]]+)\]\s*\n(?P<body>.*?)(?=^\[|\Z)')
KEY_PATTERN = re.compile(r'^(\s*)([A-Za-z0-9_-]+)(\s*=\s*.*)$')


def parse_config(content):
    first_section = re.search(r'(?m)^\[', content)
    global_body = content[:first_section.start()] if first_section else content

    sections = {}
    order = []
    for match in SECTION_PATTERN.finditer(content):
        name = match.group('name').strip()
        body = match.group('body')
        sections[name] = body
        order.append(name)
    return global_body, sections, order


def merge_section_body(target_body, source_body):
    target_lines = target_body.splitlines()
    source_lines = source_body.splitlines()
    key_positions = {}

    for idx, line in enumerate(target_lines):
        match = KEY_PATTERN.match(line)
        if match:
            key_positions[match.group(2)] = idx

    for line in source_lines:
        match = KEY_PATTERN.match(line)
        if not match:
            if line.strip() and line not in target_lines:
                target_lines.append(line)
            continue

        key = match.group(2)
        if key in key_positions:
            target_lines[key_positions[key]] = line
        else:
            target_lines.append(line)

    merged = "\n".join(target_lines).rstrip()
    return f"{merged}\n" if merged else ""


target_global, target_sections, target_order = parse_config(config_content)
source_global, source_sections, source_order = parse_config(source_content)

new_global = merge_section_body(target_global, source_global)

new_sections = dict(target_sections)
new_order = list(target_order)

for section_name in source_order:
    source_body = source_sections[section_name]
    if section_name in ("features", "agents"):
        merged_body = merge_section_body(
            target_sections.get(section_name, ""), source_body)
    elif section_name.startswith("agents."):
        merged_body = source_body.rstrip() + "\n"
    else:
        continue

    new_sections[section_name] = merged_body
    if section_name not in new_order:
        new_order.append(section_name)

rendered_parts = []

global_block = new_global.rstrip()
if global_block:
    rendered_parts.append(global_block + "\n")

for section_name in new_order:
    body = new_sections[section_name].rstrip()
    rendered_parts.append(f"[{section_name}]\n{body}\n")

new_content = "\n".join(rendered_parts).rstrip() + \
    "\n" if rendered_parts else ""

if new_content != config_content:
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("  ✓ Updated config.toml from template")
else:
    print("  ✓ config.toml is already up to date")
