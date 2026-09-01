---
type: Observation
title: Read a shared unit in the binary that uses least of it
description: A library unit linked into eight programs appears at eight different sizes, because the smart linker keeps only what each one references. The smallest of those is the place to read the unit's routine order and its near/far split -- sixty-four bytes and four items instead of two thousand bytes and forty -- and every correction found there pays out in all eight. Two one-byte tells settle near versus far -- a near return in a routine you put in the interface, and PUSH CS before a near CALL.
tags: [linking, smart-linking, pascal, units, reconstruction, method, measurement, near-far]
timestamp: 2026-08-26T00:00:00Z
---

# Read a shared unit in the binary that uses least of it

A graphics unit is linked into eight programs. In the biggest it is two thousand bytes and forty routines, and reading it means separating forty items you have to identify before you can compare any of them. In the smallest it is **sixty-four bytes and four items**, because the smart linker kept only what that program actually calls.

Read it there.

    100b:0000  b8 13 00 cd 10 cb              SetMode13h    -- 6 bytes, no frame
    100b:0006  b8 03 00 cd 10 cb              SetTextMode   -- 6 bytes, no frame
    100b:000c  c8 02 00 00 ... c9 c3          BuildRowTable -- ENTER, and a NEAR ret
    100b:0031  55 89 e5 e8 d5 ff c9 cb        initialisation -- a NEAR call to it
    100b:0039  00 x 7                         padding to the paragraph

Four items in one screen. The order is right there, the frames are right there, and the return instructions answer a question that is invisible in the large version: **which of these routines is in the interface?**

## The two tells, and they are one byte each

| you see | it means |
|---|---|
| `C3` -- a **near** return -- ending a routine you declared in the interface | it does not belong in the interface. Borland compiles every interface routine FAR |
| `E8` -- a **near** call -- reaching a routine from elsewhere in the unit | same thing, from the caller's side |
| `0E E8 xx xx` -- **PUSH CS then a near CALL** | the callee is FAR and in the same segment. That is the compiler's four-byte far call, against five for `9A seg:off` |
| `CB` -- a **far** return -- ending a routine nothing outside the unit calls | the unit is `{$F+}`, so everything in it is far whatever the interface says |

The last two are the same question answered the other way round, and both cases turn up in one afternoon's work. A routine wrongly in the interface returns far and costs a byte at each end; a unit wrongly left at `{$F-}` returns near and costs a byte at *every call site* — and puts every routine after the first at the wrong address.

## Why the small consumer is the right place

**Fewer items means fewer identifications, and identification is the expensive step.** Sixty-four bytes of four routines can be matched by shape alone. The same unit at two thousand bytes needs each routine named before its bytes mean anything, and a routine at the wrong address contaminates the reading of its neighbours.

**And the padding tells you where the unit ends.** A run of zeros to a paragraph boundary bounds the last item exactly, which in a large segment is buried.

**The correction then pays out everywhere.** This is the part worth planning around: a defect in a shared unit is one edit and N measurements. Three corrections read out of that 64-byte dump — a routine taken out of the interface, a routine rewritten as `assembler` with no frame, and two routines swapped into the original's declaration order — moved *two* separate programs' coverage, and cost nothing anywhere else.

## The method

1. Find the consumer whose copy of the unit is smallest. The segment map gives it: the unit's extent is the next segment's base.
2. Dump it whole and identify the items by shape.
3. Read the **returns** for the near/far split and the **order** for the declaration order.
4. Fix the unit, then **measure every consumer** — not just the one you read. A shared-unit change moves them all, and one of them may be a byte-exact target whose match is a ratchet you must not break.

Step 4 is not optional. The unit is shared; so is the risk.

## Blind spot

**The small consumer cannot show you what it does not reference.** Routine order among items it never calls is invisible there, and so is any routine it drops entirely. What the small copy gives is the *relative* order of the items it does keep — enough to place them against each other, not enough to order the whole unit. Build the order up from several consumers, cheapest first.

**And smart-linking is per item, so absence proves nothing about the source.** A routine missing from the small copy was not deleted from the unit; it was not called. Reading absence as evidence about the original's source is the mistake this whole approach invites -- see [Absence reads as zero](../absence-reads-as-zero/observation.md) for the general form.

**The padding is not always there.** It appears when the next segment starts at a paragraph boundary and the unit's code does not end on one. A unit whose last byte lands on the boundary gives no zeros and no free bound.

## Cost

One dump and one reading, and the payout multiplies by the number of consumers. The corrections themselves were a directive, a declaration moved, and a procedure turned into an `assembler` one.

## Example

A 1994 DOS demo in eight parts sharing one VGA unit. The smallest part's copy was 64 bytes and four items; the largest was over two thousand. Reading the small one gave three corrections — `BuildRowTable` out of the interface (its `C3` said so), `SetTextMode` as a six-byte `assembler` routine instead of a framed Pascal procedure wrapping an `asm` block, and those two swapped into the original's order — which moved two parts at once, 99.0% to 99.4% and 99.3% to 99.4%, with three byte-exact artefacts still matching. The same afternoon, `CB` ending a routine nothing outside its unit calls, plus `0E E8` at two call sites, said a *different* unit was `{$F+}`; adding the directive took that part to 99.7%. [1]

## Citations
[1] `src/VGA.PAS` and `src/P7FLIC.PAS`, parts 006 and 007 in the psycho repository; measured with `kit/tools/pascal/spans.py` and `artefact.py` on 26 Aug 2026.
