$ErrorActionPreference = "Stop"

# GTD Framework Install Script (Always Global)
# Copies everything in .gemini/ to ~/.gemini/

$ScriptDir = $PSScriptRoot
$SrcDir = Join-Path $ScriptDir ".gemini"
$TargetDir = Join-Path $HOME ".gemini"

if (-not (Test-Path $SrcDir -PathType Container)) {
    Write-Error "Source directory $SrcDir not found."
    exit 1
}

Write-Host "Installing GTD Framework (Global)..."
Write-Host "  Source: $SrcDir"
Write-Host "  Target: $TargetDir"

# Count source files and directories
$Files = Get-ChildItem -Path $SrcDir -Recurse | Where-Object { -not $_.PSIsContainer }
$FileCount = @($Files).Count
$Dirs = Get-ChildItem -Path $SrcDir -Recurse | Where-Object { $_.PSIsContainer }
$DirCount = @($Dirs).Count

# Ensure target directory exists
New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null

# Copy everything
Copy-Item -Path (Join-Path $SrcDir "*") -Destination $TargetDir -Recurse -Force

Write-Host ""
Write-Host "✓ Installation complete! (Copied: $FileCount files, $DirCount directories)"

