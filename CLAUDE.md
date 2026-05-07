# Backbone: AI Production Pipeline

This repo is an AI agent pipeline for producing **Backbone: From Breakthrough to Built-In** — a deeply researched, narrative-driven podcast about technological innovations.

Each file in `roles/` is a prompt — a complete briefing for a Claude Code Task agent. Every agent reads this file (shared context) plus its own role file (specific instructions). Templates in `templates/` define output format contracts.

---

## The Podcast

**Hosts:** Jeff Keltner and Cyrus Mistry
**Episode Length:** 90–120 minutes
**Release Cadence:** Monthly
**Core Differentiator:** Most tech content skips from "invention" to "winner." Backbone tells the **diffusion story** — the messy middle: who resisted and why, what complementary tech was needed, the tipping point from novelty to inevitability, and the second-order societal effects.

### Tone Principles
- **Narrative-driven** — tell stories, not textbook summaries
- **Human drama over technical achievement** — anchor stories are the backbone of good episodes
- **Accessible explanations** — mental models, not engineering diagrams
- **No "dorm room" debates** — avoid simplistic good/bad framing
- **Historical empathy** — don't judge past decisions by today's values without context
- **Waves, not acts** — treat each technology as an evolving story with multiple chapters

### Things to Avoid
- Over-explaining "how it works" (one clear analogy beats five technical paragraphs — 5 min max)
- Treating adoption as inevitable (resistance and contingency are often the story)
- Letting waves blur together (each should feel like a distinct chapter with its own characters)
- Front-loading all the characters (spread human drama across waves)
- Saving all consequences for the end (each wave has its own "what changed")
- Using today's values to judge past decisions
- Worshipping founders (teams, institutions, timing, and luck matter too)
- **Inappropriate language or jokes** — both hosts use casual profanity in private conversation, but Jeff has explicitly stated scripts must be clean. Keep all scripts PG-13 at most. No crude humor, no profanity.
- **Unchecked survivorship bias** — when telling stories of persistence paying off, leave room for the honest observation that many equally persistent people failed. Jeff will naturally flag this; scripts should give him space to.

---

## Pipeline Overview

```
Topic Selection (human)
  │
  ▼
Research Director ─── Phase 1: Broad Overview
  │
  ▼
Narrative Architect ─ Story Blueprint (chapter breakdown, wave boundaries, anchor stories)
  │
  ▼
Research Director ─── Phase 2: Chapter Deep Dives
  │
  ▼
Script Writer ─────── Chapter-by-chapter script.txt (TTS-ready dialogue)
  │
  ▼
Editor ────────────── Quality, pacing, accuracy, continuity, voice consistency
  │
  ▼
Fact Checker ──────── Verify claims, stats, quotes
  │
  ▼
Producer ──────────── Final assembly, episode metadata, companion content
  │
  ▼
[Post-episode feedback session: Jeff + Cyrus — free-form conversation]
  │  saved as episodes/{topic}/feedback.txt
  ├──────────────────────┐
  ▼                      ▼
Profile Updater       Pipeline Reviewer
(host profile         (pipeline improvement
 proposals)            proposals)
```

**Key mechanics:**
- The pipeline runs through **three human-review checkpoints** invoked by slash commands. Each checkpoint command runs a coherent chunk of agents and stops — Jeff and Cyrus then hold a live review meeting and save the transcript for the next checkpoint to consume.
- The Research Director runs **twice** — broad overview first (in `/blueprint`), then per-chapter deep dives after the Narrative Architect produces the blueprint (in `/script`).
- The Narrative Architect's blueprint is the **binding creative contract**. All downstream agents build from it.
- Quality control is built into the pipeline: the Editor checks pacing, accuracy, continuity, and voice consistency against host profiles; the Fact Checker verifies claims.
- **Two feedback loops close after each episode.** Jeff and Cyrus record a free-form post-episode conversation (`feedback.txt`). The Profile Updater extracts host voice signal and proposes profile edits for async review. The Pipeline Reviewer runs as a **live interactive session** — Jeff works through findings in real time, approves changes, and they're applied immediately to pipeline files. Both read from the same `feedback.txt`.

---

## Checkpoint Structure & Slash Commands

The pipeline is operated via slash commands in `.claude/commands/`. There are three content-pipeline checkpoints with human review meetings between, plus a parallel refinement loop and production wrappers.

### Three content checkpoints

