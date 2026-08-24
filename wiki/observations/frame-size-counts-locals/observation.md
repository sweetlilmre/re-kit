---
type: Observation
title: The frame is bigger than your locals account for
description: A Borland Pascal routine's prologue is two measurements. The ENTER operand is the declared locals plus the code generator's temporaries, so it measures the source's variable list; whether there is an ENTER at all names the whole unit's $G switch. A reconstruction whose prologue is the wrong size has the wrong declarations, and one of the wrong FORM has the wrong switch, however well the statements match.
tags: [pascal, codegen, turbo-pascal, source-shape, locals, x87, switches, reconstruction]
timestamp: 2026-08-24T00:00:00Z
---

# The frame is bigger than your locals account for

You have rebuilt a routine. The statements look right, the constants are right, the branches go to the right places -- and the prologue says `ENTER $1C,0` in the original and `ENTER $18,0` in yours. Four bytes.

**Four bytes of frame is not a rounding difference. It is a variable.** Turbo Pascal 7 allocates a routine's frame as the declared locals followed by whatever temporaries the code generator needs, both at fixed offsets, both counted into the one `ENTER` operand. Nothing about it is discretionary and nothing is padding: real-mode BP7 does not round the frame up, does not keep locals in registers, and does not reuse a slot across statements. So the operand is an exact sum, and it is the cheapest measurement of a source's `var` block that exists.

That makes the frame a *constraint on the declarations*, checkable before you disassemble a single statement. Add up what you declared. If it does not reach the original's number, you are missing a variable or you have typed one wrongly, and no amount of adjusting the body will close the gap.

## Reading the two halves

**The declared half is in declaration order, first-declared nearest `BP`.** An `Integer` takes 2, a `Real` 6, a `LongInt` or `Single` 4, a pointer 4. So `[BP-2]` is the first variable declared, and the offsets recover the *order* of the `var` block as well as its contents.

**The temporary half is what the code generator could not do in registers**, and for BP7 the ones worth knowing are small in number:

| the temporary | why it is there |
|---|---|
| 4 bytes, written as a pair then read by `FILD DWORD` | an integer expression on its way to the x87 |
| 6 bytes, written by an RTL store and read once | a `Real` intermediate the code generator spilled |

The distinction that matters between a spilled intermediate and a *declared* `Real` is **how often it is read**. A declared variable is stored once and read wherever the source names it; a temporary is stored and read exactly once, adjacently. Two six-byte slots where you declared one `Real` means the original named its intermediate.

## The widening idiom names the type

The four-byte slots are the more useful half, because *how* the value is widened into them says what the source declared:

    MOV AX,[mem] / XOR DX,DX     unsigned -- the source type is Word or Byte
    MOV AX,[mem] / CWD           signed   -- Integer
    ... / CDQ                    signed, from a 16-bit expression result
    FILD WORD PTR [mem]          Integer, read straight, NO temporary at all

That last row is the one that changes the frame. An `Integer` reaches the x87 through `FILD WORD` with nothing spilled; a `Word` cannot, because `FILD WORD` is signed and would read anything above 32767 as negative -- so the compiler widens it into a four-byte slot first. **Declaring a constant `Integer` where the original declared it `Word` costs the frame exactly four bytes and changes nothing else you would notice.**

One more, in the same family: a value *read from memory* where a constant could have been folded says the source named a variable or a **typed** constant. An untyped `const` is folded at compile time -- `MOV AX,1600` where the original has `MOV AX,[2]` / `MUL WORD PTR [2]` is not an optimisation difference, it is a different declaration.

## The prologue's FORM is a different measurement, and a bigger lever

The operand counts locals. **Whether there is an `ENTER` at all names a compiler switch**, and that is worth separating because it pays off on a completely different scale:

    ENTER n,0                        the unit was compiled {$G+}
    PUSH BP / MOV BP,SP / SUB SP,n   it was compiled {$G-}

`ENTER` is a 286 instruction and Borland emits it only when 286 code generation is on. So one glance at any framed routine in a segment reads `$G` for **the whole unit** -- the switch is a unit property, not a routine property, so a single reading fixes every routine the unit contains at once. Nothing else in this bundle costs one instruction and moves that much.

