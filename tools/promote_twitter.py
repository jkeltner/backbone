#!/usr/bin/env python3
"""
promote_twitter.py — Post to Twitter/X from promotion schedule

Posts content from schedule.json: threads on launch day, individual tweets
with images/clips on subsequent days.

Usage:
  python tools/promote_twitter.py refrigeration                # post next scheduled item
  python tools/promote_twitter.py refrigeration --all          # post all due items
  python tools/promote_twitter.py refrigeration --thread       # post launch thread
  python tools/promote_twitter.py refrigeration --dry-run
  python tools/promote_twitter.py refrigeration --status       # show schedule status

Config (set in .env):
  TWITTER_API_KEY
  TWITTER_API_SECRET
  TWITTER_ACCESS_TOKEN
  TWITTER_ACCESS_SECRET

Note: Twitter free tier allows 1,500 tweets/month — plenty for our cadence.
"""

import json
import os
import re
import sys
from datetime import datetime
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


def get_twitter_client():
    """Initialize Twitter API client."""
    try:
        import tweepy
    except ImportError:
        print("Error: tweepy required (pip install tweepy)")
        sys.exit(1)

    keys = {
        "consumer_key": os.environ.get("TWITTER_API_KEY"),
        "consumer_secret": os.environ.get("TWITTER_API_SECRET"),
        "access_token": os.environ.get("TWITTER_ACCESS_TOKEN"),
        "access_token_secret": os.environ.get("TWITTER_ACCESS_SECRET"),
    }

    missing = [k for k, v in keys.items() if not v]
    if missing:
        print(f"Error: missing Twitter credentials in .env: {', '.join(missing)}")
        sys.exit(1)

    client = tweepy.Client(
        consumer_key=keys["consumer_key"],
        consumer_secret=keys["consumer_secret"],
        access_token=keys["access_token"],
        access_token_secret=keys["access_token_secret"],
    )

    # v1.1 API for media uploads
    auth = tweepy.OAuth1UserHandler(
        keys["consumer_key"],
        keys["consumer_secret"],
        keys["access_token"],
        keys["access_token_secret"],
    )
    api_v1 = tweepy.API(auth)

    return client, api_v1


def load_schedule(topic):
    schedule_path = REPO_ROOT / "episodes" / topic / "promotion" / "schedule.json"
    if not schedule_path.exists():
        print(f"Error: {schedule_path} not found. Run promote_prepare.py first.")
        sys.exit(1)
    return json.loads(schedule_path.read_text()), schedule_path


def load_posting_log(topic):
    log_path = REPO_ROOT / "episodes" / topic / "promotion" / "posting-log.json"
    if log_path.exists():
        return json.loads(log_path.read_text()), log_path
    return {"posts": []}, log_path


def save_posting_log(log, log_path):
    log_path.write_text(json.dumps(log, indent=2) + "\n")


def post_thread(topic, dry_run=False):
    """Post the Twitter thread."""
    promo_dir = REPO_ROOT / "episodes" / topic / "promotion"
    thread_path = promo_dir / "twitter-thread.md"

    if not thread_path.exists():
        print(f"Error: {thread_path} not found")
        return

    text = thread_path.read_text()

    # Parse tweets from the markdown
    tweets = []
    for m in re.finditer(r"\*\*Tweet \d+:\*\*\s*\n([\s\S]+?)(?=\*\*Tweet|\*\(\d+|---|\Z)", text):
        tweet_text = m.group(1).strip()
        # Remove char count annotation
        tweet_text = re.sub(r"\n\*\(\d+ chars\)\*", "", tweet_text).strip()
        if tweet_text:
            tweets.append(tweet_text)

    print(f"Thread: {len(tweets)} tweets")
    for i, t in enumerate(tweets):
        print(f"  [{i+1}] {t[:80]}... ({len(t)} chars)")

    if dry_run:
        print("\n[dry run] Would post thread.")
        return

    client, api_v1 = get_twitter_client()
    log, log_path = load_posting_log(topic)

    previous_id = None
    for i, tweet_text in enumerate(tweets):
        try:
            response = client.create_tweet(
                text=tweet_text,
                in_reply_to_tweet_id=previous_id,
            )
            tweet_id = response.data["id"]
            previous_id = tweet_id
            print(f"  Posted tweet {i+1}: {tweet_id}")

            log["posts"].append({
                "timestamp": datetime.now().isoformat(),
                "platform": "twitter",
                "type": "thread",
                "tweet_number": i + 1,
                "tweet_id": tweet_id,
                "text": tweet_text[:100],
            })
        except Exception as e:
            print(f"  Error posting tweet {i+1}: {e}")
            break

    save_posting_log(log, log_path)


