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

The two locators answer different questions and neither is a better version of the other. One anchors on a unique ten-byte run and scores each candidate by how far the walk gets, which is what finding one ROUTINE inside a whole executable needs. The other anchors on the FIRST BYTE and takes the candidate whose forgiving prefix reaches furthest, which is what comparing a whole unit against the segment it rebuilds needs. Its two rejected predecessors are instructive in opposite directions: ranking by *fewest real differences* scores a run of zeros as a perfect match, and let two units pass that should not have; ranking by *most exact matches* is not fooled that way but drifts when the unit and the segment are different lengths, so it lands nowhere near the start and then reports a first-divergence offset that means nothing.

**So the seam is not one tool but one ENGINE and several INSTRUMENTS.** The engine holds the two comparison shapes -- a prefix walk whose rule is about a RUN, and a positional compare whose rule is about ONE BYTE. The instrument supplies the allowed-difference rule **and** the location strategy, because both belong to the artefact rather than to the comparison. That is a widening rather than a reversal: the rule is still passed in and never built in, and four scripts still become one engine. What changed is the count of things that get passed in -- and the count of things a caller can therefore get wrong, which is why this page exists. [4]

Naming the rule also shrank the family. A fourth member of it turned out not to be a fourth instrument at all: it was the positional compare's shape carrying the window rule, so once the rule was something you passed in rather than something you wrote a program around, it stopped needing a program. **An instrument count is a claim about how many rules you have, and it is wrong in the same direction every time** -- a rule buried in a tool looks like a tool. [3]

## If you are not sure which you have

Ask what produced the file, not what the number looks like. A plausible number is the failure mode here, so the number cannot referee. The two artefacts differ in one visible way -- a `.TPU` still holds unresolved references and a linked image does not -- which is the same discriminator as [A zero byte where the original has something else](../zero-byte-difference/observation.md).

# Citations

[1] `kit/tools/substrate/align.py`, `walk()` and its `density` argument, and the `DENSITY_WINDOW` / `DENSITY_LIMIT` constants above it.

[2] `kit/tools/substrate/align.py`, `locate()` and `anchor_first()` -- the two location strategies, side by side.

[3] The differential run that produced all five findings: a new instrument run beside each frozen tool it replaced, with every disagreeing row read. The five were the density gate belonging to the artefact, a walk rule having to say how many bytes it forgives rather than whether, locating unmasked before re-measuring masked, the mask and the walk being in different coordinate frames, and the fourth instrument that was a rule.

[4] The consolidation decision this widens -- *one compare tool, not four; the allowed-difference rule is passed in, never built in*. Its premise, that the four tools differed only in which differences they permit, is the thing corrected above; the restatement to one engine and several instruments is recorded here rather than only where it was argued.
