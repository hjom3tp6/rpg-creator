#!/usr/bin/env python3
"""Validate a BAKED game skill under .claude/skills/<id>/ — the DETERMINISTIC half of step 6.

This script hardens every *mechanical* check that the old workflow asked the model to eyeball by
hand: file existence, JSON parsing, id/path coherence, unfilled template placeholders, the bundled
engine, and a real end-to-end smoke test of that engine. It does NOT (and cannot) judge content
quality — ensemble rotation, heroine-beauty, narrative coherence are LLM judgment calls and stay in
references/design.md §4. Think of this as the floor: a game that fails validate.py is not ready for
those judgment gates.

    python3 "$SKILL/scripts/validate.py" --id <id>
    python3 "$SKILL/scripts/validate.py" --id <id> --snapshot        # record invariants (pre-polish)
    python3 "$SKILL/scripts/validate.py" --id <id> --check-snapshot  # normal checks + diff vs snapshot

Checks (name: what it verifies):
  required-files, no-placeholders, seed-parses, seed-game-id, seed-fields (FAIL on empty
  meta.game_title / scene.location / scene.summary; WARN-level seed-goals when goals.short is empty),
  opening-cards, persona-file, hidden-lore, path-refs, skill-name/skill-description,
  no-generic-leftovers (FAIL on games/ACTIVE, a language_policy: block, `/rpg` as resume command),
  mechanics-size (WARN > 200 lines: copying, not distilling), roster-index (FAIL: index row with no
  cast card; WARN: orphan card), lore-orphans (WARN: world/lore/*.md with no index row — it can never
  fire), seed-ids (FAIL: affinity/relationships keys or present_characters that are not cast ids),
  card-legibility (FAIL: a card lacks an Age or Appearance label; WARN: label present but empty),
  presence-matrix (WARN: "on stage" names that resolve to no cast id/name; silent if no matrix),
  bundled-engine, engine-smoke (runs the game's OWN bundled save --init, load --hot and turn in a
  temp root and checks the files and JSON), authoring-language (WARN on non-ASCII).

--snapshot writes <skill>/.validate-snapshot.json (sha256 of mechanics.md, state.seed.json and every
file under world/ characters/ story/, plus the SKILL.md frontmatter `name`); --check-snapshot adds a
`snapshot-unchanged` row that FAILs listing what changed. Use them around the optional polish step to
prove the frozen game content did not move. Normal runs ignore the snapshot file.

Output: a JSON report with one row per check ({name, status, detail}); status is PASS / WARN / FAIL.
Exit code is 0 when there is no FAIL (WARN is allowed), 1 otherwise — so it gates a pipeline cleanly.
WARN = a human/LLM must look (e.g. non-ASCII that may be a legit gloss); FAIL = mechanically broken.

Run from the project root (or pass --root). --id is the skill folder == slash command. The smoke
test uses a throwaway temp root; it never touches <root>/saves or <root>/CLAUDE.md.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
# Canonical engine source — to confirm each bundled game carries the full set of scripts.
ENGINE_SRC = os.path.normpath(os.path.join(HERE, "..", "engine"))
PLAY_REFS = ("god-mode.md",)  # the one play-time fallback ref a baked game must bundle

# Content files every baked game must have filled (mirrors compile.py's CONTENT / MIGRATE).
REQUIRED_CONTENT = (
    "SKILL.md",
    "mechanics.md",
    "state.seed.json",
    "world/world-bible.md",
    "world/lore-index.md",
    "characters/index.md",
    "characters/player.md",
    "story/main-arc.md",
)
# Trees scanned for leftover {{placeholders}} and for the authoring-language (non-ASCII) check.
CONTENT_TREES = ("world", "characters", "story", "modules")
# Path tokens a baked SKILL/mechanics may reference; each must resolve under the skill dir.
PATH_REF_RE = re.compile(r"(?:world|characters|story|modules|engine)/[\w\-./]+\.(?:md|json|py)")
PLACEHOLDER_RE = re.compile(r"\{\{.*?\}\}")
NON_ASCII_RE = re.compile(r"[^\x00-\x7f]")


class Report:
    def __init__(self):
        self.checks = []

    def add(self, name, status, detail=""):
        self.checks.append({"name": name, "status": status, "detail": detail})

    def ok(self, name, detail=""):
        self.add(name, "PASS", detail)

    def warn(self, name, detail=""):
        self.add(name, "WARN", detail)

    def fail(self, name, detail=""):
        self.add(name, "FAIL", detail)

    def counts(self):
        c = {"PASS": 0, "WARN": 0, "FAIL": 0}
        for ch in self.checks:
            c[ch["status"]] += 1
        return c


def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def iter_content_files(skill_dir):
    """Yield (relpath, abspath) for every file under the content trees (for scans)."""
    for tree in CONTENT_TREES:
        base = os.path.join(skill_dir, tree)
        if not os.path.isdir(base):
            continue
        for root, _dirs, files in os.walk(base):
            for fn in files:
                ap = os.path.join(root, fn)
                yield os.path.relpath(ap, skill_dir), ap


def frontmatter_name(skill_md_text):
    """Pull `name:` out of the SKILL.md YAML frontmatter (stdlib only, no yaml dep)."""
    if not skill_md_text.startswith("---"):
        return None, False  # no frontmatter at all
    end = skill_md_text.find("\n---", 3)
    block = skill_md_text[3:end] if end != -1 else skill_md_text[3:]
    name = None
    has_desc = False
    for line in block.splitlines():
        m = re.match(r"\s*name:\s*(\S+)", line)
        if m:
            name = m.group(1).strip()
        if re.match(r"\s*description:\s*", line):
            has_desc = True
    return name, has_desc


def check_required_files(skill_dir, rep):
    missing = [rel for rel in REQUIRED_CONTENT
               if not os.path.exists(os.path.join(skill_dir, rel))]
    if missing:
        rep.fail("required-files", "missing: " + ", ".join(missing))
    else:
        rep.ok("required-files", "all %d present" % len(REQUIRED_CONTENT))


def check_placeholders(skill_dir, rep):
    """Any leftover {{...}} means an unfilled template — a hard fail."""
    hits = []
    for rel in ("SKILL.md", "mechanics.md", "state.seed.json"):
        ap = os.path.join(skill_dir, rel)
        if os.path.exists(ap) and PLACEHOLDER_RE.search(read_text(ap)):
            hits.append(rel)
    for rel, ap in iter_content_files(skill_dir):
        if PLACEHOLDER_RE.search(read_text(ap)):
            hits.append(rel)
    if hits:
        rep.fail("no-placeholders", "unfilled {{...}} in: " + ", ".join(sorted(set(hits))))
    else:
        rep.ok("no-placeholders", "no leftover template placeholders")


def check_seed(skill_dir, gid, rep):
    path = os.path.join(skill_dir, "state.seed.json")
    if not os.path.exists(path):
        rep.fail("seed-parses", "state.seed.json missing")
        return None
    try:
        data = json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        rep.fail("seed-parses", "invalid JSON: %s" % exc)
        return None
    if not isinstance(data, dict):
        rep.fail("seed-parses", "state.seed.json must be a JSON object")
        return None
    rep.ok("seed-parses", "state.seed.json is valid JSON")
    seed_id = (data.get("meta") or {}).get("game_id")
    if seed_id == gid:
        rep.ok("seed-game-id", "meta.game_id == %s" % gid)
    else:
        rep.fail("seed-game-id", "meta.game_id is %r, expected %r" % (seed_id, gid))
    return data


def check_opening_cards(skill_dir, seed, rep):
    """Every character on stage in the opening scene must have a card file."""
    if seed is None:
        return
    present = (seed.get("scene") or {}).get("present_characters") or []
    if not present:
        rep.warn("opening-cards", "scene.present_characters is empty (no one on stage at open?)")
        return
    missing = []
    for cid in present:
        cast = os.path.join(skill_dir, "characters", "cast", "%s.md" % cid)
        player = os.path.join(skill_dir, "characters", "player.md")
        if not (os.path.exists(cast) or cid == "player" and os.path.exists(player)):
            missing.append(cid)
    if missing:
        rep.fail("opening-cards", "present_characters with no card: " + ", ".join(missing))
    else:
        rep.ok("opening-cards", "all %d opening characters have cards" % len(present))


def check_persona_file(skill_dir, seed, rep):
    if seed is None:
        return
    rel = ((seed.get("player") or {}).get("persona_file")) or "characters/player.md"
    if os.path.exists(os.path.join(skill_dir, rel)):
        rep.ok("persona-file", "player.persona_file resolves (%s)" % rel)
    else:
        rep.fail("persona-file", "player.persona_file does not exist: %s" % rel)


def _parse_table_rows(text):
    """Yield lists of cell-strings for each data row of the FIRST markdown table found."""
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        # skip the header row and the |---|---| separator
        if set("".join(cells)) <= set("-: "):
            continue
        if cells[:1] == ["id"]:
            continue
        yield cells


def check_hidden_lore(skill_dir, rep):
    """Each lore-index row with public:no must have its world/lore/<id>.md body file."""
    path = os.path.join(skill_dir, "world", "lore-index.md")
    if not os.path.exists(path):
        rep.fail("hidden-lore", "world/lore-index.md missing")
        return
    missing = []
    rows = 0
    for cells in _parse_table_rows(read_text(path)):
        if len(cells) < 2 or PLACEHOLDER_RE.search("".join(cells)):
            continue  # skip the template example row
        lore_id, public = cells[0], cells[-1].lower()
        rows += 1
        if public.startswith("no"):
            body = os.path.join(skill_dir, "world", "lore", "%s.md" % lore_id)
            if not os.path.exists(body):
                missing.append(lore_id)
    if missing:
        rep.fail("hidden-lore", "public:no lore with no world/lore/<id>.md: " + ", ".join(missing))
    elif rows == 0:
        rep.warn("hidden-lore", "no lore rows found (a world with zero secrets?)")
    else:
        rep.ok("hidden-lore", "all hidden lore rows have body files (%d rows)" % rows)


def check_path_refs(skill_dir, rep):
    """Every world/characters/story/engine path named in SKILL.md or mechanics.md must resolve."""
    broken = set()
    checked = 0
    for rel in ("SKILL.md", "mechanics.md"):
        ap = os.path.join(skill_dir, rel)
        if not os.path.exists(ap):
            continue
        for m in PATH_REF_RE.findall(read_text(ap)):
            if "<id>" in m or "<name>" in m or "{{" in m:
                continue  # generic placeholder, not a literal path
            # engine/references/* other than god-mode.md only ever appears as a compile-time
            # provenance note ("distilled from gm-protocol.md") — those refs are intentionally
            # NOT bundled into a baked game, so a "missing" verdict would be a false positive.
            if m.startswith("engine/references/") and not m.endswith("god-mode.md"):
                continue
            checked += 1
            if not os.path.exists(os.path.join(skill_dir, m)):
                broken.add(m)
    if broken:
        rep.fail("path-refs", "SKILL/mechanics reference missing paths: " + ", ".join(sorted(broken)))
    else:
        rep.ok("path-refs", "all %d referenced content paths resolve" % checked)


def check_skill_frontmatter(skill_dir, gid, rep):
    path = os.path.join(skill_dir, "SKILL.md")
    if not os.path.exists(path):
        rep.fail("skill-frontmatter", "SKILL.md missing")
        return
    name, has_desc = frontmatter_name(read_text(path))
    if name == gid:
        rep.ok("skill-name", "frontmatter name == %s (slash command /%s)" % (gid, gid))
    else:
        rep.fail("skill-name", "frontmatter name is %r, expected %r" % (name, gid))
    if has_desc:
        rep.ok("skill-description", "frontmatter has a description")
    else:
        rep.fail("skill-description", "frontmatter has no description (won't trigger well)")


def check_bundled_engine(skill_dir, rep):
    """The game must carry its OWN copy of every canonical engine script + play-time ref."""
    dst = os.path.join(skill_dir, "engine", "scripts")
    src = os.path.join(ENGINE_SRC, "scripts")
    if not os.path.isdir(dst):
        rep.fail("bundled-engine", "engine/scripts missing — run compile.py --id <id> --update-engine")
        return
    canonical = sorted(f for f in os.listdir(src) if f.endswith(".py"))
    missing = [f for f in canonical if not os.path.exists(os.path.join(dst, f))]
    if missing:
        rep.fail("bundled-engine",
                 "missing scripts: %s — run compile.py --id <id> --update-engine" % ", ".join(missing))
    else:
        rep.ok("bundled-engine", "all %d engine scripts bundled" % len(canonical))
    refs = os.path.join(skill_dir, "engine", "references")
    missing_refs = [r for r in PLAY_REFS if not os.path.exists(os.path.join(refs, r))]
    if missing_refs:
        rep.warn("bundled-engine-refs", "missing play-time ref(s): " + ", ".join(missing_refs))


def _run_engine(py, args, cwd, stdin=None):
    """Run a bundled engine script; return (ok, parsed_json_or_None, error_text)."""
    try:
        proc = subprocess.run([sys.executable, py, *args], capture_output=True, text=True,
                              timeout=60, cwd=cwd, input=stdin if stdin is not None else "")
    except (subprocess.SubprocessError, OSError) as exc:
        return False, None, "could not execute: %s" % exc
    lines = proc.stdout.strip().splitlines()
    if proc.returncode != 0:
        return False, None, "exit %d: %s" % (proc.returncode,
                                              (proc.stderr.strip() or proc.stdout.strip())[:300])
    try:
        return True, json.loads(proc.stdout), ""
    except json.JSONDecodeError:
        try:
            return True, json.loads(lines[-1]), ""
        except (IndexError, json.JSONDecodeError):
            return False, None, "output is not valid JSON: %s" % proc.stdout.strip()[:200]


def check_engine_smoke(skill_dir, gid, rep):
    """Run the game's OWN bundled engine end to end in a temp root: init -> load --hot -> turn."""
    scripts = os.path.join(skill_dir, "engine", "scripts")
    seed = os.path.join(skill_dir, "state.seed.json")
    missing = [n for n in ("save.py", "load.py", "turn.py")
               if not os.path.exists(os.path.join(scripts, n))]
    if missing:
        rep.fail("engine-smoke", "bundled engine/scripts missing: " + ", ".join(missing))
        return
    tmp = tempfile.mkdtemp(prefix="rpg-validate-")
    try:
        def step(label, script, args, stdin=None):
            ok, out, err = _run_engine(os.path.join(scripts, script), args, tmp, stdin)
            if not ok:
                rep.fail("engine-smoke", "step %s failed: %s" % (label, err))
                return None
            return out

        out = step("save --init", "save.py",
                   ["--game", gid, "--init", "--root", tmp, "--seed", seed])
        if out is None:
            return
        if out.get("_status") != "initialized":
            rep.fail("engine-smoke", "step save --init: unexpected status %r" % out.get("_status"))
            return
        out = step("load --hot", "load.py", ["--game", gid, "--hot", "--root", tmp])
        if out is None:
            return
        if out.get("_status") in ("no_save", "error") or out.get("_view") != "hot":
            rep.fail("engine-smoke", "step load --hot: unexpected output %s"
                     % json.dumps(out, ensure_ascii=False)[:200])
            return
        turn = json.dumps({"patch": {"flags": {"_smoke": True}}, "beat": "Smoke-test beat.",
                           "unlock": [{"id": "smoke-test", "title": "Smoke test"}]})
        out = step("turn", "turn.py", ["--game", gid, "--root", tmp, "--title", "Smoke Test",
                                       "--resume-cmd", "/" + gid, "--input", turn])
        if out is None:
            return
        if out.get("_status") != "ok" or out.get("newly_unlocked") != ["smoke-test"]:
            rep.fail("engine-smoke", "step turn: unexpected output %s"
                     % json.dumps(out, ensure_ascii=False)[:200])
            return
        saves = os.path.join(tmp, "saves", gid)
        absent = [f for f in ("state.json", "recap.md", "session-log.md", "codex.md")
                  if not os.path.exists(os.path.join(saves, f))]
        if absent:
            rep.fail("engine-smoke", "after turn, missing in saves/<id>/: " + ", ".join(absent))
            return
        try:
            with open(os.path.join(saves, "state.json"), encoding="utf-8") as f:
                json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            rep.fail("engine-smoke", "state.json after turn is not valid JSON: %s" % exc)
            return
        rep.ok("engine-smoke", "bundled save --init, load --hot, turn all ran; state/recap/log/codex written")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_authoring_language(skill_dir, rep):
    """Non-ASCII in content is a WARN — it may be a legit gloss/keyword, so a human/LLM must look.

    The two allowed buckets (lore-index keywords; `word (中文)` glossed samples) are legitimate; any
    OTHER non-English content must be rewritten to English (references/design.md §3). We surface the
    files+line numbers; judging which bucket each hit falls in is the LLM's job, not regex's.
    """
    hits = []
    for rel, ap in iter_content_files(skill_dir):
        for i, line in enumerate(read_text(ap).splitlines(), 1):
            if NON_ASCII_RE.search(line):
                hits.append("%s:%d" % (rel, i))
    if hits:
        shown = ", ".join(hits[:12]) + (" …(+%d more)" % (len(hits) - 12) if len(hits) > 12 else "")
        rep.warn("authoring-language",
                 "%d non-ASCII line(s) — confirm each is a lore keyword or `word (中文)` gloss, else "
                 "rewrite to English: %s" % (len(hits), shown))
    else:
        rep.ok("authoring-language", "content is all ASCII/English")


