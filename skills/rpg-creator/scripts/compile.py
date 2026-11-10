#!/usr/bin/env python3
"""Scaffold a BAKED game skill under .claude/skills/<id>/.

A baked game is a self-contained, directly-playable skill: its play loop, rules, world, cast, and
story are compiled into the skill folder, so the generic /rpg engine is never loaded at play time.
This script lays down the folder tree and seeds it from rpg-creator's templates, so the author (the
model running rpg-creator) only FILLS IN / DISTILLS content — never reinvents the layout.

Three modes:
  Fresh game     python3 compile.py --id <id>
                 → content stubs + SKILL.md & mechanics.md templates + bundled engine.
  Fork           python3 compile.py --id <id> --from .claude/skills/<other-game>
                 → copies world/ characters/ story/ state.seed.json from an existing content dir,
                   then lays down fresh SKILL.md & mechanics.md templates to DISTILL + bundled engine.
  Update engine  python3 compile.py --id <id> --update-engine
                 → re-sync the canonical engine into an existing game (only touches engine/), then exit.

Optional mechanical fill-in (fresh and --from scaffolds only; never --update-engine) — saves the
author from hand-editing placeholders:
  --title "Game Title"   substitute {{Title}} (SKILL.md, mechanics.md, main-arc heading) and set
                         meta.game_id / meta.game_title in state.seed.json.
  --structure NAME       a story-structures/<NAME>.md spine (validated): written into main-arc.md's
                         `## Design DNA` block as `- structure:` + the file's `- cast_pattern:`.
  --modules a,b,c        keep only these modules: prune unlisted library-module sections from
                         mechanics.md, drop the seed's `drift` block unless drift is listed, fill the
                         SKILL.md "Active mechanics" list and resolve the drift / coaching
                         conditional placeholders. Library names: romance, magic-potency,
                         language-coaching, drift; anything else is a custom module.
{{id}} is ALWAYS substituted in a freshly written SKILL.md / mechanics.md (the id is always known).
Other {{...}} creative placeholders are never touched. Results are reported in the JSON `fill`.

Never overwrites an existing baked skill unless --force. Run from the project root.

The two distilled files (SKILL.md, mechanics.md) are always written as TEMPLATES for the model to
fill — see this skill's references/compile.md for the exact spec.
"""
import argparse
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, "..", "assets"))
# Canonical engine source. Each baked game carries its OWN copy (true single-folder
# portability); scripts are EXECUTED not read into context, so duplication costs zero
# play-time tokens. Re-sync into an existing game with --update-engine.
ENGINE_SRC = os.path.normpath(os.path.join(HERE, "..", "engine"))
# Only the references a game loads AT PLAY time travel with it. The other refs
# (gm-protocol, drama-craft, fail-forward, lorebook-protocol) are compile-time
# distill sources only — they live in mechanics.md, never bundled into a game.
# The single OOC command is `[god]`; its full capability ref is the only play-time fallback.
PLAY_REFS = ("god-mode.md",)
STRUCTURES = os.path.normpath(os.path.join(HERE, "..", "story-structures"))
CAST_PATTERNS = ("rotating", "fixed-party", "solo", "revolving")
CAST_RE = re.compile(r"^cast_pattern:\s*([a-z-]+)\s*$", re.MULTILINE)

LORE_INDEX_STUB = """\
# Lore Index — keyword-triggered world info

Scanned cheaply every turn; only `Read` the full `world/lore/<id>.md` when a keyword hits. One row per
lore entry. Keywords: include EVERY language a player might type (e.g. both `demon king` and `魔王`).

| id | title | keywords | hint | public |
|----|-------|----------|------|--------|
| {{lore-id}} | {{Title}} | {{comma, separated, keywords}} | {{one-line hint}} | {{yes|no}} |
"""