| # | Command | Agents run | Review meeting transcript saved to |
|---|---------|-----------|------------------------------------|
| 1 | `/blueprint {topic}` | Research Director (Phase 1) → Narrative Architect | `episodes/{topic}/feedback/01-blueprint.txt` |
| 2 | `/script {topic}` | Research Director (Phase 2) → Script Writer | `episodes/{topic}/feedback/02-script.txt` |
| 3 | `/polish {topic}` | Editor → Fact Checker | `episodes/{topic}/feedback/03-polish.txt` |

After each checkpoint, Jeff and Cyrus hold a live conversation reviewing the output. The transcript is saved to the path above. The next checkpoint's agents read that file and treat it as binding guidance.

### Parallel refinement loop

After each review meeting, run `/refine {topic} {checkpoint}` in a **separate Claude Code window** from the pipeline-continuation session. It audits `roles/` and `hosts/` against the meeting transcript and proposes targeted edits to those files at `episodes/{topic}/refinements/{NN}-{checkpoint}-proposals.md`. The continuing pipeline never sees these proposals — they're applied async by Jeff. Out-of-scope changes (CLAUDE.md, templates) are deferred to `/pipeline-review` post-episode.

### Production wrappers (no review gates)

| Command | What it runs |
|---------|--------------|
| `/produce {topic}` | Producer agent → `python tools/release.py {topic} produce` (TTS, audio assembly, timestamps, transcript) |
| `/distribute {topic}` | `python tools/release.py {topic} distribute` (Transistor draft upload; pauses at human publish gates) |
| `/release-status {topic}` | Unified status report across `pipeline-status.json` + `release-status.json` |

### Post-episode

| Command | What it runs |
|---------|--------------|
| `/profile-update {topic}` | Profile Updater agent — proposes host-profile edits from `feedback.txt` |
| `/pipeline-review {topic}` | Pipeline Reviewer — live interactive session, edits applied as approved |

### Status tracking

Each episode tracks content-pipeline progress in `episodes/{topic}/pipeline-status.json`:
```json
{
  "topic": "refrigeration",
  "checkpoints": {
    "blueprint": {"status": "complete", "completed_at": "2026-05-07T..."},
    "script":    {"status": "pending"},
    "polish":    {"status": "pending"}
  }
}
```
Production/distribution status is tracked separately in `release-status.json` (managed by `tools/release.py`).

---

## Episode Structure

Every episode follows this structure. All agents need this shared vocabulary.

| Section | Duration | Hosts | Purpose |
|---------|----------|-------|---------|
| **OPENING: The Hook** | 12–18 min | Both | Cold open story, "By the Numbers" stats, "World Before," preview of waves |
| **THE WAVES** (×2–4) | 15–25 min each | Alternate drivers | Each wave: Breakthrough → Diffusion & Resistance → What Changed |
| **BUILT IN: The Big Picture** | 15–20 min | Both | Full arc, The Backbone Test, open questions, What the Story Teaches |

### What Each Wave Contains
- **The Breakthrough** — 2–3 key people with vivid human details (including the backstory that explains *why* they made their central decision), the pivotal moment, failed attempts and near-misses
- **Anchor Stories** — 1–2 specific, vivid, short-form narratives (named person, date, place) that capture larger dynamics in miniature. These are the hardest to find and the most valuable. Each anchor story is preceded by 1–2 sentences of host setup.
- **How It Works** — In the wave that first introduces the core mechanism. Mental model + analogy, not engineering specs. 5 min max. Structured as dialogue: setup → mechanism → non-driving host pushback → resolution + concrete consequence.
- **Diffusion & Resistance** — Early adopters, resisters (their arguments were often reasonable), enabling conditions, the tipping point. **Resistance gets equal time to the breakthrough — if it's shorter, the wave isn't done.**
- **What Changed** — Immediate consequences, winners and losers, the Road Not Taken (what would the world look like if the resistance had won?), the bridge to the next wave

### The Backbone Test
The show's signature closing framework, applied every episode:
1. **Invisible?** — Has it become infrastructure you only notice when it fails?
2. **What depends on it?** — Map the dependency chain
3. **What's the hidden cost?** — Energy, labor, environment, inequality, fragility. Jeff and Cyrus often disagree here — honor that tension.
4. **Could we go back?** — How deep is the dependency?
5. **What's next?** — What's still evolving behind the scenes?

