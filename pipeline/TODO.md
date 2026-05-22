# Production & Distribution — Build-Out TODO

Tracks what's left to ship the first episode. See `pipeline/launch-plan.md` for the active plan.

---

## Hard gate

- [ ] **ElevenLabs Professional Voice Cloning on v3** — ep 1 will not ship until this lands. When it does:
  - Update `roles/script-writer.md` with v3 audio-tag vocabulary
  - Regenerate refrigeration audio on v3 as the quality benchmark
  - Update `pipeline/tts-pipeline.md` model status banner

---

## Open before ship

### Service setup
- [ ] Transistor: submit RSS to Apple Podcasts and Spotify directories (one-time, blocked on first episode in feed)

### Assets
- [ ] Per-episode artwork + audiogram backgrounds (horizontal full-episode, vertical shorts) — generated externally in Claude Design, drop into `episodes/refrigeration/assets/images/`

### Workflow
- [ ] Establish Descript template for full-episode video assembly (waveform + chapter markers + captions)
- [ ] Establish Descript template for vertical shorts

### Code
- [ ] `tools/release.py produce` + `distribute` end-to-end on refrigeration after v3 regeneration

---

## Done
- [x] Music selection + bumper generation; files locked at `assets/music/backbone-{theme,bumper}.mp3` (2026-04-25)
- [x] Transistor account, show config, API key in `.env` (2026-04-25)
- [x] Show description (`assets/show-description.md`)
- [x] Show-level cover art (`assets/show_cover_art.png`)
- [x] `requirements.txt` at repo root
- [x] Pipeline specs: `production-pipeline.md`, `distribution-pipeline.md`
- [x] `audio_assemble.py`, `timestamp_chapters.py`, `generate_transcript.py` tested locally on refrigeration
- [x] `audio_assemble.py` — ID3 tag fix: switched to mutagen (title, artist, album, album_artist, genre, year, track, cover art all verified on refrigeration_beta) (2026-04-26)
- [x] `distribute_podcast.py` — Transistor API tested live: drop status from create payload (use /publish endpoint), form-encoded `episode[field]` keys, plain-text transcript via `episode[transcript_text]` (HTML silently rejected) (2026-04-26)
- [x] `.gitignore` updated for video, clips, images
- [x] Removed automated video/promo/clip tooling — video assembly is Descript by hand; promo is manual (2026-05-22)
