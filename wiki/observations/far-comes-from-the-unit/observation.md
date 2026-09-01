---
type: Observation
title: Near or far is decided by the surrounding unit
description: Two copies of a routine looked unshareable because one was far and the others near -- but far-ness is not in the procedure header, it comes from where the header sits, so one include can carry the same text into both.
tags: [pascal, turbo-pascal, codegen, calling-convention, include]
timestamp: 2026-08-28T00:00:00Z
---

# Near or far is decided by the surrounding unit

You have the same routine written out in two units, and you want one shared text -- an include, because a shared *unit* would change the emitted code at every call site. One copy is far and the other is near, so it looks like the header has to differ and no single text can carry both.

**The header does not say which it is.** In Turbo Pascal, near or far comes from the context the declaration sits in:

* a routine declared in a unit's **interface** is far, always, because another unit can call it;
* a routine that exists only in the **implementation** is near by default, and the compiler may widen it to far on its own if something forces the address to be taken;
* the `{$F+}` / `{$F-}` state at the point of compilation moves the default;
* an explicit `far` in the header is one way to say it, and the *absence* of one says nothing at all.

So the identical text `procedure SetPalette768(P : Pointer); assembler;` compiles far inside a unit whose interface declares it and near inside a unit where it is local, and both are correct. The include carries the header, the surrounding unit supplies the calling convention, and the emitted body differs by exactly the return instruction -- which the compiler chooses, not the text.

## Why it works

The header is a name, a parameter list and a set of directives. The calling convention is a property of the *symbol* as the unit's symbol table records it, and the interface is what publishes a symbol. An included file is textual inclusion at declaration level: it contributes a declaration to whatever scope the `{$I}` appears in, and inherits that scope's defaults completely.

This is what makes the include the right instrument for a routine a 1990s author duplicated between units on purpose. The source is shared; the code generation stays local to each unit; each part gets its own copy in its own segment, reached with the near or far call that part's callers expect.

## Blind spot

**The include must carry the WHOLE procedure, header and all.** A `{$I}` inside an `asm` block is answered with `Error 118: Include files are not allowed here`. At declaration level it compiles.

**A genuinely different parameter list is a real obstacle**, and this rule does not rescue it. An untyped `var P` and a `P : Pointer` compile to the same body -- both are a 4-byte address on the stack, so a `LDS SI, P` is the same encoding -- and are still two different declaration lines. That case cannot become one include, and it is the one worth writing down, because it looks identical to the case that can.

**Sharing the text does not settle the bytes.** Whether the shared version is *right* is a question for the binary, not for the compiler: the compiler accepts a header whose far-ness is wrong for what the original did. The only proof is a rebuild compared against the original.

**Staged includes obey the host's filename limits.** On a DOS toolchain that means 8.3, stem included -- a nine-character stem gets `Error 15: File not found` on a file sitting in the same directory as the one that found it.

**A marker pointing at a body that has moved stops resolving.** Where per-routine byte checks find a body by looking under an address marker, moving the body into an include leaves the marker with nothing beneath it. If the marker syntax can name the routine and its length, use that form at the include site; otherwise the lock disappears and the count falls while nothing reports a failure.

## Cost

One include per shared routine, and a marker at each including site. Both pairs converted in one sitting.

## Example

A 16-bit Pascal demo rebuild, 28 Aug 2026. Two routines were each written out twice -- a `REP OUTSB` palette write and a four-port DAC write -- with an exemption file asserting that their declarations differed and so no one text could carry them. Compared as strings the declarations were the same line; the difference the note had recorded was that the shared unit's copies were far and a scene unit's copy was near.

Both became single includes carrying header and body. All ten binaries still rebuilt byte-identical, so the compiler had emitted the far and near forms from one text, exactly where each was wanted. One lock did vanish on the first attempt, because a marker was left sitting above a `{$I}` with no routine name in it: 85 locked became 84 locked with 0 failing, which is a fall in coverage wearing the appearance of a pass.
