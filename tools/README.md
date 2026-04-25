# Backbone Tools

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install elevenlabs
cp .env.example .env   # then fill in API key and voice IDs
```

On subsequent runs, just activate the venv first:
```bash
source .venv/bin/activate
```

---

## tts_dialogue.py — Generate dialogue audio (recommended)

Uses the ElevenLabs **Text to Dialogue API** to generate one audio file per
wave/section. Natural multi-speaker prosody, far fewer API calls, no per-turn
stitching required.

Output: `wave-00-opening.mp3`, `wave-01.mp3`, `wave-02.mp3`, etc.

```bash
# Dry run — see what would be generated
python tools/tts_dialogue.py refrigeration --dry-run

# Generate all waves (prompts for confirmation)
python tools/tts_dialogue.py refrigeration

# Generate a specific wave by index (0=opening, 1=wave 1, etc.)
python tools/tts_dialogue.py refrigeration --wave 0
python tools/tts_dialogue.py refrigeration --wave 0 --yes

# Skip confirmation
python tools/tts_dialogue.py refrigeration --yes
```

---

## tts_generate.py — Generate per-turn audio segments (fallback)

Parses `episodes/{topic}/final/assembled.txt` and calls ElevenLabs for each speaker turn.
Saves numbered mp3 files to `episodes/{topic}/assets/audio/`.

### Common commands

```bash
# List all turns with segment labels (no API calls)
python tools/tts_generate.py refrigeration --list

# Dry run — see what would be generated without calling the API
python tools/tts_generate.py refrigeration --dry-run

# Generate all segments (prompts for confirmation)
python tools/tts_generate.py refrigeration

# Generate all segments, skip confirmation prompt
python tools/tts_generate.py refrigeration --yes

# Generate only turns in a specific segment (partial name match)
python tools/tts_generate.py refrigeration --segment "Opening"
python tools/tts_generate.py refrigeration --segment "Opening" --yes
python tools/tts_generate.py refrigeration --segment "Wave 1"
python tools/tts_generate.py refrigeration --segment "Wave 2"
python tools/tts_generate.py refrigeration --segment "Wave 3"
python tools/tts_generate.py refrigeration --segment "Built In"
```

### Resume after failure

Already-generated files are skipped automatically. Just re-run the same command.

### Output

```
episodes/{topic}/assets/audio/
  segment-0001-jeff.mp3
  segment-0002-cyrus.mp3
  segment-0003-jeff.mp3
  ...
  manifest.json       ← ordered list of all turns + music cue positions (for assembly)
```

### Segment names

Use `--list` to see the exact segment names in a given script before filtering.
Typical segments for a refrigeration-style episode:
- `Opening`
- `Wave 1 - The Ice Trade`
- `Wave 2 - The Machine Age`
- `Wave 3 - Cold Comes Home`
- `Built In`
