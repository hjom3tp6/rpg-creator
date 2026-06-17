# Compile — emit the two distilled files that make a game self-contained

Load this when the world content is written (`references/design.md` §3) and you're producing the parts
unique to a **baked game**: its `SKILL.md` (specialized play loop) and `mechanics.md` (distilled
rules). These two replace the entire generic engine at play time, so getting them right is what buys
the context win. `compile.py` has already laid down both as templates in `.claude/skills/<id>/`.

## The contract a baked game must satisfy
At play time the baked skill loads, in a normal turn:
- its own `SKILL.md` (boots the loop),
- `mechanics.md` **once** (the tuned rulebook),
- the scene's content (present cards; lore on a keyword hit) — lazily, same as always.

It must **never** need anything outside its own folder for a normal turn — the universal craft is
distilled into `mechanics.md`. It loads its one bundled `$SKILL/engine/references/` file live only for a
genuine edge case (an unusual `[god]` request whose scope/application needs confirming → `god-mode.md`).
If your loop tells the player's GM to read a craft file every turn, you haven't distilled enough.
(`$SKILL` = the skill's base directory, printed at invocation.)

## File A — `SKILL.md` (the specialized play loop)
Fill the template `assets/game-skill-SKILL.template.md` already copied in. Rules:

1. **Frontmatter.**
   - `name: <id>` — exactly the folder name; this is the slash command `/<id>`.
   - `description:` — written for THIS game so it triggers on it specifically: the title, its premise
     in a clause, and resume/continue phrasings in **both** the play-time languages and Chinese (the
     user's UI language) — e.g. "繼續…/玩…/continue …/load my … save". Do **not** make it sound generic
     like the old engine; it should win when the user means *this* game and stay quiet otherwise.
2. **Hardcode everything fixed for this game** — no runtime branching survives compilation:
   - the **id** and **title**;
   - the **language policy** as plain prose (e.g. "Narration in minimal Traditional Chinese; all
     dialogue in English, glossing hard words as `word (中文)`; system/coaching in Chinese") — not a
     `language_policy:` block to "honor";
   - the **active-module list** named in plain text, with the line "their rules live in `mechanics.md`";
   - the **opening beat** inlined (location, present cast, the beat, what to ask the player);
   - the **resume command** `/<id>` and the **`$SKILL` path convention** (scripts at
     `$SKILL/engine/scripts/`, where `$SKILL` = the skill's base directory printed at invocation).
3. **Trim the per-turn loop to the steps this game uses.** Drop steps for absent modules (no drift
   accrual line if drift isn't active; no coaching-note line if coaching is off). Keep: intent → minimal
   scene context (read state with `load.py --hot`; scan indexes, load present cards / keyword lore;
   `load.py --key PATH` for a cold field) → perform (per `mechanics.md`) →
   update state (`save.py`) + unlock lore (`codex.py`) → checkpoint (`checkpoint.py --game <id>
   --title "<Title>" --resume-cmd /<id>`) → log + rotate → output (scene + 2–4 options + any module
   note).
4. **Keep the context-discipline + cheap-resume rules** (load only what the turn needs; recap.md +
   state.json rehydrate a fresh session; tell the player to `/clear` then `/<id>` when context feels
   heavy). These are the lifeline and survive into every baked game.
5. **Scripts are called via `$SKILL`**, always with `--game <id>`:
   `python3 $SKILL/engine/scripts/<name>.py --game <id> …` (the game's OWN bundled engine).
6. **Point at the content tree by relative path** under the skill dir: `world/`, `characters/`,
   `story/`, `state.seed.json` (these sit inside the game folder alongside `engine/`).
7. **Fallbacks table** — list only the one rare `$SKILL/engine/references/god-mode.md` file
   with "load ONLY when…" (an unusual `[god]` request). Everything normal is in `mechanics.md`.

## File B — `mechanics.md` (the distilled rulebook — the real compile work)
This is one file that condenses, **in this game's own terms**, everything the GM needs to run a turn
well. Build it by distilling these sources and dropping whatever doesn't apply:

- **Universal craft** → read `engine/references/gm-protocol.md` (format, NPC voice, memory, flags) and
  `engine/references/drama-craft.md` (pacing & tension — every turn *turns* and ends on a hook; a clock
  ticks; stakes escalate) — these are rpg-creator's canonical engine source. Distill the operative rules
  into a tight "How to run a turn" section. Fold in the relevant bits of `engine/references/fail-forward.md`
  (failure is a story; the Fortune's-Favor crit band) if the game has rolls/attempts.
- **Lazy lore + codex** → read `engine/references/lorebook-protocol.md` (keyword-triggered loading of
  `world/lore-index.md` → `world/lore/<id>.md`, and `codex.py` unlocks). This is *the* context-saving
  mechanic, so distill a short "How lore fires & unlocks" note into `mechanics.md` rather than assuming
  it. (It's SillyTavern's World Info on a filesystem; character secrets belong here, not bloating cards.)
- **Each active module** → read `module-library/<name>.md` and write a short section with only the
  rulings this game uses, in its own flavor:
  - `romance` — disposition/affinity, harem dynamics, jealousy, **gated** & consensual intimacy, and
    the art-not-transcript rule for explicit (18+), honoring `[fade to black]` / `[explicit on/off]`.
  - `magic-potency` — the casting ruling (e.g. "better literature → bigger miracle"), what counts as a
    cast, and how bystanders read it.
  - `language-coaching` — the language split + the in-world excuse for coaching, and the `💬 教練` note
    format.
  - `drift` — the accrual + check loop and the seed/reroute behavior (keep the numbers from the seed's
    `drift` block).
  - a **custom** module → distill its `.claude/skills/<id>/modules/<name>.md` ruling here too.
- **The game's golden rules** → a short list specialized from the engine's commandments: lead with the
  chosen medium; thriller-not-hangout; gap-moe is the payoff; 18+ gated intimacy as art; failure is a
  story; always give direction via fiction (keep `goals` current); `[god]` (any `[ ]` input) is supreme
  within the 18+ guardrail; guard the context.

Aim for ~120–160 lines. If it balloons past ~200, you're copying, not distilling — cut caveats and
branches that don't apply to this world. Write it in English (it's authored content); only glossed
samples may carry a `word (中文)` gloss.

> **Custom (non-library) modules:** keep the full ruling file at `.claude/skills/<id>/modules/<name>.md`
> for reference, but still distill its operative rules into `mechanics.md` so play never has to open it.

## Re-distilling after edits
If a complexity-tuning edit (`design.md` §5) changes the **opening**, the **active-module list**, or a
**module's ruling**, re-edit the affected file: opening/module-list/language → `SKILL.md`; module
rulings/craft → `mechanics.md`. Content-only edits (a new lore, a tweaked card) need neither.

## Baked-skill checklist (run before hand-off)
- `name:` in SKILL.md == the folder id; `description` is game-specific and includes resume phrasings.
- The loop references **nothing outside the game folder** for a normal turn; only
  `$SKILL/engine/references/god-mode.md` as the one edge-case fallback. No `games/ACTIVE`, no
  `language_policy:`-to-honor, no module on/off branching, no meta-command table left behind —
  the only OOC command is `[god]`.
- Every path the SKILL names resolves: `world/`, `characters/`, `story/`, `state.seed.json` exist
  under the skill dir; the bundled `engine/scripts/*.py` exist (compile.py auto-copies them; if missing,
  run `compile.py --id <id> --update-engine`).
- `state.seed.json` parses (`python3 -c "import json,sys;json.load(open('.claude/skills/<id>/state.seed.json'))"`)
  and its `meta.game_id` == `<id>`; opening `present_characters` all have cards.
- `python3 .claude/skills/<id>/engine/scripts/load.py --game <id>` runs (prints `no_save` for a fresh
  game, or the existing state for a migration) — confirms the bundled engine works.
- `mechanics.md` covers every module in the SKILL's active list and the universal turn-craft, and is
  not a verbatim copy of the sources.
- Run the `design.md` §4 gates (ensemble-depth, legibility, beauty, authoring-language).
- Tell the user: play it by typing **`/<id>`** (first run = New Game). To retire it, just delete
  `.claude/skills/<id>/` (and optionally `saves/<id>/`).