CHAR_INDEX_STUB = """\
# Character Index

The cast roster (配角 / supporting characters), scanned cheaply each turn to decide which cards to load.
One line each. Full cards live in `characters/cast/<id>.md` and load only when the character is present.
The 主角 (protagonist) is `characters/player.md` — always loaded, not listed here.

| id | one-liner | role | usual location |
|----|-----------|------|----------------|
| {{char-id}} | {{archetype + relation to player}} | {{romanceable/ally/rival/antagonist}} | {{location}} |
"""

MAIN_ARC_STUB = """\
# Main Arc — {{Title}}

## Design DNA
<!-- The chosen design axes (from scripts/roll.py + the interview), one `- axis: value` line each.
     scorecard.py reads cast_pattern from here; roll.py reads this block to steer NEW games away
     from what this one used. compile.py --structure fills structure + cast_pattern. -->
- structure: {{structure — a story-structures/<name>.md}}
- cast_pattern: {{rotating|fixed-party|solo|revolving — from the structure file}}
- opposition: {{opposition}}
- ending: {{ending shape}}
- setting: {{setting}}
- tone: {{tone}}
- protagonist: {{protagonist situation}}
- relationship: {{central relationship}}
- drives: {{character-drive palette, e.g. debt, vow, guilt}}
- scale: {{scale}}
- twist: {{wildcard constraint, or none}}

## The Spine (where this is all going)
{{1-2 paragraphs: the central conflict or goal and its stakes, shaped by the structure.}}

## Phases
<!-- Use the phase shape the structure file defines (not always three acts); add/remove rows. -->
1. **{{Phase 1 name}}** — {{the hook and first turn}}
2. **{{Phase 2 name}}** — {{development; the turn or reveal}}
3. **{{Phase 3 name}}** — {{the peak and payoff}}

## Presence Matrix (who is on stage in which beat — shaped by the DNA's cast_pattern)
| beat | on stage (besides player) |
|------|---------------------------|
| {{beat 1}} | {{A + B}} |
| {{beat 2}} | {{A + D}} |
| {{climax}} | {{everyone}} |

## Pressure
- {{the structure's pressure source: a deadline, dwindling resources, a season turning, heat…}}

## Opposition
{{Who or what pushes back (person, institution, nature, rival, the party itself, none) + its moves.}}
"""

CONTENT = (  # (relative path, template asset OR inline stub)
    ("world/world-bible.md", ("tpl", "world-bible.template.md")),
    ("state.seed.json",      ("tpl", "state.template.json")),
    ("world/lore-index.md",  ("str", LORE_INDEX_STUB)),
    ("characters/index.md",  ("str", CHAR_INDEX_STUB)),
    ("characters/player.md", ("tpl", "protagonist-card.template.md")),
    ("story/main-arc.md",    ("str", MAIN_ARC_STUB)),
)
# Migrated from --from: copy these dirs/files verbatim instead of seeding stubs.
MIGRATE = ("world", "characters", "story", "state.seed.json")


def seed(path, kind, payload, force):
    if os.path.exists(path) and not force:
        return "skipped (exists)"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if kind == "str":
        with open(path, "w", encoding="utf-8") as f:
            f.write(payload)
        return "written"
    src = os.path.join(ASSETS, payload)
    if not os.path.exists(src):
        return f"MISSING TEMPLATE: {src}"
    shutil.copyfile(src, path)
    return "copied"


def _has_files(path):
    """True if a directory exists and contains at least one file (not just empty subdirs)."""
    for _root, _dirs, files in os.walk(path):
        if files:
            return True
    return False


def migrate(src_dir, skill_dir, force):
    actions = {}
    for item in MIGRATE:
        src = os.path.join(src_dir, item)
        dst = os.path.join(skill_dir, item)
        if not os.path.exists(src):
            actions[item] = "MISSING in source"
            continue
        # An empty pre-created dir doesn't count as "exists" — only real content blocks a migrate.
        occupied = _has_files(dst) if os.path.isdir(dst) else os.path.exists(dst)
        if occupied and not force:
            actions[item] = "skipped (exists)"
            continue
        if os.path.isdir(src):
            # dirs_exist_ok=True so we merge real files into any pre-created empty dir.
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
        actions[item] = "migrated"
    return actions


