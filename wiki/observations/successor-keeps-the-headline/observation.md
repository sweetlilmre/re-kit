---
type: Observation
title: The successor reproduces the headline number and quietly drops the diagnostic
description: A replacement tool is judged superseded because its main measurement matches the tool it replaces, row for row. What that comparison cannot see is every capability that only produces output when something FAILS -- a detail mode, a cross-artefact search, a candidate dump -- because a differential test on a corpus that passes never calls them. Three of one migration's retirement rows were wrong for exactly this reason, one of them for the tool the main line of work depended on.
tags: [tooling, migration, verification, measurement, drift]
measured_on: a two-repository toolkit migration, 49 scripts
timestamp: 2026-09-01T00:00:00Z
---

# The successor reproduces the headline number and quietly drops the diagnostic

You are retiring a tool because a new one replaces it. The check is the obvious one and it is a good check: run both on the same corpus and compare every row. They agree. The row goes to `archived` and the original is deleted.

**The comparison you ran exercised one of the tool's modes.** The others -- a `--detail` that prints the divergent regions of something that did *not* match, a search for the same span across every other artefact, a dump of the candidates a locator considered and rejected -- produce nothing on a corpus that agrees. A differential test over a passing corpus cannot call them, so it cannot miss them either. It reports agreement, truthfully, about the half of the tool that answers when things are fine.

## Why it works

A measuring tool has two audiences and they never overlap. The headline number is for the run that passes; the diagnostics are for the run that fails. So the state of the corpus decides which half of the tool is under test, and the state you compare in is almost always the passing one -- that is what makes the comparison clean enough to trust.

Follow that through and the blindness is structural rather than careless:

- **A green differential test is evidence about the passing path only.** It is not weak evidence about the rest; it is no evidence about the rest.
- **The capability with no successor leaves no trace.** A dropped output mode does not raise, does not change a number, and does not appear in any diff of the two tools' output on that corpus. Nothing anywhere says a flag is gone.
- **The cost lands later and elsewhere.** It arrives on the first day something fails, which is the day the diagnostic was for -- and by then the tool that had it is deleted and the person looking does not know it existed.

**It is the same shape as a gate that shortens a measurement without failing.** The number looks like an answer. Here the number *is* an answer, to a question narrower than the one the retirement row claims to have settled.

## Blind spot

**Enumerating flags is better and still not sufficient.** Comparing two tools' argument parsers finds a missing `--detail`; it does not find a capability that was a positional argument, a second entry point, or an undocumented behaviour reached by running the tool from a particular directory. The only complete answer is reading what the tool does, which is why this cannot be automated into the retirement check.

**A retirement row is a claim, and a stale one survives being corrected.** One row here said a script could not run at all. It ran. The tool's own header had already corrected that claim, and a *generated* document downstream carried the stale version anyway -- so the false statement was reproduced by the mechanism that was supposed to prevent drift. A generated document is only as good as what generates it, and its being generated is what stops anybody re-reading it.

**Being right about the headline makes the row harder to doubt.** A retirement row that cites a verified measurement reads as the most trustworthy kind, and it is the kind this defect hides behind.

## Cost

Reading each tool before deleting it, at the level of what it can be asked to do rather than what it printed today. On one migration that was three tools out of forty-nine, and finding them cost less than an hour; deleting one of them would have cost the main line of work its instrument.

## Example

A toolkit migration across two repositories, 49 scripts archived and 10 kept back. Three rows marked ready to delete were wrong, and each in a different way:

| the row said | what was true |
|---|---|
| "already copied" | the successor holds the logic as a LIBRARY FUNCTION with no runnable command, and a second mode -- find each span in every other built artefact -- has no equivalent at all. It was also the instrument the top open investigation ran on |
| matched on every row | true, and the detail modes that print the divergent regions of a unit that does NOT match have no successor. Eight other scripts imported it as well |
| "cannot run" | it ran, and printed its table. The tool's own header had already said so; a generated document repeated the stale claim |

The test that came out of it is one sentence, and it is worth more than the three saves: **check that the successor does the WHOLE of the job, not the headline.**

## Citations

- The retirement census and the generated disposition record that replaced it, whose rows carry each move's justifying measurement.
- [A script breaks and nothing in the import graph explains it](../config-is-a-dependency/observation.md) -- the same migration, the same lesson one level down: the import graph is the smallest of the dependency graphs and the only one with a tool.
- [A total quietly drops a component and stays plausible](../absence-reads-as-zero/observation.md) -- what happens after such a deletion lands, when the caller cannot tell a missing tool from a tool that measured nothing.
- [To know what an instrument cannot see, break the tree on purpose and check that it complains](../break-it-to-learn-what-it-sees/observation.md) -- the technique that answers this one: to test a diagnostic, you must first make something fail.
