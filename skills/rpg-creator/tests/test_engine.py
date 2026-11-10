"""Tests for engine cleanup: _common, required --game, _cold hot view, neutral strings (stdlib unittest)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.normpath(os.path.join(HERE, ".."))
SCRIPTS = os.path.join(SKILL, "engine", "scripts")
COMPILE = os.path.join(SKILL, "scripts", "compile.py")
GID = "demo"
ALL = ("save.py", "load.py", "checkpoint.py", "codex.py", "rotate_log.py", "turn.py")

STATE = {
    "meta": {"game_id": GID, "game_title": "Demo"},
    "player": {"name": "Aria", "description": "long prose", "persona_file": "characters/player.md"},
    "scene": {"location": "Gate", "present_characters": ["mira"], "summary": "dawn"},
    "goals": {"_comment": "x", "short": ["a"], "mid": ["b", "c"], "long": ["d"]},
    "drift": {"pressure": 3, "ledger": [1, 2, 3], "pending_seeds": [1]},
    "relationships": {"mira": {"stage": "x", "notes": "n", "suspects": ["s"], "trust": 5},
                      "sera": {"stage": "y", "notes": "n2"}},
    "red_tape": {"stamp": 2, "history": ["h1", "h2"]},
    "spirit_tongue": {"level": 1, "notable_castings": ["c1"]},
    "_cold": ["red_tape.history"],
}


def run(script, *args, cwd=None, stdin=""):
    return subprocess.run([sys.executable, script, *args], capture_output=True, text=True,
                          input=stdin, timeout=60, cwd=cwd)


def last_json(p):
    return json.loads(p.stdout.strip().splitlines()[-1])


class EngineBase(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.root = self._td.name

    def tearDown(self):
        self._td.cleanup()

    def script(self, name, *args, **kw):
        return run(os.path.join(SCRIPTS, name), "--game", GID, "--root", self.root, *args, **kw)

    def write_state(self, state):
        d = os.path.join(self.root, "saves", GID)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "state.json"), "w", encoding="utf-8") as f:
            json.dump(state, f)

    def hot(self):
        p = self.script("load.py", "--hot")
        self.assertEqual(p.returncode, 0, p.stderr)
        return json.loads(p.stdout)


class GameRequiredTest(EngineBase):
    def test_every_script_requires_game(self):
        for name in ALL:
            with self.subTest(script=name):
                p = run(os.path.join(SCRIPTS, name), "--root", self.root, stdin="{}")
                self.assertNotEqual(p.returncode, 0)
                self.assertIn("--game", p.stderr)

    def test_no_legacy_references(self):
        for name in ALL + ("_common.py",):
            with open(os.path.join(SCRIPTS, name), encoding="utf-8") as f:
                text = f.read()
            for bad in ("games/ACTIVE", "cartridge", "legacy single-game"):
                self.assertNotIn(bad, text, "%s mentions %s" % (name, bad))

    def test_games_active_file_is_ignored(self):
        os.makedirs(os.path.join(self.root, "games"))
        with open(os.path.join(self.root, "games", "ACTIVE"), "w") as f:
            f.write("other")
        self.write_state(STATE)
        self.assertEqual(self.hot()["meta"]["game_id"], GID)

    def test_saves_dir_helper(self):
        sys.path.insert(0, SCRIPTS)
        try:
            import _common
        finally:
            sys.path.pop(0)
        self.assertEqual(_common.saves_dir("/r", "g"), os.path.join("/r", "saves", "g"))
        with self.assertRaises(ValueError):
            _common.saves_dir("/r", "")


class HotViewTest(EngineBase):
    def test_defaults_and_cold_list(self):
        self.write_state(STATE)
        hot = self.hot()
        self.assertEqual(hot["_view"], "hot")
        # built-in defaults
        self.assertNotIn("description", hot["player"])
        self.assertNotIn("persona_file", hot["player"])
        self.assertEqual(hot["goals"]["mid_count"], 2)
        self.assertEqual(hot["goals"]["long_count"], 1)
        self.assertNotIn("_comment", hot["goals"])
        self.assertEqual(hot["drift"]["ledger_count"], 3)
        self.assertEqual(hot["drift"]["pending_seeds_count"], 1)
        self.assertEqual(hot["drift"]["pressure"], 3)
        self.assertEqual(list(hot["relationships"]), ["mira"])
        self.assertEqual(hot["relationships"]["mira"], {"stage": "x", "trust": 5})
        self.assertEqual(hot["_relationships_offstage"], ["sera"])
        # declared cold path
        self.assertNotIn("history", hot["red_tape"])
        self.assertEqual(hot["red_tape"]["history_count"], 2)
        self.assertEqual(hot["red_tape"]["stamp"], 2)
        # no special case any more: spirit_tongue is untouched without being declared
        self.assertEqual(hot["spirit_tongue"]["notable_castings"], ["c1"])

    def test_cold_declares_spirit_tongue_and_ignores_bad_paths(self):
        st = dict(STATE, _cold=["spirit_tongue.notable_castings", "nope.deep.path", "", 5,
                                "red_tape.stamp"])
        self.write_state(st)
        hot = self.hot()
        self.assertNotIn("notable_castings", hot["spirit_tongue"])
        self.assertEqual(hot["spirit_tongue"]["notable_castings_count"], 1)
        self.assertNotIn("stamp", hot["red_tape"])  # non-list: dropped, no count

    def test_full_state_and_key_still_return_cold(self):
        self.write_state(STATE)
        p = self.script("load.py", "--key", "red_tape.history")
        self.assertEqual(json.loads(p.stdout)["value"], ["h1", "h2"])
        self.assertEqual(json.loads(self.script("load.py").stdout)["red_tape"]["history"], ["h1", "h2"])

    def test_state_without_cold_matches_old_shape(self):
        st = {k: v for k, v in STATE.items() if k not in ("_cold", "red_tape", "spirit_tongue")}
        self.write_state(st)
        hot = self.hot()
        self.assertNotIn("_cold", hot)
        self.assertEqual(set(hot), {"_view", "_note", "meta", "player", "scene", "goals", "drift",
                                    "relationships", "_relationships_offstage"})

    def test_template_documents_cold(self):
        with open(os.path.join(SKILL, "assets", "state.template.json"), encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("_cold", data["_modules"]["comment"])


class NeutralStringsTest(EngineBase):
    OLD_BLOCK = ("<!-- rpg:active-game -->\n🎮 RPG 進行中：**舊**（`old`）。\n"
                 "輸入 `/rpg` 即可從 `saves/old/recap.md` 立即接續這局。\n<!-- /rpg:active-game -->")

    def pointer(self):
        with open(os.path.join(self.root, "CLAUDE.md"), encoding="utf-8") as f:
            return f.read()

    def test_pointer_text_replaces_old_chinese_block(self):
        with open(os.path.join(self.root, "CLAUDE.md"), "w", encoding="utf-8") as f:
            f.write("# Mine\n\nkeep me\n\n" + self.OLD_BLOCK + "\n\ntail\n")
        p = self.script("checkpoint.py", "--title", "Demo Game", "--recap", "# recap")
        self.assertEqual(p.returncode, 0, p.stderr)
        text = self.pointer()
        self.assertNotIn("進行中", text)
        self.assertNotIn("old", text)
        self.assertIn("🎮 RPG in progress: **Demo Game** (`demo`). Type `/demo` to resume "
                      "from `saves/demo/recap.md`.", text)
        self.assertIn("keep me", text)
        self.assertTrue(text.rstrip().endswith("tail"))
        self.assertEqual(text.count("<!-- rpg:active-game -->"), 1)

    def test_resume_cmd_override_and_idempotent(self):
        self.script("checkpoint.py", "--title", "T", "--recap", "x", "--resume-cmd", "/go")
        self.assertIn("Type `/go`", self.pointer())
        first = self.pointer()
        self.script("checkpoint.py", "--title", "T", "--recap", "x", "--resume-cmd", "/go")
        self.assertEqual(self.pointer(), first)

    def test_codex_neutral_header_and_old_header_still_dedupes(self):
        p = self.script("codex.py", "--unlock", "fog", "Grey Fog")
        self.assertTrue(last_json(p)["newly_unlocked"])
        path = os.path.join(self.root, "saves", GID, "codex.md")
        with open(path, encoding="utf-8") as f:
            self.assertTrue(f.read().startswith("# 📖 Codex\n"))
        # legacy codex with the old Chinese header
        with open(path, "w", encoding="utf-8") as f:
            f.write("# 📖 Codex — 已解鎖圖鑑\n\n<!-- codex:fog -->\n## Grey Fog\n")
        self.assertFalse(last_json(self.script("codex.py", "--unlock", "fog", "Grey Fog"))["newly_unlocked"])
        self.assertTrue(last_json(self.script("codex.py", "--unlock", "ash", "Ash"))["newly_unlocked"])
        with open(path, encoding="utf-8") as f:
            text = f.read()
        self.assertTrue(text.startswith("# 📖 Codex — 已解鎖圖鑑"))
        self.assertIn("<!-- codex:ash -->", text)

    def test_empty_codex_message_is_english(self):
        out = self.script("codex.py", "--list").stdout
        self.assertIn("No codex entries", out)
        self.assertFalse(any(ord(ch) > 0x2fff for ch in out))


class BundledEngineTest(unittest.TestCase):
    def test_compiled_game_bundles_common_and_runs_from_bundle(self):
        with tempfile.TemporaryDirectory() as root:
            p = subprocess.run([sys.executable, COMPILE, "--id", GID, "--title", "Demo",
                                "--modules", "romance", "--root", root],
                               capture_output=True, text=True, timeout=60)
            self.assertEqual(p.returncode, 0, p.stderr)
            game = os.path.join(root, ".claude", "skills", GID)
            bundled = os.path.join(game, "engine", "scripts")
            self.assertTrue(os.path.exists(os.path.join(bundled, "_common.py")))
            self.assertEqual(sorted(f for f in os.listdir(SCRIPTS) if f.endswith(".py")),
                             sorted(f for f in os.listdir(bundled) if f.endswith(".py")))
            # run from the bundled location, from an unrelated cwd, default seed path
            cwd = tempfile.mkdtemp()
            try:
                def b(name, *a, stdin=""):
                    return run(os.path.join(bundled, name), "--game", GID, "--root", root, *a,
                               cwd=cwd, stdin=stdin)
                p = b("save.py", "--init")
                self.assertEqual(last_json(p)["_status"], "initialized", p.stderr)
                self.assertEqual(json.loads(b("load.py", "--hot").stdout)["_view"], "hot")
                p = b("turn.py", "--title", "Demo", "--input", '{"beat":"hello"}')
                self.assertEqual(last_json(p)["_status"], "ok", p.stdout + p.stderr)
                for name in ("rotate_log.py",):
                    self.assertFalse(last_json(b(name, "--check"))["needs_rotation"])
                with open(os.path.join(root, "CLAUDE.md"), encoding="utf-8") as f:
                    self.assertIn("Type `/demo`", f.read())
            finally:
                import shutil
                shutil.rmtree(cwd, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
