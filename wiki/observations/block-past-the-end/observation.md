---
type: Observation
title: One block reports a large shift while every block around it is exact
description: Our segment can be shorter than the original's, so a block near the end has nothing to be compared against -- and both obvious things to do about that report a defect where there is none.
tags: [comparison, verification, alignment, segments, tooling]
measured_on: the demo reconstruction and the toolkit itself
timestamp: 2026-08-23T00:00:00Z
---

# One block reports a large shift while every block around it is exact

You are comparing a segment block by block, because a prefix comparison would freeze at the first placeholder and say nothing about the correct routines below it. Eleven of twelve blocks come back exact. The twelfth reports a large negative shift and a pile of real differences, and it is the last one.

**Check the two lengths before reading that as a defect.** Our segment can simply be shorter than the original's, and a block whose range runs off the end of ours has nothing to be compared against. Both of the obvious responses to that are wrong, and each is wrong in a way that produces a confident number:

- **Clip the block and search anyway.** The true shift no longer fits inside what is left, so the search cannot find it and returns the best of the rest -- a shift that is arbitrary and a difference count that is real, about the wrong alignment.
- **Compare past the end.** Then the measurement runs into whatever follows the segment in the image, and agreement or disagreement there is an accident of layout.

The honest answer is to compare nothing and report the shortfall in bytes -- and to put the count of such blocks in the summary line, because a segment where one block was never measured is not the same run as one where every block was.

There is a third thing to check, and it prevents the whole situation rather than diagnosing it: **a position may already be known.** Searching for a block whose start you know -- a segment that sits at offset 0, a unit at the head of its file -- is not merely wasted work. It is an opportunity for the search to find a better-scoring coincidence somewhere else, and then report it with the same confidence. Where the position is a fact, assert it; a search is for when you do not have one.

## Why it works

A block's range is a fact about the *original*. Our build's length is a separate fact, and nothing keeps the two in step while a unit is being transcribed. So "this block extends past the end of our segment" is a third outcome alongside agreement and disagreement, and it needs its own name: not measured. Collapsing it into either of the other two is what makes the tool point at the wrong place.

The failure is also self-disguising in the direction that matters most. A headline like *11 of 12 blocks exact* reads as one small remaining problem in a known place, so the effort goes into the block that is fine.

## Blind spot

**Reporting the shortfall does not explain it.** A short segment is usually a routine still to be transcribed, but it is also what a wrongly-sized local, a missing padding byte or an incorrect declaration order produces, and this measurement cannot tell those apart. It says how many bytes are missing and where, never why.

**Coverage silently drops.** Every unmeasured block is a stretch of the original nobody has compared. If the summary reports only exact-versus-inexact, the run looks cleaner than the one before it precisely because it measured less.

## Cost

Two lengths and a subtraction, before the search runs.

The subtraction needs our segment's length, and **that number is measured -- it comes out of the build's own map -- so it belongs on the command line and not in a config.** A config is for what somebody decided; a measurement put in one is a value that goes quietly stale while continuing to look authoritative. Reported honestly the summary reads *11 of 11 comparable blocks agree*, with the twelfth named as running 12 bytes past the end of ours: the same run as before, with the unmeasurable block moved out of the denominator instead of into the failures.

## Example

`PSYCHO NEUROSIS`, 23 Aug 2026: our program segment was **1,604 bytes against the original's 1,616**, so the last block ran 12 bytes past the end of ours. Clipping and searching anyway reported a shift of **-195 with 149 real differences** for 368 bytes that are **byte-for-byte identical at shift 0** -- and the headline *11 of 12 block(s) exact* named the wrong culprit. The other tool of the pair took the second wrong option: it compared 12 bytes past its own segment, and they happened to agree. [1] [2]

One consequence is worth stating because it looks like a regression and is not. Eleven of that tool's twelve rows reproduce exactly, on shift and on real-difference count; **the twelfth cannot be reproduced at all, because the number it reported was an artefact of the clip.** The choice is between matching a figure nobody can explain and recording why it is gone, and the second is worth more -- the same reasoning as a pending-fixup count that fell because two overlapping rules had been double-counting it. [2]

## Citations
[1] `kit/tools/pascal/blockcmp.py` -- the branch that reports a block as running past the end of our segment, and the `short` count in its summary.

[2] The merge that produced these figures, in which a fourth compare tool turned out to be this instrument carrying a different allowed-difference rule -- see [A compare tool's number is plausible, and it is wrong](../plausible-and-wrong/observation.md). Its measurements: 1,604 against 1,616, shift -195 with 149 real differences, 368 bytes identical at shift 0.
