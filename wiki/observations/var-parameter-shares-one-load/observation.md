---
type: Observation
title: A var parameter shares one load where a pointer cannot
description: Turbo Pascal keeps a var parameter's address in ES:DI across a run of adjacent statements that name it, and needs no hidden slot to do so. A pointer parameter must be re-loaded for every mention, and the one construct that would share a load -- a nested with -- is allocated its own four-byte slot regardless. So a routine whose frame and whose single pointer load both have to match can be reachable with a var parameter and unreachable with a pointer, and no amount of re-spelling the statements will find it.
tags: [pascal, codegen, stack-frame, with, parameters, reconstruction, measurement]
measured_on: unrecorded
timestamp: 2026-08-27T00:00:00Z
---

# A var parameter shares one load where a pointer cannot

A reconstruction sat one byte from byte-exactness for several sessions. The byte was an operand:

    original   les di, [bp + 0x0a]     C4 7E 0A     the parameter
    ours       les di, [bp - 0x13]     C4 7E ED     the with's hidden slot

Same instruction, same length, same three `add`/`adc` pairs after it reading `es:[di]`, `es:[di+4]` and `es:[di+8]`. Six spellings of those three statements were built and measured. The answer was not in the statements at all: **the routine's parameter was declared as a pointer where the original had a var parameter.**

## The two facts that have no common solution under a pointer

**A pointer dereference is re-loaded for every mention.** `P^.Field` loads `P` each time, so three field references give three `LES` instructions. There is no expression-level sharing.

**The one construct that shares a load is allocated a slot.** A nested `with` over the record loads its address once and reads all three fields off `ES:DI` -- but Turbo Pascal reserves a four-byte address slot for a `with` whether the body needs one or not, so the frame grows by four. Measured twice, on two different targets.

So for a routine that must produce *one* load **and** a frame with room for only *one* slot, a pointer parameter admits neither answer. Sharing costs a slot; not sharing costs two extra loads. Re-spelling cannot escape a structural constraint, and six attempts did not.

## What a var parameter does instead

**Its address IS the frame slot.** `[BP+n]` holds the far pointer the caller pushed, so there is nothing to spill and nothing to keep in step. The compiler will hold it in `ES:DI` across a run of adjacent statements that name the parameter -- and, crucially, needs no hidden slot to do it:

```pascal
procedure Transform(var Base : TWork; ...);
...
  with Base do                         { spills the address for the indexed
  begin                                  accesses -- Trail[I], Outp[I] }
    ...
    T.X := T.X + Base.Trail[0].X;      { ONE les di,[bp+n] ... }
    T.Y := T.Y + Base.Trail[0].Y;      { ... es:[di+4] ... }
    T.Z := T.Z + Base.Trail[0].Z;      { ... es:[di+8], no reload }
```

Both readings land at once: the `with` still spills the address for the indexed references, and the three explicit mentions share a single parameter load. The routine came out byte-identical, and so did the last of ten binaries.

**The run has to be uninterrupted.** A call between the statements ends it -- after a call the compiler must reload, because `ES:DI` is not preserved. That is the same rule that governs a `with` body, and it is why the sharing works for a *run* of statements inside a body that calls things elsewhere.

## Why the two are hard to tell apart

A `with` on a pointer dereference and a `with` on a var parameter **emit the same nine bytes**:

    LES DI,[BP+n]  /  MOV [BP-slot],DI  /  MOV [BP-slot+2],ES

and both give the same frame arithmetic. So a note recording the entry sequence, the slot offset and the frame size can be entirely correct while the declaration it describes is wrong. What separates them is a reference dozens of instructions later, where one reads the slot and the other reads the parameter.

**A declared pointer local filled by an assignment is distinguishable**, and cheaply: `P := Base` emits four `MOV`s, twelve bytes, where the `with` emits nine.

## The transferable part: question the declaration, not the statement

When several spellings of one statement have each been measured and each failed, the constraint is probably not in the statement. **Look up one level, at the declaration the statement depends on** -- a parameter's passing mode, a field's type, a variable's scope. Those change what the compiler is *able* to do, where a re-spelling only changes what it is asked to do.

The evidence for this case had already been collected on another part of the same target, where a routine taking `var O : TObj` did exactly the sought-after thing -- one load feeding three adds -- and had been fixed days earlier without the general fact being drawn out of it. **Two instances of the same shape are worth comparing before either is re-derived.**
## Blind spot

**The distinction rests on register allocation, and a switch can move it.** The shared load is the compiler choosing to keep an address live across adjacent statements; that choice is not part of the language and a different switch line -- or a different Borland release -- can spend the register elsewhere and emit the re-loads anyway. So a run of re-loads is weaker evidence than a shared load: one shape rules a pointer out, the other does not rule it in.

**And a single mention proves nothing either way.** The whole tell is what happens ACROSS adjacent statements naming the same thing. A parameter used once has no run to read, so the frame is the only remaining evidence and the declaration stays open.

