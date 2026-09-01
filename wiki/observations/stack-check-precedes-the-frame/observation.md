---
type: Observation
title: Stack checking is on by default, and it puts seven bytes in front of every framed routine
description: TP7 defaults stack checking ON, so every framed procedure -- an `assembler` one included -- opens with a seven-byte XOR AX,AX / CALLF that the original does not have. The build does not fail; every hand-transcribed routine simply differs in its opening bytes, which reads as dozens of bad transcriptions rather than one missing switch. The signature is recognisable, it is per unit, and a switch line is the one input whose absence produces a build that measures wrong instead of a build that breaks.
tags: [turbo-pascal, codegen, verification, reconstruction, switches]
measured_on: a Borland Pascal 7 reconstruction, whole corpus
timestamp: 2026-09-01T00:00:00Z
---

# Stack checking is on by default, and it puts seven bytes in front of every framed routine

Every routine you have transcribed differs from the original in its first few bytes. The bodies look right. The lengths are close. The prologue is wrong everywhere, in the same way, including in routines you wrote as `assembler` and copied instruction by instruction.

**Check the stack-checking switch before re-reading a single routine.** Turbo Pascal 7 defaults `$S` to ON, and with it on the compiler emits a call to the stack-check helper in front of the frame:

    XOR AX,AX
    CALLF <stack check>

Seven bytes, ahead of everything, on every framed procedure in the unit. The original was built with it off, so the original does not have them.

## Why it works

The switch is not a code-generation preference that shows up in some routines and not others -- it is a per-unit setting that applies to every framed routine the unit contains. That makes it the cheapest possible diagnosis and the most expensive possible thing to miss:

- **Cheap**, because one measurement covers the whole unit. If every framed routine is long by the same small constant at the front, you are looking at one switch, not at N transcriptions.
- **Expensive**, because the failure is uniform. Dozens of routines differing identically reads as a systematic misunderstanding of how the author wrote assembler, which sends the work into the routines instead of into the build.

**The `assembler` case is the one that misleads.** A routine written as `assembler` and transcribed verbatim still gets the framing the switch asks for, so the one class of routine you have the most confidence in is also wrong -- and being wrong about a verbatim copy is exactly the evidence that would make you doubt the copy.

## Blind spot

**This says nothing about which units should have it off.** The original's own units may differ, and the switch is per unit, so a corpus-wide answer is a guess. What the signature gives you is the presence or absence of the helper call, unit by unit; matching the original's choice still means reading each unit's prologues.

**A missing switch and a present one look identical in every check that is not byte-level.** The program compiles, links, runs and behaves correctly with stack checking on -- it is a debugging aid, not a semantic change -- so no behavioural instrument, no watched run and no test can see it. Only a byte comparison against the original can, which means a reconstruction pursuing behavioural fidelity alone will carry this to the end without a signal.

**The general form is the dangerous part.** A switch line is an input like any other, and **a wrong one does not fail -- it produces a build that measures wrong.** Nothing in a compiler's output says "you asked for the wrong dialect of me". Every other kind of bad input in a build gets an error; this kind gets a number.

## Cost

Reading one routine's opening bytes on each side, once per unit. No disassembler beyond that, and no rebuild: the helper call is recognisable by eye.

**Getting the switch to the compiler is its own trap, and worth knowing before you go looking for a code defect.** A `TPC.CFG` in the CURRENT directory **replaces** the one beside the compiler rather than adding to it. So a build that stages sources into a working directory and puts a config there has silently discarded every switch the installed config supplied, including this one -- and the symptom is identical to never having set it: a clean build whose prologues are all wrong. Check which config the compiler actually read before concluding anything about a switch.

## Example

A Borland Pascal 7 reconstruction of a real-mode DOS program, whose build harness documents the switch specifically because of this. With `$S` left at its default, **every hand-transcribed routine in the corpus differed from the binary in its opening bytes** -- and the harness's own note records the reason as the thing a merged build script is most likely to get wrong, since a switch line is copied rather than derived.

The same reading generalises to every switch with a visible signature and is always per unit: `$N` in whether floating point is 80x87 instructions or runtime calls, `$G` in whether there is an `ENTER` at all, `$A` in whether a frame carries alignment padding, and `$S` here.

## Citations

- The build harness's switch line, and the note above it explaining why `/$S-` is not optional.
- [The frame is bigger than your locals account for](../frame-size-counts-locals/observation.md) -- the same instruction read for a different switch, and where the per-unit rule is stated. That page names `$S` as *whether a stack check precedes the frame* without carrying the default or the signature, which is why this one exists.
- [An odd local offset means data alignment was off](../alignment-switch-pads-the-frame/observation.md) -- a third switch with a frame signature.
