#!/usr/bin/env python3
"""
audio_assemble.py — Backbone Audio Assembly

Stitches per-wave TTS audio files + music into a single episode.mp3 with
crossfades. Also produces a position map (assembly-map.json) used by
downstream tools (timestamp_chapters, clip_generate) to locate content
by time offset.

Usage:
  python tools/audio_assemble.py refrigeration
  python tools/audio_assemble.py refrigeration --model v3       # use _v3 wave files (archived)
  python tools/audio_assemble.py refrigeration --model default  # use unsuffixed wave files
  python tools/audio_assemble.py refrigeration --dry-run        # show plan, don't assemble
  python tools/audio_assemble.py refrigeration --no-music       # skip music (no music files yet)

Requires: pydub (pip install pydub), ffmpeg on PATH

Config (set in .env or pipeline/config.py):
  THEME_MUSIC       — path to theme music file (relative to repo root)
  TRANSITION_BUMPER — path to bumper file
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

# Assembly parameters (from tts-pipeline.md)
CROSSFADE_THEME_MS = 500
CROSSFADE_BUMPER_MS = 300
THEME_OUT_FADE_MS = 3000

# Loudness normalization target (EBU R128, standard for podcasts)
TARGET_LUFS = -16

# Music cue pattern
MUSIC_CUE_RE = re.compile(r"^\[MUSIC:\s*(.+?)\]$")
SEGMENT_BREAK_RE = re.compile(r"^---\s*SEGMENT BREAK:.*---$")
FRONT_MATTER_RE = re.compile(r"^---\s*$")


def load_config():
    """Load music config from .env or defaults."""
    config = {
        "theme_music": os.environ.get("THEME_MUSIC", "assets/music/backbone-theme.mp3"),
        "transition_bumper": os.environ.get("TRANSITION_BUMPER", "assets/music/backbone-bumper.mp3"),
        "theme_out_fade_ms": int(os.environ.get("THEME_OUT_FADE_MS", THEME_OUT_FADE_MS)),
    }
    return config


def load_id3_tags(topic):
    """Build ID3 tag dict from metadata.md for the full episode MP3."""
    from datetime import datetime
    tags = {
        "artist": "Jeff Keltner & Cyrus Mistry",
        "album_artist": "Backbone",
        "album": "Backbone: From Breakthrough to Built-In",
        "genre": "Podcast",
        "year": str(datetime.now().year),
        "title": f"Backbone: {topic.replace('-', ' ').title()}",
        "track": "1",
    }
    meta_path = REPO_ROOT / "episodes" / topic / "final" / "metadata.md"
    if meta_path.exists():
        text = meta_path.read_text()
        m = re.search(r'Top choice:\s*"(.+?)"', text)
        if m:
            tags["title"] = m.group(1)
        m = re.search(r"^##\s*Episode Number\s*\n+\**(\d+)\**", text, re.MULTILINE)
        if m:
            tags["track"] = m.group(1)
    return tags


def find_cover_art():
    """Return path to show cover art if present, else None."""
    for candidate in ("assets/show_cover_art.png", "assets/show_cover_art.jpg",
                      "assets/cover_art.png", "assets/cover_art.jpg",
                      "assets/cover.png", "assets/cover.jpg",
                      "assets/show-cover.png"):
        p = REPO_ROOT / candidate
        if p.exists():
            return str(p)
    return None


def write_id3_tags(mp3_path, tags, cover_path=None):
    """Write ID3v2.4 tags + optional cover art to an MP3 using mutagen.

    pydub's tags=/cover= export kwargs don't reliably write ID3 frames to
    MP3 output, so we tag after export. This is the standard pattern.
    """
    from mutagen.id3 import (
        ID3, ID3NoHeaderError,
        TIT2, TPE1, TPE2, TALB, TCON, TDRC, TRCK, APIC,
    )

    try:
        id3 = ID3(mp3_path)
    except ID3NoHeaderError:
        id3 = ID3()

    frame_map = {
        "title": TIT2,
        "artist": TPE1,
        "album_artist": TPE2,
        "album": TALB,
        "genre": TCON,
        "year": TDRC,
        "track": TRCK,
    }
    for key, frame_cls in frame_map.items():
        if key in tags and tags[key]:
            id3.add(frame_cls(encoding=3, text=str(tags[key])))

    if cover_path:
        cover_p = Path(cover_path)
        mime = "image/png" if cover_p.suffix.lower() == ".png" else "image/jpeg"
        id3.add(APIC(
            encoding=3, mime=mime, type=3,  # type 3 = front cover
            desc="Cover", data=cover_p.read_bytes(),
        ))

    id3.save(mp3_path, v2_version=4)


def measure_lufs(file_path):
    """Measure integrated loudness (LUFS) of an audio file using ffmpeg."""
    import subprocess
    result = subprocess.run(
        ["ffmpeg", "-i", str(file_path), "-af", "ebur128=framelog=verbose", "-f", "null", "/dev/null"],
        capture_output=True, text=True,
    )
    # Parse the summary line: "I: -21.4 LUFS"
    for line in result.stderr.splitlines():
        if "I:" in line and "LUFS" in line:
            m = re.search(r"I:\s*(-?\d+\.?\d*)\s*LUFS", line)
            if m:
                return float(m.group(1))
    return None


def normalize_audio(audio_segment, file_path):
    """Normalize an AudioSegment to TARGET_LUFS using measured loudness."""
    current_lufs = measure_lufs(file_path)
    if current_lufs is None:
        print(f"(could not measure LUFS, skipping normalization)", end=" ")
        return audio_segment
    adjustment = TARGET_LUFS - current_lufs
    print(f"(LUFS: {current_lufs:.1f}, adjusting {adjustment:+.1f} dB)", end=" ")
    return audio_segment.apply_gain(adjustment)


def load_dotenv():
    """Load .env file if present."""
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


def parse_assembled_script(script_path):
    """Parse assembled.txt into an ordered list of segments.

    Returns list of dicts:
      {"type": "wave", "name": "wave-00-opening", "index": 0}
      {"type": "music", "cue": "theme-in"}
    """
    text = script_path.read_text()
    lines = text.splitlines()

    # Strip front matter
    if lines and lines[0].strip() == "---":
        end_idx = None
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end_idx = i
                break
        if end_idx:
            lines = lines[end_idx + 1 :]

    segments = []
    wave_index = 0

    # Split on music cues — content between cues is a wave
    has_content = False

    for line in lines:
        line_stripped = line.strip()

        # Skip segment breaks (internal editorial markers)
        if SEGMENT_BREAK_RE.match(line_stripped):
            continue

        music_match = MUSIC_CUE_RE.match(line_stripped)
        if music_match:
            if has_content:
                # Close the current wave
                wave_index += 1
            segments.append({"type": "music", "cue": music_match.group(1)})
            has_content = False
        else:
            if line_stripped:
                has_content = True

    # The wave naming convention from tts_dialogue.py:
    # wave-00-opening, wave-01, wave-02, ..., wave-NN-built-in
    # Music cues split the script: content before theme-in is wave-00,
    # between theme-in and first bumper is wave-01, etc.
    # But we don't need to re-derive names — we discover them from files.

    return segments


def discover_wave_files(audio_dir, model_suffix=""):
    """Find wave audio files in the audio directory.

    Returns dict mapping wave index to file path.
    model_suffix: "" for default, "_v2" for v2, "_v3" for v3.
    """
    waves = {}
    if model_suffix:
        # Match files with this specific suffix: wave-00-opening_v3.mp3
        pattern = re.compile(r"wave-(\d+)(?:-[a-z-]+)?" + re.escape(model_suffix) + r"\.mp3$")
    else:
        # Match files without any model suffix: wave-00-opening.mp3 (not _v2/_v3)
        pattern = re.compile(r"wave-(\d+)(?:-[a-z-]+)?\.mp3$")

    for f in sorted(audio_dir.iterdir()):
        if f.is_file():
            m = pattern.match(f.name)
            if m:
                idx = int(m.group(1))
                waves[idx] = f

    return waves


def resolve_music_file(cue_name, config):
    """Resolve a music cue name to a file path."""
    if cue_name in ("theme-in", "theme-out"):
        path = REPO_ROOT / config["theme_music"]
    elif cue_name == "transition-bumper":
        if config["transition_bumper"]:
            path = REPO_ROOT / config["transition_bumper"]
        else:
            return None  # No bumper file yet
    else:
        return None

    if path.exists():
        return path
    return None


def assemble(topic, model_suffix="", dry_run=False, no_music=False, wave_filter=None):
    """Assemble wave files + music into episode.mp3.

    wave_filter: if set, only include this wave index (and its surrounding music cues).
    Output goes to episode-wave-NN.mp3 instead of episode.mp3.
    """
    episode_dir = REPO_ROOT / "episodes" / topic
    audio_dir = episode_dir / "assets" / "audio"
    final_dir = episode_dir / "final"
    script_path = final_dir / "assembled.txt"

    if not script_path.exists():
        print(f"Error: {script_path} not found")
        sys.exit(1)

    if not audio_dir.exists():
        print(f"Error: {audio_dir} not found")
        sys.exit(1)

    config = load_config()

    # Parse script to get segment ordering
    segments = parse_assembled_script(script_path)

    # Discover wave files
    waves = discover_wave_files(audio_dir, model_suffix)
    if not waves:
        print(f"Error: no wave files found in {audio_dir} with suffix '{model_suffix}'")
        print(f"Available files: {[f.name for f in audio_dir.iterdir() if f.suffix == '.mp3']}")
        sys.exit(1)

    print(f"Found {len(waves)} wave files:")
    for idx in sorted(waves):
        f = waves[idx]
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"  [{idx}] {f.name} ({size_mb:.1f} MB)")

    # Build assembly plan: ordered list of audio operations
    plan = []
    wave_idx = 0

    # First wave (before first music cue, or if no music cues, all content)
    if wave_idx in waves:
        plan.append({"type": "wave", "index": wave_idx, "file": waves[wave_idx]})

    for seg in segments:
        if seg["type"] == "music":
            cue = seg["cue"]
            if no_music:
                # Insert a short silence instead of music
                plan.append({"type": "silence", "duration_ms": 1500, "cue": cue})
            else:
                music_file = resolve_music_file(cue, config)
                if music_file:
                    plan.append({"type": "music", "cue": cue, "file": music_file})
                else:
                    print(f"  Warning: no music file for cue [{cue}], inserting 1.5s silence")
                    plan.append({"type": "silence", "duration_ms": 1500, "cue": cue})

            # Next wave after this music cue
            wave_idx += 1
            if wave_idx in waves:
                plan.append({"type": "wave", "index": wave_idx, "file": waves[wave_idx]})

    # Filter to a single wave if requested
    if wave_filter is not None:
        filtered = []
        include_next_music = False
        for step in plan:
            if step["type"] == "wave" and step["index"] == wave_filter:
                filtered.append(step)
                include_next_music = True
            elif step["type"] == "wave":
                include_next_music = False
            elif step["type"] in ("music", "silence") and include_next_music:
                filtered.append(step)
                include_next_music = False
            elif step["type"] in ("music", "silence") and not filtered:
                # Music before the target wave — skip
                pass
            elif step["type"] in ("music", "silence") and filtered and filtered[-1]["type"] != "wave":
                # Music after the trailing music — stop
                pass
        plan = filtered

    print(f"\nAssembly plan ({len(plan)} segments):")
    for i, step in enumerate(plan):
        if step["type"] == "wave":
            print(f"  {i+1}. Wave {step['index']}: {step['file'].name}")
        elif step["type"] == "music":
            print(f"  {i+1}. Music: [{step['cue']}] → {step['file'].name}")
        elif step["type"] == "silence":
            print(f"  {i+1}. Silence: {step['duration_ms']}ms (placeholder for [{step['cue']}])")

    if dry_run:
        print("\n[dry run] Skipping assembly.")
        return

    # Assemble audio
    from pydub import AudioSegment

    print("\nAssembling audio...")
    result = AudioSegment.empty()
    position_map = []  # Track positions for downstream tools

    for step in plan:
        offset_ms = len(result)

        if step["type"] == "wave":
            print(f"  Loading wave {step['index']}...", end=" ", flush=True)
            wave_audio = AudioSegment.from_mp3(str(step["file"]))
            wave_audio = normalize_audio(wave_audio, step["file"])
            duration_s = len(wave_audio) / 1000
            print(f"({duration_s:.1f}s)")

            position_map.append({
                "type": "wave",
                "index": step["index"],
                "file": step["file"].name,
                "start_ms": offset_ms,
                "end_ms": offset_ms + len(wave_audio),
            })
            result += wave_audio

        elif step["type"] == "music":
            print(f"  Loading music [{step['cue']}]...", end=" ", flush=True)
            music_audio = AudioSegment.from_mp3(str(step["file"]))

            if step["cue"] == "theme-out":
                music_audio = music_audio.fade_out(config["theme_out_fade_ms"])
                # Overlap theme-out with end of last spoken audio
                overlap_ms = min(CROSSFADE_THEME_MS, len(music_audio))
                result = result.append(music_audio, crossfade=overlap_ms)
            elif step["cue"] == "theme-in":
                overlap_ms = min(CROSSFADE_THEME_MS, len(music_audio))
                result = result.append(music_audio, crossfade=overlap_ms)
            elif step["cue"] == "transition-bumper":
                overlap_ms = min(CROSSFADE_BUMPER_MS, len(music_audio))
                result = result.append(music_audio, crossfade=overlap_ms)
            else:
                result += music_audio

            duration_s = len(music_audio) / 1000
            print(f"({duration_s:.1f}s)")

            position_map.append({
                "type": "music",
                "cue": step["cue"],
                "start_ms": offset_ms,
                "end_ms": len(result),
            })

        elif step["type"] == "silence":
            silence = AudioSegment.silent(duration=step["duration_ms"])
            position_map.append({
                "type": "silence",
                "cue": step.get("cue", ""),
                "start_ms": offset_ms,
                "end_ms": offset_ms + step["duration_ms"],
            })
            result += silence

    # Export
    if wave_filter is not None:
        output_path = final_dir / f"episode-wave-{wave_filter:02d}.mp3"
    else:
        output_path = final_dir / "episode.mp3"
    print(f"\nExporting to {output_path}...")
    result.export(str(output_path), format="mp3", bitrate="128k")

    if wave_filter is None:
        tags = load_id3_tags(topic)
        cover = find_cover_art()
        write_id3_tags(str(output_path), tags, cover_path=cover)
        print(f"  Wrote ID3 tags: title={tags['title']!r}, track={tags['track']}, year={tags['year']}")
        if cover:
            print(f"  Embedded cover art: {cover}")
        else:
            print("  (no cover art found in assets/ — skipping embed)")

    total_s = len(result) / 1000
    total_min = total_s / 60
    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"Done: {total_min:.1f} min ({total_s:.0f}s), {size_mb:.1f} MB")

    # Write position map for downstream tools
    map_path = final_dir / "assembly-map.json"
    map_data = {
        "topic": topic,
        "model_suffix": model_suffix,
        "total_duration_ms": len(result),
        "segments": position_map,
    }
    map_path.write_text(json.dumps(map_data, indent=2) + "\n")
    print(f"Position map: {map_path}")

    return output_path


def main():
    parser = argparse.ArgumentParser(description="Assemble Backbone episode audio")
    parser.add_argument("topic", help="Episode topic (directory name under episodes/)")
    parser.add_argument(
        "--model",
        choices=["v2", "v3", "default"],
        default="v2",
        help="Which wave files to use (v2: _v2 [default], v3: _v3, default: no suffix)",
    )
    parser.add_argument("--wave", type=int, metavar="N",
                        help="Only assemble wave N (0=opening). Output: episode-wave-NN.mp3")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without assembling")
    parser.add_argument("--no-music", action="store_true", help="Skip music (insert silence instead)")
    args = parser.parse_args()

    load_dotenv()

    suffix_map = {"default": "", "v2": "_v2", "v3": "_v3"}
    model_suffix = suffix_map[args.model]

    assemble(args.topic, model_suffix=model_suffix, dry_run=args.dry_run,
             no_music=args.no_music, wave_filter=args.wave)


if __name__ == "__main__":
    main()
