---
type: Observation
title: A compare tool's number is plausible, and it is wrong
description: The offset is right and the length is too short, or the length looks reasonable and the position is nowhere near the thing -- the density gate and the location strategy are both properties of the artefact, not of the tool.
tags: [comparison, verification, tooling, fixups, alignment]
timestamp: 2026-08-23T00:00:00Z
---

# A compare tool's number is plausible, and it is wrong

Your compare tool has produced a figure. It is not an error, and it is not absurd: a prefix of 38 bytes, or `agrees to +1492 of 1750 (88%)`. Nothing about the figure tells you whether it is true.

**Two settings decide whether it is, and neither of them belongs to the tool.** How long a walk may stay alive on differences the rule lets through, and how the thing being measured is found in the first place, are both properties of the artefact in hand. Set for the wrong artefact they do not fail -- they shorten or displace the measurement and then report it with exactly the confidence of a true one.

Which of the two went wrong is readable from the shape of the answer:

- the offset is right and the length is short -- the density gate
- the length is believable and the position is nowhere near the thing -- the location strategy

So the only question this page answers is: **which artefact are you measuring?**

<!-- generated:discriminator -->
| if you are looking at | how to tell | detail |
|---|---|---|
| a routine inside a linked image | you have an address in the original and a routine in your build that should sit at it | [routine-in-image](./routine-in-image.md) |
| a compiled unit's code at the head of a `.TPU` | output of TPC that has not been linked yet, compared against the whole segment it rebuilds | [unit-in-tpu](./unit-in-tpu.md) |
<!-- /generated:discriminator -->

## Why the answer cannot be general

A density gate -- stop the walk when too many of the last sixteen bytes were differences the rule let through -- is protection against an alignment that wandered out of the thing being measured and is staying alive on one- and two-byte holes. Whether that protection is right turns entirely on how dense the *legitimate* differences are, and that varies by orders of magnitude between artefacts: a hand-written routine inside a linked image has a handful, and one compiled unit in this corpus has 569 unresolved references. [1]

Location has the same shape. A routine inside a whole executable has no known start, so it has to be found: anchor on a run long enough to be unique, and score every candidate by how far the comparison then gets. A unit's code at the head of a `.TPU` *does* have a known start -- the head of the code section is the first instruction -- so the first byte is the anchor and the winner is the candidate whose prefix reaches furthest. Each strategy fails on the other's artefact: the scoring one drifts to whatever alignment shares the most bytes, and the first-byte one has no first byte it can trust. [1] [2]

## How both of these were found

Neither came out of reading the code. Both came out of running a new instrument beside the frozen tool it was replacing and reading every row where the two disagreed -- fourteen rows of twenty-six in one repository, and one unit reporting a percentage about the wrong place. [3]

**This also corrects the premise the consolidation began from**, which held that the four compare tools differed only in which differences they permit. They differ in how they locate as well, and the tool that had the location right carries two earlier strategies that failed, written down in its own docstring. [3] [4]

## If you are not sure which you have

Ask what produced the file, not what the number looks like. A plausible number is the failure mode here, so the number cannot referee. The two artefacts differ in one visible way -- a `.TPU` still holds unresolved references and a linked image does not -- which is the same discriminator as [A zero byte where the original has something else](../zero-byte-difference/observation.md).

# Citations

[1] `kit/tools/substrate/align.py`, `walk()` and its `density` argument, and the `DENSITY_WINDOW` / `DENSITY_LIMIT` constants above it.

[2] `kit/tools/substrate/align.py`, `locate()` and `anchor_first()` -- the two location strategies, side by side.

[3] The resolution of [One compare tool, and every caller passes its rule](https://github.com/sweetlilmre/PsychoNeurosis/issues/33), which records all five differential findings and the measurements behind them.

[4] [Draw the tooling package boundary](https://github.com/sweetlilmre/PsychoNeurosis/issues/9), whose premise this corrects, with the correction recorded on the ticket itself.
