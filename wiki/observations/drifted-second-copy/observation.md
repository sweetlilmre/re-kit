---
type: Observation
title: A tool reports a shortfall and blames something plausible for it
description: Two instruments each held a copy of one measurement; the copies drifted, and the drift did not go quiet -- it manufactured a finding that read like an observation about the code.
tags: [verification, tooling, measurement, drift, segments]
measured_on: the tracker reconstruction and the toolkit itself
timestamp: 2026-08-23T00:00:00Z
---

# A tool reports a shortfall and blames something plausible for it

A check tells you an artefact is short by a specific number of bytes, and offers a reason that fits: *"short -- 144 byte(s) of routines nothing references"*. The number is exact. The explanation is the kind a person would have reached for. Everything around it is exact.

**Before believing it, find out whether anything else holds the same measurement.** A figure computed from a table is only as good as the table, and a table that exists twice has nothing keeping the copies in step. The failure that follows is not the one people expect: a drifted copy does not merely fall silent or throw. **It produces a finding**, phrased in the vocabulary of the thing being measured, which is why nobody looks at the table.

The tell is that the explanation is about the SUBJECT while the cause is in the instrument. "Routines nothing references" is a claim about a compiler and a linker. Nothing about it points at a list of segment addresses in a Python file.

## Why it works

A measurement derived from a list inherits every property of the list, including its gaps. Where a length is computed as *the next entry's address minus this one's*, a missing entry does not produce a missing row -- it produces a WRONG ROW, because the arithmetic silently reaches past the absent neighbour to the one after it. The error is exactly the size of what is missing, which is what makes the resulting figure look measured rather than mistaken.

Two copies also fail asymmetrically, and that is worth knowing when you go looking. The instrument that reads the complete copy is fine and says nothing. Only the other one is wrong, so the two disagree -- and nothing compares them, because comparing them is what having one copy would have done for free.

## Blind spot

**Finding the second copy does not tell you which is right.** Both may be wrong, and the older one is not automatically the authority: here the shorter list was also the one whose own comment asked a reader to keep it in step with the other. The way out is a third thing neither was derived from -- a document, or the binary itself.

**A cross-check is only as good as its key.** Comparing two lists by position hides a missing entry as a shift in everything after it; comparing by name found this one immediately. Pick the comparison that makes an absence look like an absence.

**It says nothing about copies that have not drifted yet.** A second copy that currently agrees is a defect waiting rather than a defect, and no measurement can distinguish the two.

That is not a caution about a hypothetical. The same migration consolidated **three readers of one comment format into one, and all three had already diverged** -- so the case above was not the unlucky exception, it was the second of at least two, found because somebody went looking for duplicated tables after the first. Once you have found one drifted copy, the cheap next move is to enumerate every other place the same fact is written down.

## Cost

A set comparison, once, at the moment you notice two tables that look alike. The expensive version is the one where nobody notices: this pair had a comment asking a person to remember, which is a mechanism only in the sense that a note is one.

## Example

Two instruments comparing a rebuilt 16-bit DOS program against its original, 23 Aug 2026. Both carried the original's segment list -- one as `(segment, name)` pairs, one as names in link order -- and both said in their comments that it came from the same layout document. Generating one config from both, with a cross-check by name, refused to write: the pair-list was **missing a 144-byte segment**.

Two consequences, and the second is this observation:

* that segment's own length was never compared, so a headline of *"28 unit(s) exact"* was 28 of 29 with nothing naming the twenty-ninth;
* its neighbour's length ran to the segment after it and came out **144 bytes too long** -- exactly the missing segment's padded size, because each length is computed as the next segment's address minus its own -- which the tool reported as **144 bytes of routines nothing references**. The neighbour was exact. [1]

The arithmetic is worth writing down, because it is what makes the number checkable rather than quoted. Three consecutive rows of the layout, the middle one being the row that was missing:

    { segment = 0x1891, name = "OBJECTS" }
    { segment = 0x1931, name = "VTSHELL" }     <- absent from the drifted copy
    { segment = 0x193a, name = "DEVSB" }

`0x193a - 0x1931` is 9 paragraphs, so the missing segment is 144 bytes. Without its row the neighbour computes as `0x193a - 0x1891` rather than `0x1931 - 0x1891`, which is 144 bytes more. **The inflation and the missing segment are the same number by construction**, and that identity is the cheapest possible test for this class of defect: if a reported shortfall equals the size of something absent from your list, the list is what is wrong.

An earlier version of this page recorded the missing segment as **159 bytes**, which no reading of that table supports -- 159 would need ten paragraphs and would put the next segment at `0x193b`. The figure was never derived; the 144 was measured and the 159 was written beside it, and for as long as both stood the identity above was invisible.

Read once, that line is a finding about how a 1994 linker treated a runtime unit. It was a missing row in a list. [2]

**Not every changed number is this, and telling them apart matters.** The same consolidation moved one coverage figure by 24 bytes because two implementations had formulated a density gate differently -- and there the SAME spans were reported, two of them shorter, with none lost. A drifted copy manufactures a finding; a reformulated rule moves a number without hiding work. The question to ask of a changed measurement is not how far it moved but **whether anything it used to report has gone missing.**

## Citations
[1] `kit/tools/pascal/mapcmp.py` and `linkorder.py`, and `v1.31b/link.toml` in the `VangeliSTracker` repository -- the one list both now read, whose header records the drift.

[2] The migration sweep that found it, which also consolidated three diverged readers of one comment format into one, and which recorded every instrument whose answer changed and why -- see [The successor reproduces the headline number and quietly drops the diagnostic](../successor-keeps-the-headline/observation.md) for the deletions that pass stopped.
