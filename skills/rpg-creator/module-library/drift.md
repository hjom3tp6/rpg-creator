# Rule · Drift (the world reroutes — no rails)

The story has a *planned* trajectory (`story/main-arc.md` + `state.json` `goals`). **Drift is the
mechanism that lets the world deviate from that plan** because of what the player actually did — so
the game never quietly rails toward a predetermined ending. At certain moments you stop, re-examine
the *whole* story, and ask one question:

> Given everything this player has actually done, is the planned path still what **would** happen?

When the honest answer is "no," the world **bends**: factions reroute, a scripted beat is cancelled
or mutated, an allegiance flips, the central mystery reframes, a new thread is born from his specific
deeds. This is what makes the world feel **alive, uncanny, and genuinely unpredictable** instead of a
branching script. Drift bends the *world*, never the player's agency or the engine's core rules.

This module runs *on top of* the others: it feeds `drama-craft` (reversals, pinch points,
setup/payoff), respects `fail-forward` (a drift is a branch, never a dead end), and obeys god-mode.

---

## 1. Drift pressure — the hidden accumulator

Keep a hidden meter `drift.pressure` (0–100) in `state.json`. It measures how far the *world* has
been pushed off its planned course since the last reroute. **Never show it** unless the player
explicitly asks for it OOC via `[god]`. Each turn, after resolving the action, add pressure
by how much the turn diverged from the expected, on-rails path:

| The player's turn… | +pressure |
|---|---|
| On-rails: follows the obvious hook, low consequence | +0–2 |
| A real choice with consequences (a flag worth bringing back) | +3–6 |
| Touches a faction's / heroine's **core** (loyalty, secret, power, life) | +6–12 |
| Outsized outcome — a `Fortune's Favor` crit, a catastrophic fail, a death, a public miracle | +10–20 |
| Directly defies or dismantles a planned beat ("you weren't supposed to be able to do that") | +12–25 |
| A `[god]` instruction that rewrites a fact or shifts the tone | set by you, often large |

Down-weight repeats (the *second* time he robs the same caravan moves the world less). A quiet
hangout turn can add ~0. **Pressure only goes up between drifts; a drift spends it back down.**

## 2. When a drift check fires

Run a drift check (§3) when **any** of these is true — don't check every turn:

- **Threshold crossing** — `drift.pressure ≥ drift.threshold` (default 60). The world has stored
  enough divergence that it *must* express it.
- **Structural node** — an act/chapter boundary, a major `clock.deadline` resolving, a heroine route
  locking or breaking, a faction toppling, a central reveal landing, a long arc closing. These are
  the natural seams where the future re-forms.
- **Catalyst turn** — a single turn so consequential it can't be absorbed (a key NPC dies, a secret
  goes public, a war starts/ends, the player seizes or destroys something pivotal). Check immediately,
  regardless of pressure.
- **Wildcard** — a rare, low-probability roll (~1 in 12 idle turns) so drift is never perfectly
  predictable even when pressure is low. Keep it small; this is seasoning, not the main engine.
- **God-mode / director** — the player asks the world to change, or nudges tone; treat as a forced
  check at a magnitude you choose.

Record `drift.last_check_day`; don't fire structural and threshold checks for the *same* event twice.

## 3. The re-examination — "reconsider the whole story"

This is the heart of the mechanic. When a check fires, **silently** do this before you write the turn:

1. **Reload the plan.** Re-read the `goals` (short/mid/long), the relevant `story/main-arc.md` beats,
   the `drift.ledger` (past reroutes — see §5), and the recent high-weight `flags`. Hold the *intended*
   future in mind.
2. **Read what actually happened.** From `journal.md` / `session-log.md` / flags, name the 1–3 ways the
   player's real play has pushed *hardest* against that intended future. These are the **fault lines**.
3. **Pick the magnitude** (§4), weighted by stored pressure.
4. **Bend along a fault line.** Choose the change that is, in this order:
   - **Caused** — it flows from the player's actual deeds, not from nowhere. The world is *reacting*.
   - **Least expected but fair** — it should make the player blink, yet a fair re-reader sees the clue
     was always there. Prefer cashing a **planted seed** (`drama-craft` §7) over inventing a new one.
   - **Generative** — it raises stakes, opens a question, and closes none for free. It should make the
     *next* stretch of game different from what it would have been.
