---
type: Observation
title: A field nothing in the image writes is an input, not a switch that was never wired up
description: Search a binary for writes to a variable, find none, and the conclusion "nothing can set it" only follows if the binary is the whole system. A field inside a structure the program PUBLISHES for other programs is written from outside, and no-writer-inside is exactly what that looks like. The test is the address -- convert it to an offset within every published structure before concluding anything.
tags: [reverse-engineering, dgroup, naming, verification, measurement]
timestamp: 2026-08-29T00:00:00Z
---

# A field nothing in the image writes is an input, not a switch that was never wired up

You find a byte the program reads in three places and writes nowhere. You check the search twice -- every encoding of every store, the whole image -- and it holds. The natural conclusion is that the flag is vestigial: wired up and never given a way to be turned on.

**That conclusion needs the binary to be the whole system, and it usually is not.** A program that publishes a structure for other programs to read and write has fields nobody inside it ever stores to. Those are its INPUTS. No writer in the image is not evidence of a dead switch; for an input it is the *expected* observation.

## The test is one subtraction

Before concluding anything about a variable with no writer, take its address and subtract the base of every structure the program publishes. If it lands inside one, it is a field of that structure and the question is answered.

Measured, on a 16-bit DOS player that publishes a 768-byte control block over a software interrupt:

    flag at DS:$4821, control block at DS:$461a
    $4821 - $461a = $207

$207 sits one byte after a master-volume field and four after a `SeekWant`/`SeekPos`/`SeekRow` trio -- three more fields the program reads and never writes, all of them plainly requests from a client. The flag is the fourth: set it, and the player finishes without playing anything and without complaining.

## Why the wrong reading survives

Because it explains the observation completely and predicts nothing. "Vestigial" accounts for every byte you have seen and never comes back to be tested. It also *feels* measured -- the search really was exhaustive, and the note that records it can be scrupulous about the evidence while being wrong about what the evidence means.

Two other costs, both real here:

* The flag was declared as a loose variable in whichever unit seemed plausible. That put it between two other units' data and moved **every variable after it**, which showed up as sixty-plus wrong operands in units that had no defect at all.
* Being in the wrong record, it could never be named. In the right one, its neighbours name it.

## Related shapes

* A field written once at startup and read by nothing is the mirror image -- an OUTPUT, and the same subtraction finds it.
* A vector, a callback pointer, or a procedural-type variable assigned only by an external installer behaves identically.
* Inside a published structure, **a run of consecutive fields with no writer is a request block**, and identifying one member usually names the rest.

## See also

* [filler-is-not-a-finding](../filler-is-not-a-finding/observation.md)
* [absence-reads-as-zero](../absence-reads-as-zero/observation.md)
* [plausible-and-wrong](../plausible-and-wrong/observation.md)
