"""Tests for scripts/compile.py --title / --modules (stdlib unittest)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.normpath(os.path.join(HERE, ".."))
COMPILE = os.path.join(SKILL, "scripts", "compile.py")
ASSETS = os.path.join(SKILL, "assets")
GID = "demo"
TITLE = "Demo Game"


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class CompileTest(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.root = self._td.name
        self.dir = os.path.join(self.root, ".claude", "skills", GID)

    def tearDown(self):
        self._td.cleanup()

    def compile(self, *args, gid=GID, expect=0):
        p = subprocess.run([sys.executable, COMPILE, "--id", gid, "--root", self.root, *args],
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(p.returncode, expect, p.stdout + p.stderr)
        return json.loads(p.stdout)

    def f(self, rel):
        return read(os.path.join(self.dir, rel))

    def seed(self):
        return json.loads(self.f("state.seed.json"))

    def test_no_flags_only_substitutes_id(self):
        out = self.compile()
        self.assertEqual(out["_status"], "scaffolded")
        for rel, tpl in (("SKILL.md", "game-skill-SKILL.template.md"),
                         ("mechanics.md", "mechanics.template.md")):
            self.assertEqual(self.f(rel), read(os.path.join(ASSETS, tpl)).replace("{{id}}", GID))
        self.assertNotIn("{{id}}", self.f("SKILL.md"))
        self.assertIn("{{Title}}", self.f("SKILL.md"))
        # seed and stubs are byte-identical to the templates
        self.assertEqual(self.f("state.seed.json"),
                         read(os.path.join(ASSETS, "state.template.json")))
        self.assertIn("{{Title}}", self.f("story/main-arc.md"))

    def test_title_only(self):
        self.compile("--title", TITLE)
        skill = self.f("SKILL.md")
        self.assertNotIn("{{id}}", skill)
        self.assertNotIn("{{Title}}", skill)
        self.assertNotIn("{{Title}}", self.f("mechanics.md"))
        self.assertIn("# Main Arc — " + TITLE, self.f("story/main-arc.md"))
        meta = self.seed()["meta"]
        self.assertEqual((meta["game_id"], meta["game_title"]), (GID, TITLE))
        # lore-index's {{Title}} is a column example: untouched
        self.assertIn("{{Title}}", self.f("world/lore-index.md"))
        # creative placeholders untouched; modules untouched without --modules
        self.assertIn("{{premise in one clause}}", skill)
        self.assertIn("### {{romance}} (if active)", self.f("mechanics.md"))
        self.assertIn("drift", self.seed())

    def test_modules_library_subset(self):
        out = self.compile("--title", TITLE, "--modules", "romance,drift")
        mech = self.f("mechanics.md")
        self.assertIn("### romance", mech)
        self.assertIn("### drift", mech)
        self.assertNotIn("magic-potency", mech)
        self.assertNotIn("language-coaching", mech)
        self.assertNotIn("custom module", mech)
        self.assertNotIn("(if active)", mech)
        self.assertIn("## Golden rules", mech)
        self.assertIn("{{Disposition/affinity tiers", mech)  # body placeholder kept
        self.assertIn("drift", self.seed())
        skill = self.f("SKILL.md")
        self.assertIn("**Active mechanics:** romance · drift", skill)
        self.assertIn("Accrue drift.pressure", skill)
        self.assertNotIn("If drift active", skill)
        self.assertNotIn("coaching note if coaching is on", skill)
        self.assertNotIn("{{+ any module", skill)
        self.assertFalse([a for a in out["fill"] if "not found" in a], out["fill"])

    def test_modules_without_drift_or_coaching_and_custom(self):
        self.compile("--modules", "language-coaching,combat-dice")
        mech = self.f("mechanics.md")
        self.assertIn("### language-coaching", mech)
        self.assertIn("### combat-dice", mech)
        self.assertNotIn("### romance", mech)
        self.assertNotIn("### {{romance}}", mech)
        self.assertNotIn("### drift", mech)
        self.assertNotIn("### {{custom module}}", mech)
        self.assertIn("{{Distill the ruling", mech)
        self.assertNotIn("drift", self.seed())
        skill = self.f("SKILL.md")
        self.assertIn("language-coaching · combat-dice", skill)
        self.assertIn("coaching note", skill)
        self.assertNotIn("{{+ any module", skill)
        self.assertNotIn("drift.pressure", skill)
        self.assertIn("{{Title}}", skill)  # no --title given

    def test_empty_modules_removes_everything(self):
        self.compile("--modules", "")
        mech = self.f("mechanics.md")
        self.assertNotIn("(if active)", mech)
        self.assertNotIn("### ", mech.split("## Modules")[1].split("## Golden")[0])
        self.assertNotIn("drift", self.seed())

    def test_from_scaffold(self):
        self.compile("--title", "Src Game", "--modules", "romance,drift", gid="src")
        src = os.path.join(".claude", "skills", "src")
        self.compile("--from", src, "--title", TITLE, "--modules", "romance")
        self.assertEqual(self.seed()["meta"]["game_id"], GID)
        self.assertEqual(self.seed()["meta"]["game_title"], TITLE)
        self.assertNotIn("drift", self.seed())
        self.assertNotIn("{{Title}}", self.f("SKILL.md"))

    def test_update_engine_rejects_flags_and_bad_title(self):
        self.compile()
        self.compile("--update-engine", "--title", "X", expect=1)
        self.compile("--title", 'Bad "Title"', gid="other", expect=1)

    def test_structure_valid_fills_design_dna(self):
        out = self.compile("--title", TITLE, "--structure", "time-loop")
        self.assertEqual(out["structure"], "time-loop")
        arc = self.f("story/main-arc.md")
        self.assertIn("## Design DNA", arc)
        self.assertIn("- structure: time-loop\n", arc)
        self.assertIn("- cast_pattern: solo\n", arc)
        self.assertIn("- opposition: {{opposition}}", arc)  # other axes left for the author
        self.assertIn("## Phases", arc)
        self.assertIn("## Presence Matrix", arc)
        self.assertNotIn("{{structure", arc)
        self.assertTrue(any("Design DNA" in a for a in out["fill"]), out["fill"])

    def test_structure_invalid_rejected(self):
        out = self.compile("--structure", "space-opera-saga", expect=1)
        self.assertEqual(out["_status"], "error")
        self.assertIn("heist", out["message"])  # lists the valid names
        self.assertFalse(os.path.exists(self.dir))
        self.compile()
        self.compile("--update-engine", "--structure", "heist", expect=1)

    def test_no_structure_leaves_dna_placeholders(self):
        out = self.compile()
        self.assertIsNone(out["structure"])
        self.assertIn("- structure: {{structure", self.f("story/main-arc.md"))

    def test_structure_on_fork_without_dna_adds_block(self):
        self.compile(gid="src")
        src_arc = os.path.join(self.root, ".claude", "skills", "src", "story", "main-arc.md")
        with open(src_arc, "w", encoding="utf-8") as fh:
            fh.write("# Main Arc — Old\n\n## Acts\n1. **One** — a\n")
        self.compile("--from", os.path.join(".claude", "skills", "src"), "--structure", "heist")
        arc = self.f("story/main-arc.md")
        self.assertIn("## Design DNA\n- structure: heist\n- cast_pattern: fixed-party\n", arc)
        self.assertIn("## Acts", arc)

    def test_existing_files_not_touched(self):
        self.compile()
        skill_before = self.f("SKILL.md")
        out = self.compile("--title", TITLE, "--modules", "romance")
        self.assertEqual(out["actions"]["SKILL.md"], "skipped (exists)")
        self.assertEqual(self.f("SKILL.md"), skill_before)


if __name__ == "__main__":
    unittest.main()
