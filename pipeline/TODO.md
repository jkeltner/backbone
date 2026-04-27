# Production, Distribution & Promotion — Build-Out TODO

Tracks what's left to ship the first episode. Items that have been completed or formally deferred have been pruned. See `pipeline/launch-plan.md` for the active plan.

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

### Code gaps
- [ ] `tools/distribute_podcast.py` — test against real Transistor API (confirm draft-mode default)
- [ ] `tools/audio_assemble.py` — ID3 tag sanity check (title, artist, album, track, year, genre, cover art)
- [ ] `tools/release.py` — full produce/distribute end-to-end on refrigeration after v3 regeneration

### Decisions
*(none open)*

---

## Phase 2+: Make It Look Good (deferred until after ep 1)

- [ ] `social_images.py` — install playwright, test all four templates
- [ ] `clip_selector.py` — review selected clips for quality
- [ ] `clip_generate.py` — end-to-end test
- [ ] Revisit local audiogram (`tools/audiogram_video.py` + `tools/distribute_youtube.py`) if Transistor's audio→video isn't good enough

---

## Phase 3+: Drive Awareness (deferred until after ep 1)

- [ ] Twitter/X dev app + `promote_twitter.py`
- [ ] Buttondown account + `distribute_newsletter.py`
- [ ] `promote_prepare.py` review output

---

## Done
- [x] Music selection + bumper generation; files locked at `assets/music/backbone-{theme,bumper}.mp3` (2026-04-25)
- [x] Transistor account, show config, API key in `.env` (2026-04-25)
- [x] Show description (`assets/show-description.md`)
- [x] `requirements.txt` at repo root
- [x] Pipeline specs: `production-pipeline.md`, `distribution-pipeline.md`, `promotion-pipeline.md`
- [x] `audio_assemble.py`, `timestamp_chapters.py`, `generate_transcript.py` tested locally on refrigeration
- [x] `.gitignore` updated for video, clips, images
