#!/usr/bin/env python3
"""Manage the player-facing Codex (saves/<game>/codex.md) of discovered lore.

When the player uncovers a hidden piece of the world, the GM unlocks it
here. Unlocking is idempotent: re-unlocking the same id is a no-op and
reports newly_unlocked=false, so the GM knows whether to show the little
"📖 Codex updated" flourish.

Usage:
    python3 codex.py --game ID --unlock <id> "<player-facing title>" [--note "<text>"]
    python3 codex.py --game ID --list
    (--root DIR optional; the codex lives at <root>/saves/<game>/codex.md)

Codex entries are stored as markdown sections keyed by a hidden id marker
so we can dedupe without parsing prose:

    <!-- codex:grey-fog -->
    ## The Grey Fog
    (the version the player knows...)
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import atomic_write, read_text, saves_dir  # noqa: E402

HEADER = "# 📖 Codex\n"


def codex_path(root: str, game) -> str:
    return os.path.join(saves_dir(root, game), "codex.md")


def marker(entry_id: str) -> str:
    return f"<!-- codex:{entry_id} -->"


def unlock(root: str, game, entry_id: str, title: str = "",
           note: str = "") -> bool:
    """Idempotently unlock an entry. Returns True if newly unlocked."""
    path = codex_path(root, game)
    text = read_text(path)
    if marker(entry_id) in text:
        return False
    title = (title or "").strip() or entry_id
    if not text.strip():
        text = HEADER
    if not text.endswith("\n"):
        text += "\n"
    text += f"\n{marker(entry_id)}\n## {title}\n"
    if note:
        text += f"{note}\n"
    atomic_write(path, text)
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="Manage the codex.")
    ap.add_argument("--root", default=os.getcwd(), help="project root")
    ap.add_argument("--game", required=True, help="game id (the baked skill id)")
    ap.add_argument("--unlock", nargs="+", metavar=("ID", "TITLE"),
                    help="unlock entry: <id> <title...>")
    ap.add_argument("--note", default="", help="optional body text for entry")
    ap.add_argument("--list", action="store_true", help="print the codex")
    args = ap.parse_args()

    path = codex_path(args.root, args.game)
    text = read_text(path)

    if args.list:
        print(text if text.strip() else "(No codex entries unlocked yet.)")
        return 0

    if not args.unlock:
        ap.error("provide --unlock <id> <title> or --list")

    entry_id = args.unlock[0]
    title = " ".join(args.unlock[1:]).strip() or entry_id

    if not unlock(args.root, args.game, entry_id, title, args.note):
        print(json.dumps({"newly_unlocked": False, "id": entry_id},
                         ensure_ascii=False))
        return 0

    print(json.dumps({"newly_unlocked": True, "id": entry_id, "title": title},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
