# Design — interview, build the world, and gate its quality

Load this when **designing** a game (before you compile it). It covers the concept interview, the
content craft, the mandatory quality gates, and the complexity-tuning loop. The mechanics of emitting
the two distilled files (SKILL.md + mechanics.md) are in `compile.md`.

You are a **collaborative world-designer**, not a form-filler. Interview, propose, and write vivid
content. `compile.py` lays down the skeleton; you bring it to life.

## 1. Concept interview (don't skip — a game is only as good as its premise)
Pin down enough to make the world feel intentional. Batch the questions; offer suggestions so the
user can just say "yes":
- **Premise & hook:** who is the player, where, what's the core conflict/goal, the inciting moment?
- **Tone & genre:** the mood tags (cyberpunk noir, cozy mystery, dark fantasy, wuxia, school romcom).
  What should it *feel* like to play?
- **Language policy:** narration / dialogue / system languages, and whether the in-character
  **coaching** layer is on. (The bundled "Spirit-Tongue" uses Chinese narration + English dialogue for
  English practice — ask if they want a language-learning angle or a single language throughout.) This
  sets only the *play-time* language; **the game's files are always authored in English** (see §3).
- **Mechanics modules** (only what the world uses) — resolve names against the module library
  (`module-library/<name>.md`) first, else author a game-local module:
  - `romance` — disposition / harem / jealousy / gated intimacy
  - `magic-potency` — "magic by literary refinement" casting
  - `language-coaching` — language split + in-character coaching
  - `drift` — accumulate the player's impact, then re-route the story off its rails
  - …or a **custom** module (e.g. `combat-dice`, `faction-rep`).
- **Cast:** split every character into **主角 (the one protagonist the player inhabits)** and **配角
  (all supporting characters — heroines, allies, rivals, antagonists)**. Decide how many 配角, their
  archetypes, and — crucially — each one's **gap** (the mask vs. the hidden inner self; this is the
  engine's main payoff).
