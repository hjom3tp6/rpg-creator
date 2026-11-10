"""Tests for scripts/scorecard.py: cast_pattern from the Design DNA + no-DNA compatibility."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.normpath(os.path.join(HERE, ".."))
SCORECARD = os.path.join(SKILL, "scripts", "scorecard.py")
GID = "demo"

INDEX = """\
# Character Index

| id | one-liner | role | usual location |
|----|-----------|------|----------------|
| ann | Ann, a smuggler | ally | docks |
| bo | Bo, a priest | rival | temple |
| cy | Cy, a clerk | antagonist | archive |
"""

LORE = """\
| id | title | keywords | hint | public |
|----|-------|----------|------|--------|
| a | A | a | a | yes |
| b | B | b | b | no |
"""

MATRIX = """\
## Presence Matrix (who is on stage in which beat)
| beat | on stage (besides player) |
|------|---------------------------|
| ch1 | Ann + Bo |
| ch2 | Ann |
| ch3 | Bo |
| ch4 | Cy + Ann |
| climax | everyone |
"""

OLD_ARC = """\
# Main Arc — Old

## The Spine (where this is all going)
A spine.

## Acts
1. **One** — a
2. **Two** — b
3. **Three** — c

%s
## Ticking Clocks
- the eclipse in nine days
- the debt comes due

## Antagonist / Off-screen Mover
Someone.
""" % MATRIX


def new_arc(dna_lines):
    return """\
# Main Arc — New

## Design DNA
<!-- comment line -->
%s

## The Spine (where this is all going)
A spine.

## Phases
1. **The job** — a
2. **The crew** — b
3. **Legwork** — c
4. **Execution** — d

%s
## Pressure
- the window: the gala night
- heat

## Opposition
The house.
""" % ("\n".join(dna_lines), MATRIX)


class ScorecardTest(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.root = self._td.name
        self.dir = os.path.join(self.root, ".claude", "skills", GID)
        for rel, text in (("characters/index.md", INDEX), ("world/lore-index.md", LORE)):
            self.write(rel, text)

    def tearDown(self):
        self._td.cleanup()

    def write(self, rel, text):
        path = os.path.join(self.dir, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    def score(self, arc):
        self.write("story/main-arc.md", arc)
        p = subprocess.run([sys.executable, SCORECARD, "--id", GID, "--root", self.root],
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        out = json.loads(p.stdout)
        self.assertEqual(out["_status"], "ok")
        return out

    def test_no_dna_backward_compatible(self):
        out = self.score(OLD_ARC)
        self.assertIsNone(out["design_dna"])
        self.assertEqual(out["cast_pattern"], "rotating")
        self.assertEqual(out["structure"], {"acts": 3, "ticking_clocks": 2, "beats": 5})
        self.assertEqual(out["characters"]["named_total"], 4)
        self.assertEqual(out["lore"], {"lore_entries": 2, "hidden_secrets": 1})
        flags = out["measurable_flags"]
        self.assertIs(flags["rotation_floor_met"], True)        # 5 distinct >= 4 named
        self.assertIs(flags["everyone_gets_solo_time"], False)  # cy never solo
        self.assertIs(flags["full_cast_reserved_for_climax"], True)
        self.assertIn("_rotation_floor", flags)
        self.assertNotIn("_not_applicable", flags)
        self.assertEqual(out["ensemble"]["tokens_without_solo_beat"], ["cy"])

    def test_rotating_dna(self):
        out = self.score(new_arc(["- structure: conspiracy-mystery", "- cast_pattern: rotating",
                                  "- opposition: institution"]))
        self.assertEqual(out["design_dna"]["structure"], "conspiracy-mystery")
        self.assertEqual(out["design_dna"]["opposition"], "institution")
        self.assertEqual(out["cast_pattern"], "rotating")
        self.assertEqual(out["_cast_pattern_source"], "design_dna")
        self.assertEqual(out["structure"], {"phases": 4, "pressure_sources": 2, "beats": 5})
        flags = out["measurable_flags"]
        self.assertIs(flags["rotation_floor_met"], True)
        self.assertIs(flags["everyone_gets_solo_time"], False)
        self.assertNotIn("_not_applicable", flags)

    def test_fixed_party_dna_marks_rotation_flags_not_applicable(self):
        out = self.score(new_arc(["- structure: heist", "- cast_pattern: fixed-party",
                                  "- ending: {{ending shape}}"]))
        self.assertEqual(out["cast_pattern"], "fixed-party")
        self.assertNotIn("ending", out["design_dna"])  # placeholder skipped
        flags = out["measurable_flags"]
        for k in ("rotation_floor_met", "everyone_gets_solo_time",
                  "full_cast_reserved_for_climax"):
            self.assertIsNone(flags[k])
        self.assertIn("fixed-party", flags["_not_applicable"])
        self.assertIn("spotlight", flags["_not_applicable"])
        self.assertEqual(out["ensemble"]["distinct_subcasts"], 5)  # counts still reported

    def test_cast_pattern_falls_back_to_structure_file(self):
        out = self.score(new_arc(["- structure: time-loop"]))
        self.assertEqual(out["cast_pattern"], "solo")
        self.assertEqual(out["_cast_pattern_source"], "story-structures/time-loop.md")
        self.assertIsNone(out["measurable_flags"]["rotation_floor_met"])

    def test_placeholder_only_dna_treated_as_rotating(self):
        out = self.score(new_arc(["- structure: {{structure}}",
                                  "- cast_pattern: {{rotating|fixed-party|solo|revolving}}"]))
        self.assertIsNone(out["design_dna"])
        self.assertEqual(out["cast_pattern"], "rotating")
        self.assertIs(out["measurable_flags"]["rotation_floor_met"], True)


if __name__ == "__main__":
    unittest.main()
