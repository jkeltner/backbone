# How We Make Episodes

A guide to our workflow for Jeff and Cyrus.

---

## The Short Version

1. **Pick a topic** → create a folder in `/episodes/`
2. **Claude does research** → dumps everything into `research.md`
3. **We refine** → ask Claude to go deeper on specific areas
4. **We synthesize** → create `notes.md` with our editorial decisions
5. **Claude writes the script** → creates `script.md` based on our notes
6. **We record**

---

## Episode Structure

Every episode follows the same 3-act structure:

| Section | Time | What It Does |
|---------|------|--------------|
| **Intro: The Hook** | 10-15 min | Open with impact stats, then paint the "world before" |
| **Act 1: Discovery** | 20-25 min | The human story—inventors, failures, the breakthrough |
| **Act 2: Diffusion** | 25-35 min | How it spread—resistance, tipping points, who won |
| **Act 3: Aftermath** | 25-30 min | What changed—immediate effects, winners/losers, structural shifts |
| **Outro: Open Questions** | 5-10 min | 2-3 questions to leave listeners thinking |

See `episode_template.md` for detailed guidance on what goes in each section.

---

## Files Per Episode

Each episode gets its own folder with three files:

```
episodes/
└── refrigeration/
    ├── research.md    ← Claude creates this (raw research)
    ├── notes.md       ← We create this (our synthesis)
    └── script.md      ← Claude creates this (recording doc)
```

### research.md
**Who makes it:** Claude
**What it is:** Comprehensive research organized by episode section. Everything we might need—more is better. Best stuff is marked with ⭐.

**How to use it:** This is our source material. Read through it, flag what's interesting, note what's missing.

### notes.md
**Who makes it:** Us (Jeff & Cyrus)
**What it is:** Our editorial decisions—what to include, what angle to take, who drives each section, pacing notes.

**How to use it:** This is where we collaborate. Trade notes, debate what to include, figure out the story we're telling. Claude doesn't touch this unless we ask.

### script.md
**Who makes it:** Claude (based on research + our notes)
**What it is:** The recording document—structured enough to keep us on track, loose enough for real conversation.

**How to use it:** This is what we have in front of us when we record. Scripted transitions, key beats, stats to hit.

---

## Step by Step

### 1. Pick a Topic
Choose from `topics.md` or add a new one. Create a folder:
```
episodes/[topic-name]/
```

### 2. Kick Off Research
Ask Claude to research the topic. Something like:

> "Let's start research on [topic]. Create a research.md file in the episode folder using the research template."

Claude will create a comprehensive `research.md` covering all sections of the episode structure.

### 3. Review & Request More
Read through the research. Ask for deeper dives:

> "Go deeper on the resistance story—who were the main blockers?"
> "Find more specific anecdotes about [person]."
> "What are the best stats on adoption curves?"

All additions go into the same `research.md` file.

### 4. Create Episode Notes
Once research feels complete, we create `notes.md`. Copy the template from `templates/episode_notes_template.md`.

This is our working doc:
- What's the thesis of this episode?
- Which characters do we focus on?
- What's our angle on the diffusion story?
- Who drives each section?
- What do we definitely want to include?

We can do this together or async—trading notes, debating, reorganizing.

### 5. Generate the Script
When notes are ready, ask Claude to write the script:

> "Based on the research and our notes, create the script.md for this episode."

Claude produces a structured recording document with:
- Scripted intros and transitions
- Key beats in order
- Stats and details to hit
- Cues for who's driving each section

### 6. Review & Record
Review the script together. Make adjustments. Then record.

---

## Folder Structure

```
/
├── FLOW.md                  ← You are here
├── overview.md              ← Podcast concept and goals
├── episode_template.md      ← The 3-act structure (reference)
├── topics.md                ← Episode ideas
├── pilot_checklist.md       ← Checklist for pilot episode
├── AGENTS.md                ← Instructions for Claude
│
├── templates/               ← Copy these for new episodes
│   ├── research_template.md
│   ├── episode_notes_template.md
│   └── script_template.md
│
└── episodes/                ← Episode folders go here
    └── [topic-name]/
        ├── research.md
        ├── notes.md
        └── script.md
```

---

## Key Files to Know

| File | What It's For |
|------|---------------|
| `overview.md` | The podcast concept—what we're making and why |
| `episode_template.md` | Detailed guide to our episode structure |
| `topics.md` | Ideas for episodes, with pilot recommendations |
| `pilot_checklist.md` | Planning checklist for the pilot |

---

## Tips

**On research:** More is better at the start. It's easier to cut than to realize you're missing something mid-recording.

**On notes:** This is where we make the creative decisions. The research is raw material; the notes are our vision for the episode.

**On the script:** It's a guide, not a straitjacket. Leave room for genuine conversation and tangents.

**On Claude:** It's good at research, organization, and drafting. It's not good at knowing what makes a compelling episode—that's our job.

---

## Questions?

If something's unclear or the process isn't working, let's adjust. This is v1.
