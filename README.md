# Backbone: From Breakthrough to Built-In

An AI-powered production pipeline for a deeply researched, narrative-driven podcast about how technologies actually spread — not the invention myth, but the messy middle.

**Hosts:** Jeff Keltner and Cyrus Mistry

---

## The Show

Most tech content skips from "invention" to "winner." Backbone tells the **diffusion story** — the messy middle that gets glossed over: who resisted and why, what complementary infrastructure had to exist first, the tipping point from novelty to inevitability, and the second-order effects that nobody predicted.

Each episode runs 90–120 minutes and follows a consistent structure:

| Section | Length | What It Does |
|---------|--------|--------------|
| **The Hook** | 12–18 min | Cold open scene, "By the Numbers" stats, the world before this technology, wave preview |
| **The Waves** (2–4) | 15–25 min each | The diffusion story, chapter by chapter — breakthrough, resistance, what changed |
| **Built In** | 15–20 min | Full arc, the Backbone Test, what the story teaches |

**The Backbone Test** closes every episode — five questions applied to every technology:
1. *Invisible?* — Has it become infrastructure you only notice when it fails?
2. *What depends on it?* — Map the dependency chain
3. *What's the hidden cost?* — Energy, labor, environment, inequality, fragility
4. *Could we go back?* — How deep is the dependency?
5. *What's next?* — What's still evolving behind the scenes?

---

## How the Pipeline Works

This repo is an AI agent pipeline operated through **slash commands** in Claude Code. Each command runs a coherent chunk of the pipeline and stops at a natural review point. Jeff and Cyrus each write solo notes, then hold a live review meeting and save the transcript. The next command picks up from there — incorporating all of it as binding guidance.

Three content checkpoints, three review meetings, then a single refinement pass and production:

```
Topic Selection (human)
        │
        ▼
  /blueprint {topic}
  ├── Research Director (Phase 1: broad overview)
  └── Narrative Architect (story blueprint)
        │
        ▼
  [Solo notes → 01-jeff-notes.md, 01-cyrus-notes.md]
  [Audio review → episodes/{topic}/feedback/01-blueprint.txt]
        │
        ▼
  /script {topic}
  ├── Research Director (Phase 2: chapter deep dives)
  └── Script Writer (TTS-ready dialogue, chapter by chapter)
        │
        ▼
  [Solo notes → 02-jeff-notes.md, 02-cyrus-notes.md]
  [Audio review → episodes/{topic}/feedback/02-script.txt]
        │
        ▼
  /polish {topic}
  ├── Editor (pacing, voice consistency, continuity)
  └── Fact Checker (claims, stats, quotes)
        │
        ▼
  [Solo notes → 03-jeff-notes.md, 03-cyrus-notes.md]
  [Audio review → episodes/{topic}/feedback/03-polish.txt]
        │
        ▼  (in parallel with /produce, in a separate window)
  /refine {topic}   → role/host edit proposals from all 3 meetings
        │
        ▼
  /produce {topic}
  ├── Producer (final assembly, metadata, show notes)
  └── tools/release.py (TTS → audio assembly → timestamps → transcript)
        │
        ▼
  /distribute {topic}    →  Transistor draft (paused at publish gate)
        │
        ▼
  [Episode ships → Jeff + Cyrus record feedback.txt]
        │
        ├──────────────────────────┐
        ▼                          ▼
  /profile-update {topic}    /pipeline-review {topic}
  (async — proposes          (live session — edits to roles/
   host profile edits)        templates/CLAUDE.md applied
                              in real time)
```

### The three review meetings

Each `/blueprint`, `/script`, `/polish` command stops when its agents finish. Then a three-part feedback flow:

1. **Solo notes (optional but recommended).** Jeff and Cyrus each write their own notes first, saved to `episodes/{topic}/feedback/0N-jeff-notes.md` and `0N-cyrus-notes.md`. Informal markdown — organize by section, keep it terse and opinionated. These catch line-level signal that often gets lost in the live conversation.
2. **Audio review.** You and Cyrus hold a live conversation about the output — what landed, what didn't, anecdotes worth weaving in, anything that needs to change.
3. **Save the transcript** to the path the command tells you (`01-blueprint.txt` / `02-script.txt` / `03-polish.txt`).

The next command's agents read whichever of the three files exist and treat them as binding direction. **Precedence on conflict:** the transcript wins (the live conversation supersedes pre-meeting solo takes), but solo notes carry line-level signal the transcript may not revisit.

The audio review stays the heart of the feedback loop — conversation surfaces what notes don't (personal stories, off-the-cuff reactions, the "huh, I'd never thought of it that way" moments). Solo notes are the supplement: a place to capture specific reactions before the conversation drifts, and a way for Cyrus to weigh in even when scheduling slips the live meeting.

