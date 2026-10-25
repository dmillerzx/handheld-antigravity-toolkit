<#
.SYNOPSIS
    Toggles or sets the Windows boot hypervisor launch type between Auto and Off.

.DESCRIPTION
    WSL 2 and Virtual Machine Platform require the hypervisor to be active ('Auto').
    However, when not compiling or using WSL, disabling the hypervisor ('Off') eliminates
    virtualization overhead and prevents potential latency regressions for timing-critical
    emulators and real-time audio.
    
    Changes take effect upon the next Windows restart.

.PARAMETER State
    Desired state: 'Auto' (enable hypervisor for WSL2), 'Off' (disable hypervisor for bare-metal latency),
    'Status' (check current setting), or 'Toggle' (switch to the opposite state). Defaults to 'Toggle'.

.EXAMPLE
    .\scripts\toggle_hypervisor.ps1 -State Status
    .\scripts\toggle_hypervisor.ps1 -State Auto
    .\scripts\toggle_hypervisor.ps1 -State Off
    .\scripts\toggle_hypervisor.ps1 -State Toggle
#>
[CmdletBinding()]
param (
    [ValidateSet('Auto', 'Off', 'Status', 'Toggle')]
    [string]$State = 'Toggle'
)

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Error "Administrative privileges required. Please run PowerShell as Administrator."
    exit 1
}

function Get-CurrentHypervisorState {
    $bcd = bcdedit /enum '{current}' 2>&1
    $match = $bcd | Select-String -Pattern 'hypervisorlaunchtype\s+(\w+)'
    if ($match) {
        return $match.Matches[0].Groups[1].Value
    }
    # If not explicitly defined, default in modern Windows when VMP is enabled is Auto, else Off
    return "Auto"
}

$current = Get-CurrentHypervisorState
Write-Host "Current hypervisor launch setting: [$current]" -ForegroundColor Cyan

if ($State -eq 'Status') {
    exit 0
}

$target = $State
if ($State -eq 'Toggle') {
    if ($current -ieq 'Off') {
        $target = 'Auto'
    } else {
        $target = 'Off'
    }
}

Write-Host "Setting hypervisorlaunchtype to [$target]..." -ForegroundColor Yellow
$result = bcdedit /set hypervisorlaunchtype $target 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "SUCCESS: hypervisorlaunchtype set to [$target]." -ForegroundColor Green
    Write-Host "NOTE: This change requires a Windows restart to take effect." -ForegroundColor Magenta
    if ($target -eq 'Off') {
        Write-Host "WSL 2 will be disabled until hypervisorlaunchtype is set back to 'Auto'." -ForegroundColor Gray
    } else {
        Write-Host "WSL 2 will be enabled after reboot." -ForegroundColor Gray
    }
} else {
    Write-Error "Failed to set hypervisorlaunchtype: $result"
    exit 1
}
