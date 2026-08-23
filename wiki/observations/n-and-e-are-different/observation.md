---
type: Observation
title: The code is full of INT 34h and you conclude something about the coprocessor
description: Two Borland switches get conflated because their effects meet in the same bytes -- $N chooses whether 80x87 instructions are emitted at all, $E chooses how they ship, and a trap in a binary tells you about the second and nothing about the first.
tags: [turbo-pascal, codegen, x87, switches, pascal]
timestamp: 2026-08-23T00:00:00Z
---

# The code is full of INT 34h and you conclude something about the coprocessor

A disassembly of a Borland Pascal binary is peppered with `INT 34h` through `INT 3Dh` where floating point should be. Whatever you conclude next, it is probably about hardware -- that the author had a coprocessor, or did not; that this build is a variant patched for one; that our own build differs because ours has traps and theirs does not, or the reverse.

**Two switches produce those bytes and they answer different questions.** Keeping them apart is the whole of it:

| switch | what it decides |
|---|---|
| `$N` | whether 80x87 INSTRUCTIONS are emitted at all, or floating point goes through the software six-byte `Real` RTL instead |
| `$E` | whether those instructions SHIP as themselves or as `INT 34h..3Dh` traps of identical length, so a machine with no coprocessor can still run them |

A trap in the file is `$E` and says nothing whatever about `$N`. Code compiled `$N-` has no 80x87 instructions to trap, so it has no traps either -- and it is *much* slower, because every operation is an RTL call on a six-byte software float.

**And the traps say nothing about the hardware the author had.** Under `$E+` the runtime patches them back to real opcodes at startup **if** a coprocessor is present, and leaves the emulator to execute them if not. The same shipped bytes serve both machines. That is the entire point of the mechanism: identical instruction lengths, patched in place.

## Why it works

`$E+` is a *packaging* decision, chosen so one binary runs everywhere, and it is implemented by overwriting a two-byte `WAIT ESC` prefix with a two-byte `INT n`. Because the lengths match, nothing else about the code moves -- which is why the traps can be patched back at run time, and why a trap-for-trap rewrite is a safe way to make the file disassemble.

`$N` is a *code generation* decision, and it changes which routines the compiler calls and what the operands look like. The two meet only in the sense that `$N+` is what produces the instructions `$E+` then disguises.

## Blind spot

**This says nothing about which switches a particular binary was built with.** It tells you what a trap is and is not evidence of. To learn `$N`, look at the CODE: `$N+` gives you `FILD`, `FDIV`, `FLD` of a ten-byte extended constant and coprocessor-stack discipline, all wearing trap encodings; `$N-` gives you RTL calls and six-byte operands, and no traps at all.

**A rewritten copy is your own output, and will be mistaken for a variant.** Patching the traps back to real opcodes so a disassembler can read the code produces a second file that looks like a release built with `$E-`. It is not. Two sessions on one project theorised about such files being period variants; they were the project's own aids. Name them so nobody has to guess.

**Timing evidence points at `$N`, not at `$E`.** A multi-second pause where the original has none is a plausible `$N-` symptom, because software floats are orders of magnitude slower. It is a very poor emulator symptom, because the original ran the emulator too.

## Cost

Reading the switch's own documentation once, and looking at the operands rather than the interrupt number. No tooling.

## Example

Part 005 of `PSYCHO NEUROSIS`, 23 Aug 2026, on the second attempt to get this right.

The reconstruction showed a multi-second black screen where the original moved straight on. The cause was `$N`: one unit had compiled under the `$N-` default, sending 3,424 trig calls through the software six-byte-`Real` RTL, where the original's table build at `1096:051a` is 80x87 code. `{$N+}` on that unit fixed it.

The **shipped** original carries **14 emulator traps at that same address**, and the author had no coprocessor -- so in 1994 every one of those instructions was executed by the emulator. The fix therefore changed which code was emitted and nothing at all about the emulator; `$E+` stayed as it was.

That distinction was written down correctly after a session in August built an elaborate theory on it, and a later session repeated a smaller version anyway -- describing the fix as making the calls "go through x87". The unit's own comment had said *is x87 code* and listed `FILD`, `FDIV`, `FLD`, without mentioning that those ship as traps. **Accurate and incomplete, and the incompleteness was the load-bearing part.** [1] [2]

# Citations

[1] `src/P5S2.PAS` in the psycho repository -- the `{$N+}` comment, which now carries the distinction, and the measured 14 traps.

[2] `docs/23-deviations.md`, *NOT a deviation: the x87 emulator traps, and the `_fpu` files' provenance*, in the same repository.
