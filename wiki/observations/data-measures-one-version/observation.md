---
type: Observation
title: A table carried forward from the previous version has no witness in this one
description: Reconstructing version N+1 from version N's source, the code gets checked against the new binary on every build and the DATA does not. A table nothing computes is only ever confirmed by the image it was read out of -- so a retuned table survives every code comparison intact, in a unit that verifies byte-for-byte, until the layout is exact enough to compare the initialised image itself.
tags: [reconstruction, comparison, verification, dgroup, measurement]
timestamp: 2026-08-29T00:00:00Z
---

# A table carried forward from the previous version has no witness in this one

Reconstructing one release from the previous one's source is the cheap way to start, and it treats code and data very differently without saying so.

**Every line of code gets re-checked on every build.** It compiles, the bytes are compared against the new binary, and anything the author changed shows up as a difference. That is the whole method.

**A table of constants gets checked by nothing.** It is emitted verbatim, the routine that reads it is usually unchanged, and there is no instruction anywhere whose bytes depend on the values. So a table the author retuned between versions is carried forward wrong and stays wrong, in a unit that verifies byte-for-byte, for as long as the reconstruction lasts.

Measured: a 128-word logarithmic volume ramp in which **253 of 256 bytes were wrong**. Only entry 0 survived between the two versions. The unit containing it had compared identical for the whole reconstruction.

## The rule this hides behind is a correct one

The note above that table already said the newer *published* source "is worth nothing for its data" -- a count or a table in a related release is somebody else's measurement, and the binary in front of you wins. That is right, and it is exactly what conceals the problem: having correctly refused the release's numbers, the numbers you kept feel measured. They were -- **of a different binary**.

Say it as a scope rather than a preference: *data transcribed from an image is a measurement of THAT image*. Carrying it to another version is an assumption, and an assumption with no witness is not a finding.

## What to do

* When you start version N+1 from version N's source, **list the typed constants that are tables** -- the ones no code computes -- and treat every one as unverified until the initialised image can be compared.
* Do not chase them early. They are unfalsifiable until the data layout is exact, because a value in the wrong PLACE and a value that is wrong look the same. They fall out in one pass at the end, which is the cheap moment.
* The tell that you are looking at one: a run of differing bytes in the initialised region, in a unit whose code is already exact.
* Small scalars hide better than tables and matter as much: a default port, a default IRQ, a buffer count. No instruction names them, a command-line switch overwrites them, and only the image says what the default was.

## See also

* [A typed constant nothing reads is invisible to every comparison that follows an instruction](../dead-data-has-no-witness/observation.md)
* [A hardcoded address copied from the original is right by coincidence](../transcribe-the-meaning-not-the-constant/observation.md)
