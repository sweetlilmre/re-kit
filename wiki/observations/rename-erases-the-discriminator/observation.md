---
type: Observation
title: A specific name is a type tag, and unifying it merges the two things it was keeping apart
description: Two configs held the same number under different names. Measuring how every reader USED the value said one fact, so the names were unified -- and the narrower name turned out to be the only thing distinguishing two different addresses. Measured across ten readers in one toolkit; nine used it as a bound and the tenth as a meaning, and the merge made every part of a nine-part target measure short by exactly the size of its runtime library.
tags: [tooling, verification, measurement, blind-spot, method, naming]
measured_on: one reverse-engineering toolkit, ten readers across three targets
timestamp: 2026-09-03T00:00:00Z
---

# A specific name is a type tag, and unifying it merges the two things it was keeping apart

Two projects held a boundary paragraph under two names. One called it the runtime's start; the other called it the end of the walk. They looked like the same fact wearing two labels, and the obvious tidy-up is to pick one name.

**The narrow name was carrying information.** Not decoration -- a discriminator. It said *what lives at this address*, and once it was gone the two configs stated the same key with the same type and different meanings, which no reader can detect.

## Why it works

The test applied before the rename was: **how does each reader use this value?** Ten readers, and the answer came back uniform -- every one of them appended it to a list of segment bases to close the last segment's extent. One fact, two names, safe to merge.

That test asks about *syntax*. It cannot see denotation.

| what the check asked | what it found | what was true |
|---|---|---|
| how is the value used? | ten readers, all as a list bound | correct, and irrelevant |
| what is AT the address? | not asked | one target's runtime, another target's data group |

Nine readers only ever needed a bound, so for them any consistent choice worked. The tenth read it as **a meaning** -- the paragraph a data group begins at -- and a meaning is not interchangeable with a bound that happens to sit nearby.

**The rule stayed consistent and the address moved.** Both configs honestly answered "the boundary after the last listed segment". But one lists its runtime segments among the rest and the other deliberately excludes them, because the runtime is not its to transcribe. So the same rule, applied to two different segment lists, denotes two different addresses -- one before the runtime, one after it.

The value's meaning depended on **the membership of another key**, and unifying the name hid that dependency rather than resolving it.

**The measurement.** In the nine-part target, whose artefacts all rebuild byte-identical and whose data group must therefore agree exactly, every part came out short by the size of its own runtime -- the first by 15,184 bytes, which is that part's runtime segment at `0x3B50` to the byte. Nine confident figures, a full comparison table under each, and not one of them implausible on its face.

## Blind spot

**Auditing the readers is the wrong population.** The defect is in what the writers meant, and the writers are two config files whose authors are not present. A reader tells you the type; only the target tells you the referent.

**A uniform answer from a survey of usage is exactly what a merge needs to hear, so it is the most dangerous possible result.** Had two readers disagreed syntactically, the merge would have been refused. Agreement is what let it through.

**The specific name looked like the defect.** It named one language's runtime in a toolkit meant to serve any target, which is a real smell and the reason the rename was proposed. It was also true, and true of precisely one of the two projects -- so the smell and the information were the same characters. Removing the parochial-sounding name is right; removing it without asking what it discriminated is not.

**A name describing a value's POSITION is safe to generalise; a name describing its CONTENT is a claim.** `end_at` says where the list stops, which is a structural fact. `rtl_para` says the runtime is there, which is a claim about a particular binary -- and claims are exactly what you cannot merge away, because two targets can disagree about them.

## Cost

One question per reader, at rename time - **not "how is this used" but "what would I find if I looked at this address".** For nine of the ten the answer is "does not matter, it is a bound", and that answer is itself the finding: the tenth reader stands out immediately once the question is asked in that form.

## Example

A key renamed across two config files to serve both a one-target and a nine-part project. The survey said ten readers used it identically. The tenth used it to locate a data group, and the two projects place that group on opposite sides of their runtime library.

The fix is not a better name. It is **two keys**, because there were always two facts - one for where the segment walk closes, one for where the data group begins. They are equal in one target by coincidence of what its segment list contains, and that coincidence is what made them look like one fact.

## Citations

- Ten readers, three targets, one toolkit; nine parts each short by their runtime's size.
- [A tool that takes one fact by argument and another from the environment measures a chimera](../ambient-default-outvotes-the-argument/observation.md) -- the same session, the same shape of failure: every input valid, the combination meaningless, and the output a plausible number.
- [A match rule stricter than the thing it matches reports absence, not failure](../match-rule-stricter-than-its-subject/observation.md) -- a rule and its subject disagreeing quietly, where the rule is the thing to doubt.
