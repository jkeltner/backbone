# Production Pipeline

Takes content pipeline output (assembled script, wave audio files, metadata) and produces the finished episode audio plus its companion artifacts (chapters, transcript). Video assembly happens externally in Descript — see "Video handoff" below.

---

## Prerequisites

- Episode content complete: `assembled.txt`, `metadata.md`, `show-notes.md`, `social-content.md`
- TTS audio generated: `wave-*.mp3` files in `episodes/{topic}/assets/audio/`
- Python dependencies: `pydub`
- System: `ffmpeg` on PATH

---

## Steps

| # | Script | What it does | Input | Output | Auto? | Review? |
|---|--------|-------------|-------|--------|-------|---------|
| 1 | `audio_assemble.py` | Stitch wave files + music into `episode.mp3` with crossfades | wave-*.mp3, assets/music/ | final/episode.mp3, final/assembly-map.json | Yes | No |
| 2 | `timestamp_chapters.py` | Real timestamps from audio; produce chapters.json | assembly-map.json | final/chapters.json, updated metadata.md | Yes | No |
| 3 | `generate_transcript.py` | Reformat script as HTML + SRT (not speech-to-text) | assembled.txt, assembly-map.json | final/transcript.html, final/transcript.srt | Yes | No |

---

## Running

```bash
# Full production pipeline:
python tools/release.py {topic} produce

# Individual steps:
python tools/audio_assemble.py {topic}
python tools/audio_assemble.py {topic} --model v2     # use _v2 wave files
python tools/audio_assemble.py {topic} --no-music      # skip music (insert silence)
python tools/timestamp_chapters.py {topic}
python tools/generate_transcript.py {topic}
```

---

## Output Structure

```
episodes/{topic}/
├── final/
│   ├── episode.mp3           ← assembled episode audio (handoff to Descript)
│   ├── assembly-map.json     ← position map (used by timestamps)
│   ├── chapters.json         ← Podcasting 2.0 chapters
│   ├── metadata.md           ← updated with real timestamps
│   ├── transcript.html       ← styled HTML transcript
│   ├── transcript.srt        ← SRT subtitles
│   ├── assembled.txt         ← source script (input)
│   ├── show-notes.md         ← companion content (input)
│   └── social-content.md     ← promotional text (input)
└── assets/
    ├── audio/                ← per-wave TTS files (input)
    └── images/               ← externally-generated artwork (episode cover + audiogram backgrounds, horizontal and vertical); used by Descript
```

---

## Technical Details

### Audio Assembly
- Uses `pydub` for audio manipulation
- Crossfade spec: 500ms for theme music, 300ms for transition bumpers, 3s fade-out for theme-out
- Produces `assembly-map.json` — a position map tracking each segment's start/end time in the final audio
- `--no-music` flag inserts 1.5s silence at music cue positions (useful before music is selected)
- Embeds ID3 tags (title, artist, album, track, year, genre=Podcast, cover art from `assets/show_cover_art.png`)

---

## Video handoff

Audiogram and short-form video are assembled by hand in **Descript** using:
- The assembled `episode.mp3` from this pipeline
- Externally-generated per-episode artwork (cover art + audiogram backgrounds, horizontal for full episodes and vertical for shorts) — dropped into `episodes/{topic}/assets/images/`
- Descript templates for waveform overlay, chapter markers, and captions

The pipeline does not generate video. Tools for automated audiogram and clip generation have been removed; git history is the safety net if a future episode needs to revisit them.
