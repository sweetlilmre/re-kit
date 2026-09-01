---
type: Observation
title: An uninitialised variable has no witness anywhere, and link order is the only thing that brackets it
description: A typed constant is in the image, so a comparison sees it. A public symbol is in the linker map, so an absolute check names it. A variable that is neither holds no bytes and carries no symbol, so nothing in a reconstruction can reach its address. Link order can still bracket it -- every unit's variables sit above those of every unit linked before it -- which detects a stale address without computing the right one.
tags: [reverse-engineering, dgroup, verification, measurement, naming]
measured_on: unrecorded
timestamp: 2026-08-29T00:00:00Z
---

# An uninitialised variable has no witness anywhere, and link order is the only thing that brackets it

A reconstruction's address claims have very different standing, and the notation hides the difference. `{ DS:$0310 }` looks the same whichever of these it is:

| what it names | what can check it |
|---|---|
| a typed constant | the image -- the bytes are there, and a data comparison walks them |
| a public variable | the linker map -- it names the symbol and its offset |
| **a private variable** | **nothing** |

The third holds no bytes, so no comparison sees it, and carries no symbol, so no map names it. On one corpus of 289 claims, **nine were in that position** — and they were not marked in any way that distinguished them from the 280 that were checkable.

Worse, they can be *internally* consistent and still wrong together. Seven of the nine were a run of arrays whose declared addresses agreed with each other exactly: a start, then +128, +128, +128, +32, +128, +32, landing on all seven. A relative check passes that run without complaint, because a block that moved as a whole moved consistently.

## Link order brackets what nothing else reaches

The compiler lays each unit's variables above the variables of every unit linked before it. So any unit with a *public* variable is an anchor, and every unanchored unit is bracketed by the anchors either side of it in link order.

Measured, on eight anchors with no exception:

    position  0  $0d16      9  $461a     20  $5d08
              2  $0ef6     17  $4920     24  $5d38
              7  $12b8               27  $665c

The unit holding those seven arrays links at position **19**, between `$4920` and `$5d08`. Its declared block began at `$371a`. That is not a discrepancy to weigh — it is outside the bracket, so the claim is impossible.

A second unit failed the same test: it links at position 4 and claims an address below the anchor at position 2.

## Detecting is not correcting, and the difference is worth keeping

The bracket says the address is wrong. It does not say what the address is. Computing that needs every intervening unit's variable sizes, and on this corpus one intervening unit had nine declarations the transcription could not size — a record, an object, a type from elsewhere.

So the addresses were **left as they were and marked**, with the reasoning written beside them. That is deliberate:

* **A wrong number that is admitted is worth more than a wrong number that is not.** The first stops the next reader; the second recruits them.
* **Replacing it with a computed guess would destroy the evidence** that it is wrong, and produce a claim with worse provenance than the one it replaced — a guess formatted exactly like a measurement.

## The habit

* **Classify address claims by what could falsify them**, not by how they are written. Image, map, neither. The third class is small and it is where the silent errors live.
* **Look for a structural invariant when no instrument reaches a value.** Ordering, adjacency and containment are cheap, they need no build, and they are enough to detect an error even when they cannot repair it.
* **Say "stale, and I cannot compute the right one" in the source.** The alternative is not honesty deferred; it is a wrong number that keeps its authority.

## See also

* [The addresses written in comments are the only claims nothing checks](../comments-are-unchecked-claims/observation.md)
* [A name is a claim, and it should be no stronger than the evidence that produced it](../name-carries-its-evidence/observation.md)
* [A typed constant nothing reads is invisible to every comparison that follows an instruction](../dead-data-has-no-witness/observation.md)
* [The data segment is laid out in reverse of the uses clause](../dgroup-order-reverses-uses/observation.md)
