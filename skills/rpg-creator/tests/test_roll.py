"""Tests for scripts/roll.py and the story-structures/ <-> variation-tables.json contract."""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.normpath(os.path.join(HERE, ".."))
ROLL = os.path.join(SKILL, "scripts", "roll.py")
TABLES = os.path.join(SKILL, "assets", "variation-tables.json")
STRUCTURES = os.path.join(SKILL, "story-structures")
CAST_PATTERNS = {"rotating", "fixed-party", "solo", "revolving"}


def load_tables():
    with open(TABLES, encoding="utf-8") as f:
        return json.load(f)


def structure_files():
    return {fn[:-3] for fn in os.listdir(STRUCTURES)
            if fn.endswith(".md") and fn.lower() != "readme.md"}


def values(combo):
    for axis, v in combo.items():
        for x in (v if isinstance(v, list) else [v]):
            yield "%s=%s" % (axis, x)


class RollTest(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.root = self._td.name

    def tearDown(self):
        self._td.cleanup()

    def roll(self, *args, expect=0):
        p = subprocess.run([sys.executable, ROLL, "--root", self.root, *args],
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(p.returncode, expect, p.stdout + p.stderr)
        return json.loads(p.stdout)

    def fake_game(self, gid, dna_lines):
        d = os.path.join(self.root, ".claude", "skills", gid, "story")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "main-arc.md"), "w", encoding="utf-8") as f:
            f.write("# Main Arc — %s\n\n## Design DNA\n%s\n\n## The Spine\nx\n"
                    % (gid, "\n".join(dna_lines)))

    def test_seed_reproducible(self):
        a = self.roll("--seed", "42", "--count", "3")
        b = self.roll("--seed", "42", "--count", "3")
        self.assertEqual(a["_status"], "ok")
        self.assertEqual(a["seed"], 42)
        self.assertEqual(a["combos"], b["combos"])
        self.assertEqual(len(a["combos"]), 3)
        self.assertIsInstance(self.roll()["seed"], int)  # unseeded run echoes its seed

    def test_combo_shape(self):
        tables = load_tables()
        out = self.roll("--seed", "3", "--count", "4")
        for combo in out["combos"]:
            self.assertEqual(set(combo), set(tables["axes"]) | {"cast_pattern"})
            self.assertIn(combo["cast_pattern"], CAST_PATTERNS)
            drives = combo["drives"]
            self.assertEqual(len(drives), tables["axes"]["drives"]["pick"])
            self.assertEqual(len(set(drives)), len(drives))
            self.assertIn(combo["structure"], out["glossary"]["structure"])
        for axis in load_tables()["high_impact"]:  # alternatives differ on high-impact axes
            vals = [c[axis] for c in out["combos"]]
            self.assertEqual(len(set(vals)), len(vals), axis)

    def test_lock_honoured(self):
        out = self.roll("--seed", "5", "--count", "4", "--lock", "setting=high-fantasy",
                        "--lock", "tone=wry-comedic", "--lock", "drives=debt",
                        "--lock", "relationship=a bickering duo of cartographers")
        for combo in out["combos"]:
            self.assertEqual(combo["setting"], "high-fantasy")
            self.assertEqual(combo["tone"], "wry-comedic")
            self.assertIn("debt", combo["drives"])
            self.assertEqual(combo["relationship"], "a bickering duo of cartographers")
        self.assertEqual(out["locked"]["setting"], "high-fantasy")
        self.assertEqual(out["custom_locks"], ["relationship=a bickering duo of cartographers"])

    def test_lock_structure_and_cast_override(self):
        out = self.roll("--seed", "1", "--lock", "structure=heist")
        self.assertTrue(all(c["structure"] == "heist" for c in out["combos"]))
        self.assertTrue(all(c["cast_pattern"] == "fixed-party" for c in out["combos"]))
        out = self.roll("--seed", "1", "--lock", "structure=heist", "--lock", "cast_pattern=solo")
        self.assertTrue(all(c["cast_pattern"] == "solo" for c in out["combos"]))

    def test_bad_locks_rejected(self):
        self.assertEqual(self.roll("--lock", "structure=nope", expect=1)["_status"], "error")
        self.assertEqual(self.roll("--lock", "colour=red", expect=1)["_status"], "error")
        self.assertEqual(self.roll("--lock", "noequals", expect=1)["_status"], "error")
        self.assertEqual(self.roll("--lock", "cast_pattern=crowd", expect=1)["_status"], "error")

    def test_avoid_recent_skips_used_structure(self):
        self.fake_game("old-heist", ["- structure: heist", "- cast_pattern: fixed-party",
                                     "- setting: High fantasy (D&D-style)",
                                     "- opposition: {{opposition}}"])
        for seed in range(25):
            out = self.roll("--seed", str(seed), "--count", "5")
            for combo in out["combos"]:
                self.assertNotEqual(combo["structure"], "heist")
                self.assertNotEqual(combo["setting"], "high-fantasy")
        self.assertEqual(out["recent_games"], ["old-heist"])
        avoided = {(a["axis"], a["value"]) for a in out["avoided"]}
        self.assertEqual(avoided, {("structure", "heist"), ("setting", "high-fantasy")})
        self.assertIn("old-heist", out["avoided"][0]["why"])
        # a lock beats avoidance; --no-avoid-recent turns the scan off
        locked = self.roll("--seed", "0", "--lock", "structure=heist")
        self.assertTrue(all(c["structure"] == "heist" for c in locked["combos"]))
        off = self.roll("--seed", "0", "--no-avoid-recent")
        self.assertEqual((off["avoided"], off["recent_games"]), ([], []))
        seen = set()
        for seed in range(40):
            seen.update(c["structure"] for c in
                        self.roll("--seed", str(seed), "--count", "5",
                                  "--no-avoid-recent")["combos"])
        self.assertIn("heist", seen)

    def test_incompatible_pairs_never_returned(self):
        bad = [frozenset(p) for p in load_tables()["incompatible"]]
        self.assertTrue(bad)
        runs = [("--count", "6")] + [("--count", "6", "--lock", "structure=" + s) for s in
                                     ("seasons-of-a-community", "doomed-cause", "revenge")]
        for extra in runs:
            for seed in range(40):
                for combo in self.roll("--seed", str(seed), *extra)["combos"]:
                    vals = set(values(combo))
                    for pair in bad:
                        self.assertFalse(pair <= vals, "%s in %s" % (sorted(pair), combo))


