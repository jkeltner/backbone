# TTS Script Instructions: `script.txt` for ElevenLabs v3

*Last updated: February 2026*

---

## What This File Is

The `script.txt` is a **fully scripted, production-ready text file** designed to be fed into ElevenLabs' v3 model via the ElevenLabs Studio or Text to Dialogue API. Unlike `script.md` (which is a recording guide with notes, bullet points, and editorial cues), `script.txt` contains **only speakable text** — every word in the file will be spoken aloud.

This file is generated **alongside** `script.md` (both produced from the outline). Both can be iterated on independently — `script.md` guides live recording, `script.txt` feeds TTS generation.

---

## Where It Lives

```
episodes/
└── [topic-name]/
    ├── research.md
    ├── outline.md
    ├── script.md      ← recording guide (for human hosts)
    └── script.txt      ← TTS-ready script (for ElevenLabs v3)
```

---

## ElevenLabs v3 Text to Dialogue Format

The Text to Dialogue API accepts an array of speaker turns, each with a `text` and `voice_id`. The `script.txt` file uses a simple plaintext format. ElevenLabs Studio can parse this directly; for API usage, Claude can convert it to the required JSON structure.

### File Format

Each speaker turn is a block:

```
JEFF: [optional audio tags] Spoken text goes here.

CYRUS: [optional audio tags] Response text goes here.
```

**Segment breaks** mark natural chunking points (wave boundaries) for generation. These are stripped before sending to ElevenLabs:

```
--- SEGMENT BREAK: Wave 2 - The Mechanical Age ---
```

Rules:
- **Speaker labels** are `JEFF:` or `CYRUS:` at the start of each turn, followed by a space
- **One turn per block**, separated by a blank line
- **Segment break lines** start with `---` and are not spoken — they mark generation boundaries
- **No markdown**, no headers, no bullet points, no editorial notes — only speakable content
- **No stage directions or parenthetical notes** outside of square-bracket audio tags
- Everything in the file will be spoken aloud (except speaker labels, audio tags, and segment break lines)

---

## Audio Tags Reference

ElevenLabs v3 interprets square-bracket directives inline with the text. Use these to control delivery, emotion, and non-verbal sounds.

### Delivery & Volume

| Tag | Effect |
|-----|--------|
| `[whispers]` / `[whispering]` | Intimate, low-volume delivery |
| `[quietly]` / `[speaking softly]` | Gentle, quiet |
| `[loudly]` / `[shouts]` | Raised voice, dramatic emphasis |

### Emotion & Tone

| Tag | Effect |
|-----|--------|
| `[cheerfully]` | Upbeat, warm |
| `[flatly]` / `[deadpan]` | Dry, understated |
| `[playfully]` | Light, teasing |
| `[nervously]` | Uncertain, tense |
| `[resigned tone]` | Giving in, accepting |
| `[excited]` | High energy, enthusiastic |

### Non-Verbal Sounds

| Tag | Effect |
|-----|--------|
| `[laughs]` | Standalone laugh |
| `[laughing]` | Laugh woven into speech |
| `[laughs softly]` / `[light chuckle]` | Subtle amusement |
| `[sigh]` / `[sighing]` | Exhale — fatigue, relief, frustration |
| `[sigh of relief]` | Specifically relieved sigh |
| `[gasps]` | Surprise or shock |
| `[clears throat]` | Throat clear |
| `[breathes]` | Audible breath |

### Pacing & Rhythm

| Tag | Effect |
|-----|--------|
| `[pause]` | Brief beat of silence |
| `[rushed]` / `[rapid-fire]` | Faster delivery |
| `[slows down]` / `[deliberate]` | Slower, more measured |
| `[stammers]` / `[hesitates]` | Halting, uncertain rhythm |
| `[drawn out]` | Elongated delivery |
| `[emphasized]` | Extra weight on what follows |

### Combining Tags

Tags can be stacked: `[nervously][whispers] I... I'm not sure this is going to work.`

Place tags at the start of a line to set tone for the whole turn, or mid-sentence for dynamic shifts.

---

## Punctuation as Performance

Beyond audio tags, v3 responds strongly to punctuation and text formatting:

- **Ellipses (`...`)** create natural pauses. Use liberally for conversational pacing: "And then... nothing."
- **ALL CAPS** on a word signals emphasis: "That's not just big. That's ENORMOUS."
- **Em dashes (`—`)** create abrupt breaks or interruptions: "The whole system was— well, it collapsed."
- **Question marks** shift intonation naturally
- **Exclamation marks** add energy but use sparingly — the model can over-perform them
- **Commas** create micro-pauses; use them to control breath and rhythm

---

## Writing Guidelines for TTS

### General Principles

1. **Write for the ear, not the eye.** Read every line aloud. If it sounds stiff or unnatural when spoken, rewrite it.

2. **No visual formatting.** No headers, bold, italics, bullet points, tables, or markdown of any kind. The file is pure text with speaker labels and audio tags.

