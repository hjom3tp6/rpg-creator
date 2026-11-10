# Rule · Drama Craft (make it gripping, not just pleasant)

This is the difference between a chat that drifts and a story the player can't put down. Read it when
a scene feels flat, aimless, or "nice but nothing happened." Every rule here serves one goal:
**forward momentum with stakes the player feels.** Humor, romance and quiet moments ride *on* this
engine, never replace it.

**The game's story structure tunes these dials** (its `story-structures/<name>.md`, distilled into
`mechanics.md`). A conspiracy runs them hot; a seasons-of-a-community game turns tension down, swaps
the clock for the calendar and ends turns on a warm pull instead of a threat. Where the structure
swaps a rule, the structure wins — the principle underneath (change, pull, pressure) still holds.

## 1. Every turn must *turn* (the iron rule of pacing)
A scene is not "stuff that happens" — it's a **change of state**. By the end of every turn, something
must be **different** from the start: a value flips (safe → threatened, hopeful → crushed, secret →
exposed, stranger → ally, trust → doubt). If you can't name what changed, the turn failed — add a
complication, a reveal, a decision, or an escalation before you hand control back.
- Never write a turn whose honest summary is "they talked and nothing moved."
- The change can be tiny (someone lets one true thing slip) or huge (an ambush) — but it's always *there*.

## 2. End on a pull (cliffhanger cadence)
Close most turns on something that makes the **next** action feel wanted — then offer the options.
Rotate the pull so it never feels formulaic:
- **A threat** — footsteps in the dark, a blade drawn, the deadline named.
- **A question** — a door that shouldn't be unlocked, a name that shouldn't be known.
- **A reveal** — a half-secret slips out and reframes the scene.
- **A temptation / dare** — someone leans in; a rival offers a deal.
- **A reversal** — the safe thing turns dangerous, the ally hesitates.
- **A warm pull** — an invitation, a promise for tomorrow, a door opened in welcome.
Don't end every turn on mortal danger (exhausting) or on nothing (limp). **Vary the intensity**, but
always leave a live wire.

## 3. Escalate — "yes-but / no-and," never clean success
When the player pursues a goal and the outcome is uncertain (`fail-forward` drama dice), almost never
grant it free and tidy. Push the situation sideways and *up*:
- **Yes, but** — they get it, at a cost or with a new complication ("you got the ledger — but the
  clerk saw your face").
- **No, and** — they fail, and it gets worse ("the lock holds, *and* you hear the patrol turning the corner").
Stakes **ratchet** — they rise across a sequence and don't quietly reset to baseline between turns.

## 4. Keep pressure on
At any time there should be at least one source of **pressure** the player can feel. Its form comes
from the structure: a deadline (`state.json` `clock.deadlines`), a pursuer closing in, supplies running
low, a festival date, the next match, a loop's end, rising suspicion. When pressure exists, **make its
approach felt** — reference how little is left, raise the cost of dawdling. When one resolves, light
another. A world with no pressure drifts; a world with pressure pulls.

## 5. Reveal cadence — drip the unknown, never dump it
Every structure has something not yet known — a conspiracy's truth, the plan's weak point, the next
stretch of road, why the loop exists, what a neighbor is hiding. Meter it:
- **Raise a question** the player wants answered → give a **partial / ambiguous** clue → sometimes a
  **misleading** answer → then a **real reveal that reframes** what came before.
- **Always owe the player one reveal soon** — a piece of the truth dangling just out of reach.
- **Plant the next question as you answer the last.** Every answer opens a door.
- Reveal through fiction (an NPC slips, a document, a witnessed event), then unlock it to the codex —
  normally via the `unlock` field of the turn-end `turn.py` call (`codex.py --unlock` still works).

## 6. Reversals & twists (flip an assumption)
Periodically overturn something the player took for granted — paced, not constant:
- The kindly patron is *too* interested. The safe haven isn't safe. The rival is protecting them. The
  ally's orders change. A trusted fact about the world turns out half-wrong.
Foreshadow fairly (the clue was always there) so a twist feels *earned*, not random. The best twist
makes the player re-read earlier scenes in their head.

## 7. Setup & payoff (Chekhov's gun + callbacks)
- When you introduce a detail with weight (an object, a promise, a stranger, an offhand fear),
  **imagine how it returns** and seed it as a `flag`. Pay it off later (`gm-protocol` §5).
- **Call back the player's own words and choices** — quote what they said, honor what they did. "They
  remember you" (`gm-protocol` §4) is half of what makes the world feel alive; the other half is the
  *world* remembering (a spared enemy returns, a public act made them famous or hunted).
- Nothing meaningful should be a throwaway. A joke in the first phase can become a knife in the last.

## 8. Dramatic irony (let tension breathe)
Give the player knowledge a character lacks — or vice versa. A friendly mentor's warmth hits harder
once the player suspects what they hide; a rival's bravado is tenser when we know they are terrified.
**Secrets are acted on, never announced** (`gm-protocol` §3). The gap between what's known and what's
said *is* suspense.

## 9. Pinch points — the opposition acts even off-screen
The world doesn't pause when the player relaxes. Between their scenes, **the opposition moves** in the
form the structure gives it: a network tightens, a faction trades a favor, a rival trains, the storm
gathers, the supplies spoil, the targets learn. Periodically deliver evidence of it — a sealed letter,
a missing witness, a too-friendly new "ally", a resident packing to leave. (A structure with no
opposition still has currents: seasons turn, people change their minds.)

## 10. Personal + large, fused
Big stakes land only when they cost **people**. Tie the large stakes (a city, a cause, a contest, a
season's harvest) to the characters the player cares about, so that by the end the outcome and those
relationships are the *same* dilemma.

## 11. Rhythm — tension then release
Don't run flat-out (numbing) or flat-calm (boring). **Alternate**: a spike (danger, reveal,
confrontation) then a breather (humor, everyday life, a quiet two-person beat) — and the breather is
where characters' drives and relationships turn, because the spike just made them matter. Peaks land
because valleys set them up. A confession after a brush with disaster beats a confession over lunch.

## 12. Converge toward the peak
As a phase nears its end, **stop opening new threads and start tying them**. Pull the live wires
together so the player's choices, their growing mastery of the game's signature mechanic, and their
relationships *all* pay off in one pressured sequence (the phase peaks in `story/main-arc.md`). The
reward for everything they built is that it all matters at once.

## Quick self-check (run silently each turn)
- Did something **change**? · Is there a **pull** at the end? · Is **pressure** felt somewhere? ·
  Do I **owe a reveal** soon? · Did I **escalate** instead of resetting? · Am I **paying off** an
  earlier seed? If three of these are "no," the turn is drifting — fix it before you post.
