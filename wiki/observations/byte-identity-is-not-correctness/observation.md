---
type: Observation
title: Byte-identity is not correctness, and the difference is invisible to every byte instrument
description: Six routines matched the original byte for byte and the whole data group sat at shift zero while two declarations were wrong -- a font array based at the wrong subscript and a coordinate record with its fields transposed -- and both showed to the byte instruments only as small size differences, indistinguishable from ordinary transcription slack.
tags: [verification, measurement, reconstruction, blind-spot, instruments]
measured_on: a 16-bit Pascal rebuild, two wrong declarations behind six byte-identical routines
timestamp: 2026-09-04T00:00:00Z
---

# Byte-identity is not correctness, and the difference is invisible to every byte instrument

A reconstruction measured by byte comparison accumulates a comfortable set of green numbers: this routine is identical, that unit is exact, the data group is wholly in place. It is easy to read those as progress towards a working program. They are not the same measurement, and the gap between them is exactly the part no byte instrument can see.

On one target the numbers said: six routines byte-identical against the original, three of five units exact on their linker-map lengths, and 163 absolute data references paired at a shift of zero -- the entire data group in the right place. At that moment two of the reconstruction's declarations were wrong, and both were wrong in a way that ruined what appeared on screen.

* A font was declared `array [0..58]` where the original's was `array [32..90]`. Both hold 59 glyphs and both are 15104 bytes. The lookup for `'A'` therefore read 8192 bytes past the glyph it wanted, and **every character the program drew was garbage.**
* A coordinate pair was declared `record Y, X : Word` where the original's is `record X, Y : Word`. Every sprite was placed transposed, so a word spelled horizontally across the screen came out as a vertical column.

## Why it works

**A wrong declaration of the right SIZE changes almost no bytes.** The font's bounds moved one displacement constant, from `-0x11` to `-0x2011`; the whole routine was otherwise the same instructions in the same order, eight bytes short of the original. The transposed record changed which of two adjacent words each `MOV` fetched -- same instruction, same length, different operand. Neither produced a run of differing bytes; both produced the kind of small size delta that a half-finished routine produces anyway.

So the instruments were not broken and they did not lie. They were asked *do these bytes agree*, they answered honestly, and that question has no opinion about whether the program does the right thing.

**The two failures are also the ones a reader is least likely to reason about.** An array's lower bound and a record's field order are both invisible at the point of use: `Font^[Ch][J][I]` and `Path^[N][I].X` read correctly whichever way they were declared. Nothing in the source looks wrong. The evidence lives in the declaration, tens of lines away, and in the binary's displacement constants, which nobody reads unless a number is already suspect.

## Blind spot

**A watched run says THAT something is wrong and almost never WHERE.** What it reported here was "the text is unreadable" and "the sprites are in the wrong place". It could not say that a subscript base was 32 rather than 0. Localising still needed the byte comparison: the displacement differing by exactly `0x2000` is what named `32 * 256`, and the coordinate ranges in the data file -- one word spanning 38..243 where the screen is 200 high -- are what named the field order.

So neither measurement dominates. The run is the only thing that detects this class of defect; the bytes are the only thing that locates it. Used together the diagnosis took minutes. Used apart, the run gives you a symptom you cannot chase and the bytes give you a green light you should not trust.

**And a watched run cannot be delegated or inferred.** Nothing in a toolkit can look at a screen. That is why the observation is worth writing down rather than automating: the fix is an ordering decision by a person, not an instrument to add.

## Cost

One staged run, watched for about thirty seconds, beside the original for comparison. Both defects were obvious in a single screenshot pair and neither had been suspected.

Against that: the two declarations had been in place across roughly a dozen measured iterations, and every one of those iterations reported progress.

**The rule worth taking: stage the watched run as early as the program will start, not once the bytes look good.** A program that starts is enough -- it does not need to be close. The instinct to make the numbers respectable first is what hides this class of defect for as long as it takes to run out of numbers to improve.

## Example

A 1993 DOS demo rebuilt from its shipped binary, 4 Sep 2026.

At the point the two defects were found, the record held: `WaitRetrace`, `FadeStep`, `PutSprite`, `PutStrip`, `SetRGB` and `MoveBlock` byte-identical; `CyclePalette` and `ScrollUp` size-exact and differing only at far-call fixups; the third-party unit, the reconstruction's own unit and the runtime's `Crt` all exact on length; `dsmap` reporting 163 references at shift zero across the whole data group. The remaining gap was diagnosed, correctly, as a compiler-build difference in how intermediates are spilled -- a conclusion that survived the discovery of both bugs, because it was about the bytes and the bugs were not.

The font's defect showed as `PutGlyph` being 168 bytes against 153, then 145 against 153 after an unrelated fix -- a delta that sat unremarkably among five other routines with similar deltas, all of which turned out to be the compiler difference rather than a defect. The record had it on a working list as a size to close, not as a bug.

The transposed record showed as nothing at all. `DrawFrame` was 99 bytes against 111, which was read -- correctly -- as the same compiler difference.

Then one screenshot beside the original: the text strip rendering as overlapping blobs where the original reads `INTERNATIONAL MAIL`, and a swarm of sprites standing in a vertical column where the original spells a word across the screen.
