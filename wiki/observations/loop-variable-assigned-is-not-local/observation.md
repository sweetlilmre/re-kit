---
type: Observation
title: A loop counter the binary assigns to cannot have been a local
description: Turbo Pascal refuses assignment to a for-loop control variable declared in the same routine, and accepts it when the variable is declared outside. So a binary that stores into its own loop counter mid-loop has proved that counter is unit-level -- which explains counters that look like they should be locals, and rules out the flag-and-Break idiom a reconstruction reaches for instead.
tags: [pascal, turbo-pascal, source-shape, loops, variables, reconstruction]
timestamp: 2026-08-25T00:00:00Z
---

# A loop counter the binary assigns to cannot have been a local

You are reading a nested loop that leaves early. The reconstruction writes what any Pascal programmer would:

    Done := False;
    for Row := 1 to 8 do
    begin
      if Done then Break;
      for Col := 1 to Length(Rows[Row]) do
        if ... then begin Done := True; Break end;
    end;

The original does something else. At the exit point it stores the loop's *limit* into the loop's own counter:

    MOV WORD PTR [$6A2D], 8        ; Row := 8
    MOV WORD PTR [$6A2F], AX       ; Col := Length(Rows[Row])

Both loops then run out naturally on their next test. **There is no flag and no `Break`** -- and the absence of the flag is the smaller half of what this tells you.

## The inference

Turbo Pascal rejects an assignment to a `for` statement's control variable with *Error 97: Assignment to FOR-Loop variable* -- but only when the variable is **local to the routine containing the loop**. A variable declared at unit level is not covered by the check and compiles without complaint.

So the store above is not merely a style choice. It is a **proof about where the variable is declared**:

| the binary | what the source must have |
|---|---|
| stores into the loop counter inside the loop | the counter is declared OUTSIDE the routine |
| absolute address (`[$6A2D]`) rather than `[BP-n]` | corroborates it independently |

The two lines of evidence are worth keeping separate, because either can appear alone. An absolute address says unit-level on its own. But a counter at `[BP-n]` that the loop assigns to is a **contradiction**, and it means you have misread either the loop or the store.

Read the other way, this is why some counters are unit-level when nothing else about them suggests it. The author wanted the assignment idiom and the compiler made them move the variable to get it -- so an odd-looking declaration is a *consequence* of a statement three screens away.

## Why it works

The restriction exists so the compiler can keep a local counter in a register or optimise the loop's bookkeeping, and BP7 enforces it syntactically over the enclosing routine's scope only. It has no view of what another unit's code might do to a global, so it cannot enforce it there and does not try.

## Blind spot

**It says the variable is not local to THIS routine, not that it is unit-level.** A `for` in a nested procedure may assign to a counter belonging to the enclosing routine, which is also outside the check. Look for the static link at `[BP+4]` before concluding a global; see [Every element read costs fourteen bytes and goes through the frame twice](../nested-static-link/observation.md).

**The converse is not a proof.** A loop that never assigns to its counter says nothing at all about where the counter lives -- most loops are like that, and most counters are local. This only fires when the assignment is there.

**And it does not fire on `while`.** A `while` loop's variable is an ordinary variable and can be assigned freely wherever it is declared, so a hand-written `while` that mutates its own counter carries no information. Confirm the loop really is a `for` -- BP7's `for` evaluates a non-constant limit ONCE into a temporary before the first test, and that spilled limit is the cheapest way to tell the two apart.

## Cost

Reading one store. The confirmation, if you want it, is one build.

## Example

A banner routine at `1107:07a2` in a 1994 VGA demo walks eight strings looking for marker characters and stops when it has collected 144 points. The reconstruction used a `Boolean` flag and two `Break`s, with `Row`, `Col` and `Idx` as ordinary locals -- and its frame was wrong, its counters were at `[BP-n]` where the original's are at absolute addresses, and 291 bytes of the segment would not align.

The original's counters are at `$6A2D`, `$6A2F` and `$6A31`, and at `1107:0933` it assigns `8` to the first of them. Rewritten that way -- `for` loops over three unit-level Integers, with the exit written as `Col := Length(Rows[Row]); Row := TrailRows` -- the routine's whole span disappeared and the part moved 83.7% to 85.1%.

**The compiler rule was tested rather than assumed.** The first attempt used `while` loops, on the theory that BP7 would reject assignment to a `for` variable outright; that compiled but left the frame two bytes wrong, because a `while` re-evaluates `Length` every pass where the original spills it once. Changing them to `for` loops -- assignment and all -- compiled without complaint and matched the frame exactly. One build settled what could have been an argument, and the `while` version's residual frame is what said the answer was still wrong.

Three details corroborated the reading, each independently: the counters' six bytes **tile** exactly between a 768-byte palette ending at `$6A2D` and the string buffers beginning at `$6A33`; the frame's 514 bytes turned out to be **entirely compiler temporaries** once the counters moved out, being one loop limit and two 256-byte `Copy()` results; and the eight string assignments proved to be **unrolled**, with eight literal destination addresses in sequence rather than a loop. [1]

# Citations

[1] `src/P1S4.PAS`, part 001 segment `1107`, in the psycho repository; measured with `kit/tools/pascal/spans.py`, `prologue.py` and `framehist.py` against the shipped binary on 25 Aug 2026.
