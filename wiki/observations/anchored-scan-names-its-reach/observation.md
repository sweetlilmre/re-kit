---
type: Observation
title: An anchored scan reports the population its anchor can reach, and names it as though it were the population
description: A byte scan needs an anchor to tell an instruction from data, and the anchor is a precondition on the thing being counted. Every subject that does not carry it is absent from the result, and the result is then labelled with the name of the whole class. Measured on one rebuild -- 2 framed returns reported as a routine census in a 1,568-byte runtime segment holding roughly thirty routines, and a false structural inference drawn straight off the number.
tags: [tooling, verification, measurement, blind-spot, hand-assembler, stack-frame]
measured_on: a 16-bit Pascal rebuild, three segments of one part
timestamp: 2026-09-04T00:00:00Z
---

# An anchored scan reports the population its anchor can reach, and names it as though it were the population

A byte scan cannot tell an instruction from a byte of data that happens to have the same value. So it anchors: it looks for the instruction **in company**, preceded by something that makes it unambiguous.

The anchor is what makes the scan trustworthy. It is also a **precondition on the subject**, and every member of the class that does not satisfy it is silently absent.

## Why it works

Counting far returns in a 16-bit segment is the case. A return is `CA nn nn` or `CB`, and both values occur constantly inside data, so the scan requires a frame teardown immediately before — `LEAVE` or `POP BP`. After one of those, a `CA` is certainly a return.

**But a routine need not build a frame.** One that reads its parameters off `ss:[bx+n]` after `mov bx,sp` — the shape hand-written assembler and a runtime's own units use — ends in a bare `RETF` with no teardown. The scan is blind to every one of them, and its output was headed *the routine census*.

| segment | what the scan reported | what is there |
|---|---:|---|
| 1,568-byte runtime unit | **2** | roughly thirty assembler routines |
| 272-byte unit | 2 | plus 9 bare `RETF` bytes in 272 bytes, which cannot all be routines |
| 1,008-byte compiled unit | 13 | 13 — the scan was exactly right |

**The third row is the reason this survives.** On compiled Pascal, where every routine builds a frame, the anchored scan is correct and demonstrably so. It fails only on segments of frameless routines — which is precisely where a reader is least able to check it by eye, and where the tool is therefore most relied upon.

**And a false inference came straight off the number.** A 1,568-byte segment showing two returns was read as *a unit of very few routines whose bodies call nothing*. That is a structural conclusion about a program, drawn from a count of what one anchor could see.

## Blind spot

**Widening the anchor is not the fix**, and reaching for it is the trap. Dropping the requirement counts every `CA` and `CB` byte in the segment, trading a silent undercount for a silent overcount — on the segment above, 32 candidates where 2 were reported, including operands of 5,770 and 8,056 that are obviously data. Neither number is the answer, and the wide one is worse for looking generous.

**What can be said honestly is a BOUND.** Filter the operand to what a stack cleanup can be — even, and small — and report the count under its own heading, labelled an upper bound, with the unfilterable class separate: a bare return has no operand to test, so it is the weakest signal available and must not be pooled with the rest.

**The docstring stating the anchor is not the same as stating the consequence.** This one said *"`c9`/`5d` is LEAVE or POP BP first"* — completely accurate, and it describes the mechanism to somebody reading the code. What misleads is the heading over the OUTPUT, which named a census. A precondition documented at the implementation is not a caveat delivered at the result.

## Cost

One question, whenever a scan needs an anchor to be safe: **what does the anchor require of its subject, and what member of the class does not have it?** The answer here took one look at how a frameless routine ends.

## Example

Four cheap scans on one segment, one of which counts far returns. The tool's own thesis is that a missing call proves a missing routine far more cheaply than searching for the routine — which is true, and depends entirely on the population being complete.

Two counts are printed now, and neither is called a census: the framed returns, which are certain, and the frameless candidates, which are a bound. On the runtime segment that reported 2, the bound is 11 sized candidates and 13 bare — so a reader sees a segment of many routines rather than one of two.

## Citations

- One 16-bit Pascal rebuild; three segments of one part, counts as tabulated.
- [A match rule stricter than the thing it matches reports absence, not failure](../match-rule-stricter-than-its-subject/observation.md) -- the same family. There the rule was stricter than its subject and reported NOT FOUND; here the anchor is stricter than its class and reports a smaller population.
- [A stack check precedes the frame](../stack-check-precedes-the-frame/observation.md) -- what the prologue actually emits, which is what this anchor depends on.
- [An enumeration that is short reads as a finding, and the finding is about the reader](../an-addend-can-be-a-size/observation.md) -- a classifier's last branch asserting its own completeness, which is this one level along.
