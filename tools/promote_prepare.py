#!/usr/bin/env python3
"""
promote_prepare.py — Prepare promotion content and posting schedule

Reads social-content.md and adapts it for each platform:
  - Twitter/X thread + individual posts
  - LinkedIn long-form post
  - Instagram/TikTok clip captions

Builds a posting schedule (schedule.json) following the cadence:
  Launch Day:  Twitter thread, LinkedIn post, Instagram Reel
  Day 2:       Quote card #1, Clip #1
  Day 3:       Quote card #2
  Day 4:       Clip #1 (Twitter), Clip #2 (Instagram)
  Day 5:       Quote card #3
  Week 2:      "In case you missed it" recap

Usage:
  python tools/promote_prepare.py refrigeration
  python tools/promote_prepare.py refrigeration --launch-date 2026-04-01
  python tools/promote_prepare.py refrigeration --dry-run

Output:
  episodes/{topic}/promotion/
    schedule.json, twitter-thread.md, linkedin-post.md, instagram-captions.md
"""

import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def load_social_content(topic):
    social_path = REPO_ROOT / "episodes" / topic / "final" / "social-content.md"
    if not social_path.exists():
        print(f"Error: {social_path} not found")
        sys.exit(1)
    return social_path.read_text()


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


def extract_thread_posts(social_text):
    """Extract numbered thread posts from social content."""
    posts = []
    matches = re.findall(r"\*\*Post (\d+):\*\*\s*([\s\S]+?)(?=\*\*Post \d+|\Z)", social_text)
    for num, text in matches:
        posts.append(text.strip())
    return posts


def extract_short_description(social_text):
    """Extract short link description."""
    m = re.search(r"Short Link Description\s*\n+\*\(.*?\)\*\s*\n+([\s\S]+?)(?:\n---|\Z)", social_text)
    if m:
        return m.group(1).strip()
    return ""


def prepare_twitter_thread(posts, meta):
    """Format posts as a Twitter thread."""
    lines = [f"# Twitter Thread: {meta['title']}\n"]
    lines.append("*Post as a thread. Each section below is one tweet.*\n")
    lines.append("---\n")

    for i, post in enumerate(posts):
        # Trim to ~280 chars if needed (with link placeholder on last post)
        if i == len(posts) - 1 and "[LINK]" in post:
            post = post.replace("[LINK]", "{EPISODE_URL}")
        lines.append(f"**Tweet {i+1}:**\n")
        lines.append(post)
        lines.append(f"\n*({len(post)} chars)*\n")
        lines.append("---\n")

    return "\n".join(lines)


def prepare_linkedin_post(posts, meta):
    """Adapt social content into a single LinkedIn post."""
    lines = [f"# LinkedIn Post: {meta['title']}\n"]
    lines.append("*Copy and paste the text below into LinkedIn.*\n")
    lines.append("---\n")

    # LinkedIn format: hook + story + CTA
    # Use first 2-3 thread posts as the body, adapted for LinkedIn's longer format
    body_parts = []
    for post in posts[:4]:
        # LinkedIn doesn't have character limits, but line breaks matter
        body_parts.append(post)

    body_parts.append("")
    body_parts.append("---")
    body_parts.append("")
    body_parts.append(f"New episode of Backbone: From Breakthrough to Built-In")
    body_parts.append(f'"{meta["title"]}"')
    body_parts.append("")
    body_parts.append("Link in comments. (LinkedIn shows more reach when the link isn't in the post.)")

    lines.append("\n\n".join(body_parts))
    return "\n".join(lines)


def prepare_instagram_captions(posts, meta, num_clips=3):
    """Write captions for Instagram/TikTok clips."""
    lines = [f"# Instagram/TikTok Captions: {meta['title']}\n"]

    # Announcement reel caption
    lines.append("## Announcement Reel\n")
    short_desc = meta.get("description", posts[0] if posts else "")
    if len(short_desc) > 300:
        short_desc = short_desc[:297] + "..."
    lines.append(short_desc)
    lines.append("\n#backbone #podcast #technology #history #innovation\n")
    lines.append("---\n")

    # Per-clip captions
    for i in range(num_clips):
        lines.append(f"## Clip {i+1}\n")
        if i < len(posts):
            caption = posts[i + 1] if i + 1 < len(posts) else posts[i]
            if len(caption) > 300:
                caption = caption[:297] + "..."
            lines.append(caption)
        else:
            lines.append(f"[Clip {i+1} caption — edit after clip selection]\n")
        lines.append("\n#backbone #podcast #technology\n")
        lines.append("---\n")

    return "\n".join(lines)


