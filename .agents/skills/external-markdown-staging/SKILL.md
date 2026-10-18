---
name: external-markdown-staging
description: >-
  Stages sanitized, unindented Markdown directly into the user's Windows clipboard using scripts/stage_clipboard.ps1.
  Activate whenever the user requests markdown text to copy/paste to GitHub issues, PR comments, Discord, forums, or bug trackers.
---

# External Markdown Staging Skill

This skill ensures that whenever markdown content is provided for the user to paste into external platforms (GitHub, Discord, Reddit, forums), it is sanitized to remove uniform leading indentation and staged directly into the Windows clipboard.

## Why This Skill Exists
In GitHub Flavored Markdown (GFM) and CommonMark, any line with **4 leading spaces** is treated as an indented code block (`<pre><code>`). Copying text from chat UIs often inadvertently introduces 4-space indentation, breaking headings, lists, and HTML `<details>` disclosure elements.

## Procedure

1. **Write content to a clean local file** (e.g. in `notes/` or a temporary file).
2. **Execute the staging script**:
   ```powershell
   .\scripts\stage_clipboard.ps1 -FilePath "path/to/content.md"
   ```
   Or directly with text:
   ```powershell
   .\scripts\stage_clipboard.ps1 -Text "### Header`r`n* Item"
   ```
3. **Notify the User**: Inform the user that the text is active in their Windows clipboard and ready to paste with `Ctrl+V`. Provide the clickable file path link as a fallback.
