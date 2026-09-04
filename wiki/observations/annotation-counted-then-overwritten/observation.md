---
type: Observation
title: A generated file that invites annotation, a check that counts the annotation, and a remedy that deletes it
description: A tool that writes part of a document and asks a person to finish the rest has three pieces that must agree -- what it writes, what its check reads back, and what its regenerate command replaces. When the check reads the whole file instead of its own output, an annotation reads as drift; and when the writer replaces the whole file rather than its own section, the printed remedy for that false drift destroys the annotation. Measured on segdoc.py, which reported 14 rows on disk against 6 computed and whose fix would have replaced 40 lines of read binary with a 12-line table.
tags: [tooling, verification, documentation, blind-spot, instruments]
measured_on: the kit's own segdoc.py, against a map document with one added table
timestamp: 2026-09-04T00:00:00Z
---

# A generated file that invites annotation, a check that counts the annotation, and a remedy that deletes it

A tool generates part of a document and expects a person to write the rest. This is a good arrangement and a common one: the tool owns what it can compute, the person owns what no config holds. `segdoc.py` says so in its own docstring -- it writes a segment's address and size, and "rows come out named from the segment list and nothing more, so a person can annotate them afterwards".

Three pieces have to agree for that to hold, and they are usually written at different times:

1. **what the tool writes** -- its own section;
2. **what its check reads back** -- which must be that same section, not the file;
3. **what its regenerate command replaces** -- which must also be that same section.

## Both failures are the same mistake, and the second is destructive

When the check reads the WHOLE file, anything a person adds that resembles the generated rows is counted as generated. A second table -- the most natural annotation there is -- makes the check report drift that does not exist. Measured: adding one per-routine table to a map document produced *14 row(s) on disk, 6 computed*.

When the writer replaces the WHOLE file, the remedy is worse than the complaint. The false drift tells a reader to regenerate, the file's own header prints the command to do it, and running it replaces every annotated line with the generated table. The guard that existed refused to overwrite a document with **no** generated banner -- which protects a hand-written file and does nothing for a generated one that has since been annotated, because that file carries the banner.

**So the two defects compose into a trap.** A check that cannot tell annotation from output, and a writer that cannot either, means the tool reports a problem that is not there and prescribes an action that causes one.

## What to do instead

Delimit the generated section and operate only on it. A banner comment is already enough if both halves honour it: read rows from after the banner up to the first line that is not a row, and refuse to write when the file holds whole lines the generator would not have produced. Neither needs a diff of the prose -- a set comparison on whole lines is sufficient, and prose inside a generated row's own column stays free.

## Blind spot

**This cannot see an annotation that looks exactly like output.** A person who adds a row in the generated table's own shape, inside the generated section, is indistinguishable from the tool having written it -- the refusal is on whole lines outside the section, so a row added inside is still lost on regeneration. The narrow reading is that delimiting protects annotation that lives OUTSIDE the generated block, and that a document wanting per-row prose should keep it in a column the generator preserves rather than in rows of its own.

It also says nothing about a tool whose output has no delimiter at all. Adding one to an existing generated file changes every consumer's copy of that file on the same day, which is a migration rather than a fix.

## Cost

Two helpers and a guard clause. No new configuration, and no change to what the tool computes.

## Related

* `exemption-that-cannot-fail` -- a check whose scope is wrong claims to have checked more than it did. This is the inverse: a check whose scope is too wide claims a failure that is not there.
