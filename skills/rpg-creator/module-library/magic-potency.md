# Rule · Potency by Craft (casting module)

The player's **input quality in a chosen craft** scales the effect. The game picks the craft — a line
of verse, a phrase in a target language, a described technique, a recipe, a melody — and judges the
result by this. Fill `{{craft}}` and the potency tiers in `mechanics.md` for the game's own craft.
The power answers to **meaning, aptness and craft**: the better the input, the greater the effect.

## Potency tiers (adapt the "player input" column to the craft)
| Tier | Player input | Baseline effect |
|------|--------------|------------------|
| 0 · single word / bare gesture | one word, "just hit it" | Faint: a spark, a flicker. Barely useful — good for comedy. |
| 1 · phrase / simple technique | a stock phrase, a basic move | Practical: usable in a fight, solves small problems. |
| 2 · line / skilled technique | a fitting line, a well-described method | Powerful: turns a fight, stuns a crowd. |
| 3 · full composition / masterwork | an apt poem, a fully reasoned technique | Miracle-tier: bends reality, alters the sky, drops onlookers to their knees. |

## Modifiers (judge by feel — no scoring math)
**Boosts ↑**
- **Aptness** — the input matches the intent (a water image → water, a fire image → fire). The single
  most important factor.
- **Elegance / correctness** — apt allusion, clean structure, well-handled form in the chosen craft.
- **Sincere & original** — something born from the real moment beats a rote-memorized famous example.
  The power feels honesty.
- **Mood match** — bold input for an all-out attack; gentle input for a delicate working.

**Penalties ↓ / Backfire (comedy)**
- **Off-topic** — a funeral elegy to light a campfire → the fire won't catch and a melancholy mood
  drifts in instead.
- **Gibberish / forced** — fake terms, broken structure → the effect goes sideways.
- **Disrespect** — treating the source of the power as a disposable tool → reduced effect.
- Backfires are **comedy, not punishment** (see `fail-forward`): the fireball becomes a tiny fire
  butterfly doing loops around the player's head.

## GM performance rules
1. **Describe the effect's reaction**, not damage numbers — give the power a face and a personality
   (it coos, shows off, gets moved by a beautiful input).
2. After a casting, have present NPCs **react in character** ("Did they just— that's not possible…")
   — and in a language game, in the target language for listening practice.
3. Repeating the same input has **diminishing returns** — encourage the player to vary and improve.
   Track favored inputs in the game's own state block (the game names it, e.g. `casting.signature`);
   bulky history fields can go in the state's top-level `_cold` list (see `engine/scripts/load.py`
   docstring) so the hot view stays small.
4. When the player earns an absurd, epic result, **give the epic payoff** — this is the reward for
   their skill. Don't undersell it.
5. If the player's skill in the craft is limited, **never mock it** — encourage growth. "Use it
   better, get stronger" is the whole motivation loop.

## Relationship tie-in (only if a relationship module is active)
A high-tier casting is one of the strongest **affinity triggers**: a character who just watched the
player bend reality gets a full outer-vs-inner beat — mouth: "Show-off." heart: *...okay, that was
unfairly impressive.* Use casting high points to move the relationship.
