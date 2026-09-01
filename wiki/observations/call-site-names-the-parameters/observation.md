---
type: Observation
title: The call site names the parameter list
description: A Borland Pascal routine's RET operand gives the total size of its parameter block, and the caller's run of pushes partitions that total into the individual parameters, in declaration order, with their widening idioms naming their types. Between them they recover a signature -- including parameters the callee never reads -- without compiling anything, and reading the caller is cheaper and more direct than probing the compiler.
tags: [pascal, codegen, turbo-pascal, source-shape, parameters, calling-convention, reconstruction]
measured_on: the demo reconstruction and the toolkit itself and a compiler probe, part 001
timestamp: 2026-08-25T00:00:00Z
---

# The call site names the parameter list

The frame measures a routine's locals. **The call site measures its parameters**, and it is the better of the two measurements, because it is a partition rather than a sum.

`ENTER n,0` gives you one number for the whole `var` block, so it can reject a declaration list without ever naming what is missing -- see [The frame is bigger than your locals account for](../frame-size-counts-locals/observation.md). Parameters are different. The callee's `RET n` gives the total, exactly as `ENTER` does; but the *caller* pushes the parameters one at a time, in order, each with the widening or address-taking idiom its type requires. So you get the total, the partition, the order, and a strong hint at each type -- from one run of instructions you have to read anyway.

## The reading

**Borland's Pascal convention pushes left to right and the callee cleans up.** So:

- `RET n` is the size of the parameter block. `RET` alone means no parameters.
- The **first** parameter declared is pushed **first**, so it ends up at the **highest** offset. `[BP+4]` -- the slot nearest `BP` above the return address -- is the **last** parameter declared. This is the opposite way round from locals, where first-declared is nearest `BP`, and getting it backwards produces a signature that is right in every part and wrong in order.
- Each push's *form* names the type:

| the push | what was declared |
|---|---|
| `PUSH word ptr [x]` | a 2-byte value parameter -- `Integer`, `Word`, `Char`, `Boolean` |
| `MOV AX,[x] / CWD / PUSH DX / PUSH AX` | a **`LongInt` parameter** taking an `Integer` argument -- the widening is at the call site, so the two differ |
| `MOV AX,[x] / XOR DX,DX / PUSH DX / PUSH AX` | the same, from an unsigned argument |
| `PUSH DS / PUSH DI` or `PUSH ES / PUSH DI` | four bytes of far pointer |
| two or three `PUSH word ptr [BP-k]` in descending `k` | one multi-word value, pushed high word first |

**A structured value parameter is four bytes on the stack, not its own size.** The caller pushes a *pointer* and the callee copies:

    LEA DI,[BP-0C] / LDS SI,[BP+1E] / MOV CX,000C / REP MOVSB

That `REP MOVSB` at the top of a routine, writing into its own frame from a pointer parameter, is the signature of `P : SomeRecord` passed by value. The copy's length is the record's size and the copy's destination is where the parameter lives -- so `P` **is** that frame slot, and the routine has no separate locals holding the fields. A reconstruction that declares `X, Y, Z` locals and loads them from the parameter has one copy too many.

## Parameters the callee never reads

This is the finding that makes the technique worth a page rather than a footnote.

Add up the pushes and compare with `RET n`. In a Borland Pascal binary, where the callee cleans up its own parameter block, the two agreeing while the *callee* only touches some of the offsets leaves one reading: the untouched ones are **declared parameters that the routine ignores**. Not padding, not a misread -- this compiler's caller pushed them and this compiler's `RET` pops them.

They happen for ordinary reasons -- a routine grew, or was cut down, and its signature was never trimmed. **Transcribe them.** A dead parameter occupies stack space, so dropping it moves every parameter declared after it to a different offset, and a body that was otherwise perfect then reads the wrong slots throughout. The cost of keeping a parameter you cannot justify is a line of source and a comment; the cost of dropping it is every offset after it.

## Why to read the caller before writing a probe

A compiler probe -- put the construct in a unit, compile it, look at the bytes -- is the right instrument for *"which of these two forms does the compiler emit"*. It is the wrong instrument for *"what did this source declare"*, and the difference is that a probe answers a question you had to guess the shape of first.

The call site does not need the guess. It is the compiler's own answer about *this* source, already in the binary, and it costs one disassembly of a range you are working in anyway. Reach for the probe when the caller is ambiguous, not before.

