---
type: Observation
title: The data segment is laid out in reverse of the uses clause
description: Borland Pascal emits each unit's typed constants into DGROUP in the REVERSE of the order the units are named, while code segments follow that order forwards. So a reconstruction whose data segment is back to front has its uses clause back to front -- and until it is fixed, every absolute data reference in the program carries a wrong displacement and correct code measures as wrong.
tags: [pascal, turbo-pascal, dgroup, linking, source-shape, units, reconstruction]
timestamp: 2026-08-25T00:00:00Z
---

# The data segment is laid out in reverse of the uses clause

You have rebuilt a unit. Its routines are right -- the calls are in order, the constants are right, the loops have the right shape -- and the whole segment still measures as unaligned. Nothing you change to the code moves the number.

**Look at where a known table landed in the data segment. If the units come out backwards, your uses clause is backwards.**

Borland Pascal emits typed constants into DGROUP one unit at a time, in the reverse of the order the units are named in the `uses` clause. The last unit named gets the lowest offsets. Code segments are emitted in that order *forwards*, so the two run in opposite directions and a single clause sets both.

## Why it costs so much more than it looks

Every reference to a global carries its DS displacement in the instruction -- two bytes, inside an otherwise correct instruction. A `MOV WORD PTR [X],1` whose `X` is wrong is a six-byte instruction with four right bytes, and a routine full of them is a routine full of near misses. A byte comparison cannot resynchronise on that, so:

- the routine measures as **entirely** unaligned, not mostly aligned
- **the size of the miss does not matter.** Two bytes out and thousands of bytes out cost exactly the same
- the damage is **per segment**, not per routine: every unit that touches its own globals is affected at once

Which is why this is worth checking *before* rewriting any routine. A correct rewrite of a routine in a misplaced unit measures zero, and zero is the reading most likely to be believed and least likely to be questioned.

## Reading it

You do not need a map file, and you will not get one. A typed constant's bytes are identical in both builds, so find them:

1. Pick one table per unit -- a palette, a sine table, a string list -- big enough to be unique.
2. Find its bytes in the original and in your build.
3. Compare the **order**, not the offsets. Offsets need a DGROUP base; order does not.

Three units is enough to tell a reversal from a shuffle, and one is never enough.

**The header will not tell you where DGROUP starts.** In real-mode Borland Pascal the `SS` field is the *stack*, which sits beyond the image, so computing a data base from it gives a number past the end of the file. Anchor on a table whose offset you know from the disassembly instead.

## What it is NOT

**Not the interface/implementation distinction.** A unit named in the implementation section initialises after one named in the interface, which makes it the obvious candidate -- and it is the wrong one. Moving a list from implementation to interface changes this order not at all. It is the order of the names.

**Not a licence to reverse every clause.** Swept across seven parts of one program, reversing measured *better* in two, *worse* in one, and *unchanged* in the rest. The units in the others were already in the original's order. Reverse a clause when the data says that program's data segment is reversed, and not otherwise -- and check each one separately, because a program's units were written by someone who had a reason for the order.

## Why it works

DGROUP is built by allocating each unit's data as the linker walks its list of units, and that walk runs opposite to the initialisation order the code segments are emitted in. Nothing about it is discretionary, which is what makes it readable in both directions: a data segment in the original's order is evidence the clause is right, exactly as a reversed one is evidence it is wrong.

## Blind spot

**It cannot separate units with no typed constants.** A unit whose data is all `var` contributes nothing to the initialised region, so it is invisible to this test and can sit anywhere in the clause without the measurement noticing.

**Two tables in the SAME unit test nothing.** Their relative order is fixed by their declaration order and would be identical under any clause. If a part offers only one unit with constants, this technique has nothing to say about it, and a coverage number that improves by a handful of bytes after reversing it is not corroboration -- record it as a measurement and say that it is unverified.

**Order is not size.** Getting the order right leaves every offset still wrong if the total volume of constants differs, because the variables begin after all of them. Order and size are two findings and the first does not imply the second.

## Cost

Three byte-searches and a sort. No disassembly.

## Example

Part 003 of a 1994 megademo has ten code segments and three units carrying generated typed constants. Located by content, those three came out as Sprite, Morph, Tunnel where the shipped binary has Tunnel, Morph, Sprite -- an exact reversal.

The cost had already been paid twice without being recognised. The scene's main routine had been rewritten to match the original's structure exactly -- eight inlined blocks where the reconstruction had used three nested helpers -- and measured **exactly zero**, because every one of its forty-odd stores to globals carried a wrong displacement. Before that, a note in the same unit recording that three unused shape slots existed in DGROUP had been read for years without anyone drawing the consequence that omitting them moved every variable behind them.

Reversing the scene list in the main unit's uses clause put the tunnel palette back at `DS:$0002`, where the original has it and where that unit's own comment had always said it was:

    Red          $0002    ours $0002   MATCH
    SinTab       $02A8    ours $02B0
    ShapeSphere  $0636    ours $0634

Within twelve bytes across a 25,000-byte span, against thousands before. The code segments still landed in the original's order and the coverage walk rose. [1]

# Citations

[1] `src/P3MAIN.PAS`, `src/gen/P3PAL.INC` and `spans.toml`, part 003 in the psycho repository; the original's layout read from Ghidra's decompilation of `1139:03b4` and from byte searches over `work/split/NEUROSIS_003_fpu.exe`, measured with `kit/tools/pascal/spans.py` on 25 Aug 2026.
