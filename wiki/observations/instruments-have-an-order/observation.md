---
type: Observation
title: A tool that is wrong is useless; a tool that BECOMES right is worth re-asking every open question
description: The instruments in a layered reconstruction have a dependency order -- unit sizes need the link order, the data layout needs the sizes, the variable half needs the data layout. A tool downstream of a broken one produces noise, and the moment the upstream one comes right, every question that was parked for want of it is answerable at once.
tags: [tooling, verification, measurement, reconstruction, workflow]
measured_on: unrecorded
timestamp: 2026-08-29T00:00:00Z
---

# A tool that is wrong is useless; a tool that BECOMES right is worth re-asking every open question

In a layered reconstruction the instruments depend on each other:

    unit code       ->  needs nothing
    unit SIZES      ->  needs the link order to be right
    data layout     ->  needs the sizes
    variable half   ->  needs the data layout
    linked image    ->  needs all of it

A tool below a broken one does not report *less*; it reports **noise that looks like findings**. One unit sat at 49% agreement for eight sessions with a diagnosis of "unlinked fixups"; the moment the link order came right it linked at exactly the original's size, first try, with nothing changed in it.

## The moment a tool becomes trustworthy is a checkpoint

When an upstream instrument starts working, **stop and re-ask everything that was parked**. Two examples from one session, both immediately after the link order went from 30/32 to 32/32:

* Four addresses that would each have cost a scan of the image -- an object, a size, a flag, a routine -- were sitting in the linker map, which had been generated all along and had never been trustworthy enough to read.
* A number that had been reported for three sessions as "160 bytes of missing code" turned out to be the same number a different tool was reporting as a `-10` shift on 370 operands: ten paragraphs. **Reading it as a data-region shift would have sent a day in the wrong direction.**

## What to do

* Write down which instrument each open question is waiting on, not just that it is open.
* When an instrument's own verdict changes -- especially from "cannot run" to a number -- re-run every other one before doing any new work.
* Suspect a stalled measurement of being downstream of something else before suspecting the code it measures. The stalled unit above was correct the whole time.

## Blind spot

**The order is itself a claim, and a wrong one is self-confirming.** If an instrument is believed to be downstream of a broken one, its output is dismissed as noise -- including the part of it that was a real finding. That is the failure this page invites, and it is worse than the one it prevents: a defect explained away by a dependency is a defect nobody will look at again until the upstream tool comes right, and possibly not then.

**Nothing here tells you the upstream instrument is actually broken**, only that it is upstream. An instrument that is fine and reporting an uncomfortable answer occupies the same position in the chain as one that is wrong.

## See also

* [Two tools measure one thing and one number is lower](../two-tools-one-number/observation.md)
* [A script breaks and nothing in the import graph explains it](../config-is-a-dependency/observation.md)
