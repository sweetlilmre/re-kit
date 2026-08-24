---
type: Observation
title: An odd local offset means data alignment was off
description: Borland Pascal's $A switch decides whether a variable starts on a word boundary. It leaves a signature nothing else does -- a local at an ODD offset from BP -- and reading it costs one glance at a prologue. A reconstruction compiled with the default when the original was not gains a pad byte per odd-sized variable, which shifts every local below it and looks like a missing declaration.
tags: [pascal, codegen, turbo-pascal, switches, locals, alignment, reconstruction]
timestamp: 2026-08-24T00:00:00Z
---

# An odd local offset means data alignment was off

A routine's frame is two bytes larger than the original's, its first local sits one byte lower, and its declarations are identical to the original's in order, type and count. There is nothing to add and nothing to remove.

**Look at where the original put the first local. If the offset is odd, the unit was compiled `{$A-}`.**

    ENTER $1136,0    ...    LEA DI,[BP-$0B51]      $A- : packed, odd offset
    ENTER $1138,0    ...    LEA DI,[BP-$0B52]      $A+ : word-aligned, padded

Turbo Pascal 7 defaults to `{$A+}` and starts every variable on a word boundary. With alignment off it packs them. A variable of *odd* size -- a record whose fields happen to total an odd number, an odd-length array of bytes -- is where the two settings part company, and it is the only place they do.

## The shift pattern is the diagnostic, not the frame size

The frame being two bytes bigger says almost nothing on its own; a missing `Integer` says the same. What separates the two is **how the locals below it moved**.

| what you see | what it is |
|---|---|
| every local below the gap shifted by the SAME amount | one missing or extra declaration |
| locals shifted by DIFFERENT amounts at different depths | one pad byte per odd-sized variable -- alignment |

Two independent one-byte gaps in one frame is not a variable. Nothing you can declare is one byte in two places at once.

That distinction is worth having because the alternative reading -- an extra compiler temporary -- is unfalsifiable from the source, and believing it ends the investigation. It is the reading that gets recorded as *the compiler pads and Pascal cannot express it*, which is a conclusion no measurement supports.

## What it does NOT change

**Record field layout.** Turbo Pascal packs record fields regardless of `$A`; the switch governs only where a *variable* starts. So `SizeOf` of any record is the same under both settings, and a matching `SizeOf` is not evidence that alignment matches. Checking the record layout first is the natural move and it is a dead end.

## It is a per-unit switch and it must be measured per unit

**Do not put it on the compiler's command line.** `$A` is a unit property like `$G` and `$N`, and a target's units will not agree. Setting it globally is the fast way to find that out and the slow way to recover: on one corpus it gained bytes in three parts and simultaneously broke a fourth binary's byte-identical rebuild, which is the only reason it was caught at all.

Add it to one unit, rebuild that target, keep it if it measures better and revert it otherwise. Most units will not move. **A sweep that only ever adds is not a measurement** -- the reverts are the evidence that the ones you kept mean something.

## Why it works

`$A` is read when the compiler allocates a name, so it is fixed at the declaration rather than at the use. Local offsets are assigned in declaration order downward from `BP`, and the first declared local ends flush against `BP` when packing is on. An odd offset can therefore only arise from packing, and a compiler with alignment on cannot produce one at all.

## Blind spot

**A unit with no odd-sized variables reads the same under either setting**, so the technique is silent exactly where it would cost nothing to be wrong -- and silent is not the same as `$A+`.

**It says nothing about the body.** A frame that matches after the switch is added is one measurement agreeing; the statements are still unread.

**Globals and typed constants shift too**, which moves data-segment displacements throughout the unit. Expect a coverage walk to move in both directions on the first build and judge it on the total, not on the first span you look at.

## Cost

One glance at a prologue and one `LEA` or local reference. If the offset is odd, you are done.

## Example

A 3D object sorter in a 1994 VGA demo opened `ENTER $1138,0` against the original's `$1136`, with its whole-object local at `[BP-$0B52]` against `[BP-$0B51]`. The declarations matched -- same order, same types, and `SizeOf` of the record was 2,897 in both builds.

That `SizeOf` agreement was read as proof the record layout was right, which it was, and then as proof alignment was not involved, which it was not. The investigation concluded instead that the compiler had made one more loop-limit temporary than the original reused, and recorded the routine as unreachable by source-level means.

The shift pattern refuted that in one reading: locals *above* the record moved by one byte and locals *below* it by two. One extra temporary cannot do that. Adding `{$A-}` to the unit closed the routine exactly and took the part from 98.8% to 98.9% with no unaligned span of sixteen bytes or more left anywhere in it.

Swept across the rest of the target, the same switch was kept on two further units and reverted on nineteen. On the compiler's command line it gained thirty-one bytes in one part and thirty in another -- and broke a third binary's byte-identical rebuild, proving the switch was never global. [1]

# Citations

[1] `src/P2S2.PAS`, `src/P1S5.PAS`, `src/P5S3.PAS`, `build.toml` and `status.toml`, in the psycho repository; measured with `kit/tools/pascal/spans.py` and `kit/tools/pascal/artefact.py` on 24 Aug 2026. The byte-exact control that refuted the global switch is that target's launcher, `TPART0`.
