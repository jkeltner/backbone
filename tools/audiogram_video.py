#!/usr/bin/env python3
"""
audiogram_video.py — Generate full-episode audiogram video for YouTube

Composites a darkened background template + waveform visualizer + episode title +
chapter overlays + burned-in subtitles into a video backed by the episode audio.

Output: episodes/{topic}/assets/video/episode-full.mp4

Usage:
  python tools/audiogram_video.py refrigeration
  python tools/audiogram_video.py refrigeration --preview           # 10-sec clip for quick iteration
  python tools/audiogram_video.py refrigeration --cover path/to/bg.png
  python tools/audiogram_video.py refrigeration --title-font "Futura"
  python tools/audiogram_video.py refrigeration --no-subs
  python tools/audiogram_video.py refrigeration --dry-run

Requires: ffmpeg on PATH (with freetype + libass for text/subtitles)
"""

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

# ── Video settings ──
WIDTH = 1920
HEIGHT = 1080
FPS = 30

# ── Font defaults ──
# Override any of these with --title-font, --subtitle-font, --chapter-font
# Available on macOS: Avenir Next, Futura, DIN Alternate, Helvetica Neue, etc.
TITLE_FONT = "Avenir Next Demi Bold"
TITLE_FONT_SIZE = 52
SUBTITLE_FONT = "Avenir Next"
SUBTITLE_FONT_SIZE = 28
CHAPTER_FONT = "Avenir Next Medium"
CHAPTER_FONT_SIZE = 36
SUB_FONT = "Avenir Next"
SUB_FONT_SIZE = 22

# ── Waveform settings — white, bottom of frame, fully opaque ──
WAVEFORM_HEIGHT = 300
WAVEFORM_COLOR = "0xFFFFFF"
WAVEFORM_MODE = "p2p"          # point-to-point (filled, high visibility)
WAVEFORM_Y_OFFSET = 40         # px from bottom of frame
WAVEFORM_OPACITY = 1.0

# ── Background processing ──
BG_FALLBACK_COLOR = "0a0a1e"   # solid color when no image found


def check_ffmpeg():
    """Verify ffmpeg is available."""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("Error: ffmpeg not found. Install via: brew install ffmpeg")
        return False


def has_filter(name):
    """Check if ffmpeg has a specific filter."""
    result = subprocess.run(["ffmpeg", "-filters"], capture_output=True, text=True)
    return name in result.stdout


def load_metadata_title(topic):
    """Get episode title from metadata."""
    meta_path = REPO_ROOT / "episodes" / topic / "final" / "metadata.md"
    if meta_path.exists():
        text = meta_path.read_text()
        m = re.search(r'Top choice:\s*"(.+?)"', text)
        if m:
            return m.group(1)
    return f"Backbone: {topic.replace('-', ' ').title()}"


def load_chapters(topic):
    """Load chapter data for overlay text."""
    chapters_path = REPO_ROOT / "episodes" / topic / "final" / "chapters.json"
    if chapters_path.exists():
        data = json.loads(chapters_path.read_text())
        return data.get("chapters", [])
    return []


def find_background_image(topic, override=None):
    """Find background image. Priority: --cover > episode-specific > promo > cover_art."""
    if override and Path(override).exists():
        return Path(override)

    episode_cover = REPO_ROOT / "episodes" / topic / "assets" / "images" / "episode-cover.png"
    if episode_cover.exists():
        return episode_cover

    audiogram_bg = REPO_ROOT / "assets" / "audiogram_background.png"
    if audiogram_bg.exists():
        return audiogram_bg

    for name in ["promo_image.png", "promo_image.jpg", "cover_art.png", "cover_art.jpg"]:
        p = REPO_ROOT / "assets" / name
        if p.exists():
            return p

    return None


def escape_drawtext(text):
    """Escape text for ffmpeg drawtext filter."""
    return text.replace("\\", "\\\\").replace("'", "'\\''").replace(":", "\\:")


