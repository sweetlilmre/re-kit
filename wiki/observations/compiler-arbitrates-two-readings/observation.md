---
type: Observation
title: When two declarations both fit the bytes, build both -- the compiler decides
description: Two adjacent immediate stores read naturally as one 32-bit assignment and equally as two 16-bit ones. The site itself cannot distinguish them. Building each way does -- one breaks the arithmetic downstream, the other breaks the store, and only one shape satisfies both. Peephole behaviour is not something to reason out from a disassembly.
tags: [codegen, reconstruction, verification, measurement]
timestamp: 2026-08-29T00:00:00Z
---

# When two declarations both fit the bytes, build both -- the compiler decides

A pair of adjacent stores:

    MOV word [0336],1000
    MOV word [0338],0

reads as `X := $1000` with X a LongInt, and just as well as `A := $1000; B := 0` with two Words. Nothing at the site separates them.

**Build both.** The declarations differ everywhere else the variable is used, and the compiler is the arbiter:

* declared as a LongInt, two 16-bit shifts of it seventy bytes further on became RTL calls, where the original has `SHL AX,4` and `SHR AX,0Ch` on the low word alone
* declared as two Words, those shifts came right and the zero store came out `XOR AX,AX / MOV [x],AX` -- **five bytes, because Borland special-cases assigning zero** -- where the original has the six-byte immediate form

Only one shape satisfies both: a LongInt assigned whole, narrowed with an explicit `Word(...)` cast at the two use sites. Being wrong twice was the route to it.

## The general point

**A compiler's peephole choices are not derivable from a disassembly.** Whether this one prefers `XOR reg,reg / MOV mem,reg` to `MOV mem,imm` for a zero is a property of the code generator, not of the program; it will not be in any document you have; and reasoning about which is "more likely" is guessing. Writing it both ways and measuring costs two builds.

Corollary: **a reading that fits the bytes at the site you are looking at is not confirmed.** Confirmation is the whole unit still matching after the declaration changes -- which is exactly what a use site seventy bytes away tests and the site itself cannot.

## See also

* [A compare tool's number is plausible, and it is wrong](../plausible-and-wrong/observation.md)
* [Two bytes the compiler cannot emit](../instruction-the-compiler-never-emits/observation.md)
