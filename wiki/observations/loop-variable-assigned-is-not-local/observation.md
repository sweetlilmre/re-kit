---
type: Observation
title: A loop counter the binary assigns to proves nothing about where it lives
description: RETRACTED AND REPLACED. This page used to say Turbo Pascal refuses assignment to a for-loop control variable declared in the same routine, and that a store into the counter therefore proves the counter is unit-level. A probe says otherwise -- TP7 accepts the assignment for a local counter, with or without an enclosing `with`, and emits the store. The inference was unsound. What survives is the source SHAPE the store points at, which is worth recognising for its own sake.
tags: [pascal, turbo-pascal, source-shape, loops, variables, reconstruction, retraction, measurement]
timestamp: 2026-08-26T00:00:00Z
---

# A loop counter the binary assigns to proves nothing about where it lives

**This page previously carried the opposite claim and it was wrong.** It said Turbo Pascal refuses `N := Limit` inside `for N := 1 to Limit` when `N` is declared in the same routine, accepts it when `N` is declared outside, and that a binary storing into its own loop counter has therefore *proved* the counter is unit-level. The middle step does not hold, so neither does the conclusion.

## What the probe says

Three placements, one unit, driven through the compiler:

```pascal
procedure P1(var R : Integer);          { local counter, bare loop body }
var N : Integer;
begin
  for N := 1 to 25 do begin R := N;  N := 25 end;
end;

procedure P2(var R : Integer);          { local counter, inside a `with` }
var N : Integer;
begin
  for N := 1 to 25 do
    with Rec do begin A := N;  N := 25 end;
end;

procedure P3(var R : Integer);          { counter declared outside }
begin
  for G := 1 to 25 do begin R := G;  G := 25 end;
end;
```

**All three compile.** P1 and P2 each emit `MOV WORD PTR [BP-2],25` — the local counter, stored into, from inside the loop that controls it. There is no error and no warning. The `with` is irrelevant; the bare case compiles too.

So the diagnostic that page described does not exist in this compiler, and any conclusion drawn from it about a counter's scope was drawn from nothing.

## What actually survives

**The source shape.** A binary that sets its counter to the loop's limit and then falls out through the loop's own bottom test really is a different shape from one that jumps out, and recognising it still matters:

    mov  word ptr [bp-2], 19h      ; N := MaxLem
    inc  word ptr [51Eh]           ; Inc(LiveCount)
    cmp  word ptr [bp-2], 19h      ; the for loop's own test
    je   <after the loop>
    jmp  <top>

against what `Exit` gives, which is a jump straight to the epilogue. So when you see the counter assigned its limit, write **`N := Limit`**, not `Exit` and not a flag — and the ORDER is readable too, since the store above precedes the `Inc`.

That is a statement about which spelling to write. It says nothing about where the variable is declared, and the frame is what answers that: an `ENTER` operand that accounts for the counter, and a `[BP-n]` reference rather than an absolute one.

## How the error survived

Because it was **plausible and useful**. Delphi does reject this, later Object Pascal dialects reject it, and the rule reads like something a Pascal compiler ought to enforce -- so it was written down as known rather than measured, and it then did real work: it "explained" counters that looked like they should be locals. An inference that resolves a puzzle is the hardest kind to doubt.

The check costs one probe unit and one build. It should have been run when the claim was first made.

## Blind spot

**A compiler switch or a later release may still refuse it.** This was measured on one Turbo Pascal 7 installation with this project's switch line. If a target was built by a different Borland release, re-run the probe rather than trusting either version of this page.

**And the retraction does not reach downstream conclusions on its own.** Anywhere this rule was used to argue a counter must be unit-level, that argument is now unsupported and the placement needs deciding on the frame instead. Some of those placements may still be right for other reasons.

## Cost

One probe unit, three procedures, one build.

## Example

Part 004 of a 1994 VGA demo. `Spawn` opens `ENTER $06` with its counter at `[BP-$02]` -- provably a local -- and 1005:07c4 stores `$19` into that slot, which the old rule declared impossible. Writing `N := MaxLem` in place of `Exit` compiled without complaint and emitted the original's instruction exactly, taking the part from 99.3% to 99.4%. [1]

## Citations
[1] `probe/FORASGN.PAS` and `src/P4LEMS.PAS` in the psycho repository; driven with `kit/tools/pascal/codegen.py` on 26 Aug 2026.
