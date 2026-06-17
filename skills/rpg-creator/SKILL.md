---
name: rpg-creator
description: >-
  Author a brand-new narrative RPG and COMPILE it into its own self-contained, directly-playable
  skill under .claude/skills/<id>/ — a "baked game". This is skill-creator + world-forge fused: you
  interview/design a complete world (premise, cast, lore, story, mechanics), then emit a lean,
  game-specific SKILL.md + distilled mechanics.md + content tree that the player runs with its own
  slash command (e.g. /spirit-tongue), with no generic engine loaded at play time. Use WHENEVER the
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
    module-library/  assets/  references/{design,compile}.md  scripts/compile.py
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
4. **The invariants → bundled, not shared.** `compile.py` copies the engine (save/load scripts + the
   one rare-path ref `god-mode.md`, for the sole OOC command `[god]`) into the game's own `engine/`
   folder, so the game is self-contained. The baked SKILL points at `$SKILL/engine/…` and loads that
   reference only on an edge case. (Scripts are executed, never read into context — zero play-time token cost.)

The result: a game that plays like the old engine but boots from its lean SKILL.md + mechanics.md
(measured ~280 lines for the bundled spirit-tongue, vs ~700+ of generic engine/rules scaffolding the
old `/rpg` reloaded each session), and makes almost no runtime "what should I load?" decisions. (Per
turn, state reads are further trimmed by `load.py --hot` — the volatile core only.)

## Workflow

### 1. Design the world — `references/design.md`
Interview the user, then design a coherent, opinionated world: premise, tone, language policy, active
modules, a gap-driven cast, a clocked spine, and a rotating presence matrix. All the world-design
craft, the mandatory quality gates (ensemble-depth, character-legibility, heroine-beauty), and the
authoring-language rule live in **`references/design.md`** — read it before designing. Delegate each
character card to its own subagent for depth (the design ref explains how).

### 2. Scaffold the baked skill — `scripts/compile.py`
Pick a short **kebab-case id** (= the skill folder name **and** the slash command, e.g. `neon-shrine`
→ `/neon-shrine`). Let **`$SKILL`** = this skill's base directory — the absolute path printed as *"Base
directory for this skill"* at invocation (this resolves correctly whether rpg-creator runs as a local
project skill or an installed plugin, so never hardcode `.claude/skills/rpg-creator`). Then, from the
project root (the new game lands in *this* project's `.claude/skills/<id>/`):

```bash
# fresh game (the usual path): lay down the baked skill dir with content stubs + the two templates
python3 "$SKILL/scripts/compile.py" --id <id>

# fork: seed a new game from an EXISTING content dir (copies its world/ characters/ story/ + seed),
# e.g. branch off another baked game:  --from .claude/skills/<other-game>
python3 "$SKILL/scripts/compile.py" --id <id> --from .claude/skills/<other-game>
```

This creates `.claude/skills/<id>/` with the folder tree, the SKILL.md & mechanics.md **templates** to
fill, and the game's own bundled `engine/` (so it's self-contained). Content is either stubs (fresh) or
copied from `--from`. It never overwrites an existing baked skill unless you pass `--force`.

### 3. Fill the content, then COMPILE the two distilled files — `references/compile.md`
- Fill the world content (`world/ characters/ story/ state.seed.json`) per `references/design.md`.
  For a `--from` migration this is already populated — review it instead.
- Then produce the two distilled files — **this is the part unique to baked games**:
  - `SKILL.md` — fill the play-loop template: hardcode id, title, language policy, module list,
    opening, resume command `/<id>`.
  - `mechanics.md` — distill this game's active modules + the universal craft into one tuned guide.
  **`references/compile.md` is the exact spec** for both files (what to inline, what to reference,
  what to drop). Read it before writing them.

### 4. Validate & hand off — `references/compile.md` (checklist) + `references/design.md` (gates)
Run the baked-skill sanity checks (every path the SKILL references resolves; `state.seed.json` parses;
`load.py --game <id>` works; no generic-engine assumptions leaked into the loop) plus the design gates.
Then tell the user the game is ready and they can play it by typing **`/<id>`** (New Game on first run).

### 5. Complexity review & tuning — `references/design.md`
Show a structural scorecard, let the user dial complexity with AskUserQuestion, apply changes, and
**re-review the whole story for coherence** (consistency, foreshadowing, hooks) after every edit, then
re-distill `mechanics.md`/`SKILL.md` if the changes touched mechanics or the opening. Loop until ship.

## References (load on demand)
| File | Load when |
|---|---|
| `references/design.md` | designing the world: interview, cast/lore/arc craft, the quality gates, complexity tuning |
| `references/compile.md` | writing the two distilled files (SKILL.md + mechanics.md) and running the baked-skill checklist |
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
- Everything else — gap-driven cast, rotating presence, heroine beauty, English-authored files, 18+,
  plant-secrets-not-exposition — is in `references/design.md` and still applies.
