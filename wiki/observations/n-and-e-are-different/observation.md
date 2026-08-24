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

**Better, if you have a rebuild: compile the unit BOTH WAYS and let the byte walk answer.** Reading a trap correctly is a skill, and everyone involved in the argument is using it; an alignment percentage against the original is not. Flip the switch, rebuild the one unit, walk every byte of the part. The build that matches the original more closely was built the way the original was, and nobody has to be believed. This settled the case above in two builds after three sessions of argument -- `$N+` 80.4%, `$N-` 79.2%, so `$N-` moved the rebuild 137 bytes *further* from the 1994 file. **A switch is a hypothesis, and a rebuild is cheap enough to test it with.**

**A rewritten copy is your own output, and will be mistaken for a variant.** Patching the traps back to real opcodes so a disassembler can read the code produces a second file that looks like a release built with `$E-`. It is not. Two sessions on one project theorised about such files being period variants; they were the project's own aids. Name them so nobody has to guess.

**Timing evidence points at `$N`, not at `$E`.** A multi-second pause where the original has none is a plausible `$N-` symptom, because software floats are orders of magnitude slower. It is a very poor emulator symptom, because the original ran the emulator too.

**And on a reconstruction, timing is not the reason to set the switch at all.** `$N+` is warranted the moment the original's code contains 80x87 instructions, because nothing else emits them; it would be warranted if the rebuild ran no quicker, and it would still be warranted if the rebuild ran *slower*. Justifying it by the speed change inverts that, and the inversion is what regenerates the coprocessor theory -- calling `$N+` a fix invites the next reader to ask what hardware it fixed. **Set the switch to match the emitted code. If the speed then changes, that is a finding to explain, never the argument for the switch.**

## Cost

Reading the switch's own documentation once, and looking at the operands rather than the interrupt number.

If you want the operands read for you, `pascal/x87.py disasm FILE SEG:A..B` resolves the traps **in memory** and marks every line it resolved, so there is no patched copy left on disk for the next reader to mistake for the original -- which is the mechanism that replaces this page's warning about exactly that. `--sites` writes out the confirmed trap addresses, which is the input `x87.py fix` has always asked for and had no way to be given.

And the two-build test needs no tooling beyond the build you already have.

## Example

Part 005 of `PSYCHO NEUROSIS`, 23 Aug 2026, on the second attempt to get this right.

The reconstruction showed a multi-second black screen where the original moved straight on. One unit had compiled under the `$N-` default, sending 4,002 trig calls through the software six-byte-`Real` RTL, where the original's table build at `1096:051a` is 80x87 code. `{$N+}` went on that unit -- **because the original was built that way** -- and two watched runs bracket the change with nothing else in the unit moving between them: the pause was there before and gone after.

**There is not one raw 80x87 opcode in the shipped 1994 file, and that is not an argument against `$N+`.** The maintainer raised exactly that objection, and it is the strongest form of the confusion this page exists to settle: what is in the file is **12 emulator traps** in that loop body, because `$E+` overwrote every instruction's `WAIT ESC` prefix. `$N-` would have left **no traps at all** -- far calls into a software library, and nothing for an emulator to emulate -- so a trap is positive evidence of `$N+`, not evidence against it. The author had no coprocessor, the emulator executed all twelve in 1994, and the rebuild ships and runs them identically; `$E+` was never touched.

**Why the pause went is not measured**, and it is certainly not that anything acquired an FPU: neither build has one. `$N-` and `$N+`/`$E+` are two different pieces of *software* doing floating point, and nobody has timed them against each other.

That distinction survived three attempts to lose it. A session in August built an elaborate theory on it; a later one repeated a smaller version, describing the change as making the calls "go through x87"; and a third wrote the corrected account into the record while still calling `{$N+}` *the fix*, which put the performance claim back at the front and invited the same question all over again. The unit's own comment had said *is x87 code* and listed `FILD`, `FDIV`, `FLD`, without mentioning that those ship as traps. **Accurate and incomplete, and the incompleteness was the load-bearing part.** [1] [2]

# Citations

[1] `src/P5S2.PAS` in the psycho repository -- the `{$N+}` comment, which now carries the distinction, the 12 traps measured over the loop body `1096:051a..0591`, and the two-build alignment test. An earlier version of that comment put **14** traps "at `1096:051a`"; the number is the count for the whole enclosing routine and the address was the loop's. Right number, wrong extent -- recorded here because a figure that cannot be reproduced from the extent it names is how a measurement quietly becomes a claim.

[2] `docs/23-deviations.md`, *NOT a deviation: the x87 emulator traps, and the `_fpu` files' provenance*, in the same repository.
