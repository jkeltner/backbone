#!/usr/bin/env python3
"""
clip_selector.py — Select highlight clips from episode script

Agent reads script + social-content, picks 3-5 highlight segments (2-5 min each)
and writes a clip-manifest.json with start/end times derived from assembly-map.json.

Usage:
  python tools/clip_selector.py refrigeration
  python tools/clip_selector.py refrigeration --dry-run
  python tools/clip_selector.py refrigeration --count 5    # number of clips

Requires: assembly-map.json from audio_assemble.py
"""

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

# Words per minute for timing estimation
WPM = 150
# Target clip duration range
MIN_CLIP_SECONDS = 120  # 2 min
MAX_CLIP_SECONDS = 300  # 5 min
DEFAULT_CLIP_COUNT = 4


def parse_turns(script_path):
    """Parse script into turns with word counts."""
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
    current_line = 0

    for line_num, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue

        # Music cue — mark as boundary
        if re.match(r"^\[MUSIC:", stripped):
            if current_speaker and current_text:
                full_text = " ".join(current_text)
                turns.append({
                    "speaker": current_speaker,
                    "text": full_text,
                    "word_count": len(full_text.split()),
                    "line": current_line,
                })
                current_speaker = None
                current_text = []
            turns.append({"type": "music_cue", "line": line_num})
            continue

        # Segment break
        if re.match(r"^---\s*SEGMENT BREAK:", stripped):
            continue

        # Speaker turn
        m = re.match(r"^(JEFF|CYRUS):\s*(.+)$", stripped)
        if m:
            if current_speaker and current_text:
                full_text = " ".join(current_text)
                turns.append({
                    "speaker": current_speaker,
                    "text": full_text,
                    "word_count": len(full_text.split()),
                    "line": current_line,
                })
            current_speaker = m.group(1)
            current_text = [m.group(2)]
            current_line = line_num
        elif current_speaker:
            current_text.append(stripped)

    if current_speaker and current_text:
        full_text = " ".join(current_text)
        turns.append({
            "speaker": current_speaker,
            "text": full_text,
            "word_count": len(full_text.split()),
            "line": current_line,
        })

    return turns


def find_highlight_segments(turns, social_content, num_clips=DEFAULT_CLIP_COUNT):
    """Identify highlight-worthy segments using heuristics.

    Scoring criteria:
    - Contains text referenced in social-content (quote matches)
    - Contains vivid storytelling indicators (names, dates, numbers)
    - Has good back-and-forth exchange density
    - Falls at dramatically interesting moments (reactions, reveals)
    """
    spoken_turns = [t for t in turns if "speaker" in t]

    # Score each position as a potential clip start
    candidates = []

    for start_idx in range(len(spoken_turns)):
        # Find end index for 2-5 min window
        words_so_far = 0
        end_idx = start_idx

        while end_idx < len(spoken_turns):
            words_so_far += spoken_turns[end_idx]["word_count"]
            duration_s = (words_so_far / WPM) * 60

            if duration_s >= MIN_CLIP_SECONDS:
                if duration_s <= MAX_CLIP_SECONDS:
                    # Score this window
                    window = spoken_turns[start_idx : end_idx + 1]
                    score = score_window(window, social_content)
                    candidates.append({
                        "start_idx": start_idx,
                        "end_idx": end_idx,
                        "word_count": words_so_far,
                        "duration_s": duration_s,
                        "score": score,
                        "start_line": spoken_turns[start_idx]["line"],
                        "preview": spoken_turns[start_idx]["text"][:100],
                    })
                break
            end_idx += 1

    # Sort by score, pick top N non-overlapping
    candidates.sort(key=lambda c: c["score"], reverse=True)

    selected = []
    used_indices = set()

    for c in candidates:
        indices = set(range(c["start_idx"], c["end_idx"] + 1))
        if not indices & used_indices:
            selected.append(c)
            used_indices |= indices
            if len(selected) >= num_clips:
                break

    # Sort selected clips by position in script
    selected.sort(key=lambda c: c["start_idx"])
    return selected


def score_window(window, social_content):
    """Score a window of turns for highlight potential."""
    score = 0
    full_text = " ".join(t["text"] for t in window)
    full_lower = full_text.lower()

    # Social content match — strong signal
    if social_content:
        social_lower = social_content.lower()
        # Check for shared phrases (5+ word sequences)
        words = full_lower.split()
        for i in range(len(words) - 4):
            phrase = " ".join(words[i : i + 5])
            if phrase in social_lower:
                score += 15

    # Speaker diversity — good clips have back-and-forth
    speakers = set(t["speaker"] for t in window)
    if len(speakers) > 1:
        score += 5
    exchanges = sum(
        1 for i in range(1, len(window))
        if window[i]["speaker"] != window[i - 1]["speaker"]
    )
    score += min(exchanges, 6)

    # Vivid storytelling markers
    # Named people (capitalized words that aren't speakers)
    names = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b", full_text)
    score += min(len(names), 4) * 2

    # Dates and years
    dates = re.findall(r"\b(?:eighteen|nineteen|twenty)\s+\w+\b|\b1[89]\d{2}\b|\b20\d{2}\b", full_lower)
    score += min(len(dates), 3)

    # Numbers / statistics
    numbers = re.findall(r"\b\d+(?:\.\d+)?(?:\s*(?:percent|million|billion|thousand|hundred))\b", full_lower)
    score += min(len(numbers), 3) * 2

    # Emotional/reaction markers
    reactions = re.findall(r"\[(?:laughs?|pause|quietly|wow)\]", full_lower)
    score += min(len(reactions), 3) * 3

    # Questions (engagement markers)
    questions = full_text.count("?")
    score += min(questions, 4)

    # Penalize very short or very long
    total_words = sum(t["word_count"] for t in window)
    duration_s = (total_words / WPM) * 60
    if duration_s < 150 or duration_s > 270:
        score -= 3  # Mild penalty for edge-of-range durations

    return score


