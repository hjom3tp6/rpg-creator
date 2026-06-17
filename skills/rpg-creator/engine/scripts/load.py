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

--root defaults to the cwd (project root). --game selects the save; if omitted
it is read from <root>/games/ACTIVE. State lives at <root>/saves/<game>/state.json.
"""
import argparse
import json
import os
import sys

# Cold fields trimmed from the --hot view (they are prose / history / static
# persona that a normal turn does not need; fetch with --key when required).
COLD_REL_FIELDS = ("notes", "suspects", "revealed")   # per-character relationship prose
COLD_DRIFT_FIELDS = ("ledger", "pending_seeds")        # drift history/queue (read on a drift check)
COLD_GOAL_FIELDS = ("mid", "long")                     # keep short goals hot; mid/long summarized
COLD_PLAYER_FIELDS = ("description", "persona_file")   # static persona (also in characters/player.md)
COLD_SPIRIT_FIELDS = ("notable_castings",)             # casting prose log


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


def _strip_comments(obj):
    """Drop noisy _comment / comment keys anywhere in the tree (hot view only)."""
    if isinstance(obj, dict):
        return {k: _strip_comments(v) for k, v in obj.items()
                if k not in ("_comment", "comment")}
    if isinstance(obj, list):
        return [_strip_comments(v) for v in obj]
    return obj


def hot_view(data: dict) -> dict:
    """Project the full state down to the volatile core needed each turn.

    Generic across cartridges: it keys off `scene.present_characters` and a few
    well-known cold field names (above). Unknown top-level keys pass through, so
    a cartridge's custom small state still shows; only known heavy prose is cut.
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
        elif key == "drift" and isinstance(val, dict):
            slim = {k: v for k, v in val.items() if k not in COLD_DRIFT_FIELDS}
            for f in COLD_DRIFT_FIELDS:
                if isinstance(val.get(f), list):
                    slim[f + "_count"] = len(val[f])
            out[key] = slim
        elif key == "goals" and isinstance(val, dict):
            slim = {k: v for k, v in val.items() if k not in COLD_GOAL_FIELDS}
            for f in COLD_GOAL_FIELDS:
                if isinstance(val.get(f), list):
                    slim[f + "_count"] = len(val[f])
            out[key] = slim
        elif key == "player" and isinstance(val, dict):
            out[key] = {k: v for k, v in val.items() if k not in COLD_PLAYER_FIELDS}
        elif key == "spirit_tongue" and isinstance(val, dict):
            slim = {k: v for k, v in val.items() if k not in COLD_SPIRIT_FIELDS}
            for f in COLD_SPIRIT_FIELDS:
                if isinstance(val.get(f), list):
                    slim[f + "_count"] = len(val[f])
            out[key] = slim
        else:
            out[key] = val
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
    ap.add_argument("--game", default=None,
                    help="cartridge id (else read from games/ACTIVE)")
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
