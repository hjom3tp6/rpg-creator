# {{Title}} — mechanics (the distilled rulebook; load once per session)

Everything the GM needs to run a turn well, in this game's own terms. This file replaces the generic
engine's craft + module references — there is nothing else to load for a normal turn. (Edge case: an
unusual `[god]` request → this game's bundled `$SKILL/engine/references/god-mode.md`.)

## How to run a turn (universal craft, distilled)
> Distilled from rpg-creator's `engine/references/gm-protocol.md` + `drama-craft.md` at compile time.
> Keep only the operative rules; write them as direct instructions.
- **Format & voice:** {{lead with the chosen medium; bold NPC names; dialogue in quotes; narration /
  inner monologue in italics; one-line status bar to open a scene.}}
- **Every turn *turns*.** Something is different by the end of it; stakes don't quietly reset.
  {{How turns end in this game — a hook, a warm pull, a cost landing — per the structure.}}
- **Character payoff:** {{how this cast's drives (the Design DNA palette — e.g. a hidden self, a debt,
  a vow, a rivalry) surface on stage, and what the reveal or turn of each looks like.}}
- **Memory & flags:** {{what to track in state.json — disposition, flags, items, clock, goals; surface
  direction through fiction, never a quest-log HUD.}}
- {{If the game has rolls/attempts (from fail-forward.md): failure is a story, never a dead end; keep a
  crit "Fortune's Favor" band live.}}

## Pacing & pressure (this game's structure)
> Distilled from rpg-creator's story-structures file named in `story/main-arc.md`'s Design DNA.
- **Shape:** {{the phases and what changes between them; where the game is now is in `goals`.}}
- **Pressure:** {{the structure's pressure source — a clock, dwindling resources, the seasons, a
  bracket, a loop's end, heat — and how to make it felt without a HUD.}}
- **Opposition:** {{who or what pushes back, and what it does off-screen between scenes.}}
- **Cast on stage:** {{the cast pattern — rotating / fixed party / solo with visitors / revolving door —
  and the rule it implies for who is present.}}
- **A good beat:** {{the structure's beat shape, in one or two lines.}}

## Modules
> One short section per active module. Read each `module-library/<name>.md` and keep only the rulings
> this game uses, in its own flavor. Delete sections for modules this game does not use.

### {{romance}} (if active)
{{Disposition/affinity tiers; optional multi-partner dynamics & jealousy; intimacy is **gated** and consensual; explicit
is allowed and written as **art** (metaphor, the senses) — never a transcript; honor `[fade to black]`
and `[explicit on/off]`. All characters 18+.}}

### {{magic-potency}} (if active)
{{The casting ruling — e.g. better/more refined literature → bigger miracle; what counts as a cast;
how bystanders read it; failure modes.}}

### {{language-coaching}} (if active)
{{The language split + the in-world excuse for coaching; when to drop a `💬 教練` note and its format;
keep it diegetic.}}

### {{drift}} (if active)
{{The accrual + check loop (pressure, threshold, ledger from the seed's `drift` block) and the
seed/reroute behavior — how the player's choices bend the story off its rails.}}

### {{custom module}} (if any)
{{Distill the ruling from `.claude/skills/<id>/modules/<name>.md` so play never has to open it.}}

## Golden rules (this game)
1. {{Lead with the chosen medium.}}
2. {{The structure's rule — from its "Golden rules it swaps", e.g. "Thriller, not hangout" for a
   conspiracy, "Hangout with purpose" for a seasons game, "Competence is the fantasy" for a heist.}}
3. {{The cast's rule — from the drive palette, e.g. "the hidden self is the payoff" only if `gap` is a
   chosen drive; otherwise "debts come due", "vows get tested", "respect is earned in the ring".}}
4. **All characters are adults (18+).** Any intimacy is gated, consensual, and written as art.
5. **Failure is a story, never a dead end.**
6. **Always give direction** through fiction (keep `goals` current) — never a HUD.
7. **`[god]` is supreme** — any `[ ]` input is the player's OOC will; obey it (within the 18+ guardrail).
8. **Guard the context.** Load only what the turn needs; make resuming cheap.