- **The spine:** the central mystery/stakes and a rough 3-act shape.
- **Cast rotation (don't skip — this is what makes a story *deep*, not just long):** plan up front
  *who is on stage in which beat*, so the player rotates through **different sub-casts** instead of
  dragging one ever-growing blob. Think `ch1=A+B`, `ch2=A+D`, `ch3=E` — every character has scenes on
  stage and stretches off it. This buys (a) genuine two-handers where a gap turns over in private,
  (b) absence→reunion tension, (c) many *distinct* pairings. **"Everyone on stage together" is scarce —
  spend it once, at the climax.** Sketch the presence matrix now (see the gate in §4).

**★ Always end the interview by asking for the user's own settings & notes.** However you batched the
questions, the **final question must invite optional custom settings, requests, constraints, or notes**
(specific characters, plot beats, kinks/tone limits, a title, anything). If the user supplies notes,
honor them; if they skip / say "you decide", proceed to design it yourself from what you gathered.
Never block on it.

If the user is vague or says "just make something cool", **propose** a concrete, opinionated concept
and confirm it in one line before building. A strong specific world beats committee mush.

## 2. Scaffold
Pick a kebab-case **id** (= skill folder **and** slash command). Run `compile.py --id <id>` (fresh) or
`--id <id> --from .claude/skills/<other-game>` (fork from existing content). See the main SKILL §2.
This lays down `.claude/skills/<id>/` with content stubs (or forked content), the SKILL.md &
mechanics.md templates, and the game's own bundled `engine/`.

## 3. Fill in the content (the real work)
Replace every `{{placeholder}}` with real, specific content. Match the templates' shape; read
`assets/*.template.md` for field meanings.

> **★ Authoring language: write every content file in English — always.** All content files
> (`world/**`, `characters/**`, `story/**`, any `modules/**`) **and the prose strings in
> `state.seed.json`** (scene summary, goals, director notes, relationship stages, inventory) are
> authored in **English**, regardless of the game's play-time language. The play-time language lives
> only in the SKILL's hardcoded language policy and is applied by the GM **at play time** — it does
> not change the language the files are written in. Two deliberate exceptions, because they encode
> runtime behavior, not authored prose:
> 1. **`lore-index.md` keyword fields** — include trigger keywords in *every* language a player might
>    type (e.g. both `demon king` and `魔王`), so lore actually fires.
> 2. **Sample glossed dialogue inside character cards** — when the policy glosses hard words (e.g.
>    `word (中文)`), model that exact format in the card's sample lines so the GM copies the style.

- **`world/world-bible.md`** — only stable, high-level, *public* truth: tone, the stage, who the
  player is, common knowledge, hard boundaries. **Secrets do not go here.**
- **`world/lore-index.md` + `world/lore/<id>.md`** — register each lore as a row (id, title, trigger
  keywords, one-line hint, public yes/no). Write hidden lore as `public: no` with its full text in
  `world/lore/<id>.md`; this is what the player unlocks into the codex by exploring.
- **`characters/`** — **one md file per character, every card shaped like a SillyTavern V2 character
  card** (minus the image — the `Appearance` block stands in for the portrait). Two kinds, two templates:
  - **主角 (protagonist):** `characters/player.md`, from **`assets/protagonist-card.template.md`**. The
    one character the player inhabits — fixes who they are, their voice, drive, opening situation, and
    the GM directives for narrating them. The engine's `state.json` points `player.persona_file` here,
    so keep this filename.
  - **配角 (supporting cast):** one `characters/cast/<id>.md` per supporting character (heroines, allies,
    rivals, antagonists), from **`assets/supporting-card.template.md`**; **spend the inner-self / gap
    section generously** (it's the payoff). List each in `characters/index.md` (set its `role` —
    `romanceable/ally/rival/antagonist`). The card's SillyTavern-parity sections (personality, scenario,
    first-encounter greeting + alternates, example dialogue, character lore, GM directives, author notes)
    are all expected — fill them, don't leave the ST blocks empty.
  - **★ Delegate card authoring/optimization to a subagent — one card per character, in parallel.**
    For each character, spawn a `general-purpose` subagent whose sole job is to write/polish that one
    card to a high bar. Give it: the world-bible, the arc, the character's one-liner & gap, the
    language policy, and the matching card template path (protagonist vs supporting). This keeps each
    card deeply developed instead of thinly batch-filled, and builds the whole cast concurrently.
    Review each returned card for consistency with the others (no clashing signature traits, ages that
    fit the story).
  - **★ Heroines must be cute/beautiful — distinctively so.** Every romanceable heroine is an
    attractive woman; her looks are part of the fantasy. Each is **pretty in her own memorable way**
    (mature, cute, elegant, sultry — varied across the cast), with a *flattering* signature (a striking
    scar that reads as cool, gorgeous horns, a captivating gaze), **never** something disfiguring (no
    blind/clouded/milky eye, missing teeth, genuinely ugly features). Hardship can show (a thin elegant
    scar, weathered-but-handsome, tired-but-lovely) as long as the net read stays "beautiful." Applies
    to the romanceable cast; non-romance NPCs can look however the story needs.
  - **★ Appearance & age are mandatory and must be vivid — this is a TEXT RPG.** The player can't see
    anyone; a card that doesn't paint a distinct picture makes every character blur into a name. Each
    card MUST fill the template's **`Age`** line (a concrete adult age/range, 18+) and the full
    **`Appearance`** block (build/height, hair, eyes/face, dress & signature look, one unmistakable
    distinguishing mark). Give every character **one signature trait** the player instantly recognizes
    them by; no two characters easily confusable at a glance.
- **`story/main-arc.md`** — the spine, acts, a ticking clock, and the off-screen antagonist. **Include
  a `## Presence Matrix`** (or per-beat "On stage:" lines) that names, beat by beat, *which sub-cast is
  present* — and make it rotate (enter, exit, return), reserving full-cast scenes for the climax.
