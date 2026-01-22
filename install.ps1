param(
    [string]$TargetDir,
    [switch]$Global
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrEmpty($TargetDir)) {
    Write-Host "Usage: .\install.ps1 <target_dir> [-Global]"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\install.ps1 .\.agent              # Local project install"
    Write-Host "  .\install.ps1 $env:USERPROFILE\.gemini\antigravity -Global  # Global install"
    exit 1
}

$ScriptDir = $PSScriptRoot

if ($Global) {
    # Global install: skills -> global_skills, workflows -> global_workflows
    $SkillsDir = Join-Path $TargetDir "global_skills"
    $WorkflowsDir = Join-Path $TargetDir "global_workflows"
    # Use absolute path for SKILLS_ROOT, convert to forward slashes for markdown compatibility
    $AbsTarget = (Resolve-Path $TargetDir -ErrorAction SilentlyContinue).Path
    if (-not $AbsTarget) {
        # Path might not exist yet, assume it's absolute if global
        $AbsTarget = $TargetDir
    }
    $SkillsRoot = Join-Path $AbsTarget "global_skills"
} else {
    # Local install: skills -> skills, workflows -> workflows
    $SkillsDir = Join-Path $TargetDir "skills"
    $WorkflowsDir = Join-Path $TargetDir "workflows"
    # Use relative path for SKILLS_ROOT
    $SkillsRoot = "$TargetDir/skills"
}

# Ensure forward slashes for markdown
$SkillsRoot = $SkillsRoot -replace '\\', '/'

Write-Host "Installing GTD Framework..."
Write-Host "  Skills:    $SkillsDir"
Write-Host "  Workflows: $WorkflowsDir"
Write-Host "  SKILLS_ROOT: $SkillsRoot"

# Create directories
New-Item -ItemType Directory -Force -Path $SkillsDir | Out-Null
New-Item -ItemType Directory -Force -Path $WorkflowsDir | Out-Null

# Copy skills
Copy-Item -Recurse -Force (Join-Path $ScriptDir "skills\*") $SkillsDir

# Copy workflows and patch SKILLS_ROOT placeholder
Get-ChildItem (Join-Path $ScriptDir "workflows\*.md") | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    $newContent = $content.Replace('{{SKILLS_ROOT}}', $SkillsRoot)
    $dest = Join-Path $WorkflowsDir $_.Name
    Set-Content -Path $dest -Value $newContent -NoNewline
}

Write-Host ""
Write-Host "✓ Installation complete!"
