"""
Helper script to connect to an active Chrome instance via Chrome DevTools Protocol (CDP),
inspect open tabs, capture screenshots, or drive interactions using Playwright.
"""

import argparse
import json
import sys
import urllib.request


def list_tabs(port: int = 9222):
    """Lists inspectable targets via the HTTP CDP endpoint."""
    url = f"http://localhost:{port}/json/list"
    try:
        with urllib.request.urlopen(url, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            print(f"Discovered {len(data)} browser target(s):")
            for idx, target in enumerate(data):
                t_type = target.get("type", "unknown")
                title = target.get("title", "")
                t_url = target.get("url", "")
                print(f"  [{idx}] ({t_type}) {title} - {t_url}")
            return data
    except Exception as e:
        print(f"Error querying CDP endpoint at {url}: {e}", file=sys.stderr)
        return []


def inspect_with_playwright(port: int = 9222, screenshot_path: str = None):
    """Attaches to the active Chrome instance with Playwright to interact with pages."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright is not installed. Run: pip install playwright", file=sys.stderr)
        return

    with sync_playwright() as p:
        print(f"Connecting to Chrome over CDP on http://localhost:{port}...")
        browser = p.chromium.connect_over_cdp(f"http://localhost:{port}")
        contexts = browser.contexts
        if not contexts:
            print("No browser contexts found.")
            return

        pages = contexts[0].pages
        if not pages:
            print("No open pages found.")
            return

        active_page = pages[0]
        print(f"Active Tab Title: {active_page.title()}")
        print(f"Active Tab URL:   {active_page.url}")

        if screenshot_path:
            active_page.screenshot(path=screenshot_path)
            print(f"Screenshot saved to: {screenshot_path}")


def main():
    parser = argparse.ArgumentParser(description="Interact with Chrome over CDP port 9222")
    parser.add_argument("--port", type=int, default=9222, help="CDP port (default: 9222)")
    parser.add_argument("--list", action="store_true", help="List all open browser tabs")
    parser.add_argument("--screenshot", type=str, help="Capture screenshot of active tab to specified path")

    args = parser.parse_args()

    if args.list or not args.screenshot:
        list_tabs(args.port)

    if args.screenshot:
        inspect_with_playwright(port=args.port, screenshot_path=args.screenshot)


if __name__ == "__main__":
    main()
