---
description: Checkpoint 3 — Run Editor and Fact Checker against the chapter scripts, then stop for human review before audio production.
argument-hint: <topic>
---

You are running **Checkpoint 3: Polish** for the Backbone podcast pipeline.

The topic is: **$ARGUMENTS**

If `$ARGUMENTS` is empty, stop immediately and ask the user which topic to run.

## What this checkpoint does

Two role agents run in sequence:
1. **Editor** — quality, pacing, continuity, voice consistency → `episodes/{topic}/script/editor-notes.md` + revised chapter scripts
2. **Fact Checker** — verifies claims, stats, quotes → `episodes/{topic}/script/fact-check-report.md` + corrected chapter scripts

Both agents read `episodes/{topic}/feedback/02-script.txt` if present. After both complete, you stop. Jeff and Cyrus hold the final review meeting before audio and save the transcript to `episodes/{topic}/feedback/03-polish.txt`.

## Before you start

1. Verify `episodes/$ARGUMENTS/script/chapter-*.txt` files exist. If not, refuse to run and tell the user to run `/script $ARGUMENTS` first.
2. Verify `episodes/$ARGUMENTS/pipeline-status.json` shows `checkpoints.script.status === "complete"`. If not, warn but allow override.
3. Check whether `episodes/$ARGUMENTS/feedback/02-script.txt` exists. If yes, both agents must read it. If no, note this and proceed without it.

## Run the agents

### Step 1: Editor

Spawn a general-purpose agent with:

- **Task:** "Run the Editor pass for the Backbone podcast on the topic: **$ARGUMENTS**."
- **Files to read first:** `CLAUDE.md`, `roles/editor.md`, `roles/script-writer.md` (for the format contract), `hosts/jeff.md`, `hosts/cyrus.md`, `episodes/$ARGUMENTS/blueprint.md`, all `episodes/$ARGUMENTS/script/chapter-*.txt`. **If `episodes/$ARGUMENTS/feedback/02-script.txt` exists, read it and treat it as binding guidance — incorporate concerns about pacing, voice, anchor stories, transitions, or any specific lines flagged. Note in your editor-notes how you addressed each substantive point.**
- **Output:** `episodes/$ARGUMENTS/script/editor-notes.md` AND revised chapter script files (overwrite originals in place).
- **Methodology:** Follow the role file. Read the full episode end-to-end first, then go back for line edits. Apply edits directly to chapter files; document them in editor-notes.md. Add `[FLAG: ...]` markers for the Fact Checker on claims that need verification.

Wait for completion. Verify editor-notes.md and revised chapter files exist.

### Step 2: Fact Checker

Spawn a general-purpose agent with:

- **Task:** "Run the Fact Checker pass for the Backbone podcast on the topic: **$ARGUMENTS**."
- **Files to read first:** `CLAUDE.md`, `roles/fact-checker.md`, all `episodes/$ARGUMENTS/script/chapter-*.txt` (already edited), `episodes/$ARGUMENTS/script/editor-notes.md`, `episodes/$ARGUMENTS/research/overview.md`, all `episodes/$ARGUMENTS/research/chapter-*.md`. **If `episodes/$ARGUMENTS/feedback/02-script.txt` exists, read it — Jeff and Cyrus may flag specific factual concerns or new claims they want verified. Note in your fact-check-report how you addressed each substantive point.**
- **Output:** `episodes/$ARGUMENTS/script/fact-check-report.md` AND corrected chapter script files (overwrite in place — minimal changes, fix facts only, preserve voice).
- **Methodology:** Follow the role file. Priority order: numbers, quotes, historical claims, editor flags, research `[VERIFY]` markers. Use `WebSearch` and `WebFetch` for independent verification. Verdicts: Verified / Likely Correct / Unverifiable / Disputed / Incorrect / Fabricated.

Wait for completion. Verify fact-check-report.md and corrected chapter files exist.

## After both agents finish

1. Update `episodes/$ARGUMENTS/pipeline-status.json`: set `checkpoints.polish` to `{"status": "complete", "completed_at": "<ISO timestamp>"}`.
2. Print a short status report:
   - Editor: number of voice consistency flags, line edits, continuity issues found
   - Fact Checker: claims checked, corrections made, unverified flags remaining
   - Whether `feedback/02-script.txt` was read or absent
3. Tell the user: "Hold your final review meeting before audio. Save the transcript to `episodes/$ARGUMENTS/feedback/03-polish.txt`. Once you're satisfied, run `/produce $ARGUMENTS` to assemble and generate audio. In parallel, you can run `/refine $ARGUMENTS polish` in a separate window once the feedback file is saved."
4. Stop. Do not run any further agents.
