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

**THE COVERAGE WALK IS NOT CORROBORATION, AND ON ONE PART IT SAID NOTHING AT ALL.** The first example below saw the walk rise when the clause was reversed, which reads as confirmation. The second, bracketed deliberately, reports **10980 of 11440 aligned under both orders -- the same number to the byte** -- for a build whose three scene units sat in reverse order and whose initialised data was wrong in 5182 places. The reason is mechanical: a walk that locates each segment by CONTENT finds a unit at the wrong segment number just as well as at the right one, and the two-byte displacement errors inside it fall under the short-difference tolerance. So a rise is a bonus and its absence is not evidence. **Read the segment SIZES against the original's, and the initialised image; those are the two instruments that can see this.**

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

## A second example, bracketed, where the walk stayed silent

Part 005 of the same demo, the same day. Its initialised region is 11,648 bytes on both sides and 5,182 of them differed, first at `$0002`, with the rebuild resynchronising at a shift of `+4` -- which reads as one small block in the wrong place and is not what it was.

The `+4` was two typed `Word` constants, a view width and height, that the rebuild put at the FRONT of the region and the original puts at the very END of it, immediately after the previous unit's clip bounds. Everything between was one 11,532-byte generated mesh table, in the right place in both, shifted by those four bytes and therefore differing in 5,182 places for no reason of its own.

Two candidate explanations, and a build settled them:

* **the constants belong to the earlier unit.** Refuted in one build, and instructively: the object module that reads them is linked with `{$L}` from the later unit, and its `EXTRN` resolves by PASCAL SCOPE in the unit that links it. Declaring them anywhere else gives `Undefined external`. So their owner is not in question, and the ORDER OF THE UNITS is the only thing left.
* **the clause is reversed.** Naming the three scene units backwards took the initialised data from 5,182 bytes differing to **2 -- the test harness's own line terminator, and nothing else.**

The segment sizes are the independent check, and they agree without being asked: under the reversed clause the first scene unit comes out at `0x88` paragraphs where the original has `0x88`, and the four units after the scenes match the original's `0x08`, `0x14`, `0x62` and `0x11` exactly. Under scene order the three were laid down back to front.

**And the coverage walk reported 10980 of 11440 both times.** [2]

# Citations

[1] `src/P3MAIN.PAS`, `src/gen/P3PAL.INC` and `spans.toml`, part 003 in the psycho repository; the original's layout read from Ghidra's decompilation of `1139:03b4` and from byte searches over `work/split/NEUROSIS_003_fpu.exe`, measured with `kit/tools/pascal/spans.py` on 25 Aug 2026.

[2] `src/P5MAIN.PAS` and `src/P5S3.PAS`, part 005 in the same repository, 25 Aug 2026. The clause carries the measurement as a comment so nobody tidies it back into scene order. Measured with `kit/tools/pascal/dgimage.py` for the initialised image, `kit/tools/substrate/segmap.py` for the segment sizes, and `spans.py` for the number that did not move.
