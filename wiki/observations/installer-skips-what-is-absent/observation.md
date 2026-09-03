---
type: Observation
title: The installer asks least about what a project cannot have yet
description: A setup program that ranks answers by the strength of their evidence is structurally silent about every answer whose evidence the answer itself creates -- the register was offered only where a register already existed, so the one project shape guaranteed to need the question was the one shape never asked it, and two consumers installed with no ratchet at all.
tags: [tooling, verification, measurement, blind-spot, process]
measured_on: 2026-09-03
timestamp: 2026-09-03T00:00:00Z
---

# The installer asks least about what a project cannot have yet

A setup program that proposes rather than decides is the right design, and ranking its proposals by the KIND of evidence behind them -- a path a script already names, beating a conventional name, beating a directory of the right shape -- is the fix for a prototype that guessed by counting files and guessed wrong. All of that held up. The defect is one level below it: **evidence-ranking silently converts "there is nothing to point at" into "there is nothing to ask about".**

The shape is a conditional offer:

    if (root / "status.toml").is_file():
        offer("layout.register", "status.toml", CONVENTION,
              "the register's conventional name")

Read as a proposal that is what you want -- do not propose a file that is not there. Read as the program's ONLY mention of the key, it means a project with no register is never asked for one. And a register is not an arbitrary example: it is the file the setup program's own output is supposed to bring into existence, so **the projects that need the question are exactly the projects the condition excludes.** Five instruments refused to run without it, and the answer was never put to anybody.

## Why it works

Three properties have to line up, and they line up more often than they look like they will.

**An answer whose evidence is created by answering it.** Most keys name something already on disk -- sources, a reference image, a build directory -- so absence really does mean "not applicable here". A register, a lock file, an output directory a first build will create: for these, absence means "not yet", and the two are indistinguishable from a directory listing. Ranking by evidence cannot separate them because neither has any.

**A report that is true and unreadable.** The gap was not hidden. A derived list -- every key the toolkit's own source looks up, minus everything proposed or asked -- printed the key, named all five instruments that wanted it, and said in as many words that a gap here is a to-do rather than a silence. It was twelfth in a list of twelve, beside keys that are genuinely optional for a real project. **A required answer and an inapplicable one rendered identically**, so the list read as a to-do list and got treated like one, for as long as both consumers existed.

**A flag documented and never implemented.** The docstring offered a mode that writes the config after confirming each value. No such mode exists: the string appears once in the file, in the docstring. A person following the documented command sees a proposal, an exit status of zero, and no file -- see [A docstring is the one claim about a program that nothing runs](../docstring-is-an-unrun-claim/observation.md). Together with the above, the installer could neither ask the question nor write the answer, and reported success either way.

## Blind spot

**Fixing the offer moves the silence rather than ending it, and the first fix here proved it.** Making the key always asked also makes it always "covered", so a check written as *required keys minus keys this program covered* became empty by construction on the same edit that created it -- a branch that could not fail, which is [An exemption list is where a check goes to die](../exemption-that-cannot-fail/observation.md) arriving inside its own repair. The check has to read the project's OWN answers, not the installer's coverage: an installed config that does not answer a required key is a condition that has actually occurred, and it is the only formulation that can fail.

**A required list is a thing that wants to grow, and growth destroys it.** "Many instruments want it" is the wrong test -- one key here is read by thirteen programs and is still meaningless for a project that links nothing. The test that survives is narrower: without this, nothing in the project can hold a measurement. On this corpus that admitted exactly one key.

**None of this says the project should have had a register.** Whether a given reconstruction has anything to ratchet is a decision for a person, and an installer that refuses to finish is asserting the answer is always yes. What it can honestly refuse is a config that answers NEITHER way -- the state where nobody decided and nothing recorded that nobody decided.

## Cost

Reading the conditional is free once you know to suspect it. The general form is a grep with a question attached: for every key the setup program offers, ask what evidence gates the offer, and whether that evidence can exist on the first day. Anything gated on its own output is a candidate.

The rule worth writing at the top: **an installer must ask about what it cannot see, because what it cannot see is what it is there to create.** An offer may be conditional. The QUESTION may not.

## Example

A 16-bit Pascal reconstruction toolkit shared by two consumers as a submodule, 3 Sep 2026, found by bumping the second consumer -- which is the only test some of a shared toolkit's work gets.

The published check list presents thirteen instruments as the same list in every project. Five did not run in either of one consumer's two host roots, all five exiting 2, and every one of them was register-dependent: the ratchet, the artefact-identity check, the plan, the observation report and the routine locks. The first count taken was four, missing the ratchet itself; a second count read the same five out of the toolkit's source by a different route -- which key each program looks up -- and agreed. That the two routes agreed is the only reason either number is worth quoting.

Answering three keys made four of the five run. The fifth wants a map keyed by a marker that the sources do not yet carry, so it stays unanswerable, and saying so is the honest report: it is not a configuration gap but an absence of declared work.

The result the whole argument was about then turned out to be unrecordable. Both reconstructions' program bytes were identical to the originals' -- every differing byte inside the MZ header, in a relocation table a linker may order as it likes -- and the identity instrument had two comparisons, neither of which fits that shape: one compares whole files, the other truncates a file to its declared length without skipping its header. **So the register could be written and the thing worth locking still could not go into it.** A third comparison that strips both headers records it, and was checked by flipping one byte inside the image and watching the row refuse, then one byte inside the header and watching it correctly not care -- the second half being the demonstration that the new comparison is not the old one under another name. Its blind spot is stated where it is made: a claim recorded this way says the program bytes match, not that the file runs.
