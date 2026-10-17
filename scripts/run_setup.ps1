<#
.SYNOPSIS
    Convenience wrapper to run setup_rp5.py with PATH resolution.
.DESCRIPTION
    Canonical RP5 storage layout enforced by setup_rp5.py (do not create variants):
      Internal : /sdcard/bios
      MicroSD  : /storage/<SD_ID>/{bios, ROMs, ES-DE}
#>

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$WorkspaceRoot = Split-Path -Parent $ScriptDir

# Ensure platform-tools is available in current process PATH
$PlatformTools = Join-Path $WorkspaceRoot "platform-tools"
if ((Test-Path $PlatformTools) -and ($env:Path -notlike "*$PlatformTools*")) {
    $env:Path = "$PlatformTools;$env:Path"
}

# Resolve real Python executable, avoiding WindowsApps execution alias stub
$KnownPythons = @(
    (Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"),
    (Join-Path $env:LOCALAPPDATA "Programs\Python\Python311\python.exe"),
    (Join-Path $env:ProgramFiles "Python312\python.exe")
)

$PythonExe = $null
foreach ($cand in $KnownPythons) {
    if (Test-Path $cand) {
        $PythonExe = $cand
        break
    }
}

if (-not $PythonExe) {
    $cmdPy = (Get-Command python -ErrorAction SilentlyContinue).Source
    if ($cmdPy -and ($cmdPy -notmatch "WindowsApps")) {
        $PythonExe = $cmdPy
    }
}

if (-not $PythonExe) {
    Write-Error "Python 3.12 executable not found. Please install Python."
    exit 1
}

$SetupScript = Join-Path $ScriptDir "setup_rp5.py"
& $PythonExe $SetupScript @args
