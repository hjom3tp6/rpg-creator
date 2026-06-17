#!/usr/bin/env python3
"""Update game state by deep-merging a JSON patch into saves/state.json.

This keeps the GM from having to hand-rewrite the whole state file every
turn (which is token-heavy and error-prone). The GM passes only what
changed; this script merges it in and stamps last_played.

Merge rules:
  - nested objects (dicts) are merged recursively
  - everything else (numbers, strings, booleans, LISTS) is replaced

So for flat maps like affinity/flags, pass just the changed keys:
    {"affinity": {"mira": 12}, "flags": {"spared_thief": true}}
For lists like inventory, pass the FULL new list (lists are replaced):
    {"inventory": ["sealed letter", "rusty key"]}

Usage:
    echo '<patch json>' | python3 save.py [--root DIR] [--game ID]
    python3 save.py [--root DIR] [--game ID] --patch '<patch json>'

--game selects which cartridge's save to write (else read from
<root>/games/ACTIVE); state lives at <root>/saves/<game>/state.json.
If it does not exist it is created from the patch (use this on New Game,
ideally seeding from the cartridge's state.seed.json first).
"""
import argparse
import datetime
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


def state_path(root: str, game) -> str:
    return os.path.join(saves_dir(root, game), "state.json")


def deep_merge(base: dict, patch: dict) -> dict:
    for key, value in patch.items():
        if (key in base and isinstance(base[key], dict)
                and isinstance(value, dict)):
            deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def main() -> int:
    ap = argparse.ArgumentParser(description="Merge a JSON patch into state.")
    ap.add_argument("--root", default=os.getcwd(), help="project root")
    ap.add_argument("--game", default=None,
                    help="cartridge id (else read from games/ACTIVE)")
    ap.add_argument("--patch", default=None,
                    help="patch JSON (otherwise read from stdin)")
    args = ap.parse_args()

    raw = args.patch if args.patch is not None else sys.stdin.read()
    try:
        patch = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(json.dumps({"_status": "error",
                          "message": f"invalid patch JSON: {exc}"},
                         ensure_ascii=False))
        return 1
    if not isinstance(patch, dict):
        print(json.dumps({"_status": "error",
                          "message": "patch must be a JSON object"},
                         ensure_ascii=False))
        return 1

    path = state_path(args.root, args.game)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    state: dict = {}
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                state = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            print(json.dumps({"_status": "error", "message": str(exc)},
                             ensure_ascii=False))
            return 1

    deep_merge(state, patch)
    state.setdefault("meta", {})
    state["meta"]["last_played"] = datetime.datetime.now().isoformat(
        timespec="seconds")

    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

    print(json.dumps({"_status": "saved", "path": path}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
