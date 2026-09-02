---
type: Observation
title: Writing a routine is not enough to emit it
description: Borland omits a routine nothing references. A stub that only a published function pointer ever reaches produces no bytes at all until the line that publishes it exists -- and the hole it leaves sits exactly where the routine belongs, which reads as a transcription that has not been done rather than one that has.
tags: [codegen, reconstruction, verification, linking]
measured_on: unrecorded
timestamp: 2026-08-29T00:00:00Z
---

# Writing a routine is not enough to emit it

You transcribe a small routine, rebuild, and the segment is unchanged: the same hole, in the same place, the same size.

**The routine was dropped, and REACHABILITY is what decided it.** Borland emits only what something reaches, and a routine whose sole caller is outside the program -- reached through a pointer the program publishes for a client to call -- is reached by nothing at compile time. The linker is not being clever; it is answering the only question it can.

The hole is exactly where the routine goes, so the measurement after writing it is identical to the one before. **A byte comparison reports the same gap for "not transcribed yet" and "transcribed and discarded"**, and those want opposite responses -- more transcription, or a publishing statement.

## Measured

A seven-byte far entry, `PUSH AX / CALLF Dispatch`, published into a control block for external callers. Written on its own it emitted nothing. The line that brought it into the image was the assignment that publishes it:

    CtrlBlock.DispatchAX := @DispatchEntry;

## What to do

* When a rebuild does not change at all after adding code, check that something reaches it before re-reading the transcription.
* Transcribe the publishing statement and the routine in the same edit. A routine that exists only to be published is not finished until it is published.
* The same applies to a routine reached only from an interrupt vector, a VMT slot the program never calls itself, or a procedural-type variable assigned in a unit that was itself dropped.

## Blind spot

**An unchanged measurement is the evidence for two opposite conclusions**, and this page's whole subject is that the wrong one is more natural. Re-reading a transcription is what a diligent person does next, and it is exactly the wasted move here.

The rule generalises past the linker: any instrument reporting a GAP is reporting an absence, and an absence has no author. It cannot say whether the bytes were never written or were written and then removed by something downstream -- a smart linker, a dead-code pass, a conditional that excluded them. Ask what would have had to REACH the code before asking what is wrong with it.

## See also

* [A typed constant nothing reads is invisible to every comparison that follows an instruction](../dead-data-has-no-witness/observation.md)