### The /refine side loop

Once all three review meetings are done, run `/refine {topic}` once. It reads every feedback file together — solo notes and audio transcripts across all three checkpoints — and proposes targeted edits to `roles/` and `hosts/` files. These are the fixes that prevent the same issue recurring on future episodes. Proposals are written to `episodes/{topic}/refinements/proposals.md`; Jeff applies the ones that land.

Reading all three meetings at once is what makes cross-checkpoint patterns visible — for example, "the script writer drifted from the blueprint AND the editor didn't catch it AND the fact checker found knock-on errors" is one root-cause story that fragments into disconnected reports if you split it. Run it in a separate Claude Code window from your main production session if you want to keep contexts clean; it's fine to run it in parallel with `/produce` and `/distribute` since those don't depend on `roles/` or `hosts/`.

---

## The Roles

Every role has its own briefing in `roles/`. Agents read `CLAUDE.md` (shared context) plus their role file, then produce specific deliverables.

### Research Director
Runs **twice** per episode. Phase 1 (in `/blueprint`) casts a wide net — source landscape, key figures, anchor story candidates, resistance, enabling conditions. Phase 2 (in `/script`) goes deep on the specific chapters the Narrative Architect has defined. The quality of everything downstream depends on what the Research Director surfaces.

### Narrative Architect
Turns raw research into a **blueprint** — the binding creative contract. Defines wave boundaries, selects and places anchor stories, assigns hosts by worldview fit, specifies the "road not taken" for each wave, and identifies what the episode's diffusion story teaches. Every downstream agent builds from the blueprint.

### Script Writer
Writes fully scripted, TTS-ready dialogue for ElevenLabs v3. Works chapter by chapter, following the blueprint. Manages host knowledge division (one host drives each wave, the other discovers), primes every anchor story with host reaction, and writes How It Works sections as dialogue rather than monologue. Reads the Checkpoint 1 feedback (solo notes + audio transcript) and weaves in any anecdotes Jeff or Cyrus shared.

### Editor
Reviews the assembled script as a continuous episode. Catches continuity gaps, pacing problems, voice drift, planted callbacks that never land, and transitions that complete rather than propel. Also runs a systematic voice consistency check against the host profiles. Reads the Checkpoint 2 feedback (solo notes + audio transcript) and addresses each substantive point.

### Fact Checker
Verifies claims, statistics, and quotes against sources. Produces a report with confidence levels and corrects the chapter scripts in place. Treats anything Jeff or Cyrus flagged in the Checkpoint 2 meeting as Priority 1.

### Producer
Assembles the final episode: the complete script, episode metadata, show notes, and social content. Validates music cue placement and strips all pipeline flags before producing `assembled.txt`.

### Profile Updater *(post-episode)*
Reads `feedback.txt` from the post-episode conversation and proposes specific, evidence-backed edits to the host profiles. Outputs a proposals file for review — host profile changes are sensitive enough to warrant **both Jeff and Cyrus reviewing before anything is applied**.

### Pipeline Reviewer *(post-episode, live session)*
A live Claude Code session rather than an autonomous agent. Jeff opens a session with `feedback.txt`, works through findings one at a time — each finding presented as a specific proposed edit, applied immediately on approval. The output is committed changes to the repo, not a proposals document.

---

## The Host Profiles

`hosts/jeff.md` and `hosts/cyrus.md` are detailed personality profiles — background, communication style, verbal patterns, areas of expertise, and how they interact. The Script Writer reads these before writing a single line of dialogue. They evolve over time through the Profile Updater feedback loop.

**Jeff** brings a technology industry and policy background. His instincts run toward institutional reform — he tends to see resistance as solvable through better leadership or policy, and he builds arguments incrementally, hedging with "I think" and grounding abstractions in examples.

**Cyrus** brings a structural, systems-level lens. His instincts run toward disruption as a structural force — he tends to see resistance as symptomatic rather than fixable, and he speaks with density and directness, using "like" naturally and pivoting mid-thought with "by the way."

Their differing worldviews generate the show's best moments — particularly on the Backbone Test question about hidden costs, and in the "What the Story Teaches" closing beat. The Narrative Architect uses worldview fit to assign which host drives each wave.

---

## Slash Commands

All pipeline operations live in `.claude/commands/`. Every command takes the topic as its argument.

### Content pipeline (with review checkpoints)

| Command | What it runs | Stops at |
|---------|-------------|----------|
| `/blueprint <topic>` | Research Director Phase 1 → Narrative Architect | Solo notes → `feedback/01-jeff-notes.md` + `01-cyrus-notes.md`, then audio review → `feedback/01-blueprint.txt` |
| `/script <topic>` | Research Director Phase 2 → Script Writer | Solo notes → `feedback/02-jeff-notes.md` + `02-cyrus-notes.md`, then audio review → `feedback/02-script.txt` |
| `/polish <topic>` | Editor → Fact Checker | Solo notes → `feedback/03-jeff-notes.md` + `03-cyrus-notes.md`, then audio review → `feedback/03-polish.txt` |

