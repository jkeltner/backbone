# Backbone Launch Plan — MP3 to Published

## Context

Backbone's script pipeline is producing good output. The next gap is everything that happens *after* the MP3 is assembled: getting the episode onto Spotify and Apple, onto YouTube with a video layer, onto a website, and into the channels where listeners find it.

A previous session scaffolded most of this — `pipeline/production-pipeline.md`, `pipeline/distribution-pipeline.md`, `pipeline/promotion-pipeline.md`, `pipeline/TODO.md`, and ~13 Python tools in `tools/`. Most of that code is written but **untested against real APIs**. This plan is therefore less "what to build from scratch" and more "what to decide, set up, test, and fill in to ship episode 1." The refrigeration episode is the guinea pig — and explicitly a beta. The full pipeline will be re-run on it before publish.

**Decisions locked:**
- **Podcast host:** Transistor.fm ($19/mo) — auto-distributes RSS to Spotify, Apple, and all podcast apps
- **Website:** Transistor's built-in site for launch (revisit PodPage / custom later if SEO or branding becomes a constraint)
- **Launch scope for ep 1:** MVP — audio on Spotify/Apple + YouTube full-episode audio→video + one announcement. Defer clips, scheduled social threads, newsletter automation
- **Short-form video (Shorts/Reels/TikTok):** Skip for ep 1; revisit after launch
- **YouTube video:** Use **Transistor's built-in audio→video pipeline** for ep 1, not the local `tools/audiogram_video.py`. Keeps the launch surface area small. Local audiogram tool is preserved in repo for later.
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

**Coded, API-untested:**
- `tools/distribute_podcast.py` — upload to Transistor as draft

**Coded, deferred from MVP (still in repo, leave alone):**
- `tools/distribute_youtube.py`, `tools/audiogram_video.py` (replaced by Transistor's audio→video for ep 1)
- `tools/distribute_newsletter.py`, `tools/promote_prepare.py`, `tools/promote_twitter.py`, `tools/social_images.py`, `tools/clip_selector.py`, `tools/clip_generate.py`

**Master orchestrator:** `tools/release.py` — tracks step completion in `release-status.json`

**Refrigeration episode artifacts already present** in `episodes/refrigeration_beta/final/`: `episode.mp3` (v2 audio, beta), `assembly-map.json`, `chapters.json`, `transcript.html`, `transcript.srt`, `metadata.md`, `social-content.md`, `show-notes.md`. **All to be regenerated on v3 before publish.** The `_beta` suffix flips off and the directory becomes `episodes/refrigeration/` once ep 1 ships.

---

## Plan

### Phase A — Service setup

1. **Transistor.fm** — DONE 2026-04-25
   - Account created, show configured (title, description, categories: History + Technology, language, author, copyright, explicit flag)
   - Show-level cover art: DONE — uploaded to Transistor
   - API key + Show ID added to `.env`
   - RSS submission to Apple / Spotify directories: **BLOCKED** — needs first episode in feed (which is gated on v3 PVC)

2. **YouTube** — deferred from MVP path (using Transistor's audio→video)
   - If later we want our own audiogram on YouTube, re-enable `tools/distribute_youtube.py` + OAuth setup

3. **Domain** — DONE — `backbone.fm` registered and pointing at Transistor site

### Phase B — Asset prep + visual QA

4. **Show-level cover art (3000×3000 PNG)** — **OPEN**, Jeff working
5. **Music sign-off** — DONE 2026-04-25, files locked at `assets/music/backbone-{theme,bumper}.mp3`
6. ~~Full-episode audiogram visual QA~~ — REMOVED. Using Transistor's audio→video. The `tools/audiogram_video.py` path is parked for later.
7. **Episode metadata polish** — refrigeration still considered beta; pipeline will be re-run before publish, so final metadata gets locked at that point

### Phase C — Close the small code gaps

8. **`requirements.txt` at repo root** — DONE
9. **Dry-run flags in distribution tools**
   - Verify `tools/distribute_podcast.py` supports a draft-mode run that doesn't publish
10. **ID3 tag sanity check on `audio_assemble.py`** — confirm title, artist, album, track, year, genre=Podcast, cover art

### Phase D — End-to-end dry run on refrigeration

11. **Pipeline re-run** (deferred — happens after v3 PVC lands)
    - Regenerate audio on v3 with updated audio-tag vocabulary
    - Re-run audio assembly, transcript, chapters
12. **Run `python tools/release.py distribute refrigeration_beta --dry-run`**
    - Creates a draft episode in Transistor
    - Use Transistor's audio→video to create the YouTube video; keep it unlisted
13. **Fix whatever breaks.**

### Phase E — Launch ep 1 (when ready)

14. **Submit RSS feed to Apple / Spotify** from Transistor dashboard once the first draft episode exists
15. **Flip Transistor episode draft → published**
16. **Flip the Transistor-generated YouTube video unlisted → public**
17. **Post a single launch announcement** — hand-written, not automated

---

## Deferred (post-ep-1 roadmap, not in this plan's scope but tracked)

- **Newsletter launch:** Buttondown setup + `distribute_newsletter.py` test
- **Twitter/X thread automation:** dev app + `promote_twitter.py` + cadence
- **LinkedIn + Instagram:** manual posting from `promote_prepare.py` output
- **Short-form clips:** QA `clip_generate.py`, decide platforms
- **Custom YouTube audiogram:** revisit `tools/audiogram_video.py` + `tools/distribute_youtube.py` if Transistor's video output isn't good enough
- **Scheduling:** cron / Trigger.dev wrapper
- **Analytics rollup:** weekly Transistor + YouTube + Buttondown stats

---

## Critical files

**Read-only references:**
- `pipeline/production-pipeline.md`, `pipeline/distribution-pipeline.md`, `pipeline/promotion-pipeline.md`, `pipeline/TODO.md`
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
2. Transistor's audio→video has produced the YouTube video, unlisted, with correct title and description
3. The Transistor auto-website renders the show correctly
4. `release-status.json` shows production + distribution steps completed for refrigeration

Then flipping both to public + RSS submission to Apple/Spotify = the real launch.

---

## Open items

*(all top-level launch decisions locked — see TODO.md for remaining code-gap and service-setup items)*
