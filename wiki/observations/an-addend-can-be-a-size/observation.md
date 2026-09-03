---
type: Observation
title: An enumeration that is short reads as a finding, and the finding is about the reader
description: A checker classified relocation fields into three known shapes and called everything else UNEXPLAINED. A fourth shape existed -- an addend that is a buffer's SIZE rather than a small offset into a structure -- and the field carrying it was reported as a defect in two separate targets, at the same offset, on a construct both projects state in an assembler comment. Every word the tool printed was true; the list it printed them from was one item short.
tags: [tooling, verification, measurement, blind-spot, hand-assembler]
measured_on: two 16-bit Pascal reconstructions, 140 relocation fields each
timestamp: 2026-09-03T00:00:00Z
---

# An enumeration that is short reads as a finding, and the finding is about the reader

A checker that sorts its input into known cases has to say something about the leftovers. Calling them **unexplained** is honest and it is also a claim about the world -- that the list of known cases is complete.

When the list is short by one, the tool reports a defect that is not there, and it reports it in the strongest language it has.

## Why it works

The failing message named exactly what it had ruled out:

> `102c UNEXPLAINED: orig 6274, ours 03e8 -- neither ours+base (0b2e) nor a zero our side left pending`

Both clauses are true. It is not `ours+base`, and it is not a pending zero. What the sentence does not say -- because the code behind it did not consider it -- is that the value might be a **symbol plus an addend too large to look like an addend**.

The bound was a constant with a reason attached:

```
# An addend is small; a DGROUP offset is not. Anything below this on our side
# is read as `symbol + n` rather than as a value in its own right.
ADDEND_MAX = 0x100
```

**An addend can also be a size.** Reaching the top of a buffer means adding its length to its base, so the addend is however big the buffer is:

```
StackSize   EQU     1000
            EXTRN   DevStack : BYTE
    MOV     SP,OFFSET DevStack + StackSize
```

1000 is four times the bound. Read as a value in its own right it matches nothing, so it fell through to the last branch and was named a defect.

## Blind spot

**A false positive in a strict checker is protected by its own strictness.** The tool is *supposed* to fail on things it cannot account for -- that is the whole point of it -- so an unexplained field looks like the instrument working, not like the instrument being short. Nobody chases it, because chasing it means doubting the thing you built to be doubted.

**It had been failing in two independent targets, at the same offset, for as long as either had an object module.** Two consumers reporting the same defect reads as corroboration. It is the opposite: the same missing case, twice, because they share the construct and the checker.

**And the answer was written down the whole time**, in an assembler comment two lines above the instruction, naming the constant and its value. The finding was never in the binary.

**The general shape is not about addends.** Any classifier ending in `else: unexplained` is asserting that its branches are exhaustive, and that assertion is the one thing it never checks. Ask what the last branch means, and whether a case could reach it legitimately.

## Cost

One reading of the classifier's branches against a case it rejected -- and the branches are usually a dozen lines. What makes it expensive is not the reading but the willingness to doubt a check that is behaving exactly as designed.

## Example

Two reconstructions of the same program, four years apart in build, sharing one assembler construct. Both reported `102c UNEXPLAINED`, one with `orig 3f1a` and the other `orig 6274` -- different addresses, same 1000-byte addend, same stack switch. Fixing the enumeration took both from exit 1 to exit 0, and the corrected report names the implied symbol at `5e8c`, which is `6274` less `1000`, exactly where the source says the buffer starts.

Kept strict: a field whose addend is too large even to be a size is still unexplained, and shifting one module's base six bytes still produces 105 unexplained fields and a failing exit.

## Citations

- Two 16-bit Pascal reconstructions, 140 relocation fields each, one classifier.
- [A tool's docstring is the only claim about it that nothing executes](../docstring-is-an-unrun-claim/observation.md) -- the same asymmetry in prose, and the row that matters there is also an omission rather than an error: *an incomplete list is a false claim that no proofreading catches.*
- [A match rule stricter than the thing it matches reports absence, not failure](../match-rule-stricter-than-its-subject/observation.md) -- NOT FOUND as a claim about the rule; here UNEXPLAINED is a claim about the enumeration.
