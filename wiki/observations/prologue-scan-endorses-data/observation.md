---
type: Observation
title: A prologue scan finds every routine, and one thing that is not a routine
description: Scanning for ENTER or PUSH BP recovers a segment's routines with no misses, but data matches too -- and the dangerous part is not the false candidate, it is the SECOND measurement that then agrees with it. Only a call reference proves a candidate; withhold everything else you would say about one.
tags: [pascal, turbo-pascal, disassembly, verification, blind-spot, instruments]
timestamp: 2026-08-24T00:00:00Z
---

# A prologue scan finds every routine, and one thing that is not a routine

You want a segment's routines and you have no function database. Scanning for the prologue is the obvious move, and it works better than it deserves to: on one 14KB Borland Pascal segment, scanning for `ENTER n,0` and `PUSH BP / MOV BP,SP` found **22 of the 22 functions Ghidra had identified, with no misses at all**.

It also found a twenty-third, and there was nothing there. `00 C8 8E 00 00` inside a table of word offsets reads as `ENTER $8e,0` — a plausible frame at a plausible address, in the middle of data.

## The dangerous part is the second measurement, not the first

A false candidate on its own is cheap; you look at it and it is data. What is not cheap is what the tool did next. It took the candidate's "body", searched the rebuild for those bytes, found sixty-four of them, read a prologue behind them, and printed **`ours: same`**.

**A confident agreement about a routine that does not exist.** Both builds contain similar tables, so the search succeeded exactly as designed. Nothing in that pipeline was broken; the comparison was simply asked a question that presumed its own answer.

That is the same failure as a drifted second copy of a measurement: the tool did not go quiet, it *manufactured a finding*, and the manufactured one looked like the good rows around it.

## What actually discriminates

Only a reference. A candidate that a `CALL` in the same segment targets is a routine; nothing else in the local bytes settles it. Measured against the ground truth on that segment:

| candidate class | count | real |
|---|---|---|
| targeted by a `CALL` | 18 | **18** |
| no call found | 5 | 4 |

So `called` was perfectly precise, and every bit of the noise sat in the other bucket. Note the other bucket is *mostly right*: four of its five were real routines reached through an export, a procedure variable or a VMT. **Unproven does not mean false, which is why the answer is not to drop those rows.**

Things that look like discriminators and are not, all tried on that segment: the preceding byte (real routines follow `RET`, `RETF`, padding and ordinary code alike, and so did the false one); whether the next 32 bytes decode cleanly (they did for the data, and did *not* for several real routines, because a fixed window cuts an instruction in half at its end).

## The rule

**Report the candidate, and withhold every further measurement about it.** A scan may say "there may be a routine here". It may not say what the rebuild does about it, how big its frame is relative to ours, or whether it matches — because each of those silently asserts the routine exists. One line of unproven candidate costs a reader nothing; one line of unproven candidate wearing a comparison costs them the afternoon.

## Blind spot

**A routine with no frame at all is invisible to this**, so absence of a candidate is not absence of a routine. `$G-` routines with no locals, `assembler` procedures that set up no frame, and anything entered by a jump have no prologue to find. This is a way to enumerate *framed* routines cheaply; it is not a function lister, and where one exists — a real disassembler's recursive descent from entry points — that is the stricter instrument and it wins.

## Cost

One regex pass per segment, plus a second for the call targets. No disassembler needed for the scan itself.

## Example

`kit/tools/pascal/prologue.py`, on part 002 segment `108b` of a 1994 Borland Pascal demo, 24 Aug 2026. 23 candidates; 22 matched Ghidra's function list exactly; the twenty-third, `108b:2edf`, was a word-offset table. The `ours:` column endorsed it before the tool was corrected to withhold on unproven rows.

The same run's other half checked out completely: the per-routine slot map for `108b:00bf` agrees with Ghidra's stack-variable list slot for slot, once Ghidra's two-byte offset convention is accounted for, **including the two blocks of frame the routine never reads** — which is the finding the technique exists to produce. So the enumeration is trustworthy and the *identification* is not, and it is worth knowing which half of an instrument you are leaning on. [1]

# Citations

[1] `kit/tools/pascal/prologue.py` and its correction; verified against Ghidra's function list and `get_function_variables` for `NEUROSIS_002.exe` in the psycho repository.