### Production (no review gates)

| Command | What it runs |
|---------|-------------|
| `/produce <topic>` | Producer agent → `tools/release.py {topic} produce` (TTS, audio assembly, timestamps, transcript) |
| `/distribute <topic>` | `tools/release.py {topic} distribute` (Transistor draft; pauses at publish gate) |
| `/release-status <topic>` | Unified status across content checkpoints + production state |

### Side loops and post-episode

| Command | What it runs |
|---------|-------------|
| `/refine <topic>` | After all three review meetings — proposes role/host file edits from every feedback file (solo notes + audio transcripts). Single end-of-episode run. |
| `/profile-update <topic>` | Post-episode — proposes host-profile edits from `feedback.txt`. |
| `/pipeline-review <topic>` | Post-episode — live interactive session, edits to roles/templates/CLAUDE.md applied in real time. |

---

## Directory Structure

```
backbone/
├── CLAUDE.md                        ← shared context read by all agents
├── README.md                        ← this file
├── .claude/
│   └── commands/                    ← slash commands (one .md per command)
├── hosts/
│   ├── jeff.md                      ← Jeff's personality profile
│   └── cyrus.md                     ← Cyrus's personality profile
├── roles/                           ← one prompt file per agent
│   ├── research-director.md
│   ├── narrative-architect.md
│   ├── script-writer.md
│   ├── editor.md
│   ├── fact-checker.md
│   ├── producer.md
│   ├── profile-updater.md
│   └── pipeline-reviewer.md
├── templates/                       ← output format contracts
│   ├── blueprint.md
│   ├── research-overview.md
│   └── research-chapter.md
├── tools/                           ← Python production toolchain
│   ├── release.py                   ← orchestrator (produce / distribute / promote)
│   ├── tts_dialogue.py              ← ElevenLabs v3 dialogue generation
│   ├── audio_assemble.py            ← stitch waves + music into episode.mp3
│   ├── timestamp_chapters.py
│   ├── generate_transcript.py
│   └── distribute_podcast.py        ← Transistor upload
├── pipeline/                        ← specs + plans for the production toolchain
│   ├── tts-pipeline.md
│   ├── production-pipeline.md
│   ├── distribution-pipeline.md
│   ├── launch-plan.md
│   └── learnings.md                 ← distilled lessons from prior runs
├── assets/                          ← show-level: cover art master, music
└── episodes/
    └── {topic}/
        ├── research/
        │   ├── overview.md          ← Phase 1 research
        │   └── chapter-NN-*.md     ← Phase 2 chapter research
        ├── blueprint.md             ← story structure (binding contract)
        ├── script/
        │   ├── chapter-NN-*.txt    ← chapter scripts
        │   ├── editor-notes.md
        │   └── fact-check-report.md
        ├── feedback/                ← per-checkpoint feedback (solo notes + audio transcript)
        │   ├── 01-jeff-notes.md     ← Jeff's solo notes (optional, pre-meeting)
        │   ├── 01-cyrus-notes.md    ← Cyrus's solo notes (optional, pre-meeting)
        │   ├── 01-blueprint.txt     ← audio review transcript
        │   ├── 02-jeff-notes.md
        │   ├── 02-cyrus-notes.md
        │   ├── 02-script.txt
        │   ├── 03-jeff-notes.md
        │   ├── 03-cyrus-notes.md
        │   └── 03-polish.txt
        ├── refinements/             ← /refine proposals (per-checkpoint role/host edits)
        ├── feedback.txt             ← post-episode Jeff + Cyrus conversation
        ├── profile-update-proposals.md
        ├── pipeline-status.json     ← content-pipeline checkpoint state
        ├── release-status.json      ← production/distribution state
        ├── assets/                  ← per-episode audio/video
        └── final/                   ← assembled deliverables (episode.mp3, transcript, etc.)
```

---

## Producing an Episode — Step by Step

A complete episode run, start to finish:

**1. Pick a topic.** Jeff and Cyrus agree on the next backbone technology.

**2. Run `/blueprint <topic>`.** Research Director (Phase 1) and Narrative Architect produce `research/overview.md` and `blueprint.md`. Takes 30–60 minutes of agent time.

**3. Review meeting #1.** Jeff and Cyrus each read the blueprint and write solo notes to `episodes/<topic>/feedback/01-jeff-notes.md` and `01-cyrus-notes.md` (informal markdown, organize by section). Then meet live: does the thesis land? Are the wave boundaries right? Are the anchor story selections vivid enough? Any personal angle either of them want woven in? Save the audio transcript to `feedback/01-blueprint.txt`.

