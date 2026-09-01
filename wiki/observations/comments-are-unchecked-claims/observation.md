---
type: Observation
title: The addresses written in comments are the only claims nothing checks
description: A reconstruction records where each variable lives by writing the address beside the declaration, and those comments become the map everybody reads. The compiler never sees them, no comparison reads them, and a byte-exact rebuild is silent about them -- so an address carried forward from a previous version survives every instrument and goes on being quoted. They can be checked against each other without linking, and a checker that does it must model the compiler's padding or it invents findings instead.
tags: [tooling, verification, documentation, dgroup, measurement]
timestamp: 2026-08-29T00:00:00Z
---

# The addresses written in comments are the only claims nothing checks

A byte-exact reconstruction is checked from every angle. Code is checked by the comparison, sizes by the unit map, layout by the data-segment walk, order by the link-order model. **The prose is checked by nothing**, and the prose is where the addresses live:

    OutPtr : Pointer = nil;   { DS:$0310 }

That comment is a factual claim about the target, it is the form in which everything located so far is recorded, and it is the map the next person reads. Nothing in the toolchain can disagree with it. Edit it to a random number and every instrument still passes.

So these claims rot in a specific way: a variable moves between versions, or a declaration is inserted ahead of it, and the comment stays. One corpus carried **526 such claims with no check of any kind.** Six were eventually found stale by hand, two of them naming an address that by then belonged to a *different variable* — which is worse than no comment, because it reads as corroboration.

## They can be checked against each other, without linking

An absolute check needs each unit's base, a map, and a link. A relative one needs nothing: read the addresses as a **sequence** and ask whether consecutive claims are separated by the size of what is declared between them.

That is cheap, needs no build, and on the corpus above it found nine disagreements the whole rest of the toolchain was blind to — including two runs where the declarations and the comments disagreed about the *order* of variables.

**Its limit should be stated wherever it is used:** a run of stale addresses copied forward *together* stays internally consistent and passes. This finds the common failure — one comment updated and its neighbours not — and it cannot find a whole block that drifted as a unit.

## That limit turned out to be where nearly all of them were

The relative check found nine. Then the same corpus was checked against the **linker's own map**, which publishes each unit's interface symbols with their offsets — and on a byte-exact reconstruction the linker's address IS the original's.

**223 of 250 checkable claims disagreed.** Not 223 slips: whole blocks carried forward from the previous version of the target, each unit off by its own constant, every one of them internally consistent and therefore invisible to the relative pass. The limitation was written down before anybody knew it described almost the entire corpus.

The lesson is not that the relative check is weak. It is that **a check's stated blind spot is a prediction about where the errors are**, and the cheapest next move after writing one down is to go and look there.

## Two sources, neither subsuming the other

* **The map names only what a unit exports.** Implementation-section declarations are invisible to it and get the relative check or nothing.
* **The map cannot attribute a duplicated name.** Two units may each export a `DMAStop`, and the map lists both addresses under one name — so it carries no answer and must drop it. Keeping the first silently, which is what the obvious dictionary code does, produced twelve confident "the linker says" lines for the wrong variable.
* **The relative chain settles exactly those.** It knows nothing absolutely, but once its neighbours are anchored it computes the one address that fits between them, duplicated name or not.

So the order is: anchor absolutely, then chain relatively through what the anchors left. Run either alone and a quarter of the corpus stays wrong.

## The worst case is prose that argues from the address

A stale number in a `{ DS:$xxxx }` comment is a wrong label. A stale number reasoned *from* is worse:

> "$02cd sits between two interface globals, and a unit's implementation declarations all come after its interface ones, so a private declaration cannot land there."

The argument is sound, the conclusion is correct, and the address is the previous version's — the variable is at `$02d3`. **Prose that argues from an address reads as corroboration for it**, so it survives review better than the bare comment would, and no fixer can touch it: rewriting a declaration's address leaves the paragraph beside it still reasoning from the old one. On this corpus 1,228 such mentions remained after 220 declarations were corrected. A tool that rewrites addresses should count what it could not reach and say so.

