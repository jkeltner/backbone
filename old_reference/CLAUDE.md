# Backbone: From Breakthrough to Built-In

## Project Context

A podcast exploring technological innovations that shaped modern life — how they were discovered, how they spread, and their ripple effects. Think Acquired, but focused on *innovations* rather than companies.

**Hosts:** Jeff Keltner and Cyrus Mistry
**Status:** Pilot episode in development (Refrigeration)

**The Core Angle:** Most tech/business content skips from "invention" to "winner." Backbone emphasizes the **diffusion story** — the messy middle: who resisted and why, what complementary tech was needed, the tipping point from novelty to inevitability, and the second-order societal effects.

See `overview.md` for branding, audience, and goals.

---

## Episode Structure: Waves

Most backbone technologies don't have a single discovery-diffusion-aftermath arc. They evolve through **waves** — each with its own breakthrough, resistance, and consequences. The aftermath of one wave becomes the setup for the next.

| Section | Target Time | Purpose |
|---------|-------------|---------|
| **OPENING: The Hook** | 12-18 min | Cold open story, impact stats, "world before," preview of waves |
| **THE WAVES** (×2-4) | 15-25 min each | Each wave: Breakthrough → Diffusion & Resistance → What Changed |
| **BUILT IN: The Big Picture** | 15-20 min | Full arc, The Backbone Test (5 questions), open questions |

**Episode length:** 90-120 min

Each wave has a **driver** (one host leads) and both hosts participate. Hosts alternate waves. Opening and Built In are conversational (both hosts).

**Key elements within waves:**
- **Anchor stories**: 1-2 specific, vivid, short-form stories per wave that capture the larger dynamics in miniature
- **How It Works**: Placed in whichever wave first introduces the core mechanism (~5 min max)
- **The bridge**: Each wave ends by showing what's now possible but not yet realized — setting up the next wave

**The Backbone Test** (closing framework, every episode):
1. **Invisible?** — Has it become infrastructure you only notice when it fails?
2. **What depends on it?** — Map the dependency chain
3. **What's the hidden cost?** — Energy, labor, environment, inequality
4. **Could we go back?** — How deep is the dependency?
5. **What's next?** — What's still evolving behind the scenes?

See `episode_template.md` for detailed guidance on each section.

---

## Per-Episode Workflow

Each episode gets its own folder with three files:

```
episodes/
└── [topic-name]/
    ├── research.md    ← Claude creates (raw research, comprehensive)
    ├── outline.md     ← Claude drafts, Jeff & Cyrus refine (episode structure + editorial decisions)
    └── script.md      ← Claude creates from outline (recording document)
```

### 1. Raw Research (`research.md`)
**Created by:** Claude
**Purpose:** Comprehensive research organized to feed into the wave structure

- Exhaustive — more is better at this stage
- Organized by topic area (people, timeline, resistance, consequences, etc.)
- Highlight best material with ⭐
- Specifically look for **anchor story** candidates (vivid, specific, short-form)
- Link sources inline, flag claims needing verification

**Template:** `templates/research_template.md`

### 2. Episode Outline (`outline.md`)
**Created by:** Claude (initial draft), then refined collaboratively with Jeff & Cyrus
**Purpose:** The episode plan — wave structure, anchor stories, timing, host assignments

- Defines the waves and what goes in each
- Includes specific anchor stories, key characters, bridge transitions
- Timing estimates per wave
- Host assignments (who drives which wave)
- Editorial decisions: what to include, what to cut, emphasis and pacing

**Template:** `templates/outline_template.md`

### 3. Script (`script.md`)
**Created by:** Claude (based on outline)
**Purpose:** Recording document — structured enough to stay on track, loose enough for genuine conversation

- Scripted cold open and transitions between waves
- Key beats and talking points in order
- Specific stats, quotes, and details to hit
- Cues for who's driving, suggested handoffs
- Reference section (names, dates, numbers)

**Template:** `templates/script_template.md`

---

## Workflow Steps

