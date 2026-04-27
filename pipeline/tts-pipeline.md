# TTS Pipeline: Backbone Audio Assembly

This document is the technical spec for the automated Python/ElevenLabs workflow that converts a finished script into a produced audio episode. Build against this spec — the script format contract is defined here.

> **Model status (as of 2026-04-26):** v2 multilingual is the current target. Episode 1 launch is gated on ElevenLabs enabling Professional Voice Cloning on v3. **Scripts are now authored for v3** — see `roles/script-writer.md` "Audio Tags (Eleven v3)" — so when v3 PVC lands, the script writing surface is already aligned. Until then, audio tags are **stripped before TTS** in the v2 path; punctuation and capitalization are preserved (v2 honors them too).
>
> When v3 PVC lands: regenerate refrigeration on v3 as the quality benchmark, flip `MODEL_ID` to `eleven_v3`, and stop stripping audio tags (see Audio Tags section below for the pass-through contract).

---

## Overview

```
episodes/{topic}/final/assembled.txt
  │
  ▼
Parse: split into text chunks + music cue markers
  │
  ├── Text chunks → ElevenLabs v2 multilingual API (per-turn TTS)
  │                       │
  │                       ▼
  │              audio segments (per turn)
  │
  └── Music cues → resolve to audio files in assets/music/
  │
  ▼
Assemble: interleave audio segments + music files in order
  │
  ▼
episodes/{topic}/final/episode.mp3
```

---

## Input: `assembled.txt` Format Contract

The script uses these structural markers (all non-spoken, stripped before TTS):

### Speaker Labels
Every spoken turn starts with a speaker label on a new line:
```
JEFF: Spoken text here.

CYRUS: Response here.
```
Speaker labels map to ElevenLabs voice IDs (see Voice IDs section below).

### Segment Breaks
Mark generation boundaries within the script. Used as chunking points:
```
--- SEGMENT BREAK: Wave 2 - The Mechanical Age ---
```

### Music Cue Markers
On their own line, surrounded by blank lines:
```
[MUSIC: theme-in]
[MUSIC: transition-bumper]
[MUSIC: theme-out]
```

### Audio Tags
Inline delivery instructions for ElevenLabs v3:
```
JEFF: And then... [pause] nothing.
CYRUS: [laughs] That's what I was afraid of.
```

---

## Parsing Strategy

1. **Read** `assembled.txt`
2. **Strip** front matter block (`---` ... `---` at top of file)
3. **Split** on music cue markers — each `[MUSIC: ...]` line is a split point
4. Within each text block, **split further** at segment breaks (`--- SEGMENT BREAK: ... ---`)
5. Each resulting text chunk is a **TTS generation unit**
6. Track the **ordered sequence** of all units (text chunks + music cues) for assembly

### Chunk Size
- ElevenLabs v3 supports up to ~5,000 characters per API call
- Segment breaks are the natural chunking boundary and should keep chunks well under this limit
- If a chunk between two segment breaks exceeds 4,000 characters, split at a paragraph boundary (blank line between turns)

---

## ElevenLabs v2 Multilingual API

### Per-Turn TTS
Using `eleven_multilingual_v2` with per-turn generation — each speaker turn is a separate API call. This produces warmer, more natural conversational speech than the v3 Dialogue API.

Per-turn audio files are cached in `per-turn_v2/` for free re-processing (LUFS normalization, speed adjustment) without additional API calls.

### Voice IDs
Store voice IDs in a config file (not hardcoded):
```
# pipeline/config.py (or .env)
JEFF_VOICE_ID = "..."
CYRUS_VOICE_ID = "..."
```
Voice IDs are assigned when the ElevenLabs voices are created/cloned. Update config when voices change.

### Audio Tags

**Under v2 (current):** All bracketed audio tags are **stripped** before sending to the API — v2 would read them aloud. The script source retains them for v3.

**Under v3 (future, post-PVC):**
- Tags from the Script Writer's approved vocabulary (see `roles/script-writer.md`) are **passed through** unchanged.
- `[MUSIC: ...]` cue markers are *always* stripped (they are pipeline directives, not v3 tags) — handled by the music-cue parser, not the tag handler.
- Unknown tags are stripped and logged (warning, not error) — see Error Handling below.
- Stability setting: **Natural** (balanced — Creative drifts too far for our format; Robust ignores too many tags).

### Output Format
Request `mp3_44100_128` for production quality. Save each chunk as a temp file:
```
/tmp/backbone/{topic}/chunk-001.mp3
/tmp/backbone/{topic}/chunk-002.mp3
...
```

