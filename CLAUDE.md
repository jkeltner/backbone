# Backbone: AI Production Pipeline

This repo is an AI agent pipeline for producing **Backbone: From Breakthrough to Built-In** — a deeply researched, narrative-driven podcast about technological innovations.

Each file in `roles/` is a prompt — a complete briefing for a Claude Code Task agent. Every agent reads this file (shared context) plus its own role file (specific instructions). Templates in `templates/` define output format contracts. The `old_reference/` directory is archived material from the prior human workflow — useful as raw material but not active instructions.

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
[Post-episode chat: Jeff + Cyrus — ~20 min, three questions]
  │
  ▼
Profile Updater ───── Proposed edits to host profiles from chat transcript
```

**Key mechanics:**
- The pipeline runs **end-to-end from a single topic selection** — no manual gates.
- The Research Director runs **twice** — broad overview first, then per-chapter deep dives after the Narrative Architect produces the blueprint.
- The Narrative Architect's blueprint is the **binding creative contract**. All downstream agents build from it.
- Quality control is built into the pipeline: the Editor checks pacing, accuracy, continuity, and voice consistency against host profiles; the Fact Checker verifies claims.
- The Profile Updater closes the feedback loop: post-episode chats between Jeff and Cyrus feed back into the host profiles, improving script quality over time. See `roles/profile-updater.md` for the three questions to orient each chat.

---

## Episode Structure

Every episode follows this structure. All agents need this shared vocabulary.

| Section | Duration | Hosts | Purpose |
|---------|----------|-------|---------|
| **OPENING: The Hook** | 12–18 min | Both | Cold open story, "By the Numbers" stats, "World Before," preview of waves |
| **THE WAVES** (×2–4) | 15–25 min each | Alternate drivers | Each wave: Breakthrough → Diffusion & Resistance → What Changed |
| **BUILT IN: The Big Picture** | 15–20 min | Both | Full arc, The Backbone Test, open questions |

### What Each Wave Contains
- **The Breakthrough** — 2–3 key people with vivid human details, the pivotal moment, failed attempts and near-misses
- **Anchor Stories** — 1–2 specific, vivid, short-form narratives (named person, date, place) that capture larger dynamics in miniature. These are the hardest to find and the most valuable.
- **How It Works** — In the wave that first introduces the core mechanism. Mental model + analogy, not engineering specs. 5 min max.
- **Diffusion & Resistance** — Early adopters, resisters (their arguments were often reasonable), enabling conditions, the tipping point
- **What Changed** — Immediate consequences, winners and losers, the bridge to the next wave (what's now possible but not yet realized)

### The Backbone Test
The show's signature closing framework, applied every episode:
1. **Invisible?** — Has it become infrastructure you only notice when it fails?
2. **What depends on it?** — Map the dependency chain
3. **What's the hidden cost?** — Energy, labor, environment, inequality, fragility
4. **Could we go back?** — How deep is the dependency?
5. **What's next?** — What's still evolving behind the scenes?

### Host Division
Each wave has a **driver** — one host leads the narrative, the other participates and reacts. Hosts alternate waves. Opening and Built In are conversational (both hosts).

### Host Profiles
Full personality profiles for each host are in `hosts/jeff.md` and `hosts/cyrus.md`. The Script Writer reads these before writing any dialogue. They define each host's background, communication style, areas of expertise, and how they interact with each other.

### Show Sign-Off
**[PENDING]** Jeff and Cyrus will decide on the show's signature closing line — the phrase that ends every episode (e.g., Freakonomics' "take care of yourself and if you can, somebody else too"). Once decided, it will be added here and the Script Writer will use it. Until then, scripts should end warmly and include `[FLAG: awaiting signature sign-off line]`.

---

## Directory Structure

```
backbone_auto/
├── CLAUDE.md                    ← this file (shared context for all agents)
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
│   └── blueprint.md
├── episodes/                    ← per-episode working directories
│   └── {topic}/
│       ├── research/            ← research files
│       │   ├── overview.md      ← Phase 1: broad overview
│       │   ├── chapter-01-*.md  ← Phase 2: per-chapter deep dives
│       │   └── chapter-02-*.md
│       ├── blueprint.md         ← story structure (binding contract)
│       ├── script/              ← script.txt files + review artifacts
│       │   ├── chapter-01-*.txt
│       │   ├── chapter-02-*.txt
│       │   ├── editor-notes.md  ← Editor's review notes
│       │   ├── fact-check-report.md ← Fact Checker's report
│       │   └── assembled.txt    ← full episode script
│       ├── profile-update-proposals.md ← Profile Updater's proposed host file edits
│       └── final/               ← assembled deliverables
├── old_reference/               ← v1 templates (archived, not active)
└── assets/                      ← cover art, promo images
```

### File Naming
- **kebab-case** for all filenames
- Chapters numbered with zero-padded prefix: `chapter-01-the-ice-trade.md`
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

**Scope boundaries matter.** Each role has an explicit "you are NOT responsible for" section. The Research Director doesn't make editorial decisions. The Script Writer doesn't fact-check. The Narrative Architect doesn't write scripts. Stay in your lane.

**End-to-end automation.** The pipeline is designed to run from topic selection to finished script without manual intervention. A workflow orchestrator chains agents sequentially — each agent reads the prior agent's output and produces its own deliverable. Quality control is built into the pipeline through the Editor and Fact Checker roles.

---

## Quality Standards

### Research
- Cite every factual claim with a source
- Flag uncertainty: `[VERIFY]` for claims needing verification, `[GAP]` for areas needing more research
- Highlight the best material with ⭐
- Anchor stories are the highest-value research output — prioritize finding them
- Over-research. It's easier to cut than to discover gaps mid-script.

### Narrative
- Specificity over generality — named people, dates, places
- Human drama over summaries — what did it feel like?
- Resistance is often the story — give the resisters their due
- Each wave should feel like a distinct chapter, not a repetitive cycle

### Script
- The primary deliverable is `script.txt` — fully scripted TTS-ready dialogue for ElevenLabs v3
- Full specification: `old_reference/tts_script_instructions.md`
- Speaker labels (`JEFF:` / `CYRUS:`), segment breaks at wave boundaries, audio tags used sparingly
- No markdown, no editorial notes — only speakable content
- Numbers and abbreviations spelled out ("fourteen billion" not "$14B")
- Alternates between stretches of exposition and conversational banter

### AI Limitations
- Knowledge has a cutoff date — verify recent information with web searches
- AI may present plausible-sounding but incorrect information confidently
- Quotes attributed to historical figures are often inaccurate — always verify
- Different sources tell different versions — document disagreements, don't pick one arbitrarily
- When in doubt, go to the primary source
