---
type: Observation
title: A whole-line comparison against a DOS source is a check that cannot pass
description: Two copies of one body-finder compared lines against the literals asm and end; after reading with newline translation off and splitting on the line feed, so on a CRLF source every line carried a trailing carriage return, nothing matched, and the population was empty -- the gate above then reported zero duplicates and passed, printing exactly what a clean tree prints.
tags: [tooling, verification, encoding, blind-spot, measurement]
measured_on: 2026-09-03
timestamp: 2026-09-03T00:00:00Z
---

# A whole-line comparison against a DOS source is a check that cannot pass

A source read for measurement must not be rewritten, so it is opened with newline translation off. Split the result on the line feed and every line of a CRLF file ends in a carriage return. Compare such a line against a literal --

    if lines[k] == "asm":

-- and the test is false for every line of every file. The function returns nothing. **The caller does not see an error; it sees an empty population**, and a search over nothing finds nothing wrong.

The reason this is worth a page rather than a fix is what sits above it. The empty mapping fed a duplicate-detection gate, which printed

    0 routine(s) with assembler written out in a unit
    0 duplicate(s)

and exited 0. Both lines are true. Neither is informative, and the second is the line a genuinely clean tree prints -- so the gate sat on the universal check list, passing, for as long as the tree it guarded followed the project's own line-ending convention. See [A total that quietly lost a component reads as zero](../absence-reads-as-zero/observation.md).

## Why it works

**Newline translation off is correct, and it is what creates the trap.** The rule it serves -- never let a tool rewrite a byte of a file that is itself the artefact -- is not negotiable in a byte-exact reconstruction. So the carriage return is genuinely there, and the mistake is not the read mode but treating the split result as though the ending were gone.

**A regex is immune and an equality test is not.** In the same file, a marker scan using `search` found every marker while the body-finder found no bodies, because a search does not care what follows the match. That asymmetry is why nothing looked wrong: the tool reported markers and bodies from the same file in the same run, and only one of the two numbers was zero.

**The convention decides which trees are affected, so the corpus divides by line ending rather than by content.** Measured here: one repository's two reconstructions hold the same unit with the same four routines. One tree is CRLF and reported 0 bodies; the other is LF and reported 4. Identical sources, identical routines, and the only difference in the result was the ending. The consumer where the code had always worked has LF sources throughout, which is why the defect survived every run anybody had made.

## Blind spot

**The fix does not generalise from one call site, because the copies are not in one place.** The same defect existed in two functions in two files. One of them lives in a module written expressly to end this duplication -- three programs had each had their own marker regex and their own rule for pairing a marker with a routine, and that module's docstring says so -- but one copy was never moved onto it. So the deduplication was partial, and a partial deduplication is worse than none here: fixing the shared reader looked like fixing the problem, and the gate went on reporting zero. See [A second copy of one measurement drifts, and the drift manufactures a finding](../drifted-second-copy/observation.md).

**Ending-agnostic comparison is not ending-agnostic writing.** Strip the ending for a COMPARISON; never strip it on the way back to disk. A tool that normalises what it read and then writes it out has silently converted an artefact, which is the failure the read mode was protecting against.

**A line-ending checker is not the guard for this.** The one on this corpus defaults to `.BAT` alone, deliberately and with a measurement behind it: the DOS shell mis-parses an LF batch file while the Pascal compiler and the assembler tolerate LF happily, and a check that flags eight working files to catch one broken one trains its reader to ignore it. So a tree may legitimately hold both endings, and a tool that reads it may not assume either.

## Cost

Two forms, and the first is the one to prefer:

    lines = text.splitlines()            # the ending is gone, once, for the file
    if lines[k].rstrip() == "asm":       # or defend at each comparison

`splitlines` is better where the whole function reads lines, because it removes the class of bug rather than one instance of it. Defending at the comparison is the smaller edit and leaves the next comparison exposed.

The cheap detector costs one line: **print the size of the population in the same sentence as the verdict.** A gate that says "0 duplicates" is unreadable; one that says "0 duplicates among 60 routines" is a measurement; one that says "0 duplicates among 0 routines" reports its own defect. The tool that had this bug already printed its population on a line of its own and nobody read it, which is the argument for putting the count beside the verdict rather than near it.

## Example

A 16-bit Pascal reconstruction, 3 Sep 2026. Two host roots in one repository, each rebuilding one version of the same program, plus a sibling repository sharing the toolkit as a submodule.

The trigger was unrelated. The first four routines in one root were being declared with address markers, and a stale address map in the second root's copy of the unit -- inherited from the first and never re-measured -- sent the search for the real address into the image itself. All four turned out to be byte-identical in both binaries, at a segment one paragraph apart with their internal offsets unchanged. Marking them gave the duplicate-detection gate a population for the first time, which is when its zero stopped being plausible.

    v1.31b  CRLF  bodies=0   <- 67 assembler routines in that tree
    v1.51   LF    bodies=4
    psycho  LF    bodies=60

The 67 is what made it obviously wrong rather than merely suspicious. Before the markers existed the same zero had a legitimate reading -- the body-finder is marker-driven, so no markers means no bodies -- and it had been accepted on exactly that basis earlier the same day. **A defect can hide behind a correct explanation of the same number**, and the way out was not a better argument but a tree where the two explanations disagree.
