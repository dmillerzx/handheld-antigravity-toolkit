# Host Workstation Upkeep & Optimization Suite

This directory contains host-level optimization, telemetry pruning, and audio protection scripts for the **Dell Precision 5560 (Windows 11 Pro)** workstation.

---

## 1. Directory Structure

```text
workstation/
├── scripts/
│   ├── lock_audio_services.ps1                 # Locks Waves/Realtek services (Start=4) for Peace APO / RNNoise
│   ├── register_audio_shield_task.ps1          # Registers MaxxAudioShield_AntiDistortion scheduled task
│   ├── apply_windows_optimizations.ps1         # Safe Dell services tuning, DriverStore audit & registry fixes
│   ├── rollback_services_and_optimizations.ps1 # 100% clean rollback restoring stock Windows/Dell defaults
│   ├── snapshot_workstation_state.ps1          # Pre-optimization state snapshot
│   └── toggle_hypervisor.ps1                   # Toggles hypervisorlaunchtype for virtualization performance
└── docs/                                       # Workstation baselines, health reports & rollback receipts
```

---

## 2. Core Policies & Governance

1. **Dell Precision Service Boundary**:
   - Always preserve `DPMService` (Dell Peripheral Manager / `DDPM.Subagent`) to protect external monitor input switching and USB-C hub controls.
   - Set `DellTechHub` and `DellClientManagementService` to `Manual` (or `Disabled`) to eliminate ~1.3 GB of idle memory bloat.
2. **MaxxAudio Anti-Distortion Shield**:
   - Scheduled task `MaxxAudioShield_AntiDistortion` executes `lock_audio_services.ps1` at startup and logon as `SYSTEM`.
   - Prevents Waves Audio / Realtek from re-enabling DSP compression, ensuring bit-perfect Peace Equalizer APO and RNNoise AI microphone filtering.
3. **Registry & Background App Suppression**:
   - OneNote tray suppression: `HKCU:\Software\Microsoft\Office\16.0\OneNote\Options\Other\EnableMemoryTrayMenuItem = 0`.
   - Phone Link background permissions: `Disabled = 1`, `EnableMmx = 0`.
4. **Full Rollback Guarantee**:
   - `rollback_services_and_optimizations.ps1` restores all stock Dell services, audio tasks, and background apps to factory defaults at any time.
