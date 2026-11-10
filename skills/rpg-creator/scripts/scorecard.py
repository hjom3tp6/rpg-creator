#!/usr/bin/env python3
"""Structural scorecard for a BAKED game — the DETERMINISTIC counting half of step 4.

references/design.md §5 opens the complexity-tuning step with a "structural scorecard": how many
chapters/beats, characters, romanceable heroines, hidden secrets, distinct sub-casts, who gets solo
time. Those are COUNTS — the model should not eyeball them by hand (it miscounts and burns tokens).
This script reads the game files and reports the numbers + a few measurable ensemble flags.

    python3 "$SKILL/scripts/scorecard.py" --id <id>

It only COUNTS. It does NOT judge whether the size is right, which axis is thinnest, or how to tune —
those are the LLM's read and the user's call (design.md §5 steps 1-2). Pair the numbers here with that
judgment. Sister script: validate.py (the pass/fail floor for step 6).

Cast pattern: main-arc.md's `## Design DNA` block (`- cast_pattern: rotating|fixed-party|solo|revolving`,
else the pattern of its `- structure:` file in story-structures/) decides which ensemble flags apply.
The rotation flags (rotation floor, solo time, full-cast-only-at-climax) are scored only for a
`rotating` cast; for the other patterns they are null with a note naming the equivalent judgment
check. A game with no DNA block is treated as rotating (the pre-DNA behaviour). Arcs written with
`## Phases` / `## Pressure` report phases / pressure_sources; older `## Acts` / `## Ticking Clocks`
arcs keep reporting acts / ticking_clocks.

Counting is best-effort over free-form authored prose: the Presence Matrix uses display names of the
author's choosing, so sub-cast tokens are counted as written, not resolved against character ids.
Run from the project root (or pass --root).
"""
import argparse
import json
import os
import re
import sys

SPLIT_RE = re.compile(r"\s*(?:\+|,|&|/|\band\b)\s*", re.IGNORECASE)
FULL_CAST_RE = re.compile(r"\b(everyone|all|full[- ]?cast|the whole cast)\b", re.IGNORECASE)
CLIMAX_RE = re.compile(r"\b(climax|finale|final|showdown|confrontation)\b", re.IGNORECASE)
PLACEHOLDER_RE = re.compile(r"\{\{.*?\}\}")
DNA_LINE_RE = re.compile(r"^\s*[-*]\s*([A-Za-z_][\w -]*?)\s*:\s*(.+?)\s*$")
CAST_RE = re.compile(r"^cast_pattern:\s*([a-z-]+)\s*$", re.MULTILINE)
CAST_PATTERNS = ("rotating", "fixed-party", "solo", "revolving")
STRUCTURES = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                           "..", "story-structures"))
# The judgment check that replaces the rotation gate for each non-rotating cast (design.md §4).
PATTERN_CHECK = {
    "fixed-party": "spotlight: every party member owns >=1 beat their skill/stake decides, and "
                   "each member's secret or drive pays off once",
    "solo": "visitors: the protagonist carries most beats; >=2 visitors are re-met in changed "
            "circumstances and one recurring figure spans several phases",
    "revolving": "turnover: new characters keep arriving through the middle phases, some "
                 "departures land as losses, and >=1 constant changes across the story",
}


