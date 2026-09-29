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
  python tools/tts_dialogue.py refrigeration                  # v4 Dialogue API @ 1.2x (release config)
  python tools/tts_dialogue.py refrigeration --model v3       # previous release model (comparison)
  python tools/tts_dialogue.py refrigeration --model v2       # legacy per-turn v2 (tags stripped)
  python tools/tts_dialogue.py refrigeration --speed 1.1      # slower playback (default: 1.2)
  python tools/tts_dialogue.py refrigeration --dry-run
  python tools/tts_dialogue.py refrigeration --wave 0
  python tools/tts_dialogue.py refrigeration --yes
  python tools/tts_dialogue.py refrigeration --reprocess      # re-concat from cached per-turn files
  python tools/tts_dialogue.py refrigeration --clone ivc      # use instant voice clones (default: pvc)

Models:
  v4 (default) — eleven_v4 Dialogue API, native multi-speaker, performs audio tags, full PVC
                 support. Release model (locked 2026-09-28). Stability default 0.7.
  v3           — eleven_v3 Dialogue API. Previous release model, kept for comparison renders.
                 Stability default 0.0 = "Creative".
  v2           — eleven_multilingual_v2, per-turn TTS (pydub required), audio tags stripped.
                 Kept for comparison renders only.

Config (set in .env):
  ELEVENLABS_API_KEY
  JEFF_VOICE_ID_PVC / JEFF_VOICE_ID_IVC     professional / instant clone (both optional)
  CYRUS_VOICE_ID_PVC / CYRUS_VOICE_ID_IVC
  JEFF_VOICE_ID_STOCK / CYRUS_VOICE_ID_STOCK  ElevenLabs library voices (diagnostic A/B)
  JEFF_VOICE_ID / CYRUS_VOICE_ID            fallback when no per-clone ID is set
  VOICE_CLONE=pvc|ivc|stock                 default clone when --clone is not passed

Clones:
  pvc (default) — professional voice clones; output files keep their existing names
  ivc           — instant voice clones; wave files and per-turn cache get an extra
                  "_ivc" suffix so PVC and IVC renders can live side by side
  stock         — ElevenLabs library voices (not clones), "_stock" suffix; used for
                  naturalness A/B diagnostics against the clones
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
MODEL_V4 = "eleven_v4"
MODEL_V3 = "eleven_v3"
MODEL_V2 = "eleven_multilingual_v2"
DEFAULT_MODEL = MODEL_V4
MODEL_IDS = {"v4": MODEL_V4, "v3": MODEL_V3, "v2": MODEL_V2}
# Per-model stability default when --stability is not passed
DEFAULT_STABILITY = {"v4": 0.7, "v3": 0.0, "v2": 0.0}
OUTPUT_FORMAT = "mp3_44100_128"

# Voice selector: "pvc" (professional clone), "ivc" (instant clone) or "stock"
# (ElevenLabs library voices, not clones — for A/B diagnostics). PVC is the
# backward-compatible default — its files carry no extra suffix.
CLONE_CHOICES = ("pvc", "ivc", "stock")
DEFAULT_CLONE = "pvc"


def clone_suffix(clone: str) -> str:
    """Filename suffix for a clone choice: "" for pvc, "_ivc" / "_stock" otherwise."""
    return "" if clone == DEFAULT_CLONE else f"_{clone}"

# ElevenLabs Dialogue API limits per request
MAX_INPUTS_PER_REQUEST = 100
MAX_CHARS_PER_REQUEST = 5000

# Audio tags that ElevenLabs v3/v4 handle natively but v2 does not
AUDIO_TAG_RE = re.compile(r"\[(?:laughs?|pause|quietly|sighs?|clears throat|whispers?)[^\]]*\]\s*", re.IGNORECASE)

# Per-turn loudness normalization target (EBU R128, standard for podcasts)
TARGET_LUFS = -16


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


def voice_id_for(speaker: str, clone: str = DEFAULT_CLONE) -> str:
    """Resolve a speaker's voice ID for the chosen clone.

    Looks for {SPEAKER}_VOICE_ID_{CLONE} first (e.g. JEFF_VOICE_ID_IVC), then
    falls back to the plain {SPEAKER}_VOICE_ID. Fails loudly if neither is set —
    never generate with the wrong voice.
    """
    specific = f"{speaker}_VOICE_ID_{clone.upper()}"
    generic = f"{speaker}_VOICE_ID"
    vid = os.environ.get(specific, "") or os.environ.get(generic, "")
    if not vid:
        print(f"Error: {specific} (or {generic}) not set in .env")
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


