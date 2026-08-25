---
type: Observation
title: A pointer costs four bytes where the array cost four thousand
description: A reconstruction that puts a buffer on the heap where the original declared it inline leaves DGROUP short by the whole array, which displaces every variable after it and makes correct code measure as wrong. No code-level instrument can see it -- the routines differ by one indirection. The gaps between the addresses a project's own comments have accumulated price every declaration and find it.
tags: [pascal, turbo-pascal, dgroup, source-shape, variables, heap, reconstruction, blind-spot]
timestamp: 2026-08-25T00:00:00Z
---

# A pointer costs four bytes where the array cost four thousand

`Font : ^TFont` with `New` and `Dispose` around it, and `Font : TFont`, are both reasonable readings of a routine that reads a font file into memory and indexes it. They are four bytes and 3,776 bytes of DGROUP respectively.

**Every variable declared after the wrong one is then at the wrong address**, and because a data reference carries its displacement inside an otherwise correct instruction, whole units measure as unaligned while containing no defect at all. The cost is not the four bytes; it is everything above them.

## Why nothing you normally run will find it

The two versions' *code* is nearly identical. A heap array is reached through one extra indirection -- `LES DI,[Font]` before the subscript arithmetic instead of the arithmetic alone -- so:

- a frame check passes: the pointer is a unit-level variable, not a local, so no prologue changes
- a routine-by-routine byte check reports a near-match, because the difference is a handful of bytes at the top of each accessor
- the initialised-data image is untouched: neither form is a typed constant, so neither appears in it
- a coverage walk that locates by content finds the accessor perfectly well and reports the *rest of the program* as unaligned

That last one is the trap. The instrument that reports the damage points everywhere except at the cause, and the cause is one character of source.

**The one instrument that sees it is a map of data references paired against the original's**, because a whole block sitting at a uniform offset from where it should be is exactly what this produces. See [The data segment is laid out in reverse of the uses clause](../dgroup-order-reverses-uses/observation.md) for reading those shifts -- in particular that a *uniform* shift is a size or placement defect, and that the step between two runs of shifts gives the surplus or shortfall in the gap between them, in bytes.

## The method: your own comments already priced every declaration

A reconstruction accumulates addresses in its comments -- `{ DS:$5BCC -- entry 0 is the translation }` beside one array, `{ DS:$632F, stride 7 }` beside the next. Individually each is a note. **Collected and sorted, they are a map, and the gap between two consecutive addresses is the size of what is declared at the first one.**

    grep -oE 'DS:\$[0-9A-Fa-f]{4}' src/UNIT.PAS | sort -u

Then price each declaration against its gap. An array whose gap matches its computed size is confirmed. An array whose gap is far larger has something undeclared after it. **A declaration whose gap is thousands of bytes while the declaration itself is four is a pointer where an array belongs.**

The check that the whole reading is sound is that **it tiles**: each address plus its size should be the next address, with the last one landing exactly where the following unit's block begins. A layout that tiles from end to end is one where every size is right; one that does not tells you how much is missing and between which two variables.

This is worth reaching for before a linker map, and not only because it is cheaper. A map describes the build you have; the comments describe the binary you are trying to match.

## Blind spot

**The comments are not a measurement, they are a record of past measurements, and they go stale.** In the case below the same array had two addresses recorded in one file, 2,049 bytes apart, and the one beside its declaration was the wrong one. Prefer an address recorded beside the *code that uses it* -- that comment was written while somebody was reading the arithmetic -- and use tiling to arbitrate. Where two disagree, one of them is a fossil.

**A single-site shift is not a location.** A pairing supported by one reference can be a coincidence, and the arithmetic built on it will be confidently wrong. In the case below, two shifts implied that 13,000 bytes had gone missing from a region that is 1,032 bytes long in the original -- which is not a finding, it is a mispairing. Anchor on multi-site shifts before doing any arithmetic.

**And the direction of the fix is not automatic.** The original may genuinely have used the heap; plenty of 1994 code does, and the surrounding units in this very case `GetMem` four buffers deliberately. What settles it is DGROUP volume, not taste. Do not sweep pointers into arrays because one turned out to be one.

## Cost

One `grep`, a sort, and subtraction.

## Example

Part 001 of a 1994 megademo was at 81.5% with its remaining defect known to be data placement: a data-reference map paired the original's `$AAC6` with ours at a uniform shift of `-23530`, so one whole unit's block, and everything above it, sat 23,530 bytes too low. The units below it were collectively that much too small, and the number is the size of a buffer rather than of a variable or two.

The linker-map route failed immediately -- the switch that would emit one broke the compiler's command line, though the build tool at least refused to install anything rather than leave a stale executable to be measured. The sources' own `DS:` comments turned out to be enough. Sorted, the unit read:

    $5AD2  file record      $672D  Pal
    $5B6A  ProfileA         $6A2A  Font
    $5B9B  ProfileB         $80C2  Blob
    $5BCC  Trail            $9DDB  Star
    $632F  Outp             $A106  the next unit's model

`Outp`'s gap is 1,022 bytes and its record is seven, which is 146 entries exactly -- so the loop bound was confirmed on the way past. **`Font`'s gap was 3,776 bytes and `Font` was declared `^TFont`.** Making it a plain `TFont` and dropping the `New` and `Dispose` moved the shift from `-23530` to `-19758`: a difference of **exactly 3,772**, which is 3,776 minus the four bytes of pointer it replaced. The coverage walk moved 81.5% to 81.7%, with the initialised image unchanged and the x87 trap streams still identical opcode for opcode.

Two things worth carrying. **The right address was in the file all along, and so was the wrong one.** The declaration's comment said `$7233`; the drawing routine's comment, beside the subscript arithmetic that uses it, said `$6A2A`. `$6A2A` is the one under which the unit tiles -- `Star`'s ninety nine-byte records then end at `$A105`, one byte below where the next unit's block begins. A stale note beside a declaration had outlived a correct note beside the code.

**And the same table priced what is still missing.** With `Font` inline the unit totals about 15,895 bytes against the original's 17,972, and the deficit sits in one identifiable place: `Font` ends at `$78EA`, `Blob` begins at `$80C2`, and nothing is declared in the 2,008 bytes between. Two independent arithmetics -- the unit's total and the gap -- agree to within seventy bytes, which is what makes it worth chasing rather than guessing at. [1]

# Citations

[1] `src/P1S4.PAS` and `src/P1S5.PAS`, part 001, in the psycho repository; measured with `kit/tools/pascal/dsmap.py`, `spans.py`, `dgimage.py` and `fpusites.py --diff` against the shipped binary on 25 Aug 2026. Recorded as `part1-unit-sizes`, with the residual as `part1-p1s4-hole`.
