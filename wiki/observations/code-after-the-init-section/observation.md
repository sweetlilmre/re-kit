---
type: Observation
title: Code past the initialisation section came from an object file
description: A unit's initialisation code is the last thing Borland Pascal emits into its code segment, and nothing can be declared after it. So a routine at a HIGHER offset than the init section did not come from the Pascal source at all -- it came in through {$L file.OBJ}. The position is the proof, not the instructions; and because an object is linked whole, a dead routine in one ships where a dead Pascal routine would be smart-linked away.
tags: [pascal, turbo-pascal, linker, smart-linking, object-file, segment-layout, identification, reconstruction]
timestamp: 2026-08-26T00:00:00Z
---

# Code past the initialisation section came from an object file

You are reading a unit's code segment and the routines run out in a sensible order, then the initialisation section, and then -- after it -- two more routines. Pascal has no syntax for that. A unit's `begin` block is its last declaration; nothing follows it but `end.`, and Borland emits its code last in the segment.

**So code beyond the initialisation section did not come from the Pascal source.** It was linked in from an object file with `{$L file.OBJ}` and reached from `external` declarations, and the linker appended it to the unit's own segment. That is the whole inference, and it needs no instruction decoding at all.

It is worth having as its own tell because the usual one -- 386 instructions, which Turbo Pascal's built-in assembler cannot produce -- is easy to misread in both directions. An `asm` block with hand-written `DB 66h` prefixes looks 386ish and is not an object file; and an object file can hold perfectly ordinary 16-bit code, in which case the instructions say nothing whatsoever. The POSITION says it either way.

## And it explains a dead routine that ships

The second half of this is the more useful half in practice, because it resolves a contradiction that otherwise stops a reconstruction dead.

**Turbo Pascal smart-links per PROCEDURE. It links an object file per MODULE.** An unreferenced private Pascal routine is dropped from the executable; an unreferenced routine inside a linked object is not, because the linker's unit of inclusion is the whole object's code. So:

    a dead routine in the Pascal      is not in the image
    a dead routine in the .OBJ        is in the image, in full

Faced with a routine in the original that nothing anywhere calls -- no near call in its own segment, no far call in the entire image -- the natural conclusion is that the search is wrong. It may not be. Reconstructing that routine as Pascal and expecting it to appear will fail however carefully it is transcribed, because the smart linker will take it out again; and the failure looks like a transcription problem rather than a placement problem.

## Reading it

1. Find the initialisation section. It is the entry point the program's own startup chain calls -- one far call per unit, in a run at the top of the main body -- and it ends the code that the Pascal source produced.
2. Anything at a higher offset is object-file code. Its order is the object's order, not the Pascal's.
3. Count the calls to each of those routines, in the segment and across the image. The uncalled ones are the object's dead weight, and they are why the module is the unit of linkage.

## Blind spot

**Empty initialisation sections are easy to miss.** A unit whose `begin end.` is empty still gets a five-byte stub, and if you have mistaken that stub for something else you will draw the line in the wrong place. Confirm it against the startup chain's far calls rather than by looking for a big routine.

**Several objects can be linked into one unit**, and their code is appended in link order, so "after the init section" is one region rather than one module. And a unit with NO initialisation section at all gives this technique nothing to measure from.

**It does not tell you the object's source language.** TASM is the likely answer for 386 code in this era, but an object file is an object file.

## Cost

Reading two addresses and comparing them. The call count is a byte-pattern search per candidate.

## Example

Part 003's star-field unit, segment `10b8`, in a 1994 VGA demo. Its initialisation section is at `10b8:05f2` and ends at `07da`; two routines follow, at `07db` and `07f4`, both 386 -- a 32-bit multiply and a 32-bit divide, each three instructions round `IMUL`/`IDIV` with the result reassembled into `DX:AX`.

The divide is called four times from the segment, on the projection path of every point of every frame, which is why scene 2 needs a 386 when nothing else in the part does. **The multiply is called nowhere at all** -- not in its segment, and no far call to it exists anywhere in the image -- and it ships regardless. Adding both to the reconstruction as an assembled object took the part's coverage walk from 96.2% to 97.0%, and the multiply came through the smart linker untouched, which is the prediction this observation makes and the check that it holds. [1]

The same rule had already been written down in another part of the same target, from the other direction: a note in part 005's third scene records that its dead externals survive "because an external OBJ is linked whole, not per procedure". That note was in the tree while the star-field unit was being read as though its uncalled routine could not exist. [2]

# Citations

[1] `src/P3STARS.PAS` and `src/asm/STARMATH.ASM`, part 003 segment `10b8`, in the psycho repository; measured with `kit/tools/pascal/spans.py` on 26 Aug 2026.

[2] `src/P5PATCH.PAS`, same repository, dated 24 Aug 2026.
