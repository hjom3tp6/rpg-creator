# Lorebook Protocol — keyword-triggered loading + codex

How world lore loads on demand and how the player unlocks the codex. This is SillyTavern's
World Info on a filesystem, and the core of context discipline.

## lore-index.md format
`world/lore-index.md` is a **cheap, always-scanned** index: each lore's id, title, trigger
keywords, one-line hint, and whether it's public. Full text lives in `world/lore/<id>.md` and is
**only read when a keyword hits**.

```markdown
| id | title | keywords | hint | public |
|----|-------|----------|------|--------|
| old-harbor | The Old Harbor | old harbor, 舊港, docks, tide gate | The sunken district under the city | yes |
| the-drowned-bell | The Drowned Bell | drowned bell, 沉鐘, the toll, why the tide rises | Why the tide keeps rising; central mystery | no |
```
- `keywords`: include every language a player might type (as above: English and 中文). If the player input, current scene, or NPC dialogue hits one, `Read world/lore/<id>.md`
  for this turn.
- `public = yes`: common knowledge; may be referenced from turn one.
- `public = no`: hidden; reveal through exploration/dialogue/events, then unlock to the codex.

## Trigger check (turn step 2)
1. Gather this turn's trigger text: player input + `scene.location` + present NPC names + the topic
   you're about to write.
2. Scan `lore-index.md`; pick keyword hits.
3. `Read` only the hits **relevant right now** (usually 0–2). No hit → read nothing, save context.
4. Weave the lore into the fiction — don't paste setting text verbatim.

## Codex unlock (the reward for exploring)
When the player **first reveals** a hidden lore (an NPC says it, a document is found, it's witnessed):
1. Normal path: add it to the turn-end call's `unlock` list —
   `turn.py … {"unlock":[{"id":"<lore-id>","title":"<player-facing title>"}], …}`.
   (Manual alternative: `python3 $SKILL/engine/scripts/codex.py --game <id> --unlock <lore-id> "<title>"`.)
2. It writes into `saves/<id>/codex.md` (if new); `turn.py` reports `newly_unlocked: [ids]`, codex.py `true/false`.
3. If newly unlocked, add a small after-narration cue, e.g. `*(📖 Codex updated: The Drowned Bell)*` — written in the game's system language.
4. The player can review the codex anytime by asking OOC via `[god]` (e.g. `[god codex]`).

What's written to codex.md is the **player-known version** (what he understood), not necessarily the
full secret in the lore file.
