# Production Pipeline

Takes content pipeline output (assembled script, wave audio files, metadata, social content) and produces finished media assets.

---

## Prerequisites

- Episode content complete: `assembled.txt`, `metadata.md`, `show-notes.md`, `social-content.md`
- TTS audio generated: `wave-*.mp3` files in `episodes/{topic}/assets/audio/`
- Python dependencies: `pydub`, `playwright` (for social images)
- System: `ffmpeg` on PATH

---

## Steps

| # | Script | What it does | Input | Output | Auto? | Review? |
|---|--------|-------------|-------|--------|-------|---------|
| 1 | `audio_assemble.py` | Stitch wave files + music into `episode.mp3` with crossfades | wave-*.mp3, assets/music/ | final/episode.mp3, final/assembly-map.json | Yes | No |
| 2 | `timestamp_chapters.py` | Real timestamps from audio; produce chapters.json | assembly-map.json | final/chapters.json, updated metadata.md | Yes | No |
| 3 | `generate_transcript.py` | Reformat script as HTML + SRT (not speech-to-text) | assembled.txt, assembly-map.json | final/transcript.html, final/transcript.srt | Yes | No |
| 4 | `audiogram_video.py` | Cover art + waveform + chapter titles → video | episode.mp3, cover art, chapters.json | assets/video/episode-full.mp4 | Yes | Spot-check |
| 5 | `social_images.py` | Quote cards, stat graphics, announcement, cover | social-content.md, metadata.md | assets/images/*.png | Yes | Yes |
| 6 | `clip_selector.py` | Pick 3-5 highlight segments from script | assembled.txt, social-content.md | assets/clips/clip-manifest.json | Agent | Yes — approve clips |
| 7 | `clip_generate.py` | Cut audio, generate clip videos (16:9 + 9:16) | clip-manifest.json, episode.mp3 | assets/clips/clip-*.mp4 | Yes | No |

---

## Running

```bash
# Full production pipeline with review checkpoints:
python tools/release.py {topic} produce

# Individual steps:
python tools/audio_assemble.py {topic}
python tools/audio_assemble.py {topic} --model v2     # use _v2 wave files
python tools/audio_assemble.py {topic} --no-music      # skip music (insert silence)
python tools/timestamp_chapters.py {topic}
python tools/generate_transcript.py {topic}
python tools/audiogram_video.py {topic}
python tools/social_images.py {topic}
python tools/clip_selector.py {topic}
python tools/clip_generate.py {topic}
```

---

## Output Structure

```
episodes/{topic}/
├── final/
│   ├── episode.mp3           ← assembled episode audio
│   ├── assembly-map.json     ← position map (used by timestamps, clips)
│   ├── chapters.json         ← Podcasting 2.0 chapters
│   ├── metadata.md           ← updated with real timestamps
│   ├── transcript.html       ← styled HTML transcript
│   ├── transcript.srt        ← SRT subtitles (for YouTube)
│   ├── assembled.txt         ← source script (input)
│   ├── show-notes.md         ← companion content (input)
│   └── social-content.md     ← promotional text (input)
├── assets/
│   ├── audio/                ← per-wave TTS files (input)
│   ├── video/episode-full.mp4
│   ├── clips/
│   │   ├── clip-manifest.json
│   │   ├── clip-01.mp4, clip-01-vert.mp4
│   │   └── ...
│   └── images/
│       ├── episode-cover.png
│       ├── announcement.png
│       ├── quote-card-01.png, quote-card-02.png, ...
│       └── stat-graphic-01.png, ...
```

---

## Technical Details

### Audio Assembly
- Uses `pydub` for audio manipulation
- Crossfade spec: 500ms for theme music, 300ms for transition bumpers, 3s fade-out for theme-out
- Produces `assembly-map.json` — a position map tracking each segment's start/end time in the final audio
- `--no-music` flag inserts 1.5s silence at music cue positions (useful before music is selected)

### Audiogram Video
- Uses `ffmpeg` directly with `showwaves` filter for waveform visualization
- Chapter titles overlay with timed `drawtext` filters
- 1920x1080 @ 30fps, H.264, AAC 128kbps

### Social Images
- HTML templates in `templates/social/` rendered via Playwright (headless Chromium)
- Templates use `{{placeholder}}` syntax for dynamic content
- Quote cards: 1200x675 (Twitter/LinkedIn optimal)
- Episode cover: 3000x3000 (podcast app artwork)

### Clip Selection
- Heuristic scoring: social content overlap, speaker diversity, storytelling markers, emotional reactions
- Timestamps derived from assembly-map.json position data
- Manual approval step: edit `clip-manifest.json`, set `approved: true`

### Clip Generation
- Two formats per clip: landscape (1920x1080) and portrait (1080x1920)
- Uses ffmpeg `-ss` seeking for fast extraction
