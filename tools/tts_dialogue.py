#!/usr/bin/env python3
"""
tts_dialogue.py — Backbone Dialogue TTS Generator

Uses the ElevenLabs Text to Dialogue API to generate one audio file per
wave/section, preserving natural multi-speaker prosody within each section.

Instead of 500+ individual per-turn files, this produces:
  wave-00-opening.mp3
  wave-01.mp3
  wave-02.mp3
  wave-03.mp3
  wave-04-built-in.mp3

Music cue markers ([MUSIC: ...]) in the script are the natural chunking
boundaries — each section between cues becomes one API call.

Usage:
  python tools/tts_dialogue.py refrigeration
  python tools/tts_dialogue.py refrigeration --model v2       # higher quality, per-turn TTS
  python tools/tts_dialogue.py refrigeration --speed 1.5      # faster playback (default: 1.3)
  python tools/tts_dialogue.py refrigeration --dry-run
  python tools/tts_dialogue.py refrigeration --wave 0
  python tools/tts_dialogue.py refrigeration --yes

Models:
  v3 (default) — ElevenLabs Dialogue API, native multi-speaker, supports audio tags
  v2           — eleven_multilingual_v2, per-turn TTS (pydub required), audio tags stripped,
                 often warmer/more natural for conversational speech

Config (set in .env):
  ELEVENLABS_API_KEY
  JEFF_VOICE_ID
  CYRUS_VOICE_ID
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
MODEL_V3 = "eleven_v3"
MODEL_V2 = "eleven_multilingual_v2"
DEFAULT_MODEL = MODEL_V3
OUTPUT_FORMAT = "mp3_44100_128"

# ElevenLabs Dialogue API limit (inputs per request)
# If a wave exceeds this, it's split into sub-chunks
MAX_INPUTS_PER_REQUEST = 100

# Audio tags that ElevenLabs v3 handles natively but v2 does not
AUDIO_TAG_RE = re.compile(r"\[(?:laughs?|pause|quietly|sighs?|clears throat|whispers?)[^\]]*\]\s*", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Config / env
# ---------------------------------------------------------------------------

def load_env():
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
        print("ElevenLabs SDK not found. Run: pip install elevenlabs")
        sys.exit(1)
    api_key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not api_key:
        print("Error: ELEVENLABS_API_KEY not set in .env")
        sys.exit(1)
    return ElevenLabs(api_key=api_key)


def voice_id_for(speaker: str) -> str:
    vid = os.environ.get(f"{speaker}_VOICE_ID", "")
    if not vid:
        print(f"Error: {speaker}_VOICE_ID not set in .env")
        sys.exit(1)
    return vid


# ---------------------------------------------------------------------------
# Parsing — same logic as tts_generate.py
# ---------------------------------------------------------------------------

def parse_assembled(script_path: Path) -> list[dict]:
    """
    Parse assembled.txt into an ordered list of items:
      {"type": "turn",  "speaker": "JEFF"|"CYRUS", "text": "..."}
      {"type": "music", "cue": "[MUSIC: theme-in]"}
    """
    content = script_path.read_text(encoding="utf-8")

    # Strip YAML front matter
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            content = content[end + 3:].lstrip()

    items = []
    current_speaker = None
    current_lines = []

    for raw_line in content.splitlines():
        line = raw_line.strip()

        # Segment break markers (informational only, not a split point here)
        if line.startswith("---") and "SEGMENT BREAK" in line:
            if current_speaker and current_lines:
                items.append({"type": "turn", "speaker": current_speaker,
                               "text": " ".join(current_lines).strip()})
                current_speaker, current_lines = None, []
            continue

        # Music cue — this IS a split point
        if re.match(r"^\[MUSIC:", line):
            if current_speaker and current_lines:
                items.append({"type": "turn", "speaker": current_speaker,
                               "text": " ".join(current_lines).strip()})
                current_speaker, current_lines = None, []
            items.append({"type": "music", "cue": line})
            continue

        # New speaker turn
        m = re.match(r"^(JEFF|CYRUS):\s*(.*)", line)
        if m:
            if current_speaker and current_lines:
                items.append({"type": "turn", "speaker": current_speaker,
                               "text": " ".join(current_lines).strip()})
            current_speaker = m.group(1)
            current_lines = [m.group(2)] if m.group(2) else []
            continue

        # Continuation
        if current_speaker and line:
            current_lines.append(line)

    if current_speaker and current_lines:
        items.append({"type": "turn", "speaker": current_speaker,
                       "text": " ".join(current_lines).strip()})

    return items


# ---------------------------------------------------------------------------
# Wave chunking
# ---------------------------------------------------------------------------

WAVE_NAMES = {
    0: "opening",
    1: "wave-01",
    2: "wave-02",
    3: "wave-03",
    4: "wave-04",
    5: "wave-05",
}

def split_into_waves(items: list[dict], model_suffix: str = "") -> list[dict]:
    """
    Split parsed items into waves using music cues as boundaries.
    model_suffix is appended before .mp3 (e.g. "_v2" → "wave-00-opening_v2.mp3").
    Returns a list of wave dicts:
      {
        "index": 0,
        "name": "opening",
        "filename": "wave-00-opening_v2.mp3",
        "music_before": None | "[MUSIC: theme-in]",
        "music_after":  "[MUSIC: transition-bumper]" | "[MUSIC: theme-out]" | None,
        "turns": [{"speaker": "JEFF", "text": "..."}]
      }
    """
    waves = []
    current_turns = []
    music_before = None
    wave_index = 0

    def _filename(idx, name, is_named=False):
        base = f"wave-{idx:02d}-{name}" if is_named else f"wave-{idx:02d}"
        return f"{base}{model_suffix}.mp3"

    for item in items:
        if item["type"] == "music":
            # Close current wave
            if current_turns:
                name = WAVE_NAMES.get(wave_index, f"wave-{wave_index:02d}")
                waves.append({
                    "index": wave_index,
                    "name": name,
                    "filename": _filename(wave_index, name, is_named=(wave_index == 0)),
                    "music_before": music_before,
                    "music_after": item["cue"],
                    "turns": current_turns,
                })
                wave_index += 1
                current_turns = []
            music_before = item["cue"]
        else:
            current_turns.append({"speaker": item["speaker"], "text": item["text"]})

    # Final wave (after last music cue, if any turns remain)
    if current_turns:
        name = WAVE_NAMES.get(wave_index, f"wave-{wave_index:02d}")
        waves.append({
            "index": wave_index,
            "name": name,
            "filename": _filename(wave_index, name, is_named=(wave_index == 0)),
            "music_before": music_before,
            "music_after": None,
            "turns": current_turns,
        })

    # Rename last wave to built-in
    if waves:
        waves[-1]["name"] = "built-in"
        idx = waves[-1]["index"]
        waves[-1]["filename"] = _filename(idx, "built-in", is_named=True)

    return waves


def sub_chunk_wave(wave: dict, max_inputs: int = MAX_INPUTS_PER_REQUEST) -> list[list[dict]]:
    """Split a wave's turns into sub-chunks if it exceeds max_inputs."""
    turns = wave["turns"]
    if len(turns) <= max_inputs:
        return [turns]
    chunks = []
    for i in range(0, len(turns), max_inputs):
        chunks.append(turns[i:i + max_inputs])
    return chunks


