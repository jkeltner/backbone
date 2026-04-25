#!/usr/bin/env python3
"""
distribute_podcast.py — Upload episode to Transistor.fm as draft

Uploads mp3 + metadata + chapters + transcript to Transistor.fm via REST API.
Creates the episode as a draft — Jeff publishes manually.

Usage:
  python tools/distribute_podcast.py refrigeration
  python tools/distribute_podcast.py refrigeration --dry-run
  python tools/distribute_podcast.py refrigeration --publish    # publish immediately (careful!)

Config (set in .env):
  TRANSISTOR_API_KEY  — Transistor.fm API key
  TRANSISTOR_SHOW_ID  — Show ID from Transistor dashboard

API docs: https://developers.transistor.fm/
"""

import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def load_dotenv():
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


def load_metadata(topic):
    """Parse metadata.md for episode info."""
    meta_path = REPO_ROOT / "episodes" / topic / "final" / "metadata.md"
    if not meta_path.exists():
        print(f"Error: {meta_path} not found")
        sys.exit(1)

    text = meta_path.read_text()
    meta = {}

    # Title — look for "Top choice:" line
    m = re.search(r'Top choice:\s*"(.+?)"', text)
    if m:
        meta["title"] = m.group(1)
    else:
        meta["title"] = f"Backbone: {topic.replace('-', ' ').title()}"

    # Episode number
    m = re.search(r"Episode Number.*?\n+(.+)", text)
    if m and "assigned" not in m.group(1).lower():
        meta["number"] = m.group(1).strip()

    # Keywords
    m = re.search(r"Tags / Keywords\s*\n+([\s\S]+?)(?:\n---|\n##|\Z)", text)
    if m:
        meta["keywords"] = m.group(1).strip()

    return meta


def load_description(topic):
    """Load episode description from metadata.md."""
    meta_path = REPO_ROOT / "episodes" / topic / "final" / "metadata.md"
    text = meta_path.read_text()
    m = re.search(
        r"Episode Description\s*\n+\*\(.*?\)\*\s*\n+([\s\S]+?)(?:\n---|\n##)",
        text,
    )
    if m:
        return m.group(1).strip()
    return ""


def load_show_notes(topic):
    """Load show notes for the episode page."""
    notes_path = REPO_ROOT / "episodes" / topic / "final" / "show-notes.md"
    if notes_path.exists():
        return notes_path.read_text()
    return ""


def upload_to_transistor(topic, dry_run=False, publish=False):
    """Upload episode to Transistor.fm."""
    try:
        import requests
    except ImportError:
        print("Error: requests library required (pip install requests)")
        sys.exit(1)

    api_key = os.environ.get("TRANSISTOR_API_KEY")
    show_id = os.environ.get("TRANSISTOR_SHOW_ID")

    if not api_key:
        print("Error: TRANSISTOR_API_KEY not set in .env")
        sys.exit(1)
    if not show_id:
        print("Error: TRANSISTOR_SHOW_ID not set in .env")
        sys.exit(1)

    episode_dir = REPO_ROOT / "episodes" / topic
    final_dir = episode_dir / "final"
    mp3_path = final_dir / "episode.mp3"
    chapters_path = final_dir / "chapters.json"
    transcript_path = final_dir / "transcript.html"

    if not mp3_path.exists():
        print(f"Error: {mp3_path} not found. Run audio_assemble.py first.")
        sys.exit(1)

    meta = load_metadata(topic)
    description = load_description(topic)
    show_notes = load_show_notes(topic)

    print(f"Episode: {meta['title']}")
    print(f"Description: {description[:100]}...")
    print(f"MP3: {mp3_path} ({mp3_path.stat().st_size / (1024*1024):.1f} MB)")

    if chapters_path.exists():
        chapters = json.loads(chapters_path.read_text())
        print(f"Chapters: {len(chapters.get('chapters', []))} chapters")

    if transcript_path.exists():
        print(f"Transcript: {transcript_path}")

    if dry_run:
        print("\n[dry run] Would upload to Transistor.fm as draft.")
        return

    headers = {"x-api-key": api_key}
    base_url = "https://api.transistor.fm/v1"

    # Step 1: Get authorized upload URL
    print("\nRequesting upload URL...")
    resp = requests.get(
        f"{base_url}/episodes/authorize_upload",
        headers=headers,
        params={"filename": f"{topic}-episode.mp3"},
    )
    resp.raise_for_status()
    upload_data = resp.json()["data"]["attributes"]
    upload_url = upload_data["upload_url"]
    audio_url = upload_data["audio_url"]  # The final hosted URL (use when creating episode)

    # Step 2: Upload MP3
    print("Uploading MP3...")
    with open(mp3_path, "rb") as f:
        resp = requests.put(upload_url, data=f, headers={"Content-Type": "audio/mpeg"})
    resp.raise_for_status()
    print("Upload complete.")

    # Step 3: Create episode
    print("Creating episode...")
    episode_data = {
        "episode": {
            "show_id": show_id,
            "title": meta["title"],
            "summary": description,
            "description": show_notes,
            "audio_url": audio_url,
            "status": "published" if publish else "draft",
        }
    }

    if meta.get("number"):
        episode_data["episode"]["number"] = meta["number"]
    if meta.get("keywords"):
        episode_data["episode"]["keywords"] = meta["keywords"]

    resp = requests.post(f"{base_url}/episodes", headers=headers, json=episode_data)
    resp.raise_for_status()
    episode_id = resp.json()["data"]["id"]
    print(f"Episode created: ID {episode_id} (status: {'published' if publish else 'draft'})")

    # Step 4: Upload transcript if available
    if transcript_path.exists():
        print("Uploading transcript...")
        try:
            with open(transcript_path, "rb") as f:
                resp = requests.patch(
                    f"{base_url}/episodes/{episode_id}",
                    headers=headers,
                    files={"transcript": f},
                )
            resp.raise_for_status()
            print("Transcript uploaded.")
        except Exception as e:
            print(f"Warning: transcript upload failed: {e}")

    # Step 5: Upload chapters if available
    if chapters_path.exists():
        print("Uploading chapters...")
        try:
            chapters_data = json.loads(chapters_path.read_text())
            resp = requests.patch(
                f"{base_url}/episodes/{episode_id}",
                headers=headers,
                json={
                    "episode": {
                        "chapters": chapters_data.get("chapters", []),
                    }
                },
            )
            resp.raise_for_status()
            print("Chapters uploaded.")
        except Exception as e:
            print(f"Warning: chapters upload failed: {e}")

    status_label = "PUBLISHED" if publish else "DRAFT"
    print(f"\nDone! Episode '{meta['title']}' is {status_label} on Transistor.fm.")
    print("Log into Transistor.fm to review and publish." if not publish else "")

    return episode_id


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Upload episode to Transistor.fm")
    parser.add_argument("topic", help="Episode topic")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be uploaded")
    parser.add_argument("--publish", action="store_true", help="Publish immediately (default: draft)")
    args = parser.parse_args()

    load_dotenv()
    upload_to_transistor(args.topic, dry_run=args.dry_run, publish=args.publish)


if __name__ == "__main__":
    main()
