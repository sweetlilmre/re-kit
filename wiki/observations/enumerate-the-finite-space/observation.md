---
type: Observation
title: When the cause lives in a finite space, enumerate it -- and report the boundary you searched, not the absence you inferred
description: A reconstruction stalled 560 bytes short, blamed the compiler build and stopped twice on the grounds that nothing more was possible, having tested four of fourteen compiler switches; declaring one entry per remaining switch and reading a size matrix found the cause in a single run, and it was a mode of the compiler already installed.
tags: [verification, evidence, switches, codegen, process, retraction]
measured_on: a 16-bit Pascal rebuild, 4 of 14 compiler switches tried and the space reported as closed
timestamp: 2026-09-04T00:00:00Z
---

# When the cause lives in a finite space, enumerate it -- and report the boundary you searched, not the absence you inferred

A reconstruction sat 560 bytes short of its original. The difference was one cause repeated: at 61 call sites the image spent eighteen bytes where the rebuild spent eight, copying each string constant into a stack temporary and passing the temporary.

Five source shapes were written as probe units and eliminated one at a time. Three compilers were eliminated. Four compiler switches were tried. From that the project concluded **the gap is the compiler build, not the source**, wrote that into its agent file, recommended finding a different binary of the compiler, and stopped work twice on the grounds that no further progress was possible without one.

Turbo Pascal 6 has fourteen switches. Two of the ten never tried were the answer, and both are modes of the compiler that was already installed.

## Why it works

**Hypothesis generation scales with imagination; enumeration scales with the space.** Five probes took five rounds of thinking about what a compiler might do with a string constant, and each round could only test what somebody had thought of. Declaring one compiler entry per remaining switch and reading a size matrix took one run and could not miss a switch, because the switches are a list.

The space was finite, written down in the compiler's own documentation, and machine-checkable. Nothing about it required insight. It was skipped because the earlier probes felt like progress: each eliminated a real possibility and produced a real result, which is exactly what makes a search feel thorough while it is still narrow.

**The reported conclusion was stronger than the evidence, and that is the transferable failure.** *Not reproducible with what I tried* became *not reproducible with this compiler*. The first is a fact about a search; the second is a claim about the world. Only the second closes a question, and only the second gets written into a document that misleads the next reader.

The inference was not careless in shape -- three unrelated constructs really did spill intermediates to temporaries, and *one code generator does this* really was the right reading. It named the wrong generator because the sample it was drawn from covered under a third of the candidates.

## Blind spot

**A one-at-a-time sweep tests each element alone.** A cause needing two switches together would not appear, and nothing in the matrix would say so. Here one switch alone was sufficient, which was luck rather than design.

**A sweep needs a detector, and the detector decides what the sweep can see.** This one worked because the difference changed code SIZE, so a size-per-probe matrix was enough. A difference that changed instructions without changing length would have shown a row of identical numbers and read as "no switch matters" -- the same false negative one layer down. Choose the signal before trusting the sweep.

**And enumeration is only cheap where the space is enumerable.** It answers "which of these" and never "what else could it be". The five probes were not wasted: they are what established that no *source* shape produced the construct, which is what made the toolchain worth suspecting at all. The error was the order, not the work.

## Cost

Ten compiler entries and one run of the checker that compiles each probe with each compiler. Minutes.

Against that: the question had been open across most of a reconstruction, had produced a wrong conclusion in a committed document, and had twice ended a work session early.

Once the switch landed, the rest fell in about one iteration -- 96 bytes to zero -- because the same switch that closed 610 bytes also let the runtime link identically, which aligned every runtime call offset, which made every per-routine comparison legible for the first time. **A single blocking cause can make everything downstream of it look individually hard.**

## Example

A 1993 DOS demo rebuilt from its shipped binary, 4 Sep 2026.

`{$O+}` -- overlay code generation -- is what makes the compiler copy a string constant into a temporary sized to that constant and pass it through a far call to an unbounded copy helper. `{$I-}` accounts for the rest: under `$I+` every I/O operation carries a five-byte result check, and one routine performed eight of them and was exactly forty bytes over.

The sweep also settled a second question that had been open since the first day. The project had tried to tell one patch level of the compiler from another by comparing how far their runtimes agreed with the original's -- 25.9% against 26.0%, a dead heat -- while the runtime library carried its version in plain ASCII: `Portions Copyright (c) 1983,90 Borland`, byte for byte what the image held. **Check the strings before measuring the bytes.**

The reconstruction reached byte-identity with the shipped binary the same day.
