---
type: Observation
title: The decoder names two 16-bit opcodes with their 32-bit mnemonics
description: capstone 5.0.7 in CS_MODE_16 prints 0x98 as `cwde` and 0x99 as `cdq`, where a 16-bit decode is CBW and CWD. Only the mnemonic is wrong -- every operand around them decodes correctly -- so the listing reads as plausible 386 code, and copying it into an assembler source silently adds an operand-size prefix.
tags: [disassembly, instruments, blind-spot, capstone, encoding, transcription]
timestamp: 2026-08-24T00:00:00Z
---

# The decoder names two 16-bit opcodes with their 32-bit mnemonics

You are reading a 16-bit disassembly and a `cdq` appears in the middle of otherwise ordinary 8086 code, next to an `idiv bx`.

**There is no `CDQ` there.** In 16-bit mode the one-byte opcode `0x99` is `CWD` -- sign-extend AX into DX:AX -- and `0x98` is `CBW`. capstone 5.0.7 prints them as `cdq` and `cwde`, their 32-bit names, even when the engine is constructed with `CS_MODE_16`.

Measured by decoding the bare bytes:

| bytes | capstone in `CS_MODE_16` | a 16-bit decode |
|---|---|---|
| `99` | `cdq` | **`cwd`** |
| `98` | `cwde` | **`cbw`** |
| `f7 fb` | `idiv bx` | `idiv bx` -- correct |
| `c1 eb 02` | `shr bx, 2` | `shr bx, 2` -- correct |

**The mode itself is fine, which is what makes this dangerous.** The two rows that are right are the check that matters: 16-bit operands are being decoded as 16-bit operands, so nothing about the surrounding listing is suspect and there is no reason to doubt the two rows that are wrong. A reader sees `cdq` beside `idiv bx` and reads a routine that mixes 386 and 8086 code, which is a perfectly ordinary thing for a 286-or-later target to do.

## What it costs

**A transcription.** Copy `CDQ` into a Borland BASM or TASM source and the assembler does what you asked: it emits the operand-size prefix, `66 99`, and the block is one byte longer than the original at that point. Every subsequent address inside the routine shifts by one, so a byte comparison reports a difference that has nothing to do with the instruction it appears to be about -- and there are six of these in one 1,360-byte routine, each shifting everything after it.

Nothing downstream catches it. The prefix is a legal encoding of a legal instruction, so an assembler will not complain, a length check sees a plausible routine, and a walk that aligns with shifts may absorb it.

## The fix, and why it belongs in the decoder

Rewrite the two mnemonics at the point where the decode is turned into text, so no caller can inherit the wrong name:

    NARROW = {"cwde": "cbw", "cdq": "cwd"}

**Not in the callers.** The engine has one place where an instruction becomes a string and several tools read it; a mapping applied per caller is the second copy of one measurement, and `drifted-second-copy` records what that costs.

## Blind spot

**This is a version-specific defect, and the list of affected mnemonics is not derived from anything.** It was found by noticing one implausible instruction and checking that byte on its own; the two entries above are the two that were looked for. Other opcodes whose 16- and 32-bit names differ are not ruled out -- `PUSHA`/`PUSHAD`, `POPA`/`POPAD`, `IRET`/`IRETD`, the string instructions' `W`/`D` suffixes -- and none of them was measured. A decoder that is wrong about two mnemonics has no principle that stops at two.

**The correction is cosmetic to a byte comparison and load-bearing to a transcription.** Any measurement made by comparing bytes was never affected, so the fix changes no number anywhere -- which also means no existing check would ever have caught it.

## Cost

Two lines. Finding it cost one moment of disbelief at a listing.

## Example

Reading `NEUROSIS.002`'s polygon scan converter at `108b:0513`, where the original's floored-division idiom is `MOV CX,AX / CWD / IDIV BX / CMP CX,0 / JGE / DEC AX / ADD DX,BX`. The listing said `cdq`, and the routine was being transcribed verbatim into a BASM block at the time. [1]

## Citations
[1] `kit/tools/substrate/disasm.py`, the `NARROW` table above `walk()`, and `src/P2SOLID.PAS`'s `TriFill` transcription in the psycho repository.