def bundle_engine(skill_dir, force):
    """Copy the play-time engine (scripts + the 2 fallback refs) into <game>/engine/.

    This is what makes a baked game self-contained: it carries its own engine, so the
    whole folder copies anywhere with no shared dependency. Re-run (via --update-engine)
    to re-sync after the canonical engine improves.
    """
    actions = {}
    dst_scripts = os.path.join(skill_dir, "engine", "scripts")
    os.makedirs(dst_scripts, exist_ok=True)
    for fn in sorted(os.listdir(os.path.join(ENGINE_SRC, "scripts"))):
        if fn.endswith(".py"):
            shutil.copyfile(os.path.join(ENGINE_SRC, "scripts", fn),
                            os.path.join(dst_scripts, fn))
    actions["engine/scripts"] = "synced (%d .py)" % len(
        [f for f in os.listdir(dst_scripts) if f.endswith(".py")])
    dst_refs = os.path.join(skill_dir, "engine", "references")
    os.makedirs(dst_refs, exist_ok=True)
    for ref in PLAY_REFS:
        src = os.path.join(ENGINE_SRC, "references", ref)
        if os.path.exists(src):
            shutil.copyfile(src, os.path.join(dst_refs, ref))
    actions["engine/references"] = "synced (%s)" % ", ".join(PLAY_REFS)
    return actions


LIBRARY_MODULES = ("romance", "magic-potency", "language-coaching", "drift")
MODULES_LINE_ANCHOR = "{{e.g. romance \u00b7 language-coaching \u00b7 magic-potency \u00b7 drift}}"
DRIFT_STEP_RE = re.compile(r"\{\{If drift active: (.+?)\}\}\s*")
COACHING_NOTE_RE = re.compile(
    r"\{\{\+ any module\s+note, e\.g\. a `\U0001F4AC \u6559\u7df4` coaching note if coaching is on\}\}")
CUSTOM_HEADING = "### {{custom module}} (if any)"


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _write(path, text):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def parse_modules(raw):
    seen = []
    for m in (raw or "").split(","):
        m = m.strip()
        if m and m not in seen:
            seen.append(m)
    return seen


def _section_span(text, heading):
    """(start, end) of the '### ' section that begins with `heading` (to next ## / ### or EOF)."""
    start = text.find(heading)
    if start < 0:
        return None
    m = re.search(r"\n#{2,3} ", text[start + len(heading):])
    end = start + len(heading) + m.start() + 1 if m else len(text)
    return start, end


def apply_modules_mechanics(text, mods, report):
    customs = [m for m in mods if m not in LIBRARY_MODULES]
    for name in LIBRARY_MODULES:
        heading = "### {{%s}} (if active)" % name
        span = _section_span(text, heading)
        if span is None:
            report.append("mechanics.md: anchor not found for module %r (left alone)" % name)
        elif name in mods:
            text = text.replace(heading, "### %s" % name, 1)
            report.append("mechanics.md: kept section %s" % name)
        else:
            text = text[:span[0]] + text[span[1]:]
            report.append("mechanics.md: removed section %s" % name)
    span = _section_span(text, CUSTOM_HEADING)
    if span is None:
        report.append("mechanics.md: custom-module anchor not found (left alone)")
    elif not customs:
        text = text[:span[0]] + text[span[1]:]
        report.append("mechanics.md: removed custom-module section")
    else:
        body = text[span[0] + len(CUSTOM_HEADING):span[1]]
        blocks = "".join("### %s%s" % (c, body if body.endswith("\n") else body + "\n")
                         for c in customs)
        text = text[:span[0]] + blocks + text[span[1]:]
        report.append("mechanics.md: custom section(s) for %s" % ", ".join(customs))
    return re.sub(r"\n{3,}", "\n\n", text)


