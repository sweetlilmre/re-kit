---
type: Observation
title: The comment you are required to write is the one the stripper cannot remove
description: Two rules of this method meet on the same line and neither page mentions the other. Hand-written assembler must carry a comment on every line, and a trailing comment on a line of code is never dropped by the stripper -- so every one of those comments is permanent, unfilterable text in the readable copy. Write apparatus there and it survives into the copy made for a reader who cannot check it, invisible to the tag checker because it carries no mechanical tell and invisible to the assembler audit because that only checks a comment is present.
tags: [tooling, documentation, verification, blind-spot, instruments, reconstruction]
measured_on: a 1993 demo reconstruction, four source files, the first run of the stripper
timestamp: 2026-09-04T00:00:00Z
---

# The comment you are required to write is the one the stripper cannot remove

Two rules of this method meet on one line of source, and neither is stated anywhere near the other.

* **Hand-written assembler carries a comment on every line.** That is the transcription rule, and an audit enforces it.
* **A trailing comment on a line of code is never dropped.** That is the stripper's rule, and it is right: a note on an instruction belongs to the instruction, and removing it would leave bare opcodes.

Put together: **every comment the first rule obliges you to write is one the second rule guarantees will reach the readable copy.** There is no tag that removes it, because tagging works on whole comment paragraphs and this is not one.

## Why that matters more than it sounds

The readable copy exists for somebody who wants to understand the program and is *not* looking at the original binary. A comment that says

```
inc dx        { 3C5, the data port -- the original steps rather than reloads }
```

tells that reader about a comparison they cannot make, against an artefact they do not have. It is apparatus wearing the clothes of program documentation, and it is permanent.

**Neither instrument sees it.** The tag checker looks for mechanical tells — an address, a `DS:$`, a tool's name — and a sentence about "the original" has none. The assembler audit checks that a comment *exists*, never what it says. So the class is invisible to both, by construction, and the only thing that surfaces it is running the transform and reading what came out.

## Measured

First run of the stripper on a four-file tree, after a whole reconstruction written under the tagging discipline with the tag checker green throughout:

| leak | where |
|---|---|
| 3 | per-line assembler comments comparing against the original |
| 4 | equivalent-Pascal blocks whose justification sentence explained why the code was transcribed |

Zero of the seven carried a mechanical tell. The stripper itself reported *0 comments still mention an address*, correctly — none of them did.

## What to do

**Write a per-line assembler comment as though the original did not exist.** Say what the instruction does: `3C5, the Sequencer data port`. If the interesting thing is *why this was transcribed rather than written in Pascal*, that is a paragraph above the block, and it gets tagged.

The equivalent-Pascal block the audit also wants is a paragraph, so it can be split: the Pascal itself is explanation and stays, and the sentence about what the original emits is evidence and goes.

**And run the transform early.** It is the only instrument that finds this, and it costs one command. Leaving it to the end means every line written in between is a line to re-read.

## Blind spot

**This is a rule about audience, and no checker can enforce it.** "Does this sentence assume the reader has the original?" is exactly the judgement the tagging discipline exists to make, and moving it to a per-line comment does not make it mechanical. A tool could flag words like *original* or *transcribed*, and that would be a style gate crying wolf on prose that legitimately uses them in the annotated copy — where they belong.

The scan used here — grep the stripped output for a handful of apparatus words — is a reader's aid and not a gate. It found seven; it cannot promise there is no eighth phrased differently.

## Cost

One run of the stripper, and reading the result. The seven above took a few minutes to split once they were visible.

## Related

* `tag-at-write-time` — more than half of tagged apparatus carries no mechanical tell, so the checker guarding it is blind to most of what it guards. This is the sharpest corner of that: a line where the tag cannot be applied at all.
