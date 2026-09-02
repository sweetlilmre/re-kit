---
type: Observation
title: Resolve every type alias before ruling a sibling implementation's record misaligned
description: Comparing another implementation's declarations against measured offsets means adding up its field widths, and one aliased type assumed to be the wrong size shifts everything after it. The failure is silent and self-confirming -- the record looks misaligned, so it gets rejected as a naming source, and the rejection is never revisited because it explains what you saw.
tags: [reverse-engineering, naming, evidence, verification, measurement]
measured_on: unrecorded
timestamp: 2026-08-29T00:00:00Z
---

# Resolve every type alias before ruling a sibling implementation's record misaligned

A sibling implementation -- an earlier release, a related product, another program by the same authors reading the same file format -- declares the structure you are transcribing. Its names are the best available for the fields it actually reads. To use them you have to line its record up against the offsets you measured, which means adding up its field widths from the top.

**One aliased type assumed to be the wrong width shifts every field after it, and the result looks exactly like a misaligned record.**

Measured. A 1994 loader's header declaration opened:

    TS3mFileMagic1 = WORD;          { two lines away, and skipped }
    ...
      Name        : ARRAY[1..28] OF CHAR;
      Magic1      : TS3mFileMagic1;
      NPI1        : WORD;
      SeqLen      : WORD;

`Magic1` sits where a four-character signature sits in the format, and it was read as four bytes without the alias being looked up. That put every subsequent field two bytes late, so `SeqLen` -- which is the order-list length, at the offset the specification gives for it -- appeared to be two bytes off. The record was written off as unreliable and a specification was used for the names instead.

The alias is a `WORD`. Resolved, the record lines up on every field.

## Why the error survives

Because it is self-confirming and it closes the question. A misaligned record explains itself: sloppy source, a different revision, names attached to whatever was convenient. Every one of those is plausible, none is testable, and once the source is written off nothing brings it back for a second look. The rejection also *feels* like rigour -- it is a measurement being preferred over a document.

The cost is asymmetric. Rejecting a bad source costs nothing; rejecting a good one silently discards the only author-written names available for those fields, and there is no later signal that it happened.

## The check

Before concluding a sibling's record is misaligned:

* **Resolve every named type in it to a width**, including single-line aliases far from the declaration and any that alias another alias. A signature or magic field is the usual trap, because its *format* width and its *declared* width need not agree -- a program may read half of one.
* **Line up from BOTH ends.** A record with a known tail -- a magic value, a fixed-size table at the end -- pins the total. If the tail matches and the head does not, the discrepancy is inside, and it is a width you got wrong far more often than an author's mistake.
* **Prefer the arithmetic that makes the source correct**, then test it. Any offset table that makes a real implementation come out right is more likely than one that makes it wrong -- that program loaded real files.

## The wider habit

An implementation that ran is stronger evidence than a specification for anything it actually reads, and weaker for everything it skips. Both statements matter: the fields a sibling names are the ones it consumed, and the fields it leaves as `fill1` are the ones only a document can name. A correct alignment lets you take each half from the right source, and a wrong one costs you the choice entirely.

## Blind spot

**It detects a misalignment, not a wrong meaning.** A record that lines up on every field after the aliases are resolved has been shown to have the right SHAPE. Nothing here shows the fields mean what their names say -- a sibling implementation can have the widths right and the semantics drifted, and this method reports that as a clean match.

**Resolution needs the alias to be reachable.** Where the sibling's type comes from a unit you do not have, the width cannot be resolved at all -- and the method cannot then distinguish *unresolvable* from *wrong*, which is the state that produced the original error. An unreachable alias should stop the comparison rather than default to an assumed width.

## See also

* [A name is a claim, and it should be no stronger than the evidence that produced it](../name-carries-its-evidence/observation.md)
* [If the program has clients, look for their bindings before deciding a structure is unknowable](../the-other-side-is-shipped/observation.md)
* [A compare tool's number is plausible, and it is wrong](../plausible-and-wrong/observation.md)
* [A table carried forward from the previous version has no witness in this one](../data-measures-one-version/observation.md)
