---
type: Observation
title: The branch says how big the statement was, and that names it
description: A conditional jump's displacement is the SIZE of the statement it jumps over, and size is a much tighter constraint on the source than shape is. A two-byte then-part is a short jump, and in Turbo Pascal only `goto` compiles to one -- which identified a statement after twenty-nine spellings of the wrong kind had failed to.
tags: [pascal, turbo-pascal, codegen, probe, reconstruction, identification]
measured_on: a 1993 demo reconstruction, its program segment, and two compiler probes
timestamp: 2026-09-04T00:00:00Z
---

# The branch says how big the statement was, and that names it

A reconstruction was two bytes short in one routine. The original guarded a 156-byte body like this, and every build of ours emitted five bytes where it has seven:

```
    80 3e 22 03 01   cmp byte ptr [Flag], 1
    75 02            jne  +2      -> onto the near jmp
    eb 03            jmp  +3      -> over it, into the body
    e9 9a 00         jmp  near epilogue

    80 3e 22 03 01   cmp                        ours
    74 03            je   +3
    e9 9a 00         jmp  near epilogue
```

The hunt that followed was for a **shape**: what spelling of `if Flag = 1 then` emits the long form. Twenty-nine were tried across three compilers -- `case`, `while`, `repeat`, a dangling `else`, the condition through a Boolean variable, `and`, `or`, inline assembler jumping to a Pascal label, labels with and without a `goto`. None of them did.

**The answer was in the displacement, and it had been on the screen the whole time.** `jne +2` jumps over exactly two bytes. Those two bytes are the `eb 03`. So the then-part of that `if` compiled to a **two-byte short jump** -- and in Turbo Pascal exactly one statement does that, a `goto` to a label a few bytes ahead. Everything else is longer, or does not begin with `EB`. The source was

```pascal
    if Flag = 1 then goto DoIt;
    Exit;
DoIt:
    { the body }
```

which emits those seven bytes, and with them the build went byte-identical to the original.

## The rule

**Read the displacement before guessing at spellings.** In Borland's 16-bit output a forward conditional jump whose target is the statement after the then-part gives you that statement's size in one byte, and size discriminates far harder than shape:

| the then-part measures | it can only be |
|---:|---|
| 2 bytes | a short jump -- `goto` to a nearby label |
| 3 bytes | a near jump -- `Exit`, or `goto` to a far label |
| 5+ bytes | an assignment, a call, a compound statement |

A guess that does not fit the size is not worth compiling. Twenty-nine of the thirty spellings tried above fail on that arithmetic alone.

## The other half: the compiler folds, so an unfolded branch is a statement

Turbo Pascal 6.0 and 7.0 compile `if C then <big body>` by **inverting** the test: `je +3 / jmp near`. A probe swept a plain `if` across twenty-four body lengths, over and under the short-jump boundary -- below it a short `jne`, above it the folded pair, and the long form never once. A label at the head of the body does not change it either.

So a branch that keeps the **source polarity** and reaches its body by a jump was not written by the compiler's `if` handling at all. In the binary above the long form occurs once in 10,704 bytes against nine folded ones -- and one of the nine sits six lines below it, on the same routine's `for` loop. The compiler was folding right there. That contrast is the tell: **a lone unfolded branch in an otherwise folded image is a jump statement in the source.**

## The blind spot

**Size bounds the statement; it does not name it.** Two spellings here compile to the same bytes -- `goto Done` with the label at the routine's end, and a bare `Exit`, because both are one near jump to the same epilogue. No measurement separates them, and the reconstruction chose between them on the author's testimony, which is a different kind of evidence and was recorded as such. A label's name never reaches the code either.

The rule also assumes the then-part is contiguous and immediately follows the branch. That holds for Borland's straight-line output; a compiler that hoists or reorders blocks would break the arithmetic without saying so.

## Withdrawn conclusion: sixteen spellings of one construct are one experiment

Before the displacement was read, this project concluded from sixteen failed spellings that **the difference was in the code generator** -- and hypothesised a compiler patch level nobody had, which explains everything and can be checked by nobody. Three compilers agreeing made that feel strong.

It was weak, and in a way worth naming. Sixteen ways of writing an `if` are not sixteen experiments; they are one experiment repeated, because they vary the *wording* of a construct and not its *kind*. A probe earns a negative result only by varying the axis the answer might lie on, and the axis here was "is there a jump statement in the source", which no rewording of an `if` can reach.

The tell that it was one experiment was visible at the time: every one of the sixteen failed **in the same direction**, all producing the identical five bytes. Variants that all differ from the original the same way have measured one thing once.
