#!/usr/bin/env python3
"""
release.py — Master orchestrator for production, distribution, and promotion

Chains together the individual pipeline scripts, tracking completion in
release-status.json. Pauses at human review checkpoints.

Usage:
  python tools/release.py refrigeration produce      # production pipeline
  python tools/release.py refrigeration distribute    # distribution pipeline
  python tools/release.py refrigeration promote       # promotion pipeline
  python tools/release.py refrigeration status        # show current state
  python tools/release.py refrigeration full          # run everything (with pauses)

Each step can be re-run safely — scripts skip already-completed work or
overwrite as appropriate.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
TOOLS_DIR = REPO_ROOT / "tools"


def load_status(topic):
    """Load or initialize release status."""
    status_path = REPO_ROOT / "episodes" / topic / "release-status.json"
    if status_path.exists():
        return json.loads(status_path.read_text()), status_path

    status = {
        "topic": topic,
        "created": datetime.now().isoformat(),
        "updated": datetime.now().isoformat(),
        "production": {
            "audio_assembly": {"status": "pending"},
            "timestamps": {"status": "pending"},
            "transcript": {"status": "pending"},
            "audiogram_video": {"status": "pending"},
            "clip_selection": {"status": "pending", "review": "required"},
            "clip_generation": {"status": "pending"},
            "social_images": {"status": "pending", "review": "required"},
            "episode_cover": {"status": "pending", "review": "required"},
        },
        "distribution": {
            "podcast_upload": {"status": "pending", "review": "publish on Transistor"},
            "youtube_upload": {"status": "pending", "review": "publish on YouTube"},
            "newsletter_draft": {"status": "pending", "review": "review and send on Buttondown"},
        },
        "promotion": {
            "content_prep": {"status": "pending", "review": "approve schedule"},
            "twitter_thread": {"status": "pending"},
            "twitter_drip": {"status": "pending"},
            "linkedin": {"status": "pending", "review": "copy/paste to LinkedIn"},
            "instagram": {"status": "pending", "review": "upload from phone"},
        },
    }
    return status, status_path


def save_status(status, status_path):
    status["updated"] = datetime.now().isoformat()
    status_path.write_text(json.dumps(status, indent=2) + "\n")


def run_step(name, cmd, status, status_path, step_key, phase_key):
    """Run a pipeline step, updating status."""
    step = status[phase_key][step_key]

    if step["status"] == "completed":
        print(f"  [{step_key}] Already completed, skipping.")
        return True

    print(f"\n{'='*60}")
    print(f"  STEP: {name}")
    print(f"{'='*60}")

    step["status"] = "in_progress"
    step["started"] = datetime.now().isoformat()
    save_status(status, status_path)

    result = subprocess.run(
        [sys.executable] + cmd,
        cwd=str(REPO_ROOT),
    )

    if result.returncode == 0:
        step["status"] = "completed"
        step["completed"] = datetime.now().isoformat()
        save_status(status, status_path)
        print(f"  [{step_key}] Completed.")
        return True
    else:
        step["status"] = "failed"
        step["error"] = f"Exit code {result.returncode}"
        save_status(status, status_path)
        print(f"  [{step_key}] FAILED (exit code {result.returncode})")
        return False


def pause_for_review(step_name, instructions):
    """Pause and wait for human review."""
    print(f"\n{'*'*60}")
    print(f"  REVIEW CHECKPOINT: {step_name}")
    print(f"  {instructions}")
    print(f"{'*'*60}")
    try:
        response = input("\n  Press Enter to continue, or 'skip' to skip, or 'quit' to stop: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n  Stopping.")
        return "quit"
    if response == "quit":
        return "quit"
    if response == "skip":
        return "skip"
    return "continue"


def run_produce(topic):
    """Run the production pipeline."""
    status, status_path = load_status(topic)
    model_args = []  # Could be ["--model", "v3"] etc.

    print(f"\n{'#'*60}")
    print(f"  PRODUCTION PIPELINE: {topic}")
    print(f"{'#'*60}")

    # 1. Audio assembly
    if not run_step(
        "Audio Assembly",
        [str(TOOLS_DIR / "audio_assemble.py"), topic, "--no-music"] + model_args,
        status, status_path, "audio_assembly", "production",
    ):
        print("\nAudio assembly failed. Fix and re-run.")
        return False

    # 2. Timestamps & chapters
    run_step(
        "Timestamp Chapters",
        [str(TOOLS_DIR / "timestamp_chapters.py"), topic],
        status, status_path, "timestamps", "production",
    )

    # 3. Transcript
    run_step(
        "Generate Transcript",
        [str(TOOLS_DIR / "generate_transcript.py"), topic],
        status, status_path, "transcript", "production",
    )

    # 4. Audiogram video
    run_step(
        "Audiogram Video",
        [str(TOOLS_DIR / "audiogram_video.py"), topic],
        status, status_path, "audiogram_video", "production",
    )

    # 5. Social images
    run_step(
        "Social Images",
        [str(TOOLS_DIR / "social_images.py"), topic],
        status, status_path, "social_images", "production",
    )

    # Review checkpoint: social images
    review = pause_for_review(
        "Social Images",
        "Check generated images in episodes/{}/assets/images/".format(topic),
    )
    if review == "quit":
        return False

    # 6. Episode cover
    step = status["production"]["episode_cover"]
    if step["status"] != "completed":
        step["status"] = "completed"
        step["note"] = "Generated as part of social images"
        save_status(status, status_path)

    # 7. Clip selection
    run_step(
        "Clip Selection",
        [str(TOOLS_DIR / "clip_selector.py"), topic],
        status, status_path, "clip_selection", "production",
    )

    # Review checkpoint: approve clips
    review = pause_for_review(
        "Clip Selection",
        "Review clip-manifest.json, set 'approved: true' for clips you want.",
    )
    if review == "quit":
        return False

    # 8. Clip generation
    run_step(
        "Clip Generation",
        [str(TOOLS_DIR / "clip_generate.py"), topic],
        status, status_path, "clip_generation", "production",
    )

    print(f"\n{'#'*60}")
    print(f"  PRODUCTION COMPLETE")
    print(f"{'#'*60}")
    return True


def run_distribute(topic):
    """Run the distribution pipeline."""
    status, status_path = load_status(topic)

    print(f"\n{'#'*60}")
    print(f"  DISTRIBUTION PIPELINE: {topic}")
    print(f"{'#'*60}")

    # 1. Podcast upload (draft)
    run_step(
        "Podcast Upload (Transistor.fm)",
        [str(TOOLS_DIR / "distribute_podcast.py"), topic],
        status, status_path, "podcast_upload", "distribution",
    )

    review = pause_for_review(
        "Podcast",
        "Log into Transistor.fm to review and publish the episode.",
    )
    if review == "quit":
        return False

    # 2. YouTube upload (unlisted)
    run_step(
        "YouTube Upload",
        [str(TOOLS_DIR / "distribute_youtube.py"), topic],
        status, status_path, "youtube_upload", "distribution",
    )

    review = pause_for_review(
        "YouTube",
        "Log into YouTube to review, add end screen, and publish.",
    )
    if review == "quit":
        return False

    # 3. Newsletter draft
    run_step(
        "Newsletter Draft (Buttondown)",
        [str(TOOLS_DIR / "distribute_newsletter.py"), topic],
        status, status_path, "newsletter_draft", "distribution",
    )

    review = pause_for_review(
        "Newsletter",
        "Log into Buttondown to review and send the newsletter.",
    )
    if review == "quit":
        return False

    print(f"\n{'#'*60}")
    print(f"  DISTRIBUTION COMPLETE")
    print(f"{'#'*60}")
    return True


def run_promote(topic):
    """Run the promotion pipeline."""
    status, status_path = load_status(topic)

    print(f"\n{'#'*60}")
    print(f"  PROMOTION PIPELINE: {topic}")
    print(f"{'#'*60}")

    # 1. Content prep
    run_step(
        "Promotion Content Prep",
        [str(TOOLS_DIR / "promote_prepare.py"), topic],
        status, status_path, "content_prep", "promotion",
    )

    review = pause_for_review(
        "Promotion Schedule",
        "Review schedule.json and content files in episodes/{}/promotion/".format(topic),
    )
    if review == "quit":
        return False

    # 2. Twitter thread
    print("\nTwitter thread posting:")
    print("  Run: python tools/promote_twitter.py {} --thread".format(topic))
    print("  (Requires Twitter API credentials in .env)")

    step = status["promotion"]["twitter_thread"]
    if step["status"] != "completed":
        review = pause_for_review(
            "Twitter Thread",
            "Post the thread manually or via promote_twitter.py, then press Enter.",
        )
        if review == "quit":
            return False
        if review != "skip":
            step["status"] = "completed"
            save_status(status, status_path)

    # 3. LinkedIn
    print("\nLinkedIn post:")
    print("  Content ready in: episodes/{}/promotion/linkedin-post.md".format(topic))
    print("  Copy and paste into LinkedIn manually.")

    step = status["promotion"]["linkedin"]
    if step["status"] != "completed":
        review = pause_for_review("LinkedIn", "Post to LinkedIn, then press Enter.")
        if review == "quit":
            return False
        if review != "skip":
            step["status"] = "completed"
            save_status(status, status_path)

    # 4. Instagram
    print("\nInstagram/TikTok:")
    print("  Clips in: episodes/{}/assets/clips/".format(topic))
    print("  Captions in: episodes/{}/promotion/instagram-captions.md".format(topic))

    step = status["promotion"]["instagram"]
    if step["status"] != "completed":
        review = pause_for_review("Instagram/TikTok", "Upload from phone, then press Enter.")
        if review == "quit":
            return False
        if review != "skip":
            step["status"] = "completed"
            save_status(status, status_path)

    # 5. Twitter drip
    print("\nTwitter drip campaign (days 2-7):")
    print("  Run daily: python tools/promote_twitter.py {} --all".format(topic))

    print(f"\n{'#'*60}")
    print(f"  PROMOTION LAUNCHED")
    print(f"{'#'*60}")
    return True


def show_status(topic):
    """Display current release status."""
    status, _ = load_status(topic)

    print(f"\nRelease Status: {topic}")
    print(f"Updated: {status.get('updated', 'never')}\n")

    for phase_name in ["production", "distribution", "promotion"]:
        phase = status.get(phase_name, {})
        total = len(phase)
        completed = sum(1 for s in phase.values() if s.get("status") == "completed")
        print(f"  {phase_name.upper()} ({completed}/{total})")

        for step_key, step in phase.items():
            s = step.get("status", "pending")
            marker = {"completed": "[x]", "in_progress": "[~]", "failed": "[!]", "pending": "[ ]"}.get(s, "[ ]")
            review = f"  (review: {step['review']})" if step.get("review") and s != "completed" else ""
            print(f"    {marker} {step_key}{review}")

        print()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Backbone release orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  produce      Run the production pipeline (audio → video → images → clips)
  distribute   Run the distribution pipeline (Transistor → YouTube → newsletter)
  promote      Run the promotion pipeline (schedule → Twitter → LinkedIn → Instagram)
  status       Show current release status
  full         Run all pipelines sequentially
        """,
    )
    parser.add_argument("topic", help="Episode topic")
    parser.add_argument(
        "command",
        choices=["produce", "distribute", "promote", "status", "full"],
        help="Pipeline to run",
    )
    args = parser.parse_args()

    # Verify episode directory exists
    episode_dir = REPO_ROOT / "episodes" / args.topic
    if not episode_dir.exists():
        print(f"Error: episode directory not found: {episode_dir}")
        sys.exit(1)

    if args.command == "status":
        show_status(args.topic)
    elif args.command == "produce":
        run_produce(args.topic)
    elif args.command == "distribute":
        run_distribute(args.topic)
    elif args.command == "promote":
        run_promote(args.topic)
    elif args.command == "full":
        if run_produce(args.topic):
            if run_distribute(args.topic):
                run_promote(args.topic)


if __name__ == "__main__":
    main()
