---
asset: design-system
status: v2 draft
date: 2026-09-29
---

# Backbone Design System (v2)

Everything visual for Backbone comes from this folder. `tokens.css` holds the colors and type, `fonts/` holds the typefaces, `templates/` holds one HTML file per asset, and `tools/render_art.py` turns an episode's `art.json` into finished PNGs. The published reference copy of this system lives in Claude as the **Backbone** design system artifact; this folder is the one the pipeline actually renders from.

## The idea

Backbone looks like an **instrument plate**: a dark field with faint graph paper, registration brackets in the corners, a bone-white condensed wordmark, and one plotted **adoption curve** per episode. The curve is the show's thesis drawn as a picture. Every technology we cover climbs an S-curve, and the interesting part is the middle of it. The logo is that curve reduced to a mark, with a node at the tipping point.

The frame never changes between episodes. Three things change: the title, the curve, and one accent color.

## What changed from v1

| | v1 (April) | v2 |
|---|---|---|
| Ornament | Eye-on-a-line | **Diffusion mark**: flat line, S-rise, ring node at the tipping point |
| Field | Flat navy #020819 | Night #040A1C with vignette, 5% graph-paper grid, light grain |
| Per-episode art | None | Adoption plate built from the episode's own sourced data |
| Accent | One blue | Ice blue stays the show accent; each episode picks one material accent |
| Social templates | Georgia serif, purple gradient, #4A90D9 (off-brand) | Rebuilt on the cover's type and palette |
| Fonts | Saira Condensed + Barlow (+ a mono) | Same families, now written down, bundled and licensed (SIL OFL) |

## Color

| Token | Hex | Use |
|---|---|---|
| `--bb-night` | #040A1C | Field. Every asset sits on it |
| `--bb-night-deep` | #01040F | Vignette edge |
| `--bb-night-up` | #0B1530 | Center glow, raised panels |
| `--bb-bone` | #EAE5D7 | Wordmark, titles, the curve itself |
| `--bb-bone-dim` | #B9B3A4 | Body copy |
| `--bb-ash` | #857F70 | Mono labels, axis years, captions |
| `--bb-signal` | #8FB3E0 | Show accent (ice blue): taglines, subtitles, data dots |

**Episode accents.** Pick the one that matches the technology's material. One per episode, and it replaces signal on that episode's assets only.

| Name | Hex | For |
|---|---|---|
| ice | #8FB3E0 | Refrigeration, cold chain (Ep. 1) |
| copper | #D9956B | Wire, the grid, electricity |
| sodium | #E6B85C | Lighting, oil, combustion |
| phosphor | #8CCBA4 | Screens, radio, signals |
| rust | #D27A6A | Steel, rail, iron |
| lilac | #B5A3E0 | Chemistry, materials, pharma |

Accent is for small things: the subtitle, data dots, the tipping-point ring, one mono label. Never a background, never a title.

## Type

| Role | Face | Setting |
|---|---|---|
| Wordmark, titles, big numbers | Saira Condensed 700 | All caps, +0.02em, line-height 0.86 |
| Subtitles | Barlow 500 italic | Accent color, sentence or title case |
| Body, quotes | Barlow 400/500 | Bone-dim; quotes in bone |
| Taglines | Barlow Semi Condensed 600 | All caps, +0.28em, accent |
| Labels, years, URLs | JetBrains Mono 400/500 | All caps, +0.32em, ash; `<b>` lifts to bone-dim |

Titles use the episode's one-word topic (REFRIGERATION), never the full episode title. The part after the colon becomes the subtitle.

## The mark

A flat line, an S-shaped rise, a flat line, with a ring node at the inflection filled with the accent. It sits above the wordmark in centered lockups and to its left in horizontal ones. Stroke gets heavier as the mark gets smaller (see `data-stroke` in each template). Don't rotate it, recolor the line, or put more than one node on it.

## The adoption plate

Each episode's plate plots one real series from the research, the share of U.S. households (or the equivalent) that had the technology.

- **Solid line and dots**: sourced data points only, each with a source in `art.json`.
- **Dashed tails**: the shape of the curve beyond the sourced range. They are not data, and the plate never labels them with a number.
- **Ring**: where the curve crosses 50%. It echoes the logo node and carries no label.
- Monotone interpolation, so the line never overshoots the data.
- Same believability rule as the scripts: if a number would make a smart listener squint, it doesn't go on the plate.

## Templates

