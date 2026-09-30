# Production & Distribution — Build-Out TODO

Tracks what's left to ship the first episode. See `pipeline/launch-plan.md` for the active plan.

---

## Model + voice lock

- [x] **Eleven v4 (`eleven_v4`) locked as the release model with PVCs (2026-09-28).** v4 released 2026-09-28 with full PVC support; cold-open render on v4 + PVC judged "BY FAR the best" by Jeff. Tools default to `--model v4`, stability 0.5, 1.2x; `VOICE_CLONE=pvc` in `.env`; `release.py produce` renders and assembles `_v4` waves
- [x] **Settings A/B on the cold open only** (never full-episode renders for comparisons — credits): stability 0.3 / 0.5 / 0.7 showed no audible expressiveness difference → **0.7** locked for consistency across ~33 requests; **1.2x** kept over 1.1x (2026-09-28)
- [x] `roles/script-writer.md` updated for v4 (tags, stability 0.7 trade-off, no SSML, sound-effect tag hazard, 190 wpm calibration) (2026-09-28)

History (v3 era):


- [x] ElevenLabs v3 (Dialogue API) locked as the release model (2026-06-25); PVC-on-v3 wait dropped — ElevenLabs docs as of 2026-09-12 still say PVCs are "not fully optimized" for v3 and recommend Instant Voice Clones
- [x] `roles/script-writer.md` rewritten v3-native (audio-tag vocabulary, tag every genuine beat) (2026-06-25)
- [x] PVC/IVC clone selector in TTS tools (`--clone`, `VOICE_CLONE`) (2026-09-11)
- [x] Tool defaults flipped to v3 @ 1.2x; `release.py produce` assembles `_v3` waves (2026-09-12)
- [x] Chapter 01 IVC-vs-PVC A/B on v3 — hosts listened 2026-09-13, chose **IVC** ("not perfect, but launching")
- [x] `VOICE_CLONE=ivc` locked in `.env` (2026-09-13)
- [x] ~~**Naturalness pass (2026-09-24, after Jeff + Cyrus demo listen):** Cyrus re-records his IVC from expressive conversational audio; stock-voice diagnostic — 11 ElevenLabs library voices auditioned at `episodes/refrigeration/assets/audio/auditions/` (reel.mp3), pick a Jeff + Cyrus pair, set `JEFF_VOICE_ID_STOCK` / `CYRUS_VOICE_ID_STOCK` in `.env`, render chapter 01 with `--clone stock`; then A/B stability 0.5 vs 0.0 and 1.0x + silence trim vs 1.2x atempo~~ — superseded by v4 + PVC (2026-09-28)
- [x] **Music interludes shortened (2026-09-28):** Jeff regenerated the music on ElevenLabs Music v2.5 at target lengths — `intro_v2.mp3` 15 s, `bumper_v2.mp3` 5 s, `outro_v2.mp3` 20 s; `audio_assemble.py` defaults to them (new `THEME_OUT_MUSIC` for a separate outro). Ducking under the next line not implemented — revisit only if transitions still feel long
- [x] ~~**Post-launch:** when ElevenLabs fully supports PVCs on v3, re-render released episodes with `--clone pvc`~~ — moot: ep 1 ships on v4 + PVC (2026-09-28)

---

## Open before ship

### Service setup
- [ ] Transistor: submit RSS to Apple Podcasts and Spotify directories (one-time, blocked on first episode in feed)

### Assets
- [x] Per-episode artwork + audiogram backgrounds — v2 design system in `design/`, rendered by `tools/render_art.py refrigeration` (2026-09-29)
- [x] Transistor show art swapped to v2 (`assets/brand/show-cover.png`) (2026-09-29)
- [ ] Transistor ep 1 artwork: upload `episodes/refrigeration/assets/images/episode-cover.png` in the episode's settings (draft still carries the v1 show art)
- [ ] YouTube channel: upload banner + avatar from `assets/brand/`

### Workflow
- [ ] Establish Descript template for full-episode video assembly (waveform + chapter markers + captions)
- [ ] Establish Descript template for vertical shorts

### Code
- [x] `tools/release.py produce` end-to-end on refrigeration (2026-09-13). Fixed on the way: no TTS step + `--no-music` in `release.py`; `measure_lufs` read the first per-frame line (-70 LUFS → +54 dB clip) — now summary-parsed plus a final two-pass `loudnorm` to -16 LUFS / -1.5 dBTP; TTS exited 0 on failed waves and the assembler skipped missing waves silently — both now hard-fail; `timestamp_chapters.py` chapter offset from the theme-in split — now bumper-based
- [ ] `tools/release.py distribute` end-to-end on refrigeration (strip show-notes front matter before upload; sync show-notes timestamps from `chapters.json`)

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
