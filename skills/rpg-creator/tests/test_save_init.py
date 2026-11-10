"""Tests for engine/scripts/save.py --init / --set (stdlib unittest)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SAVE = os.path.join(HERE, "..", "engine", "scripts", "save.py")
GID = "demo"
SEED = {"meta": {"game_id": GID, "created": "", "last_played": ""},
        "player": {"name": "", "description": ""}, "affinity": {}, "flags": {}}


def run(root, *args, stdin=""):
    p = subprocess.run([sys.executable, SAVE, "--game", GID, "--root", root, *args],
                       input=stdin, capture_output=True, text=True, timeout=30)
    return p.returncode, json.loads(p.stdout.strip().splitlines()[-1])


class SaveInitTest(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.root = self._td.name
        self.seed = os.path.join(self.root, "seed.json")
        with open(self.seed, "w", encoding="utf-8") as f:
            json.dump(SEED, f)
        self.state = os.path.join(self.root, "saves", GID, "state.json")

    def tearDown(self):
        self._td.cleanup()

    def load(self):
        with open(self.state, encoding="utf-8") as f:
            return json.load(f)

    def test_init_copies_seed_and_stamps(self):
        rc, out = run(self.root, "--init", "--seed", self.seed)
        self.assertEqual(rc, 0)
        self.assertEqual(out["_status"], "initialized")
        st = self.load()
        self.assertTrue(st["meta"]["created"])
        self.assertTrue(st["meta"]["last_played"])
        self.assertEqual(st["meta"]["game_id"], GID)
        self.assertFalse(os.path.exists(self.state + ".tmp"))

    def test_init_with_set_and_json_parsing(self):
        rc, _ = run(self.root, "--init", "--seed", self.seed,
                    "--set", "player.name=Aria", "--set", "affinity.mira=7",
                    "--set", "flags.met=true", "--set", "player.description=a \"quiet\" one",
                    "--set", "meta.note=007x")
        self.assertEqual(rc, 0)
        st = self.load()
        self.assertEqual(st["player"]["name"], "Aria")
        self.assertEqual(st["affinity"]["mira"], 7)
        self.assertIs(st["flags"]["met"], True)
        self.assertEqual(st["player"]["description"], 'a "quiet" one')
        self.assertEqual(st["meta"]["note"], "007x")

    def test_init_refuses_existing_unless_force(self):
        run(self.root, "--init", "--seed", self.seed, "--set", "player.name=A")
        rc, out = run(self.root, "--init", "--seed", self.seed, "--set", "player.name=B")
        self.assertEqual(rc, 1)
        self.assertEqual(out["_status"], "exists")
        self.assertEqual(self.load()["player"]["name"], "A")
        rc, out = run(self.root, "--init", "--seed", self.seed, "--force",
                      "--set", "player.name=B")
        self.assertEqual(rc, 0)
        self.assertEqual(self.load()["player"]["name"], "B")

    def test_missing_or_invalid_seed(self):
        rc, out = run(self.root, "--init", "--seed", os.path.join(self.root, "nope.json"))
        self.assertEqual((rc, out["_status"]), (1, "error"))
        self.assertFalse(os.path.exists(self.state))
        bad = os.path.join(self.root, "bad.json")
        with open(bad, "w") as f:
            f.write("{not json")
        rc, out = run(self.root, "--init", "--seed", bad)
        self.assertEqual((rc, out["_status"]), (1, "error"))

    def test_default_seed_path_is_relative_to_engine(self):
        # Mimic a baked game: <game>/engine/scripts/save.py + <game>/state.seed.json
        import shutil
        game = os.path.join(self.root, "game")
        os.makedirs(os.path.join(game, "engine", "scripts"))
        for name in ("save.py", "_common.py"):
            shutil.copy(os.path.join(os.path.dirname(SAVE), name),
                        os.path.join(game, "engine", "scripts", name))
        shutil.copy(self.seed, os.path.join(game, "state.seed.json"))
        p = subprocess.run([sys.executable, os.path.join(game, "engine", "scripts", "save.py"),
                            "--game", GID, "--root", self.root, "--init",
                            "--set", "player.name=Z"], capture_output=True, text=True,
                           input=None, stdin=subprocess.DEVNULL, timeout=30)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(self.load()["player"]["name"], "Z")

    def test_set_without_init_does_not_read_stdin(self):
        run(self.root, "--init", "--seed", self.seed)
        p = subprocess.run([sys.executable, SAVE, "--game", GID, "--root", self.root,
                            "--set", "flags.x=1"], stdin=subprocess.DEVNULL,
                           capture_output=True, text=True, timeout=30)
        self.assertEqual(p.returncode, 0, p.stdout)
        self.assertEqual(self.load()["flags"]["x"], 1)

    def test_patch_then_set_and_plain_patch_unchanged(self):
        run(self.root, "--init", "--seed", self.seed)
        rc, out = run(self.root, "--patch", '{"affinity":{"a":1},"flags":{"f":1}}',
                      "--set", "affinity.a=5")
        self.assertEqual(rc, 0)
        self.assertEqual(out["_status"], "saved")
        st = self.load()
        self.assertEqual(st["affinity"]["a"], 5)
        self.assertEqual(st["flags"]["f"], 1)
        rc, out = run(self.root, stdin='{"flags":{"g":2}}')
        self.assertEqual(rc, 0)
        self.assertEqual(self.load()["flags"], {"f": 1, "g": 2})

    def test_bad_set_arg(self):
        rc, out = run(self.root, "--init", "--seed", self.seed, "--set", "noequals")
        self.assertEqual((rc, out["_status"]), (1, "error"))


if __name__ == "__main__":
    unittest.main()