class TablesContractTest(unittest.TestCase):
    def test_structures_match_tables(self):
        tables = load_tables()
        self.assertEqual(set(tables["axes"]["structure"]["values"]), structure_files())

    def test_every_structure_has_valid_cast_pattern(self):
        for name in structure_files():
            with open(os.path.join(STRUCTURES, name + ".md"), encoding="utf-8") as f:
                m = re.search(r"^cast_pattern:\s*(\S+)\s*$", f.read(), re.MULTILINE)
            self.assertTrue(m, "%s.md has no cast_pattern line" % name)
            self.assertIn(m.group(1), CAST_PATTERNS, name)

    def test_readme_indexes_every_structure(self):
        with open(os.path.join(STRUCTURES, "README.md"), encoding="utf-8") as f:
            readme = f.read()
        for name in structure_files():
            self.assertIn("`%s`" % name, readme)

    def test_tables_well_formed(self):
        tables = load_tables()
        for axis, spec in tables["axes"].items():
            self.assertGreaterEqual(len(spec["values"]), 8, axis)
            self.assertLessEqual(len(spec["values"]), 15, axis)
        for axis in tables["high_impact"]:
            self.assertIn(axis, tables["axes"])
        for pair in tables["incompatible"]:
            self.assertEqual(len(pair), 2)
            for item in pair:
                axis, vid = item.split("=", 1)
                self.assertIn(vid, tables["axes"][axis]["values"], item)


if __name__ == "__main__":
    unittest.main()
