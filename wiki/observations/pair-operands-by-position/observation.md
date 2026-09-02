---
type: Observation
title: Pair operands by position once the lengths agree
description: When every routine in a segment is already the right length, two builds can be disassembled in parallel and their displacement operands paired by code offset. A wall of differing bytes collapses into a short list of (their address, our address) with one shift each, and the shifts name declaration order, a per-unit alignment switch, a runtime entry point or a whole missing variable. The precondition is not optional and neither is reading the profile from the lowest address up.
tags: [layout, dgroup, stack-frame, verification, tooling, measurement, pascal, reconstruction]
measured_on: unrecorded
timestamp: 2026-08-27T00:00:00Z
---

# Pair operands by position once the lengths agree

A rebuild had five programs at 100% of every user byte, every program segment byte-identical, every data image identical -- and 1,287 differing bytes in one file, 189 in another, 32 in a third. Every one of them was an operand. **The measurement that turned them into a work list was pairing operands by INSTRUCTION POSITION rather than by content.**

Disassemble the same segment from both files in parallel. Wherever an instruction at code offset X carries a memory displacement on both sides and the two differ, record `(theirs, ours)`. Collapse consecutive addresses that share a shift. What comes out is not a diff, it is a map:

    seg 108b  $A696..$A858   theirs -> ours   -2614   x68
    seg 108b  $8ED0..$8ED3   theirs -> ours    +396   x6
    seg 108b  $87C4..$87C6   theirs -> ours   +2196   x2

Sixty-eight references, one cause: one unit's whole variable block at the wrong address. The 1,287 bytes were nine such rows.

## The precondition is not optional

**Every routine in the segment has to be the right LENGTH first.** Only then is the instruction at offset X on one side the counterpart of the instruction at offset X on the other, and only then does a differing operand mean a misplaced OBJECT rather than a drifted address. Across a length defect every row below it is fiction -- the same failure mode, for the same reason, as [a masked instruction diff over a whole unit](../near-match-diff/observation.md).

So the order is: confirm the lengths, then pair the operands. If the lengths disagree, this measurement is not available yet and a content-matching pass is the tool to reach for -- it needs no precondition, at the price of not pairing everything. On the 1,287-byte case a content matcher paired 153 references, left 213 unpaired, skipped 128 as ambiguous, and two of the shifts it did report were mispairings large enough to look like whole missing arrays.

## Read the profile from the lowest address up

A variable at the wrong address moves everything above it, so the rows above the lowest defect are consequences, not causes. Fixing any of them first makes the total worse and the next reading harder.

And read the boundaries, not just the shifts. **Where the shift CHANGES is where one object ends and the next begins**, which is how a block's extent is recovered without a map:

    $0000  shift +0
    $A696  shift -2614      <-- this unit's block starts here
    $F901  shift +0         <-- and ends here

A shift of `+0` above a shifted block means the block is MISPLACED rather than mis-sized, which narrows the cause to declaration order alone.

## What the shifts turn out to be

Four causes accounted for nearly every row across seven programs.

**Declaration order is the slot order**, in DGROUP and on the stack alike -- and in most cases the correct order was already written in a comment beside the declarations, put there by an earlier reading of the binary and never checked against the code below it. A file that records `{ [BP-$0e] / [BP-$0c] }` beside `I, J : Integer` is recording that the declaration is backwards.

**A per-unit alignment switch, and a word at an ODD offset is the only witness.** Under Turbo Pascal's `$A+` a word-sized variable steps past an odd slot and takes everything below it along; under `$A-` it does not. Four units in one rebuild were measured as `$A-` this way, three of them from a single local: a `Word` at `[BP-$07]` directly below a `Byte` at `[BP-$05]` cannot be an aligned build. **The unit's DGROUP is often silent on the question** -- every block in it may be even-sized and even-based -- so the frame is the only evidence there is.

**A shift nothing else shares is often not data at all.** One row read `theirs $31EE -> ours $320D`, and those are two runtime entry points: truncation and rounding, 31 bytes apart in TP 7.00's System segment. The same pair, at the same spacing, appeared in three programs. Before assuming an operand is a variable, check whether it lands in the runtime.

**Dead space the original carries and the rebuild does not.** One unit was 2,252 bytes short of its 1994 block and nothing in the whole program referenced any of those bytes: no absolute operand, no folded array base, no immediate loaded into a register. Such a block's SIZE and POSITION are measured and its identity is not recoverable -- and it has to be declared anyway, because everything above it is at the wrong address until it is. Say in the source that the name is yours and the bytes are theirs.

## The same measurement on the stack

Restricted to negative displacements off BP, this reads a routine's locals. The shifts there name the same things -- declaration order, the alignment switch, the compiler's own hidden temporaries -- with one addition worth expecting: **two arms of an `if` emitted in the opposite order show up as a block of slots each paired against the other arm's**, all carrying nonsense shifts. That is a branch sense, not a layout defect. One such case was 115 bytes in which not one instruction differed in length or opcode: the same two blocks in the other order, each addressing the slots the other had.

## Blind spot: the floor that hid the defect it was written to find

Two of them, and the first is the section above: **pairing by code offset is sound only while the lengths already agree, and this technique cannot check its own precondition.** One wrong length shifts every pairing after it and the output looks the same either way -- a clean list of plausible shifts about the wrong operands. The agreement has to come from another instrument and be taken on its authority.

The second was in this tool rather than in the method.

The first version of this tool carried a lower bound on the addresses it would report, to cut small immediates misread as displacements. Its first validation run -- over a defect deliberately reintroduced, two long integers 12,800 bytes out of place -- reported *every displacement matches*. Both addresses were under the floor.

**A filter that hides an address range is not noise reduction, it is a blind spot**, and low DGROUP is exactly where initialised data and the first variables live. The lesson generalises past this tool: a default that quietly narrows what an instrument looks at will eventually be the reason it says a rebuild is finished. Validate an instrument by reintroducing a defect it is supposed to catch, and do it before trusting a clean report from it.
