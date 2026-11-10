#!/usr/bin/env python3
"""One-call turn-end: save state + unlock lore + log the beat + render recap.

Replaces the old 5-6 call turn-end (save.py, codex.py, checkpoint.py, hand
appending session-log.md, rotate_log.py --check). The recap card is RENDERED
HERE from the merged state, not hand-written by the GM.

Usage:
    echo '<json>' | python3 turn.py --game ID --title "Title" --resume-cmd /ID
    python3 turn.py --game ID --title "Title" --resume-cmd /ID --input '<json>'

Input JSON (all keys optional, but at least one of patch/beat is required):
    {
      "patch":   { ...deep-merge patch, same semantics as save.py... },
      "beat":    "1-3 short lines: what just happened this turn",
      "unlock":  [ {"id": "lore-id", "title": "player-facing", "note": ""} ],
      "threads": ["open threads / hooks to carry in the recap"]
    }

Output: one compact JSON line, e.g.
    {"_status":"ok","newly_unlocked":["x"],"log_lines":42,"needs_rotation":false}
When needs_rotation is true it also carries trim_lines and oldest_block: the
GM summarizes oldest_block into journal.md, then runs
    rotate_log.py --game ID --trim <trim_lines>

Requires saves/ID/state.json to exist already (New Game seeds it first).
"""
import argparse
import datetime
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import checkpoint  # noqa: E402
import codex  # noqa: E402
import rotate_log  # noqa: E402
import save  # noqa: E402
from _common import atomic_write  # noqa: E402

KNOWN_KEYS = {
    "meta", "player", "scene", "clock", "goals", "director", "coaching",
    "affinity", "relationships", "flags", "inventory", "party", "threads",
    "drift",
}
RECENT_BEATS = 5
MODULE_MAX_JSON = 300


def emit(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))


def _s(v) -> str:
    """Compact one-line string for any value."""
    if v is None:
        return ""
    if isinstance(v, str):
        return " ".join(v.split())
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False, separators=(",", ":"))
    return str(v)


def _items(v) -> list:
    if v is None or v == "":
        return []
    if isinstance(v, (list, tuple)):
        return list(v)
    return [v]


def _name(v) -> str:
    if isinstance(v, dict):
        return _s(v.get("name") or v.get("id") or v)
    return _s(v)


def _dict(v) -> dict:
    return v if isinstance(v, dict) else {}


# ---------------------------------------------------------------- log
def context_header(state: dict) -> str:
    clock = _dict(state.get("clock"))
    scene = _dict(state.get("scene"))
    parts = []
    if clock.get("day") not in (None, ""):
        parts.append(f"Day {_s(clock['day'])}")
    if clock.get("phase"):
        parts.append(_s(clock["phase"]))
    if scene.get("location"):
        parts.append(_s(scene["location"]))
    return "### " + " · ".join(parts if parts else ["Turn"])


def append_beat(log_path: str, header: str, beat: str) -> None:
    text = ""
    if os.path.exists(log_path):
        with open(log_path, encoding="utf-8") as f:
            text = f.read()
    if text and not text.endswith("\n"):
        text += "\n"
    sep = "\n" if text else ""
    atomic_write(log_path, f"{text}{sep}{header}\n{beat.strip()}\n")


def recent_beats(log_path: str, n: int = RECENT_BEATS) -> list:
    if not os.path.exists(log_path):
        return []
    with open(log_path, encoding="utf-8") as f:
        text = f.read()
    blocks = re.split(r"(?m)^(?=### )", text)
    blocks = [b.strip() for b in blocks if b.strip().startswith("### ")]
    return blocks[-n:]


