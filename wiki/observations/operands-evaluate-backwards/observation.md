---
type: Observation
title: The operand it evaluates first is the one written second
description: Borland Pascal evaluates the two operands of a binary operator RIGHT TO LEFT when both need the accumulator -- the right one is computed first and parked in a spare register, then the left. So the register holding the parked value names the operand written SECOND, and a reconstruction with the terms the natural way round differs by four bytes at every such expression.
tags: [pascal, turbo-pascal, codegen, source-shape, expressions, reconstruction]
timestamp: 2026-08-26T00:00:00Z
---

# The operand it evaluates first is the one written second

A subscript in your reconstruction reads `(Y + 20) * Width + (X + 20)`, which is the natural way to write a row-major index and, as far as the program is concerned, correct. The original computes the same value in the same instructions -- and puts them in the other order:

    the original          ours
    MOV AX,[Y]            MOV AX,[X]
    ADD AX,20             ADD AX,20
    IMUL AX,AX,40         MOV DX,AX
    MOV DX,AX             MOV AX,[Y]
    MOV AX,[X]            ADD AX,20
    ADD AX,20             IMUL AX,AX,40
    ADD AX,DX             ADD AX,DX

Same seven instructions, same arithmetic, four bytes apart in where they sit -- and every instruction after them out of step.

**Borland evaluates the RIGHT operand first.** With both operands needing the accumulator, it computes one, moves it to `DX`, computes the other into `AX`, and adds. The one that goes to `DX` is evaluated first, and that one is the operand written **second** in the source.

## The reading rule

**Whatever ends up in the spare register is the SECOND term of the source expression.** In the original above, `DX` receives `(Y + 20) * Width`, so `(Y + 20) * Width` is written second and the source is

    (X + 20) + (Y + 20) * Width

which is not how anyone writes a row-major subscript, and is what the bytes say. The reconstruction had it the natural way round.

**It is worth stating as a rule because the intuition points the other way.** "Evaluated first" reads as "written first", and inverting that by hand every time is exactly the sort of step that gets skipped.

## When it applies, and when there is nothing to read

The reordering only happens when **both** operands need the accumulator. If the right operand is a simple memory load or a constant, the compiler leaves it in place and adds directly:

    MOV AX,[A]      ADD AX,[B]        -- A + B, no reordering, nothing to read
    MOV AX,[A]      ADD AX,30         -- A + 30, likewise

So the rule bites on expressions of the shape *compound* + *compound*, which is where subscripts and address arithmetic live. A chain like `A * k + B + c` associates left, so the `+ c` folds away and only the first `+` reorders.

## Why it is worth the trouble

Because it is **cheap to check and repeats**. One `MOV DX,AX` in the disassembly settles the order of one expression, and a routine that builds indices does the same thing at every store. In one reconstruction a single routine held sixteen such expressions -- four quadrants of a lens table, index and value each -- and rewriting all sixteen with the terms swapped closed 163 bytes and moved a part's coverage 0.7% in one build.

## Blind spot

**It says nothing about which order is correct** -- both compute the same number. This is a source-SHAPE finding, useful only where matching the original's bytes matters, and it makes the source read slightly wrong to a human. Say so in a comment or the next reader will tidy it back.

**And a differing operand order is not always this.** A register difference can equally come from a type difference: an array declared flat instead of two-dimensional builds its index differently and in a different register, and that IS a semantic difference in the declaration. Check the ADDRESSING as well as the register -- a folded displacement against a run-time addition is a type difference, not an evaluation-order one. See [A folded subscript names its bounds](../subscript-fold-names-the-bounds/observation.md).

## Cost

Reading one `MOV` per expression. The fix is textual.

## Example

A lens-table builder at `1012:0008` in a 1994 VGA demo. Sixteen index and value expressions of the form `(row + 20) * 40 + (col + 20)`, all written the natural way round, all four bytes displaced from the original, and five separate fifteen-byte spans in the coverage walk to show for it -- one per quadrant plus the identity case. `1012:0043` puts `(Y + 20) * 40` into `DX`, which names it the second term; rewritten as `(X + 20) + (Y + 20) * BounceW` throughout, the routine aligned and the part went 96.2% to 96.9%. [1]

# Citations

[1] `src/P1S1.PAS`, part 001 segment `1012`, in the psycho repository; measured with `kit/tools/pascal/spans.py` on 26 Aug 2026.
