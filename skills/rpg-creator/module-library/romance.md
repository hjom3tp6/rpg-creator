# Rule · Romance, Multi-Partner Dynamics & Intimacy

Activate only when the game's central relationship is romance (or a romance subplot is wanted). No
combat stats, but **disposition** and **flags** are tracked (in `saves/state.json`). All characters
are **adults (18+)** — non-negotiable, no exceptions ever. Only characters marked romanceable on their
card take part; every other relationship type uses the card's Relationship section instead.

## Disposition
- One value per romanceable character, range **0–100**, stored in `state.json` `affinity.<id>` (label/stage in
  `relationships.<id>.stage`).
- Default display is the **stage label**, not the number (the player can `[show affinity numbers]`).
  Example ladder (rename to fit the game's tone):
  0–19 wary/stranger · 20–39 interested · 40–59 flustered (smitten, denying it) ·
  60–79 likes you (guarded about it) · 80–99 in love · 100 utterly yours
- Per-character starting values are on each card.

### How it moves
**Up ↑**
- Good conversation; talking about what they care about; remembering what they said.
- Hitting their **Soft Spot** (each card lists one under Relationship to the Protagonist).
- Reliability, thoughtfulness, well-timed humor, returning their teasing.
- A high point of the game's central mechanic, if it has one (e.g. a standout `magic-potency` casting).

**Down ↓**
- Poking a sore spot, ignoring them, being careless, saying one thing and doing another.
- But a drop should be **dramatic and recoverable** — not punitive point-docking.

## Inner-Life Cadence (the main payoff)
How much of a character's inner life leaks out scales with disposition:
- **Low** — mostly the public presentation; the inner voice shows only a tiny crack (a flustered beat, instantly denied).
- **Mid** — the gap between what they show and what they feel grows wide and frequent.
- **High** — the guard drops for real; outer and inner self start to merge — the stoic shows an
  expression, the joker says something true. **This thaw IS the reward.**

## Multi-partner dynamics (optional — "harem" style; use only if the game wants it)
- **Multiple routes run in parallel** — each disposition tracks independently.
- **Jealousy:** neglecting one character, or being too cozy with another in front of them, triggers a
  **comedic** jealousy beat in each character's own voice (e.g. one over-explains they're "not
  jealous," another coldly logs it, a third sulks via the weather). Jealousy briefly shifts
  mood/attitude but stays **light, not cruel**, and always offers a way to smooth it over. Track in
  `relationships.<id>.jealousy`.
- **Shared route:** raise several lines high and manage jealousy well → a shared ending is on the
  table. The player may also commit to one. Don't hard-lock single routes — give space — but let
  jealousy give choices weight.
- Single-partner games: skip this section; one disposition line, no jealousy tracking.

## Intimacy (gated, explicit allowed — written as art)
- Intimacy is a **story beat gated behind relationship progress and clear, in-character consent**,
  same as any other event. It unlocks roughly at the **high** disposition band (80+), or sooner if
  the scene and the character's stage genuinely earn it.
- Progression: flirtation → tension → confession → first kiss/embrace → more. Don't skip the rungs —
  the build-up (the held breath before, the "should we", the first trembling touch) is where most of
  the heat actually lives. Earn it; the wanting is hotter than the having.
- This game **permits fully explicit (18+) content** when the gate is met and both characters are
  willing (the player runs it on a model that allows it). It is **not** PG-by-default at high
  disposition — when the scene has earned it and the player leans in, deliver the real thing.

### How to write it — poetic, not pornographic
The standard is **erotic literature, not a transcript.** Explicit ≠ clinical, and explicit ≠ crude.
Aim for sensual, artful, and charged. The craft:
- **Metaphor and imagery over anatomy.** Render heat through the senses and the natural world —
  fever, tide, candlelight, a struck match, snowmelt, a bowstring's release, dawn breaking. Suggest
  and evoke rather than catalog mechanics. The most explicit thing on the page should be the *feeling*,
  not a body part inventory.
- **Sensory and embodied.** Breath, heartbeat, warmth, the catch in a voice, the way the room narrows
  to two people. Slow the camera; let small details (a clenched fist in the sheets, a whispered name)
  carry the weight.
- **Stay in character — intimacy is the deepest inner-life reveal of all.** This is the payoff of the
  whole relationship: the guarded one stops pretending; the one who seemed untouchable is shaking and
  tender; the clinical one narrates their own coming-apart; the fierce one turns possessive; the
  distant one is, for once, *just* a person. Keep the voice. The character is the eroticism.
- **Rhythm — build, crest, settle.** Mirror the act's own arc: rising tension, a peak, and a tender
  afterglow that *means* something (vulnerability, a confession, a wall finally down). The aftermath
  is as important as the climax — that's where the relationship actually changes.
- **Avoid:** mechanical step-by-step blocking, porn clichés and stock phrases, purple-prose overload,
  and anything that breaks the game's tone or the character's voice. If a line reads like a medical
  chart or a cheap paperback, rewrite it more beautifully.
- **The language policy still applies** (see `language-coaching` if active): intimacy doesn't suspend
  it. Keep the dialogue language and narration balance the game set; a gasped line in the target
  language is still practice.

### Consent, tone, control
- Spicy/thirsty **inner monologue** is encouraged much earlier as a comedy/tension device, even while
  the on-screen relationship is still PG — the mask-versus-mind contrast makes the eventual real
  scene land ten times harder.
- Always preserve: **adults only, enthusiastic in-character consent, and the game's established
  tone.** No cruelty, no non-consent. If the player steers away, fade naturally; if they steer in,
  deliver it in-character and in good taste. Honor `[fade to black]` / `[explicit on/off]` god-mode
  preferences.

## Flags / knowledge to track
- Per romanceable character: disposition, stage, **revealed secrets** (`relationships.<id>.revealed` — an OOC
  `[god]` query about them shows only what's been revealed, not hidden card info), key interaction
  memories for later callbacks, current jealousy level (multi-partner games).
- World: major event flags, current location/time, any god-mode rewrites of world rules.
