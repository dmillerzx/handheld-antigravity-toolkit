<#
.SYNOPSIS
    Copies text or markdown to the Windows clipboard with strict flush-left formatting.
.DESCRIPTION
    Strips uniform leading indentation and whitespace corruption from text or markdown files,
    then copies the sanitized content directly to the Windows clipboard using Set-Clipboard.
.PARAMETER FilePath
    Path to markdown or text file to stage.
.PARAMETER Text
    Direct string to stage into the clipboard.
.EXAMPLE
    .\scripts\stage_clipboard.ps1 -FilePath "notes/comment.md"
.EXAMPLE
    .\scripts\stage_clipboard.ps1 -Text "### Header`n* Item 1"
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$false, Position=0)]
    [string]$FilePath,
    [Parameter(Mandatory=$false)]
    [string]$Text
)

if ($FilePath) {
    if (-not (Test-Path $FilePath)) {
        Write-Error "File not found: $FilePath"
        exit 1
    }
    $content = Get-Content -Path $FilePath -Raw -Encoding utf8
} elseif ($Text) {
    $content = $Text
} else {
    Write-Error "Must provide -FilePath or -Text parameter."
    exit 1
}

# Normalize line endings
$lines = $content -split "`r?`n"

# Calculate minimum non-empty line indentation
$minIndent = 9999
foreach ($line in $lines) {
    if ($line.Trim().Length -gt 0) {
        $indent = if ($line -match '^(\s*)') { $matches[1].Length } else { 0 }
        if ($indent -lt $minIndent) {
            $minIndent = $indent
        }
    }
}

# Strip uniform leading indentation if present
if ($minIndent -gt 0 -and $minIndent -ne 9999) {
    $lines = $lines | ForEach-Object {
        if ($_.Length -ge $minIndent) {
            $_.Substring($minIndent)
        } else {
            $_
        }
    }
    $content = $lines -join "`r`n"
}

# Stage to Windows clipboard
$content | Set-Clipboard
$lineCount = ($content -split "`r?`n").Count
Write-Host "[OK] Staged $lineCount lines directly into Windows clipboard (flush-left, 0-indent)." -ForegroundColor Green
