---
name: workstation-tuning
description: >-
  Deterministic Windows 11 workstation optimization, Dell Precision 5560 telemetry pruning,
  MaxxAudio distortion shield verification, safe DriverStore pruning, and rollback management.
---

# Workstation Tuning & Audio Shield Runbook

This skill provides verified operational procedures for maintaining a high-performance Windows 11 development workstation (Dell Precision 5560) alongside the Retroid Pocket 5 Android development environment.

---

## 1. MaxxAudio / Waves Audio Shield Watchdog

Dell laptops with Realtek audio drivers automatically re-enable Waves MaxxAudio background processing, causing heavy dynamic range compression and output distortion on external monitors and DACs.

### Architecture
- **Watchdog Scheduled Task**: `MaxxAudioShield_AntiDistortion`
- **Trigger**: Runs at system startup (boot) and user logon as `SYSTEM`.
- **Target Services Forced to Start=4 (Disabled)**:
  - `RtkAudioUniversalService`
  - `WavesAudioService`
  - `WavesSysSvc`
  - `RtkAudUService` (if present)
  - `WavesSvc` (if present)

### Verification Command:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\lock_audio_services.ps1
```
Confirms that Peace Equalizer APO (PID active, `peace.txt`, RNNoise VST plugin) is healthy and Waves services remain stopped.

---

## 2. Dell Precision 5560 Service Boundary & Memory Reclamation

### The Boundary Law
- **PRESERVE**: `DPMService` (Dell Peripheral Manager / `DDPM.Subagent`). Handles external Dell monitor input presets, USB-C hub switching, and mouse/keyboard settings. Never stop or disable this service.
- **PRUNE**: `DellTechHub` and `DellClientManagementService`. Spawns up to 7 child telemetry subagents (`Dell.TechHub.Instrumentation.SubAgent`, `Dell.CoreServices.Client`, `Dell.TechHub.Analytics.SubAgent`, etc.) consuming **~1.3 GB of physical RAM**.

### Execution Command:
```powershell
# Set services to Manual
Set-Service -Name DellTechHub -StartupType Manual
Set-Service -Name DellClientManagementService -StartupType Manual
Stop-Service -Name DellTechHub, DellClientManagementService -Force

# Terminate lingering telemetry subagents
Get-Process | Where-Object { $_.ProcessName -like "Dell.TechHub*" -or $_.ProcessName -eq "Dell.CoreServices.Client" -or $_.ProcessName -eq "Dell.UCA.Manager" } | Stop-Process -Force
```

---

## 3. OneNote Quick Note & Phone Link Background Suppression

### OneNote Tray Icon
Office Click-to-Run repopulates `Send to OneNote.lnk` in the user's startup folder on logon unless explicitly disabled via the Office options registry key:
```powershell
Set-ItemProperty -Path "HKCU:\Software\Microsoft\Office\16.0\OneNote\Options\Other" -Name "EnableMemoryTrayMenuItem" -Value 0 -Type DWord -Force
Set-ItemProperty -Path "HKCU:\Software\Microsoft\Office\16.0\OneNote\Options\Other" -Name "EnableMemoryShortcut" -Value 0 -Type DWord -Force
Remove-Item -Path "$([System.Environment]::GetFolderPath('Startup'))\Send to OneNote.lnk" -Force -ErrorAction SilentlyContinue
Stop-Process -Name onenotem -Force -ErrorAction SilentlyContinue
```

### Phone Link Background Permission
```powershell
$phoneReg = "HKCU:\Software\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications\Microsoft.YourPhone_8wekyb3d8bbwe"
Set-ItemProperty -Path $phoneReg -Name "Disabled" -Value 1 -Type DWord -Force
Set-ItemProperty -Path $phoneReg -Name "DisabledByUser" -Value 1 -Type DWord -Force
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\System" -Name "EnableMmx" -Value 0 -Type DWord -Force
Stop-Process -Name PhoneExperienceHost -Force -ErrorAction SilentlyContinue
```

---

## 4. Reversible Rollback Protocol

Every service modification is non-destructive and tracked against the pre-tuning baseline snapshot in `configs/system_backup/services_snapshot_pre_tuning.json`.
To restore any service back to its exact original state:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\rollback_services_and_optimizations.ps1
```
Or preview changes safely without applying:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\rollback_services_and_optimizations.ps1 -WhatIf
```

---

## 5. Installing New Dev Tooling Without Undoing the Tuning

Before installing anything that adds services, scheduled tasks, startup entries, or a hypervisor (Visual Studio, WSL2, Docker, vendor tools):

1. **Baseline first** (read-only): `.\scripts\snapshot_workstation_state.ps1 -Save configs\system_backup\state_<date>_before-<tool>.json`
2. **Install**, preferring user-scope / no-restart options and the smallest workload (e.g. VS Build Tools `VCTools`, not full VS).
3. **Diff**: `.\scripts\snapshot_workstation_state.ps1 -Compare <baseline.json>` lists added/changed services, tasks, startup entries, memory, hypervisor state, and the AGENTS.md section-10 invariants (DPMService running, Dell telemetry services Manual, MaxxAudioShield task present).
4. **Prune** only what the diff shows is new telemetry/updater noise: set to `Manual` rather than deleting, record the change, never touch `DPMService`.
5. **WSL2**: keep `%USERPROFILE%\.wslconfig` capped (host: 31.7 GB RAM / 16 logical CPUs -> `memory=10GB`, `processors=8`, `swap=2GB`, `autoMemoryReclaim=gradual`, `sparseVhd=true`). Apply with `wsl --shutdown`. Enabling Virtual Machine Platform turns the hypervisor on; note it in the diff.
6. Optional, user-approval only: Defender exclusions for build directories (speeds builds, lowers protection).
