#!/usr/bin/env python3
"""
audio_assemble.py — Backbone Audio Assembly

Stitches per-wave TTS audio files + music into a single episode.mp3 with
crossfades. Also produces a position map (assembly-map.json) used by
timestamp_chapters to locate content by time offset.

Usage:
  python tools/audio_assemble.py refrigeration                  # use _v4 wave files (release model, default)
  python tools/audio_assemble.py refrigeration --model v3       # use _v3 wave files (comparison)
  python tools/audio_assemble.py refrigeration --model v2       # use _v2 wave files (comparison)
  python tools/audio_assemble.py refrigeration --model default  # use unsuffixed wave files
  python tools/audio_assemble.py refrigeration --clone ivc      # use *_ivc wave files (instant clones)
  python tools/audio_assemble.py refrigeration --dry-run        # show plan, don't assemble
  python tools/audio_assemble.py refrigeration --no-music       # skip music (no music files yet)

Requires: pydub (pip install pydub), ffmpeg on PATH

Config (set in .env or pipeline/config.py):
  THEME_MUSIC       — path to theme-in (intro) music file (relative to repo root)
  THEME_OUT_MUSIC   — path to theme-out (outro) music file; falls back to THEME_MUSIC
  TRANSITION_BUMPER — path to bumper file
  THEME_OUT_FADE_MS — fade applied to the end of theme-out (short: the v2 outro has a composed ending)
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
THEME_OUT_FADE_MS = 500  # v2 outro (Music v2.5) resolves on its own; this only smooths the tail

# Loudness normalization target (EBU R128, standard for podcasts)
TARGET_LUFS = -16

# Music cue pattern
MUSIC_CUE_RE = re.compile(r"^\[MUSIC:\s*(.+?)\]$")
SEGMENT_BREAK_RE = re.compile(r"^---\s*SEGMENT BREAK:.*---$")
FRONT_MATTER_RE = re.compile(r"^---\s*$")


def load_config():
    """Load music config from .env or defaults."""
    config = {
        "theme_music": os.environ.get("THEME_MUSIC", "assets/music/intro_v2.mp3"),
        "theme_out_music": os.environ.get("THEME_OUT_MUSIC") or os.environ.get("THEME_MUSIC", "assets/music/outro_v2.mp3"),
        "transition_bumper": os.environ.get("TRANSITION_BUMPER", "assets/music/bumper_v2.mp3"),
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
        ["ffmpeg", "-nostats", "-i", str(file_path), "-af", "ebur128", "-f", "null", "/dev/null"],
        capture_output=True, text=True,
    )
    # Parse the summary block ("Integrated loudness: I: -21.4 LUFS"). Take the LAST match:
    # with framelog=verbose ffmpeg also prints per-frame "I:" lines and the first one
    # (at t≈0.1s) reads -70 LUFS, which once drove a +54 dB gain into clipping.
    value = None
    for line in result.stderr.splitlines():
        m = re.search(r"\bI:\s*(-?\d+\.?\d*)\s*LUFS", line)
        if m:
            value = float(m.group(1))
    if value is not None and value <= -60:
        return None  # effectively silence / measurement failure — don't "normalize" it
    return value


TARGET_TRUE_PEAK = -1.5  # dBTP ceiling for podcast delivery


def finalize_loudness(mp3_path):
    """Two-pass ffmpeg loudnorm on the assembled episode: integrated -16 LUFS, true peak -1.5 dBTP.

    Pass 1 measures; pass 2 applies loudnorm with the measured values so the gain is linear
    (no pumping) wherever the true-peak ceiling allows. Overwrites mp3_path.
    """
    import json as _json
    import subprocess
    import tempfile
    measure = subprocess.run(
        ["ffmpeg", "-nostats", "-i", str(mp3_path), "-af",
         f"loudnorm=I={TARGET_LUFS}:TP={TARGET_TRUE_PEAK}:LRA=11:print_format=json",
         "-f", "null", "/dev/null"],
        capture_output=True, text=True,
    )
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", measure.stderr, re.S)
    if not m:
        print("  WARNING: loudnorm measurement failed; leaving loudness as assembled")
        return None
    stats = _json.loads(m.group(0))
    print(f"  Loudness before: {float(stats['input_i']):.1f} LUFS, true peak {float(stats['input_tp']):.1f} dBTP")
    tmp = Path(tempfile.mkstemp(suffix=".mp3", dir=str(Path(mp3_path).parent))[1])
    filt = (f"loudnorm=I={TARGET_LUFS}:TP={TARGET_TRUE_PEAK}:LRA=11:"
            f"measured_I={stats['input_i']}:measured_TP={stats['input_tp']}:"
            f"measured_LRA={stats['input_lra']}:measured_thresh={stats['input_thresh']}:"
            f"offset={stats['target_offset']}:linear=true:print_format=summary")
    apply = subprocess.run(
        ["ffmpeg", "-nostats", "-y", "-i", str(mp3_path), "-af", filt,
         "-ar", "44100", "-b:a", "128k", str(tmp)],
        capture_output=True, text=True,
    )
    if apply.returncode != 0 or not tmp.exists():
        print(f"  WARNING: loudnorm apply failed: {apply.stderr[-300:]}")
        tmp.unlink(missing_ok=True)
        return None
    tmp.replace(mp3_path)
    os.chmod(mp3_path, 0o644)  # mkstemp creates 0600; the episode must be readable by upload/Descript
    after = measure_lufs(mp3_path)
    print(f"  Loudness after:  {after:.1f} LUFS (target {TARGET_LUFS}, ceiling {TARGET_TRUE_PEAK} dBTP)" if after is not None else "  Loudness after: (unmeasured)")
    return after


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
                segments.append({"type": "wave", "index": wave_index})
                wave_index += 1
            segments.append({"type": "music", "cue": music_match.group(1)})
            has_content = False
        else:
            if line_stripped:
                has_content = True

    if has_content:
        segments.append({"type": "wave", "index": wave_index})

    # The wave naming convention from tts_dialogue.py:
    # wave-00-opening, wave-01, wave-02, ..., wave-NN-built-in
    # Music cues split the script: content before theme-in is wave-00,
    # between theme-in and first bumper is wave-01, etc.
    # But we don't need to re-derive names — we discover them from files.

    return segments


def discover_wave_files(audio_dir, model_suffix=""):
    """Find wave audio files in the audio directory.

    Returns dict mapping wave index to file path.
    model_suffix: "" for default, "_v2" / "_v3" / "_v4" for that model.
    """
    waves = {}
    if model_suffix:
        # Match files with this specific suffix: wave-00-opening_v4.mp3
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
    if cue_name == "theme-in":
        path = REPO_ROOT / config["theme_music"]
    elif cue_name == "theme-out":
        path = REPO_ROOT / config["theme_out_music"]
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

    # Every wave the script implies must exist — a missing render must never assemble silently.
    script_waves = [seg["index"] for seg in segments if seg["type"] == "wave"]
    missing = [i for i in script_waves if i not in waves]
    if missing and wave_filter is None:
        print(f"\nError: wave file(s) missing for wave index {missing} — TTS did not render them.")
        print(f"       Run: python tools/tts_dialogue.py {topic} --wave N  (for each N), then re-assemble.")
        sys.exit(1)

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
        print("Finalizing loudness (two-pass loudnorm)...")
        finalize_loudness(output_path)
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
    load_dotenv()  # before argparse so VOICE_CLONE from .env can seed --clone's default

    parser = argparse.ArgumentParser(description="Assemble Backbone episode audio")
    parser.add_argument("topic", help="Episode topic (directory name under episodes/)")
    parser.add_argument(
        "--model",
        choices=["v2", "v3", "v4", "default"],
        default="v4",
        help="Which wave files to use (v4: _v4 [default, release model], v3: _v3, v2: _v2, default: no suffix)",
    )
    parser.add_argument("--clone", choices=["pvc", "ivc", "stock"],
                        default=os.environ.get("VOICE_CLONE", "pvc").lower(),
                        help="Which voice's wave files to use: pvc (no extra suffix, default), "
                             "ivc (files ending _ivc) or stock (files ending _stock). "
                             "Default comes from VOICE_CLONE in .env.")
    parser.add_argument("--wave", type=int, metavar="N",
                        help="Only assemble wave N (0=opening). Output: episode-wave-NN.mp3")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without assembling")
    parser.add_argument("--no-music", action="store_true", help="Skip music (insert silence instead)")
    args = parser.parse_args()

    suffix_map = {"default": "", "v2": "_v2", "v3": "_v3", "v4": "_v4"}
    model_suffix = suffix_map[args.model] + ("" if args.clone == "pvc" else f"_{args.clone}")

    assemble(args.topic, model_suffix=model_suffix, dry_run=args.dry_run,
             no_music=args.no_music, wave_filter=args.wave)


if __name__ == "__main__":
    main()