# ---------------------------------------------------------------------------
# Audio generation
# ---------------------------------------------------------------------------

def apply_speed(path: Path, speed: float) -> bool:
    """Use ffmpeg atempo to adjust speed without changing pitch. Overwrites the file."""
    import subprocess, shutil
    if not shutil.which("ffmpeg"):
        print("  WARNING: ffmpeg not found — skipping speed adjustment. Install with: brew install ffmpeg")
        return False

    tmp = path.with_suffix(".tmp.mp3")
    # atempo is capped at 2.0 per filter; chain for higher values
    filters = []
    s = speed
    while s > 2.0:
        filters.append("atempo=2.0")
        s /= 2.0
    filters.append(f"atempo={s:.4f}")
    filter_str = ",".join(filters)

    result = subprocess.run(
        ["ffmpeg", "-y", "-i", str(path), "-filter:a", filter_str, str(tmp)],
        capture_output=True
    )
    if result.returncode == 0:
        tmp.replace(path)
        return True
    else:
        print(f"  WARNING: ffmpeg speed adjustment failed: {result.stderr.decode()[:200]}")
        if tmp.exists():
            tmp.unlink()
        return False


def strip_audio_tags(text: str) -> str:
    """Remove audio tags like [laughs], [pause], etc. that v2 would read aloud."""
    return AUDIO_TAG_RE.sub("", text).strip()