**4. Run `/script <topic>`.** Research Director (Phase 2) deep-dives every chapter; Script Writer produces TTS-ready dialogue. Both agents read all available Checkpoint 1 feedback (notes + transcript). Takes 1–2 hours of agent time.

**5. Review meeting #2.** Same flow: solo notes to `02-jeff-notes.md` / `02-cyrus-notes.md` first, then live conversation. Does the dialogue sound like us? Are the anchor stories landing as scenes? Anything tonally off? Specific lines to change? Save audio transcript to `feedback/02-script.txt`.

**6. Run `/polish <topic>`.** Editor catches continuity, pacing, voice issues; Fact Checker verifies every claim. Both read all available Checkpoint 2 feedback. Takes 30–60 minutes.

**7. Review meeting #3.** Final pass before audio. Solo notes to `03-jeff-notes.md` / `03-cyrus-notes.md`, then meet. Anything else to change? Save audio transcript to `feedback/03-polish.txt`.

**8. Run `/refine <topic>`.** Reads every feedback file across all three checkpoints (solo notes + audio transcripts) and proposes role/host file improvements. Run in a separate window — it's fine in parallel with the next two steps. Jeff applies the proposals that land async; Cyrus reviews any `hosts/cyrus.md` changes before they're applied.

**9. Run `/produce <topic>`.** Producer assembles `final/`; `release.py` generates TTS audio, assembles the episode, builds chapters and transcript.

**10. Run `/distribute <topic>`.** Uploads as a Transistor draft. The script pauses at the publish gate — Jeff publishes manually from the Transistor dashboard.

**11. Episode ships.**

**12. Post-episode conversation.** Jeff and Cyrus record a free-form chat about the episode, the pipeline, what worked, what didn't. Save to `episodes/<topic>/feedback.txt`.

**13. Run `/profile-update <topic>`.** Generates host-profile edit proposals. **Cyrus reviews any proposed changes to `hosts/cyrus.md`** before they're applied.

**14. Run `/pipeline-review <topic>`.** Live session — Jeff works through pipeline-level findings with Claude, applying approved edits to roles, templates, and CLAUDE.md in real time.

---

## What Cyrus Needs to Do

If you're Cyrus, your touchpoints in the pipeline are:

- **Three review meetings per episode** (after `/blueprint`, `/script`, `/polish`). Each is two parts: solo notes to `feedback/0N-cyrus-notes.md` first (informal markdown — organize by section, terse and opinionated), then a live conversation with Jeff. Bring reactions, anecdotes, pushback, anything you want woven into your sections — it all becomes raw material.
- **Post-episode conversation** with Jeff. Free-form. What worked, what didn't, where the script got your voice right or wrong.
- **Reviewing host-profile proposals** that touch `hosts/cyrus.md` before they're applied — you have veto on changes to your own profile.

Everything else is automation. The agents handle research, drafting, editing, fact-checking, assembly, and distribution.

---

## Episodes

| Episode | Status | Notes |
|---------|--------|-------|
| Refrigeration | Beta | Full content pipeline run; awaiting ElevenLabs v3 PVC for final audio regen, then ships as ep 1 |

---

## Key Design Principles

**The blueprint is the contract.** The Narrative Architect's blueprint is what every downstream agent builds from. A weak blueprint produces a weak episode regardless of how well the other agents execute.

**Resistance deserves equal time.** The podcast's differentiator is showing why people fought technology adoption and why their arguments were often reasonable. If the resistance section of any wave is shorter than the breakthrough section, the work isn't done.

**Backstory is thesis.** Every key figure needs a formative backstory that causally explains their central decision — not biographical color, but the link between who they were and what they built.

**Contingency over inevitability.** Every wave specifies the Road Not Taken — the competing path, the near-miss, what the world would have looked like if the resistance had won. This is how the diffusion story becomes intellectually honest rather than a winner's narrative.

**Live conversation drives the feedback loop, solo notes back it up.** The audio review is what surfaces anecdotes, reactions, and "huh, I'd never thought of it that way" moments that become raw material for the hosts. Pre-meeting solo notes catch the line-level stuff the conversation rarely revisits — and let Cyrus weigh in async when scheduling slips the live meeting. The transcript wins on conflict; notes carry the specifics.

**The feedback loop compounds.** Every checkpoint's feedback (solo notes + transcript) feeds `/refine` (immediate role/host improvements). Every post-episode conversation feeds Profile Updater + Pipeline Reviewer (broader pipeline improvements). Over time, the system gets better at sounding like Jeff and Cyrus and at producing episodes they're proud of.
