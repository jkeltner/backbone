# Promotion Pipeline

Drives awareness across social channels over ~2 weeks per episode.

---

## Prerequisites

- Episode published on platforms (distribution pipeline complete)
- Social content and images generated (production pipeline complete)
- Twitter API credentials in `.env` (for automated posting)

---

## Steps

| # | Script | What it does | Auto? | Review? |
|---|--------|-------------|-------|---------|
| 1 | `promote_prepare.py` | Adapt social content for each platform + build schedule → `schedule.json` | Agent | Yes — approve schedule |
| 2 | `promote_twitter.py` | Post from schedule (thread on launch, drip over days) | Semi-auto | Content pre-approved |
| 3 | Manual (LinkedIn) | Agent writes the post; Jeff copies + pastes | No | Content pre-written |
| 4 | Manual (Instagram/TikTok) | Agent prepares clips + captions; Jeff/Cyrus uploads from phone | No | Content pre-written |

---

## Running

```bash
# Full promotion pipeline:
python tools/release.py {topic} promote

# Individual steps:
python tools/promote_prepare.py {topic}                        # generate all content + schedule
python tools/promote_prepare.py {topic} --launch-date 2026-04-01
python tools/promote_twitter.py {topic} --thread               # post launch thread
python tools/promote_twitter.py {topic} --all                  # post all due items
python tools/promote_twitter.py {topic} --status               # show what's posted/pending
python tools/promote_twitter.py {topic} --dry-run              # preview without posting
```

---

## Promotion Cadence

| Day | Twitter/X | LinkedIn | Instagram/TikTok |
|-----|-----------|----------|-------------------|
| Launch | Full 7-post thread | Long-form post | Announcement Reel |
| Day 2 | Quote card #1 | — | Clip #1 |
| Day 3 | Quote card #2 | — | — |
| Day 4 | Clip #1 | — | Clip #2 |
| Day 5 | Quote card #3 | — | — |
| Week 2 | "In case you missed it" | — | Clip #3 |

---

## Output Structure

```
episodes/{topic}/promotion/
├── schedule.json          ← what posts where and when
├── twitter-thread.md      ← ready-to-post thread text
├── linkedin-post.md       ← ready-to-copy post text
├── instagram-captions.md  ← per-clip captions + hashtags
└── posting-log.json       ← tracks what's been posted
```

---

## Platform Notes

### Twitter/X
- Free tier: 1,500 tweets/month (plenty for our cadence)
- Thread posted as reply chain for engagement
- Quote cards and clips posted as media tweets
- API credentials: developer.twitter.com → create app → generate tokens
- Add to `.env`:
  ```
  TWITTER_API_KEY=...
  TWITTER_API_SECRET=...
  TWITTER_ACCESS_TOKEN=...
  TWITTER_ACCESS_SECRET=...
  ```

### LinkedIn
- API too restricted for organic posting — manual copy/paste is standard
- Content pre-written in `linkedin-post.md`
- Tip: put episode link in comments (LinkedIn favors posts without outbound links)

### Instagram/TikTok
- No API for organic posting — upload from phone
- Clips pre-generated in both landscape (1920x1080) and portrait (1080x1920)
- Captions pre-written in `instagram-captions.md` with hashtags
- Recommended: upload vertical clips (9:16) as Reels
