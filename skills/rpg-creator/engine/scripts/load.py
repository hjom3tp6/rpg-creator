#!/usr/bin/env python3
"""Load the current game state.

Prints saves/<game>/state.json so the GM can read the current scene, affinity,
flags, clock, etc. If no save exists, prints {"_status": "no_save"} so the GM
knows to start a New Game.

Three read modes:
    python3 load.py --game ID            # FULL state (single source of truth)
    python3 load.py --game ID --hot      # HOT view: only the volatile core the
                                         # GM needs EACH turn — small & cheap.
    python3 load.py --game ID --key PATH # one field on demand, e.g.
                                         # --key relationships.sera.notes
                                         # --key drift.ledger

Why --hot: the full state grows every turn (long relationship notes, the drift
ledger, accumulating flags, cast prose). Re-reading ALL of it every turn is the
main data-layer token cost. --hot drops the COLD prose/history and keeps only
what a normal turn acts on, projecting `relationships` down to the characters
who are actually on stage (scene.present_characters). Read the FULL state (or a
single --key) only when you need a cold field — an OOC `[god]` inspect query, a
drift check that needs the ledger, etc. The file on disk is unchanged; this only trims what
you READ. (Fix A — the hot/cold read split.)

--root defaults to the cwd (project root). --game (required) selects the save; state lives at
<root>/saves/<game>/state.json.

Cold fields: built-in defaults cover the standard blocks (relationship notes/suspects/revealed,
drift ledger/pending_seeds, goals mid/long, player description/persona_file). A game can declare
extra cold fields with an optional top-level `_cold` list of dotted paths in its state, e.g.
["red_tape.history", "casting.history"]; the hot view drops them (lists are
replaced by `<field>_count`).
"""
import argparse
import copy
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import saves_dir  # noqa: E402

# Cold fields trimmed from the --hot view (prose / history / static persona a normal turn does not
# need; fetch with --key when required). Per-character relationship prose is trimmed inside the
# present-characters projection; everything else is a dotted path, like a game's own `_cold` list.
COLD_REL_FIELDS = ("notes", "suspects", "revealed")
DEFAULT_COLD = ("drift.ledger", "drift.pending_seeds",   # drift history/queue (read on a drift check)
                "goals.mid", "goals.long",               # short goals stay hot
                "player.description", "player.persona_file")  # static persona (also characters/player.md)


def state_path(root: str, game: str) -> str:
    return os.path.join(saves_dir(root, game), "state.json")


def _strip_comments(obj):
    """Drop noisy _comment / comment keys anywhere in the tree (hot view only)."""
    if isinstance(obj, dict):
        return {k: _strip_comments(v) for k, v in obj.items()
                if k not in ("_comment", "comment")}
    if isinstance(obj, list):
        return [_strip_comments(v) for v in obj]
    return obj


def _drop_path(out: dict, dotpath: str) -> None:
    """Remove a dotted path from the (already copied) hot view; lists leave `<field>_count`."""
    parts = dotpath.split(".")
    cur = out
    for p in parts[:-1]:
        cur = cur.get(p) if isinstance(cur, dict) else None
        if cur is None:
            return
    if not isinstance(cur, dict) or parts[-1] not in cur:
        return
    val = cur.pop(parts[-1])
    if isinstance(val, list):
        cur[parts[-1] + "_count"] = len(val)


def hot_view(data: dict) -> dict:
    """Project the full state down to the volatile core needed each turn.

    Generic across games: `relationships` is projected to scene.present_characters (cold prose
    fields dropped), DEFAULT_COLD paths are dropped, and so are the dotted paths in the state's
    optional top-level `_cold` list. Everything else passes through unchanged.
    """
    present = set((data.get("scene") or {}).get("present_characters") or [])
    out = {"_view": "hot",
           "_note": "Volatile core only. For a cold field use load.py --key PATH, or read full state."}

    for key, val in data.items():
        if key == "relationships" and isinstance(val, dict):
            slim = {}
            for cid, rel in val.items():
                if cid not in present:
                    continue  # absent characters' relationship data is cold
                if isinstance(rel, dict):
                    slim[cid] = {k: v for k, v in rel.items() if k not in COLD_REL_FIELDS}
                else:
                    slim[cid] = rel
            out[key] = slim
            absent = [c for c in val if c not in present]
            if absent:
                out["_relationships_offstage"] = absent  # names only; --key to load one
        else:
            out[key] = val

    out = copy.deepcopy(out)
    declared = data.get("_cold")
    extra = [p for p in declared if isinstance(p, str) and p] if isinstance(declared, list) else []
    for path in (*DEFAULT_COLD, *extra):
        _drop_path(out, path)
    return _strip_comments(out)


def get_key(data, dotpath: str):
    cur = data
    for part in dotpath.split("."):
        if isinstance(cur, list):
            try:
                cur = cur[int(part)]
            except (ValueError, IndexError):
                return None
        elif isinstance(cur, dict):
            if part not in cur:
                return None
            cur = cur[part]
        else:
            return None
    return cur


def main() -> int:
    ap = argparse.ArgumentParser(description="Load game state.")
    ap.add_argument("--root", default=os.getcwd(), help="project root")
    ap.add_argument("--game", required=True, help="game id (the baked skill id)")
    ap.add_argument("--hot", action="store_true",
                    help="print only the volatile per-turn core (cheap)")
    ap.add_argument("--key", default=None,
                    help="print one nested field on demand, e.g. relationships.sera.notes")
    args = ap.parse_args()

    path = state_path(args.root, args.game)
    if not os.path.exists(path):
        print(json.dumps({"_status": "no_save"}, ensure_ascii=False))
        return 0

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        print(json.dumps({"_status": "error", "message": str(exc)},
                         ensure_ascii=False))
        return 1

    if args.key:
        print(json.dumps({"_key": args.key, "value": get_key(data, args.key)},
                         ensure_ascii=False, indent=2))
    elif args.hot:
        print(json.dumps(hot_view(data), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