def generate_audiogram(topic, dry_run=False, cover_path=None, burn_subs=True,
                       title_font=None, subtitle_font=None, chapter_font=None,
                       preview=False, audio_path=None):
    """Generate audiogram video."""
    if not check_ffmpeg():
        sys.exit(1)

    episode_dir = REPO_ROOT / "episodes" / topic

    if audio_path:
        mp3_path = Path(audio_path)
    else:
        mp3_path = episode_dir / "final" / "episode.mp3"
    srt_path = episode_dir / "final" / "transcript.srt"

    if not mp3_path.exists():
        print(f"Error: {mp3_path} not found. Run audio_assemble.py first.")
        sys.exit(1)

    title = load_metadata_title(topic)
    chapters = load_chapters(topic)
    bg_image = find_background_image(topic, cover_path)

    # Resolve fonts (CLI overrides > defaults)
    t_font = title_font or TITLE_FONT
    s_font = subtitle_font or SUBTITLE_FONT
    c_font = chapter_font or CHAPTER_FONT

    use_drawtext = has_filter("drawtext")
    use_subtitles = burn_subs and srt_path.exists() and has_filter("subtitles")

    if not use_drawtext:
        print("Note: drawtext filter not available — install ffmpeg with freetype")
    if burn_subs and not srt_path.exists():
        print("Note: no transcript.srt — run generate_transcript.py for subtitles")
    if burn_subs and srt_path.exists() and not has_filter("subtitles"):
        print("Note: subtitles filter not available (needs libass)")

    # Output path
    video_dir = episode_dir / "assets" / "video"
    video_dir.mkdir(parents=True, exist_ok=True)
    if preview:
        out_name = "preview.mp4"
    elif audio_path and "wave-" in Path(audio_path).name:
        # Derive output name from wave audio file (e.g. episode-wave-00.mp3 → wave-00.mp4)
        stem = Path(audio_path).stem  # e.g. "episode-wave-00"
        out_name = f"{stem}.mp4"
    else:
        out_name = "episode-full.mp4"
    output_path = video_dir / out_name

    print(f"Title:      {title}")
    print(f"Audio:      {mp3_path}")
    print(f"Background: {bg_image or '(solid color)'}")
    print(f"Chapters:   {len(chapters)}")
    print(f"Fonts:      title='{t_font}', sub='{s_font}', chapter='{c_font}'")
    print(f"Subtitles:  {'yes' if use_subtitles else 'no'}")
    print(f"Output:     {output_path}{' (preview)' if preview else ''}")

    if dry_run:
        print("\n[dry run] Would generate audiogram video.")
        return

    # ── Build ffmpeg filter graph ──
    filter_parts = []

    if bg_image:
        # Scale + crop to fill frame (no darkening — image looks great as-is)
        filter_parts.append(
            f"[0:v]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={WIDTH}:{HEIGHT}"
            f"[bg]"
        )
        audio_input = "1:a"
    else:
        filter_parts.append(
            f"color=c=#{BG_FALLBACK_COLOR}:s={WIDTH}x{HEIGHT}:r={FPS}[bg]"
        )
        audio_input = "0:a"

    # Waveform — white, bottom of frame, fully opaque
    wave_y = HEIGHT - WAVEFORM_HEIGHT - WAVEFORM_Y_OFFSET
    filter_parts.append(
        f"[{audio_input}]showwaves=s={WIDTH}x{WAVEFORM_HEIGHT}"
        f":mode={WAVEFORM_MODE}:rate={FPS}:colors={WAVEFORM_COLOR}"
        f":scale=sqrt"
        f"[wave]"
    )
    if WAVEFORM_OPACITY < 1.0:
        filter_parts.append(
            f"[wave]format=rgba,colorchannelmixer=aa={WAVEFORM_OPACITY}[wave_a]"
        )
        filter_parts.append(f"[bg][wave_a]overlay=0:{wave_y}[vout]")
    else:
        filter_parts.append(f"[bg][wave]overlay=0:{wave_y}[vout]")

    if use_drawtext:
        filter_parts[-1] = filter_parts[-1].replace("[vout]", "[v1]")

        # Episode title — left-aligned, mid-height
        escaped_title = escape_drawtext(title)
        title_y = HEIGHT // 2 - TITLE_FONT_SIZE
        filter_parts.append(
            f"[v1]drawtext=text='{escaped_title}'"
            f":font='{t_font}':fontsize={TITLE_FONT_SIZE}:fontcolor=white"
            f":x=80:y={title_y}"
            f":shadowcolor=black@0.6:shadowx=3:shadowy=3"
            f"[v2]"
        )
        last_output = "v2"

        # Burn in subtitles from SRT
        if use_subtitles:
            next_output = f"{last_output}_sub"
            srt_escaped = str(srt_path).replace("\\", "\\\\").replace(":", "\\:").replace("'", "'\\''")
            sub_style = (
                f"FontName={subtitle_font or SUB_FONT},"
                f"FontSize={SUB_FONT_SIZE},"
                "PrimaryColour=&H00FFFFFF,"
                "BackColour=&H80000000,"
                "BorderStyle=4,"
                "Outline=0,"
                "Shadow=0,"
                "MarginV=480"
            )
            filter_parts.append(
                f"[{last_output}]subtitles='{srt_escaped}'"
                f":force_style='{sub_style}'"
                f"[{next_output}]"
            )
            last_output = next_output

        # Final output label
        filter_parts[-1] = filter_parts[-1].rsplit("[", 1)[0] + "[vout]"

    elif use_subtitles:
        filter_parts[-1] = filter_parts[-1].replace("[vout]", "[v_pre]")
        srt_escaped = str(srt_path).replace("\\", "\\\\").replace(":", "\\:").replace("'", "'\\''")
        sub_style = (
            f"FontName={SUB_FONT},"
            f"FontSize={SUB_FONT_SIZE},"
            "PrimaryColour=&H00FFFFFF,"
            "BackColour=&H80000000,"
            "BorderStyle=4,"
            "Outline=0,"
            "Shadow=0,"
            "MarginV=480"
        )
        filter_parts.append(
            f"[v_pre]subtitles='{srt_escaped}'"
            f":force_style='{sub_style}'"
            f"[vout]"
        )

    filter_graph = ";".join(filter_parts)

    # ── Build ffmpeg command ──
    cmd = ["ffmpeg", "-y"]

    # Input sources — for preview, seek 60s into the audio
    if preview and bg_image:
        cmd += ["-loop", "1", "-i", str(bg_image),
                "-ss", "60", "-i", str(mp3_path)]
    elif preview:
        cmd += ["-ss", "60", "-i", str(mp3_path)]
    elif bg_image:
        cmd += ["-loop", "1", "-i", str(bg_image), "-i", str(mp3_path)]
    else:
        cmd += ["-i", str(mp3_path)]

    cmd += [
        "-filter_complex", filter_graph,
        "-map", "[vout]",
        "-map", f"{audio_input.split(':')[0]}:a",
        "-c:v", "libx264",
        "-preset", "ultrafast" if preview else "medium",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-movflags", "+faststart",
    ]

    if preview:
        cmd += ["-t", "10"]

    cmd.append(str(output_path))

    label = "preview clip" if preview else "video"
    print(f"\nGenerating {label}...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error: ffmpeg failed:\n{result.stderr[-2000:]}")
        sys.exit(1)

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"Done: {output_path} ({size_mb:.1f} MB)")
    return output_path


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate audiogram video")
    parser.add_argument("topic", help="Episode topic")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--preview", action="store_true",
                        help="10-sec clip from 60s in — fast iteration on visual design")
    parser.add_argument("--cover", help="Path to background template image")
    parser.add_argument("--audio", help="Path to audio file (default: final/episode.mp3)")
    parser.add_argument("--no-subs", action="store_true", help="Skip subtitle burn-in")
    parser.add_argument("--title-font",
                        help=f"Font for episode title (default: {TITLE_FONT})")
    parser.add_argument("--subtitle-font",
                        help=f"Font for show subtitle line (default: {SUBTITLE_FONT})")
    parser.add_argument("--chapter-font",
                        help=f"Font for chapter title overlays (default: {CHAPTER_FONT})")
    args = parser.parse_args()

    generate_audiogram(
        args.topic,
        dry_run=args.dry_run,
        cover_path=args.cover,
        burn_subs=not args.no_subs,
        audio_path=args.audio,
        title_font=args.title_font,
        subtitle_font=args.subtitle_font,
        chapter_font=args.chapter_font,
        preview=args.preview,
    )


if __name__ == "__main__":
    main()
