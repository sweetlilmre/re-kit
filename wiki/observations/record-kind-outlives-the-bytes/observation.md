---
type: Observation
title: A container's record structure is evidence about the source that a byte comparison cannot give, and identical bytes can still be the wrong reconstruction
description: Two object files can hold a byte-identical code segment and still differ in which records carry it. The record kind says what the source SAID -- a repeat, an include, a group -- and that survives in the container after every byte of output has been matched. Measured on a 35,716-byte hand-written module reassembled to byte-identity where the object still differed by seven records, each naming a source construct the reconstruction had got wrong.
tags: [verification, measurement, reconstruction, object-file, omf, hand-assembler]
measured_on: a 16-bit assembler module, one segment, 38 data records
timestamp: 2026-09-04T00:00:00Z
---

# A container's record structure is evidence about the source that a byte comparison cannot give, and identical bytes can still be the wrong reconstruction

Byte-identity of the payload is usually the top of the ladder. For a module inside a container — an object file, an archive member, a linked unit — it is not, and the gap above it is informative rather than cosmetic.

The container records **how the source was written**, not just what it produced.

## What the records knew

A hand-written 16-bit assembler module of 35,716 bytes was reconstructed from its object file and reassembled with the same assembler until the code segment matched byte for byte. At that point the object files still differed by seven records, and every one of them named a source construct the reconstruction had wrong:

- **`GRPDEF` present in ours, absent in the original.** The reconstruction declared a `GROUP`; the original's segment name had been read as a group when it was the segment's **class**. The `SEGDEF`'s own `class_idx` said so. Same bytes; a different declaration.

- **`LIDATA` 2 in the original, 1 then 0 in ours.** `LIDATA` is repeated initialised data — how an assembler encodes `dup`. Where the original wrote `1714 dup ('$')` the reconstruction emitted 1,714 explicit `db` bytes. The segment was identical and the source was wrong.

- **`COMENT` 11 against 5.** The six missing ones are dependency stamps: the original was split across six include files, and their **names** are in the object even though not one byte of output remembers which file it came from.

The second is the sharpest. One of those two repeats sat inside a region a flow trace had classified as code, because 70 zero bytes decode as a legal instruction and nothing stops the walk. It was emitted as 35 instructions. The bytes were right, every byte comparison passed, and the record kind was the only witness that the source had said something else entirely.

## Why this is not pedantry

A reconstruction's purpose is a **source** somebody can read and change. Bytes are how it is checked, not what it is for. Three of these differences would have left the source misleading in ways no future check could catch:

- a `db` run where a `dup` belongs hides the intent and breaks the moment the count changes,
- a group where a class belongs is a linker-visible claim about layout,
- one file where six belong loses the module's whole structure.

And it cuts the other way too: the records are **free evidence**. The include names were recoverable when nothing else in the artefact could have named them. The `dup` counts and their repeated value were recoverable exactly. A reconstruction that stops at byte-identity leaves that on the table.

## The rule

Compare the container's record census as a separate measurement from the payload, and treat a record-kind difference as a finding about the source rather than noise about the encoder. Where the two disagree — bytes identical, records not — the records are the stronger evidence, because they describe the input and the bytes only describe the output.

Do not infer the source construct from the payload instead: a run of equal bytes is not proof of a `dup`, and putting one where the original had none is the same error in the other direction. The record kind is the witness; the bytes cannot arbitrate it.

## Blind spot

The census tells you a construct exists, never where its content sat. The six include names were recoverable and the **split between them was not** — no record maps output bytes to the file that contributed them. So this evidence bounds the source's shape without determining it, and a reconstruction that matched all eleven records could still divide the content among those six files completely differently from the original. Say which of the two you have measured.

## Related

- [[byte-identity-is-not-correctness]] — the same ceiling from the other side: there, matching bytes hid a wrong subscript; here, matching bytes hide a wrong construct.
- [[skipped-record-reads-as-zero]] — what happens when the reader ignores those records instead of reading them.
- [[an-addend-can-be-a-size]] — another case of the container carrying what the payload cannot.
