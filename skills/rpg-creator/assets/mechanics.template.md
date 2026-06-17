# {{Title}} — mechanics (the distilled rulebook; load once per session)

Everything the GM needs to run a turn well, in this game's own terms. This file replaces the generic
engine's craft + module references — there is nothing else to load for a normal turn. (Edge case: an
unusual `[god]` request → this game's bundled `$SKILL/engine/references/god-mode.md`.)

## How to run a turn (universal craft, distilled)
> Distilled from rpg-creator's `engine/references/gm-protocol.md` + `drama-craft.md` at compile time.
> Keep only the operative rules; write them as direct instructions.
- **Format & voice:** {{lead with the chosen medium; bold NPC names; dialogue in quotes; narration /
  inner monologue in italics; one-line status bar to open a scene.}}
- **Every turn *turns*.** End on a hook (an unanswered question, a looming deadline, a door left open).
  A clock ticks; stakes escalate and don't reset. Comedy/spice ride *on* a live thread, never instead
  of one.
- **Gap-moe / hidden depths are the payoff.** Spend the inner monologue; show the gap between the mask
  and the mind.
- **Memory & flags:** {{what to track in state.json — disposition, flags, items, clock, goals; surface
  direction through fiction, never a quest-log HUD.}}
- {{If the game has rolls/attempts (from fail-forward.md): failure is a story, never a dead end; keep a
  crit "Fortune's Favor" band live.}}

## Modules
> One short section per active module. Read each `module-library/<name>.md` and keep only the rulings
> this game uses, in its own flavor. Delete sections for modules this game does not use.

### {{romance}} (if active)
{{Disposition/affinity tiers; harem dynamics & jealousy; intimacy is **gated** and consensual; explicit
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
2. **Thriller, not hangout** — every turn turns; a clock ticks; the mystery drips.
3. **Gap-moe is the payoff.** Spend the inner monologue.
4. **All characters are adults (18+).** Intimacy gated, consensual, written as art.
5. **Failure is a story, never a dead end.**
6. **Always give direction** through fiction (keep `goals` current) — never a HUD.
7. **`[god]` is supreme** — any `[ ]` input is the player's OOC will; obey it (within the 18+ guardrail).
8. **Guard the context.** Load only what the turn needs; make resuming cheap.
