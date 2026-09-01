# A wiki citation may name a target, and the path test does not apply to it

**Status:** accepted, 1 Sep 2026

`kit/README.md` states the rule that gives this folder its reason to exist: if a file under `kit/` names a target's binary, a segment address or a machine path, it is in the wrong place. `WORKING.md` section 5 states, separately, that an observation carries its **blind spot** and **cites the measurement** it came from. In the wiki those two rules collide, because a citation IS a binary name and a segment address -- "measured on part 005, `12c5:01b0`" obeys the second and breaks the first in the same clause.

**Decided: the citation wins.** An observation may name the target it was measured on, at the addresses it was measured at, and that is not leakage. What the path test forbids is a kit PROGRAM holding a project's fact, because such a program computes a wrong answer everywhere else; a document that records where a finding came from computes nothing and is the only thing that makes the finding checkable.

## Considered options

**Strip the target names.** Measured on the day this was decided: 55 of 91 wiki files name the host target -- 47 mentions of the repository, 22 of a binary, 45 literal `SSSS:OOOO` addresses across 25 files. Stripping them leaves 77 observations asserting things with nothing anywhere able to re-check any of them. `observations/name-carries-its-evidence` is the corpus's own finding on exactly this: a claim no stronger than its evidence, and a name is the one error a build, a comparison and a verifier all pass.

**Generalise them** -- "measured on one target". Same loss, worded so it reads as though provenance were present.

**Keep them, and make the citation visible as a citation.** Chosen. The target moves out of the prose and into a `measured_on:` frontmatter key, so a reader sees evidence supporting a general claim rather than prose that sounds like a finding about one demo. It also makes "which target witnessed this" queryable across the whole bundle for the first time, and the honest answer today is that nearly every observation has exactly one witness.

## Consequences

A second consumer's citations sit BESIDE the first's rather than replacing them; an observation with two `measured_on:` targets is a stronger claim than one with a single value, and that is now visible without reading the body.

**This ADR exists to stop a correct-looking repair.** The failure it guards against is concrete and reasonable: somebody reads the path test, greps the wiki for a binary name, finds 22 hits and tidies them away by the rule as written. A commit message does not prevent that, because nobody greps commit messages. If the citations are to go, this file is what has to be argued with first.
