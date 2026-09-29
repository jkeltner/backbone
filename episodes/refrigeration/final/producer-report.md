---
topic: refrigeration
agent: producer
status: complete
date: 2026-09-13
---

# Producer Report: Refrigeration (Episode 1)

Read before assembling: `CLAUDE.md`, `roles/producer.md`, `pipeline/tts-pipeline.md`, all six `script/chapter-*.txt` (Editor- and Fact-Checker-passed 2026-09-13), `script/editor-notes.md`, `script/fact-check-report.md`, `blueprint.md`, `assets/show-description.md`. No `feedback/03-polish.txt` exists and the Checkpoint 3 Google Doc carries zero comments, so there were no final host notes to apply. The June `final/assembled.txt` (chapter 01 only, from the beta A/B) was replaced.

---

## Deliverables

| File | What it is |
|---|---|
| `final/assembled.txt` | The production-ready TTS script — six chapters concatenated, front matter stripped, 1,043 lines |
| `final/metadata.md` | Title options and top choice, short and long descriptions, episode number, runtime, chapter table, keywords, Transistor field map |
| `final/show-notes.md` | Listener-facing notes: summary, chapter list, people, sources (every item the script's own call-to-action promises), caveats, credits |
| `final/social-content.md` | Launch-announcement drafts (X, LinkedIn, Instagram, newsletter), three pull quotes plus alternates, a seven-post thread, a link-sharing blurb |
| `final/producer-report.md` | This file |

---

## Runtime

- **Spoken words: 24,473** (speaker labels, audio tags, segment breaks, and music cues excluded). 507 turns: Jeff 255, Cyrus 252.
- **Raw at 187 wpm: 130.9 minutes.** **At 1.2x release speed (225 wpm): 108.8 minutes** of speech.
- With music (theme in about 24.5 s, five bumpers about 9.8 s each, theme out about 24.5 s faded): **about 110 minutes finished.** Inside the 90–120 target; not flagged.
- Per chapter (words / release-speed minutes): Opening 2,529 / 11.2; Cold as a Commodity 4,565 / 20.3; The Machine and the Chain 5,093 / 22.6; Cold Comes Home 4,609 / 20.5; Cold and the Sky 4,090 / 18.2; Built In 3,587 / 15.9. Every chapter is inside its blueprint band by the Fact Checker's counter (this counter matches the Fact Checker's to the word).

---

## Music cue positions in `assembled.txt` (line numbers)

| Line | Cue | Position |
|---|---|---|
| 77 | `[MUSIC: theme-in]` | After the cold open's last line ("The good ones would've pivoted to ice cream."), before the World Before segment break |
| 151 | `[MUSIC: transition-bumper]` | End of chapter 01 → Wave 1 |
| 369 | `[MUSIC: transition-bumper]` | End of chapter 02 → Wave 2 |
| 589 | `[MUSIC: transition-bumper]` | End of chapter 03 → Wave 3 |
| 777 | `[MUSIC: transition-bumper]` | End of chapter 04 → Wave 4 |
| 915 | `[MUSIC: transition-bumper]` | End of chapter 05 → Built In |
| 1043 | `[MUSIC: theme-out]` | After the sign-off; last line of the file |

Sequence verified as exactly theme-in, five bumpers, theme-out. No doubles at any boundary; chapter 06 does not open with a second bumper. Every cue stands alone with exactly one blank line before and after (a first pass had doubled the blank line after each cue and segment break; collapsed — the file has no consecutive blank lines). Segment breaks at lines 1, 19, 79, 153, 371, 591, 779, 917.

**Audio-segment consequence:** the TTS pipeline splits on music cues, so the render produces seven wave files — wave-00-opening (welcome + cold open, 1,252 words), wave-01 (the World Before, 1,277 words), wave-02 through wave-05 (chapters 02–05), wave-06-built-in. See "Needs human attention," item 1.

---

## Checks run on the assembled file

All passed; nothing needed fixing in the chapter text itself.