## Blind spot

**The partition is exact; the grouping into declarations is not.** Three consecutive 4-byte pushes could be `A, B, C : LongInt` or three separately declared `LongInt`s, or a mix with a `Single`. Same bytes, same offsets, same code. The signature you write is one of several that compile identically, and only the *sizes and order* are measured.

**Two-byte types are indistinguishable at the call site.** `Integer`, `Word`, `Char` and `Boolean` all push one word. When the callee's use does not disambiguate them, the choice is a guess and should be flagged as one in the source.

**A single call site gives no corroboration.** A routine called from one place tells you what that caller passes, which is the signature; a routine called from several is much stronger, because the signature has to satisfy all of them and a misread partition usually fails on the second. Prefer reading a well-called routine first.

**And a caller can pass the same value twice**, or pass a local it has just computed, which tells you nothing about where that value came from. The technique recovers the *signature*, not the data flow into it.

## Cost

One disassembly of the call site -- typically twenty instructions -- plus the callee's `RET`. No compiling, no probe unit, no rebuild.

## Example

A per-point 3D transform at `12c5:01b0` in a 1994 VGA demo had been reconstructed as inlined statements in its caller's loop. Ten spans of the coverage walk traced to its address, and the caller's own source comment already said the caller "fans out to `12c5:01b0`" -- the routine boundary had been *identified* and not implemented.

The callee gave `RET $1E`: thirty bytes of parameters. The offsets it read were `[BP+04]`, `+06`, `+08`, `+0A`, `+0C`, `+0E`, `+10` and `+1E` -- a contiguous run of fourteen bytes, then **a twelve-byte gap**, then four bytes. The gap was the whole difficulty: something was declared there and nothing in the routine referred to it. A codegen probe was written into the record as the next step, on the theory that it was a structured value the compiler had pushed directly.

The caller settled it in one read, and the probe was never needed. Eight pushes, and they account for all thirty bytes:

| pushed | lands at | what it is |
|---|---|---|
| `PUSH ES / PUSH DI`, `DI = Obj^ + I*12 - 12` | `[BP+1E]` | the point, **by value** -- the callee's `REP MOVSB` |
| `[bp+8]`, `[bp+6]`, `[bp+4]`, each `CWD`-widened | `[BP+1A]`, `+16`, `+12` | three angles -- **`LongInt` parameters, `Integer` arguments** |
| three cached `LongInt`s, high word first | `[BP+0E]`, `+0A`, `+06` | the object's translation |
| `[bp-2]` | `[BP+04]` | the loop index, last declared |

So the twelve-byte gap was the three rotation angles, **passed to the routine and never read by it** -- the caller had already consumed them in three `SinCos` calls before the loop began. They were transcribed as dead `LongInt` parameters for exactly the reason above: they are twelve of the thirty bytes.

With the routine extracted and that signature written, the part's coverage walk moved from 79.8% to 81.0% and **every span in `12c5:0000..02FF` disappeared** -- the walk lists nothing at all in the range where ten had stood. The initialised data image was unchanged and the x87 trap streams stayed identical opcode for opcode, so the gain was not bought from somewhere else. [1]

Two details carry. **The by-value point removed locals rather than adding them**: because `P` is the twelve-byte copy at `[BP-0C]`, the reconstruction's `X, Y, Z` locals were a second copy the original does not make, and the model's array had to become an `array of` a *named* record type before it could be passed at all -- a change of type, not of size, so the data image confirmed it as layout-neutral. **And the same call site named the caller's own signature on the way past**: `LES DI,[BP+0A]` twice, and `RET $A`, say the caller takes the object as a far pointer parameter where the reconstruction reads unit-level variables -- with `ADD DI,$4B0` fixing the record's translation field at offset 1200, which is exactly one hundred twelve-byte points and so names an array bound the reconstruction had as sixty-four. [2]

## Citations
[1] `src/P1VECTOR.PAS`, part 001 segment `12c5`, in the psycho repository; measured with `kit/tools/pascal/spans.py`, `dgimage.py` and `fpusites.py --diff` against the shipped binary on 25 Aug 2026.

[2] The same call site, `12c5:0317` and `12c5:0361`. Recorded as an open investigation rather than acted on, because the array bound also sizes a second array and moving it shifts DGROUP -- a layout bundle, which that target has learned to land in one step.