3. **Spell out numbers and abbreviations.** Write "fourteen billion dollars" not "$14B". Write "the nineteen fifties" not "the 1950s". Write "percent" not "%". The model may mispronounce symbols and abbreviations.

4. **Use phonetic spelling for tricky names.** If a name is commonly mispronounced, include a phonetic hint in parentheses the first time — but note that v3 will attempt to speak parenthetical content, so test this. Alternatively, use the closest phonetic English spelling.

5. **Alternate between exposition and dialog.** The most effective rhythm is stretches of relatively uninterrupted storytelling (one host narrating for 6–10 sentences) broken up by genuine back-and-forth banter and reactions. Don't force interjections into every passage — let the narrative breathe, then let the conversation breathe. The contrast between the two modes is what makes it feel like a real podcast.

6. **Write the banter.** Unlike `script.md` (which leaves room for improvisation), `script.txt` must script the back-and-forth explicitly. If Jeff is supposed to react with surprise, write his surprised reaction. Banter sections should feel loose — short turns, incomplete thoughts, genuine questions.

7. **Script the transitions.** Every wave handoff, every topic shift, every "let me tell you about..." moment needs to be written out as actual dialogue.

### Podcast-Specific Guidance

8. **Opening should hook immediately.** The cold open is the first thing ElevenLabs generates — make it vivid and compelling from word one.

9. **Vary turn lengths for rhythm.** Mix short reactions ("Wait, really?", "Wow.") with longer narrative passages. This creates the cadence of real conversation.

10. **Use audio tags sparingly but intentionally.** A well-placed `[laughs]` or `[pause]` every few minutes adds life. Overusing them makes the output feel mechanical. Think of them as seasoning, not the main ingredient.

11. **Front-load emotion in the text itself.** V3 reads emotional context from the words. "That's absolutely wild" conveys excitement without needing an `[excited]` tag. Save tags for moments where the text alone doesn't convey the delivery you want.

12. **End with energy.** The closing should feel like a natural wind-down, not an abrupt stop. Script a proper goodbye that feels warm.

---

## Converting `script.md` → `script.txt`

Claude generates `script.txt` from the finalized `script.md`. Here's what changes:

| `script.md` (recording guide) | `script.txt` (TTS-ready) |
|---|---|
| Bullet-point talking points | Fully written-out dialogue |
| "Key stats to hit: ..." | Stats woven naturally into spoken sentences |
| Editorial notes and cues | Removed entirely |
| `> Scripted transitions` | Kept and expanded into full turns |
| Reference tables | Information incorporated into dialogue or omitted |
| Anchor story outlines | Fully narrated as spoken stories |
| "Both hosts discuss..." | Explicit back-and-forth scripted |
| Markdown formatting | Plain text only |
| Numbers like "1850" or "$2.4M" | Spelled out: "eighteen fifty" or "two point four million dollars" |

### What to preserve from `script.md`:
- The wave structure and order of content
- All scripted transitions (expand them)
- Anchor stories (flesh them out into spoken narrative)
- Key stats and quotes (integrate into natural speech)
- Host assignments (map to JEFF: / CYRUS: labels)

### What to add that isn't in `script.md`:
- Explicit reactions, interjections, and back-and-forth
- Conversational connective tissue ("So here's the thing...", "Right, and that's what makes this interesting...")
- Audio tags where delivery matters
- Natural speech patterns: contractions, incomplete thoughts, verbal nods

---

## Example

Here's a longer example showing the mixed rhythm — exposition passages followed by conversational dialog. Notice how Jeff narrates for a sustained stretch, then the two hosts have a genuine exchange before moving on.

```
JEFF: Picture this. It's eighteen twenty, and a twenty-three year old from Boston named Frederic Tudor is loading a ship... with ice. Literal blocks of frozen lake water, bound for the Caribbean. The newspapers called him the "Ice King" and they did NOT mean it as a compliment. His own family thought he was throwing away the family fortune on a frozen fever dream. But Tudor was obsessed. He'd seen how ice transformed a drink on a hot day, and he was convinced the rest of the world would pay for that experience if someone could just figure out how to get it to them.

CYRUS: [laughs softly] So how did that first trip go?

JEFF: About as badly as you'd expect. He lost most of the ice on the voyage — it just melted. Showed up in Martinique with a fraction of what he'd loaded, and here's the kicker... nobody there had any idea what to do with it. They'd never had ice before. There was no market. He had to literally teach people what ice was FOR.

CYRUS: Wait, so he shipped a product thousands of miles to a place where nobody wanted it, and most of it melted on the way. That is... not a great business plan.

JEFF: Terrible business plan. He went broke. Multiple times, actually.

CYRUS: But he kept going.

JEFF: He kept going. And THAT'S what makes it a great story for us, because it's such a perfect example of the diffusion problem. The technology isn't the hard part. Getting people to want it... that's the hard part. Tudor standing on a dock in the Caribbean, trying to sell frozen water to people who've never seen a cold drink — that's basically the next forty years of the ice trade in miniature.

CYRUS: [pause] And it's funny, right, because we look back now and think... of course people want cold drinks. Of course there's a market for ice. But that's the trap. We always think adoption was obvious in hindsight.

JEFF: Exactly. Nothing is obvious until someone suffers long enough to prove it works.

--- SEGMENT BREAK: Wave 1 - Diffusion & Resistance ---

CYRUS: Okay, so Tudor eventually figures out the demand side. But there's still the supply problem, right? You can't run a global business on New England pond ice forever.
```

