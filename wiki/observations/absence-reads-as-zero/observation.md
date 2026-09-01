---
type: Observation
title: A total quietly drops a component and stays plausible
description: One instrument read a number out of another's printed output; the other was gone, so the pattern matched nothing and the count fell back to zero -- and a missing tool is indistinguishable from a tool that measured nothing.
tags: [verification, tooling, measurement, coverage]
timestamp: 2026-08-23T00:00:00Z
---

# A total quietly drops a component and stays plausible

A coverage figure, or any total assembled from several measurements, comes back lower than you remember and still entirely believable. Nothing failed. No file was missing. The run printed no warning, because from the inside nothing went wrong.

**Find out how each component reached the total.** Where one instrument gets a number by running another and matching a pattern against what it printed, that pattern has two ways to match nothing, and the code cannot tell them apart:

* the other tool ran and genuinely measured nothing;
* the other tool is not there, or moved, or renamed, or now prints a different word.

Both arrive as *no match*, and the natural thing to write next is `int(m.group(1)) if m else 0`. **A zero from a missing tool adds to a total exactly as convincingly as a zero from a real measurement.**

## Why it works

A total is the one shape where a missing component cannot make itself known. A comparison that loses an input reports a mismatch; a check that loses its subject reports nothing to check. A sum just gets smaller, and every property you would use to sanity-check it -- it is a plausible number, it is less than the maximum, it did not change much -- still holds.

The printed output of another program is also the weakest possible contract. Nothing declares it, nothing versions it, and it is written to be read by a person, so the wording is exactly the part most likely to be improved.

## Blind spot

**Refusing on no-match is right and still not enough.** It converts silence into a stop, which is the important half -- but a tool that ran and printed a DIFFERENT number for a good reason still slips through, because there is a match. Only comparing against a figure recorded elsewhere catches that.

**A recorded total is not the check people assume.** If the last recorded figure came from the same broken path, it agrees with the broken run and disagrees with the repair. Here the honest figure was 12 bytes off what was on record -- and the record was the one that was wrong, for a reason a different ticket had already found and fixed.

**It only applies where one tool reads another.** A tool computing its own inputs has other problems, not this one.

## Cost

One conditional: refuse when the pattern does not match, and say what was run and what came back. The expensive version is the one where the fallback is a literal zero.

## Example

A coverage instrument for a 16-bit DOS rebuild, 23 Aug 2026. It shelled out to a second tool for the one segment it could not measure itself -- the program, which emits no unit -- and matched `agrees for the first (\d+) byte` against the output. That tool had been archived weeks of work earlier in favour of a config-driven successor. So the pattern matched nothing, the count fell back to zero, and **1,616 verified bytes left the total in silence**: the figure read 96.1% instead of 99.8%, and 96.1% is a number nobody would question.

It refuses now, naming the tool it ran and printing what came back. Repointed at the successor, the figure is 99.8% -- and **12 bytes higher than the one on record**, because the archived tool had been clipping a block that ran past the end of the rebuild. [1] [2]

## Citations
[1] `kit/tools/pascal/coverage.py` -- the branch that measures the program, and the comment on why it refuses rather than falling back.

[2] The resolutions of *progcmp is a blockcmp case, not a fourth instrument*, which found the clipping, and *The thirty-two scripts still outside the kit*, which found the silence.
