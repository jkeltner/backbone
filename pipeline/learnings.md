# Pipeline Learnings

Distilled lessons from each pipeline run. Source feedback files are deleted after their generalizable insights land here — this is the canonical record of what we learned and what we changed.

---

## From the Refrigeration v1 pilot run (Feb 2026)

The v1 run was pre-host-profiles and pre-audio-pipeline. Most of Jeff's feedback drove the structural changes already in place; what remains here is either (a) absorbed into role files, (b) still parked for future application, or (c) small craft rules that should travel with us.

### Already applied

- **Host personality files** — added `hosts/jeff.md` and `hosts/cyrus.md`. The pilot's hosts blurred together (especially in Built In where Cyrus did most of the talking and Jeff became a reactor). Profiles now distinguish them; Editor's continuity check enforces it.
- **Audio generation pipeline** — `tools/tts_dialogue.py`, `tools/audio_assemble.py`, `tools/timestamp_chapters.py`. The pilot left audio production as an open question; the pipeline now closes it.
- **Wave-count flexibility** — pilot landed at three waves vs. the four we originally outlined. Blueprint template now treats wave count as an editorial decision, not a fixed structure.
- **Complementary technologies as a standard beat** — Jeff flagged this in v1; now a required field in `templates/research-overview.md`.
- **Overview vs. wave-research detail balance** — pilot overview was over-stuffed with character detail that belonged in waves. Templates now scope overview to thesis + wave map, with character work pushed into per-chapter research.

### Still open — apply to future episodes

- **Stat repetition risk.** v1 had the same numbers landing 2–3× across Opening, Wave, and Built In (e.g. "8% → 85% adoption" appeared in three places). Editor should flag any stat that appears verbatim more than once and propose a callback rephrase (e.g. "the number we opened with").
- **Built In front-loading.** v1 piled stat recitations *before* the Backbone Test, which fatigued the listener. Built In should open with the arc, not the numbers.
- **Subscribe / follow CTA.** Jeff wants a soft listener prompt near the close ("if this resonated, share it / follow the show"). Add to `roles/script-writer.md` as a structural element of the sign-off, not an afterthought.
- **"World Before" texture in the intro hook.** Pilot opening was data-forward; Jeff wanted a sensory artifact (his example: salted meats / bacon — the "before" world that the breakthrough makes possible). Script Writer should land at least one concrete sensory detail in the cold open's world-before beat.
- **Authoritative-source baseline for research.** Open question whether each topic should start with a known canonical source list (textbooks, academic journals, established histories) before web search, vs. letting search find the best material. Worth picking a policy before episode 2.

### Parked — not blocking

- **Standard sign-off line.** `CLAUDE.md` `[PENDING]`. Jeff wants a Freakonomics-style closer; not yet written.
- **Social media engagement strategy.** Beyond posting — how the show responds, builds audience. Decided post-launch.

### Editorial discipline notes (small but worth keeping)

- Watch for the same line of dialogue or stat being delivered twice in slightly different framings — the pilot had "ninety thousand workers and twenty-five thousand horses" appear five times.
- Hosts should not repeat the same Backbone Test answer in different beats. Q3 ("hidden cost") and Q5 ("what's next") tended to converge in v1 because both pulled from the climate stats.
