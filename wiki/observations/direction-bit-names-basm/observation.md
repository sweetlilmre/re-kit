---
type: Observation
title: The direction bit tells hand assembler from compiled Pascal
description: Borland's built-in assembler emits every register-to-register op in the store direction (MOV AX,BX as 89 D8), while the Pascal code generator is mixed. So the ratio over a routine separates a BASM block from compiled Pascal in the same binary -- and it works where an ENTER-framed prologue makes the two look identical.
tags: [pascal, turbo-pascal, basm, hand-assembler, identification, encoding, disassembly]
timestamp: 2026-08-24T00:00:00Z
---

# The direction bit tells hand assembler from compiled Pascal

You have a Borland Pascal binary with no debug info, and a routine you cannot classify. It opens `ENTER n, 0`, it has BP-relative locals, and it looks like every compiled routine around it.

**Count its two-byte register-to-register operations and split them by the direction bit.** Most x86 ALU and MOV opcodes come in pairs that differ only in bit 1: `MOV AX,BX` is either `89 D8` (store direction, `r/m <- reg`) or `8B C3` (load direction, `reg <- r/m`), and both are two bytes with identical behaviour. An assembler picks one; a code generator picks whichever its register allocator reached for.

Measured on one segment of a 1994 Borland Pascal 7 binary, over `88/89`, `00/01`, `08/09`, `10/11`, `18/19`, `20/21`, `28/29`, `30/31`, `38/39` and their `|0x02` partners, counting only `mod = 11` forms:

| routine | store | load | store share |
|---|---|---|---|
| the suspect | 62 | 0 | **100%** |
| four compiled Pascal routines | 3-5 | 3-9 | 27-57% |
| a TASM-assembled `{$L}` object | 3 | 7 | 30% |

**62 of 62 is not a tendency, it is a tool that only ever emits one form.** The suspect was hand-written assembler; every routine that came from the Pascal code generator was mixed, in a band nothing in the sample left.

## What it identifies, and the conclusion that was withdrawn

The first reading of that table was that the producer was neither the Pascal code generator nor TASM -- because TASM came out mixed too -- and therefore something foreign, so transcribing the routine through Borland's own assembler would cost roughly 62 one-bit differences.

**Both halves were wrong, and a rebuild is what said so.** Transcribed as a Borland `assembler` procedure and compiled, the routine came out byte-for-byte identical through the whole prologue and sort chain, `89 D8` and `89 D1` and `89 F2` included: 1,250 of 1,360 bytes, 91.9%, with no differing run longer than two bytes and not one opcode among them. **BASM emits the store direction consistently, so a 100% store share identifies BASM rather than excluding it.** The right conclusion from the table is the narrower one -- the ratio separates *an assembler* from *the code generator* -- and which assembler is a question for a rebuild, not for the ratio.

The lesson worth keeping is the shape of the error: a ratio was used to exclude a candidate it had no power to exclude, because the only other assembler in the sample happened to sit near the code generator's band.

## Why it works

The Pascal code generator emits a register move as a side effect of allocation -- it has a value in one register and wants it in another, and which opcode form expresses that depends on which operand its tree walk treats as the destination. An assembler has one operand order in the source and one rule for encoding it, so it is consistent by construction.

## The same bit, used backwards: the residual of a failed transcription

The table above is a RATIO and needs eight qualifying operations before it will speak. There is a second use of the same fact that works with **two**, and it answers a different question -- not *is this routine assembler* but *where does the assembler BEGIN*.

Transcribe the routine as an `assembler` procedure, rebuild, and compare. If the whole routine was hand-written, it comes out identical. If only part of it was, **the bytes that stay wrong are direction bits, and they mark the half that was compiled.**

Measured, 25 August 2026, on a 72-byte routine that programs a VGA CRTC. Written as one `assembler` procedure it came back 70 of 72 bytes right, and the two survivors were:

| the original | our transcription | the instruction |
|---|---|---|
| `8B C8` | `89 C1` | `MOV CX,AX` |
| `03 C1` | `01 C8` | `ADD AX,CX` |

Two bytes, same mnemonics, opposite direction bits -- and both in the routine's opening arithmetic, none in its port-writing tail. That is the boundary, stated to the byte: the arithmetic came from the code generator and the tail was hand-written. Splitting the source into a Pascal statement followed by an `asm` block at exactly that point made all 72 bytes identical.

**Two qualifying operations decided it, where the ratio would have refused to speak.** The reason is that the rebuild supplies the comparison group the ratio has to find for itself: each byte is being judged against the same instruction from the same source, so one disagreement is already a measurement.

**And it catches the mistake in the direction people actually make.** The ratio guards against reading hand assembler as Pascal. This guards against the opposite -- transcribing compiled code as assembler because the routine *contains* an asm block -- which is the easier error to commit, because the rule *never re-express hand assembler as higher-level code* pushes hard one way and says nothing about how far the block extends.

## Blind spot

**It needs a decent count.** A 40-byte routine may have no qualifying ops at all: the companion routine to the one above, 88 bytes, scored 0 and 0, so this test said nothing about it and its assembler nature had to be established another way -- it passed arguments to the suspect in registers, which no Pascal caller can do.

**It cannot see which assembler**, as the withdrawn conclusion above shows. And it says nothing about `{$L}`-linked objects as a class: one TASM object measured 30%, which is a single sample and near enough the code generator's band to be useless as a discriminator.

**It is a ratio, so it needs the comparison group from the SAME binary.** Absolute shares are not the finding; the gap between the suspect and its neighbours is. The residual technique above is exempt from this one, and only that one: its comparison group is the rebuild.

**The residual technique needs the rest of the transcription to be right.** Two wrong bytes are legible because everything around them matched. A transcription that is wrong about an operand or a jump target produces differences that are not direction bits, and reading those as a block boundary would put it in the wrong place.

## Cost

One pass of a 16-bit decoder over each range, counting opcode bytes where `mod = 11` and the length is two. No build, no debug info, no symbol table.

## Where the tells that read the other way are

**An `ENTER n, 0` prologue with BP-relative locals is NOT evidence of compiled Pascal**, and a tell table that lists it as such is what hid this routine for as long as it was hidden. Borland emits its standard frame for an `assembler` procedure that declares local variables, so a hand-written routine with locals looks exactly like a compiled one at the entry point. Three tells in the same routine did read correctly, and all three are things no code generator does: BP used as a scratch register between a `PUSH BP` and a `POP BP`; `REP STOSW` / `ADC CX,CX` / `REP STOSB` inline where `FillChar` would be a far call into the runtime; and a general-purpose value parked in `ES` so `BX` could be borrowed as an index register.

## Example

`NEUROSIS.002` segment `108b`, the polygon scan converter at `108b:0461` and the fan filler at `108b:09b1` that is its only caller. The first is the 62/0 row above; the second is the 0/0 blind spot. Both rebuild as Borland `assembler` procedures -- the fan filler byte-identical in all 88 bytes -- and the coverage walk's largest single span anywhere, 1,276 bytes, closed. [1]

## Citations
[1] `src/P2SOLID.PAS`, the `TriFill` and `FillFan` transcriptions and the comment block above them, in the psycho repository.
