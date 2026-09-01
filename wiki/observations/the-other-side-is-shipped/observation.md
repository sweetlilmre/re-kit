---
type: Observation
title: If the program has clients, look for their bindings before deciding a structure is unknowable
description: A structure the target PUBLISHES is documented somewhere, because something had to consume it. Header files, include files and language bindings shipped alongside the binary declare it field for field, in the author's own names -- and they are evidence of a completely different class from anything recoverable by disassembly. Search the distribution for the client side before writing a filler.
tags: [reverse-engineering, naming, documentation, evidence, verification]
timestamp: 2026-08-29T00:00:00Z
---

# If the program has clients, look for their bindings before deciding a structure is unknowable

A reconstruction settles into treating the binary as the only witness, and for almost everything that is correct. It is exactly wrong for one category: **anything the program publishes for other programs to use.** A structure with external consumers had to be described to those consumers, and that description is a document written by the author, in the author's names, at a level of detail no disassembly reaches.

Measured, on a 1994 DOS music player with a 768-byte control block handed out over a software interrupt. Roughly a year of the reconstruction treated 588 of those bytes as three fillers, on the reasoning -- correct, as far as it went -- that inventing names for the one structure other programs depend on is worse than admitting ignorance.

The distribution the target binary came out of ships client bindings in five languages. Each declares the whole structure:

| Artefact | Form |
|---|---|
| a C header | `struct`, with an explicit `#pragma pack(1)` |
| an assembler include | `SEGMENT AT 0` overlay |
| a Pascal unit | `RECORD` |
| a 32-bit assembler include | the same segment |
| the user documentation | prose, with the assembler layout reprinted |

They agree field for field. **256 of the unnamed bytes turned out to be a named array with a documented protocol**, 84 more got a documented split, and the remaining 248 were confirmed as genuinely reserved -- reserved in the author's declarations too, not merely unexamined in ours.

## Why this evidence is a different class

Every other name in a reconstruction is inferred. This kind is *stated*. Two consequences worth separating:

* **It names things no amount of measurement could.** A byte incremented at one site and cleared at another is fully described by those two sites and still meaningless. The array above is written by a pattern command and read by nobody in the image -- because its readers are in other programs entirely. No disassembly of this binary can recover what it is FOR.
* **It is a check on inference, in both directions.** Every offset measured from instructions matched the published layout exactly, and one inference the reconstruction had already made -- that a run of consecutive fields with no writer is a client request block -- turned out to be written as a comment in the assembler include at precisely the byte where the run starts. The independent agreement is worth more than either source alone.

## The failure mode this exposes

A correct transcription can be complete and meaningless at the same time. Three separate sites in that reconstruction handled the array perfectly -- the right instruction, the right count, the right offset -- and every one of them was annotated with a wrong explanation, because the byte-exactness of the code offered no resistance at all to a wrong story about it.

**Byte-exactness does not validate comments.** It is easy to let a passing comparison feel like confirmation of the notes attached to it, and nothing in the toolchain distinguishes a correct transcription that is understood from one that is not.

## Where to look

Before writing a filler for anything with an external consumer, search the whole distribution -- not just the source tree -- for:

* headers and include files, in every language the program advertises support for
* sample or example clients, which often use more of the interface than the docs describe
* the user manual, which frequently reprints a layout the source never states
* setup and configuration utilities, which are clients too

Note what the search does NOT find, as well. In the same two trees there was no description whatever of two on-disk file formats the program loads, and the absence is a finding: it says those names must come from elsewhere, and it stops the search from being repeated.

## Caveats

* **A binding is a sibling artefact, not this binary.** It describes the interface as the author intended it. Where it disagrees with the instructions, the instructions win -- and the disagreement is itself worth recording.
* **Check the version.** A binding for a later or earlier release may describe a layout the target does not have.
* **Names from a binding should be marked as such** at the point of use, so a later reader can tell which fields are documentation and which are inference. See [A name is a claim, and it should be no stronger than the evidence that produced it](../name-carries-its-evidence/observation.md).

## See also

* [A name is a claim, and it should be no stronger than the evidence that produced it](../name-carries-its-evidence/observation.md)
* [A field nothing in the image writes is an input, not a switch that was never wired up](../no-writer-means-input/observation.md)
* [A filler declaration records what you have not looked at, not what is not there](../filler-is-not-a-finding/observation.md)
* [A typed constant nothing reads is invisible to every comparison that follows an instruction](../dead-data-has-no-witness/observation.md)
