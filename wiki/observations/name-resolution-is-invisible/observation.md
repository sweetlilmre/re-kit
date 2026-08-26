---
type: Observation
title: Every instrument reads clean and the screen is blank
description: A local declaration that shadows a unit-level one of the same name compiles, links, measures identical on every static instrument, and produces a program that does nothing. Coverage walks, initialised-image compares and reference maps all measure bytes; none of them can see WHICH object a name resolved to. On this class of defect a watched run is not a formality after the measurement -- it is the only instrument that works.
tags: [verification, measurement, blind-spot, pascal, scoping, reconstruction, tooling, behaviour]
timestamp: 2026-08-26T00:00:00Z
---

# Every instrument reads clean and the screen is blank

The coverage walk says 99.0%. The initialised image compares byte for byte with no difference. The floating-point trap streams are identical opcode for opcode. The reference map pairs a hundred and sixty-four absolute displacements with a hundred and forty-eight of them at zero shift. Every static instrument you own has been run and every one of them passes.

Then somebody runs it and the scene is a flat red screen.

## The shape

Two routines in one unit. A file record declared at unit level, because the original addresses it absolutely from two different routines. And a scene entry point that opens the file:

```pascal
var
  F : file;                      { DS:$563F -- unit level }

procedure LoadLogo(Name : String; Dest : Pointer);
begin
  BlockRead(F, Pal, SizeOf(Pal));      { the unit-level F }
  BlockRead(F, VirtScr^, 64000);
  ...
end;

procedure Scene1;
var
  F : file;                      { <-- and this one shadows it }
begin
  Assign(F, 'neurosis.dat');
  Reset(F, 1);
  LoadLogo('asphyxia.cel', VirtScr);
  Close(F);
end;
```

`Scene1` opens its own `F`. `LoadLogo` reads the unit's `F`, which nothing ever opened. **Both names are spelled the same and they are different objects.** The compiler is perfectly happy: each reference resolves to the nearest declaration, which is what the language says it should do.

With I/O checking off -- and it is off, because the original goes straight on after each file call -- both `BlockRead`s fail silently and return nothing. The palette buffer keeps the 768 bytes of uninitialised stack that were already there, and those get written to the DAC. The screen buffer is never filled. A flat wrong-coloured screen, and nothing else.

## Why nothing static can see it

**Because the defect is not in the bytes.** Work through what each instrument actually measures:

- **A coverage walk** compares the emitted code of each routine against the original's. A `BlockRead` call is the same four pushes and one far call whichever `F` it names; only the operand differs, and a frame-relative operand against a DS-relative one is a couple of bytes inside a routine already matching. Measured 99.0% before the fix and 99.0% after.
- **An initialised-image compare** reads the data segment's initialised bytes. A `file` record is uninitialised either way, and a local one lives on the stack and occupies no data segment at all. Identical before and after.
- **A reference map** pairs absolute data displacements. The shadowed reference is not absolute -- it is `[BP-n]` -- so it produces no row to pair. Invisible by construction.
- **A lint pass** over the sources: 0 problems in 67 files. A shadowing declaration is legal, and a checker that flagged it would fire on every correctly-shadowed name in the tree.

None of these instruments is weak here. They are measuring bytes, and the defect is in **name resolution** -- which object a spelling means. That is a property of the program's structure, not of its emitted size or content, and it is precisely what a byte-level comparison abstracts away.

## What does see it

**Running it.** That is the whole answer, and it is worth stating plainly because the ordering usually goes the other way: measure first, then run to confirm. On this class of defect the run is not a confirmation of the measurement, it is the only measurement that exists.

The second thing that sees it is **the original's own disassembly**, read for structure rather than for bytes. One instruction settled this case:

    0678  55              push bp
    0679  89 e5           mov bp, sp
    067b  bf 3f 56        mov di, 0x563f      ; Assign
    068a  bf 3f 56        mov di, 0x563f      ; Reset
    06a6  bf 3f 56        mov di, 0x563f      ; Close

**`PUSH BP` / `MOV BP,SP` with no `ENTER` means the routine has no locals at all** -- so there is no local `F` to have, and the question is closed before it is asked. And all three file calls carry the same absolute displacement as the read in the other routine, which says the file is opened by one routine and read by another. See [The frame's size counts the locals](../frame-size-counts-locals/observation.md) for the prologue as a locals census, which is the same reading used forward instead of backward.

## The general rule

**A static compare cannot distinguish two objects with the same name.** Any defect whose content is "the right code operating on the wrong object" is outside what these instruments measure -- shadowed variables are the clearest case, but the family includes a routine calling the wrong overload, a `with` binding a different record than intended, and a unit-qualified name resolving to the other unit's export.

For that family the order of work inverts. Normally: read, edit, measure, then run to confirm behaviour. Here: **the run comes first as a detector**, and the measurement only tells you that whatever you did next did not cost anything.

## Blind spot

**This observation does not give you a way to FIND these.** It tells you that your instruments cannot, which is worth knowing and is not the same thing. The practical mitigations are narrow: prefer distinct names when a unit-level object is deliberately reached from more than one routine; read the original's prologue before declaring any local at all, because a routine with no `ENTER` cannot have one; and treat "every instrument passes and it still looks wrong" as pointing at scope rather than at bytes.

**And a run is expensive.** It needs a person watching a real machine, so it cannot be put in a loop. That is an argument for running after any change that moves a declaration between scopes, not for running after everything.

## Cost

Nothing to detect once someone has watched it, and one deleted declaration to fix. The expensive part is the days it can survive while every check passes.

## Example

Part 001 of a 1994 VGA demo. Its first scene had been reconstructed to 99.0% coverage with a byte-identical initialised image and identical trap streams, and showed a flat red screen on a watched run. `Scene1` had grown a local `F : file` while `LoadLogo` read the unit-level one; the original's `Scene1` opens with no `ENTER` and addresses `DS:$563F` three times.

Removing one declaration fixed it. Coverage after the fix: 99.0%, unchanged to the byte, with the same single unaligned span as before. **The instruments recorded the repair as a no-op.** [1]

The same disassembly, read at the same sitting, also gave up two ordinary findings the byte instruments *could* see -- an argument pair the wrong way round, and a declaration order that the routine's own recorded addresses tiled out exactly -- which is the usual return on reading a segment rather than re-reading the reconstruction.

# Citations

[1] `src/P1S1.PAS`, part 001 in the psycho repository; measured with `kit/tools/pascal/spans.py`, `dgimage.py`, `dsmap.py` and `fpusites.py`, and detected by a watched DOSBox-X run on 26 Aug 2026.