**Both directions are measurements, and the negative one is the valuable half.** A segment with no `ENTER` anywhere says the original was `$G-`, and adding the switch there would be a change away from the original dressed up as a fix. Test the candidates before touching them, not after.

The same reading generalises to any switch with a visible signature -- `$N` in whether floating point is 80x87 or RTL calls, `$S` in whether a stack check precedes the frame -- and it is always per unit.

## Why it works

`ENTER n,0` is emitted from the symbol table after the routine is parsed, so `n` is the compiler's own final answer about the source's storage. Unlike the body -- where several statement shapes can produce the same bytes -- the frame has one number for one declaration list, and the code generator has no freedom to spend it differently.

## Blind spot

**It is a SUM, so it constrains the declarations without determining them.** Several `var` blocks total 28 bytes. The frame tells you that you are wrong and roughly by how much; it never tells you what to write. Use it to reject a reconstruction, then read the offsets to place what is missing.

**A routine with no locals gets no `ENTER` at all**, so the technique has nothing to read on exactly the small routines where a missing variable is easiest to overlook. And `{$G-}` changes register allocation rather than the frame, so a frame that matches is not evidence the *body* will.

**A nested routine's static link is at `[BP+4]`, not in the frame** -- it is a hidden argument and is not counted in `n`. Do not try to make the arithmetic absorb it; see [Every element read costs fourteen bytes and goes through the frame twice](../nested-static-link/observation.md).

## Cost

Reading one instruction. No disassembler beyond the prologue, and the arithmetic is addition.

## Example

A table-building routine at `1012:0004` in a 1994 VGA demo opens `ENTER $1C,0` -- 28 bytes. The reconstruction of it opened `ENTER $18,0`, while its body matched well enough that a per-routine byte check had nothing to say and the coverage walk reported the whole 696-byte routine as unaligned without saying why.

Twenty-eight resolved as four `Integer` (8), two `Real` (12), and two four-byte conversion slots (8). Three separate corrections fell out of that arithmetic, none of which was visible in the statements:

- **four Integers, not five.** The reconstruction held the loop's `X*X + Y*Y` in a variable; the original has no room for one and recomputes the two `MUL`s in the branch that needs them.
- **two Reals, not one.** The original names its intermediate -- the value is stored and read once each in different statements, which a spilled temporary never is.
- **eight bytes of conversion slot, not four.** The radius was declared `Word`, proved by `XOR DX,DX` widening it at `1012:0135` and `1012:015e`; the reconstruction had it as an untyped `const`, which the compiler folded, and then as `Integer`, which reaches the x87 through `FILD WORD` and spills nothing.

With the declarations corrected the routine aligned in full, and the part's coverage walk moved from 66.6% to 68.4%. [1]

**And the prologue's form, on the same corpus the next day, moved a part 885 bytes on one character of source.** A unit had been written without `{$G+}` while every framed routine in the original segment opened `ENTER` -- `$26,0` and `$04,0`. Adding the switch took that part's coverage walk from 80.4% to 88.1%, the largest single move the target has recorded, and the routine that had been the part's worst span fell from 426 unaligned bytes to 96. Nothing about the source's *statements* changed.

Two details from that case are worth carrying. **The evidence had been quoted in the unit's own comment for days** -- as the justification for a *different* switch, `{$S-}`, whose note read "opens `ENTER $26,0` with no stack check". The instruction naming `$G` was sitting inside the argument about `$S`, and nobody read it twice. **And two other units were REFUTED by the same test**: their originals carry no `ENTER` at all, so they are correctly `$G-` and adding the switch would have moved them away from the original. A sweep that only ever adds is not a measurement. [2]

# Citations

[1] `src/P1S1.PAS` and `spans.toml`, part 001 segment `1012`, in the psycho repository; measured with `kit/tools/pascal/spans.py` against the shipped binary on 24 Aug 2026.

[2] `src/P5S2.PAS`, part 005 segment `1096`, in the same repository; measured with `kit/tools/pascal/spans.py` on 24 Aug 2026. The refuted candidates are that target's `FIXMATH` (segments `1483` and `142a`) and its 320x400 video unit (`140c`), none of which contains an `ENTER`.