SNAPSHOT_FILE = ".validate-snapshot.json"
SNAPSHOT_TREES = ("world", "characters", "story")
SNAPSHOT_FILES = ("mechanics.md", "state.seed.json")
LEFTOVER_RES = (
    ("games/ACTIVE", re.compile(r"games/ACTIVE")),
    ("language_policy: block", re.compile(r"language_policy\s*:")),
    ("/rpg as resume command", re.compile(r"(?<![\w/.\-])/rpg(?![\w\-])")),
)
PLACEHOLDER_CONTENT_RE = re.compile(r"^(?:tbd|todo|n/?a|none|\?+|-+|—+|…+|\.{2,})$", re.I)
IGNORED_STAGE_TOKENS = {"everyone", "all", "full cast", "cast", "the cast", "everybody", "player",
                        "the player", "solo", "alone", "none", "—", "-", "–", "n/a", ""}


def _strip_md(text):
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def roster_ids(skill_dir):
    """(index_ids, card_ids): ids listed in characters/index.md and cast/*.md filename stems."""
    index_ids = []
    idx = os.path.join(skill_dir, "characters", "index.md")
    if os.path.exists(idx):
        for cells in _parse_table_rows(read_text(idx)):
            if cells and cells[0] and not PLACEHOLDER_RE.search("".join(cells)):
                index_ids.append(cells[0])
    cast_dir = os.path.join(skill_dir, "characters", "cast")
    card_ids = []
    if os.path.isdir(cast_dir):
        card_ids = sorted(f[:-3] for f in os.listdir(cast_dir) if f.endswith(".md"))
    return index_ids, card_ids


