---
type: Observation
title: A zero byte where the original has something else
description: Your byte is 0x00, theirs is a real value -- and the rule for what to do inverts by artefact.
tags: [comparison, fixups, relocation, zero-rule]
measured_on: unrecorded
timestamp: 2026-08-19T00:00:00Z
---

# A zero byte where the original has something else

You are comparing your bytes against the original. A difference has your `0x00` against their real value.

**There is no general answer to this.** The rule inverts depending on what you are holding, and applying the wrong one is destructive in both directions at once: it forgives real faults, and it reports faults that are not there. On one module that was actually correct, the wrong rule reported 65 divergent regions.

So the only question this page answers is: **which artefact are you looking at?**

<!-- generated:discriminator -->
| if you are looking at | how to tell | detail |
|---|---|---|
| a `.TPU` from Turbo Pascal | output of TPC that has not been linked yet | [tpu](./tpu.md) |
| an `.OBJ` assembled by TASM | output of TASM -- an OMF object module, not yet linked | [obj-tasm](./obj-tasm.md) |
| a linked image | the linker has already run -- an EXE, or a segment lifted out of one | [linked-image](./linked-image.md) |
<!-- /generated:discriminator -->

## Why the answer cannot be general

An unresolved reference has to sit somewhere in the byte stream until the linker fills it in. The three artefacts above are at three different points in that process, and each tool writes a different placeholder:

- Before linking, Turbo Pascal writes **zero**.
- Before linking, TASM writes an **addend** -- a partial answer, usually not zero.
- After linking, there is **no placeholder at all**.

A rule phrased as "forgive zeros" silently assumes the first case. That assumption is what makes it dangerous, because a `.TPU` and an `.OBJ` look equally like "our compiled output" from the outside.

## If you are not sure which you have

Check what produced the file, not what the bytes look like. The bytes cannot tell you: `0x00` is a legal value everywhere, and it means something different in each case.

## Blind spot

**A discriminator enumerates the artefacts somebody has held, and a reader holding a fourth one still gets an answer.** Three rows are three cases that came up; nothing here reports that a file is none of them. The nearest row will look close enough -- a library member, a packed image, an object from a different assembler -- and the reader inherits a rule chosen for a different point in the linking process, which is the exact failure this page exists to prevent, arriving through the page itself.

So the question above is worth taking literally. *What produced this file* has a right answer for every artefact; *which of these three is it most like* has a plausible answer for all of them.