# ---------------------------------------------------------------- recap
def render_recap(state: dict, title: str, beats: list) -> str:
    out = [f"# {title} — recap"]
    scene = _dict(state.get("scene"))
    clock = _dict(state.get("clock"))
    when = " · ".join(x for x in (
        f"Day {_s(clock['day'])}" if clock.get("day") not in (None, "") else "",
        _s(clock.get("phase"))) if x)
    where = _s(scene.get("location"))
    head = " — ".join(x for x in (where, when) if x)
    if head:
        out.append(f"**Scene:** 📍 {head}")
    if scene.get("summary"):
        out.append(_s(scene["summary"]))

    # present cast with affinity / relationship stage
    aff = state.get("affinity")
    rels = _dict(state.get("relationships"))
    present = _items(scene.get("present_characters"))
    cast = []
    for c in present:
        cid = _name(c)
        bits = []
        a = aff.get(cid) if isinstance(aff, dict) else None
        if isinstance(a, dict):
            a = a.get("value", a.get("score", a))
        if a not in (None, ""):
            bits.append(f"affinity {_s(a)}")
        r = rels.get(cid)
        stage = r.get("stage") if isinstance(r, dict) else (
            r if isinstance(r, (str, int, float)) else None)
        if stage not in (None, ""):
            bits.append(f"stage {_s(stage)}")
        cast.append(cid + (f" ({', '.join(bits)})" if bits else ""))
    if cast:
        out.append("**Present:** " + "; ".join(cast))

    goals = state.get("goals")
    if isinstance(goals, dict):
        for k in ("short", "mid", "long"):
            g = [_s(x) for x in _items(goals.get(k)) if _s(x)]
            if g:
                out.append(f"**Goal ({k}):** " + " | ".join(g))

    dl = [_s(x) for x in _items(clock.get("deadlines")) if _s(x)]
    if dl:
        out.append("**Deadlines:** " + " | ".join(dl))

    threads = [_s(x) for x in _items(state.get("threads")) if _s(x)]
    if threads:
        out.append("**Open threads:**")
        out.extend(f"- {t}" for t in threads)

    flags = state.get("flags")
    if isinstance(flags, dict):
        n = len([k for k in flags if not k.startswith("_") and k != "comment"])
        if n:
            out.append(f"**Flags set:** {n}")

    for k, v in state.items():
        if k in KNOWN_KEYS or k.startswith("_") or k in ("comment",):
            continue
        if isinstance(v, dict):
            v = {a: b for a, b in v.items()
                 if a not in ("_comment", "comment")}
            js = json.dumps(v, ensure_ascii=False, separators=(",", ":"))
            if v and len(js) < MODULE_MAX_JSON:
                out.append(f"**Module {k}:** {js}")

    if beats:
        out.append("")
        out.append("## Recent beats")
        out.extend(beats)
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description="One-call turn-end.")
    ap.add_argument("--root", default=os.getcwd(), help="project root")
    ap.add_argument("--game", required=True, help="game id (the baked skill id)")
    ap.add_argument("--title", default=None, help="player-facing game title")
    ap.add_argument("--resume-cmd", default=None,
                    help="slash command that resumes this game (e.g. /demo)")
    ap.add_argument("--input", default=None,
                    help="turn JSON (otherwise read from stdin)")
    ap.add_argument("--threshold", type=int, default=250)
    ap.add_argument("--keep", type=int, default=120)
    args = ap.parse_args()

    def fail(msg, status="error"):
        emit({"_status": status, "message": msg})
        return 1

    spath = save.state_path(args.root, args.game)
    if not os.path.exists(spath):
        return fail("no save; seed state.json first (New Game)", "no_save")

    raw = args.input if args.input is not None else sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return fail(f"invalid input JSON: {exc}")
    if not isinstance(data, dict):
        return fail("input must be a JSON object")
    patch = data.get("patch")
    beat = data.get("beat")
    if patch is not None and not isinstance(patch, dict):
        return fail("patch must be a JSON object")
    if not patch and not (isinstance(beat, str) and beat.strip()):
        return fail("provide at least one of patch / beat")

    try:
        with open(spath, encoding="utf-8") as f:
            state = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        return fail(str(exc))
    if not isinstance(state, dict):
        return fail("state.json is not a JSON object")

    # 2. state
    if patch:
        save.deep_merge(state, patch)
    if data.get("threads") is not None:
        state["threads"] = [_s(t) for t in _items(data["threads"])]
    if not isinstance(state.get("meta"), dict):
        state["meta"] = {}
    state["meta"]["last_played"] = datetime.datetime.now().isoformat(
        timespec="seconds")
    atomic_write(spath, json.dumps(state, ensure_ascii=False, indent=2))

    # 3. codex
    newly = []
    for u in _items(data.get("unlock")):
        if isinstance(u, str):
            u = {"id": u}
        if not isinstance(u, dict) or not u.get("id"):
            continue
        uid = _s(u["id"])
        if codex.unlock(args.root, args.game, uid, _s(u.get("title")),
                        u.get("note") or ""):
            newly.append(uid)

    # 4. session log
    log = rotate_log.log_path(args.root, args.game)
    if isinstance(beat, str) and beat.strip():
        append_beat(log, context_header(state), beat)

    # 5. recap
    title = args.title or _s(_dict(state.get("meta")).get("game_title")) \
        or args.game
    atomic_write(os.path.join(os.path.dirname(spath), "recap.md"),
                 render_recap(state, title, recent_beats(log)))

    # 6. CLAUDE.md pointer (only written when it changed)
    checkpoint.sync_pointer(args.root, args.game, title, args.resume_cmd)

    # 7. rotation
    rot = rotate_log.check(args.root, args.game, args.threshold, args.keep)
    result = {"_status": "ok", "newly_unlocked": newly,
              "log_lines": rot["total_lines"],
              "needs_rotation": rot["needs_rotation"]}
    if rot["needs_rotation"]:
        result["trim_lines"] = rot["trim_lines"]
        result["oldest_block"] = rot["oldest_block"]
    emit(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