---

## Workflow Integration

### Updated Per-Episode Workflow

```
1. PICK A TOPIC → create folder
2. INITIAL RESEARCH → research.md
3. REVIEW & REFINE → iterate on research.md
4. OUTLINE → outline.md (Claude drafts, hosts refine)
5. SCRIPTS → script.md (recording guide) + script.txt (TTS-ready)
6. REVIEW & RECORD → review, record, and/or generate audio
```

**Prompts:**
- "Generate the scripts for this episode." (creates both)
- "Regenerate script.txt from the updated script.md." (sync after edits)
- "Generate just the TTS script for this episode." (script.txt only)

### Updated Folder Structure

```
episodes/
└── [topic-name]/
    ├── research.md    ← Claude creates
    ├── outline.md     ← Claude drafts, hosts refine
    ├── script.md      ← Claude creates (recording guide)
    └── script.txt     ← Claude creates (ElevenLabs v3 TTS-ready)
```

---

## Technical Notes

### Voice Selection
Use pre-built voices from the ElevenLabs Voice Library that are optimized for v3. Professional Voice Clones (PVCs) are not yet fully optimized for v3 and may produce lower quality output. Instant Voice Clones (IVCs) are a viable alternative once available.

### Generation Workflow
- Primary tool: **ElevenLabs Studio** (handles chunking, multi-speaker assignment, and take management automatically)
- Alternative: Text to Dialogue API for programmatic generation
- The `script.txt` format maps to the API's `inputs` parameter — each `JEFF:` / `CYRUS:` turn becomes a `DialogueInput` object with the corresponding `voice_id`
- Segment break lines (`--- SEGMENT BREAK: ... ---`) mark natural chunking points at wave boundaries
- Generate multiple takes of each segment and select the best
- Stability slider: start with "Natural" for balanced output; try "Creative" for more expressiveness if needed

---

## CLAUDE.md Additions

*The following sections should be added to CLAUDE.md to integrate this into the project instructions.*

### Addition to "Per-Episode Workflow" section (add as item 4, after Script):

> ### 4. TTS Script (`script.txt`)
> **Created by:** Claude (from outline, alongside script.md)
> **Purpose:** Production-ready text for ElevenLabs v3 Text to Dialogue (via Studio or API)
>
> - Fully scripted dialogue — every word will be spoken
> - Speaker labels (JEFF: / CYRUS:) for each turn
> - Segment break lines at wave boundaries for chunking
> - Audio tags used sparingly for key delivery moments
> - Numbers and abbreviations spelled out
> - No markdown, no editorial notes, no stage directions
> - Rhythm alternates between stretches of exposition and conversational banter
>
> **Instructions:** `tts_script_instructions.md`

### Addition to "Workflow Steps" (add step 5b alongside step 5):

> ```
> 5b. TTS SCRIPT
>     Claude generates script.txt from the outline (parallel to script.md)
>     Prompt: "Generate the TTS script for this episode."
>     Can also be regenerated from a revised script.md:
>     Prompt: "Regenerate script.txt from the updated script.md."
> ```

### Addition to folder structure:

> ```
> └── episodes/
>     └── [topic-name]/
>         ├── research.md
>         ├── outline.md
>         ├── script.md
>         └── script.txt     ← ElevenLabs v3 TTS-ready script
> ```

---

## Design Decisions (Resolved)

These decisions were made during initial setup and inform how Claude generates the file:

- **Voices:** Pre-built v3-optimized voices from ElevenLabs Voice Library (not clones, for now)
- **Generation tool:** ElevenLabs Studio (handles chunking automatically; API available as fallback)
- **Chunking:** Segment breaks at wave boundaries, marked in the file with `--- SEGMENT BREAK ---` lines
- **Banter density:** Mixed rhythm — stretches of exposition broken up by dialog/banter sections. Not constant back-and-forth, not long unbroken monologues.
- **Audio tags:** Minimal. Use only at key moments where the text alone doesn't convey the intended delivery. Add more based on listening tests.
- **Workflow position:** Generated alongside `script.md` (both from the outline). Both can be iterated independently.

---

## Future Consideration

If TTS becomes the primary output (rather than a supplement to live recording), the workflow should be rethought — `script.txt` would become the main deliverable and `script.md` might be dropped or repurposed as a review/editing document for the TTS script.