def apply_modules_skill(text, mods, report):
    if MODULES_LINE_ANCHOR in text:
        text = text.replace(MODULES_LINE_ANCHOR, " \u00b7 ".join(mods) if mods else "none", 1)
        report.append("SKILL.md: Active mechanics list = %s" % (" \u00b7 ".join(mods) or "none"))
    else:
        report.append("SKILL.md: Active mechanics anchor not found (left alone)")
    m = DRIFT_STEP_RE.search(text)
    if not m:
        report.append("SKILL.md: drift step placeholder not found (left alone)")
    elif "drift" in mods:
        step = m.group(1)
        text = text[:m.start()] + step[0].upper() + step[1:] + "\n   " + text[m.end():]
        report.append("SKILL.md: drift step made plain text")
    else:
        text = text[:m.start()] + text[m.end():]
        report.append("SKILL.md: drift step removed")
    m = COACHING_NOTE_RE.search(text)
    if not m:
        report.append("SKILL.md: coaching-note placeholder not found (left alone)")
    elif "language-coaching" in mods:
        text = text[:m.start()] + ", plus a `\U0001F4AC \u6559\u7df4` coaching note" + text[m.end():]
        report.append("SKILL.md: coaching note made plain text")
    else:
        text = text[:m.start()] + text[m.end():]
        report.append("SKILL.md: coaching note removed")
    return text


def structure_names():
    if not os.path.isdir(STRUCTURES):
        return []
    return sorted(fn[:-3] for fn in os.listdir(STRUCTURES)
                  if fn.endswith(".md") and fn.lower() != "readme.md")


def structure_cast_pattern(name):
    with open(os.path.join(STRUCTURES, name + ".md"), encoding="utf-8") as f:
        m = CAST_RE.search(f.read())
    return m.group(1) if m and m.group(1) in CAST_PATTERNS else None


def _set_dna_line(block, key, value):
    line = "- %s: %s" % (key, value)
    pat = re.compile(r"^[-*]\s*%s\s*:.*$" % re.escape(key), re.MULTILINE)
    if pat.search(block):
        return pat.sub(lambda _m: line, block, count=1)
    return block.rstrip("\n") + "\n" + line + "\n"


def apply_structure(path, name, report):
    """Write structure + cast_pattern into main-arc.md's `## Design DNA` (create it if absent)."""
    pattern = structure_cast_pattern(name) or "rotating"
    text = _read(path)
    m = re.search(r"^## Design DNA[^\n]*\n", text, re.MULTILINE)
    if m is None:
        h1 = re.search(r"^# [^\n]*\n", text, re.MULTILINE)
        at = h1.end() if h1 else 0
        block = "\n## Design DNA\n- structure: %s\n- cast_pattern: %s\n" % (name, pattern)
        text = text[:at] + block + text[at:]
        report.append("story/main-arc.md: Design DNA block added (structure=%s, cast_pattern=%s)"
                      % (name, pattern))
    else:
        nxt = re.search(r"^## ", text[m.end():], re.MULTILINE)
        end = m.end() + nxt.start() if nxt else len(text)
        block = _set_dna_line(_set_dna_line(text[m.end():end], "structure", name),
                              "cast_pattern", pattern)
        if nxt and not block.endswith("\n\n"):
            block = block.rstrip("\n") + "\n\n"
        text = text[:m.end()] + block + text[end:]
        report.append("story/main-arc.md: Design DNA structure=%s, cast_pattern=%s"
                      % (name, pattern))
    _write(path, text)


