import sys
import re
import os

if len(sys.argv) < 2:
    print("Usage: python merge_codex_config.py <path_to_config.toml>")
    sys.exit(1)

config_path = sys.argv[1]

try:
    with open(config_path, 'r', encoding='utf-8') as f:
        config_content = f.read()
except FileNotFoundError:
    config_content = ''

print('  Merge processing for config.toml')

def ensure_key_in_section(content, section, key, line_to_add):
    # Check if section exists
    section_pattern = re.compile(rf'^\s*\[{re.escape(section)}\]\s*$', re.MULTILINE)
    if not section_pattern.search(content):
        # Add section at the end
        if content and not content.endswith('\n'):
            content += '\n'
        content += f'\n[{section}]\n{line_to_add}\n'
        return content

    # Section exists, check if key exists
    lines = content.split('\n')
    in_section = False
    section_start = -1
    section_end = len(lines)
    
    for i, line in enumerate(lines):
        if re.match(r'^\s*\[.*\]\s*$', line):
            if in_section:
                section_end = i
                break
            if line.strip() == f'[{section}]':
                in_section = True
                section_start = i
                
    # Search for key within section
    key_pattern = re.compile(rf'^\s*{re.escape(key)}\s*=.*$')
    key_exists = False
    for i in range(section_start + 1, section_end):
        if key_pattern.match(lines[i]):
            key_exists = True
            break
            
    if not key_exists:
        # Insert line before the end of the section
        # Move up from section_end to skip empty lines
        insert_idx = section_end
        while insert_idx > section_start + 1 and lines[insert_idx - 1].strip() == '':
            insert_idx -= 1
        lines.insert(insert_idx, line_to_add)
        return '\n'.join(lines)
        
    return content

new_content = config_content
new_content = ensure_key_in_section(new_content, 'features', 'multi_agent', 'multi_agent = true')
new_content = ensure_key_in_section(new_content, 'agents', 'max_threads', 'max_threads = 6')
new_content = ensure_key_in_section(new_content, 'agents', 'max_depth', 'max_depth = 1')

new_content = ensure_key_in_section(new_content, 'agents.test_strategist', 'description', 'description = "Designs and injects a phase-specific TDD task into PLAN.md from XML query context."')
new_content = ensure_key_in_section(new_content, 'agents.test_strategist', 'config_file', 'config_file = "agents/test_strategist.toml"')

new_content = ensure_key_in_section(new_content, 'agents.review_plan', 'description', 'description = "Pre-execution risk analyzer for plan quality, architecture, and safety concerns."')
new_content = ensure_key_in_section(new_content, 'agents.review_plan', 'config_file', 'config_file = "agents/review_plan.toml"')

new_content = ensure_key_in_section(new_content, 'agents.security', 'description', 'description = "Security auditor for vulnerability patterns and boundary validation in scoped code."')
new_content = ensure_key_in_section(new_content, 'agents.security', 'config_file', 'config_file = "agents/security.toml"')

new_content = ensure_key_in_section(new_content, 'agents.performance', 'description', 'description = "Performance auditor for bottlenecks, scaling risks, and resource pressure in scoped code."')
new_content = ensure_key_in_section(new_content, 'agents.performance', 'config_file', 'config_file = "agents/performance.toml"')

new_content = ensure_key_in_section(new_content, 'agents.tech_debt', 'description', 'description = "Technical debt auditor for maintainability risks and refactoring priorities."')
new_content = ensure_key_in_section(new_content, 'agents.tech_debt', 'config_file', 'config_file = "agents/tech_debt.toml"')

if new_content != config_content:
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("  ✓ Updated config.toml with missing keys")
else:
    print("  ✓ config.toml is already up to date")
