#!/usr/bin/env python3
"""
create_feedback_doc.py — Create a Google Doc for a checkpoint feedback review.

Called from the tail of each checkpoint command (/blueprint, /script, /polish) so the
pipeline owns the feedback-doc lifecycle end to end. The created doc lives in:

    Backbone Feedback / {topic} / {NN}-{checkpoint}

with the artifact content (blueprint.md or concatenated chapter scripts) uploaded and
auto-converted to a Google Doc. The doc URL is written to
`episodes/{topic}/feedback/docs.json` under the matching key. Jeff shares the root
"Backbone Feedback" folder with Cyrus once, ever — all sub-folders and docs inherit.

Idempotency: if `docs.json[NN]` already has a URL, the script exits without creating
a new doc. To force regeneration, delete that entry from docs.json first.

Usage:
    python tools/create_feedback_doc.py <topic> <checkpoint>
        <checkpoint>: "01", "02", or "03"
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT_FOLDER_NAME = "Backbone Feedback"
CHECKPOINT_NAMES = {"01": "blueprint", "02": "script", "03": "polish"}


def run_gws_json(args: list[str]) -> dict:
    proc = subprocess.run(["gws", *args], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(
            f"gws {' '.join(args)} failed (exit {proc.returncode}):\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    out = proc.stdout
    if out.startswith("Using keyring"):
        out = out.split("\n", 1)[1] if "\n" in out else ""
    return json.loads(out) if out.strip() else {}


def find_or_create_folder(name: str, parent_id: str | None = None) -> str:
    name_q = name.replace("'", "\\'")
    q_parts = [
        f"name = '{name_q}'",
        "mimeType = 'application/vnd.google-apps.folder'",
        "trashed = false",
    ]
    if parent_id:
        q_parts.append(f"'{parent_id}' in parents")
    q = " and ".join(q_parts)
    data = run_gws_json(
        [
            "drive",
            "files",
            "list",
            "--params",
            json.dumps({"q": q, "fields": "files(id,name)"}),
        ]
    )
    matches = data.get("files", [])
    if matches:
        return matches[0]["id"]
    body: dict = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent_id:
        body["parents"] = [parent_id]
    data = run_gws_json(
        [
            "drive",
            "files",
            "create",
            "--params",
            json.dumps({"fields": "id"}),
            "--json",
            json.dumps(body),
        ]
    )
    return data["id"]


def strip_front_matter(text: str) -> str:
    if text.startswith("---"):
        m = re.match(r"^---\n.*?\n---\n+", text, re.DOTALL)
        if m:
            return text[m.end():]
    return text


def gather_content(topic: str, checkpoint: str) -> str:
    ep_dir = Path("episodes") / topic
    if checkpoint == "01":
        path = ep_dir / "blueprint.md"
        if not path.exists():
            raise FileNotFoundError(f"{path} not found — run /blueprint first")
        return strip_front_matter(path.read_text(encoding="utf-8"))
    chapter_files = sorted((ep_dir / "script").glob("chapter-*.txt"))
    if not chapter_files:
        raise FileNotFoundError(
            f"no chapter files in {ep_dir/'script'} — run /script first"
        )
    parts = []
    for cf in chapter_files:
        body = cf.read_text(encoding="utf-8").strip()
        title = cf.stem.replace("-", " ").title()
        parts.append(f"# {title}\n\n```\n{body}\n```\n")
    return "\n".join(parts)


def upload_doc(name: str, parent_id: str, content: str) -> dict:
    """Write content to a temp markdown file inside cwd (gws restricts to cwd) and
    upload as a Google Doc with conversion."""
    with tempfile.TemporaryDirectory(dir=".") as td:
        tmp_md = Path(td) / "upload.md"
        tmp_md.write_text(content, encoding="utf-8")
        body = {
            "name": name,
            "mimeType": "application/vnd.google-apps.document",
            "parents": [parent_id],
        }
        proc = subprocess.run(
            [
                "gws",
                "drive",
                "files",
                "create",
                "--params",
                json.dumps({"fields": "id,webViewLink,name"}),
                "--json",
                json.dumps(body),
                "--upload",
                str(tmp_md),
                "--upload-content-type",
                "text/markdown",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"upload failed (exit {proc.returncode}):\n{proc.stderr or proc.stdout}"
            )
        out = proc.stdout
        if out.startswith("Using keyring"):
            out = out.split("\n", 1)[1] if "\n" in out else ""
        return json.loads(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("topic")
    parser.add_argument("checkpoint", choices=sorted(CHECKPOINT_NAMES.keys()))
    args = parser.parse_args(argv)

    if shutil.which("gws") is None:
        print("error: `gws` CLI not found on PATH.", file=sys.stderr)
        return 2

    name = CHECKPOINT_NAMES[args.checkpoint]
    feedback_dir = Path("episodes") / args.topic / "feedback"
    feedback_dir.mkdir(parents=True, exist_ok=True)
    docs_json_path = feedback_dir / "docs.json"
    docs_map = (
        json.loads(docs_json_path.read_text(encoding="utf-8"))
        if docs_json_path.exists()
        else {}
    )

    if args.checkpoint in docs_map and docs_map[args.checkpoint]:
        print(
            f"docs.json already has entry for {args.checkpoint!r}: "
            f"{docs_map[args.checkpoint]}"
        )
        print("(skipping doc creation — delete the entry from docs.json to regenerate)")
        return 0

    content = gather_content(args.topic, args.checkpoint)

    root_id = find_or_create_folder(ROOT_FOLDER_NAME)
    print(f"root folder '{ROOT_FOLDER_NAME}': {root_id}")

    ep_folder_id = docs_map.get("folder_id")
    if ep_folder_id:
        print(f"episode folder '{args.topic}': {ep_folder_id} (cached)")
    else:
        ep_folder_id = find_or_create_folder(args.topic, parent_id=root_id)
        docs_map["folder_id"] = ep_folder_id
        print(f"episode folder '{args.topic}': {ep_folder_id} (newly cached)")

    doc_name = f"{args.checkpoint}-{name}"
    result = upload_doc(doc_name, ep_folder_id, content)
    url = result["webViewLink"]
    docs_map[args.checkpoint] = url
    docs_json_path.write_text(
        json.dumps(docs_map, indent=2) + "\n", encoding="utf-8"
    )
    print(f"created doc '{doc_name}' → {url}")
    print(f"saved to {docs_json_path}")
    if not (docs_json_path.parent / f"{args.checkpoint}-{name}-comments.md").exists():
        print(
            "\nShare the root 'Backbone Feedback' folder with Cyrus once if you "
            "haven't already — all docs inside inherit access."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
