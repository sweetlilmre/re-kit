---
type: Artefact Answer
title: A routine inside a linked image
description: How to set the gate and find the routine when what you are measuring is one routine somewhere inside a whole executable.
order: 1
holding: a routine inside a linked image
identify: you have an address in the original and a routine in your build that should sit at it
artefact: routine in a linked image
tier: substrate
ladder_node: R7
tags: [comparison, verification, alignment, hand-assembler]
timestamp: 2026-08-23T00:00:00Z
---

# A routine inside a linked image

Part of [A compare tool's number is plausible, and it is wrong](./observation.md).

## What to do

**Leave the density gate on.** Here it is doing the job it was written for: a scatter of forgiven bytes this dense means the walk is no longer inside the routine.

**Locate by scoring, not by first hit.** Take a run of bytes near the start long enough to be unique in the image -- ten is enough in a 30KB one -- find every place that run occurs, and score each implied alignment by how far the comparison actually gets from it. Keep the best, never the first.

**Where the routine has a terminator, believe only an alignment that reached one.** An alignment that dribbles out in the middle scores zero. Do not report its length.

## Why it works

A routine inside a linked image has no boundary you can read off the file. The only handle is its own bytes, and a single run of them is not a strong enough handle: a ten-byte run from the middle of one routine can occur inside an unrelated one, and the alignment it implies then reports a length that is a fact about somewhere else entirely. Scoring by how far the walk gets makes the routine's own extent the evidence for where it starts.

The gate works here because the legitimate differences are sparse by nature. What a correct transcription of a hand-written routine differs by is addresses -- one byte for a frame-relative local, two for an absolute -- so a handful of one- and two-byte holes is normal and a dense field of them is not. Eight in sixteen is where the threshold sits, and it is deliberately loose: a routine that is mostly memory moves is half displacement bytes by nature. [1]

## Blind spot

**The threshold is a guess, and it has been wrong in the tightening direction.** A tighter gate cut a real 64-byte match off at 37 -- so the number in the source is not a principled value, it is the loosest setting that still caught the case it was written for. [1]

**Best fit is one answer where there may be two.** The same routine compiled into two units appears twice in the image, both occurrences legitimate. This reports one of them and gives no sign that the other exists -- see [The same routine sits mid-unit in one binary and at a segment head in another](../one-routine-two-units/observation.md).

**It cannot see a routine nobody declared.** This measures a routine you named; the complementary measurement is [Every declared routine matches, and the rebuild still behaves differently](../verifier-blind-to-absence/observation.md).

## Cost

Two images and the list of code segments. No disassembler until you read a span that will not align.

## Example

77 routines across parts 001 to 007 of `PSYCHO NEUROSIS`, measured on 23 Aug 2026: all 77 rows identical to the frozen tool this replaced -- routine, source, part, address, matched bytes, holes and which built image -- and the same verdict of 74 locked, 3 not locked, 0 failing. [2]

## Withdrawn

**Anchoring on the first unique run rather than the best-scoring one.** It reports a length measured somewhere else in the image, and the failure presents as a transcription defect in a routine that is in fact correct -- so the time goes into re-reading good bytes. [1]

# Citations

[1] `kit/tools/substrate/align.py` -- `locate()`, `walk()`, and the `DENSITY_WINDOW` / `DENSITY_LIMIT` constants, whose comments carry the 37-against-64 measurement.

[2] `kit/tools/pascal/routines.py`, and the resolution of [One compare tool, and every caller passes its rule](https://github.com/sweetlilmre/PsychoNeurosis/issues/33) for the differential run against `tools/asmverify.py`.
