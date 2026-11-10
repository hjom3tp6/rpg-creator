#!/usr/bin/env python3
"""Keep saves/<game>/session-log.md from growing without bound.

The session log holds the recent turns verbatim (a rolling window). When
it gets long, the GM should summarize the oldest part into journal.md
(long-term memory) and drop it from the log. This script handles the
deterministic part: deciding WHEN to rotate and WHICH lines to trim.

The actual summarizing is the GM's job (it needs judgment), so the flow is:

  1. python3 rotate_log.py --game ID --check
       -> {"needs_rotation": true, "total_lines": 320, "trim_lines": 200,
           "oldest_block": "...first 200 lines..."}
     If needs_rotation is false, do nothing.

  2. GM reads oldest_block, writes a concise summary into saves/<game>/journal.md

  3. python3 rotate_log.py --game ID --trim 200
       -> removes the first 200 lines from session-log.md

Usage:
    python3 rotate_log.py --game ID --check [--root DIR] [--threshold N] [--keep N]
    python3 rotate_log.py --game ID --trim N [--root DIR]

Defaults: rotate when the log exceeds --threshold lines (default 250),
keeping the most recent --keep lines (default 120).
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import saves_dir  # noqa: E402


def log_path(root: str, game) -> str:
    return os.path.join(saves_dir(root, game), "session-log.md")


def read_lines(path: str):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return f.readlines()


def check(root: str, game, threshold: int = 250, keep: int = 120) -> dict:
    """Report whether the log needs rotation (same result as --check)."""
    lines = read_lines(log_path(root, game))
    total = len(lines)
    result = {"needs_rotation": total > threshold, "total_lines": total}
    if result["needs_rotation"]:
        trim_lines = total - keep
        # Snap back to the nearest beat header so a "### " block is never cut in half
        # (keeps a few extra lines; falls back to the plain cut if there is no header).
        for i in range(trim_lines, 0, -1):
            if lines[i].startswith("### "):
                trim_lines = i
                break
        result["trim_lines"] = trim_lines
        result["oldest_block"] = "".join(lines[:trim_lines])
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="Rotate the session log.")
    ap.add_argument("--root", default=os.getcwd(), help="project root")
    ap.add_argument("--game", required=True, help="game id (the baked skill id)")
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
    print(json.dumps(check(args.root, args.game, args.threshold, args.keep),
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
