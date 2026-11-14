---
name: google-workspace-mcp
description: Sourcing, OAuth configuration, and operational runbook for the @dguido/google-workspace-mcp server. Outlines Google Cloud Auth Platform setup, desktop OAuth credentials, token lifecycle, and deterministic batch operations across Gmail, Google Drive, Calendar, Docs, and Sheets.
---

# Google Workspace MCP Runbook

This skill outlines the procedures for deploying, authenticating, and operating the `@dguido/google-workspace-mcp` Model Context Protocol server in Antigravity.

---

## 1. Architecture & Capabilities

The server connects Antigravity directly to Google Workspace REST APIs via official Google client libraries:
- **Gmail (15 tools)**: `search_emails`, `modify_email` (batch archive/label up to 1,000 threads per call), `create_filter`, `list_labels`, `get_or_create_label`, `delete_email`.
- **Google Drive (31 tools)**: `search`, `get_storage_quota`, `batch_delete`, `move_item`, `empty_trash`.
- **Calendar (7 tools)**: `list_events`, `create_event`, `find_free_time`.
- **Docs & Sheets (25 tools)**: Full document, spreadsheet, and slide creation/formatting.

---

## 2. Google Cloud Platform (GCP) OAuth Setup

1. **Create Project**: In [Google Cloud Console](https://console.cloud.google.com/), create project `Antigravity MCP`.
2. **Enable APIs**: Enable `Gmail API`, `Google Drive API`, `Google Calendar API`, `Google Docs API`, `Google Sheets API`, `People API` under **APIs & Services ➔ Library**.
3. **Google Auth Platform (Consent Screen)**:
   - User type: **External**.
   - App name: `Antigravity MCP`.
   - Developer contact: User email.
   - **Test Users**: Add user Google account email (`user@gmail.com`).
4. **Desktop OAuth Client**:
   - Go to **Clients ➔ + CREATE CLIENT**.
   - Application type: **Desktop app**.
   - Name: `Antigravity Desktop Client`.
   - Checkbox *"Use this client for an AI-powered agent"*: **LEAVE UNCHECKED** (prevents unnecessary Google verification questionnaires while in testing mode).
   - Download credentials JSON (`client_secret_*.json`).

---

## 3. Staging & One-Time Authentication Flow

1. Save credentials to default expected path:
   ```powershell
   Copy-Item "C:\Users\<user>\Downloads\client_secret_*.json" "C:\Users\<user>\.config\google-workspace-mcp\credentials.json" -Force
   ```
2. Run local authentication server:
   ```cmd
   npx -y @dguido/google-workspace-mcp auth
   ```
3. A local loopback server listens on `http://127.0.0.1:9731/oauth2callback`. A browser window opens for the user to sign in with Google.
4. On the warning screen *"Google hasn’t verified this app"*:
   - Click **Advanced** ➔ **Go to Antigravity MCP (unsafe)**.
   - Check permission boxes for Gmail, Drive, Calendar, etc., and click **Continue**.
5. Tokens are automatically cached at: `~/.config/google-workspace-mcp/tokens.json`.

---

## 4. Antigravity MCP Configuration (`~/.gemini/config/mcp_config.json`)

```json
{
  "mcpServers": {
    "google-workspace": {
      "command": "cmd.exe",
      "args": [
        "/c",
        "npx",
        "-y",
        "@dguido/google-workspace-mcp"
      ],
      "env": {
        "GOOGLE_CLIENT_ID": "<CLIENT_ID>",
        "GOOGLE_CLIENT_SECRET": "<CLIENT_SECRET>"
      }
    }
  }
}
```

---

## 5. Batch Email Triage Protocols

### A. Batch Archival (Removing INBOX Label)
In the Gmail API, *Archiving* is accomplished by removing the `INBOX` label from threads.
```json
{
  "name": "modify_email",
  "arguments": {
    "threadId": ["<threadId1>", "<threadId2>", "..."],
    "removeLabelIds": ["INBOX"]
  }
}
```
*Supports up to 1,000 thread IDs per call.*

### B. Auto-Filing into Labels
```json
{
  "name": "modify_email",
  "arguments": {
    "threadId": ["<threadId1>", "<threadId2>"],
    "addLabelIds": ["<LabelId_Receipts>"],
    "removeLabelIds": ["INBOX"]
  }
}
```

### C. Persistent Filter Creation
```json
{
  "name": "create_filter",
  "arguments": {
    "criteria": {
      "query": "subject:(receipt OR invoice OR \"order confirmation\")"
    },
    "action": {
      "addLabelIds": ["<LabelId_Receipts>"],
      "removeLabelIds": ["INBOX"]
    }
  }
}
```

---

## 6. Safety & Non-Mutating Permission Invariant

1. **Permission Guardrail (Law 23)**: Never execute mutating actions (`modify_email`, `delete_email`, `create_filter`, `batch_delete`) without explicit affirmative user confirmation.
2. **Archive-Only Baseline**: Prefer removing `INBOX` rather than trashing messages. With generous Google One storage (e.g. 5 TB), archival retains 100% searchability with zero data loss risk.
