---
type: Observation
title: An exemption list is where a check goes to die
description: Four entries in an exemption file each carried a reason that was false, and the one that remained could not fail because the tool was blind to its case -- an exemption is a claim, and a claim about two texts can be diffed.
tags: [verification, tooling, measurement, coverage]
measured_on: unrecorded
timestamp: 2026-08-28T00:00:00Z
---

# An exemption list is where a check goes to die

A tool that cannot decide something on its own gets an exemption file: cases where the rule does not apply, one per line, each with a written reason. It is the honest design -- some facts are outside what a tool can see -- and it is also the one place in a project where a false statement can sit for months without anybody noticing, because **an exemption is the only kind of configuration whose effect is to stop a check from running.**

Two failure modes, and both were live in one small file:

* **The reason is wrong.** Every entry was written in good faith, by somebody who had just looked at the two things and concluded they could not be unified. Nothing re-reads that conclusion afterwards. The check does not: the entry is precisely the instruction not to.
* **The entry cannot fail.** The rule's coverage has a hole where that case lives, so the exemption suppresses nothing. Deleting the line changes no output. It still reads, to anybody scanning the file, exactly like a check being deliberately waived.

The second is worse than having no exemption at all. An absent entry is a gap you can find by looking at the rule; a decorative entry is a gap that looks like a decision.

## Why it works

The reasons in an exemption file are usually about **declarations, interfaces or intent** -- the layer above the bytes -- which is exactly the layer a text-comparing tool cannot reach. That is why the exemption exists. It is also why the reason is so easy to get wrong: it is written from a mental model rather than a measurement, and the mental model is frequently right about *there being* a difference and wrong about *where it lives*.

Concretely, the four false entries all said "the declarations differ, so no single text can carry them". Compared as strings, character for character, the declarations were the same line. What the author had actually noticed was real -- one copy was far and the others near -- but far-ness was not in the declaration at all, it came from the surrounding unit. The difference was one level up from the text, and the note put it in the text. See [Near or far is decided by the surrounding unit](../far-comes-from-the-unit/observation.md).

## Blind spot

**A green run is not evidence.** The tool reported zero problems both before and after, and both were true statements about what it had been told to look at. The measurement that mattered was not the tool's output but the diff of the two texts the exemption had told it to leave alone.

**An exemption need not be a list at all.** The same disease arrives whenever a check's SCOPE is a constant rather than an answer, and then it is invisible in a way a file never is -- there is nothing to read. Two measured instances, both from one migration:

- A source linter whose directory was a hardcoded constant. In the second consumer the sources sat one level deeper, so it reported *0 problem(s) in 0 file(s)* **and passed**. It lints 29 files there now. The tell was subtle and worth remembering: a workaround for the defect was already in place -- that consumer's build imported the linter's function directly rather than running the tool -- so **the workaround existed and the defect did not, which is a defect nobody was going to look for.**
- An encoding auditor whose default directories named one repository's two folders, both since emptied. Given the project's own answer it covers 49 files against 19, including, for the first time, the programs in the toolkit itself. **A tool that audits everything except itself is a shape worth recognising**, and it is the same shape as a hub exempt from the check on hubs.

A list at least admits what it is skipping. A constant scope claims to have checked everything.

**Testing an exemption needs it removed.** The only cheap check for a decorative entry is to delete the line and re-run: if the count does not change, the entry is doing nothing, and either the rule or the entry is wrong. That takes seconds and nobody does it, because the file reads like documentation rather than like code.

**Pair rules cut both ways.** Where an exemption names a pair, requiring BOTH sides to be listed is the right design -- it means an exemption cannot be half-written -- but it also means moving one side of the pair into a new file silently un-exempts it, and that arrives as a new failure rather than as a lost check, which is the safe direction.

## Cost

Deleting the line and re-running is one command. Diffing the two texts the entry claims are different is one more. Both belong in whatever ritual re-reads the file, and the file should say so.

The rule worth writing at the top: **an exemption is a claim, and a claim about two texts being different can be checked. Diff them before writing the reason.**

## Example

A 16-bit Pascal rebuild, 28 Aug 2026. Five entries in an exemption file for a tool that reports assembler bodies duplicated between units instead of shared through one include.

Four of the five were false. Two pairs of routines -- a 768-byte palette write and a single-DAC-entry write -- had identical bodies AND identical headers, and both became single includes with every one of the project's ten binaries still rebuilding byte-identical. The tool had been reporting *0 duplicates* while two real duplications sat behind those exemptions.

The fifth entry was the decorative kind. Its case was a unit holding its own copy of a routine an include already carried, and the tool skipped an include's body entirely -- correctly, since counting each including unit's copy would report the cure as the disease, but that left include bodies compared against nothing. Removing the exemption changed the reported count by zero. The tool was taught to compare include bodies as well, at which point the entry finally suppressed something real, and the same change uncovered a sixtieth routine that had never been in the check's population at all, hidden by an indented `procedure` line inside a comment block.
