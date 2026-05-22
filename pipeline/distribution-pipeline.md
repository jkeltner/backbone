# Distribution Pipeline

Gets the finished episode live on podcast apps via Transistor.fm. YouTube video is uploaded directly to YouTube from Descript's export, not from this pipeline.

---

## Prerequisites

- Production pipeline complete: `episode.mp3`, `chapters.json`, `transcript.html`, `transcript.srt`
- Transistor account configured (see One-Time Setup below)
- API keys in `.env`

---

## Steps

| # | Script | What it does | Auto? | Review? |
|---|--------|-------------|-------|---------|
| 1 | `distribute_podcast.py` | Upload mp3 + metadata + chapters + transcript to Transistor.fm as draft | Yes | Jeff publishes |
| 2 | (Transistor built-in) | Episode page auto-generated from RSS; auto-distributes to Apple, Spotify, etc. | Automatic | No |

YouTube and newsletter are handled outside this pipeline (Descript export → manual YouTube upload; no automated newsletter).

---

## Running

```bash
# Full distribution pipeline:
python tools/release.py {topic} distribute

# Individual steps:
python tools/distribute_podcast.py {topic}                # upload as draft
python tools/distribute_podcast.py {topic} --dry-run      # preview
```

---

## One-Time Setup

### Transistor.fm ($19/month)
1. Create account at transistor.fm
2. Configure show: title, description, artwork, categories
3. Get API key from Settings → API
4. Get Show ID from the dashboard URL
5. Submit RSS feed to Apple Podcasts and Spotify directories (manual, once)
6. Add to `.env`:
   ```
   TRANSISTOR_API_KEY=...
   TRANSISTOR_SHOW_ID=...
   ```

---

## Service Details

### Transistor.fm
- REST API: developers.transistor.fm
- Auto-distributes RSS to Spotify, Apple Podcasts, and all podcast apps
- Supports Podcasting 2.0 chapters and transcripts
- Built-in website with embedded player
- Built-in audio→video for YouTube (not used; Descript handles video)
- Analytics dashboard

---

## Estimated Monthly Cost

| Service | Cost |
|---------|------|
| Transistor.fm | $19/month |
| **Total** | **$19/month** |
