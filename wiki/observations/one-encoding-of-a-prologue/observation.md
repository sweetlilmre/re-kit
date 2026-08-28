---
type: Observation
title: A locator keyed on one spelling of a prologue reads working code as absent
description: An instrument that finds compiled code by scanning for a frame prologue must list every encoding the compiler may pick. Missing one gave two answers, both wrong and neither an error - no code at all under one release, and code silently starting at the second routine under another.
tags: [instruments, blind-spot, encoding, turbo-pascal, disassembly, measurement, verification]
timestamp: 2026-08-28T00:00:00Z
---

# A locator keyed on one spelling of a prologue reads working code as absent

An instrument needs to find where compiled code begins inside a container it has decided not to parse -- a `.TPU`, a `.OBJ`, an image with a header of a version you would rather not encode. The cheap and often correct answer is to scan for the first routine's frame prologue and take everything from there. It avoids a format that changes between releases, which is frequently the very thing being compared.

**The scan is only as good as its list of encodings, and a missing one does not look like a failure.** It has two shapes, and the second is worse:

* **Nothing is found.** The instrument returns an empty extraction. Downstream, empty compares equal to empty, so two units that were never measured are reported as agreeing.
* **Something later is found.** The scan matches a prologue further in and the extraction silently begins at the *second* routine, dropping the first. Every byte it returns is real, the length is plausible, and the routine that was dropped is often the one the measurement was set up to look at.

Neither raises anything. Both produce a number a reader will use.

## Why it works

An x86 frame prologue has more than one legal spelling, and which one a compiler picks is a code-generation decision, not a language one:

* `ENTER nn, 0` -- one instruction, 286 and later;
* `PUSH BP` / `MOV BP, SP` / `SUB SP, nn` -- the classic three;
* and `MOV BP, SP` itself has **two encodings**, `8B EC` in the load direction and `89 E5` in the store direction, for the same instruction.

So a table listing `ENTER` and `55 8B EC` is complete right up until a release prefers `55 89 E5`, and then it finds nothing at all. The direction bit is the same axis that separates hand-written assembler from compiled output -- see [The direction bit tells hand assembler from compiled Pascal](../direction-bit-names-basm/observation.md) -- which is worth noticing here: an instrument whose author knew that a compiler picks a direction still keyed the locator on one of them.

The truncating shape has a different cause: an ordered scan returns the *first* match, so as soon as the list is incomplete the answer becomes "the first routine whose prologue I happen to recognise", which is not the same question.

## Blind spot

**A per-release table will be incomplete again.** The fix is to list the encodings, and the next release, switch or `{$G}` state can add another. What makes it survivable is refusing on no-match rather than returning empty, so the next gap arrives as a stop instead of as a zero.

**Refusing on no-match does not catch truncation**, because there is a match. The cheap guard is to compare the located offset against what the compiler itself reported -- a TPC listing prints `NNN bytes code` -- and object when the extraction is shorter. Two independent numbers for the same quantity is the general form of this.

**A frameless routine has no prologue and never will**, so a container full of them is genuinely unlocatable this way. That is a limit to state, not to paper over: an instrument that guesses an offset when it cannot find one is worse than one that says so.

## Cost

One byte string added to a table. Finding out that it was missing cost a measured comparison of the same source under four compilers.

## Example

A 16-bit Pascal probe driver, 28 Aug 2026. It compiles a single-question unit with every installed compiler and diffs the code, locating the code by `ENTER nn,0` or `55 8B EC`.

Three of one project's seven probes reported **no code at all** under both Turbo Pascal 7 releases and full code under both 6.x releases, from identical source -- TP7 spells the prologue `55 89 E5 83 EC 04` where 6.0 emits `ENTER`. The driver printed the miss as `code found at +0000`, because the report formatted `at or 0` and `None or 0` is zero, and then reported one empty extraction against another as `IDENTICAL CODE`.

A fourth probe was worse off, and it was the one four resolved investigations cited. Under 6.x its extraction began at the first `ENTER` -- which was the **second** routine, 145 bytes in. The dropped routine was the one containing the `SUB` / `MUL` / `CWD` / `IDIV` sequence the probe existed to settle.

With the store-direction prologue added, all seven probes measure under all four compilers, and the checked matrix is the instrument that says so.
