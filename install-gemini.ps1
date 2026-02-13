param(
    [switch]$Global
)

$ErrorActionPreference = "Stop"

$ScriptDir = $PSScriptRoot
$SourceGemini = Join-Path $ScriptDir ".gemini"

if ($Global) {
    $GeminiDir = Join-Path $env:USERPROFILE ".gemini"
} else {
    $GeminiDir = Join-Path (Get-Location).Path ".gemini"
}

Write-Host "Installing GTD Framework for Gemini CLI..."
Write-Host "  Source:  $SourceGemini"
Write-Host "  Target:  $GeminiDir"
Write-Host ""

# Check source exists
if (-not (Test-Path $SourceGemini)) {
    Write-Error "Error: Source .gemini directory not found at $SourceGemini"
    exit 1
}

# Create target directories
New-Item -ItemType Directory -Force -Path (Join-Path $GeminiDir "commands") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $GeminiDir "agents") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $GeminiDir "skills") | Out-Null

# Copy commands
$CommandsSource = Join-Path $SourceGemini "commands"
if (Test-Path $CommandsSource) {
    Write-Host "Copying commands..."
    Copy-Item -Path (Join-Path $CommandsSource "*") -Destination (Join-Path $GeminiDir "commands") -Recurse -Force
    $commandCount = (Get-ChildItem (Join-Path $GeminiDir "commands\*.toml")).Count
    Write-Host "  ✓ Commands: $commandCount files"
}

# Copy agents
$AgentsSource = Join-Path $SourceGemini "agents"
if (Test-Path $AgentsSource) {
    Write-Host "Copying agents..."
    Copy-Item -Path (Join-Path $AgentsSource "*") -Destination (Join-Path $GeminiDir "agents") -Recurse -Force
    $agentCount = (Get-ChildItem (Join-Path $GeminiDir "agents\*.md")).Count
    Write-Host "  ✓ Agents: $agentCount files"
}

# Copy skills
$SkillsSource = Join-Path $SourceGemini "skills"
if (Test-Path $SkillsSource) {
    Write-Host "Copying skills..."
    Copy-Item -Path (Join-Path $SkillsSource "*") -Destination (Join-Path $GeminiDir "skills") -Recurse -Force
    $skillCount = (Get-ChildItem (Join-Path $GeminiDir "skills") -Directory).Count
    Write-Host "  ✓ Skills: $skillCount directories"
}

# Copy hooks
$HooksSource = Join-Path $SourceGemini "hooks"
if (Test-Path $HooksSource) {
    Write-Host "Copying hooks..."
    New-Item -ItemType Directory -Force -Path (Join-Path $GeminiDir "hooks") | Out-Null
    Copy-Item -Path (Join-Path $HooksSource "*") -Destination (Join-Path $GeminiDir "hooks") -Recurse -Force
    $hookCount = (Get-ChildItem (Join-Path $GeminiDir "hooks\*.js")).Count
    Write-Host "  ✓ Hooks: $hookCount files"
}

# Copy GEMINI.md (thinking protocol)
$GeminiMdSource = Join-Path $ScriptDir "GEMINI.md"
if (Test-Path $GeminiMdSource) {
    if ($Global) {
        $GeminiMdTarget = Join-Path $env:USERPROFILE ".gemini\GEMINI.md"
    } else {
        $GeminiMdTarget = Join-Path (Get-Location).Path "GEMINI.md"
    }
    Write-Host "Copying GEMINI.md..."
    Copy-Item -Path $GeminiMdSource -Destination $GeminiMdTarget -Force
    Write-Host "  ✓ GEMINI.md → $GeminiMdTarget"
}

# Update settings.json with hooks configuration (only for global install)
if ($Global) {
    $SettingsFile = Join-Path $GeminiDir "settings.json"
    if (Test-Path $SettingsFile) {
        Write-Host "Updating settings.json with hooks configuration..."
        
        # Use node to merge hooks config, preserving existing hooks
        $NodeSettingsFile = $SettingsFile.Replace('\', '/')
        
        $nodeScript = @"
const fs = require('fs');
const settings = JSON.parse(fs.readFileSync('$NodeSettingsFile', 'utf8'));

const newHook = {
    type: 'command',
    command: 'node ~/.gemini/hooks/before.js',
    name: 'Rules',
    description: 'Add rules to prevent gemini do stupid thing',
    timeout: 5000
};

// Initialize hooks structure if not exists
if (!settings.hooks) {
    settings.hooks = {};
}
if (!settings.hooks.BeforeAgent) {
    settings.hooks.BeforeAgent = [];
}

// Find or create the hooks array entry
let hooksEntry = settings.hooks.BeforeAgent.find(e => e.hooks);
if (!hooksEntry) {
    hooksEntry = { hooks: [] };
    settings.hooks.BeforeAgent.push(hooksEntry);
}

// Check if this hook already exists (by name)
const existingIndex = hooksEntry.hooks.findIndex(h => h.name === newHook.name);
if (existingIndex >= 0) {
    hooksEntry.hooks[existingIndex] = newHook;
} else {
    hooksEntry.hooks.push(newHook);
}

fs.writeFileSync('$NodeSettingsFile', JSON.stringify(settings, null, 2) + '\n');
"@
        node -e $nodeScript
        Write-Host "  ✓ Hooks configuration added to settings.json"
    } else {
        Write-Host "  ⚠ settings.json not found at $SettingsFile, skipping hooks configuration"
    }
}

Write-Host ""
Write-Host "✓ Installation complete!"
Write-Host ""
Write-Host "Installed to: $GeminiDir"
Write-Host "  /commands - Workflow commands (*.toml)"
Write-Host "  /agents   - Sub-agents (*.md)"
Write-Host "  /hooks    - BeforeAgent hook"
