#!/usr/bin/env python3
"""
social_images.py — Generate social media images from HTML templates

Renders quote cards, stat graphics, announcement card, and episode cover
from HTML templates using Playwright (headless Chromium screenshot).

Usage:
  python tools/social_images.py refrigeration
  python tools/social_images.py refrigeration --dry-run
  python tools/social_images.py refrigeration --type announcement  # specific type only

Requires: playwright (pip install playwright && playwright install chromium)

Templates in: templates/social/
Output to: episodes/{topic}/assets/images/
"""

import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = REPO_ROOT / "templates" / "social"


def load_social_content(topic):
    """Parse social-content.md for quotes and stats."""
    social_path = REPO_ROOT / "episodes" / topic / "final" / "social-content.md"
    if not social_path.exists():
        print(f"Error: {social_path} not found")
        sys.exit(1)
    return social_path.read_text()


def load_metadata(topic):
    """Get episode metadata."""
    meta_path = REPO_ROOT / "episodes" / topic / "final" / "metadata.md"
    meta = {"title": topic.replace("-", " ").title(), "number": ""}
    if meta_path.exists():
        text = meta_path.read_text()
        m = re.search(r'Top choice:\s*"(.+?)"', text)
        if m:
            meta["title"] = m.group(1)
    return meta


def extract_quotes(social_text):
    """Extract pull quotes from social-content.md."""
    quotes = []
    # Match quote blocks: > "text" followed by attribution
    blocks = re.split(r"\*\*Quote \d+", social_text)
    for block in blocks[1:]:  # Skip header
        lines = block.strip().splitlines()
        quote_lines = []
        speaker = ""
        context = ""

        in_quote = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(">"):
                text = stripped.lstrip("> ").strip()
                if text.startswith('"') or text.startswith("\u201c"):
                    in_quote = True
                    text = text.strip('"\u201c\u201d')
                if in_quote and text and not text.startswith("*") and not text.startswith("\u2014"):
                    quote_lines.append(text)
                if text.startswith("\u2014") or text.startswith("--"):
                    # Attribution line
                    attr = text.lstrip("\u2014- ").strip()
                    # Split "Name on ..." or "Name, the ..."
                    parts = re.split(r"\s+on\s+|\.\s+", attr, maxsplit=1)
                    speaker = parts[0].strip().rstrip(",")
                    if len(parts) > 1:
                        context = parts[1].strip()

        if quote_lines:
            full_quote = " ".join(quote_lines)
            # Clean up trailing quote marks
            full_quote = full_quote.strip('"\u201c\u201d')
            quotes.append({
                "text": full_quote,
                "speaker": speaker or "Backbone",
                "context": f", {context}" if context else "",
            })

    return quotes


def render_template(template_path, replacements, output_path, width=1200, height=675):
    """Render an HTML template to PNG using Playwright."""
    from playwright.sync_api import sync_playwright

    html = template_path.read_text()
    for key, value in replacements.items():
        html = html.replace(f"{{{{{key}}}}}", str(value))

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        page.set_content(html)
        page.screenshot(path=str(output_path), type="png")
        browser.close()

    size_kb = output_path.stat().st_size / 1024
    print(f"  {output_path.name} ({size_kb:.0f} KB)")