def check_seed_fields(seed, rep):
    """The seed uses empty strings (not {{}}), so the placeholder scan cannot see an unfilled one."""
    if seed is None:
        return
    def get(path):
        cur = seed
        for part in path.split("."):
            cur = cur.get(part) if isinstance(cur, dict) else None
        return cur
    empty = [p for p in ("meta.game_title", "scene.location", "scene.summary")
             if not (isinstance(get(p), str) and get(p).strip())]
    if empty:
        rep.fail("seed-fields", "empty in state.seed.json: " + ", ".join(empty))
    else:
        rep.ok("seed-fields", "meta.game_title, scene.location, scene.summary are filled")
    short = get("goals.short")
    if not (isinstance(short, list) and any(str(x).strip() for x in short)) \
            and not (isinstance(short, str) and short.strip()):
        rep.warn("seed-goals", "goals.short is empty (no opening direction for the GM)")
    else:
        rep.ok("seed-goals", "goals.short is set")


def check_generic_leftovers(skill_dir, rep):
    hits = []
    for rel in ("SKILL.md", "mechanics.md"):
        ap = os.path.join(skill_dir, rel)
        if not os.path.exists(ap):
            continue
        text = read_text(ap)
        for label, rx in LEFTOVER_RES:
            if rx.search(text):
                hits.append("%s: %s" % (rel, label))
    if hits:
        rep.fail("no-generic-leftovers", "generic-engine leftovers — " + "; ".join(hits))
    else:
        rep.ok("no-generic-leftovers", "no games/ACTIVE, language_policy block or /rpg resume command")


