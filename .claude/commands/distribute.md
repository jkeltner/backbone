---
description: Run the distribution phase via release.py — uploads the episode to Transistor as a draft for human review.
argument-hint: <topic>
---

You are running **Distribution** for the Backbone podcast pipeline.

The topic is: **$ARGUMENTS**

If `$ARGUMENTS` is empty, stop and ask the user which topic to run.

## What this command does

Shells out to the Python orchestrator, which uploads to Transistor (and any other distribution targets that aren't deferred per `pipeline/launch-plan.md`):

```bash
python tools/release.py $ARGUMENTS distribute
```

The script pauses at human review gates (e.g., "publish on Transistor", "publish on YouTube", "review and send on Buttondown"). At those gates, it tells the user what to do in the relevant dashboard and exits — it does not auto-publish.

## Before you start

Verify `episodes/$ARGUMENTS/final/episode.mp3` exists. If not, tell the user to run `/produce $ARGUMENTS` first.

## Run it

Run the bash command above and report the output to the user verbatim. If the script pauses at a review gate, surface that clearly. If it errors, report the error.

After it finishes (or pauses), tell the user the next step based on what `release.py` reported. Reference `pipeline/distribution-pipeline.md` and `pipeline/launch-plan.md` if the user has questions about any of the gates.
