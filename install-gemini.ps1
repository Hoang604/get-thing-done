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

Write-Host ""
Write-Host "✓ Installation complete!"
Write-Host ""
Write-Host "Installed to: $GeminiDir"
Write-Host "  /commands - Workflow commands (*.toml)"
Write-Host "  /agents   - Sub-agents (*.md)"
Write-Host "  /skills   - Research skills"
