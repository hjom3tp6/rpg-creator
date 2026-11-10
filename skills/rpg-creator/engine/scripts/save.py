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
    echo '<patch json>' | python3 save.py --game ID [--root DIR]
    python3 save.py --game ID [--root DIR] --patch '<patch json>'

--game (required) selects the game's save; state lives at <root>/saves/<game>/state.json.
If it does not exist it is created from the patch.

New Game (no patch round-trip through the model):
    python3 save.py --game ID --init --set player.name=Rowan [--set k.sub=v ...]
  --init copies the game's state.seed.json (default: <this script>/../../state.seed.json,
  i.e. the bundled engine's parent dir; override with --seed PATH) to state.json and stamps
  meta.created / meta.last_played. Refuses with {"_status":"exists"} (exit 1) if a state.json
  already exists unless --force.
  --set KEY=VALUE (repeatable, dotted path) is applied after init or after a patch merge;
  VALUE is parsed as JSON when valid, else kept as a string. With --init or --set, stdin
  is NOT read (no patch needed).
"""
import argparse
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import atomic_write, saves_dir  # noqa: E402


def state_path(root: str, game: str) -> str:
    return os.path.join(saves_dir(root, game), "state.json")


def deep_merge(base: dict, patch: dict) -> dict:
    for key, value in patch.items():
        if (key in base and isinstance(base[key], dict)
                and isinstance(value, dict)):
            deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def parse_set(items):
    """['a.b=1', 'name=Rowan'] -> [(['a','b'], 1), (['name'], 'Rowan')]; raises ValueError."""
    out = []
    for item in items or []:
        key, sep, val = item.partition("=")
        key = key.strip()
        if not sep or not key or not all(key.split(".")):
            raise ValueError(f"--set needs KEY=VALUE with a dotted key, got {item!r}")
        try:
            val = json.loads(val)
        except json.JSONDecodeError:
            pass
        out.append((key.split("."), val))
    return out


def apply_sets(state: dict, sets) -> None:
    for parts, val in sets:
        cur = state
        for p in parts[:-1]:
            if not isinstance(cur.get(p), dict):
                cur[p] = {}
            cur = cur[p]
        cur[parts[-1]] = val


def write_atomic(path: str, state: dict) -> None:
    atomic_write(path, json.dumps(state, ensure_ascii=False, indent=2))


def err(message, status="error") -> int:
    print(json.dumps({"_status": status, "message": message}, ensure_ascii=False))
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Merge a JSON patch into state.")
    ap.add_argument("--root", default=os.getcwd(), help="project root")
    ap.add_argument("--game", required=True, help="game id (the baked skill id)")
    ap.add_argument("--patch", default=None,
                    help="patch JSON (otherwise read from stdin)")
    ap.add_argument("--init", action="store_true",
                    help="New Game: copy the seed to state.json (no patch/stdin needed)")
    ap.add_argument("--seed", default=None,
                    help="seed path for --init (default: <game>/state.seed.json next to engine/)")
    ap.add_argument("--force", action="store_true",
                    help="with --init: overwrite an existing state.json")
    ap.add_argument("--set", dest="sets", action="append", default=[], metavar="KEY=VALUE",
                    help="set a dotted-path value (repeatable); JSON-parsed if valid, else string")
    args = ap.parse_args()

    try:
        sets = parse_set(args.sets)
    except ValueError as exc:
        return err(str(exc))
    now = datetime.datetime.now().isoformat(timespec="seconds")

    if args.init:
        path = state_path(args.root, args.game)
        if os.path.exists(path) and not args.force:
            return err(f"state.json already exists: {path} (use --force to overwrite)",
                       "exists")
        seed_path = args.seed or os.path.normpath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "..", "state.seed.json"))
        try:
            with open(seed_path, encoding="utf-8") as f:
                state = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            return err(f"cannot read seed {seed_path}: {exc}")
        if not isinstance(state, dict):
            return err(f"seed {seed_path} must be a JSON object")
        if not isinstance(state.get("meta"), dict):
            state["meta"] = {}
        state["meta"]["created"] = now
        apply_sets(state, sets)
        state["meta"]["last_played"] = now
        os.makedirs(os.path.dirname(path), exist_ok=True)
        write_atomic(path, state)
        print(json.dumps({"_status": "initialized", "path": path,
                          "seed": seed_path, "set": [".".join(p) for p, _ in sets]},
                         ensure_ascii=False))
        return 0

    if args.patch is not None:
        raw = args.patch
    elif sets:
        raw = "{}"  # --set only: no stdin read
    else:
        raw = sys.stdin.read()
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
    apply_sets(state, sets)
    state.setdefault("meta", {})
    state["meta"]["last_played"] = now
    write_atomic(path, state)

    print(json.dumps({"_status": "saved", "path": path}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
