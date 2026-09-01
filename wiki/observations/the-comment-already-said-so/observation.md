---
type: Observation
title: The comment already said so, and the code did not do it
description: In a long reconstruction, the commonest place a defect hides is a comment that states the right answer beside code that does something else. The note was written while somebody was reading the binary; the code was written from a guess, or was written first and never revisited. Grepping your own comments for claims the code does not honour is a search strategy with a measured hit rate, not a curiosity.
tags: [reconstruction, method, source-shape, blind-spot, comments]
timestamp: 2026-08-25T00:00:00Z
---

# The comment already said so, and the code did not do it

A reconstruction accumulates comments as it goes: an address, a frame size, a stride, a sentence explaining what the original does at some offset. Each one is written at the moment somebody was reading the binary and understood something.

**The code beside it is often written from a different, earlier, worse understanding -- and nothing forces the two to agree.** So the note stays right while the code stays wrong, sometimes for weeks, and every instrument passes over it because instruments read code.

This is not an amusing anecdote about documentation. On one target it accounted for **five separate defects in a single day's work**, including the two largest of that day. It is worth running as a deliberate pass.

## The pass

Grep your own comments for the kinds of claim that are checkable against the declaration or statement next to them:

    grep -nE 'DS:\$|ENTER \$|stride|bytes|unit-level|BY VALUE|fans out' src/*.PAS

Then read each hit against what the code actually does. The productive shapes:

| the comment says | check that the code |
|---|---|
| a `DS:` address for a variable | declares it at unit level, not as a local or a heap pointer |
| a size in bytes, or `stride N` | declares something of exactly that size |
| `ENTER $nn` | has a `var` block that adds up to `$nn` |
| routine A "fans out to" or "calls" B | actually has a routine B for A to call |
| a named constant's value | uses that value, and as a constant of the right kind |

**The strongest single form is an address beside a declaration that is not unit-level.** `{ DS:$6A33, stride $100 }` above `var Rows : array[1..8] of String` declared *inside a procedure* is a contradiction in two words: a `DS:` address is a data-segment address, and a local has none. Nothing but a human reading both halves will notice.

## Why the note is usually the reliable half

Both halves were written by the same effort, so this is not about trusting prose over code. It is about *when* each was written:

- **A comment recording an address, a frame size or a stride is a transcription of something measured.** Somebody had the disassembly open. It is nearly free to write and nearly always right.
- **The code is an interpretation**, often written before that measurement existed, and often written to make some *other* number come out.

Two corollaries worth having. **A comment beside the code that USES a variable beats one beside its declaration** -- the first was written while somebody was reading the arithmetic, the second may be a fossil from the original guess. When two comments in one file disagree about an address, that is the tie-breaker. And **a comment can be right about the diagnosis while being wrong about the fix**, so read what it *observed*, not what it *concluded*.

## Blind spot

**A comment can be stale rather than prophetic, and there is no way to tell from the comment.** In one case the same array had two addresses recorded in one file, 2,048 bytes apart. The way to arbitrate is arithmetic, not authority: adopt the reading under which the surrounding declarations **tile** -- each address plus its size reaching the next -- and if neither does, you have found a third defect rather than resolved the first.

**It finds defects, not their sizes.** A comment saying a variable is unit-level does not say how big it is, and a comment giving a size does not say where the variable goes. Expect to do the measurement anyway; what the pass buys is knowing where to point it.

**And it cannot see what nobody has read yet.** The pass only covers ground somebody has already understood well enough to write a note about, so it is strongest on a mature reconstruction and says nothing about a segment nobody has opened. It is a way of harvesting work already done, which is exactly why it is cheap.

## Cost

One `grep` and the reading. No build, no disassembly, no instrument.

## Example

Five in one day on part 001 of a 1994 megademo, in the order they were found:

1. **A per-point 3D transform.** A comment read *"`12c5:02e3` -- `Obj_TransformAll(Obj, A1, A2, A3)`, which fans out to `12c5:01b0`"*. There was no routine at `12c5:01b0` in the reconstruction -- its body was inlined in the caller's loop. Extracting it removed every unaligned span in a 768-byte range where ten had stood.

2. **A projection scale.** A comment gave a formula; the code computed a different one. Same file, weeks old.

3. **`Font`'s address.** The declaration said `DS:$7233`; the drawing routine that indexes it said `DS:$6A2A`. Neither matched the code, which had `Font` as a **heap pointer** -- four bytes where the original has 3,776 inline. Worth 3,772 bytes of data displacement, confirmed to the byte.

4. **Eight row buffers.** The unit's header comment had said *"eight row buffers at `DS:$6A33` (stride `$100`)"* since the routine was first read. The code declared them as `array[1..8] of String` **inside a procedure**. A `DS:` address on a local is the contradiction in the previous section, verbatim. Worth exactly 2,048 bytes, and the frame corroborated independently: the original's `ENTER $202` is 514 bytes and cannot hold them.

5. **A translation vector.** A comment named three variables the routine reads from a record; the code read three unit-level globals instead.

Numbers three and four were that day's two largest data findings, and both had been sitting in plain text. [1]

Worth noting what the pass is *not* competing with. The same day's instruments were working correctly and reporting real, quantified damage -- a data-reference map gave the shortfall to the byte and a triage tool named the exact address a dozen spans traced back to. What they could not do was say *which declaration*. The comments could, because somebody had already worked it out and written it down. [2]

## Citations
[1] `src/P1BALLS.PAS` and `src/P1VECTOR.PAS`, part 001, in the psycho repository, 25 Aug 2026; each measured with `kit/tools/pascal/spans.py` and `dsmap.py` against the shipped binary and recorded in that project's register.

[2] The same day. The instruments were `dsmap.py`, `spanwhy.py` and `prologue.py`; the shortfall they quantified went from 23,530 bytes to 17,710 on the two comment-derived findings alone.
