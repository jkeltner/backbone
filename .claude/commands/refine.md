---
description: Side-loop — read a checkpoint feedback transcript and propose edits to roles/ and hosts/ files. Does NOT modify those files directly. Run in a separate window from the continuing pipeline.
argument-hint: <topic> <checkpoint>
---

You are running the **Refinement Loop** for the Backbone podcast pipeline.

Arguments: **$ARGUMENTS**

Expected format: `<topic> <checkpoint>` where checkpoint is one of `blueprint`, `script`, or `polish`.

If `$ARGUMENTS` doesn't parse into both, stop and ask the user. Example: `/refine refrigeration blueprint`.

## What this command does

This is a **separate, parallel refinement loop** — independent of the main pipeline progression. After each review meeting, Jeff (and ideally Cyrus) save a transcript. This command reads that transcript and audits the role and host files for edits that would prevent the same issue from recurring on future episodes.

You produce **proposals only**. You do NOT edit `roles/` or `hosts/` files directly. Jeff reviews the proposals async and applies the ones that land.

## Before you start

1. Parse arguments. Extract `topic` and `checkpoint`.
2. Map checkpoint to the feedback file:
   - `blueprint` → `episodes/{topic}/feedback/01-blueprint.txt`
   - `script` → `episodes/{topic}/feedback/02-script.txt`
   - `polish` → `episodes/{topic}/feedback/03-polish.txt`
3. Verify the feedback file exists. If not, stop and tell the user to save the meeting transcript first.

## Run the audit

Spawn a general-purpose agent with:

- **Task:** "Audit the Backbone pipeline's role and host files against meeting feedback. Propose targeted edits that would prevent the same issue from recurring on future episodes. Do NOT edit any files directly — produce a proposals document only."
- **Files to read:**
  - The feedback transcript at the path above
  - All files in `roles/` (research-director, narrative-architect, script-writer, editor, fact-checker, producer, profile-updater, pipeline-reviewer)
  - Both `hosts/jeff.md` and `hosts/cyrus.md`
  - `pipeline/learnings.md` (for what's already been distilled — don't re-propose lessons already applied)
  - The relevant episode artifact for context (e.g., for `blueprint` checkpoint, `episodes/{topic}/blueprint.md` and `research/overview.md`; for `script`, the chapter scripts; for `polish`, editor-notes.md and fact-check-report.md)
- **Output:** `episodes/{topic}/refinements/{NN}-{checkpoint}-proposals.md` where NN is `01`, `02`, or `03` to match the feedback file numbering.
- **Methodology:**
  1. Read the feedback transcript end-to-end. Extract every substantive concern, suggestion, or pattern.
  2. For each, decide whether it's:
     - **Episode-specific** (only relevant to this topic) → don't propose role/host edits, just note it
     - **Generalizable** (would recur on future episodes) → propose a specific edit to the relevant role or host file
     - **Already covered** (the role file already says this; the agent didn't follow it) → flag as compliance issue, not a role-file gap
  3. Stay in scope: only propose edits to `roles/*.md` and `hosts/*.md`. CLAUDE.md and template changes go through `/pipeline-review` post-episode — note them in a "Out of scope — defer to /pipeline-review" section instead.
  4. For each proposed edit, include: target file, the existing text being changed (with enough context to locate it), the proposed replacement, and a 1–2 sentence rationale citing the feedback.

## Output format

The proposals file should be structured for fast async review. Suggested layout:

```markdown
---
topic: {topic}
checkpoint: {checkpoint}
agent: refine
status: proposed
date: {YYYY-MM-DD}
source-feedback: episodes/{topic}/feedback/NN-{checkpoint}.txt
---

# Refinement Proposals — {checkpoint} checkpoint, {topic}

## Summary
{2-3 sentences on the key themes from the meeting that drove these proposals}

## Proposed edits

### 1. {short title — e.g., "Script Writer should require sensory detail in cold open"}
- **Target file:** `roles/script-writer.md`
- **Section:** "Writing the Opening Chapter" → "The Cold Open"
- **Rationale:** {1-2 sentences citing what Jeff or Cyrus said in the meeting}
- **Existing text:** > {quote from the file}
- **Proposed replacement:** > {new text}

### 2. ...

## Compliance issues (role file already covers this)
- {anything where the agent didn't follow existing guidance — note for human awareness}

## Episode-specific notes (no role edit proposed)
- {anything the agent should remember for this topic only}

## Out of scope — defer to /pipeline-review
- {anything that would require CLAUDE.md or template changes}
```

## After the agent finishes

Print a short summary:
- Number of proposed edits, broken down by target file (e.g., "3 edits to script-writer.md, 1 to jeff.md")
- Any compliance issues flagged
- Path to the proposals file

Tell Jeff: "Review proposals at {path}. Apply edits manually with the Edit tool — this command does not touch `roles/` or `hosts/` files directly. Once you've finished applying proposals from any checkpoint, you can delete the proposals file or leave it for the record."
