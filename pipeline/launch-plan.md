# Backbone Launch Plan — MP3 to Published

## Context

Backbone's script pipeline is producing good output. The next gap is everything that happens *after* the MP3 is assembled: getting the episode onto Spotify and Apple, onto YouTube with a video layer, onto a website, and into the channels where listeners find it.

The pipeline scaffolding is `pipeline/production-pipeline.md`, `pipeline/distribution-pipeline.md`, `pipeline/TODO.md`, and the audio/distribution Python tools in `tools/`. The refrigeration episode is the guinea pig. The full pipeline will be re-run on it before publish.

**Decisions locked:**
- **Podcast host:** Transistor.fm ($19/mo) — auto-distributes RSS to Spotify, Apple, and all podcast apps
- **Website:** Transistor's built-in site for launch (revisit PodPage / custom later if SEO or branding becomes a constraint)
- **Launch scope for ep 1:** audio on Spotify/Apple + YouTube full-episode video (assembled in Descript) + one announcement
- **Video assembly:** Done by hand in Descript using assembled audio + externally-generated background images. No automated audiogram or clip generation in this pipeline
- **Per-episode artwork + audiogram backgrounds:** Generated externally (Claude Design), dropped into `episodes/{topic}/assets/images/`. Horizontal backgrounds for full episodes, vertical for shorts
- **Music:** locked to `assets/music/backbone-theme.mp3` and `assets/music/backbone-bumper.mp3` (2026-04-25)
- **Show description:** locked at `assets/show-description.md`; in production on Transistor
- **Categories on Transistor:** History (primary), Technology (secondary)

**Hard gate on ep 1 ship (locked 2026-04-25):** ElevenLabs must enable Professional Voice Cloning on v3. Audio will be regenerated on v3 before publish; v2 audio is not shipping. See `~/.claude/.../memory/project_elevenlabs_v3_pro_clone_wait.md`.

**Out of scope of this plan:** script generation, TTS/audio assembly, host profile refinement, episode 2+ content work.

---

## Current State Summary

**Works end-to-end, locally:**
- `tools/audio_assemble.py` — waves + music → `episode.mp3` + `assembly-map.json`
- `tools/timestamp_chapters.py` — produces Podcasting 2.0 `chapters.json`
- `tools/generate_transcript.py` — produces `transcript.html` + `transcript.srt`

**Coded, API-tested live (2026-04-26):**
- `tools/distribute_podcast.py` — upload to Transistor as draft

**Master orchestrator:** `tools/release.py` — tracks step completion in `release-status.json`

**Out of pipeline (external):**
- Video assembly (audiogram for full episode, vertical for shorts) → Descript
- Per-episode artwork + audiogram backgrounds → Claude Design (external creator)
- Promotion → manual (no automated Twitter/LinkedIn/newsletter tooling)

**Refrigeration status (2026-05-22):** `episodes/refrigeration/` is the live in-flight ep 1. `episodes/refrigeration_beta/` is a completed beta reference (not the active episode). Audio will be regenerated on ElevenLabs v3 before publish.

---

## Plan

### Phase A — Service setup

1. **Transistor.fm** — DONE 2026-04-25
   - Account created, show configured (title, description, categories: History + Technology, language, author, copyright, explicit flag)
   - Show-level cover art: DONE — uploaded to Transistor
   - API key + Show ID added to `.env`
   - RSS submission to Apple / Spotify directories: **BLOCKED** — needs first episode in feed (which is gated on v3 PVC)

2. **YouTube** — uploads done manually from Descript exports. No service setup or API tokens required.

3. **Domain** — DONE — `backbone.fm` registered and pointing at Transistor site

### Phase B — Asset prep

4. **Show-level cover art** — DONE — `assets/show_cover_art.png` (2026-05-22)
5. **Music sign-off** — DONE 2026-04-25, files locked at `assets/music/backbone-{theme,bumper}.mp3`
6. **Per-episode artwork + audiogram backgrounds** — Generated externally in Claude Design; dropped into `episodes/{topic}/assets/images/` before Descript handoff
7. **Episode metadata polish** — locked when the pipeline is re-run on v3 audio

### Phase C — Close the small code gaps

8. **`requirements.txt` at repo root** — DONE
9. **Dry-run flags in distribution tools**
   - Verify `tools/distribute_podcast.py` supports a draft-mode run that doesn't publish
10. **ID3 tag sanity check on `audio_assemble.py`** — confirm title, artist, album, track, year, genre=Podcast, cover art

### Phase D — End-to-end dry run on refrigeration

11. **Pipeline re-run** (deferred — happens after v3 PVC lands)
    - Regenerate audio on v3 with updated audio-tag vocabulary
    - Re-run audio assembly, transcript, chapters
12. **Run `python tools/release.py refrigeration distribute`**
    - Creates a draft episode in Transistor
13. **Assemble video in Descript** from the assembled `episode.mp3` + externally-generated artwork; upload to YouTube as unlisted
14. **Fix whatever breaks.**

### Phase E — Launch ep 1 (when ready)

15. **Submit RSS feed to Apple / Spotify** from Transistor dashboard once the first draft episode exists
16. **Flip Transistor episode draft → published**
17. **Flip YouTube video unlisted → public**
18. **Post a single launch announcement** — hand-written, not automated

---

## Deferred (post-ep-1 roadmap)

- **Analytics rollup:** weekly Transistor + YouTube stats
- **Short-form clips:** decide Descript template + cadence

---

## Critical files

**Read-only references:**
- `pipeline/production-pipeline.md`, `pipeline/distribution-pipeline.md`, `pipeline/TODO.md`
- `tools/release.py` — orchestrator

**Likely to modify in Phase C/D:**
- `tools/distribute_podcast.py` — bug fixes from first real Transistor API run
- `tools/audio_assemble.py` — ID3 tags if missing

**Config:**
- `.env` (not checked in) — `TRANSISTOR_*` keys are the only required keys for the MVP path; `.env.example` lists everything

---

## Verification

The plan is verified when:
1. A draft episode exists on Transistor with correct audio (v3-regenerated), title, description, chapters, transcript
2. A video assembled in Descript is uploaded to YouTube, unlisted, with correct title and description
3. The Transistor auto-website renders the show correctly
4. `release-status.json` shows production + distribution steps completed for refrigeration

Then flipping both to public + RSS submission to Apple/Spotify = the real launch.

---

## Open items

*(all top-level launch decisions locked — see TODO.md for remaining code-gap and service-setup items)*
