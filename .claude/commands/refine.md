---
description: After all three checkpoint meetings are done — read every feedback transcript and propose edits to roles/ and hosts/ files. Single end-of-episode run; does NOT modify those files directly.
argument-hint: <topic>
---

You are running the **Refinement Loop** for the Backbone podcast pipeline.

The topic is: **$ARGUMENTS**

If `$ARGUMENTS` is empty, stop and ask the user which topic to run.

## What this command does

Once per episode, after all three review meetings have happened, this command reads every checkpoint feedback transcript together and proposes targeted edits to `roles/` and `hosts/` files — the kind of fixes that prevent the same issue recurring on future episodes.

You produce **proposals only**. You do NOT edit `roles/` or `hosts/` files directly. Jeff reviews the proposals async and applies the ones that land. Cyrus reviews any proposed changes to `hosts/cyrus.md` before they're applied.

Run this **after the `/polish` review meeting** (so all three feedback files exist) and ideally **before the next episode's `/blueprint`** (so accepted edits land first). It's fine to run it in parallel with `/produce` and `/distribute` — those don't depend on `roles/` or `hosts/`. Run it in a separate Claude Code window from your main production session if you want to keep contexts clean.

## Why one run per episode (not three)

The previous design ran `/refine` after each individual checkpoint meeting. The consolidated run sees all three transcripts together, which makes cross-checkpoint patterns visible — for example, "the script writer drifted from the blueprint AND the editor didn't catch it AND the fact checker found knock-on errors" is one root-cause story that fragments into three disconnected reports if you split it. One run, one proposals file.

## Before you start

Verify that at least one checkpoint feedback file exists at `episodes/$ARGUMENTS/feedback/`. The expected paths are:
- `episodes/$ARGUMENTS/feedback/01-blueprint.txt`
- `episodes/$ARGUMENTS/feedback/02-script.txt`
- `episodes/$ARGUMENTS/feedback/03-polish.txt`

If none exist, stop and tell the user to save at least one meeting transcript first. If only some exist, proceed with what's there and note which were missing in the proposals file.

## Run the audit

Spawn a general-purpose agent with:

- **Task:** "Audit the Backbone pipeline's role and host files against the full set of checkpoint review meeting feedback for the topic **$ARGUMENTS**. Look for cross-checkpoint patterns, not just per-meeting issues. Propose targeted edits that would prevent the same issues recurring on future episodes. Do NOT edit any files directly — produce a proposals document only."
- **Files to read:**
  - All available feedback transcripts at `episodes/$ARGUMENTS/feedback/01-blueprint.txt`, `02-script.txt`, `03-polish.txt` (skip any that don't exist; note their absence)
  - All files in `roles/` (research-director, narrative-architect, script-writer, editor, fact-checker, producer, profile-updater, pipeline-reviewer)
  - Both `hosts/jeff.md` and `hosts/cyrus.md`
  - `pipeline/learnings.md` (for what's already been distilled — don't re-propose lessons already applied)
  - Episode artifacts for context: `episodes/$ARGUMENTS/blueprint.md`, `episodes/$ARGUMENTS/research/overview.md`, `episodes/$ARGUMENTS/script/editor-notes.md`, `episodes/$ARGUMENTS/script/fact-check-report.md` (skim — you don't need every chapter file)
- **Output:** `episodes/$ARGUMENTS/refinements/proposals.md` (single file).
- **Methodology:**
  1. Read all three feedback transcripts end-to-end before proposing anything. Get the full picture first.
  2. Look for **cross-checkpoint patterns** — issues that surface in multiple meetings, root causes that explain symptoms across stages, "the X agent should have caught this" / "the Y agent created the problem" stories. These are the highest-leverage proposals.
  3. Then look for per-checkpoint signal that didn't appear cross-cuttingly.
  4. For each, decide whether it's:
     - **Episode-specific** (only relevant to this topic) → don't propose role/host edits, just note it
     - **Generalizable** (would recur on future episodes) → propose a specific edit to the relevant role or host file
     - **Already covered** (the role file already says this; the agent didn't follow it) → flag as compliance issue, not a role-file gap
  5. Stay in scope: only propose edits to `roles/*.md` and `hosts/*.md`. CLAUDE.md and template changes are out of scope and go through `/pipeline-review` post-episode — note them in a "Out of scope — defer to /pipeline-review" section instead.
  6. For each proposed edit, include: target file, the existing text being changed (with enough context to locate it), the proposed replacement, and a 1–2 sentence rationale citing the specific feedback (which meeting, what was said).

## Output format

The proposals file should be structured for fast async review:

```markdown
---
topic: $ARGUMENTS
agent: refine
status: proposed
date: {YYYY-MM-DD}
sources:
  - episodes/$ARGUMENTS/feedback/01-blueprint.txt    # mark missing if absent
  - episodes/$ARGUMENTS/feedback/02-script.txt
  - episodes/$ARGUMENTS/feedback/03-polish.txt
---

# Refinement Proposals — $ARGUMENTS

## Summary
{2-4 sentences on the dominant themes across the three meetings and what kinds of edits are proposed}

## Cross-checkpoint patterns
{The most valuable section. Issues that span multiple meetings, root causes that explain symptoms across stages.}

### 1. {short title}
- **Pattern across checkpoints:** {what showed up in which meetings}
- **Root cause:** {which role file or guidance is the actual gap}
- **Target file:** `roles/...` or `hosts/...`
- **Section:** {section name}
- **Rationale:** {1-2 sentences citing the specific feedback}
- **Existing text:** > {quote from the file}
- **Proposed replacement:** > {new text}

### 2. ...

## Per-checkpoint proposals
{Issues that surfaced in only one meeting and don't have a cross-cutting story.}

### Blueprint checkpoint
- {proposed edits, same format as above}

### Script checkpoint
- {...}

### Polish checkpoint
- {...}

## Compliance issues (role file already covers this)
{Cases where the agent didn't follow existing guidance — note for human awareness, no edit proposed.}

## Episode-specific notes (no role edit proposed)
{Things to remember for this topic only.}

## Out of scope — defer to /pipeline-review
{CLAUDE.md or template changes that would require broader review.}
```

## After the agent finishes

Print a short summary:
- Number of cross-checkpoint patterns identified
- Total proposed edits, broken down by target file (e.g., "3 edits to script-writer.md, 2 cross-cutting, 1 to jeff.md")
- Any compliance issues flagged
- Path to the proposals file

Tell Jeff: "Review proposals at `episodes/$ARGUMENTS/refinements/proposals.md`. Apply edits manually with the Edit tool. Cyrus should review any `hosts/cyrus.md` proposals before they're applied. Once you've finished applying, you can leave the proposals file as a record or delete it."
