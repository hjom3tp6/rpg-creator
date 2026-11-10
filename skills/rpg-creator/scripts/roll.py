#!/usr/bin/env python3
"""Roll design-variation combos for a NEW game — the randomness lever of design.md §1.

Asked to "be original", an LLM converges on the same few choices every time. A script's randomness
is real, so the interview starts from rolled combos instead: one value per design axis (structure,
opposition, ending, protagonist, tone, setting, a drive palette, central relationship, scale, a
wildcard twist), drawn from assets/variation-tables.json.

    python3 "$SKILL/scripts/roll.py" --count 3
    python3 "$SKILL/scripts/roll.py" --count 3 --seed 7 --lock setting=high-fantasy --lock tone=wry-comedic

  --lock axis=value   honour what the user already asked for (repeatable). A value that is not a
                      table id is kept verbatim as a custom value (except `structure`, which must name
                      a story-structures/ file). `--lock cast_pattern=<p>` overrides the pattern the
                      structure file defines.
  --seed N            reproducible roll (the seed used is always echoed back).
  --count N           N alternative combos; within one batch the high-impact axes don't repeat
                      (while values remain) and repeats on other axes are down-weighted.
  --avoid-recent      (default on; --no-avoid-recent to disable) scan
                      <root>/.claude/skills/*/story/main-arc.md for a `## Design DNA` block and skip
                      values existing games already used on the high-impact axes (structure,
                      opposition, ending, setting) — unless that would leave an axis empty.

Pairs listed under `incompatible` in the tables are never returned together (candidates that would
clash with an already-chosen value are filtered out before drawing). cast_pattern is not rolled: it
comes from the chosen story-structures/<structure>.md `cast_pattern:` line.

Output: compact JSON — combos (axis -> value id; `drives` is a list), a glossary for the terser
axes (structure, opposition, ending, twist; the rest read fine bare),
what was avoided and why, and warnings. Stdlib only. Run from the project root (or pass --root).
"""
import argparse
import glob
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TABLES = os.path.normpath(os.path.join(HERE, "..", "assets", "variation-tables.json"))
STRUCTURES = os.path.normpath(os.path.join(HERE, "..", "story-structures"))
CAST_PATTERNS = ("rotating", "fixed-party", "solo", "revolving")
CAST_RE = re.compile(r"^cast_pattern:\s*([a-z-]+)\s*$", re.MULTILINE)
DNA_LINE_RE = re.compile(r"^\s*[-*]\s*([A-Za-z_][\w -]*?)\s*:\s*(.+?)\s*$")
BATCH_REPEAT_WEIGHT = 0.15
# Ids on these axes are terse; the others read fine bare (full text: assets/variation-tables.json).
GLOSSARY_AXES = ("structure", "opposition", "ending", "twist")


def emit(obj):
    print(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))


