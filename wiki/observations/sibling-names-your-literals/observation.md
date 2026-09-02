---
type: Observation
title: A sibling's constants name your literals, and uniqueness is what makes the search usable
description: A reconstruction writes a number because a number is what the instruction holds. A sibling implementation wrote the same number as a name. Pairing every literal against every named constant finds them -- and returns mostly noise, because a small number is named by many things. Keeping only the values exactly one constant claims inverts the ratio.
tags: [reverse-engineering, naming, tooling, evidence, measurement]
measured_on: unrecorded
timestamp: 2026-08-29T00:00:00Z
---

# A sibling's constants name your literals, and uniqueness is what makes the search usable

A reconstruction reads `$45` out of an instruction and writes `$45`, because that is what was measured and anything else would be invention. A sibling implementation of the same program wrote `grTimerControl`.

The name is not decoration. It says what the value MEANS, and it says how many other places must change if it ever changes. On this corpus a literal `8` left in three places where the constant said 16 displaced fourteen units that had no defect of their own — the compare tools reported the symptom in the wrong place entirely.

So the search is simple: pair every literal in the target against every named constant in the reference, and report where they agree.

## The first run is mostly noise, and the noise has a shape

553 matches came back. The twenty most common values each carried between two and a dozen candidate names — `8` was `DevBits` and eleven others. **A match that offers a dozen names offers none.**

The fix is one filter: keep only values that exactly ONE constant in the reference claims. That inverts the ratio, because it selects for the numbers an author had to name — the ones that cannot be guessed from context. A port offset, a register number, a timeout, a size limit. Small round numbers drop out on their own, since everything names those.

What survived was worth having: **22 hardware register numbers across 72 call sites**, and one size limit across 18 more.

## Three false matches to expect, and one that is not a match at all

* **The same number, a different meaning.** `$11` is a status port offset, an enum ordinal and a structure offset in one program.
* **A number the reference names but this version changed.** A count is data and data measures one version only — the release's `MaxOutputFreq` is 45000 where this target holds 44000. **A name that does not match the value is worse than no name.**
* **A literal in hand-written assembler**, where the author was writing bytes. Though not always: the sibling here used its named constant *inside* its own inline assembler, so the transcription follows it there too.
* **And a literal the sibling also writes as a literal is not a finding.** One extended-command base was flagged, and the release writes the same bare `$11` in the same expression. The number staying a number is the transcription being faithful.

## Blind spot: what the search has to ignore

Comments, strings and character codes, stripped before the search. A tree that records every variable's address in prose has hundreds of numbers in it, and leaving them in buries the real matches under commentary.

**And the target's own declarations.** A checker anchored at the line start reported a unit's own constants as unnamed literals, because Pascal allows several declarations on one line and the second one looked like a bare number. That inflated the report with matches that were already done.

## Why it is safe to apply in bulk

An untyped constant is a compile-time value: it emits nothing, so naming ninety call sites cannot move a byte, and the rebuild proves it. That makes this one of the few passes where a wide mechanical change carries no risk to the artefact — the risk is entirely in choosing a wrong name, which is why the filter matters more than the fixer.

## See also

* [A named constant that only some of its uses go through is worse than no constant at all](../constant-only-half-applied/observation.md)
* [A name is a claim, and it should be no stronger than the evidence that produced it](../name-carries-its-evidence/observation.md)
* [A table carried forward from the previous version has no witness in this one](../data-measures-one-version/observation.md)
* [A variable nothing reads can still be named, by matching a sibling's declaration order](../sequence-names-what-nothing-reads/observation.md)
