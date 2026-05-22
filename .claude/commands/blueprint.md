---
description: Checkpoint 1 — Run Research Director Phase 1 (overview) and Narrative Architect to produce the blueprint, then stop for human review.
argument-hint: <topic>
---

You are running **Checkpoint 1: Blueprint** for the Backbone podcast pipeline.

The topic is: **$ARGUMENTS**

If `$ARGUMENTS` is empty, stop immediately and ask the user which topic to run.

## What this checkpoint does

Two role agents run in sequence:
1. **Research Director (Phase 1)** — broad overview research → `episodes/{topic}/research/overview.md`
2. **Narrative Architect** — story blueprint → `episodes/{topic}/blueprint.md`

After both complete, you stop. Jeff and Cyrus each write solo notes (`episodes/{topic}/feedback/01-jeff-notes.md`, `01-cyrus-notes.md`) before the audio review, then hold a live review meeting and save the transcript to `episodes/{topic}/feedback/01-blueprint.txt`. All three are optional; the next checkpoint reads whatever exists.

## Before you start

1. Verify `episodes/{topic}/` exists. If not, create it along with `research/` and `feedback/` subdirectories.
2. Read or create `episodes/{topic}/pipeline-status.json`. Schema:
   ```json
   {
     "topic": "{topic}",
     "checkpoints": {
       "blueprint": {"status": "pending"},
       "script":    {"status": "pending"},
       "polish":    {"status": "pending"}
     }
   }
   ```
3. If `checkpoints.blueprint.status` is already `"complete"`, warn the user that downstream checkpoints (`script`, `polish`) may have artifacts that will be invalidated by re-running. Ask them to confirm before proceeding. Do NOT delete downstream artifacts automatically.

## Run the agents

Use the Task tool (general-purpose subagent) for each role. Each agent gets a self-contained briefing — they do not see this prompt.

### Step 1: Research Director — Phase 1

Spawn a general-purpose agent with:

- **Task:** "Run Phase 1 (broad overview research) for the Backbone podcast on the topic: **$ARGUMENTS**."
- **Files to read first:** `CLAUDE.md`, `roles/research-director.md` (the full role briefing), `templates/research-overview.md`.
- **Output:** `episodes/$ARGUMENTS/research/overview.md` following the template.
- **Methodology:** Follow the role file. Run 20–40+ web searches. Use `WebSearch` and `WebFetch` heavily. Star the best material with ⭐. Flag uncertainty with `[VERIFY]`, `[GAP]`, `[MISSING PERSPECTIVE]`.
- **No feedback intake at this checkpoint** — Phase 1 is the first thing that runs.

Wait for it to complete. Read the produced overview.md to confirm it landed and looks sane (front matter present, sections populated, ⭐ markers present).

### Step 2: Narrative Architect

Spawn a general-purpose agent with:

- **Task:** "Run the Narrative Architect for the Backbone podcast on the topic: **$ARGUMENTS**. Produce the binding blueprint based on the Research Director's overview."
- **Files to read first:** `CLAUDE.md`, `roles/narrative-architect.md`, `hosts/jeff.md`, `hosts/cyrus.md`, `episodes/$ARGUMENTS/research/overview.md`, `templates/blueprint.md`.
- **Output:** `episodes/$ARGUMENTS/blueprint.md` following the template.
- **Methodology:** Follow the role file. Make editorial decisions, don't just summarize. Define thesis, set wave boundaries, select anchor stories, assign hosts by worldview fit, mark gaps with `[NEEDS RESEARCH]` for Phase 2.

Wait for it to complete. Read blueprint.md to confirm it landed.

## After both agents finish

1. Update `episodes/$ARGUMENTS/pipeline-status.json`: set `checkpoints.blueprint` to `{"status": "complete", "completed_at": "<ISO timestamp>"}`.
2. Print a short status report to the user:
   - Confirm `research/overview.md` and `blueprint.md` exist and were updated
   - Note the wave count from the blueprint and the proposed thesis (one line)
   - Tell them: "Jeff and Cyrus each write solo notes to `episodes/$ARGUMENTS/feedback/01-jeff-notes.md` and `01-cyrus-notes.md` (informal markdown — see existing examples) before the audio review. Hold the review meeting and save the transcript to `episodes/$ARGUMENTS/feedback/01-blueprint.txt`. Then run `/script $ARGUMENTS` to continue. (`/refine` is a single end-of-episode run after all three checkpoint meetings — not per-checkpoint.)"
3. Stop. Do not run any further agents.
