---
type: Observation
title: A one-byte difference between two builds is two different findings
description: Diff two builds of one program and the single-byte gaps are ambiguous -- a ModRM displacement whose record field moved, or the low half of a 16-bit data reference whose high half happened not to change. Read as a signed displacement, the second kind manufactures a record-shrink finding at dozens of sites, in units whose source is identical. The two readings are congruent modulo 256, and that congruence is the test.
tags: [comparison, verification, tooling, measurement, codegen, reconstruction, dgroup]
measured_on: unrecorded
timestamp: 2026-08-28T00:00:00Z
---

# A one-byte difference between two builds is two different findings

You are diffing two releases of one program to find what the author changed, and you bucket the differences by how far each moved, because a shift repeated at forty sites is one cause and forty lines of hex is not. The buckets come back clean, and one of them says a record shrank by 88 bytes -- at forty-eight sites, in a unit whose source you have just proved is unchanged.

**A gap of one byte does not tell you what the byte was part of.** Two entirely different things produce it:

    26 8B 45 5D   ->  26 8B 45 7D      a ModRM disp8: Song.Status moved +$20
    A1 02 0C      ->  A1 AA 0C         the LOW HALF of [$0C02] -> [$0CAA]

The first is a field displacement and the delta is real. The second is a 16-bit data reference that moved $A8, and the high byte did not change because the move did not cross a 256-byte boundary. A differ that sees bytes rather than instructions gets one byte either way.

## The signed reading is what turns it into a finding

Read the second case as a *displacement*, and $02 becoming $AA is +168, which does not fit a signed byte, so the natural normalisation makes it **-88**. Now it reads as a coherent claim -- a record got 88 bytes smaller -- and it is repeated at every site in the unit, which is exactly what a real structural change looks like. Nothing about the bucket looks weak. It is usually the *largest* bucket in the unit, because data references outnumber field accesses.

Measured, on a 16-bit Pascal reconstruction: five units reported `disp8 -$58` at 48, 63, 40, 38 and 37 sites. Every one of those units' sources turned out to be byte-for-byte unchanged between the two versions. The invented bucket was larger than the true one in four of the five.

## The test is congruence, not plausibility

**Compare each byte bucket's delta against the word buckets', modulo 256.** A byte delta congruent to a word delta in the same unit is almost certainly that same shift seen through its other half:

    byte  +$a8  x48   old $2..$4e     <-- congruent to word +$a8
    word  +$a8  x4    old $772..$7da

Two buckets, one cause. The genuine field shift in the same corpus was `byte +$20` against no word bucket at $20 at all, and it survived the test.

Report byte deltas **unsigned, modulo 256**, and let the signed reading be the annotation rather than the headline. The unsigned form is the one that is true in both readings; the signed form is a commitment to one of them, made by the arithmetic rather than by evidence.

## Blind spot

**Congruence is evidence, not proof.** A record that genuinely moved by an amount congruent to the DGROUP shift is indistinguishable on this test, and there is nothing cheap that separates them. What settles it is the OLD VALUE: a bucket of displacements into one record occupies a small range of small numbers, and a bucket of data-reference low halves is spread across the whole byte. Print the range.

**It says nothing about which record.** Even a confirmed field bucket names only the smallest displacement that moved, which bounds where the insertion was; the size comes from somewhere else -- a virtual method table's own size word states it exactly.

**It is a property of byte differencing, not of the differ.** Disassembling both sides and comparing operands by instruction removes the ambiguity entirely, at the cost of needing a decoder that agrees with the compiler about where every instruction starts -- which, on a linear decode of a data-bearing code segment, is its own failure mode.

## Cost

One line of arithmetic and one annotation. The expensive version is the one where the sign is chosen by the language's integer semantics and nobody asks what the byte was part of.
