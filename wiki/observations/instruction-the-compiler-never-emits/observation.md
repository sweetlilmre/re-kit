---
type: Observation
title: Two bytes the compiler cannot emit
description: A probe that tries every plausible spelling of a construct and produces the original's bytes in NONE of them has identified hand-written assembler -- and it does so from compiled-looking code, where the usual tells (string instructions, LOOP, register conventions) are absent. The negative result is the finding, and it is only worth anything if the spellings were exhaustive.
tags: [pascal, turbo-pascal, hand-assembler, identification, probe, codegen, reconstruction]
measured_on: the demo reconstruction and the toolkit itself and a compiler probe, part 003
timestamp: 2026-08-26T00:00:00Z
---

# Two bytes the compiler cannot emit

The tells for hand-written assembler are mostly positive: a string instruction where a single store would do, `LOOP` where the compiler counts in memory, arguments arriving in registers, a direction bit nobody would write by accident. Every one of them is something the code generator does not do, and you find them by recognising a shape.

**This is the same idea run backwards, and it reaches code where none of those tells appear.** Take a sequence that looks entirely ordinary, write a probe that spells the source every plausible way, compile it, and compare. If the original's bytes come out of NONE of the spellings, the compiler did not produce them -- and a routine full of `CALL`s and constant stores, with nothing exotic in it anywhere, has just been identified as assembler.

## The shape of the measurement

    DEC  WORD PTR [Frames]        the original, six bytes
    JNE  loop

    DEC  WORD PTR [Frames]        every build of ours, eleven
    CMP  WORD PTR [Frames],0
    JNE  loop

Five bytes, at four loops in one routine, and everything after each of them out of step. The obvious reading is that the compiler has a peephole for "decrement and test" and ours failed to trigger it, so the job is to find the spelling that does.

Seven spellings were tried, across three compilers -- Turbo Pascal 7, 6.0 and 6.1:

| spelling | what came out |
|---|---|
| `repeat Dec(x) until x = 0` | `DEC` / `CMP` / `JNE` |
| the same with a call in the body | `DEC` / `CMP` / `JNE` |
| `until x <= 0` | `DEC` / `CMP` / `JG` |
| `repeat x := x - 1 until x = 0` | `MOV`/`DEC AX`/`MOV` / `CMP` / `JNE` |
| `x` a `Word` rather than `Integer` | `DEC` / `CMP` / `JNE` |
| `while x <> 0 do Dec(x)` | `CMP` first, `JMP` back |
| `x` a `Byte` | `DEC byte` / `CMP byte` / `JNE` |

**There is no peephole.** Borland re-reads the variable and compares it against zero every time, in every dialect, whatever the type. So the original's six bytes were written by hand, and with them the routine they sit in.

## What it unlocked, which was not the five bytes

The five bytes were the cheap part. What the negative result changed was the reading of everything around them:

    CALL CheckKey
    OR   DX,DX          <-- not AL
    JE   @@1
    JMP  Done
    DEC  WORD PTR [Frames]
    JNE  @@Loop

`OR DX,DX` had been the puzzle for an hour. Turbo Pascal returns a `Boolean` in `AL`, a 16-bit value in `AX`, a `LongInt` or pointer in `DX:AX`; nothing at all comes back in `DX` alone. Once the `DEC`/`JNE` says the tail is hand-written, `DX` stops needing an explanation from the calling convention -- it is the author's own convention, and the routine it calls (which has no stack frame at all, another thing a compiled procedure gets) is an `assembler` function that honours it.

And `JE @@1 / JMP Done` stops looking like a compiler's long-branch expansion. The exit is 367 bytes away, past the reach of a short `JNE`, so a person writing the block by hand has to invert the test and jump over an unconditional jump. That is exactly what is there.

## Why the negative is trustworthy at all

A single failed spelling means nothing -- it is the ordinary state of a reconstruction in progress. What makes this evidence is **the spread**: the type varied, the loop form varied, the statement form varied, the compiler varied, and the answer never moved. A probe whose variants all differ from the original in the SAME way has measured the compiler rather than the guess.