def apply_seed(path, title, mods, gid, report):
    try:
        data = json.loads(_read(path))
    except (OSError, json.JSONDecodeError) as exc:
        report.append("state.seed.json: unreadable, not modified (%s)" % exc)
        return
    before = json.dumps(data, sort_keys=True)
    if title is not None:
        meta = data.setdefault("meta", {})
        meta["game_id"] = gid
        meta["game_title"] = title
        report.append("state.seed.json: meta.game_id/game_title set")
    if mods is not None:
        if "drift" in mods:
            report.append("state.seed.json: drift block kept")
        elif "drift" in data:
            del data["drift"]
            report.append("state.seed.json: drift block removed")
    if json.dumps(data, sort_keys=True) != before:
        _write(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def fill(skill_dir, actions, gid, title, mods, structure=None):
    """Mechanical placeholder substitution on files freshly written by THIS run."""
    report = []
    fresh = ("copied", "written")
    for rel in ("SKILL.md", "mechanics.md"):
        path = os.path.join(skill_dir, rel)
        if actions.get(rel) not in fresh or not os.path.exists(path):
            continue
        text = _read(path)
        if mods is not None:
            text = (apply_modules_skill if rel == "SKILL.md" else apply_modules_mechanics)(
                text, mods, report)
        n_id = text.count("{{id}}")
        text = text.replace("{{id}}", gid)
        note = "%s: {{id}} x%d" % (rel, n_id)
        if title is not None:
            n_t = text.count("{{Title}}")
            text = text.replace("{{Title}}", title)
            note += ", {{Title}} x%d" % n_t
        report.append(note)
        _write(path, text)
    if title is not None and actions.get("story/main-arc.md") in fresh:
        path = os.path.join(skill_dir, "story", "main-arc.md")
        text = _read(path)
        if "# Main Arc \u2014 {{Title}}" in text:
            _write(path, text.replace("# Main Arc \u2014 {{Title}}", "# Main Arc \u2014 " + title, 1))
            report.append("story/main-arc.md: heading title set")
        else:
            report.append("story/main-arc.md: heading anchor not found (left alone)")
    arc_path = os.path.join(skill_dir, "story", "main-arc.md")
    if structure is not None:
        if os.path.exists(arc_path) and (actions.get("story/main-arc.md") in fresh
                                         or actions.get("story") == "migrated"):
            apply_structure(arc_path, structure, report)
        else:
            report.append("story/main-arc.md: not written this run; set `- structure: %s` in its "
                          "Design DNA by hand" % structure)
    seed_path = os.path.join(skill_dir, "state.seed.json")
    if (title is not None or mods is not None) and os.path.exists(seed_path) \
            and actions.get("state.seed.json") in fresh + ("migrated",):
        apply_seed(seed_path, title, mods, gid, report)
    return report


def main():
    ap = argparse.ArgumentParser(description="Scaffold a baked game skill.")
    ap.add_argument("--id", required=True, help="kebab-case id (= skill folder AND slash command)")
    ap.add_argument("--root", default=os.getcwd(), help="project root")
    ap.add_argument("--from", dest="src", default=None,
                    help="seed content from an existing dir, e.g. .claude/skills/<other-game> (fork)")
    ap.add_argument("--update-engine", action="store_true",
                    help="re-sync the canonical engine into an EXISTING baked game, then exit")
    ap.add_argument("--title", default=None,
                    help="game title: substitute {{Title}} and set seed meta.game_id/game_title")
    ap.add_argument("--modules", default=None,
                    help="comma list of active modules (romance,magic-potency,language-coaching,"
                         "drift; others = custom): prune unused sections/placeholders")
    ap.add_argument("--structure", default=None,
                    help="story-structures/<NAME>.md spine; written into main-arc.md's Design DNA")
    ap.add_argument("--force", action="store_true", help="overwrite existing files")
    args = ap.parse_args()

    gid = args.id.strip()
    if not gid or "/" in gid or " " in gid or gid.startswith("_"):
        print(json.dumps({"_status": "error",
                          "message": "id must be a simple kebab-case name (no /, space, leading _)"},
                         ensure_ascii=False))
        return 1

    title = args.title.strip() if args.title is not None else None
    if title is not None and (not title or any(c in title for c in '"`$\\\n\r')):
        print(json.dumps({"_status": "error",
                          "message": "title must be non-empty and contain no \" ` $ \\ or newline "
                                     "(it is embedded in YAML frontmatter and a shell command)"},
                         ensure_ascii=False))
        return 1
    mods = parse_modules(args.modules) if args.modules is not None else None
    structure = args.structure.strip() if args.structure is not None else None
    if structure is not None and structure not in structure_names():
        print(json.dumps({"_status": "error",
                          "message": "unknown structure %r; valid: %s" % (
                              structure, ", ".join(structure_names()))}, ensure_ascii=False))
        return 1

    skill_dir = os.path.join(args.root, ".claude", "skills", gid)

    if args.update_engine:
        if title is not None or mods is not None or structure is not None:
            print(json.dumps({"_status": "error",
                              "message": "--title/--modules/--structure do not apply to "
                                         "--update-engine"},
                             ensure_ascii=False))
            return 1
        if not os.path.isdir(skill_dir):
            print(json.dumps({"_status": "error", "message": "no such game: %s" % skill_dir},
                             ensure_ascii=False))
            return 1
        acts = bundle_engine(skill_dir, args.force)
        print(json.dumps({"_status": "engine_synced", "id": gid, "skill_dir": skill_dir,
                          "actions": acts}, ensure_ascii=False, indent=2))
        return 0

    actions = {}
    for sub in ("world/lore", "characters/cast", "story", "modules"):
        os.makedirs(os.path.join(skill_dir, sub), exist_ok=True)

    # The two distilled files are ALWAYS laid down as templates to fill/distill.
    actions["SKILL.md"] = seed(os.path.join(skill_dir, "SKILL.md"),
                               "tpl", "game-skill-SKILL.template.md", args.force)
    actions["mechanics.md"] = seed(os.path.join(skill_dir, "mechanics.md"),
                                   "tpl", "mechanics.template.md", args.force)

    if args.src:
        src_dir = args.src if os.path.isabs(args.src) else os.path.join(args.root, args.src)
        if not os.path.isdir(src_dir):
            print(json.dumps({"_status": "error",
                              "message": "no such source dir: %s" % src_dir}, ensure_ascii=False))
            return 1
        actions.update(migrate(src_dir, skill_dir, args.force))
        mode = "migrate"
    else:
        for rel, (kind, payload) in CONTENT:
            actions[rel] = seed(os.path.join(skill_dir, rel), kind, payload, args.force)
        mode = "fresh"

    # Mechanical placeholder fill ({{id}} always; {{Title}}/modules only when asked).
    fill_report = fill(skill_dir, actions, gid, title, mods, structure)

    # Bundle the engine so the game is self-contained (copy anywhere, no shared dep).
    actions.update(bundle_engine(skill_dir, args.force))

    print(json.dumps({
        "_status": "scaffolded",
        "mode": mode,
        "id": gid,
        "skill_dir": skill_dir,
        "slash_command": "/%s" % gid,
        "structure": structure,
        "save_dir": os.path.join(args.root, "saves", gid),
        "actions": actions,
        "fill": fill_report,
        "next": [
            ("Read story-structures/%s.md before outlining (phases, pressure, cast pattern)" % structure
             if structure else "No --structure given: fill main-arc.md's Design DNA by hand"),
            "Fill/review world/ characters/ story/ state.seed.json (see references/design.md)",
            "DISTILL SKILL.md (play loop) + mechanics.md (rulebook) (see references/compile.md); "
            "verify what `fill` reports, then fill the remaining creative {{placeholders}}. "
            "Reference scripts as $SKILL/engine/scripts/<name>.py (this game's OWN engine, bundled).",
            "Run the baked-skill checklist + design gates, then tell the user to play with /%s" % gid,
        ],
        "note": "engine/ is bundled (self-contained). Re-sync later with: compile.py --id %s --update-engine" % gid,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