def build_clip_manifest(topic, selected_clips, spoken_turns, assembly_map=None):
    """Build clip-manifest.json with timing info."""
    clips = []

    for i, clip in enumerate(selected_clips):
        # Calculate timing
        start_turn = spoken_turns[clip["start_idx"]]
        end_turn = spoken_turns[clip["end_idx"]]

        # Estimate timing from cumulative word count
        words_before_start = sum(
            spoken_turns[j]["word_count"] for j in range(clip["start_idx"])
        )
        start_ms = int((words_before_start / WPM) * 60000)
        end_ms = start_ms + int(clip["duration_s"] * 1000)

        # If we have assembly map, adjust to wave-relative timing
        if assembly_map:
            # Use wave boundaries to refine
            wave_segments = [s for s in assembly_map["segments"] if s["type"] == "wave"]
            total_spoken_words = sum(t["word_count"] for t in spoken_turns)

            # Proportional mapping within total audio
            total_audio_ms = sum(
                s["end_ms"] - s["start_ms"] for s in wave_segments
            )
            start_ratio = words_before_start / max(total_spoken_words, 1)
            end_ratio = (words_before_start + clip["word_count"]) / max(total_spoken_words, 1)

            # Map to audio timeline (accounting for music gaps)
            cumulative_ms = 0
            for seg in wave_segments:
                seg_duration = seg["end_ms"] - seg["start_ms"]
                seg_start_ratio = cumulative_ms / max(total_audio_ms, 1)
                seg_end_ratio = (cumulative_ms + seg_duration) / max(total_audio_ms, 1)

                if seg_start_ratio <= start_ratio <= seg_end_ratio:
                    local_ratio = (start_ratio - seg_start_ratio) / max(seg_end_ratio - seg_start_ratio, 0.001)
                    start_ms = int(seg["start_ms"] + local_ratio * seg_duration)

                if seg_start_ratio <= end_ratio <= seg_end_ratio:
                    local_ratio = (end_ratio - seg_start_ratio) / max(seg_end_ratio - seg_start_ratio, 0.001)
                    end_ms = int(seg["start_ms"] + local_ratio * seg_duration)

                cumulative_ms += seg_duration

        clips.append({
            "id": i + 1,
            "title": f"Clip {i + 1}",
            "start_ms": start_ms,
            "end_ms": end_ms,
            "duration_s": round((end_ms - start_ms) / 1000, 1),
            "start_speaker": start_turn["speaker"],
            "preview": start_turn["text"][:120],
            "score": clip["score"],
            "approved": False,
        })

    return {"topic": topic, "clips": clips}


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Select highlight clips from episode")
    parser.add_argument("topic", help="Episode topic")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--count", type=int, default=DEFAULT_CLIP_COUNT)
    args = parser.parse_args()

    episode_dir = REPO_ROOT / "episodes" / args.topic
    script_path = episode_dir / "final" / "assembled.txt"
    social_path = episode_dir / "final" / "social-content.md"

    if not script_path.exists():
        print(f"Error: {script_path} not found")
        sys.exit(1)

    # Load inputs
    turns = parse_turns(script_path)
    spoken_turns = [t for t in turns if "speaker" in t]
    total_words = sum(t["word_count"] for t in spoken_turns)
    print(f"Parsed {len(spoken_turns)} turns, {total_words} words")

    social_content = ""
    if social_path.exists():
        social_content = social_path.read_text()

    assembly_map = None
    map_path = episode_dir / "final" / "assembly-map.json"
    if map_path.exists():
        assembly_map = json.loads(map_path.read_text())
        print("Using assembly map for timing")

    # Find clips
    selected = find_highlight_segments(turns, social_content, num_clips=args.count)
    print(f"\nSelected {len(selected)} clips:")

    for i, clip in enumerate(selected):
        duration_min = clip["duration_s"] / 60
        print(f"\n  Clip {i+1} (score: {clip['score']}, {duration_min:.1f} min):")
        print(f"    {clip['preview']}...")

    if args.dry_run:
        print("\n[dry run] Would write clip-manifest.json")
        return

    # Build and write manifest
    manifest = build_clip_manifest(args.topic, selected, spoken_turns, assembly_map)

    clips_dir = episode_dir / "assets" / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = clips_dir / "clip-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"\nWrote {manifest_path}")
    print("Review and set 'approved: true' for clips you want generated, then run clip_generate.py")


if __name__ == "__main__":
    main()
