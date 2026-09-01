---
type: Observation
title: Two implementations of one comparison differ by two bytes
description: A run of differing bytes is not homogeneous, so a rule that answers yes-or-no about the whole run is wrong at one end of it; a rule that returns a count is not.
tags: [comparison, verification, fixups, tooling]
measured_on: the tracker reconstruction and the toolkit itself
timestamp: 2026-08-23T00:00:00Z
---

# Two implementations of one comparison differ by two bytes

You have rewritten a compare tool and put the new one beside the old. Every row agrees except one, and that row is off by a byte or two. Neither number is obviously wrong, and two bytes is small enough to be tempting to round away.

**A run of differing bytes is not all one thing.** Take `00 00 3C` on our side against three real values on the original's: that is two unresolved references and then a genuine difference, in one run. A rule asked *whether* it may pass has only two answers available, and both of them are wrong -- one lets the `3C` through, the other throws away two bytes of real agreement. Which of the two you get is an accident of how the loop was written.

A rule asked *how many* has the right answer available: two. It passes the pair, stops at the `3C`, and the reported prefix ends where the real divergence is.

## Why it works

The unit of a difference and the unit of a decision are not the same size. A run is however many bytes happen to differ in a row, and that boundary is set by the two byte streams; the decision is about each byte's own reason for differing. Returning a count is what lets one run hold two reasons -- which is the normal case, not an edge one, because a placeholder and a mistake sit next to each other as often as anything else does.

It also gives the walk somewhere honest to stop. A count short of the run's length means "this much has a reason and the rest does not", so the walk ends there rather than one run later or one run earlier.

## Blind spot

**The count is only as good as the rule's own reason for each byte.** A rule that returns the whole run because it cannot tell one byte from another has learnt nothing from this shape -- it is the yes-or-no rule wearing a count's clothes. Two of the four rules in this toolkit genuinely are all-or-nothing (an address is a whole operand, so its run passes entirely or not at all), and that is correct for them; the shape matters where the reason is per-byte.

**A two-byte discrepancy between two tools is not always this.** It is also what a double-counted overlap looks like at small scale -- see [Two tools measure one thing and one number is lower](../two-tools-one-number/observation.md) -- and the two have different fixes. Measure the difference rather than assuming which it is.

## Cost

Nothing. It is the signature of one function.

## Example

Exactly two bytes of one unit's prefix in the `VangeliSTracker` repository, on 23 Aug 2026 -- and two bytes was the whole difference between agreeing with the tool being replaced and not. Small, and it is the smallest useful size for this finding: any larger and it would have been read as a real defect and chased in the source. [1] [2]

## Citations
[1] `kit/tools/substrate/align.py`, `walk()` -- the contract is stated on the rule signature: the rule is handed the run's length and both byte strings and returns how many bytes it passes; zero ends the walk, and a count short of the run ends it there.

[2] The resolution of *One compare tool, and every caller passes its rule*, finding 2 of 5.
