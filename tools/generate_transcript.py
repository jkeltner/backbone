#!/usr/bin/env python3
"""
generate_transcript.py — Generate transcript files from assembled script

The script IS the transcript — this reformats it, not speech-to-text.

Produces:
  transcript.html — styled HTML transcript with speaker labels and timestamps
  transcript.srt  — SRT subtitle file (for YouTube captions)

Usage:
  python tools/generate_transcript.py refrigeration

Requires: assembly-map.json from audio_assemble.py (for SRT timing)
"""

import html
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

FRONT_MATTER_RE = re.compile(r"^---\s*$")
MUSIC_CUE_RE = re.compile(r"^\[MUSIC:\s*(.+?)\]$")
SEGMENT_BREAK_RE = re.compile(r"^---\s*SEGMENT BREAK:.*---$")
SPEAKER_RE = re.compile(r"^(JEFF|CYRUS):\s*(.+)$")
AUDIO_TAG_RE = re.compile(r"\[(?:laughs?|pause|quietly|sighs?|clears throat|whispers?)[^\]]*\]", re.IGNORECASE)

# Estimated words per minute for SRT timing (when no assembly map)
WPM = 150


def parse_script(script_path):
    """Parse assembled.txt into a list of turns.

    Returns list of dicts:
      {"speaker": "JEFF", "text": "...", "word_count": N}
      {"type": "music", "cue": "theme-in"}
    """
    text = script_path.read_text()
    lines = text.splitlines()

    # Strip front matter
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                lines = lines[i + 1 :]
                break

    turns = []
    current_speaker = None
    current_text = []

    def flush():
        nonlocal current_speaker, current_text
        if current_speaker and current_text:
            full_text = " ".join(current_text)
            turns.append({
                "speaker": current_speaker,
                "text": full_text,
                "word_count": len(full_text.split()),
            })
        current_speaker = None
        current_text = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if SEGMENT_BREAK_RE.match(stripped):
            continue
        if MUSIC_CUE_RE.match(stripped):
            flush()
            cue = MUSIC_CUE_RE.match(stripped).group(1)
            turns.append({"type": "music", "cue": cue})
            continue

        speaker_match = SPEAKER_RE.match(stripped)
        if speaker_match:
            flush()
            current_speaker = speaker_match.group(1)
            current_text = [speaker_match.group(2)]
        elif current_speaker:
            # Continuation line
            current_text.append(stripped)

    flush()
    return turns


def clean_text_for_display(text):
    """Remove audio tags for display but keep the text readable."""
    # Replace [pause] with "..." and remove other tags
    text = re.sub(r"\[pause\]", "...", text)
    text = AUDIO_TAG_RE.sub("", text)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text


def generate_html(turns, topic, output_path):
    """Generate styled HTML transcript."""
    html_parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        f"<title>Transcript — Backbone: {topic.replace('-', ' ').title()}</title>",
        "<style>",
        "body { font-family: 'Georgia', serif; max-width: 720px; margin: 2rem auto; padding: 0 1rem; line-height: 1.7; color: #1a1a1a; }",
        "h1 { font-size: 1.5rem; border-bottom: 2px solid #333; padding-bottom: 0.5rem; }",
        ".turn { margin: 1.2rem 0; }",
        ".speaker { font-weight: bold; color: #2c5282; text-transform: uppercase; font-size: 0.85rem; letter-spacing: 0.05em; margin-bottom: 0.2rem; }",
        ".speaker.cyrus { color: #9b2c2c; }",
        ".text { margin: 0; }",
        ".music-break { text-align: center; color: #888; font-style: italic; margin: 2rem 0; font-size: 0.9rem; }",
        ".footer { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #ddd; font-size: 0.85rem; color: #666; }",
        "</style>",
        "</head>",
        "<body>",
        f'<h1>Backbone: {html.escape(topic.replace("-", " ").title())}</h1>',
    ]

    for turn in turns:
        if "type" in turn and turn["type"] == "music":
            label = turn["cue"].replace("-", " ").title()
            html_parts.append(f'<div class="music-break">♪ {html.escape(label)} ♪</div>')
        elif "speaker" in turn:
            speaker = turn["speaker"]
            text = clean_text_for_display(turn["text"])
            css_class = f"speaker {speaker.lower()}"
            html_parts.append('<div class="turn">')
            html_parts.append(f'  <div class="{css_class}">{html.escape(speaker)}</div>')
            html_parts.append(f'  <p class="text">{html.escape(text)}</p>')
            html_parts.append("</div>")

    html_parts.extend([
        '<div class="footer">',
        "<p>Backbone: From Breakthrough to Built-In</p>",
        "<p>Hosts: Jeff Keltner and Cyrus Mistry</p>",
        "</div>",
        "</body>",
        "</html>",
    ])

    output_path.write_text("\n".join(html_parts) + "\n")
    print(f"Wrote {output_path}")


