---
topic: refrigeration
agent: producer
status: draft
date: 2026-09-13
---

# Episode Metadata: Refrigeration

Publish-ready fields for Transistor. `tools/audio_assemble.py` reads the **Top choice** line (ID3 title) and the number section below (ID3 track); `tools/distribute_podcast.py` reads the top choice, the number, the first paragraph under the description header (Transistor summary), and the keywords list; `tools/timestamp_chapters.py` rewrites the **Chapter Markers** table and the runtime line from the real audio. Keep those headers and formats intact — the parsers key on the first occurrence of each header string.

---

## Episode Title Options

1. **Refrigeration: You Don't Make Cold, You Move Heat** — Jeff's own line from the How It Works beat. A small, true, slightly disorienting claim that makes a browser stop; it is also the show's identity in miniature (a mental model, not a summary), and it is the one thing every listener will repeat to someone else this week.
2. **Refrigeration: The Safest Chemical Ever Invented** — the Freon irony in five words; the listener knows something goes wrong. Strong, but it centers the back half of the episode and undersells Tudor and the ice trade.
3. **Refrigeration: A Slippery Speculation** — the Boston Gazette's 1806 burn. Charming and period-true; a little too inside for someone who doesn't yet know the story.
4. **Refrigeration: Let Those Laugh Who Win** — Tudor's motto, reprised in the close. Good story hook; reads as generic without context.
5. **Refrigeration: Harmless at a Thousand, Dangerous at a Billion** — the episode's portable principle. Truest to the thesis; most abstract on a podcast-app screen.

**Top choice: "Refrigeration: You Don't Make Cold, You Move Heat"**

Rationale: the best subtitle makes someone want to listen before they know anything about the topic. "You don't make cold, you move heat" does that — it sounds wrong, it is right, and it promises the episode will tell you why. It avoids the "How X Built Y" pattern, it belongs to a host rather than to a source, and it points straight at the coils on the back of the listener's own refrigerator, which is where the episode wants to leave them. Runner-up: option 2.

---

## Episode Description

*(Short form for podcast apps and Transistor's summary field; the long form for the episode page follows.)*

In February 1806 a Boston newspaper ran a one-line joke about a twenty-three-year-old who had loaded a ship with pond ice and sailed for the Caribbean, where nobody had anywhere to keep it. He went to debtors' prison. He also started a two-hundred-year story that ends with a treaty about what's inside your refrigerator — the first in United Nations history ratified by every country on earth. Jeff and Cyrus follow cold from a Boston pond to the stratosphere, and find that every time somebody won a round, the winner fought the next one.

### Long Description (episode page / website)

Every technology you depend on was once a curiosity that smart people thought would never work. Refrigeration's has a date: February 1806, when a brig cleared Boston Harbor for Martinique carrying about eighty tons of pond ice and the Boston Gazette hoped it would "not prove a slippery speculation."

Jeff and Cyrus follow cold across two centuries and four fluids. Frederic Tudor's ice trade, and the sixteen-thousand-mile voyage to Calcutta that saved him. John Gorrie, who made ice with a machine in Florida in 1850 and died broke because frozen pond water was too big an industry to beat. Carl von Linde's compressor, which ran for thirty-one years in a brewery cellar — and the five minutes in the middle of the episode where you finally learn how the box in your kitchen actually works. Gustavus Swift's refrigerator cars, the butchers of twenty states who fought them to the Supreme Court, and a ship's captain hauled out of a frozen hold by the heels. Mary Engle Pennington, hired by the federal government under her initials, who wrote the rules that made stored food something you'd eat. Einstein and Szilárd's refrigerator, which howled like a jackal. Thomas Midgley, who blew out a candle with a lungful of Freon. The electric utilities that financed the refrigerator on your light bill during the Depression. A postdoc who asked where the molecules went, a British monitoring program about to be cut for budget reasons that found a hole in the sky, a company that reversed itself in twenty days, and a treaty every nation on earth signed.

Then the Backbone Test: what depends on cold, what it costs, whether we could ever go back — and the question the story leaves you with. What's harmless at a thousand and dangerous at a billion, and who is keeping the boring long record that will catch it?

---

## Episode Number

1

Season: not used. Backbone runs as a single numbered feed; leave the season field blank in Transistor unless the hosts decide otherwise.

---

## Estimated Runtime

**Spoken words:** 24,473 (labels, audio tags, segment breaks, and music cues excluded). 507 turns — Jeff 255, Cyrus 252.

**Raw speech at 187 words per minute:** about 131 minutes. **At the 1.2x release speed (225 words per minute):** about 109 minutes of speech. With the theme in, five bumpers, and the theme out, the finished episode runs **111 minutes** — inside the 90–120 minute target.

Per chapter (spoken words / estimated release-speed minutes): Opening 2,529 / 11; Cold as a Commodity 4,565 / 20; The Machine and the Chain 5,093 / 23; Cold Comes Home 4,609 / 20; Cold and the Sky 4,090 / 18; Built In 3,587 / 16.

---

## Chapter Markers

*(Estimated from cumulative word count at 225 words per minute plus music; `tools/timestamp_chapters.py` replaces these with real timestamps from the assembled audio.)*

| Chapter | Title | Estimated Timestamp |
|---------|-------|---------------------|
| Opening | The Hook | 00:00:00 |
| Wave 1 | Cold as a Commodity | 00:11:33 |
| Wave 2 | The Machine and the Chain | 00:32:04 |
| Wave 3 | Cold Comes Home | 00:55:15 |
| Wave 4 | Cold and the Sky | 01:16:40 |
| Built In | The Big Picture | 01:35:47 |


---

## Tags / Keywords

refrigeration, cold chain, ice trade, Frederic Tudor, John Gorrie, Carl von Linde, Gustavus Swift, Mary Engle Pennington, Einstein refrigerator, Thomas Midgley, Freon, CFCs, ozone hole, Montreal Protocol, Kigali Amendment, history of technology, technology diffusion, food history, business history, thermodynamics

---

## Transistor Fields

| Field | Value |
|---|---|
| Show | Backbone: From Breakthrough to Built-In |
| Episode title | Refrigeration: You Don't Make Cold, You Move Heat |
| Number | 1 |
| Season | (blank) |
| Type | Full |
| Summary | Short description above |
| Description / show notes | `final/show-notes.md` (see note in producer-report.md about the front-matter block) |
| Keywords | Tags / Keywords above |
| Author | Jeff Keltner and Cyrus Mistry |
| Categories | History (primary); Technology (secondary) — set at show level |
| Language | English |
| Explicit | No |
| Artwork | Show-level `assets/show_cover_art.png` embedded in the MP3; per-episode cover, if produced in Claude Design, goes in `episodes/refrigeration/assets/images/` and is uploaded by hand |
| Chapters | `final/chapters.json` (Podcasting 2.0), generated by `timestamp_chapters.py` |
| Transcript | `final/transcript.srt`, converted to plain text at upload |
| Publish status | Draft; human publish gate in `/distribute` |
