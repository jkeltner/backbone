---
description: Show pipeline status for an episode — which content checkpoints are complete and where production/distribution stands.
argument-hint: <topic>
---

You are reporting **pipeline status** for the Backbone podcast.

The topic is: **$ARGUMENTS**

If `$ARGUMENTS` is empty, stop and ask which topic to inspect.

## What to report

Read both status files (one or both may not exist yet — that's fine, treat missing as "all pending"):

1. **Content pipeline:** `episodes/$ARGUMENTS/pipeline-status.json` — shows `blueprint`, `script`, `polish` checkpoint states.
2. **Production/distribution:** `episodes/$ARGUMENTS/release-status.json` — managed by `tools/release.py`. Run `python tools/release.py $ARGUMENTS status` to get a formatted report.

Also check on the filesystem:
- Existence of key artifacts: `research/overview.md`, `blueprint.md`, `script/chapter-*.txt`, `script/editor-notes.md`, `script/fact-check-report.md`, `final/assembled.txt`, `final/episode.mp3`.
- Existence of feedback files: `feedback/01-blueprint.txt`, `feedback/02-script.txt`, `feedback/03-polish.txt`. Note whether each is present (Jeff and Cyrus may have skipped a meeting).
- Existence of refinement proposals: `refinements/*.md`.

## Output format

Print a short, scannable report:

```
Backbone pipeline status — $ARGUMENTS
─────────────────────────────────────

Content pipeline:
  [✓ / ○ / —] /blueprint   ({status} {date if complete})
  [✓ / ○ / —] /script      ({status} {date if complete})
  [✓ / ○ / —] /polish      ({status} {date if complete})

Feedback transcripts:
  [✓ / —] feedback/01-blueprint.txt
  [✓ / —] feedback/02-script.txt
  [✓ / —] feedback/03-polish.txt

Refinement proposals:
  [list any files in refinements/]

Production/distribution (from release.py):
  [paste the python tools/release.py {topic} status output here]

Next step: [recommend next slash command based on state]
```

Use `✓` for complete, `○` for in-progress, `—` for not started. Keep it under 30 lines.
