#!/usr/bin/env python3
"""
split_waves_to_cache.py — Split existing wave files into per-turn cache segments

Uses the script's turn structure + character-count proportional timing to split
each wave-XX_v2.mp3 into individual per-turn cache files. These can then be
re-concatenated with LUFS normalization via:

  python tools/tts_dialogue.py refrigeration --model v2 --reprocess

This avoids re-calling the ElevenLabs API just to fix volume normalization.

Usage:
  python tools/split_waves_to_cache.py refrigeration --model v2
  python tools/split_waves_to_cache.py refrigeration --model v2 --dry-run
"""

import re
import sys
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
AUDIO_TAG_RE = re.compile(
    r"\[(?:laughs?|pause|quietly|sighs?|clears throat|whispers?)[^\]]*\]\s*",
    re.IGNORECASE,
)


def strip_audio_tags(text):
    return AUDIO_TAG_RE.sub("", text).strip()


def parse_waves(script_path):
    """Parse assembled.txt into waves with per-turn text and character counts."""
    content = script_path.read_text(encoding="utf-8")
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            content = content[end + 3:].lstrip()

    items = []
    current_speaker = None
    current_lines = []

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if line.startswith("---") and "SEGMENT BREAK" in line:
            if current_speaker and current_lines:
                items.append({"type": "turn", "speaker": current_speaker,
                              "text": " ".join(current_lines).strip()})
                current_speaker, current_lines = None, []
            continue
        if re.match(r"^\[MUSIC:", line):
            if current_speaker and current_lines:
                items.append({"type": "turn", "speaker": current_speaker,
                              "text": " ".join(current_lines).strip()})
                current_speaker, current_lines = None, []
            items.append({"type": "music", "cue": line})
            continue
        m = re.match(r"^(JEFF|CYRUS):\s*(.*)", line)
        if m:
            if current_speaker and current_lines:
                items.append({"type": "turn", "speaker": current_speaker,
                              "text": " ".join(current_lines).strip()})
            current_speaker = m.group(1)
            current_lines = [m.group(2)] if m.group(2) else []
            continue
        if current_speaker and line:
            current_lines.append(line)

    if current_speaker and current_lines:
        items.append({"type": "turn", "speaker": current_speaker,
                      "text": " ".join(current_lines).strip()})

    # Split into waves at music cues
    waves = []
    current_turns = []
    wave_index = 0
    for item in items:
        if item["type"] == "music":
            if current_turns:
                waves.append({"index": wave_index, "turns": current_turns})
                wave_index += 1
                current_turns = []
        else:
            text = strip_audio_tags(item["text"])
            if text:
                current_turns.append({
                    "speaker": item["speaker"],
                    "text": text,
                    "chars": len(text),
                })
    if current_turns:
        waves.append({"index": wave_index, "turns": current_turns})

    return waves


WAVE_FILES = {
    0: "wave-00-opening",
    1: "wave-01",
    2: "wave-02",
    3: "wave-03",
    4: "wave-04",
    5: "wave-05-built-in",
}


def split_wave(wave, audio_dir, model_suffix, cache_dir, dry_run=False):
    """Split a wave file into per-turn cache segments using proportional timing."""
    from pydub import AudioSegment

    base = WAVE_FILES.get(wave["index"])
    if not base:
        print(f"  skip wave {wave['index']} (no known filename mapping)")
        return False

    wave_path = audio_dir / f"{base}{model_suffix}.mp3"
    if not wave_path.exists():
        print(f"  skip {wave_path.name} (not found)")
        return False

    audio = AudioSegment.from_mp3(str(wave_path))
    total_ms = len(audio)
    total_chars = sum(t["chars"] for t in wave["turns"])

    if total_chars == 0:
        print(f"  skip wave {wave['index']} (no text)")
        return False

    print(f"  {wave_path.name}: {total_ms/1000:.1f}s, {len(wave['turns'])} turns, {total_chars} chars")

    # Compute proportional timestamps
    cursor_ms = 0
    segments = []
    for i, turn in enumerate(wave["turns"]):
        proportion = turn["chars"] / total_chars
        duration_ms = int(proportion * total_ms)

        # Last turn gets all remaining time (avoid rounding gaps)
        if i == len(wave["turns"]) - 1:
            duration_ms = total_ms - cursor_ms

        start_ms = cursor_ms
        end_ms = cursor_ms + duration_ms
        segments.append({
            "turn_index": i,
            "speaker": turn["speaker"],
            "start_ms": start_ms,
            "end_ms": end_ms,
            "duration_ms": duration_ms,
        })
        cursor_ms = end_ms

    if dry_run:
        for seg in segments[:5]:
            print(f"    t{seg['turn_index']:04d} ({seg['speaker']}): "
                  f"{seg['start_ms']/1000:.1f}s - {seg['end_ms']/1000:.1f}s "
                  f"({seg['duration_ms']/1000:.1f}s)")
        if len(segments) > 5:
            print(f"    ... and {len(segments) - 5} more turns")
        return True

    # Split and save
    saved = 0
    for seg in segments:
        filename = f"w{wave['index']:02d}-t{seg['turn_index']:04d}-{seg['speaker'].lower()}.mp3"
        out_path = cache_dir / filename
        chunk = audio[seg["start_ms"]:seg["end_ms"]]
        chunk.export(str(out_path), format="mp3", bitrate="128k")
        saved += 1

    print(f"    saved {saved} per-turn files to {cache_dir.name}/")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Split wave files into per-turn cache for re-processing with LUFS normalization"
    )
    parser.add_argument("topic", help="Episode topic (directory name under episodes/)")
    parser.add_argument("--model", choices=["v2", "v3"], default="v2",
                        help="Which wave files to split (default: v2)")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without splitting")
    args = parser.parse_args()

    episode_dir = REPO_ROOT / "episodes" / args.topic
    audio_dir = episode_dir / "assets" / "audio"
    script_path = episode_dir / "final" / "assembled.txt"
    model_suffix = f"_{args.model}"

    if not script_path.exists():
        print(f"Error: {script_path} not found")
        sys.exit(1)

    if not audio_dir.exists():
        print(f"Error: {audio_dir} not found")
        sys.exit(1)

    cache_dir = audio_dir / f"per-turn{model_suffix}"
    if not args.dry_run:
        cache_dir.mkdir(parents=True, exist_ok=True)

    waves = parse_waves(script_path)
    print(f"Parsed {len(waves)} waves from {script_path.name}")
    print(f"Cache directory: {cache_dir}")
    print()

    ok = 0
    for wave in waves:
        if split_wave(wave, audio_dir, model_suffix, cache_dir, dry_run=args.dry_run):
            ok += 1

    print(f"\nDone: {ok}/{len(waves)} waves split")
    if not args.dry_run:
        print(f"\nNext step: re-concatenate with normalization:")
        print(f"  python tools/tts_dialogue.py {args.topic} --model {args.model} --reprocess")


if __name__ == "__main__":
    main()
