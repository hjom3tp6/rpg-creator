#!/usr/bin/env python3
"""Manage the player-facing Codex (saves/codex.md) of discovered lore.

When the player uncovers a hidden piece of the world, the GM unlocks it
here. Unlocking is idempotent: re-unlocking the same id is a no-op and
reports newly_unlocked=false, so the GM knows whether to show the little
"📖 Codex updated" flourish.

Usage:
    python3 codex.py --unlock <id> "<player-facing title>" [--note "<text>"]
    python3 codex.py --list
    python3 codex.py [--root DIR] ...

Codex entries are stored as markdown sections keyed by a hidden id marker
so we can dedupe without parsing prose:

    <!-- codex:grey-fog -->
    ## 灰霧的真相
    （玩家已知的版本……）
"""
import argparse
import json
import os
import sys

HEADER = "# 📖 Codex — 已解鎖圖鑑\n"


def saves_dir(root: str, game) -> str:
    """Resolve the per-game saves directory (shared by all engine scripts)."""
    if not game:
        active = os.path.join(root, "games", "ACTIVE")
        if os.path.exists(active):
            with open(active, encoding="utf-8") as f:
                game = f.read().strip()
    if game:
        return os.path.join(root, "saves", game)
    return os.path.join(root, "saves")  # legacy single-game layout


def codex_path(root: str, game) -> str:
    return os.path.join(saves_dir(root, game), "codex.md")


def read_text(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as f:
        return f.read()


def marker(entry_id: str) -> str:
    return f"<!-- codex:{entry_id} -->"


def main() -> int:
    ap = argparse.ArgumentParser(description="Manage the codex.")
    ap.add_argument("--root", default=os.getcwd(), help="project root")
    ap.add_argument("--game", default=None,
                    help="cartridge id (else read from games/ACTIVE)")
    ap.add_argument("--unlock", nargs="+", metavar=("ID", "TITLE"),
                    help="unlock entry: <id> <title...>")
    ap.add_argument("--note", default="", help="optional body text for entry")
    ap.add_argument("--list", action="store_true", help="print the codex")
    args = ap.parse_args()

    path = codex_path(args.root, args.game)
    text = read_text(path)

    if args.list:
        print(text if text.strip() else "（圖鑑尚無已解鎖條目）")
        return 0

    if not args.unlock:
        ap.error("provide --unlock <id> <title> or --list")

    entry_id = args.unlock[0]
    title = " ".join(args.unlock[1:]).strip() or entry_id

    if marker(entry_id) in text:
        print(json.dumps({"newly_unlocked": False, "id": entry_id},
                         ensure_ascii=False))
        return 0

    if not text.strip():
        text = HEADER
    if not text.endswith("\n"):
        text += "\n"
    block = f"\n{marker(entry_id)}\n## {title}\n"
    if args.note:
        block += f"{args.note}\n"
    text += block

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

    print(json.dumps({"newly_unlocked": True, "id": entry_id, "title": title},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
