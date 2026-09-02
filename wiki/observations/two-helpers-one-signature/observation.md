---
type: Observation
title: Two runtime helpers with one signature, and the difference is a fixup
description: Borland's `Move` and its whole-array assignment copy take the same three arguments in the same order and differ only in which runtime routine the call names. That target is a relocation fixup, so a unit comparison that forgives pending fixups cannot see the difference at all -- it appears for the first time in the linked image, after the unit has been reported identical.
tags: [codegen, rtl, comparison, verification, linking, reconstruction]
measured_on: unrecorded
timestamp: 2026-08-29T00:00:00Z
---

# Two runtime helpers with one signature, and the difference is a fixup

Borland has two block-copy routines in its runtime with the same signature -- source, destination, count -- and the source spelling picks between them:

    Move(A, B, SizeOf(A))    ->  the overlap-checking copy
    B := A                   ->  the plain one, no overlap check

The compiler knows a whole-array or whole-record assignment cannot overlap, so it calls the cheaper routine. A written `Move` cannot know that, so it gets the one that compares the pointers and copies backwards when they do.

**Both call sites are byte-for-byte identical except for the call target.** Same pushes, same order, same lengths. And the target of a far call into another unit is a **relocation fixup** -- which is exactly what a unit-level comparison is built to forgive, because at that stage the linker has not supplied it.

So the wrong one of these is invisible to the instrument that would normally catch it. Measured: a unit compared *identical but for pending fixups* for a dozen sessions with two of these wrong, and the difference appeared the first time the linked image was compared.

## What to do

* **Read the call target, not the call.** In a disassembly the two helpers are eleven bytes apart; note both offsets once and they are then distinguishable on sight.
* When a unit is clean at unit level and dirty in the linked image, suspect a *helper* before suspecting an address. Data addresses move for layout reasons and read as runs; a wrong helper is a single isolated operand.
* Going the other way -- transcribing an assignment as `Move` -- is the easy mistake, because `Move` is what the operation obviously *is*, and the reconstruction reads better with it.

## The type constraint the fix carries

An assignment needs one type on both sides. If the two objects live in different units, the type has to be declared in whichever unit the other one **uses** -- and that direction is fixed by the dependency graph, not by preference. A copy between a producer's buffer and a consumer's published structure can only become an assignment if the type lives in the consumer.

That is a real cost and worth weighing before assuming the assignment is right: moving a type between units changes nothing in the image, but it changes which unit owns the declaration, and a wrong guess there is a second edit.

## The general shape

Any pair of runtime routines with the same signature and different guarantees has this property -- a checked and an unchecked variant, a signed and an unsigned one, a near and a far one. The operand that separates them is the one an unlinked comparison cannot see.

## Blind spot

**Every per-unit comparison is blind to this by construction, and that is not a defect in them.** The tell is a relocation target, and a unit comparison must forgive relocations because those bytes legitimately differ before linking. So the earliest instrument that can speak is the linked image -- which makes this the LAST thing to be caught, at the point where the most changes are in flight and attribution is hardest.

**And the linked image says the targets differ, not which one is right.** Two calls with identical signatures and different runtime targets tell you a choice was made; deciding which of the two the original made is an argument from the source shape and the surrounding types, not a reading. Where both spellings are type-legal at the site, the image cannot arbitrate.

## See also

* [One runtime call serves div and mod, and the call cannot tell you which](../one-helper-two-operators/observation.md)
* [A tool that is wrong is useless; a tool that BECOMES right is worth re-asking every open question](../instruments-have-an-order/observation.md)