| File | Size | Where it goes | Keep-clear |
|---|---|---|---|
| `show-cover.html` | 3000×3000 | Transistor / Apple / Spotify show art | — |
| `avatar.html` | 800×800 | YouTube + social profile (circle crop) | Outer 15% |
| `youtube-banner.html` | 2560×1440 | YouTube channel banner | All type inside the center 1546×423 |
| `episode-cover.html` | 3000×3000 | Episode artwork on Transistor | — |
| `youtube-thumbnail.html` | 1280×720 | YouTube full-episode thumbnail | Bottom-right 15% (timestamp badge) |
| `youtube-episode.html` | 1920×1080 | Descript background for the full-episode video | Below y = 700 px (waveform + captions) |
| `youtube-short.html` | 1080×1920 | Descript background for Shorts / Reels | Top 160 px, captions 680–1200 px, bottom 400 px |
| `social-announce.html` | 1200×675 | X / LinkedIn launch post, link previews | — |
| `social-quote.html` | 1080×1350 | Pull quote (portrait). One card per item in `quotes` | — |
| `social-stat.html` | 1080×1350 | One number with its comparison, and the curve unless the stat sets `"curve": null`. One card per item in `stats` | — |
| `social-compare.html` | 1080×1350 | The episode's technology against 2–4 others on one axis. Rendered only when `compare` exists | — |

Open any template straight in a browser and it shows Episode 1 as sample data.

## Making an episode's art

The Producer writes `episodes/{topic}/assets/images/art.json` as part of `/produce` (see `roles/producer.md`), and `/produce` renders it. By hand:

1. Write `art.json`:

```json
{
  "number": 2,
  "topic": "Example Topic",
  "subtitle": "The Part After the Colon",
  "accent": "copper",
  "hosts": "Jeff Keltner & Cyrus Mistry",
  "url": "backbone.fm",
  "teaser": "One sentence for the announcement card.",
  "curve": {
    "label": "What the y-axis is, in plain words",
    "range": [1900, 1950],
    "points": [[1910, 5], [1925, 40], [1940, 85]],
    "sources": ["one per point, or one covering all"]
  },
  "quotes": [
    { "text": "...", "speaker": "Cyrus Mistry", "context": "on ..." }
  ],
  "stats": [
    { "value": "5% → 85%", "label": "...", "context": "...", "sources": ["..."] },
    { "value": "4 million", "label": "...", "context": "...", "curve": null, "sources": ["..."] }
  ],
  "compare": {
    "title": "A short headline the chart proves",
    "label": "Share of U.S. households",
    "range": [1900, 1960],
    "series": [
      { "name": "Example Topic", "points": [[1910, 5], [1925, 40], [1940, 85]], "highlight": true },
      { "name": "Telephone", "points": [[1920, 34], [1946, 50]] }
    ],
    "context": "One line on what the comparison shows.",
    "sources": ["..."]
  }
}
```

   Every value above is a dummy that shows the shape; none of it is real data. Rules: curve and compare points come only from research marked verified (never `[VERIFY]` or `[BELIEVABILITY]`); every stat and chart lists its sources; quotes are verbatim from `final/assembled.txt`. A stat with `"curve": null` gets the big-number layout with no chart. Aim for 4–6 quotes and 3–4 stats.

2. `python tools/render_art.py {topic}` writes everything next to `art.json`:

| Output | Count |
|---|---|
| `episode-cover.png` + `.jpg` | 1 |
| `youtube-thumbnail.png`, `youtube-episode.png`, `youtube-short.png` | 3 |
| `social-announce.png` | 1 |
| `social-quote-01.png` … | one per quote |
| `social-stat-01.png` … | one per stat |
| `social-compare.png` | 1 if `compare` exists |

3. Look at the covers at thumbnail size before uploading. The title has to read at 60 px.

`python tools/render_art.py --show` re-renders the show-level assets into `assets/brand/`.

## Adding a new asset type

Copy the closest template in `templates/`, change its `bb-size` and layout, bind text with `data-bb="…"` (fields are listed in `_kit.js`), and add its name to `EPISODE` in `tools/render_art.py`. Every size is in `--s` (1% of the short side), so layouts carry across canvas sizes.

## Don'ts

- No gradients other than the field's vignette. No purple.
- No serif faces. No Helvetica fallback in finished renders (the fonts are bundled).
- No photos or AI imagery on the frame. If an episode ever needs an image, it goes inside a plate-shaped panel, desaturated toward night.
- No production vocabulary on public assets ("wave", "segment", "cold open").
- Don't use the accent for titles or large fills.
