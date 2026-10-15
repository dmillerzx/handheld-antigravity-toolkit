#!/usr/bin/env python3
"""
fetch_youtube.py — Comprehensive YouTube Video Intelligence & Transcript Extractor
===================================================================================
Fetches video metadata, descriptions, chapters, timestamps, and full transcript
text from YouTube videos to assist with hardware provisioning, emulator configuration,
and tutorial synthesis.

Usage:
    python scripts/fetch_youtube.py "<url_or_video_id>"
    python scripts/fetch_youtube.py "<url_or_video_id>" --json
    python scripts/fetch_youtube.py "<url_or_video_id>" --output notes/guide.md
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Ensure UTF-8 output on Windows consoles/subprocesses
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    YouTubeTranscriptApi = None

try:
    import yt_dlp
except ImportError:
    yt_dlp = None


def extract_video_id(url_or_id: str) -> Optional[str]:
    """Extracts the 11-character YouTube video ID from various URL formats."""
    url_or_id = url_or_id.strip()
    if re.match(r"^[a-zA-Z0-9_-]{11}$", url_or_id):
        return url_or_id

    patterns = [
        r"(?:v=|\/v\/|youtu\.be\/|\/embed\/|\/shorts\/)([a-zA-Z0-9_-]{11})",
        r"[?&]v=([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return None


def format_timestamp(seconds: float) -> str:
    """Formats seconds into MM:SS or HH:MM:SS."""
    s = int(seconds)
    hours = s // 3600
    minutes = (s % 3600) // 60
    secs = s % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def get_video_metadata(video_url: str) -> Dict:
    """Extracts metadata, chapters, and description using yt-dlp without downloading media."""
    if yt_dlp is None:
        return {"error": "yt-dlp is not installed"}

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            if not info:
                return {}
            return {
                "id": info.get("id"),
                "title": info.get("title"),
                "uploader": info.get("uploader"),
                "channel": info.get("channel"),
                "duration": info.get("duration"),
                "duration_formatted": format_timestamp(info.get("duration", 0)),
                "upload_date": info.get("upload_date"),
                "description": info.get("description", ""),
                "chapters": info.get("chapters") or [],
                "webpage_url": info.get("webpage_url", video_url),
            }
    except Exception as e:
        return {"error": str(e)}


def get_transcript(video_id: str, languages: Tuple[str, ...] = ("en", "en-US", "en-GB")) -> List[Dict]:
    """Fetches video transcript entries with timestamps."""
    if YouTubeTranscriptApi is None:
        return []

    raw_snippets = []
    # 1. Try modern instance .fetch()
    try:
        api = YouTubeTranscriptApi()
        raw_snippets = api.fetch(video_id, languages=languages)
    except Exception:
        pass

    # 2. Try listing transcripts and grabbing first available
    if not raw_snippets:
        try:
            api = YouTubeTranscriptApi()
            t_list = api.list(video_id)
            for t in t_list:
                raw_snippets = t.fetch()
                break
        except Exception:
            pass

    # 3. Fallback to legacy static get_transcript if present
    if not raw_snippets and hasattr(YouTubeTranscriptApi, "get_transcript"):
        try:
            raw_snippets = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
        except Exception:
            pass

    # Normalize to List[Dict]
    results = []
    for s in raw_snippets:
        if isinstance(s, dict):
            results.append({
                "text": s.get("text", ""),
                "start": float(s.get("start", 0.0)),
                "duration": float(s.get("duration", 0.0)),
            })
        else:
            results.append({
                "text": getattr(s, "text", ""),
                "start": float(getattr(s, "start", 0.0)),
                "duration": float(getattr(s, "duration", 0.0)),
            })
    return results


def build_markdown_report(meta: Dict, transcript: List[Dict]) -> str:
    """Constructs a clean markdown document with chapters, description, and transcript."""
    lines = []
    title = meta.get("title", "YouTube Video")
    uploader = meta.get("uploader") or meta.get("channel", "Unknown Channel")
    duration = meta.get("duration_formatted", "")
    url = meta.get("webpage_url", "")

    lines.append(f"# {title}")
    lines.append(f"**Channel:** {uploader} | **Duration:** {duration} | **URL:** {url}\n")

    chapters = meta.get("chapters", [])
    if chapters:
        lines.append("## Chapters & Timestamps")
        for ch in chapters:
            start_str = format_timestamp(ch.get("start_time", 0))
            ch_title = ch.get("title", "")
            lines.append(f"- **`{start_str}`** — {ch_title}")
        lines.append("")

    desc = meta.get("description", "").strip()
    if desc:
        lines.append("## Video Description & Links")
        lines.append("```text")
        lines.append(desc[:3000] + ("\n... [truncated]" if len(desc) > 3000 else ""))
        lines.append("```\n")

    lines.append("## Full Transcript")
    if not transcript:
        lines.append("*[No transcript or captions were available for this video]*")
    else:
        # Group transcript by ~30 second chunks or chapter breaks for readability
        chunk_lines = []
        chunk_start = 0.0
        for i, item in enumerate(transcript):
            start = item.get("start", 0.0)
            text = item.get("text", "").strip()
            if not text:
                continue

            if not chunk_lines:
                chunk_start = start

            chunk_lines.append(text)

            # Flush every ~30 seconds or if there's a big pause
            if (start - chunk_start >= 30.0) or (i == len(transcript) - 1):
                timestamp_str = format_timestamp(chunk_start)
                joined_text = " ".join(chunk_lines)
                lines.append(f"**`[{timestamp_str}]`** {joined_text}\n")
                chunk_lines = []

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Fetch YouTube video metadata, chapters, and transcript.")
    parser.add_argument("url", help="YouTube URL or 11-character video ID")
    parser.add_argument("--json", action="store_true", help="Output raw JSON data")
    parser.add_argument("--output", "-o", type=Path, help="Save markdown output to a file")
    args = parser.parse_args()

    video_id = extract_video_id(args.url)
    if not video_id:
        print(f"[ERROR] Could not extract a valid YouTube video ID from: {args.url}", file=sys.stderr)
        sys.exit(1)

    canonical_url = f"https://www.youtube.com/watch?v={video_id}"
    meta = get_video_metadata(canonical_url)
    transcript = get_transcript(video_id)

    if args.json:
        data = {
            "metadata": meta,
            "transcript": transcript,
        }
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json_str, encoding="utf-8")
            print(f"[+] Saved JSON to {args.output}")
        else:
            print(json_str)
        return

    report = build_markdown_report(meta, transcript)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        print(f"[+] Saved transcript report to {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