def generate_wave(client, wave: dict, output_dir: Path, dry_run: bool = False,
                  stability: float = 0.4, speed: float = 1.0,
                  model: str = MODEL_V3) -> bool:
    """Generate audio for a single wave. Uses Dialogue API for v3, per-turn TTS for v2."""
    out_path = output_dir / wave["filename"]
    turns = wave["turns"]
    sub_chunks = sub_chunk_wave(wave)
    use_v2 = (model == MODEL_V2)

    if out_path.exists():
        print(f"  skip  {wave['filename']}")
        return True

    jeff_vid  = voice_id_for("JEFF")
    cyrus_vid = voice_id_for("CYRUS")

    def vid_for(speaker):
        return jeff_vid if speaker == "JEFF" else cyrus_vid

    if dry_run:
        total_chars = sum(len(t["text"]) for t in turns)
        speed_note = f", speed={speed}x" if speed != 1.0 else ""
        mode = "per-turn TTS" if use_v2 else f"{len(sub_chunks)} request(s)"
        print(f"  dry-run  {wave['filename']}  ({len(turns)} turns, {total_chars:,} chars, "
              f"{mode}, model={model}, stability={stability}{speed_note})")
        return True

    try:
        if use_v2:
            # v2: per-turn generation, concatenated into a single wave file
            _generate_wave_v2(client, wave, out_path, output_dir,
                              model, vid_for, stability)
        else:
            # v3: Dialogue API (multi-speaker, supports audio tags natively)
            _generate_wave_v3(client, wave, out_path, output_dir,
                              model, vid_for, stability, sub_chunks)

        if speed != 1.0:
            apply_speed(out_path, speed)

        kb = out_path.stat().st_size // 1024
        speed_note = f" @{speed}x" if speed != 1.0 else ""
        model_note = f" [{model}]"
        print(f"  ok    {wave['filename']}  ({len(turns)} turns, {kb} KB{speed_note}{model_note})")
        return True

    except Exception as e:
        print(f"  ERROR {wave['filename']}: {e}")
        if out_path.exists():
            out_path.unlink()
        return False


def _generate_wave_v3(client, wave, out_path, output_dir,
                      model, vid_for, stability, sub_chunks):
    """Generate a wave using the ElevenLabs Dialogue API (v3 only)."""
    from elevenlabs import DialogueInput
    from elevenlabs.types import ModelSettingsResponseModel

    turns = wave["turns"]
    settings = ModelSettingsResponseModel(stability=stability)

    if len(sub_chunks) == 1:
        inputs = [DialogueInput(text=t["text"], voice_id=vid_for(t["speaker"]))
                  for t in turns]
        audio_iter = client.text_to_dialogue.convert(
            inputs=inputs,
            model_id=model,
            output_format=OUTPUT_FORMAT,
            settings=settings,
        )
        with open(out_path, "wb") as f:
            for chunk in audio_iter:
                f.write(chunk)
    else:
        from pydub import AudioSegment
        combined = AudioSegment.empty()
        for i, chunk_turns in enumerate(sub_chunks):
            inputs = [DialogueInput(text=t["text"], voice_id=vid_for(t["speaker"]))
                      for t in chunk_turns]
            audio_iter = client.text_to_dialogue.convert(
                inputs=inputs,
                model_id=model,
                output_format=OUTPUT_FORMAT,
                settings=settings,
            )
            tmp_path = output_dir / f"_tmp_{wave['index']:02d}_{i}.mp3"
            with open(tmp_path, "wb") as f:
                for chunk in audio_iter:
                    f.write(chunk)
            combined += AudioSegment.from_mp3(tmp_path)
            tmp_path.unlink()
        combined.export(out_path, format="mp3", bitrate="128k")


