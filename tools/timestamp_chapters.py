#!/usr/bin/env python3
"""
timestamp_chapters.py — Replace estimated timestamps with real ones

Reads assembly-map.json (produced by audio_assemble.py) and:
1. Produces chapters.json (Podcasting 2.0 format for Transistor)
2. Updates metadata.md with real timestamps

Usage:
  python tools/timestamp_chapters.py refrigeration

Requires: assembly-map.json from audio_assemble.py
"""

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def ms_to_timestamp(ms):
    """Convert milliseconds to HH:MM:SS format."""
    total_seconds = int(ms / 1000)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def ms_to_seconds(ms):
    """Convert milliseconds to seconds (float)."""
    return round(ms / 1000, 1)


# Chapter names mapped from wave indices
WAVE_NAMES = {
    0: "The Hook",
    -1: "The Big Picture",  # last wave, sentinel
}


def load_assembly_map(topic):
    """Load the assembly map JSON."""
    map_path = REPO_ROOT / "episodes" / topic / "final" / "assembly-map.json"
    if not map_path.exists():
        print(f"Error: {map_path} not found. Run audio_assemble.py first.")
        sys.exit(1)
    return json.loads(map_path.read_text())


def load_blueprint_chapter_names(topic):
    """Try to extract chapter/wave names from blueprint.md."""
    bp_path = REPO_ROOT / "episodes" / topic / "blueprint.md"
    names = {}
    if bp_path.exists():
        text = bp_path.read_text()
        # Look for wave headers like "## WAVE 1: The Ice Trade"
        for m in re.finditer(r"##\s*WAVE\s+(\d+)[:\s—–-]+(.+)", text, re.IGNORECASE):
            idx = int(m.group(1))
            names[idx] = m.group(2).strip()
        # Look for opening
        if re.search(r"##\s*OPENING", text, re.IGNORECASE):
            names[0] = names.get(0, "The Hook")
        # Look for built-in / big picture
        for m in re.finditer(r"##\s*BUILT\s*IN[:\s—–-]*(.+)?", text, re.IGNORECASE):
            label = m.group(1).strip() if m.group(1) else "The Big Picture"
            names[-1] = label
    return names


def load_metadata_chapter_names(topic):
    """Extract chapter names from metadata.md table."""
    meta_path = REPO_ROOT / "episodes" / topic / "final" / "metadata.md"
    names = {}
    if meta_path.exists():
        text = meta_path.read_text()
        # Parse table rows like "| Opening | The Hook | 00:00 |"
        for m in re.finditer(
            r"\|\s*(?:Opening|Wave\s+(\d+)|Built\s*In)\s*\|\s*(.+?)\s*\|",
            text,
            re.IGNORECASE,
        ):
            wave_num = m.group(1)
            title = m.group(2).strip()
            if wave_num:
                names[int(wave_num)] = title
            elif "opening" in m.group(0).lower():
                names[0] = title
            else:
                names[-1] = title  # Built In
    return names


def generate_chapters(topic):
    """Generate chapters.json and update metadata.md."""
    assembly_map = load_assembly_map(topic)
    segments = assembly_map["segments"]

    # Get chapter names from metadata or blueprint
    chapter_names = load_metadata_chapter_names(topic)
    if not chapter_names:
        chapter_names = load_blueprint_chapter_names(topic)

    # Build chapters from wave segments.
    # Waves are split at EVERY music cue, so a chapter can span several waves
    # (e.g. [MUSIC: theme-in] inside the opening splits it into two waves). A new
    # chapter starts at the first wave and at every wave that directly follows a
    # transition-bumper; waves that follow theme-in (or another wave) are
    # continuations. Chapter titles are then assigned in order: Opening, Wave 1..N,
    # Built In.
    ordered_titles = []
    if 0 in chapter_names:
        ordered_titles.append(chapter_names[0])
    for k in sorted(i for i in chapter_names if i > 0):
        ordered_titles.append(chapter_names[k])
    if -1 in chapter_names:
        ordered_titles.append(chapter_names[-1])

    chapters = []
    prev_cue = None
    chapter_no = -1
    for seg in segments:
        if seg["type"] == "music":
            prev_cue = seg.get("cue")
            continue
        if seg["type"] != "wave":
            continue
        starts_chapter = (chapter_no < 0) or (prev_cue == "transition-bumper")
        prev_cue = None
        if not starts_chapter:
            continue  # continuation of the current chapter
        chapter_no += 1
        if chapter_no < len(ordered_titles):
            title = ordered_titles[chapter_no]
        elif chapter_no == 0:
            title = "The Hook"
        else:
            title = f"Chapter {chapter_no + 1}"
        chapters.append({
            "title": title,
            "startTime": ms_to_seconds(seg["start_ms"]),
            "startTimestamp": ms_to_timestamp(seg["start_ms"]),
        })
    if len(chapters) != len(ordered_titles) and ordered_titles:
        print(f"  WARNING: {len(chapters)} chapter boundaries in audio vs "
              f"{len(ordered_titles)} named chapters — check bumper placement")

    # Podcasting 2.0 chapters format
    chapters_json = {
        "version": "1.2.0",
        "chapters": [
            {"startTime": c["startTime"], "title": c["title"]}
            for c in chapters
        ],
    }

    # Write chapters.json
    out_dir = REPO_ROOT / "episodes" / topic / "final"
    chapters_path = out_dir / "chapters.json"
    chapters_path.write_text(json.dumps(chapters_json, indent=2) + "\n")
    print(f"Wrote {chapters_path}")
    for c in chapters:
        print(f"  {c['startTimestamp']}  {c['title']}")

    # Update metadata.md timestamps
    meta_path = out_dir / "metadata.md"
    if meta_path.exists():
        meta_text = meta_path.read_text()

        # Build replacement map: title → new timestamp
        ts_map = {c["title"]: c["startTimestamp"] for c in chapters}

        # Replace timestamps in the table
        def replace_timestamp(match):
            full = match.group(0)
            title_col = match.group(2).strip()
            # Find matching chapter
            for title, ts in ts_map.items():
                if title.lower() == title_col.lower():
                    # Replace the timestamp in the row
                    return re.sub(r"\d{1,3}:\d{2}(:\d{2})?", ts, full, count=1)
            return full

        updated = re.sub(
            r"(\|\s*(?:Opening|Wave\s+\d+|Built\s*In)\s*\|\s*(.+?)\s*\|\s*)(\d{1,3}:\d{2}(?::\d{2})?)\s*\|",
            replace_timestamp,
            meta_text,
        )

        # Update estimated runtime with actual
        total_ms = assembly_map["total_duration_ms"]
        total_min = total_ms / 60000
        updated = re.sub(
            r"approximately \*\*[\d–]+\s*minutes\*\*",
            f"**{total_min:.0f} minutes**",
            updated,
        )
        # Add note that timestamps are from actual audio
        updated = updated.replace(
            "*Note: Timestamps are approximate estimates based on word count. Actual timestamps should be set from the final audio file.*",
            "*Timestamps updated from final audio assembly.*",
        )

        meta_path.write_text(updated)
        print(f"Updated timestamps in {meta_path}")

    # Total duration
    total_s = assembly_map["total_duration_ms"] / 1000
    print(f"\nTotal episode duration: {ms_to_timestamp(assembly_map['total_duration_ms'])} ({total_s/60:.1f} min)")

    return chapters_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/timestamp_chapters.py <topic>")
        sys.exit(1)

    topic = sys.argv[1]
    generate_chapters(topic)


if __name__ == "__main__":
    main()
