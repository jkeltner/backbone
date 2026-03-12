#!/usr/bin/env python3
"""
tts_generate.py — Backbone TTS Audio Generator

Parses an episode's assembled.txt, calls ElevenLabs TTS for each
speaker turn, and saves numbered audio segments to:
  episodes/{topic}/assets/audio/

A manifest.json is written alongside the audio files, recording the
full ordered sequence of turns and music cues for the assembly step.

Usage:
  python tools/tts_generate.py refrigeration
  python tools/tts_generate.py refrigeration --dry-run
  python tools/tts_generate.py refrigeration --segment "Wave 2"
  python tools/tts_generate.py refrigeration --list

Config (set in .env or environment):
  ELEVENLABS_API_KEY
  JEFF_VOICE_ID
  CYRUS_VOICE_ID
  ELEVENLABS_MODEL_ID   (default: eleven_v3)
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DEFAULT_MODEL = "eleven_v3"
OUTPUT_FORMAT = "mp3_44100_128"
MAX_CHARS = 4500  # ElevenLabs safe limit per call


# ---------------------------------------------------------------------------
# Config / env
# ---------------------------------------------------------------------------

def load_env():
    """Load .env from repo root if present."""
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def get_client():
    try:
        from elevenlabs.client import ElevenLabs
    except ImportError:
        print("ElevenLabs SDK not found. Install with:  pip install elevenlabs")
        sys.exit(1)

    api_key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not api_key:
        print("Error: ELEVENLABS_API_KEY not set. Add it to .env or set the environment variable.")
        sys.exit(1)

    return ElevenLabs(api_key=api_key)


def voice_id_for(speaker: str) -> str:
    vid = os.environ.get(f"{speaker}_VOICE_ID", "")
    if not vid:
        print(f"Error: {speaker}_VOICE_ID not set. Add it to .env or set the environment variable.")
        sys.exit(1)
    return vid


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_assembled(script_path: Path) -> list[dict]:
    """
    Parse assembled.txt into an ordered list of items:
      {"type": "turn",  "speaker": "JEFF"|"CYRUS", "text": "...", "segment": "..."}
      {"type": "music", "cue": "[MUSIC: theme-in]",               "segment": "..."}

    Strips front matter, segment break markers, and blank lines.
    Audio tags ([laughs], [pause], etc.) are preserved — ElevenLabs v3 handles them.
    """
    content = script_path.read_text(encoding="utf-8")

    # Strip YAML front matter (--- ... ---)
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            content = content[end + 3:].lstrip()

    items = []
    current_speaker = None
    current_lines = []
    current_segment = "Opening"

    for raw_line in content.splitlines():
        line = raw_line.strip()

        # Segment break — update segment label, flush current turn
        if line.startswith("---") and "SEGMENT BREAK" in line:
            if current_speaker and current_lines:
                items.append(_make_turn(current_speaker, current_lines, current_segment))
                current_speaker, current_lines = None, []
            current_segment = re.sub(r"---\s*SEGMENT BREAK:\s*", "", line).rstrip("-").strip()
            continue

        # Music cue marker
        if re.match(r"^\[MUSIC:", line):
            if current_speaker and current_lines:
                items.append(_make_turn(current_speaker, current_lines, current_segment))
                current_speaker, current_lines = None, []
            items.append({"type": "music", "cue": line, "segment": current_segment})
            continue

        # New speaker turn
        m = re.match(r"^(JEFF|CYRUS):\s*(.*)", line)
        if m:
            if current_speaker and current_lines:
                items.append(_make_turn(current_speaker, current_lines, current_segment))
            current_speaker = m.group(1)
            current_lines = [m.group(2)] if m.group(2) else []
            continue

        # Continuation line
        if current_speaker and line:
            current_lines.append(line)

    # Flush last turn
    if current_speaker and current_lines:
        items.append(_make_turn(current_speaker, current_lines, current_segment))

    return items


def _make_turn(speaker, lines, segment):
    return {
        "type": "turn",
        "speaker": speaker,
        "text": " ".join(lines).strip(),
        "segment": segment,
    }


# ---------------------------------------------------------------------------
# Job list (handles chunking of long turns)
# ---------------------------------------------------------------------------

def build_jobs(items: list[dict]) -> list[dict]:
    """
    Convert parsed items into a numbered job list.
    Speaker turns exceeding MAX_CHARS are split at sentence boundaries.
    Music cues are included as non-audio jobs (for the manifest).

    Segment names are inferred from music cue positions since the Producer
    strips segment break markers from assembled.txt:
      Opening → [MUSIC: theme-in] → Opening (By the Numbers onwards)
      → [MUSIC: transition-bumper] → Wave 1
      → [MUSIC: transition-bumper] → Wave 2  (etc.)
      → [MUSIC: transition-bumper] → Built In
    """
    # First pass: assign segment names based on music cue sequence
    SEGMENT_MAP = {
        "theme-in": None,           # stays "Opening"
        "transition-bumper": None,  # increments wave counter
        "theme-out": None,
    }
    wave_counter = 0
    current_segment = "Opening"
    for item in items:
        if item["type"] == "music":
            cue = item["cue"]
            if "theme-in" in cue:
                current_segment = "Opening"  # still opening after theme music
            elif "transition-bumper" in cue:
                wave_counter += 1
                wave_names = {1: "Wave 1", 2: "Wave 2", 3: "Wave 3", 4: "Wave 4"}
                # Last transition-bumper leads into Built In
                # We'll fix this below after counting total bumpers
                current_segment = wave_names.get(wave_counter, f"Wave {wave_counter}")
            elif "theme-out" in cue:
                current_segment = "Built In"
        item["segment"] = current_segment

    # Fix: last wave before theme-out should be "Built In"
    # Count transition-bumpers to find total waves
    bumper_count = sum(1 for i in items if i["type"] == "music" and "transition-bumper" in i["cue"])
    if bumper_count > 0:
        # Re-do segment assignment with correct Built In label
        wave_counter = 0
        current_segment = "Opening"
        for item in items:
            if item["type"] == "music":
                if "theme-in" in item["cue"]:
                    current_segment = "Opening"
                elif "transition-bumper" in item["cue"]:
                    wave_counter += 1
                    if wave_counter == bumper_count:
                        current_segment = "Built In"
                    else:
                        current_segment = f"Wave {wave_counter}"
                elif "theme-out" in item["cue"]:
                    current_segment = "Built In"
            item["segment"] = current_segment

    # Second pass: build job list
    jobs = []
    idx = 0

    for item in items:
        if item["type"] == "music":
            jobs.append({
                "index": idx,
                "type": "music",
                "cue": item["cue"],
                "segment": item["segment"],
                "filename": None,
            })
            idx += 1

        elif item["type"] == "turn":
            chunks = _split_text(item["text"])
            for part, chunk in enumerate(chunks):
                suffix = f"-pt{part + 1}" if len(chunks) > 1 else ""
                filename = f"segment-{idx:04d}-{item['speaker'].lower()}{suffix}.mp3"
                jobs.append({
                    "index": idx,
                    "type": "turn",
                    "speaker": item["speaker"],
                    "text": chunk,
                    "segment": item["segment"],
                    "filename": filename,
                    "chars": len(chunk),
                })
                idx += 1

    return jobs


def _split_text(text: str, max_chars: int = MAX_CHARS) -> list[str]:
    """Split text at sentence boundaries if it exceeds max_chars."""
    if len(text) <= max_chars:
        return [text]

    chunks, current = [], ""
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        if current and len(current) + len(sentence) + 1 > max_chars:
            chunks.append(current.strip())
            current = sentence
        else:
            current = (current + " " + sentence).strip() if current else sentence
    if current:
        chunks.append(current.strip())
    return chunks


# ---------------------------------------------------------------------------
# Audio generation
# ---------------------------------------------------------------------------

def generate_turn(client, job: dict, output_dir: Path) -> bool:
    """Call ElevenLabs TTS for one speaker turn. Returns True on success."""
    out_path = output_dir / job["filename"]

    if out_path.exists():
        print(f"  skip  {job['filename']}")
        return True

    vid = voice_id_for(job["speaker"])
    model = os.environ.get("ELEVENLABS_MODEL_ID", DEFAULT_MODEL)

    try:
        audio_iter = client.text_to_speech.convert(
            text=job["text"],
            voice_id=vid,
            model_id=model,
            output_format=OUTPUT_FORMAT,
        )
        with open(out_path, "wb") as f:
            for chunk in audio_iter:
                f.write(chunk)
        kb = out_path.stat().st_size // 1024
        print(f"  ok    {job['filename']}  ({job['chars']} chars, {kb} KB)")
        return True

    except Exception as e:
        print(f"  ERROR {job['filename']}: {e}")
        # Remove partial file if it exists
        if out_path.exists():
            out_path.unlink()
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    load_env()

    parser = argparse.ArgumentParser(description="Generate TTS audio segments for a Backbone episode")
    parser.add_argument("topic", help="Episode directory name (e.g. refrigeration)")
    parser.add_argument("--dry-run", action="store_true", help="Plan without calling the API")
    parser.add_argument("--segment", metavar="NAME", help="Only generate turns in matching segment(s)")
    parser.add_argument("--list", dest="list_only", action="store_true", help="List all turns and exit")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    script_path = REPO_ROOT / "episodes" / args.topic / "final" / "assembled.txt"
    output_dir  = REPO_ROOT / "episodes" / args.topic / "assets" / "audio"
    manifest_path = output_dir / "manifest.json"

    if not script_path.exists():
        print(f"Error: assembled script not found at {script_path}")
        sys.exit(1)

    # --- Parse ---
    print(f"\nParsing {script_path} ...")
    items = parse_assembled(script_path)
    jobs  = build_jobs(items)

    turn_jobs  = [j for j in jobs if j["type"] == "turn"]
    music_jobs = [j for j in jobs if j["type"] == "music"]
    total_chars = sum(j["chars"] for j in turn_jobs)

    print(f"  {len(turn_jobs)} speaker turns  ({total_chars:,} chars)")
    print(f"  {len(music_jobs)} music cues")

    if any(j["chars"] > MAX_CHARS for j in turn_jobs):
        long = [j for j in turn_jobs if j["chars"] > MAX_CHARS]
        print(f"  Note: {len(long)} turns were split into multiple chunks")

    # --- List mode ---
    if args.list_only:
        print()
        for j in jobs:
            if j["type"] == "turn":
                print(f"  {j['index']:04d}  {j['speaker']:<5}  [{j['segment']}]  {j['chars']} chars")
            else:
                print(f"  {j['index']:04d}  MUSIC  {j['cue']}")
        return

    # --- Filter by segment ---
    if args.segment:
        run_jobs = [j for j in turn_jobs if args.segment.lower() in j["segment"].lower()]
        print(f"\n  Filtered to '{args.segment}': {len(run_jobs)} turns")
    else:
        run_jobs = turn_jobs

    # --- Status ---
    output_dir.mkdir(parents=True, exist_ok=True)
    already_done = sum(1 for j in run_jobs if (output_dir / j["filename"]).exists())
    to_generate  = len(run_jobs) - already_done

    print(f"\nOutput directory: {output_dir}")
    print(f"  Already generated : {already_done}")
    print(f"  To generate       : {to_generate}")

    if args.dry_run:
        print("\n[dry-run] No API calls will be made.")
        for j in run_jobs:
            exists = (output_dir / j["filename"]).exists()
            status = "skip" if exists else "generate"
            print(f"  {status:8s}  {j['filename']}  ({j['chars']} chars)")
        # Still write the manifest in dry-run mode
        manifest_path.write_text(json.dumps(jobs, indent=2))
        print(f"\nManifest written: {manifest_path}")
        return

    if to_generate == 0:
        print("\nAll segments already generated.")
        manifest_path.write_text(json.dumps(jobs, indent=2))
        print(f"Manifest written: {manifest_path}")
        return

    if not args.yes:
        confirm = input(f"\nGenerate {to_generate} audio segment(s) via ElevenLabs? [y/N] ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            sys.exit(0)

    # --- Generate ---
    client = get_client()
    ok, failed = 0, 0

    print()
    for j in run_jobs:
        if generate_turn(client, j, output_dir):
            ok += 1
        else:
            failed += 1

    # Always write manifest (includes music cue positions for assembly step)
    manifest_path.write_text(json.dumps(jobs, indent=2))
    print(f"\nManifest written: {manifest_path}")
    print(f"\nDone: {ok} generated, {already_done} skipped, {failed} failed")
    if failed:
        print("Re-run to retry failed segments (successful files are not re-generated).")


if __name__ == "__main__":
    main()