def check_mechanics_size(skill_dir, rep):
    ap = os.path.join(skill_dir, "mechanics.md")
    if not os.path.exists(ap):
        return
    n = len(read_text(ap).splitlines())
    if n > 200:
        rep.warn("mechanics-size", "mechanics.md is %d lines (spec ~120-160; >200 means copying, "
                 "not distilling)" % n)
    else:
        rep.ok("mechanics-size", "mechanics.md is %d lines" % n)


def check_roster(skill_dir, rep):
    index_ids, card_ids = roster_ids(skill_dir)
    no_card = [i for i in index_ids if i not in card_ids]
    if no_card:
        rep.fail("roster-index", "characters/index.md rows with no characters/cast/<id>.md: "
                 + ", ".join(no_card))
    else:
        orphans = [c for c in card_ids if c not in index_ids]
        if orphans:
            rep.warn("roster-index", "cast cards not listed in characters/index.md (orphan): "
                     + ", ".join(orphans))
        else:
            rep.ok("roster-index", "index and cast cards agree (%d characters)" % len(index_ids))
    lore_dir = os.path.join(skill_dir, "world", "lore")
    lore_ids = set()
    li = os.path.join(skill_dir, "world", "lore-index.md")
    if os.path.exists(li):
        for cells in _parse_table_rows(read_text(li)):
            if len(cells) >= 2 and not PLACEHOLDER_RE.search("".join(cells)):
                lore_ids.add(cells[0])
    if os.path.isdir(lore_dir):
        orphan_lore = sorted(f[:-3] for f in os.listdir(lore_dir)
                             if f.endswith(".md") and f[:-3] not in lore_ids)
        if orphan_lore:
            rep.warn("lore-orphans", "world/lore files with no lore-index row (can never fire): "
                     + ", ".join(orphan_lore))
            return
    rep.ok("lore-orphans", "every lore body file has an index row")


