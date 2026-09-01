---
type: Observation
title: A filler declaration records what you have not looked at, not what is not there
description: Naming an unidentified run `Filler` and moving on is right, and it quietly converts an open question into a settled-looking one. Three times in one reconstruction a filler run sitting beside a newly added field turned out to BE a field, each found by an instruction read long after the filler was written. Re-read every filler adjacent to anything new.
tags: [reconstruction, measurement, dgroup, verification, naming]
measured_on: unrecorded
timestamp: 2026-08-29T00:00:00Z
---

# A filler declaration records what you have not looked at, not what is not there

You cannot name a run of bytes nothing has referenced, so you declare it as filler with its address and its size and you move on. That is correct practice -- inventing a name for unmeasured bytes is worse. But the declaration then reads like a finding, and it is not one.

**A filler is a record of where you stopped looking.** It survives in the source looking exactly like a measured field, and nothing about it says "re-check me when something changes nearby".

## Three, in one reconstruction, all beside something new

* A one-byte filler between a newly widened flag array and a published pointer turned out to be the **channel count** -- the number that makes the array in front of it interpretable. Read from a store in a routine transcribed twelve sessions after the filler was declared.
* A four-byte filler after a tick counter turned out to be a **second published entry point**, holding the address of a stub that takes its argument in a register where the first takes it on the stack. The filler was exactly the right size and exactly the wrong name.
* Two four-byte fillers in a loader's constants turned out to be **magic strings** the file's own address map had already named, in a comment, before anyone declared them.

The pattern in all three: **a filler run immediately adjacent to a field that the version under reconstruction ADDED.** New fields arrive next to each other; a filler beside one is the next candidate, not background.

## What to do

* Grep the sources for filler declarations whenever a new field lands next to one.
* Prefer a filler with a stated WIDTH over one with a guessed name, and state in the note what would identify it -- "an instruction that names this address" is usually enough to make the search obvious later.
* When the layout comparison comes out exact except for one run, look at the fillers before looking anywhere else.

## See also

* [A typed constant nothing reads is invisible to every comparison that follows an instruction](../dead-data-has-no-witness/observation.md)
* [A compare tool's number is plausible, and it is wrong](../plausible-and-wrong/observation.md)
