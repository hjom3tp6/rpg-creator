"""Tests for scripts/validate.py's mechanical checks (stdlib unittest)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.normpath(os.path.join(HERE, ".."))
COMPILE = os.path.join(SKILL, "scripts", "compile.py")
VALIDATE = os.path.join(SKILL, "scripts", "validate.py")
GID = "demo"

SKILL_MD = """---
name: demo
description: Play "Demo", a baked narrative RPG. Use when the user types /demo.
---
# Demo
Resume with `/demo`. Read `mechanics.md`, `world/world-bible.md`, `characters/index.md`.
"""
MECHANICS = "# Mechanics\n\n" + "\n".join("Rule %d: keep it short." % i for i in range(30)) + "\n"
BIBLE = "# World\nA small harbor town.\n"
LORE_INDEX = """# Lore Index

| id | title | keywords | hint | public |
|----|-------|----------|------|--------|
| grey-fog | The Fog | fog, mist | hint | no |
"""
INDEX = """# Character Index

| id | one-liner | role | usual location |
|----|-----------|------|----------------|
| mira | Mira, a tsundere knight | romanceable | gate |
| sera | Sera the quiet scribe | ally | library |
"""
CARD = """# {name} - tagline

- **id:** {cid}
- **Age:** 24

## Appearance
Tall, with red braids and a scarred chin.

## Personality
Proud.
"""
PLAYER = """# Aria - the heir

- **id:** player
- **Age:** late 20s

## Appearance
- **Build & look:** lean, ink-stained fingers
"""
ARC = """# Main arc

## Presence Matrix (who is on stage)
| beat | on stage (besides player) |
|------|---------------------------|
| 1 | Mira |
| 2 | Mira + Sera (cameo) |
| 3 | player alone |
| climax | everyone |

