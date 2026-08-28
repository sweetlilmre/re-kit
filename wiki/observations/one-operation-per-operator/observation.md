---
type: Observation
title: Borland Pascal emits one instruction per operator, so `+ 3 + 5` is not `+ 8`
description: The compiler walks an expression tree and codes each operator as it goes; it does not fold two adjacent integer constants first. So `X + 3 + 5` is ADD AX,3 / ADD AX,5, `X + 3 + 1 + 1` ends in two INC AX, and `Y - 9 - 0` really does emit SUB AX,0. Transcribing the arithmetic instead of the operators produces the right numbers and the wrong bytes.
tags: [pascal, turbo-pascal, borland, codegen, transcription, expressions]
timestamp: 2026-08-25T00:00:00Z
---

# Borland Pascal emits one instruction per operator, so `+ 3 + 5` is not `+ 8`

You are transcribing a routine that draws with computed coordinates. The binary says

    MOV  AX, [DI+2fc]     ; a record field
    ADD  AX, 3
    ADD  AX, 5
    PUSH AX

and you write `Rec.X + 8`, because it is. The build comes back with `ADD AX,8`, three bytes where the original has six, and every byte after it shifts.

**The compiler does not fold adjacent constants.** It walks the expression tree and codes each operator in turn, so the source wrote `+ 3 + 5` and got two additions. The parenthesisation and the associativity are not stylistic -- they are in the instruction stream, one operator at a time.

## What each shape looks like

| the source wrote | the compiler emitted |
|---|---|
| `X + 8` | `ADD AX, 8` |
| `X + 3 + 5` | `ADD AX, 3` / `ADD AX, 5` |
| `X + 3 + 1 + 1` | `ADD AX, 3` / `INC AX` / `INC AX` |
| `X + 5` | `ADD AX, 5` |
| `X - 3 - 2` | `SUB AX, 3` / `DEC AX` / `DEC AX` |
| `Y - 9 - 0` | `SUB AX, 9` / `SUB AX, 0` |
| `Y - 0` | `SUB AX, 0` |

Two sub-rules fall out of the table and both are load-bearing:

**A constant of 1 or 2 becomes INC or DEC rather than ADD.** `INC AX` is one byte and `ADD AX,1` is three, so the compiler takes the shorter form -- and for 2 it takes it twice. That is why `+ 3 + 1 + 1` and `+ 3 + 2` are the SAME five bytes and cannot be told apart, while `+ 5` is different from both.

**`- 0` is not optimised away.** A subtraction of zero still costs `SUB AX,0`, three bytes that do nothing. It is the strongest tell in the table, because nobody writes `- 0` by accident: seeing it means the source really has a constant that happens to be zero, which in practice means a hand-unrolled sequence where one line's offset is the base case.

## Why it matters

**It is not a peephole difference; it changes lengths.** A folded constant is shorter than the operators that produced it, so every instruction after the expression moves, and a comparison walk resynchronises somewhere later and reports a span far bigger than the expression.

**It reads a hand-unrolled loop back out of the binary.** A run of calls whose arguments step `+ 3 + 1`, `+ 3 + 1 + 1`, `+ 3 + 3`, `+ 3 + 4`, `+ 3 + 5` against a matching `- 9 - 1`, `- 9 - 0`, `- 9 + 1`, `- 9 + 1 + 1`, `- 9 + 3` is not five unrelated expressions. It is one shape written out by hand with a base and a per-line offset, and the base is `+ 3` and `- 9` because those are the operators that survived.

## Blind spot

**A byte-diff walk that forgives short runs hides this until it does not.** A tolerance rule that skips one or two differing bytes as a displacement will swallow `ADD AX,8` against `ADD AX,3` and then fail on the extra instruction, so the reported span starts in the wrong place -- at the next mismatch rather than at the expression. Look upstream of a span's start for arithmetic before assuming the span names the defect.

**The frame says nothing about this.** A folded constant and an unfolded one have identical frames, so a prologue comparison passes and the routine still differs. This is the class of defect that survives every frame check.

## Cost

Reading the arithmetic instruction by instruction rather than evaluating it. No build needed to see it; one build to confirm.

## Example

`NEUROSIS.004` segment `1005`, the diagonal digger at `0df5`. Nine drawing calls, every one of them with folded constants in the reconstruction and every one of them differing. Rewriting the nine as the original's operators -- and nothing else in the routine -- took the part's coverage walk from 70.4% to 75.6%, 529 bytes. `1005:0EAE` is the `SUB AX,9` / `SUB AX,0` pair and `1005:0ED2` the `ADD AX,3` / `ADD AX,3`. The same rule fixed the walker's column bounds at `1005:15B8` in the same part. [1]

# Citations

[1] `src/P4LEMS.PAS`, `Digger` and `Walker` and the notes in them, in the psycho repository.
