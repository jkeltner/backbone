---
description: Checkpoint 2 — Run Research Director Phase 2 (chapter deep dives) and Script Writer to produce per-chapter scripts, then stop for human review.
argument-hint: <topic>
---

You are running **Checkpoint 2: Script** for the Backbone podcast pipeline.

The topic is: **$ARGUMENTS**

If `$ARGUMENTS` is empty, stop immediately and ask the user which topic to run.

## What this checkpoint does

Two role agents run in sequence:
1. **Research Director (Phase 2)** — chapter-specific deep dives → `episodes/{topic}/research/chapter-{NN}-{name}.md` (one per chapter)
2. **Script Writer** — TTS-ready dialogue → `episodes/{topic}/script/chapter-{NN}-{name}.txt` (one per chapter)

Both agents read the Checkpoint 1 feedback bundle if present and incorporate it. The bundle is up to three files in `episodes/{topic}/feedback/`:
- `01-jeff-notes.md` — Jeff's solo notes, written before the audio review (markdown, informal)
- `01-cyrus-notes.md` — Cyrus's solo notes, written before the audio review (markdown, informal)
- `01-blueprint.txt` — the audio review meeting transcript

**Precedence when sources conflict:** the transcript is the final word — the live conversation supersedes pre-meeting solo takes. Notes still cover line-level signal the transcript may not revisit.

After both complete, you stop. Jeff and Cyrus then write their `02-jeff-notes.md` / `02-cyrus-notes.md`, hold the next review meeting, and save the transcript to `episodes/{topic}/feedback/02-script.txt`.

## Before you start

1. Verify `episodes/$ARGUMENTS/blueprint.md` exists. If not, refuse to run and tell the user to run `/blueprint $ARGUMENTS` first.
2. Verify `episodes/$ARGUMENTS/pipeline-status.json` shows `checkpoints.blueprint.status === "complete"`. If not, warn but allow override.
3. Check which of these feedback files exist: `episodes/$ARGUMENTS/feedback/01-jeff-notes.md`, `01-cyrus-notes.md`, `01-blueprint.txt`. Both agents must read whichever are present. Note in your status report which were present and which were absent. Proceeding with none is acceptable (Jeff may have skipped the review).
4. Ensure `episodes/$ARGUMENTS/script/` directory exists.
5. If `checkpoints.script.status` is already `"complete"`, warn the user that downstream `polish` artifacts may be invalidated by re-running. Confirm before proceeding.

## Run the agents

### Step 1: Research Director — Phase 2

Read `episodes/$ARGUMENTS/blueprint.md` yourself first to identify the chapter list (Opening, each Wave, Built In). The Research Director will produce one research file per chapter.

Spawn a general-purpose agent with:

- **Task:** "Run Phase 2 (chapter deep dives) for the Backbone podcast on the topic: **$ARGUMENTS**."
- **Files to read first:** `CLAUDE.md`, `roles/research-director.md`, `episodes/$ARGUMENTS/blueprint.md`, `episodes/$ARGUMENTS/research/overview.md`, `templates/research-chapter.md`. **Read any of these Checkpoint 1 feedback files that exist and treat them as binding guidance from Jeff and Cyrus: `episodes/$ARGUMENTS/feedback/01-jeff-notes.md`, `01-cyrus-notes.md`, `01-blueprint.txt`. The transcript wins when it conflicts with a solo note (the live conversation supersedes pre-meeting takes); solo notes still carry line-level signal the transcript may not revisit. Incorporate concerns, fill any gaps they identified, and use any anecdotes they shared as raw material. Note in your output how you addressed each substantive point and which source it came from.**
- **Output:** One file per chapter in the blueprint: `episodes/$ARGUMENTS/research/chapter-{NN}-{name}.md` (zero-padded chapter numbers, kebab-case names matching the blueprint's chapter titles).
- **Methodology:** Phase 2 is depth, not breadth. Fully develop anchor stories, fill `[NEEDS RESEARCH]` and `[GAP]` markers from the blueprint, end each chapter file with a "Key Details for Script" section.

Wait for completion. Verify each expected chapter research file exists.

### Step 2: Script Writer

Spawn a general-purpose agent with:

- **Task:** "Write TTS-ready chapter scripts for the Backbone podcast on the topic: **$ARGUMENTS**."
- **Files to read first:** `CLAUDE.md`, `roles/script-writer.md`, `hosts/jeff.md`, `hosts/cyrus.md`, `episodes/$ARGUMENTS/blueprint.md`, all `episodes/$ARGUMENTS/research/chapter-*.md`. **Read any of these Checkpoint 1 feedback files that exist: `episodes/$ARGUMENTS/feedback/01-jeff-notes.md`, `01-cyrus-notes.md`, `01-blueprint.txt`. Transcript wins on conflict; solo notes carry line-level signal the transcript may not revisit. Incorporate any narrative direction, host-anecdote material, or tone notes. Note in your output how you addressed each substantive point and which source it came from.**
- **Output:** One file per chapter: `episodes/$ARGUMENTS/script/chapter-{NN}-{name}.txt`.
- **Methodology:** Follow the role file. ElevenLabs v3 format, speaker labels, audio tags sparingly, numbers spelled out, music cue markers (`[MUSIC: theme-in]` etc.) at correct positions, segment breaks at wave boundaries. Sign-off line locked verbatim: *"Stay curious, and mind the backbones."*

Wait for completion. Verify chapter scripts exist.

## After both agents finish

1. Update `episodes/$ARGUMENTS/pipeline-status.json`: set `checkpoints.script` to `{"status": "complete", "completed_at": "<ISO timestamp>"}`.
2. Print a short status report:
   - Number of chapter research files produced
   - Number of chapter script files produced
   - Total approximate word count across scripts (rough indicator of episode length)
   - Which Checkpoint 1 feedback files were present (`01-jeff-notes.md`, `01-cyrus-notes.md`, `01-blueprint.txt`)
3. Tell the user: "Jeff and Cyrus each write solo notes to `episodes/$ARGUMENTS/feedback/02-jeff-notes.md` and `02-cyrus-notes.md` before the audio review. Hold the review meeting and save the transcript to `episodes/$ARGUMENTS/feedback/02-script.txt`. Then run `/polish $ARGUMENTS`. (`/refine` is a single end-of-episode run after all three checkpoint meetings — not per-checkpoint.)"
4. Stop. Do not run any further agents.
