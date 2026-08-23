---
type: Observation
title: Two tools measure one thing and one number is lower
description: A tool that adds two classes of permitted byte counts anything in both of them twice; measure the overlap, and the discrepancy stops being an opinion.
tags: [comparison, verification, fixups, relocation, tooling]
timestamp: 2026-08-23T00:00:00Z
---

# Two tools measure one thing and one number is lower

A reimplementation reproduces the tool it replaces on every row, every verdict and every summary line -- except one count, and that count is **lower**. Nothing else moved.

**Look for two classes that overlap before looking for a bug in either tool.** A count of outstanding debts is usually the sum of several classes: bytes that are zero on our side, bytes the object module recorded as relocations, and so on. Where two classes can describe the same byte, adding the class sizes counts that byte twice, and the sum is larger than the truth by exactly the size of the overlap. The union is the honest figure.

This is worth reaching for first because it is *cheap to settle*. The overlap is a set intersection: compute it, and the discrepancy stops being two opinions about a number and becomes an arithmetic identity. That is what turns "my number differs" into "their number double-counts", which are very different claims to put in front of somebody.

## Why it works

Classes of permitted difference get added one at a time, each for a good reason, and each one is written as a predicate over bytes. Nothing in that process asks whether two predicates can be true of the same byte -- the code that adds them is a `+`, and a `+` cannot tell. So the defect is not in either class's reasoning; it is in the assumption of disjointness that nobody wrote down and nobody tested.

## Blind spot

**Only visible where the classes actually overlap.** A corpus in which they never do would never show this, and the tool would look correct for years. So a clean differential run is not evidence the sum is safe -- it is evidence this corpus does not exercise the overlap.

**Lower is not automatically right.** The direction tells you where to look, not who is correct: a reimplementation can also be lower because it is missing a class entirely, which looks identical from the outside. The thing that settles it is the measured overlap matching the discrepancy exactly. If it does not match, the difference is something else and this page does not apply.

**A changed number with no published explanation loses a measurement its authority.** Whichever way it resolves, the new figure and the reason for it have to be written down beside the old one, because the next reader's first instinct will be that the new tool is wrong.

## Cost

One set intersection per artefact, and the willingness to publish a number that is lower than the one people are used to.

## Example

`VangeliSTracker`, 23 Aug 2026. The frozen tool reported `PLAYMOD` **1187** and `SOUNDDEV` **1024** outstanding fixups; the replacement reported **1178** and **839**. The two classes were "a zero on our side" and "a byte the object module recorded as a relocation", and the overlaps measured **exactly 9 and 185** -- the two discrepancies, to the byte. A byte that is both a zero and a recorded relocation is one debt, counted twice. [1] [2]

# Citations

[1] `kit/tools/pascal/units.py`, which reports the union, and `kit/tools/substrate/omf.py`, which reads the relocation set out of the object module.

[2] The resolution of [One compare tool, and every caller passes its rule](https://github.com/sweetlilmre/PsychoNeurosis/issues/33), under *One deliberate difference, and it is the frozen tool that is wrong*.
