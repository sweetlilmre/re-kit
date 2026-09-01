---
type: Observation
title: A check written for one document's role, aimed at its type, goes quiet rather than wrong
description: A rule that only makes sense for a hub was applied to every document of type Observation, which on this corpus is 77 documents of which 3 are hubs. It could therefore fail 74 pages for doing exactly what they exist to do, and it failed two. It looked like a working check with two findings, because a misaimed check is quiet in proportion to how little it looks for -- so the narrowness of the pattern, not the correctness of the scope, is what kept the false-positive rate low. The fix is to derive the ROLE rather than read the type, from the same definition the generator already uses.
tags: [verification, tooling, measurement, drift]
measured_on: the kit's own wiki bundle, 86 documents
timestamp: 2026-09-01T00:00:00Z
---

# A check written for one document's role, aimed at its type, goes quiet rather than wrong

A wiki bundle here holds two shapes of page. A **hub** is an observation with children, each child answering for a different artefact, and the rules in those children **invert** -- what you must forgive in one artefact is exactly what convicts in another. So a hub is a discriminator and must never state a rule, because a rule stated in a hub is a rule stated for the wrong half of the corpus.

A **single page** has no children. It states its rule, and that is the whole job. There is nowhere else for the rule to go.

The check that enforces the first of those was written correctly and then aimed at `type: Observation`. Both shapes carry that type. **77 documents have it; 3 are hubs.**

## What that looks like from outside

    2 profile problem(s) in 86 document(s)

Two findings. A check that reports two problems out of eighty-six reads like a working check with a small backlog, and that is how it read for as long as it ran. Both findings were false:

- one flagged *a per-unit comparison must mask fixups because those bytes legitimately differ* -- descriptive of a necessity, with a subject, in a page explaining why an instrument is blind;
- the other flagged *Mask the hex literals in the operand text, diff the mnemonic sequences* -- a genuine bare imperative, in a single page, which is that page's entire contribution.

The second one matters more than the first. It is not a wording accident that a better pattern would catch. **The check was working exactly as written and asking a question that page had no business answering.**

## Why it stayed quiet, which is the transferable part

The obvious reading is that the check was mostly right and needed two exemptions. The measurement says otherwise: it was misaimed at 74 of 77 documents and only spoke twice, because the thing it looks for is six bare verbs with a short list of excusing words beside them.

**A misaimed check is quiet in proportion to how little it looks for.** Narrow the pattern and the false-positive rate falls, which reads exactly like the scope being right. Widen it later -- add a verb, drop an excusing word -- and a dozen legitimate pages fail at once, in a change whose author believes they are tightening a working check.

So the low count was evidence of a narrow pattern and evidence of nothing else, and it had been read as evidence about the scope. Two exemptions would have been the natural repair, and each would have made the misaim harder to see by removing the only symptom of it.

## What it should have asked

Not *what type is this document* but *does this document have children*. That is derivable: the generator in the same tool already walks a page's siblings and counts the ones typed as an artefact answer, because it builds the hub's table out of them.

The fix reuses that definition rather than writing a second one about filenames. **A second copy of this particular definition would be worse than most**, because drifting it changes which documents are checked without changing a single message -- the run stays green and the coverage moves silently.

Verified in both directions: with the scope corrected the bundle reports zero, and a rule injected into a real hub still fails it.

## Blind spot

`is_hub` reads its siblings' frontmatter, so **a child whose `type` is wrong or missing makes its parent look like a single page**, and the parent silently stops being checked. The failure is the one this observation is about, one level down: nothing reports a document that left the check's scope, because leaving the scope is not an error condition.

The same reasoning applies to any check that derives its applicability rather than being told it. Deriving is right -- it is what stops the two definitions drifting -- and the cost is that the derivation itself is unguarded. A check on how many hubs the bundle contains would catch it, and does not exist.

## Citations

- `kbprofile.py`, `check_hub_states_no_rule` and `is_hub`.
- The rationale the check was built from is in the bundle's own `README.md`, which records that the no-rule check is a heuristic over prose and had already produced one false positive -- a sentence that was the hub doing its job. That was read as a wording problem and repaired as one.
- [To know what an instrument cannot see, break the tree on purpose and check that it complains](../break-it-to-learn-what-it-sees/observation.md) -- the probe used here, and one of the two pages this check falsely accused.
- [A total quietly drops a component and stays plausible](../absence-reads-as-zero/observation.md) -- the same shape in a different instrument: a low number that is evidence of the measurement not running, read as evidence about the thing measured.
