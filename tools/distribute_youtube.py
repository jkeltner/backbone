#!/usr/bin/env python3
"""
distribute_youtube.py — Upload episode video to YouTube

Uploads audiogram MP4 + metadata + SRT captions to YouTube as unlisted/scheduled
via YouTube Data API v3.

Usage:
  python tools/distribute_youtube.py refrigeration
  python tools/distribute_youtube.py refrigeration --dry-run
  python tools/distribute_youtube.py refrigeration --public    # set as public (default: unlisted)

Config (set in .env):
  YOUTUBE_CLIENT_ID      — OAuth2 client ID
  YOUTUBE_CLIENT_SECRET  — OAuth2 client secret
  YOUTUBE_REFRESH_TOKEN  — OAuth2 refresh token (from initial auth flow)

One-time setup:
  1. Create project in Google Cloud Console
  2. Enable YouTube Data API v3
  3. Create OAuth2 credentials (Desktop app)
  4. Run: python tools/distribute_youtube.py --auth  (to get refresh token)
"""

import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

# YouTube API quota: uploads cost 1,600 units out of 10,000 daily — fine for monthly episodes


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

    m = re.search(r'Top choice:\s*"(.+?)"', text)
    meta["title"] = m.group(1) if m else f"Backbone: {topic.replace('-', ' ').title()}"

    m = re.search(r"Tags / Keywords\s*\n+([\s\S]+?)(?:\n---|\n##|\Z)", text)
    meta["keywords"] = m.group(1).strip().split(", ") if m else []

    return meta


def load_description(topic):
    """Build YouTube description from metadata + show notes."""
    meta_path = REPO_ROOT / "episodes" / topic / "final" / "metadata.md"
    text = meta_path.read_text()

    parts = []

    # Episode description
    m = re.search(
        r"Episode Description\s*\n+\*\(.*?\)\*\s*\n+([\s\S]+?)(?:\n---|\n##)",
        text,
    )
    if m:
        parts.append(m.group(1).strip())

    # Chapter timestamps
    chapters_path = REPO_ROOT / "episodes" / topic / "final" / "chapters.json"
    if chapters_path.exists():
        chapters = json.loads(chapters_path.read_text())
        parts.append("\n🕐 Chapters:")
        for ch in chapters.get("chapters", []):
            ts = ch.get("startTime", 0)
            minutes = int(ts // 60)
            seconds = int(ts % 60)
            parts.append(f"{minutes}:{seconds:02d} — {ch['title']}")

    parts.append("\n—")
    parts.append("Backbone: From Breakthrough to Built-In")
    parts.append("Hosts: Jeff Keltner and Cyrus Mistry")
    parts.append("New episodes monthly.")

    return "\n".join(parts)


def run_auth_flow():
    """Interactive OAuth2 flow to get a refresh token."""
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("Error: google-auth-oauthlib required (pip install google-auth-oauthlib)")
        sys.exit(1)

    client_id = os.environ.get("YOUTUBE_CLIENT_ID")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("Error: YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET must be set in .env")
        sys.exit(1)

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }

    flow = InstalledAppFlow.from_client_config(
        client_config,
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
    )
    credentials = flow.run_local_server(port=0)

    print(f"\nRefresh token (add to .env as YOUTUBE_REFRESH_TOKEN):")
    print(credentials.refresh_token)
    return credentials


def get_credentials():
    """Build OAuth2 credentials from refresh token."""
    try:
        from google.oauth2.credentials import Credentials
    except ImportError:
        print("Error: google-auth required (pip install google-auth)")
        sys.exit(1)

    client_id = os.environ.get("YOUTUBE_CLIENT_ID")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        print("Error: YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, and YOUTUBE_REFRESH_TOKEN must be set in .env")
        print("Run: python tools/distribute_youtube.py --auth")
        sys.exit(1)

    return Credentials(
        token=None,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        token_uri="https://oauth2.googleapis.com/token",
    )


def upload_to_youtube(topic, dry_run=False, public=False):
    """Upload video to YouTube."""
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError:
        print("Error: google-api-python-client required")
        print("pip install google-api-python-client google-auth-oauthlib")
        sys.exit(1)

    episode_dir = REPO_ROOT / "episodes" / topic
    video_path = episode_dir / "assets" / "video" / "episode-full.mp4"
    srt_path = episode_dir / "final" / "transcript.srt"

    if not video_path.exists():
        print(f"Error: {video_path} not found. Run audiogram_video.py first.")
        sys.exit(1)

    meta = load_metadata(topic)
    description = load_description(topic)
    privacy = "public" if public else "unlisted"

    print(f"Title: {meta['title']}")
    print(f"Privacy: {privacy}")
    print(f"Video: {video_path} ({video_path.stat().st_size / (1024*1024):.1f} MB)")
    print(f"Tags: {', '.join(meta['keywords'][:10])}")

    if dry_run:
        print("\n[dry run] Would upload to YouTube as", privacy)
        return

    credentials = get_credentials()
    youtube = build("youtube", "v3", credentials=credentials)

    # Upload video
    print("\nUploading video...")
    body = {
        "snippet": {
            "title": meta["title"],
            "description": description,
            "tags": meta["keywords"][:30],  # YouTube limit
            "categoryId": "27",  # Education
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(str(video_path), mimetype="video/mp4", resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"  Upload progress: {pct}%")

    video_id = response["id"]
    print(f"Video uploaded: https://youtube.com/watch?v={video_id}")

    # Upload captions if available
    if srt_path.exists():
        print("Uploading captions...")
        try:
            caption_body = {
                "snippet": {
                    "videoId": video_id,
                    "language": "en",
                    "name": "English",
                }
            }
            caption_media = MediaFileUpload(str(srt_path), mimetype="application/x-subrip")
            youtube.captions().insert(
                part="snippet",
                body=caption_body,
                media_body=caption_media,
            ).execute()
            print("Captions uploaded.")
        except Exception as e:
            print(f"Warning: caption upload failed: {e}")

    print(f"\nDone! Video is {privacy}: https://youtube.com/watch?v={video_id}")
    return video_id


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Upload episode to YouTube")
    parser.add_argument("topic", nargs="?", help="Episode topic")
    parser.add_argument("--auth", action="store_true", help="Run OAuth2 auth flow")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be uploaded")
    parser.add_argument("--public", action="store_true", help="Set as public (default: unlisted)")
    args = parser.parse_args()

    load_dotenv()

    if args.auth:
        run_auth_flow()
        return

    if not args.topic:
        parser.error("topic is required (unless using --auth)")

    upload_to_youtube(args.topic, dry_run=args.dry_run, public=args.public)


if __name__ == "__main__":
    main()
