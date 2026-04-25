#!/usr/bin/env python3
"""
distribute_newsletter.py — Draft episode newsletter via Buttondown API

Reads social-content.md and show-notes.md, drafts a newsletter email,
and pushes it to Buttondown as a draft for Jeff to review and send.

Usage:
  python tools/distribute_newsletter.py refrigeration
  python tools/distribute_newsletter.py refrigeration --dry-run
  python tools/distribute_newsletter.py refrigeration --send     # send immediately (careful!)

Config (set in .env):
  BUTTONDOWN_API_KEY — Buttondown API key

API docs: https://api.buttondown.email/v1/docs
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
    meta_path = REPO_ROOT / "episodes" / topic / "final" / "metadata.md"
    meta = {"title": topic.replace("-", " ").title()}
    if meta_path.exists():
        text = meta_path.read_text()
        m = re.search(r'Top choice:\s*"(.+?)"', text)
        if m:
            meta["title"] = m.group(1)
        m = re.search(
            r"Episode Description\s*\n+\*\(.*?\)\*\s*\n+([\s\S]+?)(?:\n---|\n##)",
            text,
        )
        if m:
            meta["description"] = m.group(1).strip()
    return meta


def load_social_content(topic):
    path = REPO_ROOT / "episodes" / topic / "final" / "social-content.md"
    if path.exists():
        return path.read_text()
    return ""


def load_show_notes(topic):
    path = REPO_ROOT / "episodes" / topic / "final" / "show-notes.md"
    if path.exists():
        return path.read_text()
    return ""


def draft_newsletter(topic):
    """Compose newsletter body in markdown (Buttondown is markdown-native)."""
    meta = load_metadata(topic)
    social = load_social_content(topic)
    notes = load_show_notes(topic)

    # Extract thread posts for story beats
    posts = re.findall(r"\*\*Post \d+:\*\*\s*([\s\S]+?)(?=\*\*Post \d+|\Z)", social)
    posts = [p.strip() for p in posts]

    # Extract people mentioned from show notes
    people_section = ""
    m = re.search(r"## People Mentioned\s*\n([\s\S]+?)(?=\n## |\Z)", notes)
    if m:
        people = re.findall(r"\*\*(.+?)\*\*\s*—\s*(.+?)(?=\n\n|\Z)", m.group(1), re.DOTALL)
        if people:
            people_lines = []
            for name, desc in people[:6]:  # Top 6
                short_desc = desc.split(".")[0].strip()  # First sentence
                people_lines.append(f"- **{name}** — {short_desc}")
            people_section = "\n".join(people_lines)

    # Build newsletter
    body = f"""# New Episode: {meta['title']}

{meta.get('description', '')}

**[Listen to the full episode →]({{{{EPISODE_URL}}}})**

---

## The Story in Brief

"""

    # Use first 3-4 thread posts as story beats
    for post in posts[:4]:
        body += post + "\n\n"

    if people_section:
        body += """---

## People in This Episode

""" + people_section + "\n\n"

    body += """---

## Listen & Share

- **[Listen on your favorite podcast app]({{EPISODE_URL}})**
- **[Watch on YouTube]({{YOUTUBE_URL}})**
- Share this episode with someone who loves technology history

If you enjoyed this, forward this email to a friend. That's genuinely how this show grows.

---

*Backbone: From Breakthrough to Built-In*
*Hosts: Jeff Keltner & Cyrus Mistry*
*New episodes monthly.*
"""

    subject = f"New Episode: {meta['title']}"
    return subject, body


def push_to_buttondown(subject, body, dry_run=False, send=False):
    """Push newsletter to Buttondown as draft."""
    try:
        import requests
    except ImportError:
        print("Error: requests required (pip install requests)")
        sys.exit(1)

    api_key = os.environ.get("BUTTONDOWN_API_KEY")
    if not api_key:
        print("Error: BUTTONDOWN_API_KEY not set in .env")
        sys.exit(1)

    print(f"Subject: {subject}")
    print(f"Body: {len(body)} chars")
    print(f"Status: {'send' if send else 'draft'}")

    if dry_run:
        print(f"\n--- Newsletter Preview ---\n")
        print(body[:1000])
        if len(body) > 1000:
            print(f"\n... ({len(body) - 1000} more chars)")
        print("\n[dry run]")
        return

    headers = {"Authorization": f"Token {api_key}"}
    data = {
        "subject": subject,
        "body": body,
        "status": "sent" if send else "draft",
    }

    resp = requests.post(
        "https://api.buttondown.email/v1/emails",
        headers=headers,
        json=data,
    )

    if resp.status_code in (200, 201):
        result = resp.json()
        email_id = result.get("id", "")
        status = result.get("status", "draft")
        print(f"\nNewsletter created: {email_id} (status: {status})")
        if not send:
            print("Log into Buttondown to review and send.")
    else:
        print(f"Error: {resp.status_code} — {resp.text[:300]}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Draft newsletter via Buttondown")
    parser.add_argument("topic", help="Episode topic")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--send", action="store_true", help="Send immediately (default: draft)")
    args = parser.parse_args()

    load_dotenv()
    subject, body = draft_newsletter(args.topic)
    push_to_buttondown(subject, body, dry_run=args.dry_run, send=args.send)


if __name__ == "__main__":
    main()
