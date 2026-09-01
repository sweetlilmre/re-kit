---
type: Artefact Answer
title: A compiled unit's code at the head of a .TPU
description: How to set the gate and find the code when what you are measuring is a whole compiled unit against the original segment it rebuilds.
order: 2
holding: a compiled unit's code at the head of a `.TPU`
identify: output of TPC that has not been linked yet, compared against the whole segment it rebuilds
artefact: TPU
tier: pascal
ladder_node: R7
tags: [comparison, verification, alignment, fixups, turbo-pascal]
timestamp: 2026-08-23T00:00:00Z
---

# A compiled unit's code at the head of a `.TPU`

Part of [A compare tool's number is plausible, and it is wrong](./observation.md).

## What to do

**Turn the density gate off, and say at the call site why.** Dense unresolved references are normal in this artefact, so the gate does not protect the measurement here -- it shortens it.

**Anchor on the first byte.** Every position in the file whose byte equals the segment's first byte is a candidate. Take the candidate whose prefix reaches furthest.

**Require room for `min(overlap, length)` bytes, not for the whole segment.** A half-written unit compiles much shorter than the segment it rebuilds, and both halves of that expression are load-bearing -- see the blind spot.

## Why it works

The head of a unit's code section *is* its first instruction, so the first byte is a legitimate anchor rather than a guess. That single-byte constraint looks far too weak to be useful, and the reason it holds is what it excludes: it keeps the search out of the `.TPU`'s symbol table and off its runs of zeros, both of which have scored well enough to win under stronger-looking rankings. Ranking by prefix length is also alignment-independent, which is what makes the reported first divergence the real one.

The gate has to come off because Turbo Pascal leaves every unresolved reference as zeros plus a fixup record, and a unit can hold a great many: one unit in this corpus has 569. A gate calibrated for a routine's handful of address holes reads that as an alignment that has wandered, and stops. What carries the gate's load instead is the cap on the run rule -- four bytes, the longest thing a single fixup can zero -- so a field of zeros still cannot read as agreement. [1]

## Blind spot

**Turning the gate off removes the protection it exists for.** Nothing else stops a walk that is alive on differences alone except the four-byte cap, and the cap is a weaker guard than the gate: it bounds each run but not their density. This is why the setting is a parameter with a stated reason at each call site rather than a default anybody can inherit.

**The overlap requirement is wrong in both directions if either half of it is dropped.** Requiring the whole segment to fit from the candidate onwards rejects every candidate for a partial unit, and reports *not located* for a unit whose opening is perfect. Dropping the length floor gives a segment shorter than the overlap a harder test than it had before, which once took a 29-byte unit from 93% to not located. [1]

**A unit that links an object module cannot be measured by this rule at all.** TASM leaves an addend where the compiler leaves a zero, so the assembler half reads as a wall of differences. Those units need the object file's own relocations, which is a stricter measurement rather than a looser one. [2]

## Cost

A freshly compiled `.TPU`, so DOSBox and a working period toolchain -- the unit has to be built from the current source to be comparable at all, and a stale build reports a number that looks like an answer. No disassembler.

**Check that freshness by CONTENT, not by timestamp.** The obvious test -- is the `.TPU` older than the `.PAS` -- does not work here: an emulated DOS writes DOS timestamps that do not compare reliably against the host's, and an mtime check reported a FRESH build as stale. A stale-build guard that cries wolf is worse than none, because the first thing anybody does with one is stop believing it. Compare what the build was made from instead. [3]

## Example

26 units in the `VangeliSTracker` repository, 23 Aug 2026. With the density gate left on, **14 of the 26 reported a prefix shorter than the truth, one of them 38 bytes instead of 1,617** -- and the offset was right in every single case. The offset being right is the tell: a wrong offset gives nonsense, a wrong gate gives a plausible number. [3]

## Withdrawn

**Two rankings that were tried before prefix length, both recorded on the tool that replaced them:**

- *Fewest real differences.* A run of zeros scores as a perfect match, and **two units passed that should not have.**
- *Most exact matches.* Not fooled by zeros, but it drifts when the two sides are different lengths, sliding to whatever alignment shares the most bytes -- "which can be nowhere near the start, and then reports a first-divergence offset that means nothing." [1]

# Citations

[1] `kit/tools/substrate/align.py` -- `anchor_first()` and `pending()`, whose docstrings carry both failed rankings and the 29-byte measurement.

[2] `kit/tools/pascal/objcheck.py`, and `kit/tools/substrate/omf.py` for reading the relocations out of the object module.

[3] `kit/tools/pascal/units.py`. Verified against the frozen tool it replaced by a differential run, matching it on every row; the frozen tool's own docstring is where the two rejected location strategies are recorded, and its content-based staleness check is where the timestamp finding above comes from.
