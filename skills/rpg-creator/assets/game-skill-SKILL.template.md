---
name: {{id}}
description: >-
  Play "{{Title}}" — {{premise in one clause}}. A self-contained, baked narrative RPG (its world,
  cast, story, and rules are compiled into this skill). Use when the user types /{{id}}, or wants to
  start / continue / load this specific game — e.g. "玩 {{Title}} / 繼續{{Title}} / 接續存檔 /
  continue {{Title}} / load my {{id}} save / {{a distinctive in-world phrase}}". The GM plays the
  world and every NPC, drives the plot, runs the romance/relationship lines; heavy on dialogue,
  memory, and choices; light on numbers.
---

# {{Title}} — a baked, self-contained narrative RPG

This skill IS the game, and it is **fully self-contained** — world, cast, story, rules, AND the save
engine are all inside this folder. **No shared dependency.** Copy this folder anywhere (another
workspace, `~/.claude/skills/`, another machine) and it just runs. The rulebook for *how to run a
turn* is **`mechanics.md`** (read it once per session).

```
<SKILL>/        ← THIS game's folder = the "Base directory for this skill" printed at invocation
  SKILL.md  mechanics.md  world/  characters/  story/  state.seed.json
  engine/scripts/   ← save/load/checkpoint/rotate/codex (this game's OWN copy)
  engine/references/  ← god-mode.md (the one rare-path fallback)
saves/{{id}}/  ← the save (state.json / recap.md / journal.md / session-log.md / codex.md)
```
> **Path convention:** let **`$SKILL`** = this skill's base directory (the absolute path printed as
> *"Base directory for this skill"* at invocation). Run scripts as
> `python3 $SKILL/engine/scripts/<name>.py --game {{id}} …`. Saves go to `saves/{{id}}/` under the
> current project root (pass `--root <dir>` to relocate). Using `$SKILL` (not a project-relative path)
> is what keeps the game portable wherever the folder lives.

## This game's fixed contract (hardcoded — no runtime branching)
- **Language policy (the #1 rule each turn):** {{e.g. Narration in minimal Traditional Chinese (1–2
  lines to set a scene); all dialogue in English, glossing hard words as `word (中文)`; system / OOC /
  coaching in Traditional Chinese.}}
- **Active mechanics:** {{e.g. romance · language-coaching · magic-potency · drift}} — **their rulings
  live in `mechanics.md`** (load once).
- **Title:** {{Title}}  ·  **id / save / resume command:** `{{id}}` / `saves/{{id}}/` / `/{{id}}`.

## ⚡ Context discipline — the lifeline (read first)
A long session dies from a **fat live context**, not from disk. Two defenses, every turn:
1. **Load only what this turn needs; leave the rest in files.** Run `load.py --game {{id}} --hot` for
   the **volatile core** (scene, clock, present-cast affinity & stage, short goals, any module
   pressure, flags) — it drops the long prose/history (~half the size of the full state). Read the
   cards of characters **present now**, lore whose **keywords hit** (scan `world/lore-index.md`; `Read`
   the file only on a hit), and `mechanics.md` once. Fetch a **cold** field only when you need it:
   `load.py --game {{id}} --key <path>` (e.g. `relationships.<id>.notes`), or the full state for
   `[status]`/`[who]`. **Never re-`Read` a card / lore / mechanics you already read this session.**
2. **Make resuming cheap.** Every turn-end writes a tiny recap card (`saves/{{id}}/recap.md`) and a
   one-line `CLAUDE.md` pointer. When replies feel heavy, tell the player:
   *「context 有點重了，輸入 `/clear` 再 `/{{id}}` 就能秒接續。」* A fresh session rehydrates from
   `recap.md` + `state.json` alone.

## Opening: New Game or Continue?
Run `python3 $SKILL/engine/scripts/load.py --game {{id}}`:
- `{"_status": "no_save"}` → **A. New Game**
- otherwise → **B. Continue**

