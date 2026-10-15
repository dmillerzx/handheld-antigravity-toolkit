---
name: youtube-research
description: >-
  Extracts metadata, chapters, links, and complete timestamped transcripts from
  YouTube videos and tutorials using `scripts/fetch_youtube.py`. Use whenever you need
  to research, synthesize, or extract setup guides and emulator settings from YouTube.
---

# YouTube Video & Tutorial Research Skill

This skill allows agents to extract detailed metadata, descriptions, chapters, and full timestamped transcripts from YouTube videos without requiring a browser or API keys.

## Quick CLI Reference

```powershell
# Print clean formatted markdown with chapters and transcript to console:
python scripts/fetch_youtube.py "<youtube_url_or_video_id>"

# Save markdown output to disk (e.g. for persistent notes):
python scripts/fetch_youtube.py "<youtube_url_or_video_id>" -o notes/video_guide.md

# Output structured JSON:
python scripts/fetch_youtube.py "<youtube_url_or_video_id>" --json
```

## Typical Use Cases

1. **Handheld Emulation Tutorials**:
   - Extracting exact settings, Turnip driver recommendations, and shader configurations demonstrated by channels like *Retro Game Corps*, *Joey's Retro Handhelds*, and *Tech Dweeb*.
2. **Winlator / DroidDeck / PC Gaming Setup**:
   - Extracting box64/FEX environment flags, DXVK settings, and game compatibility tricks from YouTube walkthroughs.
3. **Chapter-Targeted Inquiries**:
   - Skimming the extracted `## Chapters & Timestamps` section to pinpoint the exact moment a setting or trick is configured.
