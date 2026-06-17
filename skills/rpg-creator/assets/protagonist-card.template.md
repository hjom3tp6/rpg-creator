<!-- 主角 (PROTAGONIST / PLAYER) card. Lives at characters/player.md — the engine's state.json points
     `player.persona_file` here, so keep this filename. ONE per game.

     Same SillyTavern-V2 lineage as the 配角 (supporting) card, re-aimed at the character the player
     inhabits: there is no "disposition toward the player" and no first-meeting greeting; instead this
     card fixes who the player IS, how the GM narrates them, and what the world keeps pulling them into.
     ST fields are noted in <!-- --> for parity.

     Volatile state (location, inventory, stats, relationships) lives in saves/<id>/state.json, NOT here.
     The protagonist is an adult (18+). -->

# {{Player default name}} — {{epithet, e.g. "the washed-up summoner"}}

- **id:** player
- **Role:** {{who the player is in this world — their station, job, reputation}}
- **Age:** {{a concrete adult age or tight range — 18+}}
- **Tags:** {{comma, separated, e.g. underdog, exiled-noble, secretly-powerful}}  <!-- ST: tags -->
- **Default control:** {{how much the GM voices the protagonist vs. waits for the player — e.g. "narrate actions, but quote the player's lines only when the player writes them"}}

## Appearance  <!-- ST: description (visual) — how the world sees the player; lighter than an NPC's -->
- **Build & look:** {{the broad strokes others notice}}
- **Signature detail:** {{the one thing that marks them — a scar, a relic, worn gear}}

## Background  <!-- ST: description — where they come from and why it matters now -->
{{1–2 paragraphs: history that shaped them and the wound/legacy the story will press on.}}

## Personality & Voice  <!-- ST: personality — traits + how their narration/dialogue should read -->
{{Temperament in a few adjectives, plus the register of their inner voice (dry, earnest, horny-but-
hiding-it…) so the GM keeps the POV consistent.}}

## Wants & Drive
- **Stated goal:** {{what the player says they're after}}
- **True drive:** {{the deeper need the arc satisfies — may differ from the stated goal}}
- **Flaw / wound:** {{the thing that holds them back; what growth looks like}}

## Starting Situation  <!-- ST: scenario — the world-state at New Game, the opening hook -->
{{Where they are and what's pressing on them as the game opens — the situation the SKILL's opening beat
drops the player into.}}

## The World's Pull
{{What keeps dragging them into the plot — the hook that makes staying out of it impossible.}}

## Core Power / Mechanic 🔒
{{The protagonist's central ability or gimmick and how it works at the start. Delete if the game has
no such mechanic. Spoiler-gated growth can be noted for the GM.}}

## Example Voice  <!-- ST: mes_example — sample lines/inner monologue so the GM renders the player right -->
<!-- Only used when the GM voices the protagonist (per Default control). "Player:" is the protagonist;
     we don't use SillyTavern's {{char}} macro here — {{...}} means "fill this in". -->
<START>
Player: *{{a sample inner monologue in their register}}* "{{a sample spoken line}}"

## GM Directives — narrating the player  <!-- ST: system_prompt + post_history_instructions -->
- **Always:** {{keep POV/agency rules — e.g. never decide the player's feelings or choices for them}}
- **Offer:** {{the kinds of options to surface each turn so the player steers}}
- **Never:** {{railroad, mind-read, or speak the player's committed lines unprompted}}

## Author Notes (OOC — never shown)  <!-- ST: creator_notes -->
{{Design intent for the protagonist's arc; how they pair against the cast. Backstage only.}}
