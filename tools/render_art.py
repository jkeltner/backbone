#!/usr/bin/env python3
"""Render Backbone artwork from the HTML templates in design/templates/.

    python tools/render_art.py refrigeration            # all episode assets
    python tools/render_art.py refrigeration --only episode-cover youtube-thumbnail
    python tools/render_art.py --show                   # show-level assets -> assets/brand/

Episode data lives in episodes/{topic}/assets/images/art.json (schema: design/README.md).
Output PNGs land next to it. Requires playwright (already in requirements for the pipeline).
"""
import argparse, json, re, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / "design" / "templates"
EPISODE = ["episode-cover", "youtube-thumbnail", "youtube-episode", "youtube-short",
           "social-announce", "social-quote", "social-stat", "social-compare"]
SHOW = ["show-cover", "avatar", "youtube-banner"]


def size_of(tpl: Path):
    m = re.search(r'bb-size" content="(\d+)x(\d+)', tpl.read_text())
    return int(m.group(1)), int(m.group(2))


COVERS = {"episode-cover", "show-cover"}


def flatten(png: Path):
    """Podcast directories reject artwork with an alpha channel; store plain RGB.
    Covers also get a JPEG twin: the grain makes the 3000px PNG ~4.5 MB, the JPEG ~1 MB."""
    try:
        from PIL import Image
    except ImportError:
        return
    im = Image.open(png).convert("RGB")
    im.save(png, optimize=True)
    if png.stem in COVERS:
        im.save(png.with_suffix(".jpg"), quality=92, optimize=True, progressive=True)


def jobs_for(names, art):
    """Expand templates into render jobs. Quote and stat cards render once per item in
    art["quotes"] / art["stats"] (social-quote-01.png, -02 ...); a stat may carry its own
    "curve" (or null for no chart). The comparison card renders only if art has "compare"."""
    out = []
    for name in names:
        if art is None:
            out.append((name, name, None))
        elif name == "social-quote":
            for i, q in enumerate(art.get("quotes") or [art["quote"]], 1):
                out.append((name, f"{name}-{i:02d}", {**art, "quote": q}))
        elif name == "social-stat":
            for i, st in enumerate(art.get("stats") or [art["stat"]], 1):
                out.append((name, f"{name}-{i:02d}", {**art, "stat": st, "curve": st.get("curve", art.get("curve"))}))
        elif name == "social-compare":
            if art.get("compare"):
                out.append((name, name, art))
        else:
            out.append((name, name, art))
    return out


def render(names, data, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, out_name, data in jobs_for(names, data):
            tpl = TPL / f"{name}.html"
            w, h = size_of(tpl)
            page = browser.new_page(viewport={"width": w, "height": h})
            if data:
                page.add_init_script(f"window.BB = {json.dumps(data)};")
            page.goto(tpl.as_uri())
            page.wait_for_function("window.__bbReady === true", timeout=20000)
            page.wait_for_timeout(250)
            out = out_dir / f"{out_name}.png"
            page.screenshot(path=str(out))
            page.close()
            flatten(out)
            print(f"  {out.relative_to(ROOT)}  ({w}×{h})")
        browser.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("topic", nargs="?")
    ap.add_argument("--only", nargs="+")
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args()
    if a.show:
        render(a.only or SHOW, None, ROOT / "assets" / "brand")
    if a.topic:
        art = ROOT / "episodes" / a.topic / "assets" / "images" / "art.json"
        if not art.exists():
            sys.exit(f"Missing {art.relative_to(ROOT)} — copy the schema from design/README.md")
        render(a.only or EPISODE, json.loads(art.read_text()), art.parent)
    if not (a.show or a.topic):
        ap.print_help()


if __name__ == "__main__":
    main()
