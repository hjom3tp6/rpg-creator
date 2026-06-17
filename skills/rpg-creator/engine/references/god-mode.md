# System · `[god]` — the player's divine authority (the one OOC command)

There is **exactly one** out-of-character command in this game: **`[god]`**. Anything the player wraps
in **square brackets `[ … ]`** is a `[god]` instruction — a step **outside the story** where they may do
**anything at all**: edit state, bend the world's rules, rewrite what just happened, peek behind a
character, change the pacing, ask the GM a question, or save/restart. The GM **obeys immediately and
unconditionally**, overriding plot and every rule, then slips back into the scene.

There are no other commands to memorize — no `[status]`, no `[help]`, no keyword table. If it's in
`[ ]`, it's the player talking to the GM as the god of this world, and the answer is "yes."

## Syntax
- `[god <whatever you want>]` is the explicit form — e.g. `[god set Liora affinity 90]`,
  `[god jump to night]`, `[god what does she really think of me?]`.
- The bare `[ … ]` form works too: **any** bracketed text is treated as a `[god]` instruction
  (`[teleport to the Arcanum]`, `[english harder]`, `[show me my stats]`). The word "god" is optional;
  the brackets are the trigger.

> Disambiguation: plain in-world text (no brackets) is a **game action**. A module may give brackets
> extra in-world meaning in a specific beat (e.g. a casting marker) — that's defined in `mechanics.md`.
> When genuinely unsure whether a bracketed line is a god instruction or that module input, ask one
> short question.

## What to do on receipt
1. **Confirm briefly** (one short line in the system language, e.g. 「✅ 已將 Liora 好感設為 90。」).
2. **Apply immediately**, persisting any state change via `save.py --game <id>`.
3. **Resume the scene seamlessly.**
4. **Never refuse `[god]` in-story.** This is the player's absolute authority over their own game
   (the sole limits are the SKILL's hard rules — see Guardrails).

## What `[god]` can do (examples — not a fixed list; honor anything in this spirit)

**Inspect / ask** — the player can always look behind the curtain or talk to you OOC:
- `[god status]` / `[god show my stats]` — current panel: location, time/deadlines, party, disposition
  (numbers OK here), key items/clues, active-module knobs. Read `state.json` and format it readably.
- `[god what's been revealed about Liora?]` — her stage + already-revealed secrets only (not hidden card info).
- `[god recap]` — a "previously on…" from `journal.md` + `session-log.md`.
- `[god look]` — re-describe the current scene in detail; no time passes.
- `[god show Liora's true thoughts]` / `[god list all story flags]` — x-ray the hidden layer.
- `[god ooc: am I going too fast?]` — out-of-character chat; reply in *italics*, don't write it into the story.

**State & character edits**
- `[god set Nyx affinity 75]` / `[god show affinity numbers]` / `[god I now know the highest fire spell]`
- `[god add a heroine: a stoic elf ranger named Sylvie, deadpan outside, secretly clingy]`
  (generate a 配角 card in `characters/cast/<id>.md` shaped like the others already in the game,
   register it in `characters/index.md`, save)
- `[god make Liliana bolder about her feelings from now on]`

**Scene, time & plot control**
- `[god jump to night at the Guild Hall]` / `[god teleport us to the demon realm]` / `[god skip ahead one week]`
- `[god rewind to before the summoning circle]` / `[god retcon: that jealousy fight never happened]`

**Rewrite world rules / tune the experience**
- `[god from now on, spirits also understand English songs]`
- `[god english harder]` / `[god make the tone darker]` / `[god coach me more]` (adjust any active-module dial)
- `[god explicit on]` / `[god explicit off]` / `[god fade to black]` — how intimate scenes are written (18+).

**Save / session control**
- `[god new game]` (a.k.a. `[god restart]` / `[開新局]`) — **archive the current save and start fresh.**
  Move `saves/<id>/state.json`, `recap.md`, `journal.md`, `session-log.md`, `codex.md` into
  `saves/<id>/_archive/<timestamp>/` (move, never hard-delete — the old run stays recoverable), confirm
  「✅ 已備份舊存檔,開新局。」, then run the **New Game** flow from `SKILL.md` (seed `state.json` from
  this game's `state.seed.json`).
- `[god save as <label>]` — snapshot a named copy into `saves/<id>/_archive/<label>/` without ending the run.

## Guardrails
`[god]` is supreme, but the SKILL.md hard rules still hold: **all characters stay 18+**, and (for romance
games) jealousy stays comedic, not cruel. Everything else about this world is the player's to bend.