def _generate_wave_v2(client, wave, out_path, output_dir,
                      model, vid_for, stability):
    """Generate a wave using per-turn TTS calls (v2 multilingual). Strips audio tags."""
    from pydub import AudioSegment

    turns = wave["turns"]
    combined = AudioSegment.empty()

    for i, turn in enumerate(turns):
        text = strip_audio_tags(turn["text"])
        if not text:
            continue

        tmp_path = output_dir / f"_tmp_{wave['index']:02d}_turn_{i:04d}.mp3"
        audio_iter = client.text_to_speech.convert(
            text=text,
            voice_id=vid_for(turn["speaker"]),
            model_id=model,
            output_format=OUTPUT_FORMAT,
            voice_settings={
                "stability": stability,
                "similarity_boost": 0.75,
            },
        )
        with open(tmp_path, "wb") as f:
            for chunk in audio_iter:
                f.write(chunk)
        combined += AudioSegment.from_mp3(tmp_path)
        tmp_path.unlink()

    combined.export(out_path, format="mp3", bitrate="128k")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    load_env()

    parser = argparse.ArgumentParser(description="Generate dialogue audio for a Backbone episode")
    parser.add_argument("topic", help="Episode directory name (e.g. refrigeration)")
    parser.add_argument("--dry-run", action="store_true", help="Plan without calling the API")
    parser.add_argument("--wave", type=int, metavar="N", help="Only generate wave N (0=opening)")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--stability", type=float, default=0.4, metavar="N",
                        help="Voice stability 0.0–1.0 (lower=more expressive, default: 0.4)")
    parser.add_argument("--speed", type=float, default=1.3, metavar="N",
                        help="Playback speed multiplier (default: 1.3). Requires ffmpeg.")
    parser.add_argument("--model", choices=["v3", "v2"], default="v3",
                        help="ElevenLabs model: v3 (Dialogue API, audio tags) or "
                             "v2 (multilingual_v2, per-turn, higher quality). Default: v3")
    args = parser.parse_args()

    model_id = MODEL_V2 if args.model == "v2" else MODEL_V3

    script_path = REPO_ROOT / "episodes" / args.topic / "final" / "assembled.txt"
    output_dir  = REPO_ROOT / "episodes" / args.topic / "assets" / "audio"

    if not script_path.exists():
        print(f"Error: assembled script not found at {script_path}")
        sys.exit(1)

    # Parse and split into waves
    model_suffix = f"_{args.model}"  # "_v3" or "_v2"
    print(f"\nParsing {script_path.name} ...")
    print(f"  Model: {model_id}" + (" (per-turn TTS, audio tags stripped)" if args.model == "v2" else " (Dialogue API)"))
    items = parse_assembled(script_path)
    waves = split_into_waves(items, model_suffix=model_suffix)

    print(f"  {len(waves)} waves found:")
    for w in waves:
        total_chars = sum(len(t["text"]) for t in w["turns"])
        sub_chunks = sub_chunk_wave(w)
        chunk_note = f", {len(sub_chunks)} requests" if len(sub_chunks) > 1 else ""
        print(f"    [{w['index']}] {w['filename']}  —  {len(w['turns'])} turns, {total_chars:,} chars{chunk_note}")

    # Filter to single wave if requested
    if args.wave is not None:
        run_waves = [w for w in waves if w["index"] == args.wave]
        if not run_waves:
            print(f"Error: wave {args.wave} not found")
            sys.exit(1)
    else:
        run_waves = waves

    output_dir.mkdir(parents=True, exist_ok=True)
    already_done = sum(1 for w in run_waves if (output_dir / w["filename"]).exists())
    to_generate  = len(run_waves) - already_done

    print(f"\nOutput: {output_dir}")
    print(f"  Already generated: {already_done}")
    print(f"  To generate:       {to_generate}")

    if args.dry_run:
        print("\n[dry-run] No API calls will be made.\n")
        client = None
        for w in run_waves:
            generate_wave(client, w, output_dir, dry_run=True,
                          stability=args.stability, speed=args.speed,
                          model=model_id)
        return

    if to_generate == 0:
        print("\nAll waves already generated.")
        return

    api_label = "per-turn TTS" if args.model == "v2" else "Dialogue API"
    if not args.yes:
        confirm = input(f"\nGenerate {to_generate} wave(s) via ElevenLabs {api_label}? [y/N] ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            sys.exit(0)

    client = get_client()
    ok, failed = 0, 0

    print()
    for w in run_waves:
        if generate_wave(client, w, output_dir, stability=args.stability, speed=args.speed,
                         model=model_id):
            ok += 1
        else:
            failed += 1

    print(f"\nDone: {ok} generated, {already_done} skipped, {failed} failed")
    if failed:
        print("Re-run to retry failed waves.")


if __name__ == "__main__":
    main()
