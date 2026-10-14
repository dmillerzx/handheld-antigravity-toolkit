<#
.SYNOPSIS
    Convenience wrapper to run setup_rp5.py with PATH resolution.
#>

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$WorkspaceRoot = Split-Path -Parent $ScriptDir

# Ensure platform-tools is available in current process PATH
$PlatformTools = Join-Path $WorkspaceRoot "platform-tools"
if ((Test-Path $PlatformTools) -and ($env:Path -notlike "*$PlatformTools*")) {
    $env:Path = "$PlatformTools;$env:Path"
}

# Ensure Python is found
$PythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $PythonExe) {
    $PythonDefault = "C:\Users\dmill\AppData\Local\Programs\Python\Python312\python.exe"
    if (Test-Path $PythonDefault) {
        $PythonExe = $PythonDefault
    } else {
        Write-Error "Python executable not found. Please install Python."
        exit 1
    }
}

$SetupScript = Join-Path $ScriptDir "setup_rp5.py"
& $PythonExe $SetupScript $args