def read_text(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def structure_names():
    if not os.path.isdir(STRUCTURES):
        return []
    return sorted(fn[:-3] for fn in os.listdir(STRUCTURES)
                  if fn.endswith(".md") and fn.lower() != "readme.md")


def structure_cast_pattern(name):
    text = read_text(os.path.join(STRUCTURES, name + ".md"))
    m = CAST_RE.search(text or "")
    return m.group(1) if m and m.group(1) in CAST_PATTERNS else None


def parse_dna(text):
    """`- axis: value` lines under `## Design DNA` -> {axis: value}; {{placeholders}} skipped."""
    dna, inside = {}, False
    for line in (text or "").splitlines():
        if line.startswith("## "):
            if inside:
                break
            inside = "design dna" in line.lower()
            continue
        if not inside:
            continue
        m = DNA_LINE_RE.match(line)
        if m and "{{" not in m.group(2):
            dna[m.group(1).strip().lower().replace(" ", "_").replace("-", "_")] = m.group(2)
    return dna


def match_id(value, ids):
    """Map a free-form value to a table id: exact id, or an id followed by a non-slug char."""
    norm = re.sub(r"\s+", "-", value.strip().lower())
    for vid in ids:
        if re.match(re.escape(vid) + r"(?![a-z0-9])", norm):
            return vid
    return None


def scan_recent(root, tables):
    """{axis: {id: [game ids]}} for high-impact axes, from existing games' Design DNA blocks."""
    used, games = {}, []
    pattern = os.path.join(root, ".claude", "skills", "*", "story", "main-arc.md")
    for path in sorted(glob.glob(pattern)):
        gid = os.path.basename(os.path.dirname(os.path.dirname(path)))
        dna = parse_dna(read_text(path))
        if not dna:
            continue
        games.append(gid)
        for axis in tables.get("high_impact", []):
            raw = dna.get(axis)
            ids = list(tables["axes"].get(axis, {}).get("values", {}))
            vid = match_id(raw, ids) if raw else None
            if vid:
                used.setdefault(axis, {}).setdefault(vid, []).append(gid)
    return used, games


def parse_locks(raw_locks, tables):
    """['axis=value', ...] -> ({axis: [values]}, cast_pattern_override, custom, error)."""
    locks, custom, cast_override = {}, [], None
    for raw in raw_locks or []:
        if "=" not in raw:
            return None, None, None, "--lock must be axis=value, got %r" % raw
        axis, value = (s.strip() for s in raw.split("=", 1))
        axis = axis.lower().replace("-", "_")
        if not value:
            return None, None, None, "--lock %s has an empty value" % axis
        if axis == "cast_pattern":
            if value not in CAST_PATTERNS:
                return None, None, None, "cast_pattern must be one of %s" % ", ".join(CAST_PATTERNS)
            cast_override = value
            continue
        if axis not in tables["axes"]:
            return None, None, None, "unknown axis %r (axes: %s, cast_pattern)" % (
                axis, ", ".join(tables["axes"]))
        ids = list(tables["axes"][axis]["values"])
        vid = match_id(value, ids)
        if vid is None:
            if axis == "structure":
                return None, None, None, "unknown structure %r (have: %s)" % (
                    value, ", ".join(ids))
            vid = value
            custom.append("%s=%s" % (axis, value))
        spec_pick = tables["axes"][axis].get("pick", 1)
        if spec_pick == 1 and axis in locks and locks[axis] != [vid]:
            return None, None, None, "axis %r takes one value; locked twice" % axis
        locks.setdefault(axis, [])
        if vid not in locks[axis]:
            locks[axis].append(vid)
    return locks, cast_override, custom, None


def incompatible_set(tables):
    return {frozenset(pair) for pair in tables.get("incompatible", []) if len(pair) == 2}


def clashes(axis, vid, chosen, bad):
    me = "%s=%s" % (axis, vid)
    for other_axis, vals in chosen.items():
        if other_axis == axis:
            continue
        for v in (vals if isinstance(vals, list) else [vals]):
            if frozenset((me, "%s=%s" % (other_axis, v))) in bad:
                return True
    return False


def roll_one(tables, rng, locks, avoid, batch_used, bad, warnings):
    axes = tables["axes"]
    high_impact = set(tables.get("high_impact", []))
    order = list(locks) + ["structure"] + [a for a in axes if a != "structure"]
    chosen = {}
    for axis in order:
        if axis in chosen or axis not in axes:
            continue
        spec = axes[axis]
        k = spec.get("pick", 1)
        picks = list(locks.get(axis, []))
        if axis in locks and len(picks) >= k:
            chosen[axis] = picks if k > 1 else picks[0]
            continue
        ids = list(spec["values"])
        while len(picks) < k:
            free = [v for v in ids if v not in picks]
            ok = [v for v in free if not clashes(axis, v, chosen, bad)]
            if not ok:
                warnings.append("%s: every value clashes with a locked value; drew one anyway" % axis)
                ok = free
            fresh = [v for v in ok if v not in avoid.get(axis, {})]
            if not fresh:
                if avoid.get(axis):
                    warnings.append("%s: all compatible values used by existing games; avoid "
                                    "relaxed" % axis)
                fresh = ok
            if axis in high_impact:  # alternatives in one batch differ where it matters most
                fresh = [v for v in fresh if v not in batch_used.get(axis, set())] or fresh
            weights = [BATCH_REPEAT_WEIGHT if v in batch_used.get(axis, set()) else 1.0
                       for v in fresh]
            picks.append(rng.choices(fresh, weights=weights)[0])
        chosen[axis] = picks if k > 1 else picks[0]
    for axis, vals in chosen.items():
        batch_used.setdefault(axis, set()).update(vals if isinstance(vals, list) else [vals])
    return chosen


def main():
    ap = argparse.ArgumentParser(description="Roll design-variation combos for a new game.")
    ap.add_argument("--root", default=os.getcwd(), help="project root")
    ap.add_argument("--seed", type=int, default=None, help="RNG seed (reproducible)")
    ap.add_argument("--lock", action="append", default=[], metavar="AXIS=VALUE",
                    help="fix an axis to a value the user asked for (repeatable)")
    ap.add_argument("--count", type=int, default=3, help="number of alternative combos")
    ap.add_argument("--avoid-recent", action=argparse.BooleanOptionalAction, default=True,
                    help="skip high-impact values existing games already used (default on)")
    args = ap.parse_args()

    try:
        with open(TABLES, encoding="utf-8") as f:
            tables = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        emit({"_status": "error", "message": "cannot read %s: %s" % (TABLES, exc)})
        return 1
    if args.count < 1:
        emit({"_status": "error", "message": "--count must be >= 1"})
        return 1
    locks, cast_override, custom, err = parse_locks(args.lock, tables)
    if err:
        emit({"_status": "error", "message": err})
        return 1

    warnings = []
    bad = incompatible_set(tables)
    for axis, vals in locks.items():
        for v in vals:
            if clashes(axis, v, {a: x for a, x in locks.items() if a != axis}, bad):
                warnings.append("locked %s=%s is marked incompatible with another lock; "
                                "honoured anyway" % (axis, v))

    root = os.path.abspath(args.root)
    used, games = scan_recent(root, tables) if args.avoid_recent else ({}, [])
    avoid = {a: ids for a, ids in used.items() if a not in locks}
    avoided = [{"axis": a, "value": v, "why": "used by existing game(s): " + ", ".join(g)}
               for a, ids in avoid.items() for v, g in ids.items()]

    seed = args.seed if args.seed is not None else random.SystemRandom().randrange(1, 10 ** 6)
    rng = random.Random(seed)
    batch_used, combos = {}, []
    for _ in range(args.count):
        combo = roll_one(tables, rng, locks, avoid, batch_used, bad, warnings)
        pattern = cast_override or structure_cast_pattern(combo["structure"])
        if pattern is None:
            warnings.append("story-structures/%s.md has no valid cast_pattern line" %
                            combo["structure"])
        ordered = {"structure": combo["structure"], "cast_pattern": pattern}
        ordered.update((a, combo[a]) for a in tables["axes"] if a != "structure" and a in combo)
        combos.append(ordered)

    glossary = {}
    for combo in combos:
        for axis, vals in combo.items():
            if axis not in GLOSSARY_AXES:
                continue
            values = tables["axes"][axis]["values"]
            for v in (vals if isinstance(vals, list) else [vals]):
                if v in values:
                    glossary.setdefault(axis, {})[v] = values[v]

    emit({
        "_status": "ok",
        "seed": seed,
        "count": len(combos),
        "combos": combos,
        "glossary": glossary,
        "locked": {a: (v if tables["axes"][a].get("pick", 1) > 1 else v[0])
                   for a, v in locks.items()},
        "custom_locks": custom,
        "avoided": avoided,
        "recent_games": games,
        "warnings": sorted(set(warnings)),
        "next": "Offer 2-3 combos (+ 'tell me what you want'); read story-structures/<structure>.md "
                "for the chosen one; record the axes in main-arc.md `## Design DNA`; scaffold with "
                "compile.py --structure <structure>.",
    })
    return 0


if __name__ == "__main__":
    sys.exit(main())
