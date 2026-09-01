---
type: Observation
title: A typed constant nothing reads is invisible to every comparison that follows an instruction
description: A declared constant that no instruction names still occupies bytes. Every verification instrument here works by following code -- a decoder, a fixup map, an operand pairing -- so all of them are blind to it by construction, and a unit can compare byte-for-byte identical while carrying data the original does not have or missing data it does. Only a LAYOUT comparison sees it.
tags: [comparison, verification, dgroup, reconstruction, measurement, tooling]
timestamp: 2026-08-29T00:00:00Z
---

# A typed constant nothing reads is invisible to every comparison that follows an instruction

You have a unit that compares identical to the original, instruction for instruction, and its data block is the wrong size.

**A typed constant is emitted whether or not anything reads it.** Borland allocates it from the declaration, not from the use, so a declaration that has outlived its readers -- or one that never had any -- costs bytes in the image and nothing anywhere in the code segment points at it.

Every instrument that verifies code is blind to this **by construction**:

* a decoder walks instructions, and there is no instruction
* a fixup map lists relocation targets, and dead data is never a target
* an operand pairing compares what two builds reference, and neither references it
* a coverage walk locates content by matching it, and matching finds it in both

## Three shapes, all measured on one 16-bit Pascal reconstruction

**A declaration that outlived its readers.** An eight-entry pan table was read at three call sites. Over several sessions all three moved to a per-channel field in another record, and every one of those changes verified byte-for-byte. The declaration stayed. Sixteen bytes of initialised data that no instruction could ever point at, found only when the data layout came out sixteen bytes long.

**Declarations that never had readers.** Three four-byte magic strings sat consecutively where the source declared one. The unit's code was byte-exact without the other two, which is itself the proof that the original does not reference them either -- the format stamps a marker the loader reads as filler and never checks.

**A guess that never had to be resolved.** When a channel count doubled, an array needed sixteen entries where eight were measured; eight went in as a repeated pattern and were flagged in the source as a guess. The right answer was that the table does not exist. **A guess that turns out to be unnecessary is the best outcome for a guess** -- and flagging it is what stopped it being quietly believed in the meantime.

## What to do

Get the layout comparison working, and treat a size disagreement in a unit whose code is exact as a DATA question, not a code one. The reverse inference is the useful one:

    code exact + data short   ->  a declaration you have not made
    code exact + data long    ->  a declaration nothing reads

Neither can be chased through the disassembly, because there is nothing there to chase. Reading the original's own bytes at the address is the only move.

## See also

* [Every declared routine matches, and the rebuild still behaves differently](../verifier-blind-to-absence/observation.md)
* [A total quietly drops a component and stays plausible](../absence-reads-as-zero/observation.md)
* [A filler declaration records what you have not looked at, not what is not there](../filler-is-not-a-finding/observation.md)
