---
name: rpg-creator
description: >-
  Author a brand-new narrative RPG and COMPILE it into its own self-contained, directly-playable
  skill under .claude/skills/<id>/ — a "baked game". This is skill-creator + world-forge fused: you
  interview/design a complete world (premise, cast, lore, story, mechanics), then emit a lean,
  game-specific SKILL.md + distilled mechanics.md + content tree that the player runs with its own
  slash command (e.g. /neon-shrine), with no generic engine loaded at play time. Use WHENEVER the
  user wants to create, build, design, author, or compile a new RPG world / story / game / cartridge
  / scenario, or says things like "做一個新遊戲 / 開一個新世界 / 幫我做一個 RPG / 我想自己做一個劇本
  / create a new RPG / build me a game / make a sci-fi (wuxia, horror, school…) RPG / 把這個遊戲做成
  skill / compile this game". This is the AUTHORING tool; each baked <id> skill is for PLAYING.
---

# RPG-Creator — author a world, then COMPILE it into its own playable skill

Old model (now retired): one generic `/rpg` engine read a swappable cartridge and, **every turn at
play time**, re-decided which generic references + module rules to load. That runtime filtering — plus
all the world-agnostic "if this module is active / else" boilerplate — burned context before the story
even started.

**This tool reverses that.** You do the filtering **once, here, at author time**, and emit a
**baked game**: a self-contained skill that holds a play loop *already specialized to this one world*.
At play time the baked skill loads a short, pre-tuned guide and the scene's content — nothing generic.

```
$SKILL/  (this skill's base dir — local skill OR installed plugin)  ← THIS skill: author + compiler
    engine/                   ←   CANONICAL engine source (scripts + craft/fallback refs); copied into each game
    module-library/  story-structures/  assets/  references/{design,compile}.md
    scripts/{roll,compile,scorecard,validate}.py
.claude/skills/<id>/          ← OUTPUT: one baked, SELF-CONTAINED game skill (/​<id>)
    engine/                   ←   its OWN bundled copy of the engine (no shared dep — copy the folder anywhere)
saves/<id>/                   ← that game's save (state.json / recap.md / journal.md / log / codex)
```

> Each baked game is **fully self-contained**: it carries its own `engine/`, so the whole folder copies
> to any workspace / `~/.claude/skills/` / another machine and just runs. The engine is EXECUTED, not
> read into context, so this duplication costs zero play-time tokens. Re-sync the engine into an existing
> game after improving it: `compile.py --id <id> --update-engine`. Run scripts from the project root.

## What "compiling" actually does (the core idea — read first)

A baked game must run a full GM loop **without** loading the generic engine. So at compile time you
**distill**, not copy:

1. **The play loop → a game-specific `SKILL.md`.** Language policy, active-module list, opening beat,
   game id, and resume command are all **hardcoded** — no "honor the manifest", no module on/off
   branches. The per-turn loop keeps only the steps this game uses.
2. **The rules → one `mechanics.md`.** Read this game's active modules
   (`module-library/<name>.md`) **and** the universal craft (`engine/references/gm-protocol.md`
   + `drama-craft.md`), and condense the parts that apply into a single tuned file in the game's own
   terms. Drop every branch, caveat, and module this game doesn't use. ~4–6 generic files (≈550
   lines) collapse into one (~120–160 lines). This is where the context win comes from.
3. **The world → a content tree, loaded lazily (unchanged).** `world/ characters/ story/` +
   `state.seed.json` keep the same keyword-triggered, load-on-present discipline that already works.
4. **The invariants → bundled, not shared.** `compile.py` copies the engine (turn/save/load/codex scripts + the
   one rare-path ref `god-mode.md`, for the sole OOC command `[god]`) into the game's own `engine/`
   folder, so the game is self-contained. The baked SKILL points at `$SKILL/engine/…` and loads that
   reference only on an edge case. (Scripts are executed, never read into context — zero play-time token cost.)

The result: a game that plays like the old engine but boots from its lean SKILL.md + mechanics.md
(a typical baked game boots on ~280 lines, vs ~700+ of generic engine/rules scaffolding the
old `/rpg` reloaded each session), and makes almost no runtime "what should I load?" decisions. (Per
turn, state reads are further trimmed by `load.py --hot` — the volatile core only.)

## Workflow
Outline first, expand second: settle the game's *shape* on three cheap files before spending tokens on
full cards and the distilled files, so tuning never throws away expensive work.