def check_seed_ids(skill_dir, seed, rep):
    if seed is None:
        return
    index_ids, card_ids = roster_ids(skill_dir)
    known = set(index_ids) | set(card_ids) | {"player"}
    bad = []
    for block in ("affinity", "relationships"):
        val = seed.get(block)
        if isinstance(val, dict):
            bad += ["%s.%s" % (block, k) for k in val if not k.startswith("_") and k not in known]
    present = (seed.get("scene") or {}).get("present_characters")
    if isinstance(present, list):
        bad += ["scene.present_characters[%s]" % c for c in present
                if isinstance(c, str) and c not in known]
    if bad:
        rep.fail("seed-ids", "seed ids that are not cast ids: " + ", ".join(bad))
    else:
        rep.ok("seed-ids", "all seed affinity/relationships/present_characters ids are cast ids")


def card_field(text, label):
    """Find an Age/Appearance field in a card: (found, content). Heading or bold label, any case."""
    text = _strip_md(text)
    lines = text.splitlines()
    head = re.compile(r"^\s*#{1,6}\s*%s\b" % label, re.I)
    bold = re.compile(r"^\s*(?:[-*+]\s+)?\*\*\s*%s\b[^*\n]*\*\*\s*:?\s*(.*)$" % label, re.I)
    plain = re.compile(r"^\s*(?:[-*+]\s+)?%s\s*:\s*(.*)$" % label, re.I)
    for i, line in enumerate(lines):
        if head.match(line):
            body = []
            for nxt in lines[i + 1:]:
                if re.match(r"^\s*#{1,6}\s", nxt):
                    break
                body.append(nxt)
            return True, "\n".join(body)
        m = bold.match(line) or plain.match(line)
        if m:
            rest = [m.group(1)]
            for nxt in lines[i + 1:]:
                if not nxt.strip() or re.match(r"^\s*(?:#|[-*+]\s)", nxt):
                    break
                rest.append(nxt)
            return True, "\n".join(rest)
    return False, ""


