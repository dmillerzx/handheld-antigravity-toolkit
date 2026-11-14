<#
.SYNOPSIS
    Launches Google Chrome with Chrome DevTools Protocol (CDP) remote debugging enabled.

.DESCRIPTION
    Starts Google Chrome bound to a local debugging port (default 9222) and a persistent
    profile directory so cookies, logins, and session state are preserved across runs.

.PARAMETER Port
    The remote debugging port to listen on. Defaults to 9222.

.PARAMETER UserDataDir
    Directory to store the Chrome profile. Defaults to AntigravityDebug in local app data.

.PARAMETER Url
    Initial URL to navigate to. Defaults to about:blank.
#>

param(
    [int]$Port = 9222,
    [string]$UserDataDir = "$env:LOCALAPPDATA\Google\Chrome\User Data\AntigravityDebug",
    [string]$Url = "about:blank"
)

$chromePath = "$env:ProgramFiles\Google\Chrome\Application\chrome.exe"
if (-not (Test-Path $chromePath)) {
    $chromePath = "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe"
}
if (-not (Test-Path $chromePath)) {
    $chromePath = "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
}

if (-not (Test-Path $chromePath)) {
    Write-Error "Google Chrome executable not found in standard installation directories."
    exit 1
}

if (-not (Test-Path $UserDataDir)) {
    New-Item -ItemType Directory -Path $UserDataDir -Force | Out-Null
}

Write-Host "Starting Google Chrome with remote debugging on port $Port..."
Write-Host "Profile: $UserDataDir"

Start-Process $chromePath -ArgumentList @(
    "--remote-debugging-port=$Port",
    "--user-data-dir=$UserDataDir",
    "--no-first-run",
    "--no-default-browser-check",
    $Url
)

Start-Sleep -Seconds 2

try {
    $version = Invoke-RestMethod -Uri "http://localhost:$Port/json/version" -TimeoutSec 3
    Write-Host "Chrome CDP active: $($version.'Browser')" -ForegroundColor Green
    Write-Host "WebSocket Debugger URL: $($version.webSocketDebuggerUrl)"
} catch {
    Write-Warning "Could not connect to http://localhost:$Port/json/version. Ensure no conflicting Chrome instance is running."
}
