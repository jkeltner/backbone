#!/usr/bin/env python3
"""
release.py — Master orchestrator for production and distribution

Chains together the audio production and podcast distribution scripts,
tracking completion in release-status.json. Pauses at human review checkpoints.

Video assembly (audiogram for YouTube, vertical clips for shorts) is done
by hand in Descript using the assembled audio + externally-generated
background images from each episode's `assets/` folder. It is not in
this pipeline's scope.

Usage:
  python tools/release.py refrigeration produce      # audio production
  python tools/release.py refrigeration distribute   # Transistor draft upload
  python tools/release.py refrigeration status       # show current state
  python tools/release.py refrigeration full         # produce + distribute

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
        },
        "distribution": {
            "podcast_upload": {"status": "pending", "review": "publish on Transistor"},
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
    """Run the audio production pipeline."""
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

    print(f"\n{'#'*60}")
    print(f"  PRODUCTION COMPLETE")
    print(f"  Next: hand the assembled audio to Descript for video assembly.")
    print(f"{'#'*60}")
    return True


def run_distribute(topic):
    """Run the podcast distribution pipeline (Transistor draft upload)."""
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

    print(f"\n{'#'*60}")
    print(f"  DISTRIBUTION COMPLETE")
    print(f"{'#'*60}")
    return True


def show_status(topic):
    """Display current release status."""
    status, _ = load_status(topic)

    print(f"\nRelease Status: {topic}")
    print(f"Updated: {status.get('updated', 'never')}\n")

    for phase_name in ["production", "distribution"]:
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
  produce      Run the audio production pipeline (audio assembly → timestamps → transcript)
  distribute   Run the distribution pipeline (Transistor draft upload, pauses at publish gate)
  status       Show current release status
  full         Run produce + distribute sequentially
        """,
    )
    parser.add_argument("topic", help="Episode topic")
    parser.add_argument(
        "command",
        choices=["produce", "distribute", "status", "full"],
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
    elif args.command == "full":
        if run_produce(args.topic):
            run_distribute(args.topic)


if __name__ == "__main__":
    main()
