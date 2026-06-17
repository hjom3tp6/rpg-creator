#!/usr/bin/env python3
"""Keep saves/session-log.md from growing without bound.

The session log holds the recent turns verbatim (a rolling window). When
it gets long, the GM should summarize the oldest part into journal.md
(long-term memory) and drop it from the log. This script handles the
deterministic part: deciding WHEN to rotate and WHICH lines to trim.

The actual summarizing is the GM's job (it needs judgment), so the flow is:

  1. python3 rotate_log.py --check
       -> {"needs_rotation": true, "total_lines": 320, "trim_lines": 200,
           "oldest_block": "...first 200 lines..."}
     If needs_rotation is false, do nothing.

  2. GM reads oldest_block, writes a concise summary into saves/journal.md

  3. python3 rotate_log.py --trim 200
       -> removes the first 200 lines from session-log.md

Usage:
    python3 rotate_log.py --check [--root DIR] [--threshold N] [--keep N]
    python3 rotate_log.py --trim N [--root DIR]

Defaults: rotate when the log exceeds --threshold lines (default 250),
keeping the most recent --keep lines (default 120).
"""
import argparse
import json
import os
import sys


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


def log_path(root: str, game) -> str:
    return os.path.join(saves_dir(root, game), "session-log.md")


def read_lines(path: str):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return f.readlines()


def main() -> int:
    ap = argparse.ArgumentParser(description="Rotate the session log.")
    ap.add_argument("--root", default=os.getcwd(), help="project root")
    ap.add_argument("--game", default=None,
                    help="cartridge id (else read from games/ACTIVE)")
    ap.add_argument("--check", action="store_true",
                    help="report whether rotation is needed")
    ap.add_argument("--trim", type=int, default=None,
                    help="remove the first N lines from the log")
    ap.add_argument("--threshold", type=int, default=250,
                    help="rotate when log exceeds this many lines")
    ap.add_argument("--keep", type=int, default=120,
                    help="how many recent lines to keep")
    args = ap.parse_args()

    path = log_path(args.root, args.game)
    lines = read_lines(path)

    if args.trim is not None:
        n = max(0, args.trim)
        remaining = lines[n:]
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(remaining)
        print(json.dumps({"_status": "trimmed", "removed": min(n, len(lines)),
                          "remaining_lines": len(remaining)},
                         ensure_ascii=False))
        return 0

    # default / --check
    total = len(lines)
    needs = total > args.threshold
    result = {"needs_rotation": needs, "total_lines": total}
    if needs:
        trim_lines = total - args.keep
        result["trim_lines"] = trim_lines
        result["oldest_block"] = "".join(lines[:trim_lines])
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
