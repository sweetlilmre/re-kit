---
type: Observation
title: Documentation defects are invisible to every check and visible on the first read-through
description: A comment cannot fail a build, a comparison or a self-check, so a documentation pass ends with every instrument green and no evidence about the thing it was for. The defects are real and they have shapes -- the right words in the wrong place, a rule stated as complete when it is not, an explanation that assumes something said three units away -- and the only instrument that finds them is a person following the path a reader would take.
tags: [documentation, verification, process, reverse-engineering]
measured_on: unrecorded
timestamp: 2026-08-29T00:00:00Z
---

# Documentation defects are invisible to every check and visible on the first read-through

A reconstruction accumulates instruments, and by the end almost everything has one. Bytes have a comparison. Sizes have a map. Layout has a walk. Addresses in comments can be checked against a linker map. **Explanation has nothing**, and after a long documentation pass that shows up as a peculiar kind of silence: every tool reports success and not one of them has said anything about the work that was actually done.

The defects are there. Three found in one session, each after the tools had gone green:

* **A stripper rule matched an address prefix only at the start of a comment.** The tree's usual shape is a rule of dashes and then the address on the line below, so **every routine's headline kept its address** — the first line of prose a reader meets, in every block comment in the file. The tool reported success, the code was untouched, the byte comparison passed.
* **The most important line in a subsystem had the wrong comment above it.** The line where the music signals the demo — the reason the program exists — was introduced by a paragraph about the compiler's `with` implementation. Every word of it true, none of it what a reader arriving there needs.
* **A hardware note was true and presented as complete.** A port map described four ports as the way registers are reached; a second window existed two hundred lines away. A reader forms a whole-seeming model and later meets code that contradicts it.

## The three shapes are worth naming

* **Right words, wrong place.** The explanation exists somewhere in the tree. It is not where the reader is when they need it.
* **True but closed.** A rule stated without its exceptions is worse than no rule, because it licenses confident wrong inferences. The reader does not go looking for a second window they have been told does not exist.
* **Assumes a neighbour.** A passage that only makes sense after something said in another unit, with nothing pointing there.

None of the three is a wrong statement. That is exactly why nothing catches them: a checker looks for false, and these are all true.

## The method is to walk, not to review

Reviewing a file means reading what is there and asking whether it is correct. **Walking means picking a question a reader would actually arrive with and following it across whatever files it crosses**, in order, without using anything you already know.

Three questions of that kind were enough here — how does a note become a sound, how does the caller talk to this, where does the hardware get touched. Each crossed three or four units, and each found something in its first pass.

Two rules make it work:

* **Write the paths down first.** An entry document that names two or three reading orders is worth having for its own sake, and it also turns "read the docs" into a repeatable procedure with a beginning and an end.
* **Suspect the files you have already finished.** Two of the three defects above were in files marked done, and one was introduced BY the documentation pass itself — the port map that misleads by omission did not exist before the pass that wrote it. **A documentation pass creates defects of exactly the kind it is looking for**, and finishing a file is the moment it becomes invisible.

## And the count that measures the pass will lie

The obvious progress measure — routines with no comment above them — went from 81 to 75 across a sweep that materially documented four subsystems. It counts every routine covered by a GROUP header as undocumented, so satisfying it means writing "sets the flag" above `Flag := f` scores of times.

A metric is useful while it points at clusters worth investigating, and it becomes an argument for making the tree worse the moment the clusters are gone. **Retire it then, rather than driving it to zero.**

## See also

* [The addresses written in comments are the only claims nothing checks](../comments-are-unchecked-claims/observation.md)
* [A measurement tool reads whatever is on disk, and a failed build leaves the last good answer there](../artefact-outlives-its-source/observation.md)
* [Every declared routine matches, and the rebuild still behaves differently](../verifier-blind-to-absence/observation.md)
* [A name is a claim, and it should be no stronger than the evidence that produced it](../name-carries-its-evidence/observation.md)