def sub_chunk_wave(wave: dict, max_inputs: int = MAX_INPUTS_PER_REQUEST,
                   max_chars: int = MAX_CHARS_PER_REQUEST) -> list[list[dict]]:
    """Split a wave's turns into sub-chunks by input count and character count."""
    turns = wave["turns"]
    total_chars = sum(len(t["text"]) for t in turns)
    if len(turns) <= max_inputs and total_chars <= max_chars:
        return [turns]

    chunks = []
    current_chunk = []
    current_chars = 0

    for turn in turns:
        turn_chars = len(turn["text"])
        if current_chunk and (len(current_chunk) >= max_inputs
                              or current_chars + turn_chars > max_chars):
            chunks.append(current_chunk)
            current_chunk = []
            current_chars = 0
        current_chunk.append(turn)
        current_chars += turn_chars

    if current_chunk:
        chunks.append(current_chunk)
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


def measure_lufs(file_path):
    """Measure integrated loudness (LUFS) of an audio file using ffmpeg."""
    import subprocess
    result = subprocess.run(
        ["ffmpeg", "-i", str(file_path), "-af", "ebur128=framelog=verbose", "-f", "null", "/dev/null"],
        capture_output=True, text=True,
    )
    for line in result.stderr.splitlines():
        if "I:" in line and "LUFS" in line:
            m = re.search(r"I:\s*(-?\d+\.?\d*)\s*LUFS", line)
            if m:
                return float(m.group(1))
    return None


def normalize_segment(audio_segment, file_path, target_lufs=TARGET_LUFS):
    """Normalize an AudioSegment to target LUFS. Returns (normalized_audio, adjustment_db).

    For very quiet segments (LUFS below -50 or unmeasurable), falls back to peak
    normalization — sets peak to -1 dBFS then adjusts to approximate the target LUFS.
    """
    current_lufs = measure_lufs(file_path)

    if current_lufs is not None and current_lufs > -50:
        # Normal LUFS-based normalization — no gain cap
        adjustment = target_lufs - current_lufs
        return audio_segment.apply_gain(adjustment), adjustment

    # Fallback: peak normalization for near-silence or unmeasurable segments.
    # Normalize peak to -1 dBFS, then pull back to approximate target LUFS.
    # Typical speech has ~10-14 dB crest factor (peak - LUFS), so -1 dBFS peak
    # ≈ -11 to -15 LUFS. We add a small reduction to land near target.
    peak_dbfs = audio_segment.max_dBFS
    if peak_dbfs < -60:
        # Truly silent — don't amplify noise
        return audio_segment, 0.0
    target_peak = -1.0
    peak_adjustment = target_peak - peak_dbfs
    # Pull back so the result isn't too hot relative to LUFS-normalized segments
    adjustment = peak_adjustment - 3.0
    return audio_segment.apply_gain(adjustment), adjustment


def strip_audio_tags(text: str) -> str:
    """Remove audio tags like [laughs], [pause], etc. that v2 would read aloud."""
    return AUDIO_TAG_RE.sub("", text).strip()


