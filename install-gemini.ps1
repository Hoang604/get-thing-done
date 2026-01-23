param(
    [switch]$Global
)

$ErrorActionPreference = "Stop"

$ScriptDir = $PSScriptRoot

if ($Global) {
    $TargetDir = Join-Path $env:USERPROFILE ".gemini\commands"
} else {
    $TargetDir = Join-Path (Get-Location).Path ".gemini\commands"
}

Write-Host "Installing GTD Framework for Gemini CLI..."
Write-Host "  Target: $TargetDir"

# Create target directory
New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null

Function Get-BodyContent([string]$fileContent) {
    # Splits by --- on a line by itself.
    # Returns the content after the second --- marker
    $parts = $fileContent -split '(?m)^---$'
    if ($parts.Count -ge 3) {
        # 0 is empty (before first ---)
        # 1 is frontmatter
        # 2 is body (and anything else if split limit wasn't used, but here we take the rest)
        # We need to join from index 2 onwards just in case, or just take the rest of the string
        # safely we can just use substring if we find the offsets, but split is easier.
        return ($parts[2..($parts.Count-1)] -join "---")
    }
    return $fileContent
}

# Convert all workflows
Get-ChildItem (Join-Path $ScriptDir "workflows\*.md") | ForEach-Object {
    $workflowFile = $_.FullName
    $filename = $_.BaseName
    $content = Get-Content $workflowFile -Raw
    
    # Extract description
    $desc = "GTD Workflow"
    if ($content -match '(?m)^description:\s*(.*)$') {
        $desc = $matches[1].Trim().Trim('"').Trim("'")
    }
    
    $body = Get-BodyContent $content
    $skillsToAdd = ""
    
    # Check for research skill
    if ($body -match '\{\{SKILLS_ROOT\}\}/research/SKILL.md') {
        $skillPath = Join-Path $ScriptDir "skills\research\SKILL.md"
        if (Test-Path $skillPath) {
            $skillContent = Get-Content $skillPath -Raw
            $skillBody = Get-BodyContent $skillContent
            $skillsToAdd += "`n`n---`n# Skill: research (The Archaeologist)`n$skillBody"
        }
        $body = $body -replace '> Read and apply `\{\{SKILLS_ROOT\}\}/research/SKILL.md`.*', '> Apply the research skill documented at the end of this prompt.'
    }
    
    # Check for code skill
    if ($body -match '\{\{SKILLS_ROOT\}\}/code/SKILL.md') {
        $skillPath = Join-Path $ScriptDir "skills\code\SKILL.md"
        if (Test-Path $skillPath) {
            $skillContent = Get-Content $skillPath -Raw
            $skillBody = Get-BodyContent $skillContent
            $skillsToAdd += "`n`n---`n# Skill: Code (The Runtime Realist)`n$skillBody"
        }
        $body = $body -replace '> Read and apply `\{\{SKILLS_ROOT\}\}/code/SKILL.md`.*', '> Apply the Code skill documented at the end of this prompt.'
    }
    
    # Escape triple quotes for TOML multi-line strings
    $body = $body.Replace('"""', '\"""')
    $skillsToAdd = $skillsToAdd.Replace('"""', '\"""')
    
    # Construct TOML
    # Note: Using `n for newlines in the string
    $toml = "description=""$desc""`nprompt=""""""`n$body$skillsToAdd`n"""""""
    
    $outFile = Join-Path $TargetDir "$filename.toml"
    Set-Content -Path $outFile -Value $toml -Encoding UTF8
    
    Write-Host "  ✓ $filename.toml"
}

Write-Host ""
Write-Host "✓ Installation complete!"
