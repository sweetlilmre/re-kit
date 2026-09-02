---
type: Observation
title: A named constant that only some of its uses go through is worse than no constant at all
description: Change the constant and the uses that go through it move; the ones written as literals do not. Three times in one file of one reconstruction, and the cost lands somewhere other than the defect -- once sixteen percentage points of a unit's agreement, once fourteen entirely correct units reading variables the short array had displaced.
tags: [reconstruction, codegen, measurement, verification]
measured_on: unrecorded
timestamp: 2026-08-29T00:00:00Z
---

# A named constant that only some of its uses go through is worse than no constant at all

A reconstruction carries a named constant -- a channel count, a buffer size, a table width -- and the next version changes it. You change the declaration, rebuild, and the unit is closer but still wrong.

**Some of the uses were written as literals.** They were correct when the literal and the constant agreed, and nothing distinguished them; the moment the constant moves, the literals become a defect that looks nothing like a stale constant. It reads as a second independent problem, in a different part of the unit, discovered later.

## Three, measured on one 16-bit Pascal reconstruction, all in one file

**A record's array field.** A channel count went from 8 to 16 and a record's size came out 71 bytes against the original's 119. `119 - 7 = 112` and `112 / 7 = 16` had already fixed the count; `71 - 7 = 64` is 16 volumes plus **8** notes, and that arithmetic named the surviving literal on sight -- one field declared `array[1..8]` where every other use went through the constant.

**A loop bound.** The same count again, written `for i := 1 to 8` inside a rarely-read block. Changing that single literal moved the unit's agreement from 37% to 53%: everything after the loop had been shifted by the four extra bytes of the wider compare.

**An array in another unit's block.** The same count a third time, `array[1..8] of Word`. This one cost the most and cost it somewhere else entirely: the array sits early in its unit's data block, so sixteen missing bytes displaced every variable after it AND every unit's block that follows -- **fourteen units that were entirely correct went from differing to exact when it was widened**, because they were reading variables another unit's declaration had moved.

## The symptom appears in units that are correct

That is the part worth carrying. A short array does not make the unit that declares it look wrong -- an indexed read with range checking off emits identical bytes whatever the bound is, so the unit compares byte-for-byte identical while its data is short. What looks wrong is everything DOWNSTREAM in the layout, none of which has a defect.

So a run of units all reporting the same data-address delta is not a run of defects. It is one declaration, in the last unit before the run begins, and the arithmetic points at it: the delta IS the size error.

## What to do

* When a constant changes, grep for its OLD VALUE as a literal in the same unit before rebuilding. It is faster than finding it from the diff.
* Prefer the arithmetic that found it: when a size is wrong by a whole multiple of something, factor the difference and see which term is short.
* A unit that improves and then stops improving after a constant change usually has exactly one literal left.

## Blind spot

**A literal equal to the constant is not necessarily a use of it.** This finds numbers that should have gone through the name by changing the name and watching what moves -- so any literal that happens to share the value moves too, and replacing it introduces a coupling that was never there. A screen width of 320 and an unrelated table of 320 entries are the same number and not the same fact.

**It cannot see a use that arithmetic has already absorbed.** Where the source wrote the value into an expression the compiler folded, there is no literal left to find and no site to fix -- and the constant then appears fully applied while a folded copy of the old value survives in the image.

## See also

* [A hardcoded address copied from the original is right by coincidence](../transcribe-the-meaning-not-the-constant/observation.md)
