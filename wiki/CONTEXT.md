---
type: Glossary
title: The method -- vocabulary
description: The method's vocabulary -- what we measure, what measures it, how a wiki page is shaped, how the catalogue is organised, and the fidelity ladder.
tags: [glossary, vocabulary]
timestamp: 2026-09-01T00:00:00Z
---

# The method -- vocabulary

**Vocabulary for the METHOD.** How a page is shaped, how the catalogue is organised, the fidelity ladder it all hangs off -- and, since 23 Aug 2026, the words for what we measure, the programs that measure it, and how a measurement is held: thirteen terms that used to live in a host repository's root glossary and had to be carried to every new target unchanged.

**This file travels with the kit.** It is the kit's half of the vocabulary, so it goes wherever `kit/` goes. A host repository's own `CONTEXT.md` keeps only the words for ITS target -- the things that would have to be rewritten for a different binary -- and points here for the rest.

## Language

### The knowledge base

**Technique**:
One method. It answers one question about a binary.
_Avoid_: trick, approach, procedure, recipe

**Wiki**:
The whole thing a reader browses -- hubs, artefact answers, case studies and orientation together.
_Avoid_: knowledge base (fine in conversation, but the wiki is the readable thing), manual, site

**Catalogue**:
The technique pages inside the wiki, and only those. The inventory it was cut from held 209 techniques -- that is a measurement of the SOURCE MATERIAL, not of the wiki, and the page count was always meant to be an output rather than a target. Consolidating toward a number is how you lose the distinction that cost most to learn.
_Avoid_: manual, library, index

**Tier**:
Which layer of knowledge a piece of advice belongs to. There are exactly two, below. A tier is a field on one section of a page, not a way of grouping pages: one page can hold a Pascal-tier section and a substrate-tier section.
_Avoid_: level, layer, category

**Substrate tier**:
Knowledge about DOS and 16-bit binaries. It says nothing about Pascal, so it should also work on a C or assembler program. Examples: MZ headers, LZEXE packing, segment addresses.
_Avoid_: DOS layer, lower tier, base tier

**Pascal tier**:
Knowledge that is true only for Borland Pascal. Examples: `.TPU` files, DGROUP layout, smart linking.
_Avoid_: compiler layer, upper tier

**Withdrawn conclusion**:
A claim this project made, believed, and then disproved by measurement. These belong in the catalogue next to the technique that produced them. They are not an appendix.
_Avoid_: mistake, error, false start, retraction

### What we measure, and what measures it

**Artefact**:
A thing you can measure. It is a whole file, or one named part of a file. Examples: `PSYCHO.EXE`, one segment, one routine, one `.PAS` file.
_Avoid_: target, object, item, subject

**Instrument**:
A tool or a method that measures how well an artefact agrees with the original. A person who watches the screen is an instrument.
_Avoid_: tool, check, test, measure (as a noun)

**Blind spot**:
The thing an instrument cannot see. Every instrument has one. Each instrument is blind to something the next one catches.
_Avoid_: limitation, gap, weakness


### The toolkit

**Toolkit**:
The reusable programs, with no project facts in them. It lives at `kit/tools`, in three folders: `substrate`, `pascal`, `wikitools`. **`tools` was on this avoid-list until 23 Aug 2026**, because the word once named both the frozen scripts at a host repo's root and the reusable set. The folder is now called `tools` and the ambiguity ends with the frozen copies, so the avoid-list drops it -- a glossary that contradicts the directory layout is worse than none.
_Avoid_: library, framework, package

**Core**:
The part of a program with no project facts in it. The reusable part.
_Avoid_: engine, kernel, generic layer

**Driver**:
The part of a program that holds one project's own facts: file names, addresses, unit lists.
_Avoid_: script, wrapper, harness (a harness is a different thing)

**Compare tool**:
A program that compares our bytes against the original's bytes.
_Avoid_: comparator, differ, verifier

**Allowed-difference rule**:
The rule that says which differences a compare tool accepts. It is passed in, never built in, because the rule inverts by artefact.
_Avoid_: excuse rule, mask, tolerance, heuristic

**Scratch folder**:
A temporary folder that a build erases and then uses. One per project, named in config, because three build scripts once shared one and could not run at the same time.
_Avoid_: build dir, temp, workspace


### Verification

**Harness**:
A small program that runs one piece of the subject on its own -- one effect, one screen, one whole part -- so a person can watch it. A harness is itself a deviation: it is ours, not the original's.
_Avoid_: test, driver, runner

**Marker**:
A comment in a `.PAS` file that a tool reads. `{ @asm 003 11f3:0105 }` names the address in the original that a routine's bytes must match.
_Avoid_: annotation, tag, directive

