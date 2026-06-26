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
- **Pro-innovation, honest about costs** — the show has a point of view: a slight pro-capitalism, pro-innovation lean. Most of these stories are, at bottom, about how **science and business combine to drive society forward** — creative destruction, free markets solving a problem because a return waits for whoever cracks it, invention becoming innovation when someone makes it scalable and commercial. Let the hosts genuinely admire that. But the lean is honest, not naive: name the real human costs plainly (the displaced butcher who spent thirty years learning his trade) without apologizing for the system that flourished. That honesty is what keeps the lean from sounding like cheerleading.
- **Two people, not a produced show** — the hosts speak as two smart friends having a real conversation. They are never aware of the episode's machinery. The show's internal vocabulary (waves, cold open, segments, By the Numbers, the Backbone Test as a named segment) and host assignments are production scaffolding — felt by the listener, never spoken aloud. See *Host Division* and *Things to Avoid*.
- **Believable beats technically-true** — a statistic that is correctly sourced but *sounds* unbelievable damages trust in everything around it. Every stat must pass two tests: true **and** believable to a smart listener on first hearing. Cut or hedge anything that fails the second, and pair every number with a comparative anchor that helps rather than strains.

### Things to Avoid
- Over-explaining "how it works" (one clear analogy beats five technical paragraphs — 5 min max)
- Treating adoption as inevitable (resistance and contingency are often the story)
- Letting waves blur together (each should feel like a distinct chapter with its own characters)
- Front-loading all the characters (spread human drama across waves)
- Saving all consequences for the end (each wave has its own "what changed")
- Using today's values to judge past decisions
- Worshipping founders (teams, institutions, timing, and luck matter too)
- **Inappropriate language or jokes** — both hosts use casual profanity in private conversation, but Jeff has explicitly stated scripts must be clean. Keep all scripts PG-13 at most. No crude humor, no profanity.
- **Unchecked survivorship bias** — when telling stories of persistence paying off, leave room for the honest observation that many equally persistent people failed. Jeff will naturally flag this; scripts should give him space to — once, lightly, where it fits. Don't dwell or moralize.
- **The echo handoff** — the single most-flagged scripting failure. The next speaker repeating the previous speaker's words (often verbatim) as a reaction or transition: *"Tammany Hall is killed by an ice scandal." / "Tammany Hall is killed by an ice scandal."* Banned as a default. Reactions should be questions, emphasis, additive thoughts, or research-handoffs — not mirrors. Literal repetition is allowed only rarely, as a deliberate earned emphasis.
- **Meta / production language in dialogue** — never let the show's internal structure or production notes be spoken: "this wave," "your wave," "cold open," "segment," "By the Numbers," "I want to leave you with," "that's the through line," "that's a critical reframe," or previewing a disagreement ("this is where we disagree"). Carry transitions with story, not labels.
- **Fake naivety** — writing a host as a dim audience stand-in who's "never thought about" everyday things. Both hosts are smart and curious; genuine discovery is earned by a real find and framed as comparing research ("did you come across…?"), not feigned ignorance.
- **Unbelievable statistics** — a sourced-but-implausible-sounding number ("Americans open the fridge a hundred and seven times a day," "the fridge is the most-touched object in the home, more than the phone," "adoption faster than the smartphone curve"). Cut or hedge; credibility costs more than the stat is worth.

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

| # | Command | Agents run | Pre-meeting Google Doc | Audio review transcript |
|---|---------|-----------|------------------------|------------------------|
| 1 | `/blueprint {topic}` | Research Director (Phase 1) → Narrative Architect | `docs.json["01"]` → fetched `01-blueprint-comments.md` | `01-blueprint.txt` |
| 2 | `/script {topic}` | Research Director (Phase 2) → Script Writer | `docs.json["02"]` → fetched `02-script-comments.md` | `02-script.txt` |
| 3 | `/polish {topic}` | Editor → Fact Checker | `docs.json["03"]` → fetched `03-polish-comments.md` | `03-polish.txt` |

