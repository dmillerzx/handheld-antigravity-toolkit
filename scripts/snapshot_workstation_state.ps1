<#
.SYNOPSIS
  Snapshot / diff the workstation's background footprint so new installs can be audited against the tuned baseline.
.DESCRIPTION
  -Save    : write services, scheduled tasks, startup entries, and key invariants to a JSON file.
  -Compare : diff the live state against a saved JSON and report added / removed / changed items.
  Read-only. Never changes services, tasks, or registry. Pair with scripts\rollback_services_and_optimizations.ps1
  for restoring the pre-tuning snapshot; this tool is for checking what a NEW install changed.
.EXAMPLE
  .\scripts\snapshot_workstation_state.ps1 -Save configs\system_backup\state_2026-10-25_before-vs.json
  .\scripts\snapshot_workstation_state.ps1 -Compare configs\system_backup\state_2026-10-25_before-vs.json
#>
[CmdletBinding(DefaultParameterSetName = 'Save')]
param(
    [Parameter(ParameterSetName = 'Save', Mandatory)][string]$Save,
    [Parameter(ParameterSetName = 'Compare', Mandatory)][string]$Compare
)
$ErrorActionPreference = 'Stop'

function Get-State {
    $svc = Get-CimInstance Win32_Service | ForEach-Object {
        [pscustomobject]@{ Key = $_.Name; StartMode = $_.StartMode; State = $_.State; Path = $_.PathName }
    }
    $tasks = Get-ScheduledTask | ForEach-Object {
        [pscustomobject]@{ Key = ($_.TaskPath + $_.TaskName); State = [string]$_.State }
    }
    $startup = Get-CimInstance Win32_StartupCommand | ForEach-Object {
        [pscustomobject]@{ Key = ($_.Location + '|' + $_.Name); Command = $_.Command }
    }
    $os = Get-CimInstance Win32_OperatingSystem
    [pscustomobject]@{
        Captured   = (Get-Date).ToString('o')
        Services   = @($svc)
        Tasks      = @($tasks)
        Startup    = @($startup)
        MemoryUsedGB = [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) / 1MB, 2)
        Hypervisor = [bool](Get-CimInstance Win32_ComputerSystem).HypervisorPresent
        # Invariants from AGENTS.md section 10.
        Invariants = [pscustomobject]@{
            DPMService_Running        = ((Get-Service DPMService -ErrorAction SilentlyContinue).Status -eq 'Running')
            DellTechHub_StartMode     = (Get-CimInstance Win32_Service -Filter "Name='DellTechHub'" -ErrorAction SilentlyContinue).StartMode
            DellClientMgmt_StartMode  = (Get-CimInstance Win32_Service -Filter "Name='DellClientManagementService'" -ErrorAction SilentlyContinue).StartMode
            MaxxAudioShieldTask       = [bool](Get-ScheduledTask -TaskName 'MaxxAudioShield_AntiDistortion' -ErrorAction SilentlyContinue)
        }
    }
}

function Compare-Set($name, $old, $new, $props) {
    $o = @{}; foreach ($i in $old) { $o[$i.Key] = $i }
    $n = @{}; foreach ($i in $new) { $n[$i.Key] = $i }
    $added   = $n.Keys | Where-Object { -not $o.ContainsKey($_) } | Sort-Object
    $removed = $o.Keys | Where-Object { -not $n.ContainsKey($_) } | Sort-Object
    Write-Output "`n== $name =="
    if (-not $added -and -not $removed) { Write-Output '  no additions or removals' }
    foreach ($k in $added) {
        $detail = ($props | ForEach-Object { "$_=$($n[$k].$_)" }) -join ' '
        Write-Output "  + $k   $detail"
    }
    foreach ($k in $removed) { Write-Output "  - $k" }
    foreach ($k in ($n.Keys | Where-Object { $o.ContainsKey($_) } | Sort-Object)) {
        $diffs = $props | Where-Object { "$($o[$k].$_)" -ne "$($n[$k].$_)" } | ForEach-Object { "$_ $($o[$k].$_) -> $($n[$k].$_)" }
        if ($diffs) { Write-Output "  ~ $k   $($diffs -join '; ')" }
    }
}

$state = Get-State
if ($PSCmdlet.ParameterSetName -eq 'Save') {
    $dir = Split-Path -Parent $Save
    if ($dir) { New-Item -ItemType Directory -Force $dir | Out-Null }
    $state | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $Save -Encoding UTF8
    Write-Output ("Saved {0} services, {1} tasks, {2} startup entries -> {3}" -f $state.Services.Count, $state.Tasks.Count, $state.Startup.Count, $Save)
    return
}

$base = Get-Content -LiteralPath $Compare -Raw | ConvertFrom-Json
Write-Output ("Baseline: {0}   Now: {1}" -f $base.Captured, $state.Captured)
Compare-Set 'Services'      $base.Services $state.Services @('StartMode', 'State')
Compare-Set 'ScheduledTasks' $base.Tasks   $state.Tasks    @('State')
Compare-Set 'Startup'       $base.Startup  $state.Startup  @('Command')
Write-Output ("`n== Memory / hypervisor ==`n  used GB: {0} -> {1}   hypervisor: {2} -> {3}" -f $base.MemoryUsedGB, $state.MemoryUsedGB, $base.Hypervisor, $state.Hypervisor)
Write-Output "`n== Invariants (AGENTS.md s10) =="
foreach ($p in $state.Invariants.PSObject.Properties) {
    $was = $base.Invariants.($p.Name)
    $flag = if ("$was" -eq "$($p.Value)") { 'OK ' } else { 'CHANGED' }
    Write-Output ("  [{0}] {1}: {2} -> {3}" -f $flag, $p.Name, $was, $p.Value)
}
