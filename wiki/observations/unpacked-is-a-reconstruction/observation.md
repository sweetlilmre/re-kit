---
type: Observation
title: An unpacked binary is the unpacker's reconstruction, and only its load image is evidence
description: Unpack a compressed executable and you get a file, not an artefact. The packer discarded the header fields and the relocation encoding it did not need, so the unpacker had to invent them -- and a rebuild that matches the program perfectly will still differ there. Compare the load image, and prove the rest by re-packing.
tags: [reverse-engineering, comparison, verification, tooling, reconstruction, linking]
timestamp: 2026-08-29T00:00:00Z
---

# An unpacked binary is the unpacker's reconstruction, and only its load image is evidence

The target ships compressed, so the first move is to unpack it and reconstruct against the result. That result is a file with an MZ header, a relocation table and a load image, and it is easy to treat all three as the original's.

**Only the load image is.** A packer keeps what it needs to reproduce the program in memory and discards the rest, so anything it discarded, the unpacker had to make up.

Two places this bites, both measured on one 16-bit DOS target whose rebuild matched the program exactly:

* **Header fields the packer overwrote.** A packed executable's own header describes the *stub*, not the program, so fields like the maximum allocation are gone. The unpacker here hardcodes `0xFFFF`, with a comment saying the original "is kept nowhere". A real linker emits whatever the source's memory directive asked for -- and that value is right and will never match.
* **The relocation table's ENCODING.** A relocation is a linear address, but MZ stores it as segment:offset, and the split is not unique: `(1764, 0)` and `(4, 110)` are the same place. Packers re-encode relocations in their own compact form -- here a stream of byte deltas -- so the unpacker rebuilds an MZ table from scratch, using whatever normalisation its decoder loop falls into. This one keeps segment 0 until the offset would overflow; the linker normalises to the nearest paragraph. **843 identical addresses, 771 written differently.**

## The test that settles it

Do not chase those differences. **Re-pack your rebuild with the original's own stub and compare against the file that shipped.**

That comparison is the real one in both directions. It is the artefact that actually existed, and it is strictly stronger than the unpacked comparison: if your image or your relocation SET differed in anything the packed format preserves, the packed output could not match. Ours came out byte-identical at 36,008 bytes with the unpacked file still differing in the two ways above, which is the whole argument in one measurement.

## How to hold the target from the start

* Compare the load image and the linear relocation SET. Sort the relocations to linear addresses before comparing them; do not compare the table bytes.
* Treat the unpacked file's header as annotation, not evidence -- read the entry point and stack out of it, and expect nothing else to match.
* Say so in the notes beside the unpacked artefact, because the next person will see a file that is 99.99% identical and reasonably try to close the gap.

## The general shape

Anything between the shipped bytes and the bytes you compare is a transform with its own conventions: a self-extracting archive, an overlay loader, an installer that relocates, a decryptor. The rule is the same -- **compare on the far side of the transform, and prove the near side by re-applying it.**

## See also

* [file-bigger-than-image](../file-bigger-than-image/observation.md)
* [instruments-have-an-order](../instruments-have-an-order/observation.md)
