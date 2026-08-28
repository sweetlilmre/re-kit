---
type: Observation
title: The main program is a list of every unit's entry-point offsets
description: "A part's own program segment calls each unit's routines by absolute offset, so comparing it byte for byte checks every entry point at once -- and it catches what a coverage walk and a segment-size check both miss: routines in the wrong order inside a right-sized segment, a unit displaced by whole paragraphs, and bytes the rebuild has that the original does not. Prologue offsets then localise the defect to one routine, and separate two errors that cancel."
tags: [layout, code-segment, verification, tooling, reconstruction, measurement, pascal]
timestamp: 2026-08-27T00:00:00Z
---

# The main program is a list of every unit's entry-point offsets

Three instruments said a part was finished. The coverage walk aligned every byte of every user segment. Every segment was the original's exact size. The initialised data image compared identical. One unit still had a routine in the wrong place, and the thing that found it was the smallest segment in the file: **the program itself**.

A compiled main body is almost nothing but far calls. It opens with the unit-initialisation chain -- one call per unit, in reverse of the link order -- and then calls each scene, each helper, the runtime's exit. **Every one of those calls names a segment and an OFFSET, so the program segment is a table of every unit's entry points, written by the compiler, in a form that cannot drift.** Compare it byte for byte and a routine that has moved inside its own unit announces itself immediately:

    1000:0082   original  LCALL 1139:03b4
                ours      LCALL 1139:03a2

That is eighteen bytes of displacement inside a unit whose segment was the right size, whose every routine the walk had scored aligned, and whose data image was identical. The cause was one routine defined at the end of the file behind a `forward` where the original has it in the middle.

## Why the other instruments cannot see these

**A coverage walk locates each segment's content wherever it sits.** That is what makes it robust, and it is exactly why it is blind to arrangement: a routine in the wrong place is still a routine it finds. It also counts the ORIGINAL's bytes, so **bytes the rebuild has and the original does not are invisible to it by construction** -- one unit was thirteen bytes too long while the walk reported 100%.

**A segment-size check rounds to a paragraph**, so it hides an error of one to fifteen bytes. Read the RAW length from the map as well, and beware: a unit with external `.OBJ` code linked after it has that code outside the map's length column, so take the segment's extent from the NEXT segment's start instead.

**And a total that balances hides an ordering.** In one part a unit was 64 bytes -- four paragraphs -- short, every segment after it sat four paragraphs low, and the walk still reported every byte aligned.

The program segment has none of those weaknesses. It is small, it is absolute, and it is not a total.

## What it found, once it was being read

On one target, in one pass over seven programs:

* A routine defined last behind a `forward` where the original has it mid-segment -- eighteen bytes, invisible to everything else.
* **Five of seven programs carrying their exit twice.** `end.` already emits the runtime exit; an explicit `Halt(0)` as the last statement emits that sequence a second time. Seven bytes each, and the comment beside each one pointed at the address of the single copy the original has, which is what a doubled one looks like.
* **Programs missing the 286 switch.** The directive that enables `PUSH imm8` and `LEAVE` is per-file, and a program is a file -- nothing inherits it from the units it uses. Two bytes per immediate argument and one at the teardown.
* A unit four paragraphs short, and another thirteen bytes long.

Four of those programs then rebuilt byte-identical, and a fifth on the first build after its harness was removed.

## Then prologue offsets localise it

The program segment says a unit is wrong and by how much; it does not say where. **Take every prologue in the unit -- ENTER imm,0 and PUSH BP / MOV BP,SP -- on both sides and subtract.** The output is a per-routine displacement, and it separates what a length total cannot:

    routine   orig     ours     drift
    ...       0x287    0x287    +0
    0x287     0x3d7    0x3cf    -8      <- this routine is 8 bytes SHORT
    0x446     0x562    0x563    +9      <- and this one 9 bytes LONG

**Two defects nine and eight bytes in opposite directions inside one unit, cancelling to +1.** Neither is visible in any total. Worse, fixing either ALONE makes every downstream measurement worse -- the second defect stops being hidden, the unit changes size, and every segment after it moves a paragraph. They have to close together, and knowing that before starting is the difference between one careful change and a day of thrashing.

## Blind spot

**A masked instruction diff over a whole unit is not safe across a defect.** Once the offsets have drifted, the "original" side it pairs with each of your instructions is whatever sits at the drifted address, not the counterpart. Acting on such a pairing produced two changes that were individually plausible, both wrong here, and both measurably worse. **Diff one routine at a time, anchored on its own prologue**, and use the prologue offsets first to decide which routine.

**And a prologue scan finds things that are not routines** -- the byte patterns occur in data and inside longer instructions. Cross-check the count against the map and against the routines you can name; an assembler routine may open with no recognisable prologue at all.

**The program segment cannot see a unit's internals** when two errors cancel exactly, and it cannot see anything about a part whose main body you have not reconstructed -- which is the case for as long as a test harness supplies the program. That is one more reason to retire the harness early: it is not only two segments the original does not have, it is the loss of the instrument that reads all the others.

## And the localiser finds what even this cannot

The program segment checks ENTRY POINTS. A routine that moves but is not itself
an entry point, in a unit whose total size is still right, is invisible to it as
well -- and on one target exactly that happened twice over. A routine had been
moved into what looked like the correct position; the program segment went
byte-identical, the walk read 100%, and the routine was still 92 bytes out of
place, because the two errors it created cancelled BEFORE the entry point the
program calls.

**The per-routine prologue drift is what caught it**, and only after the
candidate list was filtered to prologues that something in the segment actually
CALLS. Unfiltered, the two sides are paired by index, so one false positive in a
different place on each side shifts every row below it and invents a large
cancelling pair that is not there. That false alarm appeared on a segment whose
entry points were byte-identical, which is how it was noticed; the filter removed
it and the same run then reported the real 18-byte pair.

Rows at or past the unit's initialisation section are a separate matter: that
section is the compiler's last output, so anything after it arrived from an
`.OBJ`, and a one-byte row there is a scan artefact rather than a finding.

## Cost

One byte comparison of a segment that is typically 80 to 350 bytes. It should run after every build, on every part.

## Example

Psycho Neurosis (Asphyxia, 1994), seven parts in Borland Pascal 7. Comparing each part's segment 1000 against the 1994 file found the doubled exit in five programs, the missing 286 switch in three, a 240-byte program that had been built at 256 with no check reporting it, and one unit's routine eighteen bytes out of place. Six of the seven program segments then rebuilt byte-identical and all ten targets reached 100% of every user byte. The seventh is two bytes, localised by prologue offsets to two routines that cancel. [1]

# Citations

[1] src/NEUR1.PAS through src/NEUR7.PAS, src/PART3_MORPH.PAS and src/P1S4.PAS in the psycho repository; measured against work/split/NEUROSIS_00n.exe with the compiler's map file on 27 Aug 2026.
