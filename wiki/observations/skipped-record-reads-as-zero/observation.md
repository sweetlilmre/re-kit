---
type: Observation
title: A reader that skips a record type it does not decode returns the right length with holes in it, and shifts everything positioned after it
description: An unknown record can be stepped over safely -- that is what a length-prefixed format is for -- but only when it carries no content. A record that carries content and is skipped costs twice. Its bytes come back as zero, and any later record positioned RELATIVE to the last one decoded is placed against a stale base. Measured on an Intel OMF reader that skipped LIDATA, where two records covered 1,784 bytes of a 35,716-byte segment and every fixup after them was misplaced.
tags: [tooling, verification, measurement, blind-spot, object-format, silent-failure]
measured_on: a 16-bit object module, one segment, 38 data records and 989 fixups
timestamp: 2026-09-04T00:00:00Z
---

# A reader that skips a record type it does not decode returns the right length with holes in it, and shifts everything positioned after it

Length-prefixed record formats are designed to be read partially. Each record says how long it is, so a reader can decode the three types it cares about and step over the rest. That is a genuine property of the format and it is why partial readers are normal and correct.

It stops being correct the moment a skipped record **carries content**.

## The two costs, and both are silent

An OMF object module holds its initialised bytes in `LEDATA` records. It also holds them in `LIDATA` records — *repeated* data, which is how an assembler encodes a `dup`. A reader that decodes `LEDATA` and skips `LIDATA` fails twice:

1. **The bytes come back as zero.** The reader allocates the segment to its declared length and fills what it decoded, so the image is exactly the right size and looks complete. Where a `LIDATA` record belonged there is a hole. Nothing in the output distinguishes a hole from a region that is genuinely zero — and initialised data that repeats is very often a repeat of zero, which is precisely why the hole looks plausible.

2. **Everything positioned relatively is displaced.** A `FIXUPP` record's offset is relative to *the data record it follows*. A reader that tracks "the last record I decoded" rather than "the last record that existed" places every fixup after a skipped one against a stale base. The fixup set is then wrong by however much the skipped record covered, and it is wrong for the rest of the module.

The second cost is the worse one, because a displaced fixup mask does not read as absent. It reads as a *different* set of bytes being excused — plausible in shape, wrong in position, and applied to exactly the comparison that was supposed to be strict.

## Measured

An OMF reader written to answer one question — *which bytes of this module are relocations, so a byte comparison can excuse them* — decoded `THEADR`, `LNAMES`, `SEGDEF`, `LEDATA` and `FIXUPP`, and skipped the rest by length. Correct for every module it had been used on.

Given a hand-written assembler module of 35,716 bytes in one segment, it returned 35,716 bytes: the right length. Two `LIDATA` records covering 1,784 bytes came back as zero, and the fixups recorded after them were placed against the offset of the last `LEDATA`.

An independent reader written for a different purpose — mapping the module's regions, which needs each record's extent — expanded the `LIDATA` and disagreed. That is how it was found: not by a check failing, but by two readers of the same file being compared. **No check failed.** The length matched, the fixup count matched, and the comparison the reader existed to serve came out green.

## The general shape

Ask of each record type skipped: *does it place bytes, and does anything downstream measure position from it?* Those two questions separate a record that may safely be stepped over from one that may not.

- A record that neither places bytes nor is a positioning anchor — a comment, a dependency stamp, a debug directive — is safe to skip and always will be.
- A record that places bytes must be decoded or the reader must **refuse**, because its absence is indistinguishable from zeros.
- A record that anything measures relative to must be *counted* even when its content is not needed, or the reader must decode it.

The cheap version of this is a reader that keeps a set of record types it saw and did not decode, and says so in its output. A parse that announces `skipped 2 x LIDATA` invites the question; one that prints a segment length and a fixup count does not.

## Related

- [[absence-reads-as-zero]] — the same failure one layer down: a missing thing and a zero thing are the same bytes.
- [[block-past-the-end]] — a length that agrees while the content does not.
- [[two-readers-one-file]] — comparing independent parsers is what caught this, and is cheaper than proving one correct.
