#!/usr/bin/env python3
"""Write the rehydration card and refresh the CLAUDE.md pointer.

This is the engine's "memory checkpoint". It does two cheap, deterministic
things at turn-end so that a *fresh* session (after /clear or auto-compact)
can resume the game without re-reading the whole history:

  1. Overwrites saves/<game>/recap.md with the compact recap card the GM
     passes on stdin (single source of "where are we right now").
  2. Idempotently updates a small managed block in the project-root
     CLAUDE.md so any new session in this folder auto-knows a game is in
     progress and how to resume it.

The recap card is ALWAYS overwritten (not appended) — it is a snapshot, not
a log. Keep it small (≈15-30 lines): scene, present cast, goals (short/mid/
long), open threads, ticking clocks, the last few beats, affinity at a
glance. That is all "Continue" needs to read.

Usage:
    echo '<recap markdown>' | python3 checkpoint.py --game ID --title "..."
    python3 checkpoint.py --game ID --title "..." --recap '<markdown>'

The CLAUDE.md pointer lives between these markers (everything else in the
file is left untouched):

    <!-- rpg:active-game -->
    🎮 ...
    <!-- /rpg:active-game -->
"""
import argparse
import datetime
import os
import sys

BEGIN = "<!-- rpg:active-game -->"
END = "<!-- /rpg:active-game -->"


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


def write_recap(root: str, game, body: str) -> str:
    path = os.path.join(saves_dir(root, game), "recap.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(body if body.endswith("\n") else body + "\n")
    os.replace(tmp, path)
    return path


def update_pointer(root: str, game, title, resume_cmd=None) -> str:
    """Replace (or insert) the managed block in <root>/CLAUDE.md.

    resume_cmd is the slash command that resumes this game (e.g. "/spirit-tongue"
    for a baked game skill). Defaults to "/rpg" for the legacy generic engine.
    """
    path = os.path.join(root, "CLAUDE.md")
    label = title or game or "(unknown)"
    gid = game or "?"
    cmd = resume_cmd or "/rpg"
    stamp = datetime.datetime.now().isoformat(timespec="minutes")
    block = (
        f"{BEGIN}\n"
        f"🎮 RPG 進行中：**{label}**（`{gid}`，更新 {stamp}）。\n"
        f"輸入 `{cmd}` 即可從 `saves/{gid}/recap.md` 立即接續這局。\n"
        f"{END}"
    )

    text = ""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            text = f.read()

    if BEGIN in text and END in text:
        pre = text[: text.index(BEGIN)]
        post = text[text.index(END) + len(END):]
        new = pre + block + post
    else:
        sep = "" if (text == "" or text.endswith("\n\n")) else (
            "\n" if text.endswith("\n") else "\n\n")
        new = text + sep + block + "\n"

    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(new)
    os.replace(tmp, path)
    return path


def clear_pointer(root: str) -> str:
    """Remove the managed block (e.g. on world-switch or game end)."""
    path = os.path.join(root, "CLAUDE.md")
    if not os.path.exists(path):
        return path
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if BEGIN in text and END in text:
        pre = text[: text.index(BEGIN)].rstrip("\n")
        post = text[text.index(END) + len(END):].lstrip("\n")
        new = (pre + "\n\n" + post).strip("\n")
        new = new + "\n" if new else ""
        with open(path, "w", encoding="utf-8") as f:
            f.write(new)
    return path


def main() -> int:
    ap = argparse.ArgumentParser(description="Write recap + CLAUDE.md pointer.")
    ap.add_argument("--root", default=os.getcwd(), help="project root")
    ap.add_argument("--game", default=None,
                    help="cartridge id (else read from games/ACTIVE)")
    ap.add_argument("--title", default=None, help="player-facing game title")
    ap.add_argument("--resume-cmd", default=None,
                    help="slash command that resumes this game (e.g. /spirit-tongue)")
    ap.add_argument("--recap", default=None,
                    help="recap markdown (otherwise read from stdin)")
    ap.add_argument("--clear-pointer", action="store_true",
                    help="remove the CLAUDE.md block instead of writing")
    args = ap.parse_args()

    import json
    if args.clear_pointer:
        p = clear_pointer(args.root)
        print(json.dumps({"_status": "pointer_cleared", "claude_md": p},
                         ensure_ascii=False))
        return 0

    body = args.recap if args.recap is not None else sys.stdin.read()
    if not body.strip():
        print(json.dumps({"_status": "error", "message": "empty recap"},
                         ensure_ascii=False))
        return 1

    recap = write_recap(args.root, args.game, body)
    pointer = update_pointer(args.root, args.game, args.title, args.resume_cmd)
    print(json.dumps({"_status": "checkpointed", "recap": recap,
                      "claude_md": pointer}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