## A fixer that touches prose needs a much higher bar than one that touches declarations

A declaration has one address and one owner. A sentence has neither, and every rule for pairing a name with a number in prose has a counter-example. Four attempts on one corpus:

| the rule | what it did |
|---|---|
| nearest address to each name | rewrote `LoopMod ... is $02c8` with ForceLoopMod's address — English parallelism puts the nearer name first |
| nothing but punctuation between them | safe, and blind to every sentence with a verb in it |
| names and addresses must alternate | good, but a name between two addresses claims both |
| **only text inside `{ }` is prose** | removed 49 false pairings at a stroke |

The last one is the load-bearing rule and it was found last. `if CanalPtr^.Period > $1FFF then` is a line of code; `$1FFF` is a clamp the program compares against, and `CanalPtr` is right beside it. Scanning whole lines put those two together. **Forty-nine of fifty-five candidates were constants in live expressions**, and the only reason none was rewritten is that an earlier, blunter rule had happened to reject them for an unrelated reason.

Three narrower rules came out of reading the output rather than trusting it:

* **Every name competes, including ones the checker cannot resolve.** A name declared in two units has no answer in the map — but it still owns the address beside it, and letting a further-away resolvable name win writes that name's value onto its neighbour's number.
* **An assigned number is a value.** `StepVal := $1000` says what the variable holds.
* **A range is a claim about a span.** Rewriting either end of `$0018..$001d` leaves a sentence that says nothing.

**And some mentions can never be paired.** A note whose subject is an address, that then names a different variable — `{ DS:$0c74 -- the third duplicated global, after AltMode ... }` — reads to any rule as `AltMode = $0c74`. The fix is not a cleverer rule; it is to write the subject's name next to its address, so the sentence says what it means. On this corpus 165 mentions name no variable at all, and no rule can attribute them.

## A checker that does not model the layout manufactures findings

The first version of that checker reported **28 disagreements. Nineteen were its own.**

| what it did not model | what it reported |
|---|---|
| the compiler word-aligns anything wider than a byte | 12 alignment pads, as stale addresses |
| typed constants and plain variables occupy separate areas | 6 section crossings, as huge jumps |
| a string type whose name begins with `P` is not a pointer | 2 string constants, off by 76 |
| an `absolute` declaration occupies no space of its own | 1, off by one |
| an unknown type's ALIGNMENT is unknown too | 2 enumerations at odd addresses |

Every one of those looked exactly like a real finding, and the padding rule was **stated outright in the source's own comments, beside the declarations being flagged**. The manufactured findings are indistinguishable from real ones until each is opened by hand, and the cost of that is paid by the person who trusts the tool.

The last row is the one worth generalising. Faced with a name it could not size, the checker assumed the alignment anyway — reasoning that aggregates start on even addresses. That is true of records and false of small enumerations, and **the name does not say which**. Unknown has to mean unknown: report it as unverifiable and break the chain, rather than let a guess masquerade as a measurement.

## The habit

* **Anything a reconstruction records only in prose is unverified by construction.** Ask, for each such class of claim, what would falsify it — and if the answer is "someone reading carefully", build the check.
* **A relative check is often available where an absolute one is not**, and is worth far more than its weakness suggests, because the failure it catches is the common one.
* **Trust the claim going forward even when it disagrees.** Resetting the cursor to what the comment says makes one bad address report once; computing forward from the correct value drags every later claim into the report and buries the second real error.
* **Validate the checker against known-good input before believing its output**, and expect the first run to be mostly its own bugs.

## See also

* [A name is a claim, and it should be no stronger than the evidence that produced it](../name-carries-its-evidence/observation.md)
* [A measurement tool reads whatever is on disk, and a failed build leaves the last good answer there](../artefact-outlives-its-source/observation.md)
* [Every declared routine matches, and the rebuild still behaves differently](../verifier-blind-to-absence/observation.md)
* [A typed constant nothing reads is invisible to every comparison that follows an instruction](../dead-data-has-no-witness/observation.md)
* [The same bytes answer to two different addresses](../two-names-one-address/observation.md)