def _content_empty(content):
    stripped = PLACEHOLDER_RE.sub("", content)
    stripped = re.sub(r"[\s*_\-–—:]+", " ", stripped).strip()
    # a bullet list of unfilled labels ("Build & height:") is still empty
    if not stripped:
        return True
    return bool(PLACEHOLDER_CONTENT_RE.match(stripped))


def check_card_legibility(skill_dir, rep):
    cards = []
    cast_dir = os.path.join(skill_dir, "characters", "cast")
    if os.path.isdir(cast_dir):
        cards += [(os.path.join("characters", "cast", f), os.path.join(cast_dir, f))
                  for f in sorted(os.listdir(cast_dir)) if f.endswith(".md")]
    player = os.path.join(skill_dir, "characters", "player.md")
    if os.path.exists(player):
        cards.append(("characters/player.md", player))
    absent, empty = [], []
    for rel, ap in cards:
        text = read_text(ap)
        for label in ("Age", "Appearance"):
            found, content = card_field(text, label)
            if not found:
                absent.append("%s:%s" % (rel, label))
            elif _content_empty(content):
                empty.append("%s:%s" % (rel, label))
    if absent:
        rep.fail("card-legibility", "missing Age/Appearance label in: " + ", ".join(absent))
    elif empty:
        rep.warn("card-legibility", "Age/Appearance present but empty/placeholder in: "
                 + ", ".join(empty))
    else:
        rep.ok("card-legibility", "all %d cards have Age and Appearance" % len(cards))


