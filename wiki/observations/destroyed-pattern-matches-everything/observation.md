---
type: Observation
title: A search whose pattern was destroyed matches everything, and it agrees with you
description: A quoting form that silently produced an EMPTY pattern turned a file scan into a universal match, so every file reported the condition being looked for. The number was not absurd -- it split a corpus exactly along the line the hypothesis predicted, and it justified a bulk rewrite of four documents that had nothing wrong with them. A tool cannot tell an empty pattern from a matching one unless somebody makes it, and the reading that arrives as confirmation is the one nobody checks.
tags: [verification, tooling, measurement, drift]
measured_on: the kit's own documents, 7 files
timestamp: 2026-09-01T00:00:00Z
---

# A search whose pattern was destroyed matches everything, and it agrees with you

A scan says every file in one group has a property and no file in the other group does. The split is clean, it falls exactly where you expected it to fall, and it is the evidence for a change you were already planning.

**Check that the search ran with the pattern you think you gave it.** A pattern that arrives EMPTY matches every line of every file, so the scan reports the condition present, everywhere, in the confident voice of a real measurement.

Measured here, looking for carriage returns in a set of markdown files:

    A)  the pattern bare, as its own argument            -> no match, correctly
    B)  the same pattern inside a nested substitution     -> the condition found, in EVERY file
    C)  what the search actually received in form B       -> zero bytes

The two scans had been written in different forms, in separate commands, minutes apart. One group of files was scanned with form A and the other with form B, so the corpus appeared to divide neatly into two kinds -- and the division agreed with a theory already held about which files were which.

## Why it works

An empty pattern is not an error in most search tools; it is a legal pattern that matches at every position. So the failure has no error path, and the two outcomes it sits between are indistinguishable from the outside:

- the pattern was fine and the condition is genuinely everywhere;
- the pattern was destroyed and nothing was tested.

That is the same shape as an instrument reading zero because the thing it calls is gone. **The rule generalises from tools to patterns: where a search consumes something it was handed, it must be able to tell absence from a match.** A scan that cannot say *my pattern was empty* is a scan whose clean result carries no information.

**The direction of the error is what makes it expensive.** A destroyed pattern does not fail closed and report nothing found -- that would be safe, because nobody acts on an empty result. It fails OPEN and reports everything found, which is an actionable answer.

## Blind spot

**A plausible split is the hardest case, and it is the common one.** If the false positive covered every file the result would look broken. Here it covered exactly the files scanned with the broken form, which was a subset chosen for an unrelated reason -- so the artefact wore the shape of a finding. **The corpus did not split along the property; it split along which command had measured it.**

**Confirmation is when a measurement gets the least scrutiny.** This reading was produced while looking for evidence that four documents broke a rule they themselves state, and it said exactly that. A measurement that contradicts you gets checked twice; one that agrees gets acted on. There is no instrument for this, which is why the second reading has to be a habit rather than a step.

**The second reading must not share the first one's machinery.** What caught this was a tool that answers the same question by a different route entirely -- version control's own record of the property -- not a re-run of the scan. Re-running form B produces the same answer forever, and running it more carefully still produces it.

## Cost

One independent reading of the same property, before acting. Seconds, and the thing it protects against is a bulk change to files that were correct.

Cheaper still, where the tool allows it: have the scan print the pattern it received. Form C above is the whole diagnosis and it took one command.

## Example

Seven markdown documents, 1 Sep 2026. The claim was that four of them used one line ending and the other ninety-one used another, in direct contradiction of a rule those same four documents state. It justified a planned bulk rewrite of all four -- a whole-file diff on the most-read documents in the tree.

**There were no carriage returns anywhere.** Every file measured zero, and version control reported the same for all of them. The rule was never broken; the measurement was.

Three instances of the same underlying trap appeared in that one session, which is the reason this page exists rather than a note: a pattern destroyed by nested quoting, a script whose escapes were consumed before the interpreter saw them so it never ran, and a body of prose whose formatting characters were eaten mid-sentence by the shell that carried it. Only the first produced a false finding; all three came from passing text through an argument instead of a file.

## Citations

- The three failures above, and the rule they all violate: text containing characters the shell reads goes to a tool through a FILE, never through an argument.
- [A total quietly drops a component and stays plausible](../absence-reads-as-zero/observation.md) -- the inverse: a pattern matching nothing because its target is gone, indistinguishable from a target that measured nothing. Its rule, that an instrument must tell absence from zero, is what this extends to patterns.
- [A tool reports a shortfall and blames something plausible for it](../drifted-second-copy/observation.md) -- the same lesson about a plausible number that manufactures a finding rather than going quiet.
- [To know what an instrument cannot see, break the tree on purpose and check that it complains](../break-it-to-learn-what-it-sees/observation.md) -- the discipline that would have caught this in one command: give the scan a file you know lacks the property, and check that it says so.