def generate_wave(client, wave: dict, output_dir: Path, dry_run: bool = False,
                  stability: float = 0.4, speed: float = 1.0,
                  model: str = DEFAULT_MODEL, reprocess: bool = False,
                  clone: str = DEFAULT_CLONE) -> bool:
    """Generate audio for a single wave. Uses Dialogue API for v3/v4, per-turn TTS for v2."""
    out_path = output_dir / wave["filename"]
    turns = wave["turns"]
    sub_chunks = sub_chunk_wave(wave)
    use_v2 = (model == MODEL_V2)
    cache_suffix = "_v2" + clone_suffix(clone)  # per-turn cache is only used by the v2 path

    if out_path.exists() and not reprocess:
        print(f"  skip  {wave['filename']}")
        return True

    if dry_run:
        total_chars = sum(len(t["text"]) for t in turns)
        speed_note = f", speed={speed}x" if speed != 1.0 else ""
        mode = "per-turn TTS" if use_v2 else f"{len(sub_chunks)} request(s)"
        print(f"  dry-run  {wave['filename']}  ({len(turns)} turns, {total_chars:,} chars, "
              f"{mode}, model={model}, clone={clone}, stability={stability}{speed_note})")
        return True

    try:
        if reprocess and use_v2:
            # Re-concatenate from cached per-turn files with normalization (no API calls)
            print(f"  reprocess  {wave['filename']}...")
            ok = _reprocess_wave_v2(wave, out_path, output_dir, cache_suffix)
            if not ok:
                print(f"  ERROR: cached per-turn files not found for {wave['filename']}")
                print(f"         Run without --reprocess first to generate and cache per-turn files.")
                return False
        elif use_v2:
            # v2: per-turn generation, cached + normalized, concatenated into a single wave file
            jeff_vid = voice_id_for("JEFF", clone)
            cyrus_vid = voice_id_for("CYRUS", clone)
            vid_for = lambda speaker: jeff_vid if speaker == "JEFF" else cyrus_vid
            _generate_wave_v2(client, wave, out_path, output_dir,
                              model, vid_for, stability, cache_suffix)
        else:
            # v3/v4: Dialogue API (multi-speaker, supports audio tags natively)
            jeff_vid = voice_id_for("JEFF", clone)
            cyrus_vid = voice_id_for("CYRUS", clone)
            vid_for = lambda speaker: jeff_vid if speaker == "JEFF" else cyrus_vid
            _generate_wave_dialogue(client, wave, out_path, output_dir,
                              model, vid_for, stability, sub_chunks)

        if speed != 1.0:
            apply_speed(out_path, speed)

        kb = out_path.stat().st_size // 1024
        speed_note = f" @{speed}x" if speed != 1.0 else ""
        model_note = f" [{model}, {clone}]"
        reprocess_note = " (reprocessed)" if reprocess else ""
        print(f"  ok    {wave['filename']}  ({len(turns)} turns, {kb} KB{speed_note}{model_note}{reprocess_note})")
        return True

    except Exception as e:
        print(f"  ERROR {wave['filename']}: {e}")
        if out_path.exists():
            out_path.unlink()
        return False


def _generate_wave_dialogue(client, wave, out_path, output_dir,
                      model, vid_for, stability, sub_chunks):
    """Generate a wave using the ElevenLabs Dialogue API (v3/v4)."""
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


def _per_turn_cache_dir(output_dir, model_suffix):
    """Return the per-turn cache directory for a given model suffix."""
    cache_dir = output_dir / f"per-turn{model_suffix}"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _per_turn_filename(wave_index, turn_index, speaker):
    """Consistent per-turn cache filename."""
    return f"w{wave_index:02d}-t{turn_index:04d}-{speaker.lower()}.mp3"


def _generate_wave_v2(client, wave, out_path, output_dir,
                      model, vid_for, stability, cache_suffix="_v2"):
    """Generate a wave using per-turn TTS calls (v2 multilingual). Strips audio tags.

    Per-turn files are cached in per-turn{cache_suffix}/ (e.g. per-turn_v2/,
    per-turn_v2_ivc/) for free re-processing later. The clone is part of the
    suffix so a PVC cache is never reused for an IVC render, or vice versa.
    Each turn is LUFS-normalized to -16 LUFS before concatenation.
    """
    from pydub import AudioSegment

    cache_dir = _per_turn_cache_dir(output_dir, cache_suffix)
    turns = wave["turns"]
    combined = AudioSegment.empty()

    for i, turn in enumerate(turns):
        text = strip_audio_tags(turn["text"])
        if not text:
            continue

        cache_path = cache_dir / _per_turn_filename(wave["index"], i, turn["speaker"])

        if cache_path.exists():
            # Use cached per-turn file (no API call)
            seg = AudioSegment.from_mp3(cache_path)
        else:
            # Generate via API and cache
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
            with open(cache_path, "wb") as f:
                for chunk in audio_iter:
                    f.write(chunk)
            seg = AudioSegment.from_mp3(cache_path)

        # Normalize each turn to target LUFS before concatenation
        seg, adj = normalize_segment(seg, cache_path)
        if abs(adj) > 0.5:
            print(f"    turn {i} ({turn['speaker']}): {adj:+.1f} dB", flush=True)
        combined += seg

    combined.export(out_path, format="mp3", bitrate="128k")