def build_schedule(launch_date, meta, num_quote_cards=3, num_clips=3):
    """Build the posting schedule."""
    schedule = {
        "topic": meta.get("topic", ""),
        "title": meta["title"],
        "launch_date": launch_date.isoformat(),
        "posts": [],
    }

    def add(day_offset, platform, content_type, description, file_ref=None):
        post_date = launch_date + timedelta(days=day_offset)
        schedule["posts"].append({
            "date": post_date.isoformat(),
            "day": f"Day {day_offset}" if day_offset > 0 else "Launch",
            "platform": platform,
            "type": content_type,
            "description": description,
            "file": file_ref,
            "posted": False,
        })

    # Launch day
    add(0, "twitter", "thread", "Full episode announcement thread", "twitter-thread.md")
    add(0, "linkedin", "post", "Long-form episode announcement", "linkedin-post.md")
    add(0, "instagram", "reel", "Announcement reel with episode teaser", None)

    # Days 2-5
    add(1, "twitter", "image", "Quote card #1", "quote-card-01.png")
    add(1, "instagram", "clip", "Clip #1 with caption", "clip-01-vert.mp4")

    add(2, "twitter", "image", "Quote card #2", "quote-card-02.png")

    add(3, "twitter", "clip", "Clip #1 (landscape)", "clip-01.mp4")
    if num_clips >= 2:
        add(3, "instagram", "clip", "Clip #2 with caption", "clip-02-vert.mp4")

    add(4, "twitter", "image", "Quote card #3", "quote-card-03.png")

    # Week 2
    add(7, "twitter", "recap", '"In case you missed it" tweet with link', None)
    if num_clips >= 3:
        add(7, "instagram", "clip", "Clip #3 with caption", "clip-03-vert.mp4")

    return schedule


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Prepare promotion content and schedule")
    parser.add_argument("topic", help="Episode topic")
    parser.add_argument("--launch-date", help="Launch date (YYYY-MM-DD), default: today")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.launch_date:
        launch = datetime.strptime(args.launch_date, "%Y-%m-%d")
    else:
        launch = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    social_text = load_social_content(args.topic)
    meta = load_metadata(args.topic)
    meta["topic"] = args.topic
    posts = extract_thread_posts(social_text)

    print(f"Episode: {meta['title']}")
    print(f"Launch date: {launch.strftime('%Y-%m-%d')}")
    print(f"Thread posts: {len(posts)}")

    # Prepare content
    twitter = prepare_twitter_thread(posts, meta)
    linkedin = prepare_linkedin_post(posts, meta)
    instagram = prepare_instagram_captions(posts, meta)
    schedule = build_schedule(launch, meta)

    if args.dry_run:
        print(f"\nSchedule ({len(schedule['posts'])} posts):")
        for p in schedule["posts"]:
            print(f"  {p['date']} [{p['platform']}] {p['type']}: {p['description']}")
        print("\n[dry run]")
        return

    # Write files
    promo_dir = REPO_ROOT / "episodes" / args.topic / "promotion"
    promo_dir.mkdir(parents=True, exist_ok=True)

    (promo_dir / "twitter-thread.md").write_text(twitter)
    (promo_dir / "linkedin-post.md").write_text(linkedin)
    (promo_dir / "instagram-captions.md").write_text(instagram)
    (promo_dir / "schedule.json").write_text(json.dumps(schedule, indent=2) + "\n")
    (promo_dir / "posting-log.json").write_text(json.dumps({"posts": []}, indent=2) + "\n")

    print(f"\nWrote promotion content to {promo_dir}:")
    for f in sorted(promo_dir.iterdir()):
        print(f"  {f.name}")

    print(f"\nSchedule ({len(schedule['posts'])} posts over {(schedule['posts'][-1]['date'][:10] if schedule['posts'] else 'N/A')}):")
    for p in schedule["posts"]:
        print(f"  {p['date'][:10]} [{p['platform']:10s}] {p['type']:8s} — {p['description']}")


if __name__ == "__main__":
    main()