def _first_word(s):
    m = re.match(r"[^\W_][\w'’]*", s.strip().strip("*_`\"'“”"))
    return m.group(0).lower() if m else ""


def check_presence_matrix(skill_dir, rep):
    arc = os.path.join(skill_dir, "story", "main-arc.md")
    if not os.path.exists(arc):
        return
    lines = read_text(arc).splitlines()
    start = next((i for i, l in enumerate(lines)
                  if re.match(r"^\s*#{1,6}\s.*presence matrix", l, re.I)), None)
    if start is None:
        return
    rows = []
    for line in lines[start + 1:]:
        if re.match(r"^\s*#{1,6}\s", line):
            break
        if line.strip().startswith("|"):
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
    data = [r for r in rows if r and not set("".join(r)) <= set("-: ")]
    if len(data) < 2:
        return
    header, body = data[0], data[1:]
    col = next((i for i, h in enumerate(header) if "on stage" in h.lower()),
               1 if len(header) > 1 else 0)
    # names that resolve: ids, id parts, first word of the index one-liner, first word of card H1
    index_ids, card_ids = roster_ids(skill_dir)
    names = set()
    for cid in set(index_ids) | set(card_ids):
        names.add(cid.lower())
        names.update(p.lower() for p in cid.split("-") if p)
    idx = os.path.join(skill_dir, "characters", "index.md")
    if os.path.exists(idx):
        for cells in _parse_table_rows(read_text(idx)):
            if len(cells) > 1:
                names.add(_first_word(cells[1]))
    for cid in card_ids:
        h1 = next((l for l in read_text(os.path.join(skill_dir, "characters", "cast", cid + ".md"))
                   .splitlines() if l.startswith("# ")), "")
        names.add(_first_word(h1[2:]))
    names.discard("")
    unresolved = []
    for r in body:
        if col >= len(r) or "{{" in r[col]:
            continue
        cell = re.sub(r"\([^)]*\)", "", r[col])
        for tok in re.split(r"\s*(?:\+|,|&|/|;|\band\b)\s*", cell):
            tok = tok.strip().strip("*_`").strip()
            low = tok.lower()
            if low in IGNORED_STAGE_TOKENS or low.startswith(("everyone", "all ", "full cast",
                                                              "player", "no one", "nobody")):
                continue
            if low in names or _first_word(tok) in names:
                continue
            if tok not in unresolved:
                unresolved.append(tok)
    if unresolved:
        rep.warn("presence-matrix", "'on stage' names matching no cast id/name: " + ", ".join(unresolved))
    else:
        rep.ok("presence-matrix", "all Presence Matrix names resolve to cast")


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def snapshot_data(skill_dir):
    files = {}
    for rel in SNAPSHOT_FILES:
        ap = os.path.join(skill_dir, rel)
        if os.path.exists(ap):
            files[rel] = _sha(ap)
    for tree in SNAPSHOT_TREES:
        base = os.path.join(skill_dir, tree)
        for root_, _dirs, fns in os.walk(base):
            for fn in fns:
                ap = os.path.join(root_, fn)
                files[os.path.relpath(ap, skill_dir).replace(os.sep, "/")] = _sha(ap)
    sk = os.path.join(skill_dir, "SKILL.md")
    name = frontmatter_name(read_text(sk))[0] if os.path.exists(sk) else None
    return {"skill_name": name, "files": dict(sorted(files.items()))}


