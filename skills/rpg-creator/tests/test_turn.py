"""Tests for engine/scripts/turn.py (stdlib unittest)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TURN = os.path.join(HERE, "..", "engine", "scripts", "turn.py")
GID = "demo"


def run_turn(root, payload, game=GID, extra=()):
    p = subprocess.run(
        [sys.executable, TURN, "--game", game, "--title", "Demo Game",
         "--resume-cmd", "/demo", "--root", root, *extra],
        input=json.dumps(payload), capture_output=True, text=True)
    out = json.loads(p.stdout.strip().splitlines()[-1])
    return p.returncode, out


class TurnTest(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.root = self._td.name
        self.sdir = os.path.join(self.root, "saves", GID)
        os.makedirs(self.sdir)
        self.seed({
            "meta": {"game_title": "Demo Game"},
            "scene": {"location": "Harbor", "present_characters": ["mira"],
                      "summary": "Fog rolls in."},
            "clock": {"day": 3, "phase": "evening", "deadlines": ["ship leaves Day 5"]},
            "goals": {"_comment": "x", "short": ["find the key"], "mid": [], "long": []},
            "affinity": {"mira": 10},
            "relationships": {"mira": {"stage": "wary"}},
            "flags": {},
        })

    def tearDown(self):
        self._td.cleanup()

    def seed(self, state):
        with open(os.path.join(self.sdir, "state.json"), "w") as f:
            json.dump(state, f)

    def state(self):
        with open(os.path.join(self.sdir, "state.json")) as f:
            return json.load(f)

    def read(self, name, base=None):
        with open(os.path.join(base or self.sdir, name), encoding="utf-8") as f:
            return f.read()

    def test_no_save(self):
        rc, out = run_turn(self.root, {"beat": "x"}, game="ghost")
        self.assertEqual(rc, 1)
        self.assertEqual(out["_status"], "no_save")

    def test_requires_patch_or_beat(self):
        rc, out = run_turn(self.root, {"threads": ["a"]})
        self.assertEqual(rc, 1)
        self.assertEqual(out["_status"], "error")

    def test_patch_merge_and_threads(self):
        rc, out = run_turn(self.root, {
            "patch": {"affinity": {"mira": 12}, "flags": {"spared": True}},
            "threads": ["who sent the letter?"]})
        self.assertEqual(rc, 0)
        s = self.state()
        self.assertEqual(s["affinity"]["mira"], 12)
        self.assertTrue(s["flags"]["spared"])
        self.assertEqual(s["scene"]["location"], "Harbor")
        self.assertIn("last_played", s["meta"])
        self.assertEqual(s["threads"], ["who sent the letter?"])
        # threads persist on a turn that doesn't resend them
        run_turn(self.root, {"beat": "b"})
        self.assertIn("who sent the letter?", self.read("recap.md"))

    def test_beat_header_and_recap(self):
        rc, out = run_turn(self.root, {"beat": "Mira hands over a rusty key."})
        self.assertEqual(rc, 0)
        log = self.read("session-log.md")
        self.assertIn("### Day 3 · evening · Harbor", log)
        self.assertIn("Mira hands over a rusty key.", log)
        recap = self.read("recap.md")
        for needle in ("Harbor", "Fog rolls in.", "find the key", "Mira hands over",
                       "mira (affinity 10, stage wary)", "ship leaves Day 5"):
            self.assertIn(needle, recap)
        self.assertLessEqual(len(recap.splitlines()), 30)
        self.assertEqual(out["_status"], "ok")
        self.assertFalse(out["needs_rotation"])
        self.assertNotIn("oldest_block", out)

    def test_unlock_idempotent(self):
        u = {"unlock": [{"id": "grey-fog", "title": "Grey Fog", "note": "n"}], "beat": "b"}
        _, out1 = run_turn(self.root, u)
        _, out2 = run_turn(self.root, u)
        self.assertEqual(out1["newly_unlocked"], ["grey-fog"])
        self.assertEqual(out2["newly_unlocked"], [])
        codex = self.read("codex.md")
        self.assertEqual(codex.count("<!-- codex:grey-fog -->"), 1)
        self.assertIn("## Grey Fog", codex)

    def test_claude_md_not_rewritten(self):
        cmd = os.path.join(self.root, "CLAUDE.md")
        with open(cmd, "w", encoding="utf-8") as f:
            f.write("# My project\n\nkeep me\n")
        run_turn(self.root, {"beat": "one"})
        first = self.read("CLAUDE.md", self.root)
        self.assertIn("keep me", first)
        self.assertIn("<!-- rpg:active-game -->", first)
        os.utime(cmd, (1000, 1000))
        run_turn(self.root, {"beat": "two"})
        self.assertEqual(self.read("CLAUDE.md", self.root), first)
        self.assertEqual(os.stat(cmd).st_mtime, 1000)

    def test_rotation(self):
        log = os.path.join(self.sdir, "session-log.md")
        with open(log, "w") as f:
            f.write("".join(f"line {i}\n" for i in range(300)))
        rc, out = run_turn(self.root, {"beat": "late"})
        self.assertTrue(out["needs_rotation"])
        self.assertEqual(out["log_lines"], out["trim_lines"] + 120)
        self.assertTrue(out["oldest_block"].startswith("line 0\n"))
        self.assertEqual(out["oldest_block"].count("\n"), out["trim_lines"])

    def test_rotation_snaps_to_beat_header(self):
        log = os.path.join(self.sdir, "session-log.md")
        with open(log, "w") as f:
            f.write("".join(f"### Day {i}\nbeat a\nbeat b\n" for i in range(100)))
        rc, out = run_turn(self.root, {"beat": "late"})
        self.assertTrue(out["needs_rotation"])
        self.assertEqual(out["trim_lines"] % 3, 0)  # cut lands on a "### " header
        self.assertGreaterEqual(out["log_lines"] - out["trim_lines"], 120)

    def test_odd_state(self):
        self.seed({"scene": "weird", "clock": [1], "goals": ["a"], "affinity": [],
                   "relationships": 5, "flags": None, "threads": 7,
                   "meta": "bad",
                   "spirit": {"_comment": "c", "potency": 3},
                   "bigblock": {"x": "y" * 400},
                   "mod": None})
        rc, out = run_turn(self.root, {"beat": "ok", "patch": {"scene": {"x": 1}}})
        self.assertEqual(rc, 0, out)
        recap = self.read("recap.md")
        self.assertIn('"potency":3', recap)
        self.assertNotIn("bigblock", recap)
        self.assertNotIn("_comment", recap)
        # missing everything
        self.seed({})
        rc, out = run_turn(self.root, {"beat": "ok"})
        self.assertEqual(rc, 0, out)
        self.assertIn("### Turn", self.read("session-log.md"))


if __name__ == "__main__":
    unittest.main()