### 1. Design the world — `references/design.md`
Interview the user, then design a coherent, opinionated world: premise, tone, language policy, active
modules, a cast with varied drives, a spine in the chosen story structure, and a presence plan for its
cast pattern. **Start from real randomness:** `python3 "$SKILL/scripts/roll.py" --count 3` (add
`--lock axis=value` for whatever the user already asked for) rolls design combos from
`assets/variation-tables.json`, skipping what existing games used; offer 2–3 of them plus "tell me
what you want", then read only the chosen `story-structures/<name>.md`. All the world-design craft,
the mandatory quality gates (ensemble-depth, character-legibility, heroine-beauty when romance is
active), and the authoring-language rule live in **`references/design.md`** — read it before designing.

### 2. Scaffold the baked skill — `scripts/compile.py`
Pick a short **kebab-case id** (= the skill folder name **and** the slash command, e.g. `neon-shrine`
→ `/neon-shrine`). Let **`$SKILL`** = this skill's base directory — the absolute path printed as *"Base
directory for this skill"* at invocation (this resolves correctly whether rpg-creator runs as a local
project skill or an installed plugin, so never hardcode `.claude/skills/rpg-creator`). Then, from the
project root (the new game lands in *this* project's `.claude/skills/<id>/`):

```bash
# fresh game (the usual path). --title / --modules fill the mechanical placeholders for you:
# {{id}}/{{Title}}, seed meta, the active-module list, unused module sections, the drift block.
python3 "$SKILL/scripts/compile.py" --id <id> --title "<Title>" --modules romance,drift --structure heist

# fork: seed a new game from an EXISTING content dir (copies its world/ characters/ story/ + seed),
# e.g. branch off another baked game:  --from .claude/skills/<other-game>
python3 "$SKILL/scripts/compile.py" --id <id> --title "<Title>" --modules <list> --from .claude/skills/<other-game>
```

`--modules` takes library names (`romance`, `magic-potency`, `language-coaching`, `drift`); any other
name is a custom module. `--structure` takes a `story-structures/` name (validated) and writes it + its
`cast_pattern` into main-arc.md's `## Design DNA`. The JSON `fill` list says what was substituted (and any anchor it couldn't
find) — **verify it, don't redo it by hand**. The game's own bundled `engine/` is laid down too (self-
contained). It never overwrites an existing baked skill unless you pass `--force`.

### 3. Write the OUTLINE only — `references/design.md` §3
Fill just the three cheap shape files plus the world-bible: **`world/world-bible.md`**, the rows of
**`characters/index.md`** and **`world/lore-index.md`**, and **`story/main-arc.md`** (Design DNA, spine,
phases, pressure, opposition, Presence Matrix). No full character cards, lore bodies, or distilled files yet. (A `--from` fork is
already populated — review it instead.)