## Ticking Clocks
- the tide
"""


def seed_data():
    return {
        "meta": {"game_id": GID, "game_title": "Demo", "created": "", "last_played": "",
                 "schema_version": 3},
        "player": {"name": "Aria", "description": "", "persona_file": "characters/player.md"},
        "scene": {"location": "Harbor gate", "present_characters": ["mira"],
                  "summary": "Dawn at the gate."},
        "clock": {"day": 1, "phase": "morning", "deadlines": []},
        "goals": {"short": ["Get inside"], "mid": [], "long": []},
        "affinity": {"mira": 0, "sera": 0, "_comment": "ignored"},
        "relationships": {"mira": {"stage": "stranger"}},
        "flags": {}, "inventory": [],
    }


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


class ValidateBase(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.root = self._td.name
        self.dir = os.path.join(self.root, ".claude", "skills", GID)
        p = subprocess.run([sys.executable, COMPILE, "--id", GID, "--title", "Demo",
                            "--modules", "romance", "--root", self.root],
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.w("SKILL.md", SKILL_MD)
        self.w("mechanics.md", MECHANICS)
        self.w("world/world-bible.md", BIBLE)
        self.w("world/lore-index.md", LORE_INDEX)
        self.w("world/lore/grey-fog.md", "The fog is old.\n")
        self.w("characters/index.md", INDEX)
        self.w("characters/player.md", PLAYER)
        for cid, name in (("mira", "Mira"), ("sera", "Sera")):
            self.w("characters/cast/%s.md" % cid, CARD.format(name=name, cid=cid))
        self.w("story/main-arc.md", ARC)
        self.set_seed(seed_data())

    def tearDown(self):
        self._td.cleanup()

    def w(self, rel, text):
        write(os.path.join(self.dir, rel), text)

    def r(self, rel):
        with open(os.path.join(self.dir, rel), encoding="utf-8") as f:
            return f.read()

    def set_seed(self, data):
        self.w("state.seed.json", json.dumps(data, indent=2))

    def edit_seed(self, fn):
        data = json.loads(self.r("state.seed.json"))
        fn(data)
        self.set_seed(data)

    def validate(self, *extra):
        p = subprocess.run([sys.executable, VALIDATE, "--id", GID, "--root", self.root, *extra],
                           capture_output=True, text=True, timeout=120)
        rep = json.loads(p.stdout)
        rep["rc"] = p.returncode
        rep["by"] = {c["name"]: c for c in rep.get("checks", [])}
        return rep

    def fails(self, rep):
        return {c["name"] for c in rep["checks"] if c["status"] == "FAIL"}

    def status(self, rep, name):
        return rep["by"][name]["status"] if name in rep["by"] else None


class CleanGameTest(ValidateBase):
    def test_clean_game_has_no_fail(self):
        rep = self.validate()
        self.assertEqual(self.fails(rep), set(), rep["checks"])
        self.assertEqual(rep["rc"], 0)
        for name in ("seed-fields", "no-generic-leftovers", "mechanics-size", "roster-index",
                     "lore-orphans", "seed-ids", "card-legibility", "presence-matrix",
                     "engine-smoke", "bundled-engine"):
            self.assertEqual(self.status(rep, name), "PASS", rep["by"].get(name))

    def test_smoke_leaves_real_root_untouched(self):
        self.validate()
        self.assertFalse(os.path.exists(os.path.join(self.root, "saves")))
        self.assertFalse(os.path.exists(os.path.join(self.root, "CLAUDE.md")))

    def test_bundled_engine_includes_common(self):
        self.assertTrue(os.path.exists(os.path.join(self.dir, "engine", "scripts", "_common.py")))
        os.remove(os.path.join(self.dir, "engine", "scripts", "_common.py"))
        rep = self.validate()
        self.assertIn("bundled-engine", self.fails(rep))
        self.assertIn("engine-smoke", self.fails(rep))


class SeedChecksTest(ValidateBase):
    def test_empty_seed_fields_fail(self):
        for path in (("meta", "game_title"), ("scene", "location"), ("scene", "summary")):
            with self.subTest(path=path):
                orig = self.r("state.seed.json")
                self.edit_seed(lambda d: d[path[0]].__setitem__(path[1], "  "))
                rep = self.validate()
                self.assertEqual(self.fails(rep), {"seed-fields"})
                self.assertIn(".".join(path), rep["by"]["seed-fields"]["detail"])
                self.w("state.seed.json", orig)

    def test_empty_goals_short_warns_only(self):
        self.edit_seed(lambda d: d["goals"].__setitem__("short", []))
        rep = self.validate()
        self.assertEqual(self.fails(rep), set())
        self.assertEqual(self.status(rep, "seed-goals"), "WARN")

    def test_unknown_affinity_key_fails(self):
        self.edit_seed(lambda d: d["affinity"].__setitem__("ghost", 3))
        rep = self.validate()
        self.assertEqual(self.fails(rep), {"seed-ids"})
        self.assertIn("affinity.ghost", rep["by"]["seed-ids"]["detail"])

    def test_unknown_relationship_key_fails(self):
        self.edit_seed(lambda d: d["relationships"].__setitem__("ghost", {}))
        self.assertEqual(self.fails(self.validate()), {"seed-ids"})

    def test_unknown_present_character_fails_seed_ids(self):
        self.edit_seed(lambda d: d["scene"].__setitem__("present_characters", ["mira", "ghost"]))
        self.assertIn("seed-ids", self.fails(self.validate()))


class LeftoverTests(ValidateBase):
    def test_games_active(self):
        self.w("mechanics.md", MECHANICS + "Read games/ACTIVE first.\n")
        self.assertEqual(self.fails(self.validate()), {"no-generic-leftovers"})

    def test_language_policy_block(self):
        self.w("SKILL.md", SKILL_MD + "\nlanguage_policy:\n  narration: zh\n")
        self.assertEqual(self.fails(self.validate()), {"no-generic-leftovers"})

    def test_rpg_resume_command(self):
        self.w("SKILL.md", SKILL_MD + "\nType `/rpg` to resume.\n")
        self.assertEqual(self.fails(self.validate()), {"no-generic-leftovers"})

    def test_rpg_creator_is_not_a_leftover(self):
        self.w("SKILL.md", SKILL_MD + "\nBuilt with /rpg-creator and skills/rpg-creator.\n")
        self.assertEqual(self.fails(self.validate()), set())

    def test_mechanics_size_warn(self):
        self.w("mechanics.md", "\n".join("line %d" % i for i in range(201)) + "\n")
        rep = self.validate()
        self.assertEqual(self.status(rep, "mechanics-size"), "WARN")
        self.assertEqual(self.fails(rep), set())


class RosterTests(ValidateBase):
    def test_index_row_without_card_fails(self):
        self.w("characters/index.md", INDEX + "| bram | the smith | ally | forge |\n")
        rep = self.validate()
        self.assertEqual(self.fails(rep), {"roster-index"})
        self.assertIn("bram", rep["by"]["roster-index"]["detail"])

    def test_orphan_card_warns(self):
        self.w("characters/cast/extra.md", CARD.format(name="Extra", cid="extra"))
        rep = self.validate()
        self.assertEqual(self.fails(rep), set())
        self.assertEqual(self.status(rep, "roster-index"), "WARN")
        self.assertIn("extra", rep["by"]["roster-index"]["detail"])

    def test_orphan_lore_warns(self):
        self.w("world/lore/lonely.md", "never fires\n")
        rep = self.validate()
        self.assertEqual(self.fails(rep), set())
        self.assertEqual(self.status(rep, "lore-orphans"), "WARN")
        self.assertIn("lonely", rep["by"]["lore-orphans"]["detail"])


class CardTests(ValidateBase):
    def test_missing_age_fails(self):
        self.w("characters/cast/mira.md", CARD.format(name="Mira", cid="mira").replace(
            "- **Age:** 24\n", ""))
        rep = self.validate()
        self.assertEqual(self.fails(rep), {"card-legibility"})
        self.assertIn("mira.md:Age", rep["by"]["card-legibility"]["detail"])

    def test_missing_appearance_in_player_fails(self):
        self.w("characters/player.md", "# Aria\n\n- **Age:** 30\n")
        rep = self.validate()
        self.assertEqual(self.fails(rep), {"card-legibility"})
        self.assertIn("player.md:Appearance", rep["by"]["card-legibility"]["detail"])

    def test_empty_or_placeholder_content_warns(self):
        for old, new in (("- **Age:** 24", "- **Age:**"),
                         ("- **Age:** 24", "- **Age:** TBD"),
                         ("Tall, with red braids and a scarred chin.", "")):
            with self.subTest(new=new):
                self.w("characters/cast/sera.md", CARD.format(name="Sera", cid="sera").replace(old, new))
                rep = self.validate()
                self.assertEqual(self.fails(rep), set())
                self.assertEqual(self.status(rep, "card-legibility"), "WARN")

    def test_label_match_is_tolerant(self):
        text = "# Sera\n\n**age**: 31\n\n### APPEARANCE\nShort and sharp-eyed.\n"
        self.w("characters/cast/sera.md", text)
        self.assertEqual(self.status(self.validate(), "card-legibility"), "PASS")


class PresenceTests(ValidateBase):
    def test_unresolved_name_warns(self):
        self.w("story/main-arc.md", ARC.replace("| 1 | Mira |", "| 1 | Mira + Zorblax |"))
        rep = self.validate()
        self.assertEqual(self.fails(rep), set())
        self.assertEqual(self.status(rep, "presence-matrix"), "WARN")
        self.assertIn("Zorblax", rep["by"]["presence-matrix"]["detail"])
        self.assertNotIn("Sera", rep["by"]["presence-matrix"]["detail"])

    def test_no_matrix_emits_nothing(self):
        self.w("story/main-arc.md", "# Main arc\n\n## Acts\n1. one\n")
        rep = self.validate()
        self.assertNotIn("presence-matrix", rep["by"])
        self.assertEqual(self.fails(rep), set())


class SmokeTests(ValidateBase):
    def test_broken_save_fails_with_step(self):
        write(os.path.join(self.dir, "engine", "scripts", "save.py"),
              "import sys\nsys.stderr.write('boom-save')\nsys.exit(3)\n")
        rep = self.validate()
        self.assertEqual(self.fails(rep), {"engine-smoke"})
        d = rep["by"]["engine-smoke"]["detail"]
        self.assertIn("save --init", d)
        self.assertIn("boom-save", d)

    def test_broken_turn_fails_with_step(self):
        write(os.path.join(self.dir, "engine", "scripts", "turn.py"),
              "import sys\nsys.stderr.write('boom-turn')\nsys.exit(2)\n")
        rep = self.validate()
        self.assertEqual(self.fails(rep), {"engine-smoke"})
        self.assertIn("step turn", rep["by"]["engine-smoke"]["detail"])

    def test_seed_that_breaks_load_fails(self):
        # a seed that is not an object makes save --init fail
        self.w("state.seed.json", "[1, 2]")
        self.assertIn("engine-smoke", self.fails(self.validate()))


class SnapshotTests(ValidateBase):
    def snapshot(self):
        p = subprocess.run([sys.executable, VALIDATE, "--id", GID, "--root", self.root, "--snapshot"],
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        return json.loads(p.stdout)

    def test_snapshot_then_check_clean(self):
        out = self.snapshot()
        self.assertTrue(os.path.exists(out["path"]))
        rep = self.validate("--check-snapshot")
        self.assertEqual(self.status(rep, "snapshot-unchanged"), "PASS")
        self.assertEqual(self.fails(rep), set())

    def test_normal_run_ignores_snapshot_file(self):
        self.snapshot()
        rep = self.validate()
        self.assertNotIn("snapshot-unchanged", rep["by"])
        self.assertEqual(self.fails(rep), set())
        self.assertEqual(self.status(rep, "no-placeholders"), "PASS")

    def test_changes_are_listed(self):
        self.snapshot()
        self.w("mechanics.md", MECHANICS + "extra rule\n")
        self.w("characters/cast/new.md", CARD.format(name="New", cid="new"))
        os.remove(os.path.join(self.dir, "world", "lore", "grey-fog.md"))
        self.w("SKILL.md", SKILL_MD.replace("name: demo", "name: demo-polished"))
        rep = self.validate("--check-snapshot")
        self.assertIn("snapshot-unchanged", self.fails(rep))
        d = rep["by"]["snapshot-unchanged"]["detail"]
        for frag in ("changed: mechanics.md", "added: characters/cast/new.md",
                     "removed: world/lore/grey-fog.md", "demo-polished"):
            self.assertIn(frag, d)

    def test_skill_md_body_edit_is_allowed(self):
        self.snapshot()
        self.w("SKILL.md", SKILL_MD + "\nMore polish text.\n")
        self.assertEqual(self.status(self.validate("--check-snapshot"), "snapshot-unchanged"), "PASS")

    def test_check_without_snapshot_fails(self):
        self.assertIn("snapshot-unchanged", self.fails(self.validate("--check-snapshot")))


if __name__ == "__main__":
    unittest.main()