def post_single(topic, post_entry, dry_run=False):
    """Post a single scheduled item (image or clip tweet)."""
    promo_dir = REPO_ROOT / "episodes" / topic / "promotion"
    episode_dir = REPO_ROOT / "episodes" / topic

    content_type = post_entry["type"]
    description = post_entry["description"]
    file_ref = post_entry.get("file")

    # Build tweet text based on type
    if content_type == "image":
        tweet_text = description
    elif content_type == "clip":
        tweet_text = description
    elif content_type == "recap":
        tweet_text = f"In case you missed it — new episode of Backbone is live. {{EPISODE_URL}}"
    else:
        tweet_text = description

    # Find media file
    media_path = None
    if file_ref:
        # Check multiple locations
        for d in [
            episode_dir / "assets" / "images",
            episode_dir / "assets" / "clips",
            promo_dir,
        ]:
            p = d / file_ref
            if p.exists():
                media_path = p
                break

    print(f"  [{post_entry['platform']}] {content_type}: {tweet_text[:80]}...")
    if media_path:
        print(f"  Media: {media_path}")

    if dry_run:
        return

    client, api_v1 = get_twitter_client()
    log, log_path = load_posting_log(topic)

    kwargs = {"text": tweet_text}

    # Upload media if present
    if media_path and media_path.exists():
        try:
            if media_path.suffix == ".mp4":
                media = api_v1.media_upload(str(media_path), media_category="tweet_video")
            else:
                media = api_v1.media_upload(str(media_path))
            kwargs["media_ids"] = [media.media_id]
        except Exception as e:
            print(f"  Warning: media upload failed: {e}")

    try:
        response = client.create_tweet(**kwargs)
        tweet_id = response.data["id"]
        print(f"  Posted: {tweet_id}")

        log["posts"].append({
            "timestamp": datetime.now().isoformat(),
            "platform": "twitter",
            "type": content_type,
            "tweet_id": tweet_id,
            "text": tweet_text[:100],
        })
        save_posting_log(log, log_path)
    except Exception as e:
        print(f"  Error: {e}")


def show_status(topic):
    """Show schedule status."""
    schedule, _ = load_schedule(topic)
    log, _ = load_posting_log(topic)

    posted_count = len(log.get("posts", []))
    today = datetime.now().strftime("%Y-%m-%d")

    print(f"Episode: {schedule.get('title', topic)}")
    print(f"Launch: {schedule.get('launch_date', 'not set')}")
    print(f"Posted: {posted_count} items\n")

    for post in schedule.get("posts", []):
        date = post["date"][:10]
        status = "DONE" if post.get("posted") else ("DUE" if date <= today else "upcoming")
        marker = "[x]" if status == "DONE" else ("[!]" if status == "DUE" else "[ ]")
        print(f"  {marker} {date} [{post['platform']:10s}] {post['type']:8s} — {post['description']}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Post to Twitter/X")
    parser.add_argument("topic", help="Episode topic")
    parser.add_argument("--thread", action="store_true", help="Post launch thread")
    parser.add_argument("--all", action="store_true", help="Post all due items")
    parser.add_argument("--status", action="store_true", help="Show schedule status")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    load_dotenv()

    if args.status:
        show_status(args.topic)
        return

    if args.thread:
        post_thread(args.topic, dry_run=args.dry_run)
        return

    schedule, schedule_path = load_schedule(args.topic)
    today = datetime.now().strftime("%Y-%m-%d")

    # Find due Twitter posts
    twitter_posts = [
        p for p in schedule.get("posts", [])
        if p["platform"] == "twitter" and not p.get("posted") and p["date"][:10] <= today
    ]

    if not twitter_posts:
        print("No Twitter posts due today.")
        show_status(args.topic)
        return

    if args.all:
        for post in twitter_posts:
            if post["type"] == "thread":
                post_thread(args.topic, dry_run=args.dry_run)
            else:
                post_single(args.topic, post, dry_run=args.dry_run)
    else:
        # Post next due item
        post = twitter_posts[0]
        if post["type"] == "thread":
            post_thread(args.topic, dry_run=args.dry_run)
        else:
            post_single(args.topic, post, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
