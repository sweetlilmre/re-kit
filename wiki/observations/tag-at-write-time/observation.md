---
type: Observation
title: A judgement is free at the moment you make it and expensive at every moment after
description: A reconstruction's comments serve two opposite readers, and separating them is a judgement no pattern can make. Recorded as you write, it costs nothing, because you have just made it. Recorded afterwards it must be re-derived from prose alone, and the instrument that guards the separation is blind to more than half of what needs deciding -- measured at 475 of 908 tagged lines carrying no mechanical tell at all.
tags: [method, documentation, tooling, blind-spot, verification]
measured_on: one 34-unit 16-bit Pascal reconstruction, 908 tagged lines
timestamp: 2026-09-04T00:00:00Z
---

# A judgement is free at the moment you make it and expensive at every moment after

A reconstruction's source carries two kinds of prose that look identical and serve opposite readers:

- **the evidence** -- how this was learned. A segment address, a rejected hypothesis, the tool that settled it.
- **the explanation** -- what the code does, for somebody who does not care how it was recovered.

A copy meant for the second reader has to lose the first. Nothing can separate them mechanically, because the difference is not in the words: *"the loader reads the header twice"* is explanation, and *"the loader reads the header twice, which is how we knew the first read was discarded"* is both. **So the split is a judgement, and the only question is when it is made.**

## Why it works

**At write time the judgement has already happened.** You are typing the comment because you just decided something. Whether you decided *what this does* or *how you now know it* is not a question you have to answer -- it is the reason your hands are moving. Marking it costs one tag.

**Afterwards it is a different task entirely**, and a much larger one. It is no longer "record the decision I just made". It is "reconstruct, from prose, a decision somebody made months ago, for every paragraph in the tree" -- and the person doing it is usually not the person who made it, even when it is the same person.

The tooling is not the cost. The tooling is cheap and it exists. The cost is one judgement per paragraph, and it is the same judgement either way. Only its price changes.

## Blind spot

**The instrument that guards this cannot see most of what it guards.** A checker for untagged apparatus can only fire on a *mechanical* tell -- a `segment:offset`, a segmented address, the name of a measuring tool, a withdrawal marker. It must not fire on prose style, because a tool that guessed at tone would raise so many false alarms that nobody would run it, and an instrument nobody runs is worse than none.

Measured on one 34-unit target:

| tagged lines | carrying a mechanical tell | carrying none |
|---|---:|---:|
| 908 | 433 (48%) | **475 (52%)** |

**More than half the apparatus was invisible to the check.** Those 475 lines are in the stripped copy's exclusion list only because a person put them there. Had that person not, nothing would have objected.

**The failure is silent by design.** Tagging is keep-by-default, which is the right way round -- on a real corpus half the comments carry no apparatus and never need touching. The price of keep-by-default is that an untagged apparatus comment does not fail. It **leaks**: it appears, reading perfectly well, in the document prepared for the reader it was never meant for.

**So a late pass is not merely more work, it is work with no safety net over half its surface.** An early tag cannot leak, because the tag and the comment are the same act.

## Cost

One marker, at the moment of writing, on roughly half the comments you write. Against: a full re-read of the tree, one judgement per paragraph, with an instrument that can confirm fewer than half your answers.

## Example

A 34-unit reconstruction, 908 tagged lines, tagged after the fact. The stripping tools -- the copier, the tag checker, the brace checker, the config gate -- were all already built and needed nothing. What remained was the reading, and the reading was the entire job.

The sibling tree of the same program, reconstructed first, carries **zero** tags. It is the same size and the same kind of work, and the decision about whether it ever gets a readable copy is still open -- because the cost being weighed is not the tools, which are free, but re-deriving a thousand judgements nobody wrote down at the time.

## Citations

- One 34-unit 16-bit Pascal reconstruction; 908 tagged lines, 433 with a mechanical tell.
- [An enumeration that is short reads as a finding, and the finding is about the reader](../an-addend-can-be-a-size/observation.md) -- the same shape in a classifier: what the instrument cannot enumerate, it reports wrongly or not at all.
- [A tool's docstring is the only claim about it that nothing executes](../docstring-is-an-unrun-claim/observation.md) -- prose with no failing state, which is why a leak here is silent.
