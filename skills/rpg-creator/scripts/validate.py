#!/usr/bin/env python3
"""Validate a BAKED game skill under .claude/skills/<id>/ — the DETERMINISTIC half of step 5.

This script hardens every *mechanical* check that the old workflow asked the model to eyeball by
hand: file existence, JSON parsing, id/path coherence, unfilled template placeholders, the bundled
engine, and that load.py actually runs. It does NOT (and cannot) judge content quality — ensemble
rotation, heroine-beauty, narrative coherence are LLM judgment calls and stay in references/design.md
§4. Think of this as the floor: a game that fails validate.py is not ready for those judgment gates.

    python3 "$SKILL/scripts/validate.py" --id <id>

Output: a JSON report with one row per check ({name, status, detail}); status is PASS / WARN / FAIL.
Exit code is 0 when there is no FAIL (WARN is allowed), 1 otherwise — so it gates a pipeline cleanly.
WARN = a human/LLM must look (e.g. non-ASCII that may be a legit gloss); FAIL = mechanically broken.

Run from the project root (or pass --root). --id is the skill folder == slash command.
"""
import argparse
import json
import os
import re
import subprocess
import sys

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


def check_load_runs(skill_dir, gid, root, rep):
    """load.py from the game's OWN bundled engine must actually run (proves the engine works)."""
    load_py = os.path.join(skill_dir, "engine", "scripts", "load.py")
    if not os.path.exists(load_py):
        rep.fail("load-runs", "bundled engine/scripts/load.py missing")
        return
    try:
        proc = subprocess.run(
            [sys.executable, load_py, "--game", gid, "--root", root],
            capture_output=True, text=True, timeout=30)
    except (subprocess.SubprocessError, OSError) as exc:
        rep.fail("load-runs", "could not execute load.py: %s" % exc)
        return
    if proc.returncode != 0:
        rep.fail("load-runs", "load.py exited %d: %s" % (proc.returncode, proc.stderr.strip()[:200]))
        return
    try:
        out = json.loads(proc.stdout)
    except json.JSONDecodeError:
        rep.fail("load-runs", "load.py output is not valid JSON")
        return
    status = out.get("_status", "state")
    rep.ok("load-runs", "bundled load.py runs (status: %s)" % status)


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


def main():
    ap = argparse.ArgumentParser(description="Validate a baked game skill (deterministic checks).")
    ap.add_argument("--id", required=True, help="baked game id (= skill folder == slash command)")
    ap.add_argument("--root", default=os.getcwd(), help="project root")
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

    check_required_files(skill_dir, rep)
    check_placeholders(skill_dir, rep)
    seed = check_seed(skill_dir, gid, rep)
    check_opening_cards(skill_dir, seed, rep)
    check_persona_file(skill_dir, seed, rep)
    check_hidden_lore(skill_dir, rep)
    check_path_refs(skill_dir, rep)
    check_skill_frontmatter(skill_dir, gid, rep)
    check_bundled_engine(skill_dir, rep)
    check_load_runs(skill_dir, gid, root, rep)
    check_authoring_language(skill_dir, rep)

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