**The pipeline owns feedback-doc creation.** At the end of each checkpoint command, `python tools/create_feedback_doc.py {topic} {NN}` uploads the deliverable (blueprint, script bundle, polished script) to a Google Doc inside `Backbone Feedback / {topic} /` in Jeff's Drive and writes the doc URL to `episodes/{topic}/feedback/docs.json` under the matching key (`"01"`, `"02"`, `"03"`). Jeff and Cyrus comment on the doc inline; no manual upload, no URL pasting. Idempotent — re-running a checkpoint doesn't dupe the doc; if Jeff wants a fresh one, he deletes the key from `docs.json`. **Share the root `Backbone Feedback` folder with Cyrus once, ever** — all sub-folders and docs inherit access.

After each checkpoint, Jeff and Cyrus can produce up to two feedback artifacts in `episodes/{topic}/feedback/`:
- The auto-created Google Doc with both hosts' inline comments added in Drive. The next checkpoint command runs `python tools/fetch_feedback.py {topic} {NN}` which uses the `gws` CLI to export the doc as markdown, fetch comments + replies via the Drive API, and write the comment-annotated `0N-{checkpoint}-comments.md` audit trail. Downstream agents read the `.md`.
- `0N-{checkpoint}.txt` — the audio review meeting transcript.

Both are optional. The next checkpoint's agents read whichever exist and treat them as binding guidance. **Precedence on conflict:** the transcript wins — the live conversation supersedes pre-meeting comments. Comments still carry line-level signal the transcript may not revisit.

### Refinement pass (single end-of-episode run)

After all three review meetings, run `/refine {topic}` once. It re-fetches any Google Docs listed in `docs.json` so every `0N-{checkpoint}-comments.md` is current, then reads all six possible feedback artifacts together (three comment markdowns plus three transcripts) and proposes targeted edits to `roles/` and `hosts/` files at `episodes/{topic}/refinements/proposals.md`. Reading all three meetings in one pass makes cross-checkpoint patterns visible — symptoms that span multiple stages but trace to a single role-file gap. Run in a separate Claude Code window if you want to keep contexts clean; it's safe to run in parallel with `/produce` and `/distribute`. Proposals are applied async by Jeff; Cyrus reviews any `hosts/cyrus.md` changes before they're applied. Out-of-scope changes (CLAUDE.md, templates) are deferred to `/pipeline-review` post-episode.

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
| **OPENING: The Hook** | 8–12 min | Both | Cold open story leads, "World Before" woven in as backstory, a 1–2 sentence teaser (not a full preview). Get into the narrative fast. |
| **THE WAVES** (×2–4) | 15–25 min each | Lead by lens | Each wave: Breakthrough → Diffusion & Resistance → What Changed. The lead shifts to whoever's lens fits the beat, even within a wave. |
| **BUILT IN: The Big Picture** | 15–20 min | Both | "By the Numbers" (present-day scale), Full arc, The Backbone Test, open questions, What the Story Teaches |

**Note on "waves":** the word is internal vocabulary — a structural tool for the team and the blueprint. It is **never spoken on air**. The listener feels chapters through narrative bridges, not labels. "By the Numbers" now lands near the **end** (Acquired-style), not in the opening.

### What Each Wave Contains
- **The Breakthrough** — 2–3 key people with vivid human details (including the backstory that explains *why* they made their central decision), the pivotal moment, failed attempts and near-misses
- **Anchor Stories** — 1–2 specific, vivid, short-form narratives (named person, date, place) that capture larger dynamics in miniature. These are the hardest to find and the most valuable. Each anchor story is preceded by 1–2 sentences of host setup.
- **How It Works** — In the wave that first introduces the core mechanism. Mental model + analogy *and then the actual mechanism* — analogy first, but don't gloss the real thing (what's compressed, what changes state, what gets hot vs. cold, where the energy goes). 5 min max. Structured as dialogue: setup → mechanism → the other host's pushback (the real objection) → resolution + concrete consequence. Led by whoever's lens fits (usually Cyrus for science).
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

