---
type: Observation
title: A believable percentage about a position nowhere near the thing
description: When the search runs under a looser rule than the comparison, the search slides to wherever the loose rule scores best -- and a positional rule and a sliced buffer must share one coordinate frame.
tags: [comparison, verification, alignment, relocation, tooling]
measured_on: the tracker reconstruction and the toolkit itself
timestamp: 2026-08-23T00:00:00Z
---

# A believable percentage about a position nowhere near the thing

Your compare tool reports something like `agrees to +1492 of 1750 (88%)`. The percentage is high enough to look like progress and low enough to look honest. Then you check where it measured, and it is near the end of the thing rather than the start of it.

**The search and the comparison were not using the same rule.** If the position is searched for under a rule that lets more through than the rule that then measures, the search does not find where the thing is -- it finds where the loose rule scores best. Those are different places, and the second one is systematically late: a rule that passes a byte position *whatever the byte's value* scores best inside the longest stretch of nothing, which in a code image is near the end.

The fix is to search under the plain rule, then re-measure at that position under the looser one, and keep the looser figure only where it reaches further than the plain one. The search gets the strict rule because finding the thing is the harder question; the measurement gets the loose one because that is what the artefact actually allows.

## A second way the same rule goes wrong: two coordinate frames

The looser rule here is a set of byte positions read out of an object module, and those positions are offsets **into the whole image**. The walk is handed **a slice** starting wherever the thing was located. Unless the set is shifted by that offset, every position in it lands outside the run being judged, and nothing is let through at all.

That is the same rule failing in the opposite direction on the same day: too permissive when it drove the search, then completely inert when it reached the comparison. A positional rule carries an origin whether or not anybody wrote it down, and a sliced buffer has a different one.

## Blind spot

**Invisible wherever the two rules happen to agree, which is most of the time.** A unit with no object module has an empty position set, and then the strict and loose searches return the same answer -- so a whole corpus can pass while the bug is present. It surfaces only on the artefacts the loose rule was added for, which are the minority by definition.

**A high percentage is the wrong thing to be reassured by.** Both failures above produce a number in the plausible band. The check that catches them is not the figure, it is whether the reported position is where the thing should be -- so the position has to be printed, not just the score.

## Cost

Nothing beyond calling the search and the measurement in that order. One extra walk per artefact that has a loose rule at all.

## Example

`PLAYMOD` in the `VangeliSTracker` repository, 23 Aug 2026: located near the end of itself and reported `agrees to +1492 of 1750`. The relocation set that caused it came from the unit's own object module -- and once the search was moved onto the plain rule, the same set applied at the comparison passed nothing at all until it was shifted into the slice's frame. [1] [2]

## Citations
[1] `kit/tools/pascal/units.py`, `measure()` -- the comment beginning *LOCATE ON THE PLAIN RULE, always*, and the shift applied to the relocation set below it.

[2] The resolution of *One compare tool, and every caller passes its rule*, findings 3 and 4 of 5.