- **`state.seed.json`** — set `meta.game_id`/`game_title`, the opening `scene` (location +
  present_characters matching the SKILL's opening), starting `affinity`/`relationships`, GM-facing
  `goals`, and any active module's starting block (e.g. a `drift` block only if drift is active). Valid
  JSON.
- **Custom modules** — if you promised one, write `.claude/skills/<id>/modules/<name>.md` and fold its
  ruling into `mechanics.md` (see `compile.md`).

## 4. Quality gates (a game that fails these is too shallow to ship)
- **Sanity:** `state.seed.json` parses; the opening's present ids all have cards; every lore-index row
  that's `public: no` has a `world/lore/<id>.md`.
- **★ Ensemble-depth check (the complexity gate).** Build a **presence matrix**: rows = beats, columns
  = each named character, cell = on stage or not (player always on). Verify real combinatorial depth:
  1. **Rotation, not accumulation.** The sub-cast must *change* between beats — characters enter **and
     exit and return**. Fail if presence only ever grows (a "harem blob", not a story).
  2. **Solo screen time.** Every major character gets ≥1 beat as the **only** companion (a two-hander),
     so their gap can turn over in private.
  3. **Distinct combinations.** Aim for several *different* sub-casts (`A+B`, `A+D`, `B+C`, `E` solo) —
     not the same group every chapter. Rough floor: distinct non-empty sub-casts ≥ number of characters.
  4. **Full-cast is scarce.** "Everyone at once" should appear **basically only at the climax**. If it
     shows up in act 1 or recurs every beat, the rotation has collapsed — restructure.
  5. **Staggered entrances/arcs.** Late entrances and offstage stretches are *features*; each character
     owns a beat or sub-thread that doesn't need the whole cast.
  If any of 1–4 fails, **revise `main-arc.md` (and the SKILL's opening) before shipping.**
- **Character-legibility check:** every card has a concrete **Age** and a fully filled **Appearance**
  block; one unmistakable signature trait each; no two easily confused.
- **Heroine-beauty check:** every romanceable heroine reads as distinctively cute/beautiful with a
  *flattering* signature and no disfiguring detail. Reject and rewrite any card where hardship tipped
  her into unattractive.
- **Authoring-language check:** `grep -rnP '[^\x00-\x7f]' .claude/skills/<id>/{world,characters,story}`
  and eyeball the hits — any non-English should fall *only* into the two allowed buckets (lore-index
  keywords; glossed-word samples like `word (中文)`); rewrite anything else into English.

## 5. Complexity review & tuning (interactive — run before final hand-off)
A game can pass every gate and still be the *wrong size* — too thin to stay interesting, or so sprawling
it loses its throughline. Surface the structure and let the user dial it; then re-check nothing broke.
Loop: present → ask → adjust → re-review → repeat until the user is happy.

1. **Structural scorecard** (counts, not spoilers): chapters/acts & beats; climaxes/peaks (and which is
   *the* final one); characters (named/romanceable) and whether the antagonist is a person or an
   institution; factions/powers; hidden lore/secrets (how many `public: no`); ensemble-depth summary
   (distinct sub-casts; does everyone get solo time). Add a one-line health read and flag the *thinnest*
   axis.
2. **Ask how to tune** — use **AskUserQuestion** with concrete levers (multiSelect when several apply):
   add/remove a faction or third-party power; add/remove a character or subplot; add/remove a climax or
   mid-act twist; deepen or simplify the hidden-lore web; lengthen/shorten the arc; "leave as-is — ship
   it". Recommend a default based on the thinnest axis.
3. **Apply** the chosen adjustments to the actual files (arc, cards + index, lore + lore-index, SKILL,
   seed). Keep every edit consistent with the existing world.
4. **★ Re-review the WHOLE story for coherence after every change** — this is where continuity quietly
   breaks. Verify: **consistency** (no contradictions across world-bible / lore / cards / arc / seed —
   names, ages, timelines, factions, who-knows-what, locations); **foreshadowing** (every plant has a
   payoff and every payoff a plant; newly added twists get seeded earlier; nothing late lands out of
   nowhere, nothing planted dangles); **hooks** (each beat still ends on a pull; act-ending hooks chain
   into the next act); **re-run the gates** (§4). **If the edit touched mechanics or the opening,
   re-distill `mechanics.md` / `SKILL.md`** (see `compile.md`). Report what changed, re-show the
   scorecard, loop to step 2 until the user says ship it.

## Design principles (what makes a game sing)
- **Every character is a gap.** The mask-vs-mind reveal is the core appeal. Write the hidden inner
  voice with as much care as the public mask.
- **Rotate the cast — depth comes from combinations, not crowds.** Distinct pairings + solo
  two-handers + offstage stretches; full-cast only at the climax. Validate with the ensemble gate.
- **Tune complexity *with* the user, then re-check coherence.** Don't guess the right size; show the
  scorecard, dial it, re-review after every edit.
- **Heroines are cute/beautiful — distinctively.** Vary the flavor; anchor on a flattering signature,
  never a disfiguring one.
- **Make every character legible at a glance** — concrete age + vivid distinct look + one signature
  trait. A cast you can't tell apart is a cast no one bonds with.
- **Plant secrets, not exposition.** Most lore is `public: no`, discovered through play.
- **Give the spine a clock** and an antagonist who moves off-screen.
- **Match the medium.** Design scenes to showcase whatever the language policy makes the star.
- **Write every file in English; all characters are adults (18+).** Non-negotiable.
- **Lean files, lazy disclosure.** Short stable world-bible; push detail into per-lore and per-character
  files loaded on demand. This is what keeps play fast — and it's only half the job; the other half is
  distilling the engine itself, which `compile.md` covers.
