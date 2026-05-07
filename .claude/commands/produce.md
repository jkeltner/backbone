---
description: Run the Producer agent (final assembly + metadata + show notes), then chain into the Python production pipeline (TTS, audio assembly, timestamps, transcript).
argument-hint: <topic>
---

You are running **Production** for the Backbone podcast pipeline.

The topic is: **$ARGUMENTS**

If `$ARGUMENTS` is empty, stop immediately and ask the user which topic to run.

This is **not a review checkpoint** — there are no review meetings between steps. It runs straight through, but pauses if the Producer flags issues that need human attention.

## What this command does

1. **Producer agent** — assembles `final/assembled.txt`, generates metadata, show notes, social content
2. **`tools/release.py {topic} produce`** — runs the Python production pipeline (TTS, audio assembly, timestamps, transcript)

## Before you start

1. Verify all `episodes/$ARGUMENTS/script/chapter-*.txt` files exist and `episodes/$ARGUMENTS/script/fact-check-report.md` exists. If not, refuse to run and tell the user to run `/polish $ARGUMENTS` first.
2. Verify `episodes/$ARGUMENTS/pipeline-status.json` shows `checkpoints.polish.status === "complete"`. If not, warn but allow override.

## Step 1: Producer agent

Spawn a general-purpose agent with:

- **Task:** "Run the Producer for the Backbone podcast on the topic: **$ARGUMENTS**. Assemble final deliverables."
- **Files to read first:** `CLAUDE.md`, `roles/producer.md`, all `episodes/$ARGUMENTS/script/chapter-*.txt`, `episodes/$ARGUMENTS/script/editor-notes.md`, `episodes/$ARGUMENTS/script/fact-check-report.md`, `episodes/$ARGUMENTS/blueprint.md`. **If `episodes/$ARGUMENTS/feedback/03-polish.txt` exists, read it for any final notes Jeff and Cyrus made before audio.**
- **Output:** `episodes/$ARGUMENTS/final/assembled.txt`, `final/metadata.md`, `final/show-notes.md`, `final/social-content.md`.
- **Methodology:** Follow the role file. Music cue validation is mandatory — fix placement deterministically rather than flagging. Strip all `[FLAG: ...]`, `[VERIFY]`, `[GAP]` markers from `assembled.txt`. Estimate runtime from word count.

Wait for completion. Verify all four files exist. Read the Producer's final report — if anything is flagged for human attention (runtime over 120 min, unresolved markers, anything else), surface it to the user before continuing.

## Step 2: Python production pipeline

Once the Producer finishes cleanly, shell out to the orchestrator:

```bash
python tools/release.py $ARGUMENTS produce
```

This runs TTS → audio assembly → timestamps → transcript. The script tracks state in `episodes/$ARGUMENTS/release-status.json` and skips already-completed steps.

If the script exits with a non-zero status or pauses for a review gate (e.g., "publish on Transistor"), report what it said to the user and stop. Do not attempt to bypass review gates.

## After both steps finish

Print a final status report:
- Producer deliverables: ✓ assembled.txt (XX,XXX words, ~Y minutes runtime), ✓ metadata.md, ✓ show-notes.md, ✓ social-content.md
- Audio: episode.mp3 size + duration
- Outstanding flags from Producer (if any)
- Next step: `/distribute $ARGUMENTS` to upload to Transistor as a draft, OR `/release-status $ARGUMENTS` to inspect state.