def read_text(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return f.read()


def table_rows(text):
    """Data rows (header + |---| separator dropped) of the FIRST markdown table in `text`."""
    rows, in_table = [], False
    for line in (text or "").splitlines():
        s = line.strip()
        if not s.startswith("|"):
            if in_table:
                break  # table ended
            continue
        in_table = True
        cells = [c.strip() for c in s.strip("|").split("|")]
        if set("".join(cells)) <= set("-: "):
            continue  # |---|---| separator
        if cells[:1] == ["id"] or cells[:1] == ["beat"]:
            continue  # header
        rows.append(cells)
    return rows


def section(text, heading_substr):
    """Return the lines under the first `## ` heading whose text contains heading_substr (ci)."""
    out, capturing = [], False
    for line in (text or "").splitlines():
        if line.startswith("## "):
            if capturing:
                break
            capturing = heading_substr.lower() in line.lower()
            continue
        if capturing:
            out.append(line)
    return "\n".join(out)


def count_characters(skill_dir):
    text = read_text(os.path.join(skill_dir, "characters", "index.md"))
    roles = {}
    total = 0
    for cells in table_rows(text):
        if PLACEHOLDER_RE.search("".join(cells)):
            continue
        total += 1
        role = (cells[2].lower() if len(cells) > 2 else "unspecified") or "unspecified"
        roles[role] = roles.get(role, 0) + 1
    return {
        "supporting_cast": total,            # 配角 count (index rows)
        "named_total": total + 1,            # + the protagonist
        "romanceable": roles.get("romanceable", 0),
        "by_role": roles,
    }


def count_lore(skill_dir):
    text = read_text(os.path.join(skill_dir, "world", "lore-index.md"))
    total = hidden = 0
    for cells in table_rows(text):
        if len(cells) < 2 or PLACEHOLDER_RE.search("".join(cells)):
            continue
        total += 1
        if cells[-1].lower().startswith("no"):
            hidden += 1
    return {"lore_entries": total, "hidden_secrets": hidden}


def has_heading(text, heading_substr):
    return any(l.startswith("## ") and heading_substr.lower() in l.lower()
               for l in (text or "").splitlines())


def parse_dna(text):
    """`- axis: value` lines under `## Design DNA` -> {axis: value}; {{placeholders}} skipped."""
    dna = {}
    for line in section(text, "Design DNA").splitlines():
        m = DNA_LINE_RE.match(line)
        if m and not PLACEHOLDER_RE.search(m.group(2)) and "{{" not in m.group(2):
            dna[m.group(1).strip().lower().replace(" ", "_").replace("-", "_")] = m.group(2)
    return dna


def resolve_cast_pattern(dna):
    """(pattern, source) — DNA line, else the structure file's line, else rotating (default)."""
    raw = (dna.get("cast_pattern") or "").strip().lower()
    if raw in CAST_PATTERNS:
        return raw, "design_dna"
    name = (dna.get("structure") or "").strip().lower()
    text = read_text(os.path.join(STRUCTURES, name + ".md")) if re.fullmatch(r"[a-z0-9-]+", name) \
        else None
    m = CAST_RE.search(text or "")
    if m and m.group(1) in CAST_PATTERNS:
        return m.group(1), "story-structures/%s.md" % name
    if raw:
        return "rotating", "default (unrecognised cast_pattern %r)" % raw
    return "rotating", "default (no Design DNA cast_pattern)"


def count_items(text, heading, numbered):
    """Numbered (`1. `) or bulleted (`-`/`*`) non-placeholder lines under a `## ` heading."""
    def hit(l):
        return re.match(r"\s*\d+\.\s", l) if numbered else l.strip().startswith(("-", "*"))
    return len([l for l in section(text, heading).splitlines()
                if hit(l) and not PLACEHOLDER_RE.search(l)])


def parse_arc(skill_dir):
    text = read_text(os.path.join(skill_dir, "story", "main-arc.md"))
    if text is None:
        return {"_note": "story/main-arc.md missing", "_dna": {}}
    out = {"_dna": parse_dna(text)}
    if has_heading(text, "Phases"):
        out["phases"] = count_items(text, "Phases", True)
    else:
        out["acts"] = count_items(text, "Acts", True)
    if has_heading(text, "Pressure"):
        out["pressure_sources"] = count_items(text, "Pressure", False)
    else:
        out["ticking_clocks"] = count_items(text, "Ticking Clock", False)
    matrix = section(text, "Presence Matrix")
    out.update(ensemble(matrix))
    return out


def ensemble(matrix_text):
    """Measurable ensemble-depth signals from the Presence Matrix (design.md §4)."""
    beats = []  # (label, token_set, is_full_cast)
    for cells in table_rows(matrix_text):
        if len(cells) < 2 or PLACEHOLDER_RE.search("".join(cells)):
            continue
        label, on_stage = cells[0], cells[-1]
        full = bool(FULL_CAST_RE.search(on_stage))
        tokens = frozenset(t.lower() for t in SPLIT_RE.split(on_stage)
                           if t.strip() and not FULL_CAST_RE.search(t))
        beats.append((label, tokens, full))
    if not beats:
        return {"beats": 0, "_note": "no Presence Matrix rows found (can't score ensemble depth)"}

    distinct = {("*full*" if full else fs) for _l, fs, full in beats if fs or full}
    solo_tokens = sorted({next(iter(fs)) for _l, fs, full in beats
                          if not full and len(fs) == 1})
    all_tokens = sorted(set().union(*[fs for _l, fs, _f in beats]) or set())
    full_idx = [i for i, (_l, _fs, full) in enumerate(beats) if full]
    last = len(beats) - 1
    full_labels = [beats[i][0] for i in full_idx]
    full_cast_only_at_climax = all(
        i == last or CLIMAX_RE.search(beats[i][0]) for i in full_idx) if full_idx else True

    return {
        "beats": len(beats),
        "distinct_subcasts": len(distinct),
        "full_cast_beats": len(full_idx),
        "full_cast_labels": full_labels,
        "full_cast_only_at_climax": full_cast_only_at_climax,
        "characters_with_solo_beat": solo_tokens,
        "matrix_tokens": all_tokens,
        "tokens_without_solo_beat": sorted(set(all_tokens) - set(solo_tokens)),
    }


def main():
    ap = argparse.ArgumentParser(description="Structural scorecard for a baked game (counts only).")
    ap.add_argument("--id", required=True, help="baked game id (= skill folder)")
    ap.add_argument("--root", default=os.getcwd(), help="project root")
    args = ap.parse_args()

    gid = args.id.strip()
    root = os.path.abspath(args.root)
    skill_dir = os.path.join(root, ".claude", "skills", gid)
    if not os.path.isdir(skill_dir):
        print(json.dumps({"_status": "error", "message": "no such baked game: %s" % skill_dir},
                         ensure_ascii=False))
        return 1

    chars = count_characters(skill_dir)
    lore = count_lore(skill_dir)
    arc = parse_arc(skill_dir)

    dna = arc.pop("_dna", {})
    cast_pattern, cast_source = resolve_cast_pattern(dna)

    # The one measurable ensemble floor from design.md §4: distinct sub-casts >= named characters.
    distinct = arc.get("distinct_subcasts")
    rotation_floor_met = (distinct >= chars["named_total"]) if isinstance(distinct, int) else None
    flags = {
        "rotation_floor_met": rotation_floor_met,
        "_rotation_floor": "distinct_subcasts (%s) >= named characters (%d)" % (
            distinct, chars["named_total"]),
        "everyone_gets_solo_time": (not arc.get("tokens_without_solo_beat"))
        if "tokens_without_solo_beat" in arc else None,
        "full_cast_reserved_for_climax": arc.get("full_cast_only_at_climax"),
    }
    if cast_pattern != "rotating":
        flags = {
            "rotation_floor_met": None,
            "everyone_gets_solo_time": None,
            "full_cast_reserved_for_climax": None,
            "_not_applicable": "cast_pattern is %s: the rotation flags apply only to a rotating "
                               "cast. Judge instead (design.md §4) — %s." % (
                                   cast_pattern, PATTERN_CHECK[cast_pattern]),
        }

    print(json.dumps({
        "_status": "ok",
        "id": gid,
        "design_dna": dna or None,
        "cast_pattern": cast_pattern,
        "_cast_pattern_source": cast_source,
        "characters": chars,
        "lore": lore,
        "structure": {k: arc[k] for k in ("phases", "acts", "pressure_sources", "ticking_clocks",
                                          "beats") if k in arc},
        "ensemble": {k: arc[k] for k in (
            "distinct_subcasts", "full_cast_beats", "full_cast_labels",
            "full_cast_only_at_climax", "characters_with_solo_beat",
            "tokens_without_solo_beat", "matrix_tokens", "_note") if k in arc},
        "measurable_flags": flags,
        "note": ("Counts only. Whether this size is RIGHT — thinnest axis, what to add/cut — is the "
                 "LLM's read and the user's call (design.md §5). Flags are measurable floors, not "
                 "quality verdicts: a passing flag still needs the §4 judgment gates."),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