**Fragment**:
Hand-written assembler inside a compiled Pascal routine. It has no routine boundary, so its marker states a byte count instead.
_Avoid_: inline block, snippet, chunk

**Ratchet**:
A measure that cannot go backwards without failing the build. The register locks each routine's matched length, so a change that shortens a match is a regression rather than a smaller number. `ratchet.py` fails the run; `routines.py --emit` measures what it compares against, because a length typed into a config is a length that goes quietly stale.
_Avoid_: gate (a gate is a different thing), guard, lock

### How the catalogue is organised

**Hub**:
A symptom page that has artefact answers under it. It is a DISCRIMINATOR and never states a rule, because its children hold rules that invert: what one artefact requires you to forgive is what convicts another, so a rule in the hub is a rule stated for the wrong half of the corpus. A page with no children is not a hub and states its rule directly, having nowhere else to put it.
_Avoid_: parent page, index page, landing page


**Lookup key**:
The thing a reader knows before they open a page. It decides how the catalogue is sorted. The key chosen here is what you OBSERVED, which is why the observation is the page and the artefact is a section inside it.
_Avoid_: axis, organising principle, taxonomy

**Symptom page**:
A page you find by what you observed. It opens with the observation, then has one section for each artefact you might be holding. Example: "a zero byte where the original has something else". **This is what the bundle calls `type: Observation`** -- the word here is the design's and the word in the frontmatter is the tree's, and they name the same thing. Every page in the wiki is one.
_Avoid_: lookup page, diagnostic page

**Procedure page**:
A page you find by the job you decided to do. Example: "unpack the container". `type: Procedure` is registered in the profile and the validator accepts it; **there are no instances yet**, so this term describes a page the bundle can hold and does not.
_Avoid_: how-to, task page, method page

**Section**:
One artefact's answer inside a page. It carries its own rule, its own caveats, its own withdrawn conclusions, and its own tier. **In the tree it is a document of its own, `type: Artefact Answer`**, filed beside the hub it answers under -- one per artefact, so one can grow without bloating its siblings, and so the hub's table can be generated from their frontmatter instead of written twice.
_Avoid_: branch, case, variant

**Cross-index**:
A list that points at pages already written, sorted a second way. It adds no pages. Three were decided -- the nine classes of withdrawn conclusion, the twelve activities, and the ladder nodes -- and **none has been built**. The ladder one was dropped deliberately and for a stated reason: every artefact answer written so far sits at the same ladder node, so it would file them all together and tell a reader nothing. That is worth keeping as the test for the other two, which is whether the second sort separates anything.
_Avoid_: view, tag, secondary axis

### The fidelity ladder

**Ladder**:
The ordered set of gates and rungs. It runs from "we know nothing about this artefact" up to "its bytes are identical to the original".
_Avoid_: scale, spectrum, hierarchy, maturity model

**Gate**:
A node near the bottom of the ladder that you must pass through. A gate is never a goal. You cannot read a file you have not unpacked. There are three: container opened, identified, charted.
_Avoid_: stage, prerequisite, step

**Rung**:
A node on the ladder that you can choose as a goal. There are six, from "it compiles" up to "the artefact is byte-identical".
_Avoid_: level, grade, tier (a tier is a different thing)

**Strand**:
One of the two paths up the ladder. The behavioural strand watches the demo run. The structural strand compares bytes. Neither one proves the other.
_Avoid_: branch, track, axis

**Target rung**:
The rung an artefact is meant to reach. A person declares it.
_Avoid_: goal, aim, requirement

**Achieved rung**:
The rung an artefact has reached. A tool computes it. A person may not assert it, with one exception: watching the demo run.
_Avoid_: status, actual, current level

**Transcription stance**:
What the Pascal source is allowed to look like. There are three, below. The stance is independent of the rung.
_Avoid_: style, fidelity mode, approach

**Verbatim**:
A stance. Hand-written assembler is copied instruction by instruction, with a comment on every line.
_Avoid_: literal, exact, faithful

**Idiomatic**:
A stance. The binary is plainly compiler output, so normal Pascal is the honest transcription. Inventing assembler here would be the deviation.
_Avoid_: natural, clean, native

**Equivalent**:
A stance. The code is knowingly different but has the same visible effect. It can never be byte-identical.
_Avoid_: approximate, rewritten, functional

**Provenance**:
How a piece of source came to exist. Did a person read the bytes, or write something plausible? It never tells you whether the code is correct.
_Avoid_: evidence class, confidence, quality

**Deviation**:
A difference from the original that we chose on purpose and wrote down. Anything not written down is a defect, not a choice.
_Avoid_: divergence, variance, exception