---

## Music Files

Locked 2026-04-25. Resolved from `assets/music/` based on the cue name:

| Cue marker | File | Notes |
|------------|------|-------|
| `[MUSIC: theme-in]` | `assets/music/backbone-theme.mp3` | Full theme |
| `[MUSIC: transition-bumper]` | `assets/music/backbone-bumper.mp3` | 5–10 sec version |
| `[MUSIC: theme-out]` | `assets/music/backbone-theme.mp3` | Same as theme-in, faded out |

Defaults are baked into `tools/audio_assemble.py`. Override via env vars only if intentionally swapping music:
```
THEME_MUSIC=assets/music/backbone-theme.mp3
TRANSITION_BUMPER=assets/music/backbone-bumper.mp3
```

---

## Assembly

Use a library like `pydub` to assemble audio segments in order:

```python
# Pseudocode
segments = parse_assembled_script("assembled.txt")  # returns ordered list of TextChunk | MusicCue

audio = AudioSegment.empty()
for segment in segments:
    if isinstance(segment, TextChunk):
        chunk_audio = generate_tts(segment)  # ElevenLabs API call
        audio += chunk_audio
    elif isinstance(segment, MusicCue):
        music_audio = load_music(segment.cue_name)  # from assets/music/
        if segment.cue_name == "theme-out":
            music_audio = music_audio.fade_out(THEME_OUT_FADE_DURATION * 1000)
        audio += music_audio

audio.export("episodes/{topic}/final/episode.mp3", format="mp3", bitrate="128k")
```

### Crossfade / Overlap
- Theme-in: 500ms crossfade between cold open audio and music (avoids hard cut)
- Transition bumpers: 300ms crossfade on both sides
- Theme-out: fade the music over the last 3 seconds of spoken audio (overlap, don't follow)

---

## Output

```
episodes/{topic}/final/
├── assembled.txt        ← input (script)
├── episode.mp3          ← final produced audio (with ID3 tags + cover art)
├── metadata.md          ← episode metadata (from Producer agent)
├── show-notes.md
└── social-content.md
```

### ID3 Tags

ID3v2.4 tags are written via **mutagen** *after* pydub exports the MP3 — pydub's `tags=`/`cover=` export kwargs do not reliably write ID3 frames to MP3 output.

| Frame | Source |
|---|---|
| `TIT2` (title) | `metadata.md` "Top choice:" line; falls back to `Backbone: {topic}` |
| `TPE1` (artist) | "Jeff Keltner & Cyrus Mistry" |
| `TPE2` (album artist) | "Backbone" |
| `TALB` (album) | "Backbone: From Breakthrough to Built-In" |
| `TCON` (genre) | "Podcast" |
| `TDRC` (year) | Current year |
| `TRCK` (track) | Episode number from `metadata.md`, defaults to "1" |
| `APIC` (cover) | `assets/cover_art.png` (front cover, embedded at 2048×2048) |

---

## Configuration File

Create `pipeline/config.py` (or `pipeline/config.yaml`) to hold all tunable parameters:

```python
# Voice IDs
JEFF_VOICE_ID = ""
CYRUS_VOICE_ID = ""

# Music
THEME_MUSIC = "assets/music/backbone-theme.mp3"
TRANSITION_BUMPER = "assets/music/backbone-bumper.mp3"
THEME_OUT_FADE_DURATION = 3  # seconds

# ElevenLabs
ELEVENLABS_API_KEY = ""  # load from environment, don't hardcode
MODEL_ID = "eleven_multilingual_v2"
OUTPUT_FORMAT = "mp3_44100_128"

# Chunking
MAX_CHUNK_CHARS = 4000

# Assembly
CROSSFADE_THEME_MS = 500
CROSSFADE_BUMPER_MS = 300
```

---

## Error Handling

- **API failures**: retry up to 3 times with exponential backoff before failing the chunk
- **Missing voice ID**: fail loudly with a clear message — don't generate with wrong voice
- **Missing music file**: fail loudly — don't produce an episode silently missing its music
- **Chunk too long**: split automatically and log a warning (not an error)
- **Unknown audio tag**: strip and log — don't fail the whole generation

---

## Development Notes

- Build chunked generation first (text → audio files), test with a short section
- Add music assembly second, after TTS is working
- The script format is stable — `assembled.txt` files produced by the pipeline are already music-cue-annotated and ready for this workflow
