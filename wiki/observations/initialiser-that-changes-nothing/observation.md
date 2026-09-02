---
type: Observation
title: An initialiser that changes no byte means the declaration is at the wrong address
description: Set a typed constant's initial value to the one the original's image holds, rebuild, and compare. If nothing moved, the value did not land where you thought -- the declaration is somewhere else in its unit's block. Within a unit, the ORDER of declarations is as measurable as their sizes, and this is the cheapest probe for it.
tags: [dgroup, measurement, verification, reconstruction, tooling]
measured_on: unrecorded
timestamp: 2026-08-29T00:00:00Z
---

# An initialiser that changes no byte means the declaration is at the wrong address

A unit's initialised data is laid out in DECLARATION ORDER: each typed constant lands where the previous one left off. So the order of declarations inside a unit is a measurable fact about the original, not a matter of taste -- and until something disagrees, nothing forces you to measure it.

**The probe is a value you already know.** Take a typed constant whose initial value the original's image shows -- a 1 among zeros is ideal -- set it in the source, and rebuild.

    value lands, image changes    ->  the declaration is at the right address
    value set, image unchanged    ->  the declaration is somewhere else

The second case is the finding. A layout comparison will say it plainly: the count of blocks *in place* falls by one and one block reports as **moved**, which is the only reading that means "right content, wrong place". A byte comparison of the initialised half cannot say it, because both blocks are zeros either way.

## Measured

A ring buffer's consumer cursor starts at 1 in the original -- the image holds `01 00` at its address and a routine sets it again at run time beside the producer's `:= 0`. Setting the declaration to 1 changed nothing in the rebuild. The whole run was then reordered against addresses each of which an instruction names, and the block came back in place: the ring pair moves to the FRONT of the unit's block where the previous version has an unrelated word first.

## Why the order changes between versions at all

Because the author edited the declaration list. A version that adds three variables usually adds them where they belong logically, not at the end -- so a reconstruction carried forward from the previous release has the old order and the new sizes, and every address after the insertion point is wrong by the same amount. That reads as one unit being the wrong size and is not.

## Blind spot

**The probe needs its value to be UNIQUE in the block.** Setting a constant to what the image already holds at the position you expect, and seeing nothing move, is only evidence of a misplaced declaration when the value was not already there. Where it was -- a zero, a common size, a repeated flag -- nothing moves for the opposite reason, and the two outcomes are identical.

**It also assumes the build is otherwise unchanged.** Any edit that shifts the block for a different reason during the same rebuild makes the probe unreadable, so it is one probe per build, which is what makes it expensive rather than what makes it hard.

## See also

* [The total balances and the layout is still wrong](../balanced-total-hides-order/observation.md)
* [The data segment is laid out in reverse of the uses clause](../dgroup-order-reverses-uses/observation.md)