Each question gets 2–3 minutes of genuine discussion, not a summary sentence.

### What the Story Teaches
The Built In section closes with a portable principle from this episode's diffusion story — something specific to what happened, not a generic observation. This is the intellectual payoff of the whole episode and builds the show's identity over time. See the Narrative Architect and Script Writer roles for guidance.

### Host Division
Each wave has a **driver** — one host leads the narrative, the other participates and reacts. **Hosts are assigned by worldview fit, not just rotation.** Jeff's instincts run toward institutional reform; Cyrus's toward structural disruption. The host whose analytical lens fits the wave's central tension should drive it. Opening and Built In are conversational (both hosts).

### Host Profiles
Full personality profiles for each host are in `hosts/jeff.md` and `hosts/cyrus.md`. The Script Writer reads these before writing any dialogue. They define each host's background, communication style, areas of expertise, and how they interact with each other.

### Show Sign-Off
Every episode ends with a two-beat close: a brief wrap-up that tees up the next episode's *type* (without naming the topic), then the signature sign-off line.

**Template:**
> "That's it for this episode of Backbone. We'll be back in a few weeks to dive into another hidden technology that makes the modern world run. Until then — stay curious, and mind the backbones."

The exact wrap-up wording can vary slightly episode to episode (e.g., the bridge sentence may flex to match the just-told story's tone), but the **final line is fixed**:

> **"Stay curious, and mind the backbones."**

Riffed off Whole Earth Catalog's "stay hungry, stay foolish" — repurposed for a show about technological diffusion. The pluralized "backbones" is intentional: it sends the listener back into their own life looking for hidden infrastructure plural, not just the one we just covered.

---

## Directory Structure

```
backbone/
├── CLAUDE.md                    ← this file (shared context for all agents)
├── README.md
├── requirements.txt             ← Python deps for the production/distribution toolchain
├── .env.example                 ← template for required service keys (Transistor, ElevenLabs, etc.)
├── hosts/                       ← host personality profiles (read by Script Writer)
│   ├── jeff.md
│   └── cyrus.md
├── roles/                       ← agent prompt files
│   ├── research-director.md
│   ├── narrative-architect.md
│   ├── script-writer.md
│   ├── editor.md
│   ├── fact-checker.md
│   ├── producer.md
│   └── profile-updater.md
├── templates/                   ← output format contracts
│   ├── research-overview.md
│   ├── research-chapter.md
│   ├── blueprint.md
│   └── social/                  ← HTML templates for social-image rendering
├── episodes/                    ← per-episode working directories
│   └── {topic}/
│       ├── research/            ← research files (overview + per-chapter deep dives)
│       ├── blueprint.md         ← story structure (binding contract)
│       ├── script/              ← script.txt files + review artifacts (editor-notes, fact-check-report)
│       ├── feedback/            ← per-checkpoint review meeting transcripts (01-blueprint.txt, 02-script.txt, 03-polish.txt)
│       ├── refinements/         ← /refine side-loop proposals (per-checkpoint role/host edit proposals)
│       ├── feedback.txt         ← post-episode conversation (Jeff + Cyrus)
│       ├── profile-update-proposals.md
│       ├── pipeline-status.json ← content-pipeline checkpoint state
│       ├── release-status.json  ← production/distribution state (managed by release.py)
│       ├── assets/              ← per-episode generated assets (audio/, video/)
│       └── final/               ← assembled deliverables (episode.mp3, transcript, chapters, metadata, show-notes, social-content, assembly-map)
├── assets/                      ← show-level assets
│   ├── show-description.md      ← canonical show copy (tagline, short, long descriptions)
│   ├── cover_art.png            ← show-level cover art
│   ├── audiogram_background.png
│   ├── promo_image.png
│   └── music/                   ← locked: backbone-theme.mp3, backbone-bumper.mp3
├── pipeline/                    ← technical specs + plans for automated tooling
│   ├── tts-pipeline.md          ← Python/ElevenLabs audio assembly spec
│   ├── production-pipeline.md
│   ├── distribution-pipeline.md
│   ├── promotion-pipeline.md
│   ├── launch-plan.md           ← walkable plan to ship ep 1
│   └── TODO.md                  ← open work, pruned
└── tools/                       ← runnable scripts (Python)
    ├── README.md
    ├── audio_assemble.py
    ├── timestamp_chapters.py
    ├── generate_transcript.py
    ├── distribute_podcast.py
    ├── distribute_youtube.py    (deferred from MVP — Transistor handles audio→video)
    ├── audiogram_video.py       (deferred from MVP)
    ├── tts_dialogue.py
    ├── tts_generate.py
    ├── split_waves_to_cache.py
    ├── release.py               ← master orchestrator
    └── (social_images, clip_selector, clip_generate, promote_*, distribute_newsletter — deferred)
```

### File Naming
- **kebab-case** for all filenames
- Chapters numbered with zero-padded prefix: `chapter-01-the-ice-trade.md`

### Episode Iteration Policy
- **One canonical directory per topic** (`episodes/{topic}/`). No archive directories — git is the version history.
- Iterate in place. Feedback lives in `episodes/{topic}/feedback.txt` and downstream review artifacts (`editor-notes.md`, `fact-check-report.md`, `profile-update-proposals.md`).
- Generalizable lessons from each run get distilled into `pipeline/learnings.md`; the source feedback file is then deleted.
- `episodes/refrigeration_beta/` is the active beta — kept under `_beta` until ep 1 ships so we can iterate audio combinations against a stable script + asset set. Once ep 1 is live, it becomes `episodes/refrigeration/`.

### Front Matter
All deliverables include front matter for status tracking:
```
---
topic: refrigeration
agent: research-director
phase: 1
status: draft | complete
date: 2026-02-16
---
```

---

## How Roles Work

Each role file in `roles/` is a **complete task briefing** — an agent reads it and knows exactly what to do, what to produce, and what standards to meet.

**Mechanics:**
- Agents read: `CLAUDE.md` (this file) + their role file + relevant episode files
- Agents produce specific deliverables following templates in `templates/`
- Agents communicate through **files**, not conversation — one agent's output is another's input
- Flag conflicts or concerns with `[FLAG: ...]` markers in deliverables
- The ⭐ system highlights the best material in research deliverables
- `[MISSING PERSPECTIVE]` marks key voices with no accessible documented record — flag, don't fabricate

**Scope boundaries matter.** Each role has an explicit "you are NOT responsible for" section. The Research Director doesn't make editorial decisions. The Script Writer doesn't fact-check. The Narrative Architect doesn't write scripts. Stay in your lane.

**End-to-end automation.** The pipeline is designed to run from topic selection to finished script without manual intervention. A workflow orchestrator chains agents sequentially — each agent reads the prior agent's output and produces its own deliverable. Quality control is built into the pipeline through the Editor and Fact Checker roles.

---

## Quality Standards

### Research
- Cite every factual claim with a source
- Flag uncertainty: `[VERIFY]` for claims needing verification, `[GAP]` for areas needing more research, `[MISSING PERSPECTIVE]` for key voices with no accessible record
- Highlight the best material with ⭐
- Anchor stories are the highest-value research output — prioritize finding them
- **The Road Not Taken** is as important as the breakthrough: find the competing paths, the near-misses, the alternatives that didn't win
- Statistics need comparative anchors — always pair a number with a before/after, vs.-competitor, or per-person frame
- Over-research. It's easier to cut than to discover gaps mid-script.

### Narrative
- Specificity over generality — named people, dates, places
- Human drama over summaries — what did it feel like?
- Resistance is often the story — give the resisters their due
- Each wave should feel like a distinct chapter, not a repetitive cycle

### Script
- The primary deliverable is `script.txt` — fully scripted TTS-ready dialogue for ElevenLabs v3
- Speaker labels (`JEFF:` / `CYRUS:`), segment breaks at wave boundaries, audio tags used sparingly
- Music cue markers (`[MUSIC: theme-in]`, `[MUSIC: transition-bumper]`, `[MUSIC: theme-out]`) placed at the correct positions — consumed by the TTS pipeline, not spoken
- No markdown, no editorial notes — only speakable content (plus structural markers)
- Numbers and abbreviations spelled out ("fourteen billion" not "$14B")
- Alternates between stretches of exposition and conversational banter
- Full TTS pipeline spec (chunking, ElevenLabs API, audio assembly): `pipeline/tts-pipeline.md`

### AI Limitations
- Knowledge has a cutoff date — verify recent information with web searches
- AI may present plausible-sounding but incorrect information confidently
- Quotes attributed to historical figures are often inaccurate — always verify
- Different sources tell different versions — document disagreements, don't pick one arbitrarily
- When in doubt, go to the primary source
