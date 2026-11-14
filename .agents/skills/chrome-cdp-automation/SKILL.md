---
name: chrome-cdp-automation
description: Runbook and automation toolchain for driving authenticated Google Chrome tabs via Chrome DevTools Protocol (CDP port 9222) on Windows. Use whenever the user requests web automation, DOM inspection, data extraction, or UI testing inside an existing authenticated browser session.
---

# Chrome CDP Automation Runbook (Windows)

This skill provides deterministic procedures to launch, attach to, and automate active Google Chrome sessions on Windows using the Chrome DevTools Protocol (CDP) on `localhost:9222`.

---

## 1. Overview & When to Use

Use this workflow when:
- The user needs the agent to interact with a web service that is **already logged in** (e.g., GitHub, internal corporate tools, web dashboards).
- Bypassing manual re-authentication, MFA, or SSO prompts by sharing or persisting session state.
- Inspecting DOM elements, extracting tables/data, or running UI automations on an active desktop tab without requiring an external browser extension.

---

## 2. Launching Chrome with CDP Remote Debugging

Chrome must be started with remote debugging enabled. Two modes are supported:

### Mode A: Dedicated Persistent Profile (Recommended)
Preserves logins, cookies, and local storage in a dedicated workspace directory without conflicting with other running instances:
```powershell
.\.agents\skills\chrome-cdp-automation\scripts\launch_chrome_debug.ps1 -Port 9222
```
Or directly via PowerShell:
```powershell
Start-Process "chrome.exe" -ArgumentList @(
    "--remote-debugging-port=9222",
    "--user-data-dir=$env:LOCALAPPDATA\Google\Chrome\User Data\AntigravityDebug",
    "--no-first-run",
    "--no-default-browser-check"
)
```

### Mode B: Attaching to Default Chrome Profile (Legacy)
If you want to use your primary profile:
1. Completely close all running instances of Chrome.
2. Launch Chrome with the debug port:
   ```powershell
   Start-Process "chrome.exe" -ArgumentList "--remote-debugging-port=9222"
   ```

### Mode C: Modern Chrome (136+) In-Browser Debugging & `chrome-devtools-mcp` (Recommended)
Starting in Chrome 136+, Chrome silently blocks `--remote-debugging-port` when launched against the default user profile for security, and copying the profile directory breaks LevelDB locks and Windows App-Bound Encryption.

To connect cleanly to the user's active, authenticated browser session without cloning profiles:
1. Instruct the user to navigate to: `chrome://inspect/#remote-debugging`
2. Check the box: **"Allow remote debugging for this browser instance"**
3. Launch `chrome-devtools-mcp` in auto-connect mode:
   ```powershell
   npx -y chrome-devtools-mcp@latest --autoConnect
   ```
4. Communicate via standard Model Context Protocol (MCP) JSON-RPC over stdio (`list_pages`, `select_page`, `evaluate_script`, `click`, `take_snapshot`).
5. Upon task completion, terminate the background MCP process immediately to release resources.

---

## 3. Verifying Endpoint & Discovering Open Tabs

### Check CDP Health
```powershell
Invoke-RestMethod -Uri "http://localhost:9222/json/version"
```

### List All Open Inspectable Tabs
```powershell
python .agents/skills/chrome-cdp-automation/scripts/cdp_interact.py --list
```
Or using PowerShell:
```powershell
Invoke-RestMethod -Uri "http://localhost:9222/json/list" | Select-Object id, title, url
```

---

## 4. Driving Tabs via Playwright over CDP

The agent can connect directly to the existing browser session via Playwright without spawning a new browser process:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    context = browser.contexts[0]
    
    # Target the active page or search by URL
    page = context.pages[0] if context.pages else context.new_page()
    print(f"Connected to: {page.title()} ({page.url})")
    
    # Drive interactions, fill forms, or extract data
    # page.click("button#submit")
    # page.screenshot(path="active_tab.png")
```

---

## 5. Human-in-the-Loop Protocol (MFA, Passkeys & CAPTCHA)

1. **Security Challenges**: Never attempt to programmatically bypass CAPTCHAs, hardware tokens (YubiKey), or biometric passkeys.
2. **User Hand-off**: When a 2FA challenge or CAPTCHA appears, the agent pauses execution and prompts the user to complete the check on-screen.
3. **Resumption**: Once the user completes the flow and the destination URL loads, the agent detects the URL change and resumes automated execution.