def write_snapshot(skill_dir):
    snap = snapshot_data(skill_dir)
    path = os.path.join(skill_dir, SNAPSHOT_FILE)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(snap, f, indent=2, sort_keys=True)
    return path, snap


def check_snapshot(skill_dir, rep):
    path = os.path.join(skill_dir, SNAPSHOT_FILE)
    if not os.path.exists(path):
        rep.fail("snapshot-unchanged", "no %s — run validate.py --id <id> --snapshot first" % SNAPSHOT_FILE)
        return
    try:
        old = json.loads(read_text(path))
        old_files = old["files"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        rep.fail("snapshot-unchanged", "unreadable snapshot: %s" % exc)
        return
    cur = snapshot_data(skill_dir)
    diffs = []
    if old.get("skill_name") != cur["skill_name"]:
        diffs.append("SKILL.md name: %r -> %r" % (old.get("skill_name"), cur["skill_name"]))
    for rel in sorted(set(old_files) | set(cur["files"])):
        if rel not in cur["files"]:
            diffs.append("removed: " + rel)
        elif rel not in old_files:
            diffs.append("added: " + rel)
        elif old_files[rel] != cur["files"][rel]:
            diffs.append("changed: " + rel)
    if diffs:
        rep.fail("snapshot-unchanged", "invariants moved since snapshot — " + "; ".join(diffs))
    else:
        rep.ok("snapshot-unchanged", "%d files and the skill name match the snapshot" % len(cur["files"]))


def main():
    ap = argparse.ArgumentParser(description="Validate a baked game skill (deterministic checks).")
    ap.add_argument("--id", required=True, help="baked game id (= skill folder == slash command)")
    ap.add_argument("--root", default=os.getcwd(), help="project root")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--snapshot", action="store_true",
                      help="record invariant hashes to <skill>/%s and exit" % SNAPSHOT_FILE)
    mode.add_argument("--check-snapshot", action="store_true",
                      help="run the normal checks plus a diff against the recorded snapshot")
    args = ap.parse_args()

    gid = args.id.strip()
    root = os.path.abspath(args.root)
    skill_dir = os.path.join(root, ".claude", "skills", gid)

    rep = Report()
    if not os.path.isdir(skill_dir):
        rep.fail("skill-dir", "no such baked game: %s" % skill_dir)
        print(json.dumps({"_status": "fail", "id": gid, "skill_dir": skill_dir,
                          "summary": rep.counts(), "checks": rep.checks},
                         ensure_ascii=False, indent=2))
        return 1

    if args.snapshot:
        path, snap = write_snapshot(skill_dir)
        print(json.dumps({"_status": "snapshot", "id": gid, "path": path,
                          "files": len(snap["files"]), "skill_name": snap["skill_name"]},
                         ensure_ascii=False))
        return 0

    check_required_files(skill_dir, rep)
    check_placeholders(skill_dir, rep)
    seed = check_seed(skill_dir, gid, rep)
    check_seed_fields(seed, rep)
    check_opening_cards(skill_dir, seed, rep)
    check_persona_file(skill_dir, seed, rep)
    check_hidden_lore(skill_dir, rep)
    check_path_refs(skill_dir, rep)
    check_skill_frontmatter(skill_dir, gid, rep)
    check_generic_leftovers(skill_dir, rep)
    check_mechanics_size(skill_dir, rep)
    check_roster(skill_dir, rep)
    check_seed_ids(skill_dir, seed, rep)
    check_card_legibility(skill_dir, rep)
    check_presence_matrix(skill_dir, rep)
    check_bundled_engine(skill_dir, rep)
    check_engine_smoke(skill_dir, gid, rep)
    check_authoring_language(skill_dir, rep)
    if args.check_snapshot:
        check_snapshot(skill_dir, rep)

    counts = rep.counts()
    status = "fail" if counts["FAIL"] else "pass"
    print(json.dumps({
        "_status": status,
        "id": gid,
        "skill_dir": skill_dir,
        "summary": counts,
        "checks": rep.checks,
        "note": ("Deterministic floor only. PASS here does NOT mean the design gates pass — still run "
                 "the references/design.md §4 quality gates (ensemble-depth, legibility, beauty) by hand."),
    }, ensure_ascii=False, indent=2))
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
