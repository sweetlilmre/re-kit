---
type: Observation
title: Two alignments reach the same length and the locator keeps the wrong one
description: A locator that scores candidate positions by how far the comparison gets cannot separate an exact alignment from one that only reached the same length because a forgiveness rule excused a run of bytes. Both score equal, the tie falls to whichever the search reached first, and with two near-identical routines that is the earlier one -- so the later routine is measured against the earlier one's body and reported as slightly imperfect when it is byte-identical.
tags: [tooling, verification, measurement, blind-spot, instruments, reconstruction]
measured_on: a 1993 demo reconstruction, two 424-byte palette rotators 92% alike
timestamp: 2026-09-04T00:00:00Z
---

# Two alignments reach the same length and the locator keeps the wrong one

An instrument that measures a named routine has to find it first. The honest way is to search the built image for the original's bytes and score every candidate position by how far the comparison gets, keeping the best — which is right, and is what stops a run from the middle of one routine anchoring an alignment inside an unrelated one.

**It stops being right when two candidates reach the same length.** The comparison is allowed to forgive things — a relocated address, an unresolved fixup, a data-group displacement — so a position can walk the whole routine while excusing a run of bytes. A position that walks the whole routine excusing nothing scores exactly the same. Length alone cannot separate them, and the tie falls to whichever the search reached first: the **lower address**.

## Why that is the wrong one, reliably

Two routines that are nearly identical usually share their opening bytes, because what differs between them is operands rather than shape. The probe the search anchors on is taken from the start, so it matches the earlier routine first. The later routine's marker therefore locates the earlier routine's body.

Measured: two palette rotators of 424 bytes each, one rotating a band forward and one backward, 92% byte-identical and sharing their first ten bytes. The second one's marker located the first one's body, walked all 424 bytes with 32 differences forgiven, and reported the routine as imperfect. That routine was byte-identical to the original at its own address.

**The reported number is plausible, which is the whole problem.** 32 forgiven bytes in 424 reads as a routine that is nearly right — the most believable result an instrument can print, and the least likely to be questioned. Worse, the same shape conceals a real defect: a broken later routine would report the earlier one's health, because the earlier one is what is being measured.

## The fix, and it is small

Score by length **and** by how little was forgiven. The walk already knows how many holes it opened; the locator has only to keep the number and prefer the smaller one when the lengths tie. No new configuration, no change to what counts as a hole, and no effect on any case where one candidate genuinely goes further than another.

## Blind spot

**This orders two candidates; it does not tell you a candidate is the right routine.** Two positions can still tie on both length and holes — identical bytes in two places, which is what a duplicated routine is — and the tie then falls to the lower address again, correctly for byte-identity and arbitrarily for identity of purpose. Where a program genuinely holds one routine twice, only a reference proves which is which, and that is `two-names-one-address`.

It also says nothing about a routine whose body has changed enough that the probe no longer matches at all. That is the NOT FOUND case, and its cause is usually that the segment layout has not converged rather than that the routine is wrong.

## Cost

Three lines, and the hole count is already computed and thrown away.

## Related

* `drifted-second-copy` — a measurement that does not go quiet but manufactures a finding phrased in the vocabulary of the thing measured. This is that failure inside a locator.
* `two-names-one-address` — when the bytes really are in two places, arithmetic on linear addresses separates them.
