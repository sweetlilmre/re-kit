---
type: Observation
title: Every routine is present, aligned, and in the wrong place
description: Definition order is segment order, and a coverage walk that locates each routine by content scores a fully permuted segment at 99.9%. The sequence of routine LENGTHS is the fingerprint that sees it -- the same multiset in a different order -- and matching it against the original's recorded address map names the permutation, after which most routines match to the byte. Two units wrong by the same amount in opposite directions can make the walk read exactly 100.0%.
tags: [layout, code-segment, verification, tooling, reconstruction, measurement, pascal]
measured_on: the demo reconstruction and the toolkit itself, part 003
timestamp: 2026-08-26T00:00:00Z
---

# Every routine is present, aligned, and in the wrong place

A coverage walk that finds each segment's content wherever it sits is the right instrument for almost everything and it is structurally blind to one thing: **order**. Sixteen routines in one 14 KB segment, every one of them present, every one of them byte-for-byte correct internally, arranged in a completely different sequence from the original -- and the walk reported 99.9% for as long as anyone cared to run it. It finds a routine by matching bytes, so a routine in the wrong place is still a routine it finds.

**In Pascal, definition order IS segment order.** The compiler emits routines in the order it reads them, so the arrangement is a property of the source text and nothing about the source text looks wrong. There is no diagnostic, no warning, and no total that changes: the segment's size is the sum of its parts either way.

## The fingerprint is the sequence of lengths

Take the routine boundaries in both images -- the prologues do this, `ENTER imm,0` or `PUSH BP / MOV BP,SP` -- and subtract consecutive offsets. You now have two sequences of lengths. If the arrangement is wrong they are **the same multiset in a different order**, and that is a signature nothing else produces:

    original   191   767   100    63  1360    88    36  ...
    ours        36   100   731   355  1360    88    63  ...

Read it as a permutation, not as a set of size defects. `36` is the seventh in the original and the first in ours; `100` the third and the second; `63` the fourth and the seventh. Two of them, `1360` and `88`, are in the same place in both, which is what makes the pattern legible rather than noise.

**Then pair the lengths against the original's recorded address map** -- the addresses were written down when the segment was first read; nothing had ever checked the build against them. Reordering the definitions to that map took eleven of the sixteen routines to an exactly matching length immediately, which is the confirmation that the pairing was right. The five that remained were then real content differences, each one small and each one findable, because every routine was finally at its recorded address.

Doing this in the other order does not work. Chasing the five content differences first means chasing them at unknown addresses in a segment whose every offset is displaced.

## The residual, once the order is right

With the order fixed, the remaining differences are content, and an instruction-level diff with **the immediates and displacements masked out** isolates them in one pass. Mask the hex literals in the operand text, diff the mnemonic sequences, and every surviving difference is structural:

    - mov di, word ptr [bp - #]
    + mov ax, word ptr [bp - #]
    + inc ax
    + mov di, ax

Masking matters more than it looks. Absolute data references and far-call segments differ throughout a rebuild for reasons that are not code defects at all, and an unmasked byte comparison drowns the three-instruction findings in them.

## Two wrong units can read as perfect

The same blindness has a worse form. In a second part, one unit was sixteen bytes too large and another sixteen too small; the runtime landed on exactly the right paragraph, every far call resolved correctly, and **the walk reported 100.0% of every byte aligned**. Both units were wrong. Fixing one of them made thirty-four unaligned bytes appear -- all of them the low byte of a far-call operand -- and only then could the other be found.

A coverage figure of 100.0% is a statement about bytes located, not about a layout matched. The check that catches this is not a walk: it is **each segment's size against the original's paragraph boundaries, one row per unit**, which is a different quantity and cannot cancel. The wiki's [The total balances and the layout is still wrong](../balanced-total-hides-order/observation.md) is the same failure in the data segment, where it is a per-reference shift map that sees it.

## Blind spot

**A length multiset can be genuinely ambiguous.** Two routines of the same length are indistinguishable by this method, and one segment here had `1360` twice. Fall back to content: a masked instruction diff of the two candidates against the one original will separate them.

**Padding hides small errors.** Segment lengths are reported to a paragraph, so an error of one to fifteen bytes shows as zero. Read the RAW length from the map and, for the last routine, find the true end of the code -- the five bytes of an empty initialisation section followed by zeros -- rather than trusting the padded figure. Getting this wrong once turned a +4 into a +16 and sent the reading off in the wrong direction.

**And a prologue scan finds things that are not routines.** The byte pattern occurs in data and inside longer instructions. Cross-check the count against the map and against the routines you can name; an assembler routine may open with no recognisable prologue at all.

## Cost

One subtraction per routine on each side, twice. The correction is a text move -- and it can be done mechanically: parse the implementation section into blocks bounded by each declaration and its terminating `end;` at column zero, keeping each routine's preceding comment with it, and re-emit in the target order. Sixteen routines moved that way compiled first time and needed no forward declaration, which is worth knowing before hand-editing two thousand lines.

## Example

Part 002 of a 1994 VGA demo, Borland Pascal 7. `P2S2` held sixteen routines in a different order from `NEUROSIS.002`; the walk had reported 99.9% throughout. Reordering to the address map already in the file's header comment brought eleven of the sixteen to an exact length; the remaining five were a word-versus-byte parameter costing two bytes in three routines, a fused expression costing thirty-six, a one-based array costing forty-eight, and a routine that in the original neither counted frames nor flipped pages, costing 121. The unit went from 14,160 bytes to the original's 14,048 and the part from 99.9% to 100.0% with no unaligned span at all.

In the same session `P2S1` had four routines transposed -- 152, 145, 270, 127 against the original's 270, 127, 152, 132 -- and part 003 read exactly 100.0% while two of its units were sixteen bytes wrong in opposite directions. [1]

## Citations
[1] `src/P2GARAGE.PAS`, `src/P2SOLID.PAS`, `src/P3STARS.PAS` and `src/P3GLOBE.PAS` in the psycho repository; measured with `kit/tools/pascal/spans.py`, `prologue.py`, `unitorder.py` and the compiler's own map file on 26 Aug 2026.
