# Distribution Pipeline

Gets the finished episode live on platforms: podcast apps (via Transistor.fm), YouTube, and newsletter (via Buttondown).

---

## Prerequisites

- Production pipeline complete: `episode.mp3`, `chapters.json`, `transcript.html`, `transcript.srt`, `episode-full.mp4`
- Service accounts configured (see One-Time Setup below)
- API keys in `.env`

---

## Steps

| # | Script | What it does | Auto? | Review? |
|---|--------|-------------|-------|---------|
| 1 | `distribute_podcast.py` | Upload mp3 + metadata + chapters + transcript to Transistor.fm as draft | Yes | Jeff publishes |
| 2 | `distribute_youtube.py` | Upload audiogram mp4 + metadata + SRT captions to YouTube as unlisted | Yes | Jeff publishes |
| 3 | (Transistor built-in) | Episode page auto-generated from RSS | Automatic | No |
| 4 | `distribute_newsletter.py` | Draft newsletter from social content → push to Buttondown as draft | Agent | Jeff reviews + sends |

---

## Running

```bash
# Full distribution pipeline:
python tools/release.py {topic} distribute

# Individual steps:
python tools/distribute_podcast.py {topic}                # upload as draft
python tools/distribute_podcast.py {topic} --dry-run      # preview
python tools/distribute_youtube.py {topic}                 # upload as unlisted
python tools/distribute_youtube.py {topic} --auth          # one-time OAuth setup
python tools/distribute_newsletter.py {topic}              # create draft
python tools/distribute_newsletter.py {topic} --dry-run    # preview
```

---

## One-Time Setup

### 1. Transistor.fm ($19/month)
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

### 2. YouTube (free)
1. Create YouTube channel (or use existing Google account)
2. Go to Google Cloud Console → create project → enable YouTube Data API v3
3. Create OAuth2 credentials (Desktop application type)
4. Run auth flow: `python tools/distribute_youtube.py --auth`
5. Add to `.env`:
   ```
   YOUTUBE_CLIENT_ID=...
   YOUTUBE_CLIENT_SECRET=...
   YOUTUBE_REFRESH_TOKEN=...   # from auth flow
   ```

### 3. Buttondown (free tier to start)
1. Create account at buttondown.email
2. Configure sending domain (optional but recommended)
3. Get API key from Settings
4. Add to `.env`:
   ```
   BUTTONDOWN_API_KEY=...
   ```

---

## Service Details

### Transistor.fm
- REST API: developers.transistor.fm
- Auto-distributes RSS to Spotify, Apple Podcasts, and all podcast apps
- Supports Podcasting 2.0 chapters and transcripts
- Built-in website with embedded player
- Analytics dashboard

### YouTube
- Data API v3: 10,000 daily quota units
- Video upload costs 1,600 units (6 uploads/day max — fine for monthly episodes)
- Captions uploaded via Captions API
- SRT subtitles auto-indexed for search

### Buttondown
- API for programmatic email drafts
- Markdown-native (newsletter body written in markdown)
- Free tier: up to 100 subscribers
- $9/month for custom domain + more subscribers

---

## Estimated Monthly Cost

| Service | Cost |
|---------|------|
| Transistor.fm | $19/month |
| YouTube | Free |
| Buttondown | Free → $9/month |
| **Total** | **$19–28/month** |
