#!/usr/bin/env python3
"""
clip_generate.py — Generate clip videos from episode audio

Reads clip-manifest.json, cuts audio segments, and generates audiogram videos
in both 16:9 (YouTube/Twitter) and 9:16 (Instagram/TikTok) formats.

Usage:
  python tools/clip_generate.py refrigeration
  python tools/clip_generate.py refrigeration --clip 1        # specific clip only
  python tools/clip_generate.py refrigeration --approved-only  # only approved clips
  python tools/clip_generate.py refrigeration --dry-run

Requires: ffmpeg on PATH
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

# Video dimensions
LANDSCAPE = {"w": 1920, "h": 1080}
PORTRAIT = {"w": 1080, "h": 1920}
FPS = 30
WAVEFORM_COLOR = "0x4A90D9"
BG_COLOR = "1a1a2e"


def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("Error: ffmpeg not found. Install: brew install ffmpeg")
        return False


def load_metadata_title(topic):
    meta_path = REPO_ROOT / "episodes" / topic / "final" / "metadata.md"
    if meta_path.exists():
        text = meta_path.read_text()
        m = re.search(r'Top choice:\s*"(.+?)"', text)
        if m:
            return m.group(1)
    return f"Backbone: {topic.replace('-', ' ').title()}"


def find_cover_art(topic):
    for name in ["episode-cover.png", "cover.png", "cover.jpg"]:
        for d in [
            REPO_ROOT / "episodes" / topic / "assets" / "images",
            REPO_ROOT / "assets",
        ]:
            p = d / name
            if p.exists():
                return p
    return None


def ms_to_ffmpeg_time(ms):
    """Convert ms to HH:MM:SS.mmm format for ffmpeg."""
    hours = int(ms // 3600000)
    minutes = int((ms % 3600000) // 60000)
    seconds = (ms % 60000) / 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"


def generate_clip(topic, clip, mp3_path, cover_path, clips_dir, title):
    """Generate one clip in both landscape and portrait."""
    clip_id = clip["id"]
    start_ms = clip["start_ms"]
    end_ms = clip["end_ms"]
    duration_s = (end_ms - start_ms) / 1000

    start_time = ms_to_ffmpeg_time(start_ms)
    duration_str = f"{duration_s:.3f}"

    print(f"\n  Clip {clip_id}: {duration_s:.0f}s ({start_time})")

    for orientation, dims, suffix in [
        ("landscape", LANDSCAPE, ""),
        ("portrait", PORTRAIT, "-vert"),
    ]:
        output_name = f"clip-{clip_id:02d}{suffix}.mp4"
        output_path = clips_dir / output_name

        w, h = dims["w"], dims["h"]
        wave_h = 150 if orientation == "landscape" else 200
        wave_y = h - wave_h - 40

        # Build filter
        filters = []

        if cover_path:
            input_args = ["-loop", "1", "-i", str(cover_path)]
            filters.append(f"[0:v]scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=#{BG_COLOR}[bg]")
            audio_ref = "1:a"
        else:
            input_args = []
            filters.append(f"color=c=#{BG_COLOR}:s={w}x{h}:r={FPS}[bg]")
            audio_ref = "0:a"

        # Waveform
        filters.append(f"[{audio_ref}]showwaves=s={w}x{wave_h}:mode=cline:rate={FPS}:colors={WAVEFORM_COLOR}[wave]")
        filters.append(f"[bg][wave]overlay=0:{wave_y}[v1]")

        # Title
        escaped_title = title.replace("'", "'\\''").replace(":", "\\:")
        font_size = 36 if orientation == "landscape" else 32
        title_y = 60 if orientation == "landscape" else 100
        filters.append(
            f"[v1]drawtext=text='{escaped_title}'"
            f":fontsize={font_size}:fontcolor=white"
            f":x=(w-text_w)/2:y={title_y}"
            f":shadowcolor=black:shadowx=2:shadowy=2[v2]"
        )

        # Backbone branding
        filters.append(
            f"[v2]drawtext=text='Backbone\\: From Breakthrough to Built-In'"
            f":fontsize=22:fontcolor=0xcccccc"
            f":x=(w-text_w)/2:y={title_y + font_size + 15}[vout]"
        )

        filter_graph = ";".join(filters)

        cmd = [
            "ffmpeg", "-y",
            "-ss", start_time, "-t", duration_str,
            *input_args,
            "-ss", start_time, "-t", duration_str,
            "-i", str(mp3_path),
            "-filter_complex", filter_graph,
            "-map", "[vout]",
            "-map", f"{audio_ref.split(':')[0]}:a",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-shortest",
            "-movflags", "+faststart",
            str(output_path),
        ]

        subprocess.run(cmd, capture_output=True, text=True, check=True)
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"    {orientation}: {output_name} ({size_mb:.1f} MB)")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate clip videos")
    parser.add_argument("topic", help="Episode topic")
    parser.add_argument("--clip", type=int, help="Generate specific clip number only")
    parser.add_argument("--approved-only", action="store_true", help="Only generate approved clips")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not check_ffmpeg():
        sys.exit(1)

    episode_dir = REPO_ROOT / "episodes" / args.topic
    clips_dir = episode_dir / "assets" / "clips"
    manifest_path = clips_dir / "clip-manifest.json"
    mp3_path = episode_dir / "final" / "episode.mp3"

    if not manifest_path.exists():
        print(f"Error: {manifest_path} not found. Run clip_selector.py first.")
        sys.exit(1)
    if not mp3_path.exists():
        print(f"Error: {mp3_path} not found. Run audio_assemble.py first.")
        sys.exit(1)

    manifest = json.loads(manifest_path.read_text())
    clips = manifest.get("clips", [])
    title = load_metadata_title(args.topic)
    cover = find_cover_art(args.topic)

    # Filter clips
    if args.clip:
        clips = [c for c in clips if c["id"] == args.clip]
        if not clips:
            print(f"Error: clip {args.clip} not found in manifest")
            sys.exit(1)
    if args.approved_only:
        clips = [c for c in clips if c.get("approved", False)]
        if not clips:
            print("No approved clips. Edit clip-manifest.json and set 'approved: true'.")
            sys.exit(1)

    print(f"Generating {len(clips)} clip(s) for '{title}'")
    if cover:
        print(f"Cover: {cover}")

    if args.dry_run:
        for c in clips:
            print(f"  Clip {c['id']}: {c['duration_s']}s — {c.get('preview', '')[:80]}...")
        print("\n[dry run]")
        return

    for clip in clips:
        try:
            generate_clip(args.topic, clip, mp3_path, cover, clips_dir, title)
        except subprocess.CalledProcessError as e:
            print(f"  Error generating clip {clip['id']}: {e.stderr[:300] if e.stderr else e}")

    print(f"\nDone. Clips in {clips_dir}")


if __name__ == "__main__":
    main()
