---
name: homelab-infrastructure-audit
description: Non-invasive, read-only network and storage auditing runbook for UniFi Cloud Gateways and Synology DSM 7 NAS devices. Covers UniFi JSON telemetry extraction, RF/VLAN security profiling, Synology DSM WebAPI CSRF SynoToken handling, and Btrfs container inspection.
---

# Homelab Infrastructure Audit Runbook

This skill outlines the procedures for non-invasive, read-only security and performance audits across UniFi network gateways and Synology DSM 7 NAS appliances.

---

## 1. Governance & Safety Invariant (Law 23)

- **Strict Read-Only Boundary**: Never modify firewall rules, Wi-Fi parameters, storage pools, or containers during an audit.
- **Surface Critical Exposures**: Quantify risks around UPnP exposure, flat-network consumer IoT broadcast domains, unencrypted DNS, and missing snapshot immutability.
- **Client Risk Profiling**: Categorize every connected endpoint (Core Compute, Media, Smart Appliances, Security/Surveillance) to isolate potential lateral traversal vectors.

---

## 2. UniFi Gateway Auditing via API/Web (`https://<gateway_ip>`)

Extracting live telemetry from UniFi Cloud Gateways (e.g. UCG Fiber, UDM Pro):

### Key Endpoints:
- `/proxy/network/api/s/default/rest/wlanconf`:
  - Inspect Wi-Fi SSIDs, frequency bands (5GHz vs 2.4GHz), and WPA security (`wpa_mode`, `wpa3_transition`, `pmf_mode`).
  - Verify RF optimizations: 802.11r Fast Roaming (`fast_roaming_enabled: true`), 802.11v BSS Transition (`bss_transition: true`), multicast enhancement (`mcastenhance_enabled: true`), minimum data rates (`minrate_na_data_rate_kbps`), and DTIM periods (`dtim_na: 3`, `dtim_ng: 1`).
- `/proxy/network/api/s/default/rest/networkconf`:
  - Inspect LAN subnets and VLAN tags (`vlan_enabled`).
  - Verify UPnP state (`upnp_lan_enabled`): If `true`, flag as high-risk in mixed environments.
  - Verify WAN DNS servers (`wan_dns1`, `wan_dns2`) and IPv6 routing state (`wan_type_v6`).
- `/proxy/network/api/s/default/stat/sta`:
  - Extract complete active client table, MAC fingerprints, hostnames, and IP assignments.

### Audit Checklist & Recommendations:
1. **UPnP Status**: Toggle UPnP off to prevent smart appliances and compromised IoT from opening dynamic inbound WAN pinholes.
2. **VLAN Segmentation**: Move consumer IoT (doorbells, smart beds, appliances, smart TVs) onto a dedicated VLAN (e.g. VLAN 20) with Inter-VLAN rules preventing IoT-to-LAN initiated connections.
3. **DNS Shield**: Enable DNS-over-HTTPS (DoH) via Cloudflare or Quad9 with automatic DNSSEC validation.
4. **IPv6 WAN**: If the ISP advertises IPv6, enable DHCPv6-PD (/56) and SLAAC on the LAN.

---

## 3. Synology DSM 7 WebAPI Auditing (`https://<nas_ip>:5001`)

Synology DSM 7 mandates CSRF protection for all WebAPI interactions.

### CSRF SynoToken Protocol:
In an authenticated DSM web session, requests will fail with `{"error":{"code":119},"success":false}` unless authenticated with a `SynoToken`:
1. **Extract Token**:
   ```javascript
   const token = window.synoToken || (window.SYNO && window.SYNO.SDS && window.SYNO.SDS.Session ? window.SYNO.SDS.Session.SynoToken : null);
   ```
2. **Pass Token**: Supply token both as an HTTP header and as a query parameter:
   ```javascript
   fetch(`/webapi/entry.cgi?api=<API>&version=1&method=<METHOD>&SynoToken=${token}`, {
     headers: { 'X-SYNO-TOKEN': token }
   });
   ```
3. **POST Format**: APIs specifying `"requestFormat": "JSON"` in `SYNO.API.Info` require HTTP POST with `Content-Type: application/x-www-form-urlencoded` or JSON payload.

### Core Audit Endpoints:
- **`SYNO.Core.System` (method `info`)**:
  - Model (e.g., DS920+), CPU cores/frequency (Celeron J4125), RAM size (e.g., 20 GB), DSM firmware version and update level, system temperature, and uptime.
- **`SYNO.Storage.CGI.Storage` (method `load_info`)**:
  - Storage Pools: RAID/SHR type, disk temperatures, S.M.A.R.T. health status.
  - Volumes: Usable size, used capacity, Btrfs filesystem status.
  - Data Scrubbing: Verify scrubbing schedule (`schedule_done`).
- **`SYNO.Docker.Container` (method `list`, POST JSON)**:
  - Container Manager containers, active images, status (healthy, uptime), port bindings, and bridge network configuration.
- **`SYNO.Core.Share` (method `list`)**:
  - Shared folder mappings, descriptions, and storage volume assignments (e.g. verifying high-IOPS NVMe flash pool tiering for `/docker` vs bulk HDD array for `/Media` and `/Backups`).
- **`SYNO.Core.Security.AutoBlock` (method `get`)**:
  - Verify IP auto-blocking threshold (e.g., 10 failed login attempts) to protect SSH and management interfaces.
- **Ransomware Defense**:
  - Verify that critical backup shares (Proxmox backups, client system images) utilize immutable Btrfs snapshots (WORM retention) via Snapshot Replication.
