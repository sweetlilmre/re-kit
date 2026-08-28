---
type: Observation
title: A sixteen-bit address computation that emits thirty-two-bit code
description: In Borland Pascal the sum of a Word and an Integer is a LongInt, because neither type can hold every result. An address expression written from a Word row table and an Integer column therefore compiles to CWD, a register pair, XOR DX,DX and ADC where the original has one ADD -- twelve to twenty bytes per site, in the innermost loop of every blitter. The promotion is silent, the arithmetic is right, and the give-away is a sign-extension instruction inside an address computation.
tags: [pascal, types, code-generation, addressing, reconstruction, performance, measurement]
timestamp: 2026-08-26T00:00:00Z
---

# A sixteen-bit address computation that emits thirty-two-bit code

A row-offset table and a column index, added to reach a pixel. The most natural line anybody writes:

```pascal
Mem[Screen : YOfs[Y] + X] := Colour;
```

The original does it in three instructions:

    add  bx, bx                 ; Y * 2, a word index
    mov  di, [bx + YOfs]        ; DI := Y * 320
    add  di, X                  ; + the column

The rebuild does it in eleven:

    mov  di, Y
    shl  di, 1
    mov  ax, [di + YOfs]
    xor  dx, dx                 ; <-- widen the table entry to 32 bits
    add  ax, cx
    adc  dx, bx                 ; <-- 32-bit add
    mov  di, ax                 ; and throw the top half away again

**`YOfs` is an `array of Word` and `X` is an `Integer`, so `YOfs[Y] + X` is a `LongInt`.** Neither operand type can hold every result of the addition -- a Word reaches 65,535 but not −1, an Integer reaches −32,768 but not 40,000 -- so the language widens to the smallest type that can, and that is the 32-bit one. The arithmetic is correct. The code is three times the size, in the innermost loop of a blitter, and the final `MOV DI, AX` discards the half that forced the widening in the first place.

## The give-away

**A sign-extension or zero-extension instruction inside an address computation.** An address is 16 bits on this machine; nothing about computing one needs `CWD`, `XOR DX,DX`, `CBW`, or an `ADC`. When one appears between the table lookup and the store, a type has been promoted:

| in the emitted code | what it means |
|---|---|
| `XOR DX,DX` after loading the table entry | an unsigned operand widened to 32 bits |
| `CWD` after loading the index | a signed operand widened to 32 bits |
| a `CX:BX` (or any) register PAIR holding one address | the sum is being kept as a LongInt |
| `ADC` in an address | the add is 32-bit |
| `MOV DI, AX` right after | the high half is discarded, so the width bought nothing |

The same tell fires on `Word * Integer`, on comparisons, and on anything fed to `div` -- it is a property of the operand types, not of the expression's shape.

## What to do about it

Three answers, and which one is right is a measurement, not a preference:

1. **Match the types.** If both operands are `Integer`, or both `Word`, the sum stays 16-bit. Declaring the row table `array[..] of Integer` costs nothing (a screen offset fits) and the promotion disappears.
2. **Cast the sum down.** `Mem[S : Integer(YOfs[Y]) + X]` keeps it 16-bit. Uglier, and it only fixes the one site.
3. **The original was assembler.** If the emitted code still differs after the types match -- particularly if the original doubles with `ADD reg,reg` where the compiler emits `SHL reg,1` -- the routine was hand-written and the expression is a transcription, not a spelling. That is the common case for a blitter's inner loop, which is exactly where this expression lives.

**Do not reach for the cast first.** A cast that makes the bytes match can also change what the program computes, and on one target an added `LongInt` cast in a neighbouring expression measured *worse* -- it forced the runtime's 32-bit multiply and replaced three instructions with a far call.

## The version that is not merely bigger but wrong

The same promotion rules produce a genuine defect one step along, and it is worth knowing because every instrument reports it as a size difference:

    ours:      mul  T  /  cwd  /  idiv Denom
    original:  cwd     /  imul T  /  idiv Denom

`MUL` leaves its product in `DX:AX`. The `CWD` that follows **overwrites `DX` with the sign of `AX`**, so the product's high half is destroyed before `IDIV` ever sees it. Any pair of operands whose product exceeds 16 bits divides from a truncated dividend. The original's `CWD` is dead -- `IMUL` overwrites `DX` immediately -- and it is what ships.

Reaching the original's form from Pascal turned out to be impossible: a probe spelling `(X1 - X0) * T div Denom + X0` eight ways -- the addend at either end, the multiply's operands swapped, the difference lifted into its own variable, the quotient cast down, and `LongInt` casts on each of the three operands in turn -- and driving all eight through three compiler releases produced `MUL` in every 16-bit spelling and a runtime call in the two cast ones. **Twenty-four builds, no match.** See [Two bytes the compiler cannot emit](../instruction-the-compiler-never-emits/observation.md): a construct no spelling reaches is not a spelling problem.

## Blind spot

**Matching the types can be wrong about the source.** A row table really might have been `array of Word` in 1994, with the author writing the assembler precisely because the Pascal was slow. Changing the declaration to make one expression compile smaller is a claim about the original's *types*, and it moves every other reference to that table. Measure the whole part, not the span.

**And the promotion is invisible in the source.** Nothing in `YOfs[Y] + X` says "thirty-two bits"; both operands look 16-bit and the declarations are usually in another unit. There is no warning, no lint rule that would not also fire on a hundred correct lines, and the reconstruction reads perfectly.

## Cost

One declaration, or one transcription. Finding it is the work, and the tell above makes that a few seconds once you know to look for a widening instruction where no width is needed.

## Example

Part 005 of a 1994 VGA demo. Three sites: a texture sampler's clip-and-read, and two copies of a dot-interpolation loop's pixel write. The clip-and-read also held both coordinates in registers across four bounds tests with no store, which no Pascal local can do -- so all three were hand assembler, and transcribing them took the part's coverage walk from 99.0% to 99.8%. The remaining three bytes in that part are far-call targets into the runtime, which no edit to a routine can change. [1]

# Citations

[1] `src/P5ROTO.PAS`, `src/P5PATCH.PAS` and `probe/MULSIGN.PAS`, part 005 in the psycho repository; measured with `kit/tools/pascal/spans.py` and `codegen.py` on 26 Aug 2026.
