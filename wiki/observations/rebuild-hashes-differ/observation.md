---
type: Observation
title: The same source builds twice and the files do not hash the same
description: A Turbo Pascal .TPU and a TASM .OBJ carry a build timestamp, so file hashing cannot answer whether a change altered the output -- the executable can, and it is the only thing that can.
tags: [verification, comparison, turbo-pascal, tasm, rebuild, tooling]
timestamp: 2026-08-23T00:00:00Z
---

# The same source builds twice and the files do not hash the same

You want to know whether a change to the build altered what comes out. You build, hash everything, change nothing, build again, and hash again -- and the hashes move. Nothing was edited.

**The intermediate files carry a build timestamp.** A `.TPU` records when the unit was compiled, and a `.OBJ` records when the module was assembled, so two builds of byte-for-byte identical source differ in those bytes and in nothing else. File hashing therefore cannot answer the question at all: it reports a difference on every rerun, and a real difference looks exactly the same as the clock moving.

**The executable can answer it.** A linked DOS image has no timestamp field, so it is stable across builds of the same source -- which makes it the unit of a reproducibility check, and the only one worth building a claim on.

## Why it works

The compiler and the assembler are writing files another tool has to decide about later: a linker deciding whether a unit needs recompiling, a make deciding whether a rule is out of date. A date is the cheapest way to carry that, so the format has a field for it. The linker's output has no such consumer -- nothing downstream asks the executable when it was made -- so nothing writes a date into it.

This is also why the useful comparison of a `.TPU` is of its **code section** rather than its bytes. The section is what the compiler emitted for the source; everything around it is bookkeeping, and the timestamp lives in the bookkeeping.

## Blind spot

**Stability is not correctness.** Two builds agreeing proves the build is deterministic, which is exactly the thing that lets you attribute a later difference to your change. It says nothing about whether either build is right.

**A stable executable can still hide an unstable input.** If the toolchain embeds nothing, an output that never changes is also what you get from a build that silently did not run -- so the check needs the build to have reported what it compiled, not just the hashes to match.

**It is a claim about this toolchain, not all of them.** A linker that stamps a date, or one that pads with uninitialised memory, would not give a stable image. Measure it once on a new toolchain rather than assuming it.

## Cost

Two builds and a hash of each output file. Minutes, and it only has to be done once per toolchain.

## Example

`PSYCHO NEUROSIS`, 23 Aug 2026, establishing a reference before three build scripts were merged into one. Two consecutive full builds of unchanged source: of 243 staged and built files the `.TPU` and `.OBJ` outputs differed, and **all 35 `.EXE` files were byte-identical**.

That reference is what made the merge checkable rather than arguable -- the merged tool's 35 executables were compared against it and matched, so the three artefacts already sitting at R7 were not being taken on trust. The equivalent check for the sibling target, whose build produces units rather than programs, had to be the unit instrument's rows instead: 2 byte-identical and 24 identical but for fixups, before and after. [1] [2]

# Citations

[1] `kit/tools/pascal/build.py`, in the psycho repository -- its header records the measurement and why an executable is the unit of the check.

[2] The resolution of [One build harness across both repos](https://github.com/sweetlilmre/PsychoNeurosis/issues/35).