So the discipline is the same as for any probe: make the variants differ along the axis you suspect, and include the one you believe. Here the believed spelling -- `repeat Dec(x) until x = 0` -- was variant one, and its failing is what makes the other six worth reading.

## Caveat: the invert-and-jump-over shape is not by itself a hand tell

The reading of `JE @@1 / JMP Done` above -- a person inverting a test to jump over an unconditional jump, because the real target is out of a short branch's reach -- is sound in that routine, where the `DEC`/`JNE` had already settled that the block was written by hand.

**On its own it convicts nothing.** Another target has that exact shape in code that is demonstrably compiled: a `cmp / jne +2 / jmp +3 / jmp near` guard sitting in front of a 156-byte body whose every remaining byte comes out of an ordinary Pascal `for` loop, in a routine carrying the compiler's own frame and `{$S+}` stack-check call. What produced it there was a `goto` in the source, not a hand -- see [The branch says how big the statement was](../branch-tells-you-the-statement-size/observation.md), which also gives the arithmetic that identifies it.

So the shape says "something other than the compiler's `if` handling emitted this branch". That is two possibilities, not one, and the other tells in this observation are what choose between them.

## Withdrawn conclusion: what a spread of spellings does and does not measure

The section above earns its negative result from **the spread** -- type, loop form, statement form and compiler all varied. A later use of the same technique got that wrong and is worth recording here rather than in an appendix, because the technique is what invites the error.

Sixteen spellings of one `if` statement, across three compilers, all failed to reproduce a guard. That was read as "no source construct emits this", and from it, a difference in the code generator. But sixteen ways of wording one construct vary the *wording* and not the *kind*; they are one experiment repeated, and they cannot reach an answer that lies in a different kind of statement. It did: the source had a `goto`.

The warning sign was there and was read as strength. All sixteen failed **in the same direction**, producing byte-for-byte identical output. A spread that genuinely covers its axis fails in different ways; a spread that fails identically has measured one thing, once.

## Blind spot

**It proves the compiler cannot, not that a person did.** A third possibility is always open: a compiler you have not tried, a switch you have not set, a runtime helper that inlines. The probe should carry the switches of the real build (`{$G+}`, `{$S-}`, `{$R-}` and the rest), because a frame or a range check appearing in the probe and not the original is a difference in the PROBE, not a finding.

**And it says nothing about extent.** Six bytes being hand-written does not make the whole routine hand-written, and reading it that way is a bigger claim than the measurement supports. The routine here begins with a `CALL` and no prologue, which is separate evidence pointing the same way -- but that is a second measurement, not this one.

## Cost

One probe unit, one build per compiler, and a disassembly of the marked region. The variants have to be made self-identifying: each writes a distinct constant to a marker variable immediately before the construct, so the bytes can be paired to the variant without depending on the compiler's emission order. A first attempt paired them by order and mis-attributed two of seven.

## Example

Part 003's morph scene, segment `1139`, in a 1994 VGA demo. Four countdown loops in one routine, each five bytes longer in the reconstruction than in the original, and the reconstruction's coverage walk stuck with three spans in that segment that no edit to the Pascal moved. `probe/DECLOOP.PAS` settled it in one build across three compilers.

The routine had been read as compiled Pascal for the whole of the project's life, on good grounds: its body is constant stores and near calls, it has no string instructions, no `LOOP`, no register-passed arguments, and the reconstruction of it as Pascal already aligned for most of its length. The two tells that were there -- `OR DX,DX` and the absent prologue -- had both been seen and neither had been believed, because each on its own had a plausible innocent reading. [1]

## Citations
[1] `probe/DECLOOP.PAS` and `src/P3MORPH.PAS`, part 003 segment `1139`, in the psycho repository; measured with `kit/tools/pascal/codegen.py` and `kit/tools/pascal/spans.py` on 26 Aug 2026.