5. **Rewrite the future to match.** Update `goals` (this is mandatory — drift that doesn't change the
   goals didn't happen). Cancel or **mutate** now-invalidated planned beats; reroute the relevant
   faction/NPC trajectories; set new `flags`; queue follow-ons in `drift.pending_seeds`. Spend pressure
   back down (subtract the magnitude's cost; a big upheaval can reset to ~0–15).
6. **Record it** in `drift.ledger` (§5) so it *sticks and compounds*.

### Dimensions to bend (pick what the player actually moved)
- **Allegiance** — an ally's orders change; a protector is reassigned to hunt him; an enemy defects.
- **Power** — who holds the key object / territory / secret shifts; a faction rises or breaks.
- **The mystery** — the central question reframes; a "truth" turns half-wrong; a new layer opens
  (then `codex.py --unlock` only what's *revealed in fiction*, not the whole twist).
- **A heroine's line** — her situation, faction, or feeling reroutes (never her core voice; never
  force the romance — see `romance`).
- **The clock** — a deadline accelerates, dissolves, or a new one ignites (`drama-craft` §4).
- **The world itself** — a place, custom, or rule of the setting is permanently altered by his deeds.

## 4. Magnitude bands

| Band | Pressure feel | What bends | Cost spent |
|---|---|---|---|
| **Ripple** | low | One local thread reroutes; a minor NPC's plan changes; a small fact shifts. Mostly invisible. | −15–25 |
| **Shift** | mid | A live storyline changes direction; a faction moves; an allegiance bends; the mystery gains a layer. The player *feels* it soon. | −30–50 |
| **Upheaval** | high / catalyst | The arc's **spine** bends — a planned ending is now off the table, a new center of gravity forms. Rare; reserve for big pressure or catalyst turns. | resets toward 0 |

Vary the band; don't run Upheavals back-to-back (exhausting) or only Ripples (the world feels inert).

## 5. The world-changes ledger — drift must *stick*

A drift that resets next turn is just weather. Persist every Shift/Upheaval (and notable Ripples) in
`drift.ledger` as compact entries the GM re-reads on future checks:

```json
{ "day": 14, "band": "shift", "fault": "spared the inquisitor",
  "change": "Her order now shelters him instead of hunting him; the rival temple takes up the hunt." }
```

Rules for the ledger:
- **Changes compound, never revert.** Each new drift builds on the standing ledger — the world keeps
  diverging, getting further from the original script the longer the game runs. That growing distance
  *is* the point.
- **No free retcons.** Drift **reframes** the future, it doesn't rewrite established hard facts the
  player witnessed. If a fault line seems to need a past fact changed, instead reveal it was *always*
  more complicated (a reframe), and unlock that to codex.
- **Pay off the ledger.** Treat standing entries like Chekhov's guns — a faction you rerouted in Act I
  should *return* changed in Act III (`drama-craft` §7, §12).

## 6. Surfacing — felt, rarely announced

- **Most drift is silent.** You simply reroute the world; the player discovers it through
  consequences — an "ally" arrives with new orders, a door that was open is now watched, a name he
  knew now means something else. Let him *feel* the tilt, then *understand* it.
- **Occasionally make a drift land hard** through fiction — a reveal that reframes the scene, a
  faction's sudden move, a "the ground shifts under everything you assumed" beat. Use `drama-craft`'s
  reversal/pinch-point craft to deliver it; pace it like a twist, earned by a planted clue.
- **Never announce the mechanic.** No "the world has drifted," no meta. The uncanny feeling comes from
  consequence, not narration. Drift is the engine; the story is all the player ever sees.

## 7. Guardrails (drift bends the world, not these)
- **Player agency is sacred.** Drift reroutes the *world's* response to him; it never overrides his
  choices, lines, or feelings, and never punishes a reasonable play with arbitrary doom.
- **Coherence over chaos.** Every drift is a *consequence*, traceable to the ledger and his deeds — an
  earned swerve, not a dice-roll of randomness. If you can't name the fault line that caused it, don't
  drift.
- **Fail forward still holds.** A drift opens branches, never dead ends; even an Upheaval leaves the
  player a live thread to pull (`fail-forward`).
- **It escalates, it doesn't reset.** Stakes ratchet across drifts; the world doesn't sneak back to its
  baseline (`drama-craft` §3).
- **Cartridge spine is the floor, not the rails.** Honor the cartridge's premise, tone, and the
  non-negotiables in `story/main-arc.md` / `game.md` (e.g. the Hollowing keeps creeping, English stays
  in the spotlight). Drift bends *which way* the story goes, not *what kind of story* it is.
- **God-mode `[ ]` outranks drift.** If the player commands the world a certain way, that wins.

## 8. State block (`state.json`)
```json
"drift": {
  "pressure": 0,            // hidden 0–100 accumulator since last reroute
  "threshold": 60,          // pressure level that forces a check
  "last_check_day": 1,      // day a check last fired (avoid double-firing a node)
  "ledger": [],             // standing world-changes (see §5) — compounds, never reverts
  "pending_seeds": []       // queued follow-ons a past drift promised; pay them off later
}
```

## Quick self-check (run silently when a check fires)
- Can I **name the fault line** (his deed) that caused this? · Did I **rewrite the goals**? · Is it
  **least-expected but fair** (a planted seed paying off)? · Did I **log it to the ledger** so it
  sticks? · Did I **spend pressure** down? · Is the player still fully in control, with a live thread
  to pull? If any is "no," it's not drift yet — it's noise. Fix it before you post.
