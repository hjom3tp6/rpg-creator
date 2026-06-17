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

Never overwrites an existing baked skill unless --force. Run from the project root.

The two distilled files (SKILL.md, mechanics.md) are always written as TEMPLATES for the model to
fill — see this skill's references/compile.md for the exact spec.
"""
import argparse
import json
import os
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

## The Spine (where this is all going)
{{1-2 paragraphs: the central mystery/conflict and its eventual stakes.}}

## Acts
1. **{{Act 1 name}}** — {{the hook and first turn}}
2. **{{Act 2 name}}** — {{escalation; the midpoint reveal}}
3. **{{Act 3 name}}** — {{the confrontation and payoff}}

## Presence Matrix (who is on stage in which beat — MUST rotate; full cast only at the climax)
| beat | on stage (besides player) |
|------|---------------------------|
| {{beat 1}} | {{A + B}} |
| {{beat 2}} | {{A + D}} |
| {{climax}} | {{everyone}} |

## Ticking Clocks
- {{a deadline/pressure that should always be felt}}

## Antagonist / Off-screen Mover
{{Who pushes back, and what they do while the player is busy.}}
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


def main():
    ap = argparse.ArgumentParser(description="Scaffold a baked game skill.")
    ap.add_argument("--id", required=True, help="kebab-case id (= skill folder AND slash command)")
    ap.add_argument("--root", default=os.getcwd(), help="project root")
    ap.add_argument("--from", dest="src", default=None,
                    help="seed content from an existing dir, e.g. .claude/skills/<other-game> (fork)")
    ap.add_argument("--update-engine", action="store_true",
                    help="re-sync the canonical engine into an EXISTING baked game, then exit")
    ap.add_argument("--force", action="store_true", help="overwrite existing files")
    args = ap.parse_args()

    gid = args.id.strip()
    if not gid or "/" in gid or " " in gid or gid.startswith("_"):
        print(json.dumps({"_status": "error",
                          "message": "id must be a simple kebab-case name (no /, space, leading _)"},
                         ensure_ascii=False))
        return 1

    skill_dir = os.path.join(args.root, ".claude", "skills", gid)

    if args.update_engine:
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

    # Bundle the engine so the game is self-contained (copy anywhere, no shared dep).
    actions.update(bundle_engine(skill_dir, args.force))

    print(json.dumps({
        "_status": "scaffolded",
        "mode": mode,
        "id": gid,
        "skill_dir": skill_dir,
        "slash_command": "/%s" % gid,
        "save_dir": os.path.join(args.root, "saves", gid),
        "actions": actions,
        "next": [
            "Fill/review world/ characters/ story/ state.seed.json (see references/design.md)",
            "DISTILL SKILL.md (play loop) + mechanics.md (rulebook) (see references/compile.md). "
            "Reference scripts as $SKILL/engine/scripts/<name>.py (this game's OWN engine, bundled).",
            "Run the baked-skill checklist + design gates, then tell the user to play with /%s" % gid,
        ],
        "note": "engine/ is bundled (self-contained). Re-sync later with: compile.py --id %s --update-engine" % gid,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
