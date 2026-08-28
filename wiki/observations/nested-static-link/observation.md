---
type: Observation
title: Every element read costs fourteen bytes and goes through the frame twice
description: A routine that reaches its data through [BP+4] and then a far load out of that frame is NESTED, and the data belongs to the routine enclosing it -- which fixes the source's shape, not just its instructions.
tags: [pascal, codegen, nesting, basm, turbo-pascal, source-shape]
timestamp: 2026-08-23T00:00:00Z
---

# Every element read costs fourteen bytes and goes through the frame twice

You are reading a routine and every single element access looks like this:

    MOV DI,[BP+4]        the enclosing frame
    LES DI,SS:[DI+4]     a far pointer OUT of that frame -- a var parameter
    ADD DI,AX
    MOV AX,ES:[DI-3]

Fourteen bytes to fetch one value, and it happens on every iteration. It looks like code somebody forgot to optimise.

**It is not. The routine is nested, and what it is reading belongs to the routine that encloses it.** `[BP+4]` is the *static link* -- a pointer to the enclosing procedure's frame that Turbo Pascal pushes as a hidden argument -- and not a parameter of this routine's own. The `LES` is there because what sits in the enclosing frame is itself a far pointer: a `var` parameter of the outer routine. Two indirections, because the data is two scopes away from the instruction that wants it.

The other tell is at the end: a nested procedure reached through a static link ends `RET 2`, because the link is an argument and gets cleaned up like one.

**This fixes the shape of the source, not just its instructions.** A reconstruction that declares the same data as unit variables turns every one of these into a single DGROUP read, and no amount of care inside the routine will recover the byte stream -- the routine has to be nested inside the right enclosing routine before its bytes can match at all.

## Why it works

Turbo Pascal has exactly one mechanism for a nested procedure to reach an enclosing scope, and it is visible in the instruction stream: the frame pointer of the enclosing activation, passed in and read back out. There is no other reason for a routine to load a frame pointer it did not establish. A unit-level variable compiles to a DGROUP reference, a parameter compiles to a fixed offset off this routine's own `BP`, and a local compiles to a negative one -- so the positive displacement at `[BP+4]` followed by a load *through* what it fetched has one cause.

The displacement off the static link is also information: it says where in the enclosing frame the variable sits, which constrains the enclosing routine's own declarations.

## Blind spot

**The displacement names a position, not a variable.** `SS:[DI-$0A]` says the tenth byte below the enclosing frame pointer and nothing more, so the enclosing routine's locals still have to be worked out from their sizes and declaration order. Get that order wrong and every displacement below the mistake moves.

**Once nested, an enclosing variable cannot be named inside an `asm` block, and the failure is silent.** Written as `LES DI, SrcOfs` inside an `asm` block in a nested procedure, Turbo Pascal emits `LES DI,[BP-6]` -- it has resolved the *enclosing* procedure's variable against the *nested* procedure's frame. **It compiles cleanly and is wrong at run time.** Those fetches have to be written as Pascal and the assembler left to work on the result. This is a second scope trap in the same family as the one where a field name inside `with` assembles as its own offset constant.

**It says nothing about whether the nesting is deliberate.** Compilers of this era nest whatever the source nests; the pattern proves the original's source shape, not that the shape was a good idea. It is often the opposite -- see the example.

## Cost

A disassembler and the routine's prologue. No comparison against a rebuild is needed to read it: the pattern is diagnostic on its own.

## Example

Two cases in `PSYCHO NEUROSIS`, both on 23 Aug 2026.

`1107:0287` in part 001 is a Hoare quicksort over 144 seven-byte records, nested inside a one-line wrapper at `1107:03d7` whose only statement calls it. The array it sorts is the wrapper's caller's `var` parameter, so every depth-key fetch is the fourteen bytes above -- on the order of a thousand times a frame. **This is one of the few places where the reconstruction is faster than the original**, which matters to any pacing comparison for that scene and is recorded as a deviation rather than fixed. [1]

Part 003's globe scene had its structure wrong for weeks. `Globe_LoadTables`, `Palette_FadeIn` and `Globe_RenderFrame` are all nested inside `Demo_Scene4` in the original -- `119d:019a` is `MOV DI,[BP+4]` / `LES DI,SS:[DI-$0A]`, and `119d:00a9` reads the target palette as `SS:[DI+$FCF6]`. Ours held the tables and the palette as unit variables, which made every one of those a DGROUP read. Once nested, `RenderFrame` matched for all **121** bytes of it, ending on its real `LEAVE` / `RET 2`. The `asm`-block trap in the blind spot above was found in that same routine. [1]

# Citations

[1] `docs/23-deviations.md` in the psycho repository -- the depth-sort entry and the part 003 globe-scene entry, with the addresses, the 121-byte result and the `LES DI, SrcOfs` trap. The span was found by `shapediff.py 001`, which lists it as `1107:0287..039a`; that script is archived under the psycho repository's `archive/pre-kit-scripts` tag and its measurement is `kit/tools/pascal/spans.py`.
