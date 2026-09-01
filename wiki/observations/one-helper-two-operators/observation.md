---
type: Observation
title: One runtime call serves div and mod, and the call cannot tell you which
description: Borland compiles LongInt div and LongInt mod to the same runtime routine. It returns the quotient in one register pair and the remainder in the other, so which operator the source used is not in the call at all -- it is in the two instructions that may or may not follow it. A reconstruction that reads the call and stops gets the operator wrong half the time, and both spellings compile, run, and produce plausible-looking output.
tags: [pascal, runtime, codegen, reconstruction, longint, measurement, arithmetic]
measured_on: the demo reconstruction and the toolkit itself, part 006
timestamp: 2026-08-26T00:00:00Z
---

# One runtime call serves div and mod, and the call cannot tell you which

Two statements, one instruction stream:

```pascal
V := (Round(X / 20.0) div 2) * 60;
V := (Round(X / 20.0) mod 2) * 60;
```

Both compile to the same three runtime calls in the same order. The `div` version:

    call  RoundToInt
    mov   cx, 2
    xor   bx, bx
    call  LongDivMod          ; <-- the same routine
    mov   cx, 60
    xor   bx, bx
    call  LongMul

and the `mod` version differs by exactly two instructions:

    call  LongDivMod          ; <-- the same routine
    mov   ax, cx              ; <-- and only these
    mov   dx, bx              ; <--
    mov   cx, 60
    xor   bx, bx
    call  LongMul

**The operator is not in the call. It is in whether those two moves are there.**

## Why, and it is in the helper's tail

Disassemble the routine and the last four instructions give the whole rule:

    mov   ecx, edx            ; ECX := the REMAINDER
    shld  edx, eax, 0x10      ; quotient  -> DX:AX
    shld  ebx, ecx, 0x10      ; remainder -> CX:BX
    retf

One division, both results, returned in two different register pairs. **The quotient comes back in DX:AX, which is where the caller's next expression already expects a value, so `div` needs no fixup at all. `mod` has to move the other pair across.** So the presence of a `MOV AX,CX / MOV DX,BX` immediately after the call is the entire signal — and its absence is the other half of the signal, which is the part that gets missed.

The same shape appears wherever a runtime helper computes more than it is asked for. Read the helper once and write down which pair holds what; it is not guessable from the call site.

## What makes this expensive

**Both spellings compile and both run.** There is no error, no warning, no crash. `div` where the original had `mod` produces a number of the wrong magnitude that flows into whatever the expression feeds, and unless that consumer happens to be visibly wrong the mistake survives every static check — the byte difference is two instructions in a routine hundreds of bytes long.

And it repeats: an expression like this is usually written once and copied, so one misread operator becomes four or eight sites.

## The second reading, which is free

**Check the value's range against what consumes it.** In the case above `V` was the red channel of a DAC palette write, valid 0..63:

| spelling | X from 320 down to 190 | V |
|---|---|---|
| `div 2` | `Round(X/20)` = 16..10, halved = 8..5 | **300..480** -- far outside the DAC, and truncated to nonsense by the Byte parameter |
| `mod 2` | `Round(X/20) mod 2` = 0 or 1 | **0 or 60** -- a clean two-step flicker |

The register evidence and the range agree, and either one alone would have been enough. When a reconstructed expression feeds something with a known domain -- a palette entry, a screen coordinate, an array index -- computing the range is a check that costs nothing and catches the operator, the sign and the width all at once.

## Blind spot

**The fixup is not unique to `mod`.** `MOV AX,CX / MOV DX,BX` after a call is *a* pair of moves; other constructs move a register pair around too, and a caller that wants the quotient in an unusual place will also emit moves. What identifies `mod` is the moves being *from the pair the helper leaves the remainder in*, immediately after that particular helper. Confirm the helper is the div/mod one before reading its callers.

**And the register pairs are the compiler's convention, not the language's.** They are stable within one Borland release and must be read out of the binary in hand rather than assumed. Read the helper.

## Cost

One disassembly of one runtime routine, once per target. After that the operator is a two-instruction lookup at every site.

## Example

Part 006 of a 1994 VGA demo. Four copies of one statement, each carrying a two-byte span the coverage walk had reported for days. The runtime helper's tail identified the operator, the DAC's 0..63 range confirmed it, and changing `div` to `mod` at four sites closed all four spans and took the part from 99.5% to 99.6%. The reconstruction had been writing 300..480 into a palette entry that accepts 0..63. [1]

A guess had been tried on the same spans one tick earlier -- that the operands of the multiply were the wrong way round, by analogy with a genuine operand-order finding elsewhere in the same part. It measured nothing and was reverted. The helper's tail was two minutes of disassembly and settled it.

## Citations
[1] `src/P6FIRE.PAS`, part 006 in the psycho repository; the runtime routine read at its own offset via `kit/tools/pascal/rtl.py`, measured with `spans.py` on 26 Aug 2026.
