---
type: Observation
title: A hello-world names the compiler that built a stranger
description: Which compiler built an unknown binary is usually argued from file dates and folklore. Compile a four-line program with each installed candidate, take its runtime library's head, and search for it in the unknown with relocations masked -- the one that is found is the answer, and the ones that are not are excluded. It costs one build per candidate and it is a measurement.
tags: [toolchain, runtime, pascal, turbo-pascal, verification, measurement, reconstruction]
measured_on: unrecorded
timestamp: 2026-08-28T00:00:00Z
---

# A hello-world names the compiler that built a stranger

A new binary arrives and everything downstream depends on which compiler produced it -- a reconstruction that guesses wrong is not slightly off, it is a different instruction stream. The evidence usually offered is circumstantial: the file's date, what the author's other releases used, a configuration file shipped with a *different* version of the source.

**Build a minimal program with each candidate and look for its runtime in the unknown.**

    program P; begin Write('x') end.

Compile it with every installed compiler. Each links a stub of the runtime library -- the initialisation, the exit path, the write helper -- and that stub is the compiler's, not the program's. Take the first couple of hundred bytes of it and search the unknown binary for them, **with every relocated word zeroed on both sides**. A relocated word holds a load-time segment value, so unmasked it differs at every far pointer for reasons that say nothing about who compiled anything.

One candidate is found. The others are not found at all, which is the more useful half.

## Why a stranger's runtime is findable

Because the runtime's head is the one region a smart linker cannot rearrange. The program's own code sits wherever the link order puts it and its length depends on the source; the library's entry block is emitted first, in one order, by one code generator, and a program that writes a single character pulls in almost exactly the subset that any program pulls in. Two builds by the same compiler share it. Two builds by different major versions do not, and the divergence starts within a dozen bytes.

Measured, on two 16-bit DOS Pascal binaries a year apart: Turbo Pascal 6's probe stub was located in both, at each one's last code segment; Turbo Pascal 7's was located in neither. Not "matched worse" -- **not found**, which is a categorical answer rather than a threshold.

## A partial match is still an answer

The located block will not compare 100%, and expecting it to is how this gets misread. Two programs link different subsets of the library and the parts above the stable core shift. What matters is that the head was FOUND -- the search either anchors or it does not.

So read the result as: *found* excludes nothing about the version's patch level, *not found* excludes the whole major version. On the corpus above, 6.0 and 6.01 scored 33.1% and 33.0% against the same target and are simply not separable this way. That is a real limit, and it is the same limit for the binary you already understand, which is the control worth running.

## Run it against a binary you already know

**The probe means nothing without a control.** Point the same test at a binary whose compiler you have already established by other means, and check that it answers the same way. If the known binary comes back *not found* for its own compiler, the search rule is too strict -- which is a failure this class of tool has had before, where an exact-match rule over a masked window had never once succeeded and reported it as absence.

## Blind spot

**Base addresses.** A comparison tool that resolves a segment against the *project's* notion of where a load image starts will compute a negative file offset for a probe binary that loads somewhere else, and report `NOT FOUND` -- which reads as "there is no runtime here" rather than "I looked outside the file". Two candidates were excluded that way before the frame was noticed. Express the reference segment in whatever frame the tool is using, and sanity-check the printed file offset before believing an absence.

**Patch levels and configuration.** This identifies a code generator, not an installation. Switches that change codegen, a patched library, or a vendor's own rebuild of the runtime are all invisible here.

**It needs the candidates installed.** The method excludes what it can run and says nothing about what it cannot. A compiler nobody has is not ruled out by this; it is simply absent from the experiment, and the report should say which candidates were tried.

## Cost

One four-line source file, one build per candidate, and a search. Seconds, against a question that otherwise gets settled by argument and stays settled wrongly for weeks.
