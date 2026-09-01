---
type: Observation
title: A measurement tool reads whatever is on disk, and a failed build leaves the last good answer there
description: Every instrument that compares a build product against a target opens a file by path. Nothing in that file says which source it was built from, so a build that refuses leaves the previous product in place and every downstream measurement reports the previous verdict -- correctly, for source that no longer exists. The build's own warning is not a guard, because a warning has to be read.
tags: [tooling, verification, measurement, reverse-engineering, process]
measured_on: unrecorded
timestamp: 2026-08-29T00:00:00Z
---

# A measurement tool reads whatever is on disk, and a failed build leaves the last good answer there

A reconstruction's instruments all have the same shape: open the product, open the target, compare. The product is named by a path. **Nothing inside it records which source produced it**, so when a build refuses and leaves the previous product in place, every instrument downstream reports the previous verdict — and reports it *correctly*, because that file really was byte-identical. It is simply an answer to a question nobody is asking any more.

Measured. In one session a build refused six consecutive times while four separate measurements reported the linked image byte-identical, the packed output byte-identical, 32 of 32 units exact and 32 of 32 link positions agreeing. Every number was true of an `.EXE` compiled before the edits. Three of those verdicts were reported to a person as confirmation that the edits were sound.

## Why the build's own warning did not help

It was as loud as a warning can be:

    BUILD FAILED -- 1 error(s) above. NOTHING WAS INSTALLED, so anything in the
    output directory is STALE and any measurement of it is meaningless.

That sentence anticipated the exact failure and named it. It did not fire, because the build's output was being read through a filter — `grep -iE "error|fatal|FAILED"` — and the message that mattered contains none of those words in a matching position. The filter existed to keep a noisy tool's output short.

**A warning that has to be read is not a guard.** It depends on the reader's attention at the moment they are least likely to have it: mid-task, expecting success, filtering for brevity. The guard has to live where it cannot be skipped by accident, which is inside the instrument that consumes the artefact.

## The check

One comparison of modification times, in whatever module already answers questions about the host's layout, so that every instrument gets it and none of them owns it:

* **The artefact must be newer than every source it was built from.** Older means it was not built from what is on disk, and measuring it means nothing.
* **A missing artefact fails too**, for the same reason a tool that finds nothing must never report agreement.
* **Timestamps, not hashes.** A hash is exact and needs a manifest, which is one more thing that can go stale. A file older than its inputs is wrong under every build system, and a false alarm costs one rebuild.
* **Fail with the diagnosis, not just the symptom.** The message should say to read the build's output *in full* rather than filtering it, because the filter is how the reader got here.

## The wider shape

This is one instance of a general hazard: **an instrument whose input is addressed by path rather than by content cannot detect that it is answering a stale question.** The same failure appears wherever a pipeline stage is skipped rather than failed —

* a cached artefact keyed on a name rather than a content hash
* a generated file whose generator errored, leaving the previous generation
* a test run against a binary a compile step did not replace
* a report regenerated from an extract that failed to refresh

In every case the observation is not an error but a *correct answer to a superseded question*, and that is what makes it survive review. Nothing looks wrong. The numbers are real. They are about a file nobody is thinking about any more.

## See also

* [Every declared routine matches, and the rebuild still behaves differently](../verifier-blind-to-absence/observation.md)
* [A tool that is wrong is useless; a tool that BECOMES right is worth re-asking every open question](../instruments-have-an-order/observation.md)
* [The same source builds twice and the files do not hash the same](../rebuild-hashes-differ/observation.md)
* [Two tools measure one thing and one number is lower](../two-tools-one-number/observation.md)