def ms_to_srt_time(ms):
    """Convert milliseconds to SRT timestamp format (HH:MM:SS,mmm)."""
    hours = int(ms // 3600000)
    minutes = int((ms % 3600000) // 60000)
    seconds = int((ms % 60000) // 1000)
    millis = int(ms % 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def generate_srt(turns, topic, output_path, assembly_map=None):
    """Generate SRT subtitle file.

    If assembly_map is available, uses real timing.
    Otherwise estimates from word count at WPM.
    """
    srt_parts = []
    counter = 1
    current_ms = 0.0

    # If we have an assembly map, compute per-wave offsets
    wave_offsets = {}
    if assembly_map:
        for seg in assembly_map["segments"]:
            if seg["type"] == "wave":
                wave_offsets[seg["index"]] = seg["start_ms"]

    wave_idx = 0
    wave_start_ms = 0

    for turn in turns:
        if "type" in turn and turn["type"] == "music":
            wave_idx += 1
            if wave_idx in wave_offsets:
                current_ms = wave_offsets[wave_idx]
                wave_start_ms = current_ms
            else:
                current_ms += 2000  # approximate music duration
            continue

        if "speaker" not in turn:
            continue

        text = clean_text_for_display(turn["text"])
        words = turn["word_count"]

        # Duration based on word count
        duration_ms = (words / WPM) * 60000

        # Split long turns into subtitle chunks (~15 words each)
        text_words = text.split()
        chunk_size = 15
        chunks = []
        for i in range(0, len(text_words), chunk_size):
            chunks.append(" ".join(text_words[i : i + chunk_size]))

        chunk_duration = duration_ms / max(len(chunks), 1)

        for chunk in chunks:
            start = current_ms
            end = current_ms + chunk_duration
            srt_parts.append(str(counter))
            srt_parts.append(f"{ms_to_srt_time(start)} --> {ms_to_srt_time(end)}")
            srt_parts.append(f"[{turn['speaker']}] {chunk}")
            srt_parts.append("")
            counter += 1
            current_ms = end

    output_path.write_text("\n".join(srt_parts) + "\n")
    print(f"Wrote {output_path} ({counter - 1} subtitles)")


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/generate_transcript.py <topic>")
        sys.exit(1)

    topic = sys.argv[1]
    episode_dir = REPO_ROOT / "episodes" / topic
    final_dir = episode_dir / "final"
    script_path = final_dir / "assembled.txt"

    if not script_path.exists():
        print(f"Error: {script_path} not found")
        sys.exit(1)

    turns = parse_script(script_path)
    spoken_turns = [t for t in turns if "speaker" in t]
    total_words = sum(t["word_count"] for t in spoken_turns)
    print(f"Parsed {len(spoken_turns)} spoken turns, {total_words} words")

    # Load assembly map if available (for SRT timing)
    map_path = final_dir / "assembly-map.json"
    assembly_map = None
    if map_path.exists():
        assembly_map = json.loads(map_path.read_text())
        print(f"Using real timing from {map_path}")
    else:
        print(f"No assembly map found — using estimated timing at {WPM} WPM")

    generate_html(turns, topic, final_dir / "transcript.html")
    generate_srt(turns, topic, final_dir / "transcript.srt", assembly_map)


if __name__ == "__main__":
    main()