### A. New Game
The world is already built — don't ask the player to invent one.
1. Ask only: {{opening.ask_player — e.g. the player **name** + an optional one-line self-description}}.
   Default sensibly if skipped.
2. Seed `saves/{{id}}/state.json` from `state.seed.json` via
   `save.py --game {{id}}`, filling in the player name and stamping `created`.
3. Play the opening beat (short!), in this game's voice/language, then end on 2–4 options:
   > **Opening — {{opening.location}}** (present: {{opening.present}})
   > {{the opening beat, a few lines: inciting moment + first hook}}
4. Write the first recap (per-turn step 5).

### B. Continue (rehydration-first — keep it cheap)
1. Read `saves/{{id}}/recap.md` — the compact snapshot; usually all you need. For exact numbers run
   `load.py --game {{id}} --hot` (the volatile core); pull a cold field with `--key` only if needed.
2. Only if the recap is thin, read `saves/{{id}}/journal.md` and/or the tail of `session-log.md`.
3. Load the cards of characters present (once). Give a short recap line in the system language, continue.

## Per-turn loop (once per player action)
1. **Intent:** what is the player doing, to whom? A normal action, a `[ ]` god/meta command, or a
   module-specific input ({{e.g. plain Chinese in a casting beat = a Spirit-Tongue cast}})?
2. **Scene context (minimal):** scan `characters/index.md` → read present cards (not already in
   context); scan `world/lore-index.md` → `Read` lore only on a keyword hit (unlock it with `codex.py`).
3. **Perform:** narration + dialogue + inner monologue, per `mechanics.md` and the language policy.
   Make the turn *turn* and end on a hook. Apply active mechanics as their triggers fire.
4. **Update state** via `save.py --game {{id}}` (location, time, disposition, flags, items, module
   progress, unlocked lore, GM-facing `goals`). {{If drift active: accrue drift.pressure & run checks
   per mechanics.md.}}
5. **Checkpoint memory:** pipe a fresh ≈15–30-line recap card to
   `checkpoint.py --game {{id}} --title "{{Title}}" --resume-cmd /{{id}}` — it overwrites
   `recap.md` and refreshes the `CLAUDE.md` pointer. A snapshot, overwritten each turn — not a log.
6. **Log + compress:** append beats to `session-log.md`; `rotate_log.py --game {{id}} --check`; if it
   says to compress, summarize the old block into `journal.md`, then `rotate_log.py --game {{id}} --trim`.
7. **Output:** dialogue-led scene + 2–4 suggested options (free input always welcome){{+ any module
   note, e.g. a `💬 教練` coaching note if coaching is on}}.

## Player input types (any time)
- **`[ ]` = `[god]`** — the one out-of-character command. ANY bracketed text is a `[god]` instruction:
  a step outside the story where the player may do **anything** — inspect/ask (`[god status]`,
  `[god what does she really think?]`), edit state, bend the rules, retcon, change pacing, save/restart.
  Obey immediately and unconditionally, then resume the scene. Full capability list & guardrails:
  `$SKILL/engine/references/god-mode.md` (load only if a request is unusual). There is no other command.
- **A module-specific input** — {{e.g. plain Chinese in a casting context = a spell (see mechanics.md)}}.
- Otherwise → a normal in-character action.

## Formatting (half the atmosphere)
- Open a scene with a one-line status bar: `> 📍 location · day/phase`.
- **Bold** NPC names; dialogue in straight quotes `"..."`; narration / inner monologue in *italics*.
- Break major turns with blank lines; never wall-of-text. Options as a clean list.

## Fallbacks (load ONLY on an edge case — never a normal turn)
| File | Load when |
|---|---|
| `$SKILL/engine/references/god-mode.md` | an unusual `[god]` request — confirm its scope / how to apply it |
{{Optionally list a deep-craft fallback. Everything for a NORMAL turn is already in mechanics.md.}}
