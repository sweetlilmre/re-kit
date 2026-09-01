---
type: Observation
title: The original contains code that does nothing, and you have to put it back
description: Real programs carry statements with no effect -- a loop of self-assignments, a test whose branches are identical, an addition of zero. A reconstruction will never invent them, and leaving them out is a hole of exactly their size that no amount of re-reading the source will find. They are only ever found by reading the original's bytes and refusing to explain away what is there.
tags: [reconstruction, decompilation, verification, dead-code, source-shape, measurement]
timestamp: 2026-08-26T00:00:00Z
---

# The original contains code that does nothing, and you have to put it back

Your reconstruction of a routine is short by eighty bytes. The statements you have all match, the constants are right, the frame is right, and there is no obvious place for eighty more bytes to go. You read your source again. It looks correct, because it is correct -- as a program. What it is not is the same program.

**The original has a loop in it that does nothing at all**, and you will not find it by looking at your own code, because there is nothing there to look at. The absence has no shape.

## What they look like

Three from one corpus in one day:

    for I := 1 to 49 do
    begin
      if ProfileA[I] <> 0 then ProfileA[I] := ProfileA[I];
      if ProfileB[I] <> 0 then ProfileB[I] := ProfileB[I];
    end;

Forty-nine iterations of two conditional self-assignments. Eighty-three bytes.

    Bias := 0;
    if LensTab[I] <> I   then Bias := 0;      { it is already zero }
    if LensTab[I] = 1640 then Bias := Bias + 0;
    Cell[I] := Source[LensTab[I]] + Bias;     { and so this adds nothing }

Two dead tests inside a live loop, sixteen hundred times over.

    Seek(F, DataOfs);
    ...
    Unread : file;                            { declared, never opened }

Storage reserved and abandoned -- eight separate instances in one target, from two unreferenced bytes to five hundred and twelve.

None of these is a decompiler artefact. They are what the author wrote: a check that was meaningful before a rewrite, a bias that was tuned to zero and left in, a second file handle that a loader stopped needing. **Software accumulates this. A reconstruction, written cleanly from an understanding of what the routine does, cannot.**

## Why the usual instruments cannot find them

A per-routine byte check reports the routine as differing and says nothing about why. A coverage walk reports an unaligned span, which tells you *where* but is equally consistent with a dozen other causes. A frame check finds the unreferenced *declarations* -- that half is easy, because the `ENTER` operand counts them -- but a dead *statement* is invisible to every declaration-driven tool, because it declares nothing.

So the only instrument that finds them is the disassembly, read with a particular discipline: **when an instruction sequence appears to do nothing, do not assume you have misread it.** The reflex is to look for the meaning -- surely the store is to a different address, surely the compare has a side effect. Check, and then believe the bytes. Two identical `MOV AL,[BP-7]` loads either side of a compare are two identical loads.

## The reading rule

Read the operands, not the intent:

- **A store and a load of the same address, in the same iteration, with nothing between them** is a self-assignment, whatever the surrounding code implies it ought to be.
- **A conditional whose taken branch reproduces the state the fall-through already has** is dead. Zeroing a byte that was zeroed at the top of the same loop body is the common shape.
- **An arithmetic instruction with an identity operand** -- `ADD reg,0`, `IMUL reg,1` -- was a variable once. The compiler folds a constant expression, so a zero that survives into the instruction stream came from a source that named it.

And once found, transcribe it **verbatim, with a comment saying it does nothing and why you are sure**. The next reader will otherwise delete it as a mistake, and it will cost the same eighty bytes a second time.

## Blind spot

**It cuts the other way too, and that is the expensive direction.** Code that does nothing in the ORIGINAL must go in; code that does nothing in your reconstruction and not in the original must come out, and the same reflex protects both. A reconstruction that has accumulated its own dead statements is the more likely case early on, when routines are rewritten repeatedly.

**Dead code is not the only explanation for a shortfall**, and reaching for it first is how a reconstruction acquires padding. Check the frame, the declarations and the statement shapes before concluding that eighty bytes of the original do nothing -- the alternatives are far commoner, and a wrong dead-code claim is unfalsifiable in a way a wrong declaration is not.

**And it says nothing about behaviour**, which is the point: putting these back moves a coverage measurement and changes what runs not at all. On a target where the goal is behavioural fidelity, that makes them worth exactly the bytes and no more -- valuable for the measurement, not for the program.

## Cost

Reading the disassembly of the span, which is being done anyway. The transcription is a few lines.

## Example

Part 001 of a 1994 VGA demo, in the same session: eighty-three bytes in a loader and two dead tests in a lens gather, found within an hour of each other, in units that had been read a dozen times. The loader's span had been the largest in its segment for weeks. Neither routine's reconstruction was *wrong* about what the code achieves; both were missing what the code contains. Putting them back moved the part's coverage walk 93.0% to 95.1% together with three other findings, and changed the running program not at all. [1]

## Citations
[1] `src/P1BALLS.PAS` and `src/P1LOGO.PAS`, part 001 segments `1107` and `1012`, in the psycho repository; measured with `kit/tools/pascal/spans.py` on 26 Aug 2026.
