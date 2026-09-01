---
type: Observation
title: A harness can never match the original's runtime call addresses, and the coverage number quietly pays for it
description: Building a test harness around a reconstructed unit puts a different main program ahead of the runtime, so every far call into the runtime differs in its segment word by construction. Most of those 4-byte differences a coverage walk absorbs; where they cluster it cannot, and the walk reports them as a code defect. Measure the deltas before treating any of it as reconstruction work.
tags: [reconstruction, measurement, linking, turbo-pascal, dos, coverage, harness, blind-spot]
timestamp: 2026-08-26T00:00:00Z
---

# A harness can never match the original's runtime call addresses, and the coverage number quietly pays for it

A reconstruction usually cannot run the original's main program yet, so each unit gets a **harness**: a small main that calls one scene and exits. The harness is not the original main, so it is not the same size, so everything linked after it sits at a different paragraph -- including the runtime. Every `9A` far call into the runtime then differs from the original's in its segment word, in every harness, forever.

This is not a defect and no amount of source work removes it.

## What it looks like

Tabulate the far calls rather than reading spans. For each differing `9A`, take our operand minus the original's:

    part 001:  76 far call(s), 1 identical
        offset   +13  segment   +18   x30
        offset    +0  segment   +18   x17
        offset   +33  segment   +18   x13
    part 004:  57 far call(s), 1 identical
        offset  +194  segment   +22   x32
        offset    +0  segment   +22   x22

**One segment delta dominates each target.** That single number is the size difference of everything ahead of the runtime, in paragraphs -- +18 paragraphs is 288 bytes of extra main program. It is the harness, and it is the same for every call in the target.

**The offset deltas are a second, independent story.** A delta of 0 means that runtime routine sits at the same offset inside the runtime; +104 means it sits 104 bytes further in, so a *different amount or order of runtime* was linked. That one is worth chasing when byte-exactness is the goal, and it is a linking question, not a source question.

## Why the coverage number understates it

A walk that tolerates small holes resynchronises after an isolated 4-byte difference, so most of these vanish from the span list. Where far calls cluster -- three in twenty bytes -- there is nothing left to resynchronise on and the walk reports the whole run as unaligned.

The consequence is a number that looks like reconstruction work and is not:

    part 001:  76 differing far calls  ->   2 bytes of spans
    part 004:  57 differing far calls  ->  55 bytes of spans

Part 004 is not eight hundred percent worse reconstructed than part 001. Its far calls are simply denser. **Ranking targets by their span totals ranks them by call density.**

## What to do

Separate the two populations before deciding anything. Classify each span by whether a `9A` at the same position in both images encloses it and only the operand differs; report those apart from the rest. On this target that turned a "119 bytes of work remaining" reading into 19, and the 19 were real.

Two traps in doing the classification itself, both of which produced wrong numbers first:

- **Locating a whole segment and indexing into it does not work** on a large segment. A best-global-alignment score can land the window in another routine, and then every span in that segment is compared against the wrong bytes -- runtime call targets come back as ordinary code differences. Anchor each span the way the walk does, with a window ENDING at the span.
- **A one-byte span inside a five-byte far call decodes as garbage** if you disassemble from the span's first byte. Walk back up to four bytes looking for the `9A`.

## Blind spot

**This says nothing about whether the reconstruction is right.** It only removes a class of difference from the count. A harness that calls the wrong routine with the wrong arguments still scores well on a walk, because the walk reads the image and not the behaviour.

**And the two deltas can hide each other.** A target whose offset deltas are all zero has a faithful runtime layout and only a harness-sized shift; one with a recurring +104 has something extra linked in early. Reporting only the segment delta loses that, and the offset delta is the one that a byte-exact rebuild has to close.

## Cost

One pass over each image collecting `9A` sites, grouped by delta pair.

## Example

Psycho Neurosis, seven reconstructed parts. 558 far calls differ across five of them and 1 is identical in the whole set; the segment deltas are +18, +22, +30, +40 paragraphs -- one per target, matching each harness's size. The parts that rebuild BYTE-IDENTICAL in the same repository are the three that are whole programs rather than harnesses, which is the same observation from the other side. [1]

# Citations

[1] `spans.toml`, `kit/tools/pascal/spans.py`, and the far-call tabulation in the psycho repository, 26 Aug 2026.
