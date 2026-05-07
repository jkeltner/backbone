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

Both agents read `episodes/{topic}/feedback/01-blueprint.txt` (the review meeting transcript from Checkpoint 1) if present and incorporate it. After both complete, you stop. Jeff and Cyrus hold the next review meeting and save the transcript to `episodes/{topic}/feedback/02-script.txt`.

## Before you start

1. Verify `episodes/$ARGUMENTS/blueprint.md` exists. If not, refuse to run and tell the user to run `/blueprint $ARGUMENTS` first.
2. Verify `episodes/$ARGUMENTS/pipeline-status.json` shows `checkpoints.blueprint.status === "complete"`. If not, warn but allow override.
3. Check whether `episodes/$ARGUMENTS/feedback/01-blueprint.txt` exists. If yes, both agents must read it. If no, note this in your status report and proceed without it (this is acceptable — Jeff may choose to skip the meeting).
4. Ensure `episodes/$ARGUMENTS/script/` directory exists.
5. If `checkpoints.script.status` is already `"complete"`, warn the user that downstream `polish` artifacts may be invalidated by re-running. Confirm before proceeding.

## Run the agents

### Step 1: Research Director — Phase 2

Read `episodes/$ARGUMENTS/blueprint.md` yourself first to identify the chapter list (Opening, each Wave, Built In). The Research Director will produce one research file per chapter.

Spawn a general-purpose agent with:

- **Task:** "Run Phase 2 (chapter deep dives) for the Backbone podcast on the topic: **$ARGUMENTS**."
- **Files to read first:** `CLAUDE.md`, `roles/research-director.md`, `episodes/$ARGUMENTS/blueprint.md`, `episodes/$ARGUMENTS/research/overview.md`, `templates/research-chapter.md`. **If `episodes/$ARGUMENTS/feedback/01-blueprint.txt` exists, read it before starting and treat it as binding guidance from Jeff and Cyrus — incorporate concerns, fill any gaps they identified, and use any anecdotes they shared as raw material. Note in your output how you addressed each substantive point.**
- **Output:** One file per chapter in the blueprint: `episodes/$ARGUMENTS/research/chapter-{NN}-{name}.md` (zero-padded chapter numbers, kebab-case names matching the blueprint's chapter titles).
- **Methodology:** Phase 2 is depth, not breadth. Fully develop anchor stories, fill `[NEEDS RESEARCH]` and `[GAP]` markers from the blueprint, end each chapter file with a "Key Details for Script" section.

Wait for completion. Verify each expected chapter research file exists.

### Step 2: Script Writer

Spawn a general-purpose agent with:

- **Task:** "Write TTS-ready chapter scripts for the Backbone podcast on the topic: **$ARGUMENTS**."
- **Files to read first:** `CLAUDE.md`, `roles/script-writer.md`, `hosts/jeff.md`, `hosts/cyrus.md`, `episodes/$ARGUMENTS/blueprint.md`, all `episodes/$ARGUMENTS/research/chapter-*.md`. **If `episodes/$ARGUMENTS/feedback/01-blueprint.txt` exists, read it and incorporate any narrative direction, host-anecdote material, or tone notes. Note in your output how you addressed each substantive point.**
- **Output:** One file per chapter: `episodes/$ARGUMENTS/script/chapter-{NN}-{name}.txt`.
- **Methodology:** Follow the role file. ElevenLabs v3 format, speaker labels, audio tags sparingly, numbers spelled out, music cue markers (`[MUSIC: theme-in]` etc.) at correct positions, segment breaks at wave boundaries. Sign-off line locked verbatim: *"Stay curious, and mind the backbones."*

Wait for completion. Verify chapter scripts exist.

## After both agents finish

1. Update `episodes/$ARGUMENTS/pipeline-status.json`: set `checkpoints.script` to `{"status": "complete", "completed_at": "<ISO timestamp>"}`.
2. Print a short status report:
   - Number of chapter research files produced
   - Number of chapter script files produced
   - Total approximate word count across scripts (rough indicator of episode length)
   - Whether `feedback/01-blueprint.txt` was read or absent
3. Tell the user: "Hold your review meeting. Save the transcript to `episodes/$ARGUMENTS/feedback/02-script.txt`. Then run `/polish $ARGUMENTS`. In parallel, you can run `/refine $ARGUMENTS script` in a separate window once the feedback file is saved."
4. Stop. Do not run any further agents.
