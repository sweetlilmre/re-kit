---
type: Observation
title: A hardcoded address copied from the original is right by coincidence
description: Transcribing hand assembler verbatim is the correct discipline for instructions, and wrong for the addresses inside them. A displacement in the original encodes where that build put a variable; copied as a literal into a rebuild whose layout differs by two bytes, the instruction is byte-perfect and reads the wrong memory. Every static instrument passes, because the bytes are what you asked for. Write what the number MEANS -- OFFSET Var minus the stride -- and it survives the next reorder.
tags: [hand-assembler, transcription, addressing, reconstruction, verification, blind-spot, measurement]
timestamp: 2026-08-26T00:00:00Z
---

# A hardcoded address copied from the original is right by coincidence

The rule for hand-written assembler is to transcribe it verbatim: same instructions, same order, same encodings, comment every line, and do not improve it. That rule is right, and it has an exception nobody states.

**The addresses inside those instructions are not part of the code. They are part of the layout.**

    original:   IMUL DI, N, 1641
                LEA  AX, [DI - 895]        ; @Under[N]

`-895` is `1641 - 746`, and `746` is where *that build* put the array. Copy it into a rebuild whose data segment differs by two bytes and the instruction is byte-for-byte what the original has, decodes identically, disassembles identically — and reads two bytes into every row of the array. In a 40×40 sprite gather, that is every pixel taken from two columns along. The sprites draw. They look nearly right. They are wrong in all 1,600 pixels.

## Why nothing catches it

Because you asked for those bytes and you got them:

- **A coverage walk** compares emitted bytes against the original's. The literal makes them *match better* than the correct version does — the correct displacement differs from the original's by exactly the layout gap, so writing the bug scores higher than writing the fix.
- **An initialised-image compare** sees no data change at all.
- **A reference map** pairs the displacement and reports the shift, which is real information — but it reads as one more layout row among dozens, indistinguishable from the ordinary consequence of an unconverged segment.
- **A lint pass** sees a valid constant in an `asm` block.

That third point is the trap worth naming. **The instrument that could see it reports the symptom of a defect and the symptom of correctness in the same column.** A displacement two bytes off because the variable moved, and a displacement two bytes off because you hardcoded the wrong one, are the same row.

And the incentive runs the wrong way: because a hardcoded literal matches the original's bytes exactly, **the byte-level score rewards the bug**. Anybody optimising the percentage will reintroduce it.

## The fix, and it is shorter than the bug

Write the arithmetic the original's assembler was doing:

    LEA  AX, [DI + OFFSET Under - 1641]     ; @Under[N], 1-based

The assembler computes `OFFSET Under - 1641` at build time from *this* build's layout. When the layout converges the emitted byte becomes the original's `-895` on its own; when it does not, the code is still correct. The displacement stops being a fact you asserted and becomes one the toolchain derives.

**The general form:** any constant in a transcribed `asm` block that is an *address* — a folded array base, a variable's offset, a jump into a table — must be written as a symbol plus arithmetic. Constants that are *values* — a loop count, a screen width, a colour, a bias — are transcribed literally, because those really are the code.

    LEA  AX, [DI - 895]                     WRONG: an address as a literal
    LEA  AX, [DI + OFFSET Under - 1641]     right
    MOV  CX, 1600                           right: 40 x 40 is a value
    MOV  DI, [BX + OFFSET YOfs]             right: symbolic already

## How to sweep for it

Grep the transcribed blocks for numeric displacements and ask of each one: *is this a place or a quantity?* A place with no symbol in it is a defect waiting for the next declaration to move. The audit is mechanical and it is worth doing the moment a second one of these turns up, rather than after the third.

## Blind spot

**This does not tell you the layout is right.** Making the displacement symbolic makes the *code* correct against whatever layout you have; it does not close the gap between your layout and the original's. Those two bytes are still missing, and now the emitted displacement differs from the original's by exactly that amount — which is the honest reading, and it will only close when the data segment does.

**And the discipline can be over-applied.** A folded subscript base is an address; a stride is not. Turning `IMUL DI, N, 1641` into a symbolic size expression buys nothing and loses the transcription's literal fidelity to the instruction stream. The test is whether the number would change if a declaration moved.

## Cost

One expression per site, and the sites are only in transcribed assembler. Finding them costs a grep. Not finding them costs a watched run, and only a watched run — see [Every instrument reads clean and the screen is blank](../name-resolution-is-invisible/observation.md) for the other member of this family.

## Example

Part 001 of a 1994 VGA demo. A lens-gather routine, correctly identified as hand assembler and correctly transcribed instruction by instruction, carried `LEA AX,[DI-895]` from the original. The rebuild's array sat two bytes lower, so every one of the ten bouncing sprites gathered its 1,600 pixels from two columns along. Coverage 99.0% before, 99.0% after, same single unaligned span; the initialised image identical both ways; the emulator trap streams identical both ways. The defect was reported from a screenshot. [1]

# Citations

[1] `src/P1LOGO.PAS`, part 001 in the psycho repository; measured with `kit/tools/pascal/spans.py`, `dgimage.py` and `fpusites.py`, and detected by a watched DOSBox-X run on 26 Aug 2026.
