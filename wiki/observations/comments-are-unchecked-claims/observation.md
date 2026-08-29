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

**Its limit should be stated wherever it is used:** a run of stale addresses copied forward *together* stays internally consistent and passes. This finds the common failure — one comment updated and its neighbours not — and it cannot find a whole block that drifted as a unit. Anchors settle those, and anchors come from instructions.

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

* [name-carries-its-evidence](../name-carries-its-evidence/observation.md)
* [artefact-outlives-its-source](../artefact-outlives-its-source/observation.md)
* [verifier-blind-to-absence](../verifier-blind-to-absence/observation.md)
* [dead-data-has-no-witness](../dead-data-has-no-witness/observation.md)
* [two-names-one-address](../two-names-one-address/observation.md)
