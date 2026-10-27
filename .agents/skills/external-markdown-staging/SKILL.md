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

---

## 3. Humanized Contributor Voice & Anti-AI Checklist

When drafting comments, issue updates, or PR descriptions for external repositories:

1. **Strictly Ban AI Template Archetypes**:
   - ❌ NO `### Root Cause Analysis` or `### Summary of Findings`
   - ❌ NO `### Suggested Fixes for Developers` (do not lecture maintainers)
   - ❌ NO didactic bullet lists with bold definitions
   - ❌ NO decorative horizontal rules (`---`) separating every sentence
   - ❌ NO robotic filler ("I hope this helps!", "Please let me know if you need more telemetry.")

2. **The Authentic Contributor Pattern**:
   - **Direct Context**: *"Hey! Running into a crash on an Adreno 650 device (Retroid Pocket 5, Android 13) when launching."*
   - **Targeted Log Snippet**: Fenced code block with only the 5–15 relevant lines of logcat/stack trace.
   - **What Was Tested**: Plain, conversational statement of reproduction steps.
   - **Zero-Pressure Offer**: *"Happy to provide more logs or test a patch if helpful; zero rush or obligation."*

