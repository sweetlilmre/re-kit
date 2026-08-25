---
type: Observation
title: Inc(v, n) and v := v + n compile to different code
description: Borland Pascal's Inc emits a read-modify-write instruction against memory; the equivalent assignment loads the target into a register pair, adds, and stores back. For a LongInt that is twelve bytes against eighteen. Both are correct Pascal and neither is an optimisation of the other, so a reconstruction that picks the shorter one shifts every byte after it in the segment -- and the coverage walk blames somewhere else.
tags: [pascal, codegen, turbo-pascal, source-shape, statements, reconstruction, blind-spot]
timestamp: 2026-08-25T00:00:00Z
---

# Inc(v, n) and v := v + n compile to different code

`Inc(X, D)` and `X := X + D` mean the same thing and produce different bytes. Turbo Pascal treats `Inc` as an instruction to modify memory in place; it treats the assignment as an expression to evaluate and a result to store. Neither is an optimisation of the other and the compiler will not convert between them, so **which one the 1994 author typed is recoverable from the binary, and getting it wrong costs six bytes a site on a `LongInt`.**

## The two shapes

For `LongInt` locals at `[BP-0C]` and a value at `[BP+0E]`:

    Inc(X, D)                       X := X + D
    ---------------------------     ------------------------------
    MOV AX,[BP+0E]                  MOV AX,[BP-0C]
    MOV DX,[BP+10]                  MOV DX,[BP-0A]
    ADD [BP-0C],AX                  ADD AX,[BP+0E]
    ADC [BP-0A],DX                  ADC DX,[BP+10]
                                    MOV [BP-0C],AX
                                    MOV [BP-0A],DX
    12 bytes                        18 bytes

**The tell is the direction of the `ADD`.** `Inc` loads the *increment* into registers and adds the register into memory, so the destination operand is the target. The assignment loads the *target* into registers and adds memory into it, so the target appears as a source and is written back by two explicit `MOV`s. One glance at whether the target is the `ADD`'s destination or its source settles which statement was written.

The same split applies to `Dec` against `X := X - D`, and it scales with the type: an `Integer` costs one instruction of difference rather than three, and the register pair collapses to a single register.

## Operand order is visible too, once you are in the assignment form

The assignment form loads its **left** operand first. So when one side is a function call, the binary says which side it was on:

    P^.X := IntToFixed(D) + P^.X        P^.X := P^.X + IntToFixed(D)
    ----------------------------        ----------------------------
    PUSH D                              LES DI,[..]
    CALL IntToFixed                     MOV AX,ES:[DI]      \ the field is
    LES DI,[..]                         MOV DX,ES:[DI+2]    / loaded first,
    ADD AX,ES:[DI]                      PUSH D                then spilled
    ADC DX,ES:[DI+2]                    CALL IntToFixed       across the call
    MOV ES:[DI],AX                      ...

A call as the left operand needs no spill, because nothing is live across it. A call as the right operand forces the compiler to keep the already-loaded field somewhere, which shows up as extra frame traffic. **So the presence or absence of a spill around a call names the operand order**, and a routine written the wrong way round differs by more than the two operands swapping.

## Why it works

`Inc` is not a function and not a macro; it is a code-generator special case that exists precisely to emit the in-place form. The assignment goes through the ordinary expression evaluator, which has no rule for recognising that the target is also an operand. Real-mode BP7 does no peephole pass over the result, so nothing afterwards collapses one into the other.

## Blind spot

**A byte-diff walk that forgives short runs will not report this, and will blame something else.** Six bytes is under most tolerance thresholds, so the site itself reads as a near-match; what the walk sees is that everything *after* the site is displaced. On one part more than a dozen separate unaligned spans all traced back to a single address, and that address was the third of three consecutive `Inc` sites -- the reported spans were downstream shrapnel, none of them containing the defect. **Trace a cluster of spans to its earliest length change before reading any of them.**

**The frame does not move**, so a prologue check passes either way. This is the same family as [Borland Pascal emits one instruction per operator](../one-operation-per-operator/observation.md): a defect that changes only the *length* of a statement, invisible to every instrument that measures declarations.

**And it is not a style question you can settle by preference.** Both forms appear in real 1994 sources, sometimes in adjacent routines, so there is no rule like "the author always used `Inc`" to fall back on. It has to be read per site.

## Cost

Reading one `ADD`'s operand order. No arithmetic.

## Example

A per-point 3D transform at `12c5:01b0` in a 1994 VGA demo had just been extracted into its own routine, and its prologue and by-value parameter copy came out byte-identical to the original. Its three translation adds were written as `Inc(P.X, TX)` and so on, which read naturally and are what the routine's earlier inlined version had used.

The original does not do that. At `12c5:01da` it is `MOV AX,[BP-0C] / MOV DX,[BP-0A] / ADD AX,[BP+0E] / ADC DX,[BP+10] / MOV [BP-0C],AX / MOV [BP-0A],DX` -- the assignment form, three times, eighteen bytes each. Ours was twelve each, so the routine was 18 bytes short and everything after it in a 21,264-byte segment was displaced.

`spanwhy` had been saying so for two iterations without being understood: more than a dozen unaligned spans across the segment each reported *first length change ... at `12c5:0201`*, and `12c5:0201` is inside the third of those three adds. The spans it listed -- at `04b7`, `04e9`, `0522`, `056e`, `0651`, `069f` -- contained no defect at all.

Writing the three as `P.X := P.X + TX` brought the routine to **305 bytes with 24 differing, and all 24 are call displacements or absolute DGROUP displacements**, which are the allowed-difference classes. The same unit's translate routine had the same defect, and its operand order was recoverable on top: `12c5:03b6` calls `IntToFixed` and *then* does `ADD AX,ES:[DI]`, so the call is the left operand. That span fell from 91 bytes to 29. The part's coverage walk moved 81.2% to 81.5% on the two changes together. [1]

Worth noting what the gain was *not*. The same session had just landed a much larger and fully measured restructuring of the same unit -- a record type, two pointer parameters, and an array bound corrected from 64 to 100 on the evidence of a `$4B0` displacement -- and that bundle moved the walk **nine bytes**. The statement-length defects it exposed were worth eight times as much. A correct structural change that does not pay is not evidence the structure was wrong; it is often the thing that makes the next defect legible. [2]

# Citations

[1] `src/P1S5.PAS`, part 001 segment `12c5`, in the psycho repository; measured with `kit/tools/pascal/spans.py` and `spanwhy.py` against the shipped binary on 25 Aug 2026.

[2] The same file and date. The bundle is recorded as `part1-object-record` and the residual as `part1-dgroup-placement`, which is the unit's whole data block sitting some 26KB from the original's -- the reason the routine's remaining 24 bytes are displacements rather than instructions.
