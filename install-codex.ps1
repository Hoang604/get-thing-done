<#
.SYNOPSIS
Codex CLI Install Script for Windows

.DESCRIPTION
Copies agents and skills from .codex\ to target location and merges config.toml.

.EXAMPLE
.\install-codex.ps1
Installs to the local .\.codex\ directory.

.EXAMPLE
.\install-codex.ps1 -Global
Installs to the global ~\.codex\ directory.
#>

param (
    [switch]$Global
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if ($Global) {
    # Resolve ~ to the user profile directory
    $CodexDir = Join-Path $env:USERPROFILE ".codex"
} else {
    $CodexDir = Join-Path $PWD ".codex"
}

$SourceCodex = Join-Path $ScriptDir ".codex"

Write-Host "Installing Codex Framework..."
Write-Host "  Target:  $CodexDir"
Write-Host ""

if (-not (Test-Path -Path $CodexDir)) {
    New-Item -ItemType Directory -Force -Path $CodexDir | Out-Null
}

$AgentsDir = Join-Path $CodexDir "agents"
$SkillsDir = Join-Path $CodexDir "skills"

New-Item -ItemType Directory -Force -Path $AgentsDir | Out-Null
New-Item -ItemType Directory -Force -Path $SkillsDir | Out-Null

$SourceAgents = Join-Path $SourceCodex "agents"
if (Test-Path -Path $SourceAgents) {
    Write-Host "Copying agents..."
    Copy-Item -Path "$SourceAgents\*" -Destination $AgentsDir -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  ✓ Agents copied"
}

$SourceSkills = Join-Path $SourceCodex "skills"
if (Test-Path -Path $SourceSkills) {
    Write-Host "Copying skills..."
    Copy-Item -Path "$SourceSkills\*" -Destination $SkillsDir -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  ✓ Skills copied"
}

$ConfigFile = Join-Path $CodexDir "config.toml"
Write-Host "Updating $ConfigFile..."

if (-not (Test-Path -Path $ConfigFile)) {
    $BaseConfig = @"
[features]
multi_agent = true

[agents]
max_threads = 6
max_depth = 1

[agents.test_strategist]
description = "Designs and injects a phase-specific TDD task into PLAN.md from XML query context."
config_file = "agents/test_strategist.toml"

[agents.review_plan]
description = "Pre-execution risk analyzer for plan quality, architecture, and safety concerns."
config_file = "agents/review_plan.toml"

[agents.security]
description = "Security auditor for vulnerability patterns and boundary validation in scoped code."
config_file = "agents/security.toml"

[agents.performance]
description = "Performance auditor for bottlenecks, scaling risks, and resource pressure in scoped code."
config_file = "agents/performance.toml"

[agents.tech_debt]
description = "Technical debt auditor for maintainability risks and refactoring priorities."
config_file = "agents/tech_debt.toml"
"@
    Set-Content -Path $ConfigFile -Value $BaseConfig -Encoding UTF8
    Write-Host "  ✓ Generated config.toml"
} else {
    # Call the external Python script to merge TOML
    $MergeScriptContent = Join-Path $ScriptDir "merge_codex_config.py"
    if (Test-Path -Path $MergeScriptContent) {
        python $MergeScriptContent $ConfigFile
    } else {
        Write-Host "  ⚠ merge_codex_config.py not found at $MergeScriptContent. Skipping config merge."
    }
}

Write-Host ""
Write-Host "✓ Installation complete!"
Write-Host ""
