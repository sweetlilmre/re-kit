---
type: Observation
title: A variable nothing reads can still be named, by matching a sibling's declaration order
description: Reverse engineering names a variable from what uses it, so a variable with no readers looks unnameable and gets a filler. But a compiler emits per-routine statics in source declaration order, and that order survives into the image. Line the run up against a sibling implementation's declaration block and the dead ones are named by their position between the live ones.
tags: [reverse-engineering, naming, dgroup, measurement, evidence]
timestamp: 2026-08-29T00:00:00Z
---

# A variable nothing reads can still be named, by matching a sibling's declaration order

Every naming technique in a reconstruction runs through USE. A byte is named by the instruction that reads it, the value it is compared against, the routine it is passed to. That works until you meet a variable nothing reads -- and those are common, because compilers emit storage for a declaration whether or not anything touches it. The reconstruction transcribes the space correctly, cannot name it, and writes a filler.

**The space is still ordered, and the order is evidence.** A compiler that emits per-routine static storage lays it down in source declaration order, and that order survives into the image intact. So a run of unnamed bytes is not an unordered blob: it is a *sequence*, and a sequence can be matched against a sibling implementation's declaration block even when nothing in either program reads the members.

## What it looks like

Measured, on a 1994 player with an earlier release of the same codebase available as source. One routine's block of compiler-emitted statics, with four regions the reconstruction had carried as fillers for months:

| the image's run | the sibling's declaration |
|---|---|
| `Word` -- no reader | `incr : INTEGER` |
| `Word` -- one writer, three readers | `OTempoCt : WORD` |
| pointer, pointer | `Can : PCanal`, `Raw : PModRawChan` |
| `LongInt` -- no reader | `NoteHzFreq : LONGINT` |
| `Word` -- a loop index | `i : WORD` |
| `Word` -- no reader | `j : WORD` |
| `Word`, `LongInt` | `t : WORD`, `step : LONGINT` |
| `Word` -- no reader | `FBCount : WORD` |
| `Byte` | `NumChannels : BYTE` |

Eleven declarations, every width matching in sequence with no slack anywhere. Four of them named, and none of the four had a reader in either program.

**The dead ones were dead in the sibling too.** Each of `incr`, `NoteHzFreq`, `j` and `FBCount` occurs exactly once in the whole of the sibling's unit -- its own declaration. They are leftovers of an earlier version of the routine, and they were already leftovers when that source was written. That is not a coincidence to explain away; **it is why the technique was needed.** A variable that had a reader would have been named years ago by the ordinary method.

## Why it is sound, and where it stops being sound

The strength is that the match is *rigid*. A run of eleven declarations with no spare bytes has no freedom in it: get one width wrong and every field after it is displaced, and the mismatch is visible immediately. That is a much stronger constraint than naming one isolated field from a plausible-looking neighbour.

It stops being sound at exactly the point the rigidity goes:

* **A short run proves nothing.** Two `Word`s in a row match almost any two `Word`s. Anchor the run at both ends on something with a reader, and count the members.
* **The versions must be close enough that the routine did not change shape.** A declaration added or removed in the newer version breaks the alignment, and a run that "almost" matches has been fitted rather than measured.
* **The name is the sibling's, and it should say so** at the point of use. It is a real source and a different one from an instruction. See [name-carries-its-evidence](../name-carries-its-evidence/observation.md).
* **Order is not layout.** This says which declaration a region belongs to. It does not independently confirm the widths -- the byte-exactness of the surrounding code does that, and the two have to agree before either is worth trusting.

## The habit worth taking from it

When a region has no reader, stop asking what reads it and ask **what it sits between**. Take the nearest named variable on each side, and match the whole run rather than the gap. The unnamed bytes are the ones the ordinary method will never reach, so they are exactly where a second, order-based source of evidence earns its keep.

The corollary is worth stating too: **when the search comes back empty, record that.** In the same session the same technique was tried on another unit whose sibling declares one typed constant in the entire file -- nothing to match against. Written down at the declaration, that stops the search being run a second time.

## See also

* [name-carries-its-evidence](../name-carries-its-evidence/observation.md)
* [dead-data-has-no-witness](../dead-data-has-no-witness/observation.md)
* [filler-is-not-a-finding](../filler-is-not-a-finding/observation.md)
* [length-sequence-names-the-order](../length-sequence-names-the-order/observation.md)
* [dgroup-order-reverses-uses](../dgroup-order-reverses-uses/observation.md)