def auto_font_size(text, base=28, max_chars=200):
    """Scale font size based on text length."""
    if len(text) > max_chars:
        return max(18, base - (len(text) - max_chars) // 20)
    return base


def generate_images(topic, dry_run=False, image_type=None):
    """Generate all social images for an episode."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Error: playwright required")
        print("pip install playwright && playwright install chromium")
        sys.exit(1)

    social_text = load_social_content(topic)
    meta = load_metadata(topic)

    images_dir = REPO_ROOT / "episodes" / topic / "assets" / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    generated = []

    # 1. Quote cards
    if not image_type or image_type == "quotes":
        quotes = extract_quotes(social_text)
        print(f"Generating {len(quotes)} quote card(s)...")

        for i, q in enumerate(quotes):
            output = images_dir / f"quote-card-{i+1:02d}.png"
            if dry_run:
                print(f"  [dry run] {output.name}: \"{q['text'][:60]}...\"")
                continue
            render_template(
                TEMPLATES_DIR / "quote-card.html",
                {
                    "quote_text": q["text"],
                    "speaker_name": q["speaker"],
                    "context": q["context"],
                    "font_size": str(auto_font_size(q["text"])),
                },
                output,
            )
            generated.append(output)

    # 2. Stat graphics
    if not image_type or image_type == "stats":
        stats = extract_stats(social_text)
        print(f"Generating {len(stats)} stat graphic(s)...")

        for i, s in enumerate(stats):
            output = images_dir / f"stat-graphic-{i+1:02d}.png"
            if dry_run:
                print(f"  [dry run] {output.name}: {s['number']}")
                continue
            render_template(
                TEMPLATES_DIR / "stat-graphic.html",
                {
                    "stat_number": s["number"],
                    "stat_label": s["label"],
                    "context": s.get("context", ""),
                    "number_size": str(s.get("number_size", 96)),
                },
                output,
            )
            generated.append(output)

    # 3. Announcement card
    if not image_type or image_type == "announcement":
        print("Generating announcement card...")
        # Extract teaser from episode description
        m = re.search(
            r"Episode Description\s*\n+\*\(.*?\)\*\s*\n+([\s\S]+?)(?:\n---|\n##)",
            (REPO_ROOT / "episodes" / topic / "final" / "metadata.md").read_text(),
        )
        teaser = m.group(1).strip()[:200] + "..." if m else ""

        output = images_dir / "announcement.png"
        if dry_run:
            print(f"  [dry run] {output.name}")
        else:
            title_size = 56 if len(meta["title"]) < 40 else 44
            render_template(
                TEMPLATES_DIR / "announcement.html",
                {
                    "episode_title": meta["title"],
                    "teaser": teaser,
                    "title_size": str(title_size),
                },
                output,
            )
            generated.append(output)

    # 4. Episode cover
    if not image_type or image_type == "cover":
        print("Generating episode cover...")
        output = images_dir / "episode-cover.png"
        if dry_run:
            print(f"  [dry run] {output.name}")
        else:
            title_size = 120 if len(meta["title"]) < 30 else 90
            render_template(
                TEMPLATES_DIR / "episode-cover.html",
                {
                    "episode_title": meta["title"],
                    "episode_number": meta.get("number", ""),
                    "title_size": str(title_size),
                },
                output,
                width=3000,
                height=3000,
            )
            generated.append(output)

    print(f"\n{'[dry run] ' if dry_run else ''}Generated {len(generated)} image(s) in {images_dir}")
    return generated


def extract_stats(social_text):
    """Extract notable statistics from social content for stat graphics."""
    stats = []

    # Look for striking numbers in the thread posts
    # Pattern: number + context
    stat_patterns = [
        (r"(\d+(?:,\d+)*)\s*percent", "number"),
        (r"(\d+(?:,\d+)*)\s*(?:million|billion|thousand)", "number"),
        (r"from\s+(\w+)\s+(?:percent\s+)?to\s+(\w+)(?:\s+percent)?", "range"),
    ]

    # Simpler approach: scan thread posts for compelling number sentences
    posts = re.findall(r"\*\*Post \d+:\*\*\s*([\s\S]+?)(?=\*\*Post|\Z)", social_text)
    for post in posts:
        sentences = re.split(r"(?<=[.!?])\s+", post.strip())
        for sent in sentences:
            # Look for sentences with numbers that feel statistical
            if re.search(r"\b\d{2,}(?:,\d{3})*\b|\b(?:eight|ninety|eighty|thirty)\b", sent, re.IGNORECASE):
                numbers = re.findall(r"\b\d{1,3}(?:,\d{3})*\b", sent)
                if numbers:
                    # Use the most striking number
                    biggest = max(numbers, key=lambda n: int(n.replace(",", "")))
                    label = sent.strip()
                    if len(label) > 120:
                        label = label[:117] + "..."
                    stats.append({
                        "number": biggest,
                        "label": label,
                        "number_size": 96 if len(biggest) < 8 else 72,
                    })

    # Deduplicate and limit
    seen = set()
    unique_stats = []
    for s in stats:
        if s["number"] not in seen:
            seen.add(s["number"])
            unique_stats.append(s)
    return unique_stats[:4]  # Max 4 stat graphics


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate social media images")
    parser.add_argument("topic", help="Episode topic")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--type", choices=["quotes", "stats", "announcement", "cover"])
    args = parser.parse_args()

    generate_images(args.topic, dry_run=args.dry_run, image_type=args.type)


if __name__ == "__main__":
    main()
