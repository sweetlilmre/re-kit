---
type: Observation
title: A block reached through its neighbour's symbol is invisible to every search for its own address
description: The standard question about an unexplained region is "what reads or writes these bytes". A downward-growing stack answers that question with nothing, truthfully -- the code loads the address ABOVE the block and lets the hardware walk down through it. So the region looks dead to every instrument, and the instruction that proves it alive names a different variable.
tags: [reverse-engineering, dgroup, verification, measurement, naming]
timestamp: 2026-08-29T00:00:00Z
---

# A block reached through its neighbour's symbol is invisible to every search for its own address

Faced with a region no declaration explains, a reconstruction asks one question: **what reads or writes these bytes?** Search the image for the address, find the instructions, name the region from what they do. When the search comes back empty the region is recorded as reserved, and the record is honest — the search really did find nothing.

**A stack breaks that question, because a stack is never addressed by its base.** The code loads a pointer to the address *above* the block and the hardware walks down through it. Nothing anywhere holds the block's own address. Every instrument agrees it is dead, and every instrument is right about what it measured and wrong about what that means.

Measured. A 1000-byte region sat unexplained for the whole of one reconstruction:

    $5e8c  DevStack   1000 bytes
    $6274  <unexplained>  1000 bytes
    $665c  SavedSS

The instruction that uses it is `MOV SP,OFFSET SavedSS` — SP set to `$665c`, with SS already pointing at the data segment. That is the top of the unexplained block, written as the address of the variable *after* it. **`$6274` appears in no instruction in the image.**

## Why it survived so long

Three separate readings had gone past it:

* An **exhaustive operand search** found no reference, correctly.
* A **byte comparison** could not see it: uninitialised storage holds no bytes, so every layout that keeps the total size agrees.
* A **sibling release** was consulted and had nothing there — the earlier version declares its stack, its saved SS and its saved SP with no gap between. The gap is real and new.

Each answer was accurate. Together they made a strong case for "reserved", and the case was wrong.

## The tell was arithmetic, not evidence

What eventually broke it open was a number that would not come out round. The assembler reached the first stack's top with `OFFSET DevStack + 998` where the sibling writes `OFFSET DevStack + StackSize`. **A constant that has to be written as 998 where the original writes it as its own size means a base is misplaced**, and correcting it produced two blocks of exactly the stack size, back to back, with the second one's top landing precisely on the next named variable.

Three equal, adjacent, suspiciously round quantities are an argument on their own. Follow them before concluding a region is reserved.

## What to check before recording a region as dead

* **Does any instruction load an address just PAST the region?** That is a downward stack, a descending buffer pointer, or a reverse copy.
* **Does any instruction load an address just BEFORE it?** That is the ascending equivalent.
* **Is the size equal to a neighbour's size?** Two adjacent blocks of the same length usually means two of the same thing.
* **Count the stack switches against the re-entrancy guards.** They come in pairs. This program grew a second guard in the version under reconstruction, and the second guard existed because a second routine needed a second stack — the guard was documented years before the stack it implied was found.

## See also

* [link-order-brackets-the-unanchored](../link-order-brackets-the-unanchored/observation.md)
* [dead-data-has-no-witness](../dead-data-has-no-witness/observation.md)
* [filler-is-not-a-finding](../filler-is-not-a-finding/observation.md)
* [no-writer-means-input](../no-writer-means-input/observation.md)
* [verifier-blind-to-absence](../verifier-blind-to-absence/observation.md)