```
1. PICK A TOPIC
   Choose from topics.md, create a folder in /episodes/
   ↓
2. INITIAL RESEARCH
   Claude creates comprehensive research.md
   Prompt: "Let's start research on [topic]."
   ↓
3. REVIEW & REFINE
   Jeff/Cyrus review, request deeper dives
   Claude adds to research.md (all refinements stay in one file)
   Prompts:
     "Go deeper on the resistance story."
     "Find more anchor stories for Wave 2."
     "What are the best stats on adoption curves?"
   ↓
4. OUTLINE
   Claude drafts outline.md based on research
   Jeff & Cyrus refine: adjust waves, pick anchor stories,
   assign host duties, make pacing decisions
   ↓
5. SCRIPT
   Claude creates script.md from outline
   Prompt: "Based on the outline, create the script for this episode."
   ↓
6. REVIEW & RECORD
   Review the script together. Make adjustments. Record.
```

---

## Folder Structure

```
/
├── overview.md              # Podcast concept, branding, goals
├── episode_template.md      # Episode structure guide (wave framework, Backbone Test, etc.)
├── topics.md                # Episode topic ideas and evaluation criteria
├── pilot_checklist.md       # Planning checklist for pilot episode
├── AGENTS.md                # This file (project context + AI instructions)
├── CLAUDE.md                # Same as AGENTS.md
│
├── templates/               # Blank templates for per-episode files
│   ├── research_template.md
│   ├── outline_template.md
│   └── script_template.md
│
├── assets/                  # Cover art, promo images
│   ├── cover_art.png
│   └── promo_image.png
│
└── episodes/                # Episode folders
    └── [topic-name]/
        ├── research.md
        ├── outline.md
        └── script.md
```

---

## Tone & Style Guidelines

- **Narrative-driven**, not textbook summaries
- **Human drama** over technical achievement — anchor stories are the backbone of good episodes
- **Accessible explanations** — mental models, not engineering diagrams
- **No "dorm room" debates** — avoid simplistic good/bad framing
- **Historical empathy** — don't judge past decisions by today's values without context
- **Waves, not acts** — treat each technology as an evolving story with multiple chapters, not a single before/after

---

## Research Guidelines

When researching, prioritize:
1. **Anchor stories** — specific, vivid, short-form stories with named people, dates, places
2. **The "world before"** — what life was like without the innovation (visceral, not abstract)
3. **Human stories** — inventors, resisters, winners, losers, with personal details
4. **The diffusion story** — not just the breakthrough, but how it spread and who fought it
5. **Statistics that capture scale of change** — tangible comparisons, before/after contrasts
6. **Wave boundaries** — look for distinct phases where the technology entered new domains

**Always:**
- Highlight the best material (⭐) so it's easy to find
- Flag claims that need fact-checking
- Suggest primary sources when possible
- Note when information might be uncertain or contested
- Specifically identify anchor story candidates

**Avoid:**
- Generic overviews without specific details
- Over-explaining technical mechanisms (5 min max in the episode)
- Treating adoption as inevitable (resistance is often the story)

---

## Tips

**On research:** More is better at the start. It's easier to cut than to realize you're missing something mid-recording. Anchor stories are the hardest to find and the most valuable — look in magazine features, book chapters, and newspaper archives.

**On the outline:** This is where the creative decisions happen. The research is raw material; the outline is the vision for the episode. Claude drafts it, but Jeff and Cyrus shape it.

**On the script:** It's a guide, not a straitjacket. Leave room for genuine conversation, especially during the Built In section.

**On Claude:** Good at research, organization, and drafting. Not good at knowing what makes a compelling episode — that's Jeff and Cyrus's job. Ask Claude for deeper research, alternative anchor stories, or draft revisions, but make the editorial calls yourselves.

---

## AI Limitations to Remember

- Knowledge has a cutoff date — verify recent information independently
- AI may present plausible-sounding but incorrect information confidently
- Quotes attributed to historical figures are often inaccurate — always verify
- AI tends to oversimplify complex historical debates
- Different sources may tell different versions; AI may pick one arbitrarily

**When in doubt, go to the primary source.**

---

*Last updated: February 2026*
