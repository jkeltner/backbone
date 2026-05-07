---
description: Run the Profile Updater agent against the post-episode conversation transcript. Produces proposed edits to host profiles for async review.
argument-hint: <topic>
---

You are running the **Profile Updater** for the Backbone podcast pipeline.

The topic is: **$ARGUMENTS**

If `$ARGUMENTS` is empty, stop and ask which topic to run against.

## What this command does

After an episode ships, Jeff and Cyrus record a free-form post-episode conversation, saved as `episodes/{topic}/feedback.txt`. This command runs the Profile Updater agent, which extracts host voice signal from the transcript and proposes targeted edits to `hosts/jeff.md` and `hosts/cyrus.md`.

This is **distinct from `/refine`** — `/refine` runs after each pipeline checkpoint and proposes role-file edits. `/profile-update` runs once after the whole episode and proposes host-profile edits. It produces proposals only — does NOT edit profile files directly.

## Before you start

1. Verify `episodes/$ARGUMENTS/feedback.txt` exists (this is the post-episode conversation, not the per-checkpoint feedback files in `feedback/`). If not, stop and tell the user to save the post-episode conversation transcript first.
2. Note that recording-session transcripts at `episodes/$ARGUMENTS/jeff_cyrus_recording/*.txt` (if they exist) are also valid input and should be passed to the agent.

## Run the agent

Spawn a general-purpose agent with:

- **Task:** "Run the Profile Updater for the Backbone podcast on the topic: **$ARGUMENTS**. Analyze the post-episode conversation and propose host-profile edits."
- **Files to read:** `CLAUDE.md`, `roles/profile-updater.md`, `episodes/$ARGUMENTS/feedback.txt`, any files under `episodes/$ARGUMENTS/jeff_cyrus_recording/` if present, `hosts/jeff.md`, `hosts/cyrus.md`, `episodes/$ARGUMENTS/script/editor-notes.md` (Voice Consistency Flags section especially).
- **Output:** `episodes/$ARGUMENTS/profile-update-proposals.md` following the structure in the role file.
- **Methodology:** Follow the role file. Be conservative — patterns over one-offs. Cross-reference Voice Consistency Flags from editor-notes. Use the Good/Bad examples in the role file as the bar.

Wait for completion.

## After the agent finishes

Print a short summary:
- Number of proposed Jeff changes (by type: Add / Correct / Remove)
- Number of proposed Cyrus changes
- Number of new voice samples surfaced
- Any unresolved Voice Consistency Flags
- Path to the proposals file

Tell Jeff: "Review proposals at `episodes/$ARGUMENTS/profile-update-proposals.md`. Cyrus should review changes that affect his profile before applying. Apply approved edits manually with the Edit tool. Mark `status: applied` in the proposals file front matter once done."
