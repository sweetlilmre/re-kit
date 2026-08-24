---
type: Observation
title: A runtime `DEC` before an array subscript names the array's bounds
description: Borland Pascal folds an array's low bound into the addressing displacement when the subscript is a bare variable, and evaluates it at runtime when the subscript is an expression. So whether the original computes `I-1` in a register tells you whether the source wrote `A[I]` into a one-based array or `A[I-1]` into a zero-based one -- a declaration you cannot otherwise see, because both compute the same address.
tags: [pascal, codegen, turbo-pascal, source-shape, arrays, addressing, reconstruction]
timestamp: 2026-08-24T00:00:00Z
---

# A runtime `DEC` before an array subscript names the array's bounds

Two Pascal sources that read the same element:

    Vert : array[1..75, 1..3] of Integer;   ...   Vert[I, 1]
    Vert : array[0..74, 0..2] of Integer;   ...   Vert[I - 1, 0]

Same storage, same bytes on disk, same element for the same `I`. They do not compile to the same instructions, and the difference is visible in four bytes at the top of every access.

**The bare variable is folded.** `A[I, 1]` on a one-based array is `base + (I-1)*6`, and the compiler rewrites it as `(base - 6) + I*6`: it scales the variable and moves the whole low-bound adjustment into the constant displacement, which costs nothing because the displacement was going to be there anyway.

    MOV DI,[BP-2]  /  SHL DI,1  /  MOV SI,DI  /  SHL DI,1  /  ADD DI,SI
    MOV AX,[DI-4]

**The expression is not.** `A[I - 1, 0]` on a zero-based array has a low bound of zero -- nothing left to fold -- and a subscript the compiler must actually evaluate. So the `-1` appears as an instruction and the array's own offset stays in the displacement:

    MOV AX,[BP-2]  /  DEC AX  /  MOV SI,AX  /  SHL AX,1  /  ADD AX,SI
    MOV DI,AX  /  SHL DI,1  /  MOV AX,[DI+4]

The two sequences are the same length. What separates them is that one begins by *adjusting* and the other begins by *scaling*, and that the displacement is the array's true offset in one case and the array's offset minus a stride in the other.

## What it is worth

**It reads a declaration that leaves no other trace.** Array bounds are not in the binary. The data is the same bytes either way, the loop is `for I := 1 to Count` either way, and the element fetched is the same. Nothing in the values, the loop or the stores distinguishes them. The addressing preamble is the only witness.

**And it is cheap and unambiguous.** One instruction, at a fixed place, present on every single access. A loop body that reads three components gives three independent readings of the same fact.

## Reading it

| what the original does first | what the source declared |
|---|---|
| scales the subscript variable, displacement is offset minus a stride | one-based array, bare variable subscript |
| `DEC`/`INC`/`ADD` on the subscript, displacement is the array's own offset | bounds shifted from the index, expression subscript |

The second column's displacement is checkable independently: it should equal the array's address, which a data-segment map or a decompiler will give you. If the displacement matches the symbol exactly, the low bound was not folded.

**A constant second subscript is added before the element scale, one `INC` at a time.** `((I-1)*3 + 2)*2` appears as `ADD AX,SI` then `INC AX` twice rather than `ADD AX,2`, because two one-byte instructions are shorter than one three-byte one. Do not read the repeated `INC` as a loop; it is a constant column index, and counting the `INC`s gives you the column.

## Why it works

The fold is a constant-propagation the code generator performs while building the address expression, and it can only run when every term but one is constant. A bare variable subscript leaves the low bound as the only non-constant-adjacent term, so it merges into the displacement. An explicit `I - 1` puts a subtraction in the expression tree before the code generator gets there, and the tree is evaluated as written.

## Blind spot

**It says the bounds were shifted, not by how much or in which direction.** `A[I - 1]` on `array[0..N]` and `A[I + 1]` on `array[2..N]` both leave an adjustment in a register. Read the *sense* of the instruction -- `DEC` against `INC` -- and the displacement against the array's real address, and only then claim a bound.

**It is silent on one-element and constant subscripts.** `A[3]` is entirely constant and folds to a plain displacement no matter how the array is declared, so a routine that only ever indexes constants tells you nothing.

**Do not reach for the compiler version.** The fold is not a version behaviour: the same divergence appears under Turbo Pascal 6, 6.1 and 7.01 on the same source, so a build with an older compiler will not make it go away and is not evidence about which compiler shipped the binary.

**And nesting the declaration is not the same lever.** `array[1..N, 1..3]` and `array[1..N] of array[1..3]` compile identically -- tested both before and after the fold was removed -- so a two-step versus one-step scale is not read as a nested declaration.

## Cost

Reading the four to six instructions before each array access. No arithmetic beyond comparing one displacement against one known address.

## Example

A 1994 VGA demo's object loader fills four polygon meshes from tables of vertices. The reconstruction declared them `array[1..N, 1..3] of Integer` and read `Vert[I, 1]`, which is the obvious transcription and produced a correct picture. The original's decompilation computed every component as `((I-1)*3 + (J-1))*2 + base`, with the `-1` in a register and the table's own offset in the displacement.

The gap showed in the coverage walk as five eleven-byte and four nine-byte unaligned runs at regular spacing -- **one difference repeated per object and per component, not nine separate problems**, which the regular spacing said before anything was disassembled.

Two hypotheses were tested and refuted first, and both are worth recording because each cost a build. **The compiler version**: rebuilding with Turbo Pascal 6 and 6.1 left those runs byte-for-byte identical, eliminating the whole family. **The unit boundary**: moving the tables into another unit, on the theory that a link-time fixup could not be folded, changed nothing at all.

Declaring the tables `array[0..N-1, 0..2]` and reading `Vert[I - 1, 0]` moved the part from 98.9% to 99.1% and shrank every one of those runs. [1]

# Citations

[1] `src/gen/P2OBJ.INC`, `src/P2S2.PAS` and `spans.toml`, part 002 segment `108b`, in the psycho repository; the original's shape read from Ghidra's decompilation of `108b:1cf2`, measured with `kit/tools/pascal/spans.py` on 24 Aug 2026.