def _reprocess_wave_v2(wave, out_path, output_dir, model_suffix):
    """Re-concatenate a wave from cached per-turn files with LUFS normalization.

    No API calls — reads only from the per-turn cache directory.
    Returns True if successful, False if cache files are missing.
    """
    from pydub import AudioSegment

    cache_dir = output_dir / f"per-turn{model_suffix}"
    if not cache_dir.exists():
        return False

    turns = wave["turns"]
    combined = AudioSegment.empty()
    missing = 0

    for i, turn in enumerate(turns):
        text = strip_audio_tags(turn["text"])
        if not text:
            continue

        cache_path = cache_dir / _per_turn_filename(wave["index"], i, turn["speaker"])
        if not cache_path.exists():
            missing += 1
            continue

        seg = AudioSegment.from_mp3(cache_path)
        seg, adj = normalize_segment(seg, cache_path)
        if abs(adj) > 0.5:
            print(f"    turn {i} ({turn['speaker']}): {adj:+.1f} dB", flush=True)
        combined += seg

    if missing:
        print(f"  WARNING: {missing} cached per-turn files missing for {wave['filename']}")
        if len(combined) == 0:
            return False

    combined.export(out_path, format="mp3", bitrate="128k")
    return True


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
    parser.add_argument("--stability", type=float, default=None, metavar="N",
                        help="Voice stability 0.0–1.0 (lower = more expressive, higher = more consistent). "
                             "Default: 0.7 for v4, 0.0 for v3. Raise if a render hallucinates.")
    parser.add_argument("--speed", type=float, default=1.2, metavar="N",
                        help="Playback speed multiplier via ffmpeg atempo (default: 1.2). Requires ffmpeg.")
    parser.add_argument("--model", choices=["v2", "v3", "v4"], default="v4",
                        help="ElevenLabs model: v4 (Dialogue API, audio tags, PVC — release model, default), "
                             "v3 (Dialogue API — previous release model, comparison) or "
                             "v2 (multilingual_v2, per-turn, tags stripped — legacy/comparison)")
    parser.add_argument("--reprocess", action="store_true",
                        help="Re-concatenate from cached per-turn files with LUFS normalization. "
                             "No API calls — requires a prior run that cached per-turn files.")
    parser.add_argument("--clone", choices=list(CLONE_CHOICES),
                        default=os.environ.get("VOICE_CLONE", DEFAULT_CLONE).lower(),
                        help="Which voices to use: pvc (professional clones, default), ivc "
                             "(instant clones) or stock (ElevenLabs library voices). Reads "
                             "{SPEAKER}_VOICE_ID_{CLONE} from .env, falling back "
                             "to {SPEAKER}_VOICE_ID. Default comes from VOICE_CLONE in .env.")
    args = parser.parse_args()

    model_id = MODEL_IDS[args.model]
    if args.stability is None:
        args.stability = DEFAULT_STABILITY[args.model]
    clone = args.clone

    script_path = REPO_ROOT / "episodes" / args.topic / "final" / "assembled.txt"
    output_dir  = REPO_ROOT / "episodes" / args.topic / "assets" / "audio"

    if not script_path.exists():
        print(f"Error: assembled script not found at {script_path}")
        sys.exit(1)

    # Parse and split into waves
    model_suffix = f"_{args.model}" + clone_suffix(clone)  # "_v4", "_v4_ivc", "_v3", ...
    print(f"\nParsing {script_path.name} ...")
    print(f"  Model: {model_id}" + (" (per-turn TTS, audio tags stripped)" if args.model == "v2" else " (Dialogue API)")
          + f", stability {args.stability}, speed {args.speed}x")
    print(f"  Clone: {clone}  (JEFF={voice_id_for('JEFF', clone)}, CYRUS={voice_id_for('CYRUS', clone)})")
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
                          model=model_id, clone=clone)
        return

    if args.reprocess:
        # Re-concatenate from cached per-turn files — no API calls needed
        print(f"\n[reprocess] Re-concatenating from cached per-turn files with LUFS normalization...")
        ok, failed = 0, 0
        for w in run_waves:
            if generate_wave(None, w, output_dir, stability=args.stability, speed=args.speed,
                             model=model_id, reprocess=True, clone=clone):
                ok += 1
            else:
                failed += 1
        print(f"\nDone: {ok} reprocessed, {failed} failed")
        if failed:
            print("Missing cached files — run without --reprocess first to generate them.")
            sys.exit(1)
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
                         model=model_id, clone=clone):
            ok += 1
        else:
            failed += 1

    print(f"\nDone: {ok} generated, {already_done} skipped, {failed} failed")
    if failed:
        print("Re-run to retry failed waves.")
        sys.exit(1)  # make failures visible to release.py — a missing wave must not assemble silently


if __name__ == "__main__":
    main()
