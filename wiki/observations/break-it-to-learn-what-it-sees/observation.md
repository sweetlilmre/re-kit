---
type: Observation
title: To know what an instrument cannot see, break the tree on purpose and check that it complains
description: Every instrument has a blind spot and none of them announces it. A passing report is compatible with the check working and with the check being structurally unable to see the thing you are trusting it for, and those two states look identical. Constructing the failure takes minutes and settles it -- and on this corpus it changed a decision that would otherwise have rested on ninety edits and a hope.
tags: [verification, tooling, measurement, process, reverse-engineering]
timestamp: 2026-08-29T00:00:00Z
---

# To know what an instrument cannot see, break the tree on purpose and check that it complains

A green report says the check found nothing. It does not say the check *could* have found something, and those two states are indistinguishable from the outside. The gap matters most exactly when you are about to rely on the instrument for a change you cannot otherwise verify.

**So construct the failure.** Make the smallest edit that produces the defect you are worried about, run the instrument, and see whether it objects. Revert either way. It costs minutes and it converts a belief into a fact.

## Measured, and it changed a decision

A second reconstruction of the same program had no whole-program link, so no linked-image comparison — only a per-unit check comparing compiled units against the original's. That check was clean: 26 units, none mismatched, none missing. The question was whether it was strong enough to make a ninety-site renaming pass safe, since the risk of renaming is that a declaration moves and every address after it shifts.

The probe was one line: insert an extra `Word` ahead of an existing variable, shifting every subsequent data address in the unit by two bytes.

**The check reported the unit identical.**

It is blind by construction, and the reason is sound: a data address is a fixup, unresolved until link time, and a per-unit comparison must mask fixups because those bytes legitimately differ. The instrument was working exactly as designed and was structurally incapable of seeing the one thing being asked of it.

The same defect in the first reconstruction had displaced sixty-six operands and was caught only by the linked image. Without the probe, the plan was ninety edits guarded by a check that cannot see them fail.

## What makes a good probe

* **Smallest edit that produces the real defect.** Not a syntax error, not a deleted routine — the actual shape you fear. A shifted declaration, a changed constant, a stale artefact, a renamed symbol.
* **Revert immediately, and verify the revert.** The probe must leave nothing. Confirm the tree is clean afterwards rather than assuming the restore worked.
* **Probe the instrument you are about to trust, not the one you have.** The question is never "do the checks pass" but "would this check catch THIS mistake".

## Two in one session, both silent

The blindness is rarely announced and rarely obvious:

* A per-unit comparison could not see a shifted data declaration, because it masks fixups.
* Measurement tools read a build artefact by path, so after a failed build they reported the previous run's verdict — correctly, about a file nobody was thinking about. Four instruments agreed on a byte-identical result for source that no longer existed.

Neither was a bug. Both were instruments doing precisely what they were built to do, in a situation where that was not what was wanted.

## The habit

**Before trusting an instrument for a decision, ask what it would look like if the instrument were blind — and then go and see.** A blind check and a working check produce the same output on a healthy tree, which is the only tree you normally have.

Write down what each instrument cannot see, beside the instrument. A blind spot recorded once is a blind spot the next person does not have to rediscover with ninety edits.

## See also

* [A measurement tool reads whatever is on disk, and a failed build leaves the last good answer there](../artefact-outlives-its-source/observation.md)
* [Every declared routine matches, and the rebuild still behaves differently](../verifier-blind-to-absence/observation.md)
* [A tool that is wrong is useless; a tool that BECOMES right is worth re-asking every open question](../instruments-have-an-order/observation.md)
* [Documentation defects are invisible to every check and visible on the first read-through](../walk-the-path-a-reader-takes/observation.md)
