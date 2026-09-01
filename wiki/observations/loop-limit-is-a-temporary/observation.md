---
type: Observation
title: A loop limit that is not a constant is a frame slot you must not declare
description: Borland Pascal evaluates a `for` loop's upper bound once into a stack temporary and then compares against it every iteration, so the slot is written once and read often -- indistinguishable from a declared local. Transcribing it as one produces both it and the compiler's, and the frame lands over.
tags: [pascal, turbo-pascal, borland, frame-layout, transcription, blind-spot, instruments]
timestamp: 2026-08-24T00:00:00Z
---

# A loop limit that is not a constant is a frame slot you must not declare

You are recovering a routine's `var` block from its frame, the way `frame-size-counts-locals` describes: add up the declarations, and if they do not reach the prologue's operand you are missing one. You find a slot that is written once near the top of a loop and read on every iteration, and you declare it.

**It may not be a declaration at all.** Borland Pascal compiles `for I := 1 to Expr do` by evaluating `Expr` ONCE into a stack temporary and comparing the counter against that temporary each time round. The generated code is:

    MOV  AX, <the limit expression>
    MOV  [BP-n], AX          ; the temporary
    MOV  AX, 1
    CMP  AX, [BP-n]          ; and again at the bottom of the loop

which is exactly what a declared local initialised from an expression looks like. There is nothing in the instruction stream that distinguishes them.

## Why it matters, and it is not cosmetic

**Declaring it produces two slots where the original has one** -- yours and the compiler's, because the compiler still makes its temporary for the same loop. The frame comes out over, and every slot below the mistake is at the wrong offset.

Measured on one segment of a Borland Pascal 7 binary. Three routines share a body and each opens `ENTER $1154` = 4,436 bytes:

| what was declared | frame emitted |
|---|---|
| the two loop limits declared as locals, plus padding bytes to place them | **$115c** -- 8 over |
| neither declared, limits written as expressions | **$1152** -- 2 under |
| neither declared, plus the one genuine Byte the routine does have | **$1154** -- exact |

A fourth routine in the same segment had the same defect and the same cure. The middle row is the useful one: it shows the compiler making the temporaries by itself once the source stops competing with it.

## The tell, and it is arithmetic rather than inspection

**Count what the declarations must be and see what is left over.** In the routine above, the value parameter's copy is 2,897 bytes, the local face array 1,495, two Integers 4, and one Byte 1; the frame is 4,436, so the remainder is the compiler's -- and the loop-limit slots are among it even though both are read constantly.

**A word at an odd BP offset is NOT proof of a one-byte local declared before it.** That sub-rule holds for declarations, and a temporary obeys no such rule; here two words sat at odd offsets and both were the compiler's. Reading them as declarations is what produced the 8-over row above, because placing them needed invented padding bytes.

## Blind spot

**A prologue scan cannot see this, and worse, it can say the opposite.** An instrument that reports "the lowest slot touched is [BP-n], so the bytes beyond it are the code generator's temporaries" states something true and implies something false: that everything at or above the lowest touched slot is declared. The bytes beyond the last touched slot are a LOWER BOUND on the temporaries, never the whole of them. The instrument here was reworded rather than left to mislead a second time.

**The distinction is not recoverable from one routine in isolation.** What separates the two readings is the frame arithmetic closing, so it takes a build to settle -- which means a routine whose other declarations are still wrong cannot be used to test this, and two uncertainties have to be resolved together.

**Only some limits become temporaries.** A constant limit is compared as an immediate and costs nothing, so `for I := 1 to 100` leaves no slot at all. The rule fires on a variable, a field, a function result -- anything the compiler will not fold.

## Cost

Reading the loop's compare operand, then arithmetic on the frame. Settling it needs one build per variant.

## Example

`NEUROSIS.002` segment `108b`: the three renderers at `0a2d`, `0b42` and `0ca1`, and the face sorter at `0e03`. In the renderers `[BP-$1151]` takes `O.FaceCount` at `108b:0bb9` and `[BP-$1153]` takes `Faces[F].Count` at `108b:0be1`; in the sorter `[BP-$1134]` takes `Tmp.FaceCount` at `108b:0e1a` and is REUSED by a second loop at `108b:0ed7`, which is itself a hint -- a declared variable would not be re-initialised from the same expression at two unrelated places. Declaring all four cost 8 bytes of frame in three routines and 2 in the fourth; handing them back to the compiler took the part's coverage walk from 77.4% to 78.3%. [1]

## Citations
[1] `src/P2SOLID.PAS`, the `var` blocks of `RenderA`/`RenderB`/`RenderC` and `ObjSortFaces` and the notes in them, in the psycho repository.
