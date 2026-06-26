#!/usr/bin/env python3
"""
fetch_feedback.py — Fetch a per-checkpoint Google Doc + inline comments via the gws CLI
and write a markdown file with comments quoted inline at their anchor points.

Used by /script, /polish, and /refine to ingest checkpoint feedback. The Google Doc URL
for each checkpoint is stored in `episodes/{topic}/feedback/docs.json`:

    {
      "01": "https://docs.google.com/document/d/<id>/edit",
      "02": "https://docs.google.com/document/d/<id>/edit",
      "03": "https://docs.google.com/document/d/<id>/edit"
    }

A bare file ID (without the URL wrapper) is also accepted.

Output: `episodes/{topic}/feedback/0N-{checkpoint}-comments.md`. Body comes from
`gws drive files export` (text/markdown). Comments come from `gws drive comments list`
and are inserted as block quotes after the line containing each comment's
`quotedFileContent.value`. Comments with no resolvable anchor land in a final
"Unanchored comments" section.

Usage:
    python tools/fetch_feedback.py <topic> <checkpoint-number>

    <checkpoint-number>: "01", "02", or "03"
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CHECKPOINT_NAMES = {"01": "blueprint", "02": "script", "03": "polish"}
COMMENT_FIELDS = (
    "nextPageToken,comments(id,author(displayName),content,quotedFileContent,"
    "createdTime,resolved,replies(author(displayName),content,createdTime))"
)


def extract_file_id(url_or_id: str) -> str:
    """Accept a Google Doc URL or a bare file ID."""
    url_or_id = url_or_id.strip()
    m = re.search(r"/document/d/([A-Za-z0-9_-]+)", url_or_id)
    if m:
        return m.group(1)
    if "/" not in url_or_id and " " not in url_or_id:
        return url_or_id
    raise ValueError(f"Could not extract file ID from: {url_or_id!r}")


def run_gws(args: list[str], capture_json: bool = True) -> dict | str:
    proc = subprocess.run(
        ["gws", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"gws {' '.join(args)} failed (exit {proc.returncode}):\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    output = proc.stdout
    if "Using keyring backend:" in output:
        output = output.split("\n", 1)[1] if "\n" in output else ""
    if not capture_json:
        return output
    try:
        return json.loads(output)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"gws returned non-JSON output:\n{output[:500]}") from e


def export_doc_markdown(file_id: str) -> str:
    """Export the Google Doc as markdown. gws refuses to write outside cwd, so we
    create a temp dir inside cwd and write the export file there."""
    with tempfile.TemporaryDirectory(dir=".") as td:
        out_path = Path(td) / "doc.md"
        proc = subprocess.run(
            [
                "gws",
                "drive",
                "files",
                "export",
                "--params",
                json.dumps({"fileId": file_id, "mimeType": "text/markdown"}),
                "--output",
                str(out_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"export failed (exit {proc.returncode}):\n{proc.stderr or proc.stdout}"
            )
        if not out_path.exists():
            raise RuntimeError(f"export produced no output:\n{proc.stdout}\n{proc.stderr}")
        return out_path.read_text(encoding="utf-8")


def fetch_comments(file_id: str) -> list[dict]:
    """Fetch all comments, following pagination. The Drive API defaults to a
    page size of 20 and silently truncates without it, so request the max (100)
    and follow nextPageToken until exhausted."""
    comments: list[dict] = []
    page_token: str | None = None
    while True:
        params: dict = {"fileId": file_id, "fields": COMMENT_FIELDS, "pageSize": 100}
        if page_token:
            params["pageToken"] = page_token
        data = run_gws(["drive", "comments", "list", "--params", json.dumps(params)])
        if not isinstance(data, dict):
            break
        comments.extend(data.get("comments", []))
        page_token = data.get("nextPageToken")
        if not page_token:
            break
    return comments


def normalize_anchor(text: str) -> str:
    """Unescape HTML entities and collapse whitespace for matching."""
    return " ".join(html.unescape(text).split())


def render_comment(c: dict, is_reply: bool = False) -> list[str]:
    author = (c.get("author") or {}).get("displayName", "UNKNOWN")
    date = (c.get("createdTime") or "").split("T")[0]
    label = "REPLY" if is_reply else "COMMENT"
    header = f"**{author.upper()} {label}"
    if date:
        header += f" ({date})"
    header += "**"
    if not is_reply and c.get("resolved"):
        header = header[:-2] + " [RESOLVED]**"
    body_lines = (c.get("content") or "").splitlines() or [""]
    lines = [f"> {header}:" if is_reply else None]
    if not is_reply:
        anchor = normalize_anchor((c.get("quotedFileContent") or {}).get("value", ""))
        if len(anchor) > 200:
            anchor = anchor[:97] + "…" + anchor[-97:]
        if anchor:
            lines = [f'> {header} on "{anchor}":']
        else:
            lines = [f"> {header}:"]
    for bl in body_lines:
        lines.append(f"> {bl}" if bl else ">")
    for reply in c.get("replies") or []:
        lines.append(">")
        for rl in render_comment(reply, is_reply=True):
            lines.append(rl)
    return lines


def find_anchor_line(md_lines: list[str], anchor: str, already_used: dict[int, int]) -> int | None:
    """Return the index of the line that contains the anchor text (normalized).
    Tracks how many times each line has been used so multiple comments on the
    same line preserve insertion order."""
    if not anchor:
        return None
    norm_anchor = normalize_anchor(anchor)
    if not norm_anchor:
        return None
    snippet = norm_anchor[:60]
    best = None
    for i, line in enumerate(md_lines):
        if snippet in normalize_anchor(line):
            best = i
            if already_used.get(i, 0) == 0:
                return i
    return best


def build_output(topic: str, checkpoint: str, file_id: str, body_md: str, comments: list[dict]) -> str:
    name = CHECKPOINT_NAMES[checkpoint]
    md_lines = body_md.splitlines()
    insertions: dict[int, list[str]] = {}
    used: dict[int, int] = {}
    unanchored: list[dict] = []
    for c in sorted(comments, key=lambda x: x.get("createdTime", "")):
        anchor = normalize_anchor((c.get("quotedFileContent") or {}).get("value", ""))
        line_idx = find_anchor_line(md_lines, anchor, used) if anchor else None
        if line_idx is None:
            unanchored.append(c)
            continue
        used[line_idx] = used.get(line_idx, 0) + 1
        block = [""] + render_comment(c) + [""]
        insertions.setdefault(line_idx, []).extend(block)
    out: list[str] = []
    out.append(f"# Feedback document: {name} (checkpoint {checkpoint})")
    out.append("")
    out.append(f"> Topic: `{topic}`. Source: Google Doc `{file_id}`.")
    out.append("> Body exported via `gws drive files export` (text/markdown).")
    out.append("> Comments fetched via `gws drive comments list` and inserted")
    out.append("> as block quotes after the line containing each anchor.")
    out.append("")
    out.append("---")
    out.append("")
    for i, line in enumerate(md_lines):
        out.append(line)
        if i in insertions:
            out.extend(insertions[i])
    if unanchored:
        out.append("")
        out.append("---")
        out.append("")
        out.append("## Unanchored comments")
        out.append("")
        out.append("> Comments whose anchored text could not be located in the exported markdown.")
        out.append("")
        for c in unanchored:
            out.extend(render_comment(c))
            out.append("")
    return "\n".join(out).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("topic")
    parser.add_argument("checkpoint", choices=sorted(CHECKPOINT_NAMES.keys()))
    args = parser.parse_args(argv)

    if shutil.which("gws") is None:
        print(
            "error: `gws` CLI not found on PATH. Install with `cargo install gws-cli` "
            "or see https://github.com/googleworkspace/cli.",
            file=sys.stderr,
        )
        return 2

    feedback_dir = Path("episodes") / args.topic / "feedback"
    docs_json = feedback_dir / "docs.json"
    if not docs_json.exists():
        print(
            f"error: {docs_json} not found. Create it with:\n"
            f'  {{ "{args.checkpoint}": "<Google Doc URL or file ID>" }}',
            file=sys.stderr,
        )
        return 2
    try:
        docs_map = json.loads(docs_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"error: {docs_json} is not valid JSON: {e}", file=sys.stderr)
        return 2
    if args.checkpoint not in docs_map:
        print(
            f"error: docs.json has no entry for checkpoint {args.checkpoint!r}. "
            f"Known keys: {sorted(docs_map.keys())}",
            file=sys.stderr,
        )
        return 2

    file_id = extract_file_id(docs_map[args.checkpoint])
    body_md = export_doc_markdown(file_id)
    comments = fetch_comments(file_id)

    name = CHECKPOINT_NAMES[args.checkpoint]
    out_path = feedback_dir / f"{args.checkpoint}-{name}-comments.md"
    out_path.write_text(
        build_output(args.topic, args.checkpoint, file_id, body_md, comments),
        encoding="utf-8",
    )
    print(f"wrote {out_path} ({len(comments)} comment(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
