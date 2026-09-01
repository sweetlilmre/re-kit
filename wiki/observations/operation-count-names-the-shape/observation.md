---
type: Observation
title: The byte walk reports the same number either way
description: A rebuild that computes the same value more times than the original does is invisible to a coverage walk and exact to a count of floating-point sites -- because a trap count measures the source's SHAPE, and no address has to line up for it to be read.
tags: [turbo-pascal, codegen, x87, measurement, blind-spot, pascal]
measured_on: the demo reconstruction and the toolkit itself, parts 003, 006
timestamp: 2026-08-25T00:00:00Z
---

# The byte walk reports the same number either way

A reconstruction's coverage walk is the instrument of record: it reads every byte of every original segment against the rebuild and says what cannot be aligned. So when a defect is fixed, the walk is where the gain is expected to show.

**It does not always show there, and on one class it cannot.** An expression written to compute the same value twice where the original computed it once, or written inline where the original called a helper, adds instructions in the middle of a stretch the walk has already given up on. Nothing resynchronises, nothing new fails to align, and the reported total does not move by a single byte.

Measured, on two parts of one demo in one session:

| the defect | the walk | the trap count |
|---|---|---|
| `if Abs(Dy) >= Abs(Dx)` where the original tested two variables it had already stored | **9229 of 10160 either way** | 98 -> 96, exact |
| `Angle * Pi / 180` inline at two call sites where the original had a nested helper | 86.6% -> 87.1% | 95 -> 92, exact |

The first row is the important one. Two builds differing by six bytes of real code, bracketed with nothing else moved, and the walk produced **byte for byte the same number**. Had the trap count not been looked at, the defect had nowhere to appear at all.

## Why it works

Under `{$E+}` every 80x87 instruction ships as a two-byte `INT $34..$3E` in place of its `WAIT ESC` prefix (see [the two switches](../n-and-e-are-different/observation.md)). So the sequence of trap numbers in a binary is one entry per floating-point operation, in the order the code performs them, and each entry names which escape opcode it replaced.

That makes it a **fingerprint of the source's shape rather than of its layout**. Two builds of the same source produce the same sequence at different addresses; two builds of *differently shaped* source produce different sequences at any addresses at all. The count is therefore readable without either segment map, and a `difflib` pass over the two sequences reports each run one side has too many of -- with the original's address, which the original's own layout is entitled to describe.

**And a count is a stricter measurement than an alignment percentage, on this class.** A byte walk over a linked image has to tolerate short differences: a single displaced global changes two bytes of every instruction that reads it, and a walk that stopped at the first of them would report nothing else ever again. That tolerance is what makes the walk useful on a linked image, and it is the same tolerance that makes it blind here. A count of operations has no tolerance to spend -- one operation, one entry.

The two defects above are the same defect wearing two costumes: **the rebuild performed an operation the original had arranged not to perform twice.** A stored intermediate and a called helper are both the author declining to recompute, and both are invisible to a reader who only checks that the arithmetic is right.

## Blind spot

**It assumes the two builds lay their units down in the same order.** Where they do not, a moved unit reads as a long run missing followed by a long run extra, and neither names a defect -- every operation is present, elsewhere. Measured on a part whose order is known to be wrong: `MISSING 32`, `EXTRA 15`, `MISSING 3`, `EXTRA 8`, netting correctly to -12 and localising nothing. **The tell is a run far larger than the net difference.** Fix the order first.

**A matching count is not a matching shape.** Swapping two operations, or replacing one expression with another of equal operation count, leaves the count identical. The count is necessary and not sufficient, and a stream that agrees says only that this instrument has nothing further to offer.

**It sees only floating point.** The same defect class in integer code -- a subexpression recomputed, a helper inlined -- has no equivalent fingerprint, and on a part with one trap in it there is nothing to count. The two cases above were both found in units full of trigonometry, which is where this instrument can see at all.

**A count difference names a unit, not a line.** It says which segment and roughly where; the pairing that identifies the actual statement is still done by hand against a disassembly, and that step is where a wrong answer gets in.

## Cost

One regular-expression pass over each image and a `difflib` call -- cheaper than the walk it complements, and it needs neither build's segment map. There is no reason not to run it on every part every time.

The real cost is remembering to. An instrument that agrees with the record is easy to stop consulting, and this one earns its place precisely on the runs where the record looks fine.

## Example

`PSYCHO NEUROSIS` (Asphyxia, 1994), parts 006 and 003, 25 August 2026.

Both parts had carried a trap-count mismatch for days -- two too many and three too many -- with the mismatch recorded as an open item and read as *a unit has the wrong `$N`*. It was not a switch on either part; every unit's switch was already right, and the surplus was two ordinary expressions.

In part 006, scene 1's Bresenham path builder stores `Abs(Dx)` and `Abs(Dy)` into `Major` and `Minor` and then, in the original, tests those two variables. The reconstruction tested `Abs(Dy) >= Abs(Dx)`, recomputing both -- two extra `ESC D9` sites and six extra bytes. The branch sense settles which way round the source names them: the original pushes `Major`, then `Minor`, and skips the block on `JB`, which is `if Major <= Minor`. Writing it that way took the part from 98 traps to the original's 96. **The coverage walk reported 9229 of 10160 aligned before the edit and 9229 of 10160 after it** -- the bracket build was run specifically to be sure of that, because a number that does not move is normally the sign an edit did not land. [1]

In part 003, scene 1 converts degrees to radians before each of two trig calls. The original does it in a **nested** function -- each call site pushes the six-byte `Real` and then `BP`, and the routine opens `ENTER 6,0` and closes `RET 8`, the static link being what makes it nested (see [the static link](../nested-static-link/observation.md)). The reconstruction had the conversion inline in both statements, so the multiply and the divide were emitted twice rather than once: three sites more than the original ships. Extracting the function matched the count exactly and moved the walk 86.6% to 87.1%. **The source comment had named the address of the original's helper all along** -- `1015:0708 converts degrees to radians` -- so the reading had been done and only the transcription had not. [2]

That last point is the one worth keeping. Neither defect was a discovery about the binary; both were already written down. What was missing was an instrument that noticed the source did not say what the comment beside it said.

## Citations
[1] `src/P6WHOOSH.PAS` in the psycho repository, `BuildPath`, and the bracket build recorded against `1095:02ac`. The two-build measurement -- old expression and new, nothing else in the tree moved -- is what establishes the walk's number as unchanged rather than merely unchecked.

[2] `src/P3TUNNEL.PAS`, `UpdateMotion`, against `1015:0708` and `1015:075a` in `NEUROSIS_003_fpu.exe`. The original's two call sites are at `1015:077b` and `1015:07b6`.

[3] `kit/tools/pascal/fpusites.py --diff`, which is where this measurement now lives, and whose docstring carries the blind spot above.