### Host Division — by lens, not by chapter
Hosts do **not** take turns "owning" waves. Each owns a **recurring perspective** that threads through the entire episode:
- **Jeff** leads on **history, business, institutions, and policy** — founders and markets, regulatory and antitrust fights, organizational drama, deal mechanics. His instinct runs toward institutional/policy dimensions.
- **Cyrus** leads on **science, systems, and market structure** — how the technology actually works, the physics/chemistry, systemic and economic dynamics, second-order effects at scale. His instinct runs toward structural/systems dimensions.

Whoever's lens fits the beat in front of you **leads that beat**, regardless of where it falls — and the lead can pass back and forth *within* a single wave as the material shifts (business of the ice trade → Jeff; why sawdust insulates → Cyrus → monopoly fight → Jeff). This is what makes the hosts' curiosity authentic: when Cyrus explains the refrigeration cycle, Jeff's questions are *real*, and vice versa.

**The division is felt, never announced.** No "this is your wave," no "I'll take this part." The hand-off is carried by the material — the moment the conversation turns to *how the cold gets made*, Cyrus is simply the one talking. Opening and Built In are the most conversational, but the lens principle holds throughout.

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
│       ├── feedback/            ← per-checkpoint feedback: docs.json (Google Doc URLs per checkpoint) → fetched 0N-{checkpoint}-comments.md (audit trail) + audio review transcript (01-blueprint.txt, 02-script.txt, 03-polish.txt)
│       ├── refinements/         ← /refine side-loop proposals (per-checkpoint role/host edit proposals)
│       ├── feedback.txt         ← post-episode conversation (Jeff + Cyrus)
│       ├── profile-update-proposals.md
│       ├── pipeline-status.json ← content-pipeline checkpoint state
│       ├── release-status.json  ← production/distribution state (managed by release.py)
│       ├── assets/              ← per-episode generated assets (audio/, video/)
│       └── final/               ← assembled deliverables (episode.mp3, transcript, chapters, metadata, show-notes, social-content, assembly-map)
├── assets/                      ← show-level assets
│   ├── show-description.md      ← canonical show copy (tagline, short, long descriptions)
│   ├── show_cover_art.png       ← show-level cover art master (square)
│   └── music/                   ← locked: backbone-theme.mp3, backbone-bumper.mp3
├── pipeline/                    ← technical specs + plans for automated tooling
│   ├── tts-pipeline.md          ← Python/ElevenLabs audio assembly spec
│   ├── production-pipeline.md
│   ├── distribution-pipeline.md
│   ├── launch-plan.md           ← walkable plan to ship ep 1
│   └── TODO.md                  ← open work, pruned
└── tools/                       ← runnable scripts (Python)
    ├── README.md
    ├── audio_assemble.py
    ├── timestamp_chapters.py
    ├── generate_transcript.py
    ├── distribute_podcast.py
    ├── tts_dialogue.py
    ├── tts_generate.py
    ├── split_waves_to_cache.py
    ├── create_feedback_doc.py   ← creates per-checkpoint Google Doc via gws (auto-called by /blueprint, /script, /polish)
    ├── fetch_feedback.py        ← fetches checkpoint Google Doc + comments via gws → .md (audit trail)
    └── release.py               ← master orchestrator
```

**Out of pipeline scope:** Video assembly (audiogram, vertical shorts) is done by hand in Descript using the assembled `episode.mp3` plus externally-generated background images (cover + horizontal full-episode + vertical shorts) dropped into `episodes/{topic}/assets/images/`. Promotion is manual. There is no automated audiogram, clip, social-image, or social-posting tooling in this repo.

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