### 4. Complexity review & tuning — `scripts/scorecard.py` + `references/design.md` §5
Settle the game's final size/shape *with the user* **now, while changes are cheap.** The scorecard reads
only the outline files; get the counts from the script (don't hand-count):

```bash
python3 "$SKILL/scripts/scorecard.py" --id <id>
```

It reports the Design DNA & cast pattern, cast size & roles, romanceable count, lore/hidden-secret
counts, phases/beats/pressure, and the measurable ensemble signals (distinct sub-casts, who has a solo beat, whether full-cast is reserved for
the climax, rotation-floor met). **Read those numbers, then judge** — present a one-line health read and
the thinnest axis, let the user dial complexity with AskUserQuestion, apply changes to the outline, and
**re-review the story for coherence** (consistency, foreshadowing, hooks) after every edit. Re-run
`scorecard.py` after each edit; loop until the user is happy with the shape.

### 5. Expand + distill — `references/design.md` §3 and `references/compile.md`
With the shape frozen: write the full cards (one subagent per character; the design ref explains how),
the `world/lore/<id>.md` bodies, and `state.seed.json`. Then produce the two distilled files — **the part
unique to baked games**:
- `SKILL.md` — fill the play-loop template: language policy, opening, creative placeholders (id, title,
  module list and drift/coaching lines were already filled by `compile.py` — verify them).
- `mechanics.md` — distill this game's active modules + the universal craft into one tuned guide.
**`references/compile.md` is the exact spec** for both files. Read it before writing them.

### 6. Validate — `scripts/validate.py` (deterministic) + `references/design.md` (gates)
Run the **deterministic** half first — don't hand-check it:

```bash
python3 "$SKILL/scripts/validate.py" --id <id>
```

It mechanically checks the whole floor (required files; no leftover `{{placeholders}}`;
`state.seed.json` parses & `meta.game_id == <id>`; opening cards exist; hidden `public:no` lore has a
body file; every world/characters/story path the SKILL/mechanics reference resolves; frontmatter
`name == <id>` with a description; the engine is bundled; `load.py --game <id>` actually runs) and
exits non-zero on any **FAIL**. **Fix every FAIL and re-run until it exits 0;** then eyeball the
**WARN**s (e.g. non-ASCII that must be a lore keyword or a `word (中文)` gloss, not stray prose).

A green `validate.py` is the *floor, not the ceiling* — it can't judge quality. With it passing, run
the **`references/design.md` §4 judgment gates by hand**: ensemble-depth for the cast pattern (rotating:
real rotation, solo time, full-cast only at climax), character-legibility, heroine-beauty (romance). The checklist in `references/compile.md`
maps each item to whether validate.py covers it or you must judge it. If a gate fails, fix the content
(and re-run the scorecard if the shape moved).

### 7. Engineering polish before ship — OPTIONAL, delegate to `skill-creator`
Only if the user asks for it or the `skill-creator` skill is available: with the game's **content frozen
and gates green**, spawn a subagent that invokes **`skill-creator`** to polish the baked skill *as a
Claude skill* — SKILL.md frontmatter, the `description` so `/<id>` triggers crisply on this game (and
stays quiet otherwise), and overall skill structure/conventions. Otherwise skip it.
- **★ Hard boundary — skill-creator may touch ONLY the skill-engineering surface.** It must **not** alter
  game content (`world/ characters/ story/`) or the *meaning* of `mechanics.md`, the language policy, the
  active-module list, or the opening. Those already passed the gates; rewriting them would silently break
  the coherence you just verified. Hand the subagent this boundary explicitly.
- **★ Regression check after the polish:** `/<id>` still triggers, `load.py --game <id>` still runs, and
  the SKILL's hardcoded invariants (id / language policy / module list / opening / resume command `/<id>`)
  are unchanged. If the polish moved any of them, revert that part.

Then tell the user the game is ready — they play it by typing **`/<id>`** (New Game on first run).

## References (load on demand)
| File | Load when |
|---|---|
| `references/design.md` | designing the world: interview, cast/lore/arc craft, the quality gates, complexity tuning |
| `references/compile.md` | writing the two distilled files (SKILL.md + mechanics.md) and running the baked-skill checklist |
| `story-structures/<name>.md` | after the combo is chosen — ONLY the chosen spine (phases, pressure, cast pattern, swapped rules) |
| `assets/variation-tables.json` | never read by hand — `scripts/roll.py` draws from it (edit it to add options) |
| `module-library/<name>.md` | distilling a module's rules into a game's mechanics.md (`romance`, `magic-potency`, `language-coaching`, `drift`) |
| `engine/references/{gm-protocol,drama-craft}.md` | the universal GM craft you distill into mechanics.md (engine = the canonical source under this skill) |
| `assets/*.template.md`, `assets/state.template.json` | the shape of each content file |

## Principles
- **Distill, don't copy.** A baked game must never need the generic engine at play time. If you find
  yourself telling the SKILL to "load the engine", you haven't distilled enough.
- **Hardcode what's fixed for this game** (language, modules, opening, id) so the play loop carries no
  runtime branching.
- **Keep the lazy content tree lazy.** Lore fires on keyword; cards load when present. Don't inline
  the whole world into SKILL.md — that just moves the bloat.
- **Self-contained games; one canonical engine.** The engine source lives once here
  (`rpg-creator/engine/`); `compile.py` copies it into each game's own `engine/` so the game is
  portable with no shared dependency. Improve the engine here, then re-sync games with
  `compile.py --id <id> --update-engine`.
- **Roll, don't converge.** Start every design from `roll.py`; the chosen structure, not habit, sets
  the spine, pressure and cast pattern.
- Everything else — varied drives, cast patterns, heroine beauty (romance), English-authored files,
  18+, plant-secrets-not-exposition — is in `references/design.md` and still applies.
