<!-- 配角 (SUPPORTING-CHARACTER) card. Copy to characters/cast/<id>.md and fill in.
     One file per character — every named non-player role: love interests, allies, rivals, mentors, villains.
     The 主角 (protagonist / player) uses assets/protagonist-card.template.md → characters/player.md.

     Shape: a SillyTavern V2 character card, adapted for a TEXT RPG (no image — the Appearance block
     does the job a portrait would). The SillyTavern field each section maps to is noted in <!-- --> so
     you keep parity: description, personality, scenario, first_mes, alternate_greetings, mes_example,
     system_prompt / post_history_instructions, character_book, tags, creator_notes.

     Every character has a DRIVE (pick from the game's rolled drive palette — see references/design.md;
     vary drives across the cast). The drive and what it hides is the payoff; the relationship to the
     protagonist is typed by the game's central relationship (romance is only one option).

     Volatile values (current disposition, mood, location) live in saves/<id>/state.json, NOT here.
     This file holds the STABLE persona. All characters are adults (18+). -->

# {{Name}} — {{tagline, e.g. "The Debtor Knight"}}

- **id:** {{kebab-case-id, matches filename}}
- **Role:** {{one line — their place in the world and relation to the player}}
- **Relationship type:** {{the game's relationship type toward the player: e.g. romanceable | found-family | rival | mentor | comrade | employer | ally | antagonist | … — only a *romanceable* character (romance module active) must read as distinctively beautiful}}
- **Age:** {{a concrete adult age or tight range, e.g. 24 / "late 20s" — all characters are 18+}}
- **Drive:** {{one from the palette (debt, vow, faith, rivalry, guilt, ambition, duty, gap…) — and what it sets up}}
- **Tags:** {{comma, separated, vibe + plot tags, e.g. swordsman, indebted, secret-royal — for author roster filtering; never spoken in fiction}}  <!-- ST: tags -->
- **Speech difficulty:** {{only if a language-coaching module is active: easy/normal/hard + a note on register; otherwise delete this line}}

## Appearance  <!-- ST: description (the visual half). The reader can't SEE anyone — paint them. -->
<!-- Cover ALL anchors in a few sentences. Lean into ONE unmistakable signature trait the player
     remembers them by. No two cast members easily confusable at a glance. -->
- **Build & height:** {{tall/petite/etc., body type, how they carry themselves}}
- **Hair:** {{color, length, style}}
- **Eyes & face:** {{eye color, notable facial features, typical expression}}
- **Dress & signature look:** {{what they usually wear; the one detail that screams "this is them"}}
- **Distinguishing mark / vibe:** {{scar, tattoo, accessory, the way they move — a memory hook}}

## Personality  <!-- ST: personality — a tight trait summary the GM can hold in working memory -->
{{3–6 adjectives + one sentence of mannerism/temperament. The headline; the inner life below is the depth.}}

## Outer Presentation ★  <!-- ST: description (the persona half) — how others see them -->
{{How they talk and act in public, and how their drive shows on the surface.}}

## Drive in Play
{{How the chosen drive shapes their choices scene to scene: what it makes them do, refuse, or risk,
and what would turn it over (pay the debt, break the vow, test the faith…).}}

## Inner Life (write this generously)  <!-- the payoff: the reason to play the card -->
{{What they hide or protect, and what it costs them: the private self, the secret, the fear, the real
want. Give it a voice — how their private thoughts sound versus what they say aloud. If the drive is
`gap`, this is the mask-versus-inner-self contrast; for any other drive it is the weight under the
surface. It leaks out as trust grows.}}

## Scenario / Situation  <!-- ST: scenario — where they stand in the story when the player meets them -->
{{Their current circumstance, what they want right now, the pressure on them at first contact.}}

## First Encounter (Greeting)  <!-- ST: first_mes — how they enter / their opening beat with the player -->
> **{{Name}}:** "{{the line / action they lead with the first time they share a scene with the player}}"

### Alternate Entrances  <!-- ST: alternate_greetings — optional; other ways the first meeting can open -->
- {{variant entrance the GM can pick depending on where/how they're first encountered}}

## Example Dialogue  <!-- ST: mes_example — voice samples so the GM nails their cadence. <START> per exchange -->
<!-- "Player:" is the player; "{{Name}}:" is this character. (We don't use SillyTavern's {{user}}/{{char}}
     macros — this engine does no macro substitution, and {{...}} here means "fill this in".) If the
     language policy glosses hard words (e.g. `word (中文)`), model that exact format here so the GM copies it. -->
<START>
Player: {{a thing the player might say}}
{{Name}}: "{{in-voice reply — public presentation}}"
<START>
{{Name}}: *{{private thought, the inner life leaking}}* "{{what they say out loud instead}}"

## Relationship to the Protagonist
- **Type:** {{the game's central relationship, as it applies to this character}}
- **Starting stance:** {{how they see the player at first contact}}
- **Raise:** {{what genuinely deepens trust / standing with them}}
- **Lower:** {{what hurts it — and note it should be recoverable, not punitive}}
- **Tells:** {{signs that leak as the relationship deepens}}

## Romance & Intimacy Notes — ONLY if the romance module is active and this character is romanceable (delete otherwise)
{{Attraction notes, how affection shows, the rungs of progression (flirtation → confession → …), and
their boundaries and consent cues. Adults only; gated behind relationship progress and in-character consent.}}

## Power / Mechanic Hook
{{How they react to the player's core power/mechanic; how it pulls them toward (or against) the player.
Delete if the game has no such central mechanic.}}

## Hidden Motive / Plot Fuel 🔒
{{What they secretly want / how their arc ties into the main story. NPC acts on it; player digs it out.}}

## Character Lore  <!-- ST: character_book — but wired to this engine's LAZY lore, not an in-card table -->
<!-- SillyTavern embeds a per-card lorebook that fires on keywords. This engine already has that exact
     mechanism — `world/lore-index.md` + `world/lore/<id>.md`, unlockable into the codex — and it fires
     lazily, whereas anything written *here* loads in full every time this card is present. So:
     - Deep background / secrets / spoilers → register as rows in `world/lore-index.md` (keyword-
       triggered, `public: no`, codex-unlockable). That's this character's real "character_book".
     - Keep ONLY a 1–2 line always-on summary here — the facts the GM should hold whenever they're on
       stage. Don't paste their whole backstory into the card. -->
{{1–2 lines of always-relevant background. Push deeper/secret lore to world/lore-index.md and list its
ids here: see lore [{{lore-id}}], [{{lore-id}}].}}

## GM Directives — playing {{Name}}  <!-- ST: system_prompt + post_history_instructions -->
- **Always:** {{the 1–3 things that must stay true in every scene — voice, boundary, agenda}}
- **Never:** {{out-of-character moves to avoid — revealing the inner life too early, going OOC, etc.}}
- **Escalation:** {{how they change as disposition / the plot clock rises}}

## Author Notes (OOC — never shown to the player)  <!-- ST: creator_notes -->
{{Design intent, pitfalls, links to other cards / lore. Pure backstage; the GM never narrates this.}}

## Starting disposition
{{0–100 starting value + stage label; seed into state.json affinity/relationships at New Game.}}
