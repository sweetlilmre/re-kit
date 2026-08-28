---
type: Observation
title: A named constant that only some of its uses go through is worse than no constant at all
description: Change the constant and the uses that go through it move; the ones written as literals do not. The rebuild then disagrees with the original in a way that looks like a second, unrelated defect. Twice in one reconstruction this cost real ground, once sixteen percentage points of a unit's agreement.
tags: [reconstruction, codegen, measurement, verification]
timestamp: 2026-08-29T00:00:00Z
---

# A named constant that only some of its uses go through is worse than no constant at all

A reconstruction carries a named constant -- a channel count, a buffer size, a table width -- and the next version changes it. You change the declaration, rebuild, and the unit is closer but still wrong.

**Some of the uses were written as literals.** They were correct when the literal and the constant agreed, and nothing distinguished them; the moment the constant moves, the literals become a defect that looks nothing like a stale constant. It reads as a second independent problem, in a different part of the unit, discovered later.

## Both measured on one 16-bit Pascal reconstruction

**A record's array field.** A channel count went from 8 to 16 and a record's size came out 71 bytes against the original's 119. `119 - 7 = 112` and `112 / 7 = 16` had already fixed the count; `71 - 7 = 64` is 16 volumes plus **8** notes, and that arithmetic named the surviving literal on sight -- one field declared `array[1..8]` where every other use went through the constant.

**A loop bound.** The same count again, written `for i := 1 to 8` inside a rarely-read block. Changing that single literal moved the unit's agreement from 37% to 53%: everything after the loop had been shifted by the four extra bytes of the wider compare.

## What to do

* When a constant changes, grep for its OLD VALUE as a literal in the same unit before rebuilding. It is faster than finding it from the diff.
* Prefer the arithmetic that found it: when a size is wrong by a whole multiple of something, factor the difference and see which term is short.
* A unit that improves and then stops improving after a constant change usually has exactly one literal left.

## See also

* [transcribe-the-meaning-not-the-constant](../transcribe-the-meaning-not-the-constant/observation.md)
