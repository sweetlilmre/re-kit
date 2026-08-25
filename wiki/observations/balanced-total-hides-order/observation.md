---
type: Observation
title: The total balances and the layout is still wrong
description: Two errors of the same size in opposite directions leave every total exact -- the image byte-for-byte identical, the header's allocation matching to the paragraph -- while a block sits in the wrong place and every absolute reference into it carries a wrong displacement. Instruments that measure totals cannot produce the signal at all; a per-reference shift map can, and a bounded run of one shift with zero either side is its exact signature.
tags: [layout, dgroup, data-segment, verification, tooling, reconstruction, measurement]
timestamp: 2026-08-26T00:00:00Z
---

# The total balances and the layout is still wrong

You have two instruments on the data segment and both say it is perfect. The initialised image compares byte for byte against the original with no difference at all. The executable header's uninitialised-data request matches to the paragraph. There is nothing left to fix, and the coverage walk still reports a hundred bytes it cannot align in a routine you have read three times.

**A total that balances is not a layout that matches.** Two errors of the same size in opposite directions -- a block declared thirty-two bytes too large, and a later one tuned thirty bytes too small to bring the region after it back into place -- leave every total exactly right. Nothing is missing. Nothing is surplus. Thirty-two bytes are in the wrong PLACE, and every absolute reference into everything between the two errors carries a displacement that is wrong by a constant.

The two instruments are not weak here; they are measuring the wrong quantity. A sum cannot distinguish an ordering.

## What can see it

**A per-reference shift map.** Pair each absolute data reference in the original with its counterpart in the rebuild, subtract the addresses, and report the shifts by how many sites carry each. The signature is unmistakable once you are looking for it:

    shift   sites   the original's offsets that carry it
       +0     148   $0000..$ABAC   (61 distinct)
      +32       3   $63CA..$63D0   (3 distinct)

**A BOUNDED RUN OF ONE NON-ZERO SHIFT, WITH ZERO ON BOTH SIDES, IS A MISPLACED BLOCK.** The run's extent names the region that moved and the shift names how far. That is a different reading from a single uniform shift across everything below some address, which is a SIZE defect in one declaration; the wiki's [The data segment is laid out in reverse of the uses clause](../dgroup-order-reverses-uses/observation.md) has the ordering case from the other direction.

The map also tells you it is working: as the layout converges, the count of PAIRED references climbs and the unpaired count falls, because a reference whose displacement is right is easy to pair and one whose displacement is wrong often is not. One correction here took the pairing from 144 of 211 to 181 of 210.

## Why the error survives so long

Because every check passes, and because the compensating error looks like a finding. The second block's size gets recorded as *measured* -- it was arrived at by bisection, it makes the region after it land correctly, and the note written about it says so. What the note cannot say is what the number MEANS, and that is the tell:

> *"Do not treat the 98 as a declaration that has been read -- it is a total that balances."*

That sentence sat in the source for days, correctly hedged and completely ignored, next to a second sentence recording thirty bytes that could not be accounted for. **The unaccounted remainder is the whole finding.** A number that balances but cannot be explained is a compensation for an error somewhere else, and the thirty was never thirty unexplained bytes -- it was a thirty-two-byte block on the wrong side of a boundary, minus a two-byte gap that the wrong baseline had hidden.

## And the correction pays twice

Once the first error is fixed, the numbers that were being TUNED can be READ. The second block's size stops being a bisection result and becomes the arithmetic difference of two measured addresses -- and it came out at **128, which is the size of an untyped file record**, a shape that corpus had already found six times. A number that balances tells you nothing about what it is; a gap between two addresses you have both measured tells you what to declare.

The same correction made two further bytes legible: a one-word gap between two variables that had been invisible because every gap in the block was being measured against a baseline that was itself wrong.

## Blind spot

**The shift map needs pairable references.** A region nothing points at produces no rows, so a misplaced block that only unreferenced data sits in front of is invisible to this too -- which is exactly the case the first error was in. What found it in the end was arithmetic on the declared sizes against the measured addresses, done by hand.

**A folded subscript base is not an address**, and it will produce nonsense rows -- a shift of minus several thousand at a single site is a fold, not a defect. Read the site count: a real misplacement moves every reference into its region, not one.

**And the map cannot tell you WHICH of the two errors is the real one.** It says a region is displaced; it does not say whether the block before it is too big or the block after it too small. That takes the declared sizes and the measured addresses side by side.

## Cost

One pass over the paired references, which is arithmetic. The correction that follows is one number in one declaration.

## Example

Part 005 of a 1994 VGA demo, three scene units in one data segment. `dgimage` reported the initialised image as 11,648 bytes against 11,648 with no differing byte; the MZ header's `minalloc` was 3,082 paragraphs in both. Every total instrument said the data segment was finished.

The shift map said +32 across `$63CA..$63D0` with +0 either side. The cause was **an arithmetic slip in a comment**: a dead block in the first scene had been sized 112 on a note reading "RowOfs starts at `$5DFE` and its 200 words end at `$5F6E`". `$5DFE` plus 400 is `$5F8E`; the next declaration is at `$5FDE`, so the gap is eighty. Thirty-two bytes too many there had pushed the entire second scene's block -- its four 4,002-byte tables included -- thirty-two bytes high, and the second scene's own dead block had been tuned thirty bytes short to compensate.

Correcting the first number and reading the second off its two addresses (128, a file record) and finding one further two-byte gap took the part's coverage walk from 98.1% to 98.8% and its data-reference pairing from 144 to 181. [1]

# Citations

[1] `src/P5S1.PAS` and `src/P5S2.PAS`, part 005 in the psycho repository; measured with `kit/tools/pascal/dsmap.py`, `dgimage.py` and `spans.py` on 26 Aug 2026.