- Begins with a segment break (`--- SEGMENT BREAK: Opening - The Welcome ---`); no front-matter block anywhere in the file (each chapter's YAML block, including the `editor-pass:` and `fact-check-pass:` lines, stripped).
- `[FLAG: …]`, `[VERIFY]`, `[GAP]`, `[NEEDS RESEARCH]`, `[MISSING PERSPECTIVE]` markers: **0 found** (the Fact Checker had already cleared all 27).
- Every non-blank line is a `JEFF:`/`CYRUS:` turn, a music cue, or a segment break; one blank line between turns.
- Digits, `$`, `%` in spoken lines: **none.** Markdown (headers, bold, italics, backticks, bullets, blockquotes) in spoken lines: **none.**
- Audio tags: 216 total, all from the Script Writer's approved vocabulary (`[reflective]` 27, `[deliberate]` 27, `[laughs softly]` 22, `[amused]` 19, `[laughs]` 17, `[skeptical]` 17, `[quietly]` 15, `[curious]` 14, `[incredulous]` 13, `[genuinely surprised]` 11, `[dry]` 9, `[warmly]` 7, `[exhales]` 5, `[deadpan]` 5, `[mischievously]` 3, `[emphatic]` 2, `[awed]` 1, `[scoffs]` 1, `[sighs]` 1). **No tag-only turns; no turn stacks more than two tags.**
- Close: the penultimate turn carries the wrap-up ("That's it for this episode of Backbone. We'll be back in a few weeks…"), the final spoken line is exactly `CYRUS: Until then — stay curious, and mind the backbones.` with **no tag**, and nothing is spoken after `[MUSIC: theme-out]`.
- Chapter joins read cleanly: each bridge points forward (ch01 → "a guy in debtors' prison with a pond and a motto"; ch02 → "making it… and then moving it"; ch03 → "something you'd trust… then something you could own"; ch04 → "Don't last a century. And don't reach the sky." → ch05's Midgley prologue; ch05 → "Four fluids" → ch06 "So we've walked two hundred years").
- Consistency spot-checks across chapters: Kigali "a third to half a degree" (ch05, ch06 twice); "roughly one in eight" and "four homes in a hundred" (ch05, ch06); the 1940 census 44/27/27 (ch04, ch06); "one baby in four" (ch01) → ch03 payoff; "four fluids" (ch05, ch06); "the fifty-nine cents" (ch02 → ch06 close). No discrepancies.
- **Character set:** the file is UTF-8 with no control characters, no non-breaking spaces, no zero-width characters, and no curly quotes. Non-ASCII characters present, deliberately kept: the em dash (U+2014, 472 uses — the Script Writer's performance punctuation for v3, present in every prior render) and acute accents in proper names (Szilárd, Leó, Carré, Orléans; 16 characters total), which help pronunciation. If a strictly 7-bit file is wanted, the em dash → `--` conversion is a one-line change, but it would alter v3's pacing and was not made.

---

## Needs human attention before audio generation

1. **Chapter-marker numbering in `metadata.md` is by audio segment, not blueprint wave.** `tools/timestamp_chapters.py` names audio segment N from the metadata row labeled "Wave N." Because `[MUSIC: theme-in]` splits the opening into two segments, a table numbered by blueprint wave would shift every chapter marker one segment early — which is what happened to the beta's `chapters.json` (its "The Ice Trade" landed at 2:36, the World Before segment). I numbered the rows as segment indices instead (Wave 1 = "The World Before Cold" at ~5:58, Wave 2 = Cold as a Commodity, … Built In = The Big Picture) and documented it in the table's note. Result: seven correct, listener-useful chapter markers. If a "World Before" marker is unwanted, the tool needs a small change (treat the segment right after theme-in as a continuation of the opening) rather than a table change.

2. **Show-notes timestamps are estimates.** `timestamp_chapters.py` updates only `metadata.md`; the chapter list in `show-notes.md` carries the same estimated times and should be synced from `final/chapters.json` before upload (a one-minute manual step, or a future tool tweak).

3. **`distribute_podcast.py` uploads `show-notes.md` raw** as Transistor's description — including the YAML front-matter block and markdown syntax. The front matter is kept here because CLAUDE.md requires it on every deliverable. Strip the block (and consider converting the markdown to HTML) at the distribute step.

4. **Voice clone choice is still open.** Per `pipeline/tts-pipeline.md`, ep 1 ships on whichever clone wins the chapter 01 IVC-vs-PVC A/B (`--clone ivc|pvc`). Nothing in this package depends on the choice, but `audio_assemble.py` must be run with the matching `--clone`.

5. **Stale artifacts in `final/`:** `assembly-map.json` (from the June two-segment beta render) and five `beta-chapter-01-*.mp3` files remain. `release.py produce` will regenerate the map; the beta MP3s are harmless but could be moved out to avoid confusion.

6. **Hedged and unverifiable items** are all hedged on air (see the fact-check report) and are listed as caveats in the show notes rather than restated as facts: Roffignac's ice-dumping, the Calcutta crowd stories, the Gorrie "God Almighty" clipping, "more ice than any cargo except cotton," Harrison's explosions, the Berlin family, Pennington as "highest-paid woman," Reagan's skin cancer as motive, the McNeill wording (six books quote it identically; the page itself was not checked), the refrigerated-warehouse capacity range, and the off-grid appliance count. Nothing here blocks audio.

No runtime flag, no unresolved markers, no format violations. The package is ready for `python tools/release.py refrigeration produce`.
