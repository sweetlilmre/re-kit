# How we work

**Read this first, at the start of every session.** It is the method; it holds no fact about any particular target. What is true of the target you are working on is in the host repository's own agent file and in `kit.toml`.

**It is longer than it should be, and the honest response is to say which part you read.** Sections 1, 2, 2a and 4 are the session: where things are, what to work on, the loop, and the checks. Section 8 is REFERENCE -- what to distrust -- consulted when you have a question rather than read through, and the instrument tables that used to sit here are now `INSTRUMENTS.md`, behind the pointer in section 3. Sections 5, 6, 7 and 9 are the rules and the traps, and they repay one careful reading each. A document read at the start of every session is one whose length is a defect, so it is worth knowing that the first four sections are about a page.

## 1. Where this project keeps things

`kit.toml` at the host's root answers that -- where the sources are, where the wiki is, what the register is called, where a build leaves its output. `kit.local.toml` beside it holds the machine paths and is never committed. **Neither is hand-written**: `kit/tools/wizard.py` writes them, and [`SETUP.md`](SETUP.md) says how -- including what it refuses to guess.

You do not need to read either. Every program here asks them, and prints which answer it used and where it came from:

    using    layout.src = 'src'  (kit.toml)

If a program says `kit.toml does not answer ...`, that is the answer -- add it, or pass the value on the command line. An explicit argument always wins.

## 2. How to pick up the next piece of work

    kit/tools/pascal/plan.py --report

The plan is an ordered list of investigations and the rows under them. **The order is the priority**; there is no priority number. Take the first open one.

An investigation is one finding a person saw, written as prose, citing the observation it came from. It is resolved with prose saying what was found -- not by closing it.

**If the next investigation needs a run somebody has to WATCH**, that is an observation and not a measurement: nobody may record it on their behalf. Say so, take the next investigation meanwhile, and record the run through `observe.py` once it has actually happened -- refusing to record a run nobody made is the one thing that tool exists for.

If the plan is empty, the next work is whatever the register's stalest observation points at: `observe.py --report`.

**A harness that no longer EXISTS reports stale for ever, and that is what `--supersede` is for.** Retire the row with `observe.py --supersede OLD --by NEW --date YYYY-MM-DD`: it changes no measured field, moves the row out of the stale count, and refuses unless the old harness is really gone AND the successor already has an observation of its own. Do not delete such rows -- on one target two of them had recorded a `differs` that led to a real fix. And do not retire one whose successor is unobserved: that is precisely the gap the report is for, and the tool will say so.

## 2a. The loop, once you have picked something up

Sections 2, 4, 5 and 7 each describe a piece of a session. This is how they join, because knowing each piece is not the same as knowing the order.

    plan.py --report                     what to work on -- the first open one
    spans.py SPANS.toml PART             where the rebuild does NOT line up
    spanwhy.py SPANS.toml PART           and WHERE THE DEFECT ACTUALLY IS
    dsmap.py SPANS.toml PART             is the DATA in the right place?
    fpusites.py SPANS.toml               which units are $N- and should be $N+?
    dgimage.py SPANS.toml                is the initialised DATA identical?
    survey.py / rtl.py entries / x87.py  read the segment before writing Pascal
                     ... edit the sources ...
    build.py CONFIG.toml TARGET          rebuild -- one target and its deps
    routines.py                          did the DECLARED routines still hold?
    spans.py SPANS.toml PART             did the span actually SHRINK?
    run it, and WATCH it                 <- only a person can do this
    observe.py                           record what they saw

**Two instruments, two different questions, and you want both.** `routines.py` answers *did I break something that was already right* -- it is the regression check, and it is driven by declarations. `spans.py` answers *did the transcription land* -- it walks every byte, so it is the only one that can see a routine nobody declared. A green `routines.py` with an unchanged span means the edit compiled and achieved nothing.

**Rebuild one target, not everything.** `build.py CONFIG.toml TPART5` stages that target and whatever it depends on, read out of the staged sources' own `uses` clauses. A whole-project rebuild is cheap enough to be worth doing before you believe a final number -- seconds, on this corpus -- but it is not the inner loop.

**The run is the part nothing here can do.** A part's rung moves on somebody watching it, and `observe.py` exists to refuse a run nobody made. If the next investigation needs one and you cannot do it now, say so, take the next one, and come back -- see section 2.

### Where a kit change fits in that loop

You will find kit work while doing target work, and it comes in three shapes. Tell them apart before writing anything:

| what you found | where it goes |
|---|---|
| this binary does X | the host's notes, and a plan row |
| ANY binary built this way does X | a wiki observation -- section 5 |
| an instrument cannot see X, or said something false | the instrument, AND a wiki observation for its blind spot |
| you did the same thing by hand twice | a tool -- and it is BORN in `kit/tools`, never in the host |

**A kit change and this project's accepting it are two acts** -- section 7 has the commands. Do not batch them: the gitlink is what records which kit a measurement was made with, so a change pushed without the bump means a number in the host's notes that nothing can reproduce.

**Improve the instrument before the measurement it produced.** If a tool tells you something surprising, section 8's first line applies -- distrust the verifier first. The cost of being wrong here is asymmetric: a bad transcription is caught by the next comparison, and a bad instrument silently blesses every transcription after it.

### Closing an iteration

Two things happen every iteration, and a third happens on a trigger.

    ALWAYS   commit the source edit and the measurement it produced, and PUSH

    ON A TRIGGER   the kit pass: write it, commit the kit, bump the gitlink, push

**The kit pass fires when one of three things is true, and not otherwise:**

| trigger | what to write |
|---|---|
| a finding that would hold for ANY binary built this way | a wiki observation -- section 5 has the test |
| **you pasted a script into the shell** | see below -- this is the trigger that does not fire on its own |
| an instrument changed, or said something false | the instrument, AND an observation for its blind spot |

**The tool trigger is written as an observable act, not as a judgement, because the judgement version does not work.** "Did the same thing by hand twice" needs you to REMEMBER the first time, and you will not: each inline script feels like a one-off answer to the question in front of you, and the sixth one feels exactly like the first. On this corpus the same twenty-line linked-image comparison was retyped six times across four sessions before anybody noticed, and each time it was thrown away.

So the test is mechanical: **an inline script long enough to be worth writing is long enough to be worth keeping.** If you could not have pasted it from a file, it does not exist as a tool yet -- and the fact that you had to retype it IS the evidence that you wrote it before. Retyping is the symptom; you do not need to recall the disease.

Three practical consequences:

* A script that answers a question about the TARGET -- dump these bytes, what is at this address -- is a one-off and stays one. A script that answers a question about the COMPARISON is a tool, because that question recurs by construction.
* Write it into `kit/tools` at once, even roughly. A rough tool in the kit beats a polished script in the scrollback, because only one of them exists tomorrow.
* Give it the docstring while you still know why the existing instrument was not enough. That paragraph is the whole value: the next person's question is not "what does this do" but "why is there a second one of these".

Most iterations trigger none of them. That is the normal case and it is not a failure -- an iteration that transcribes a routine the previous one located has produced target knowledge, which belongs in the host's notes and nowhere else. **Do not manufacture an observation to have written one.** A wiki of thin entries is worse than a smaller one, because it makes the index unreadable and the next person stops checking it.

**When a trigger DOES fire, it fires now, not later.** This is the failure that has actually happened: the pass was deferred across roughly thirty iterations of one reconstruction, and what came back was not thirty observations. It was seven, written afterwards from commit messages, with the reasoning reconstructed rather than recorded -- and the only findings that survived are the ones a commit message happened to argue in full. At least two corrections were gone entirely. A transferable rule costs ten minutes on the day and cannot be recovered on any later one.

**The reliable trigger is having been WRONG in a way a rule would have prevented.** Five of those seven were corrections. A discovery was going to happen anyway; a mistake is what generalises, and it is also the thing you are least inclined to write down.

**Pushing is not batched.** A commit that has not been pushed is one machine away from being the only copy, and a kit commit that has not been pushed makes the host's gitlink unresolvable for anybody else -- the same failure as not bumping it.

### What tells you the loop is working

The plan shrinks, the coverage walk's spans shrink, and the ratchet does not fall. Nothing else is evidence, and in particular a green check list is not: it is the floor, not the goal.

And the wiki grows. A reconstruction that advances for a week without adding an observation is either working in a very well-mapped corner or -- much more likely -- throwing away the half of the work that outlives the target.

## 3. Which instrument answers which question

**[`INSTRUMENTS.md`](INSTRUMENTS.md)** -- the lookup table, grouped by the question
you have. Reach for it when you need to know: how to get INTO a file at all; what
to read in a segment before writing any Pascal; how to build it; which instrument
measures what came out, and where the defect that opened a span actually is; or
which tool keeps the record honest.

It was section 3 of this file and is a page of tables nobody reads linearly, which
is the whole reason it moved. **The section number stays** so that every reference
to sections 4 to 9 keeps pointing where it did.

**Two things worth knowing before you go there.** `spans.py` is what to reach for
when a check is green and the rebuild still misbehaves -- every other instrument
measures something somebody DECLARED, so a routine nobody declared is not a row in
its scheme. And `build.py` MAKES the thing the others measure rather than measuring
anything, which is why a harness is not one of them.

## 4. The checks, and when to run them

    V=.venv/Scripts/python.exe

    $V kit/tools/wikitools/okfcheck.py
    $V kit/tools/wikitools/kbprofile.py          # --write regenerates
    $V kit/tools/wikitools/glossary.py
    $V kit/tools/pascal/markers.py --emit build/measured.toml
    $V kit/tools/pascal/ratchet.py --measured build/measured.toml
    $V kit/tools/pascal/observe.py --report
    $V kit/tools/pascal/artefact.py --check
    $V kit/tools/pascal/plan.py --report
    $V kit/tools/pascal/shared_asm.py --gate
    $V kit/tools/pascal/routines.py
    $V kit/tools/pascal/paslint.py
    $V kit/tools/pascal/asmaudit.py
    $V kit/tools/pascal/probecheck.py build.toml   # SLOW: one DOSBox run per probe per compiler
    $V kit/tools/encaudit.py
    $V kit/tools/eolcheck.py
    $V kit/tools/toolindex.py --check

    git ls-files -i -c --exclude-standard              # in the host AND in kit/

**Not a program, deliberately.** That last line names every file git tracks that the ignore rules claim to exclude, and a `.gitignore` added after the fact does nothing to a file already tracked -- so the commit that looks like the fix is the commit that hides it. It has to run in the kit as well as the host, because a submodule has its own index and the host's run cannot see inside it. Nine such files travelled in the kit for a day, and only the SECOND consumer could see them: the host they were committed from holds them in its working tree and reports clean. Wrapping one git command in Python would add a tool that measures nothing the command does not.

**`probecheck` is the one entry that names a config file**, because it drives the compilers and
those live in the build data rather than in the answers file. It is also the one check with a
real cost -- seconds per probe per compiler -- so it belongs in the list a session runs before
committing rather than in the loop it runs while editing. Skipping it is safe on any day nobody
touched a probe; a probe is cited by resolved investigations and by source comments the way a
binary is, and nothing else in a tree ever recompiles one.

**Some tools gate and are deliberately NOT on that list.** `braces`, `tagcheck`, `dsverify`, `unitorder`, `cleanconf` and `clean` all exit non-zero, and each belongs to a job rather than to a session: they check a source tree mid-transform, or a stripped copy against its original, and running them where that job is not underway reports on something nobody is doing. `cleanconf.py`'s docstring asks to be in "the gate" -- that means the gate of the transform it serves, and a host repository that runs one adds it to its own list. **The list above is what is true of every target; a tool that answers a question only one effort is asking belongs to that effort.**

**No paths and no numbers, and both absences are the point** -- this is the same list in every project. A host repository may have checks of its own on top; those live in its agent file.

**Run the list in full at the end of any session that touches the kit.** Not at the start: at the end, when there is something to be wrong about.

**A measured value never goes in a config or a document.** Coverage comes from the scan that measures it (`markers.py --emit` feeding `ratchet.py --measured`), and the routine lock lives in the register where a rise happens by itself. A number typed into a documented command sat two below the truth for days.

## 5. When a finding becomes a wiki observation

Write one when the finding would be true of **another binary built the same way**. Not when it is true of this target.

    a rule about how Borland Pascal emits something          -> observation
    a rule about what THIS program's scene 4 does            -> the host's notes
    a measurement instrument's blind spot                    -> observation
    where THIS target put a variable                         -> the host's notes

An observation states what you SAW and what it means, carries its **blind spot** -- what the instrument cannot see -- and cites the measurement. `wiki/README.md` has the shape and the validators; `wiki/CONTEXT.md` has the vocabulary, and it is worth reading before arguing about any of these words.

A conclusion that turned out to be wrong is written down as a **withdrawn conclusion**, next to the technique that produced it, not in an appendix. A lesson kept away from the point of use does not prevent its own recurrence.

## 6. Standing rules

- **Never re-express hand-written assembler as higher-level code.** Transcribe it verbatim, comment every line, and put the equivalent code above it as a comment, labelled as reference only. Re-expressing one routine's inner loops once invented four bug classes that do not otherwise exist.
- **A measurement beats an argument.** Put the claimed difference in a probe and let a build settle it. Confident claims about a compiler have had roughly a one-in-six survival rate here.
- **Distrust the verifier before the transcription.** The measuring tools have been wrong more often than the code they judged. Check a surprising measurement a second way.
- **Encoding and line endings split by who READS the file, and every script must say which it means.** Never rely on the locale.

  | the file is read by | encoding | line ending |
  |---|---|---|
  | humans and modern tools -- `.md` | `utf-8` | LF, so pass `newline='\n'` |
  | a 1990s DOS tool -- `.PAS` `.ASM` `.INC` `.MAP` `.BAT` `.CFG` | **`ascii`**, strictly on write | CRLF |
  | our own scripts' stdout via `subprocess` | `utf-8` | -- |

  `ascii` on a DOS source is a **guard**, not a preference: it raises rather than quietly writing an em dash as two bytes into a file the compiler will read. This rule has cost two mojibaked documents, two false comparisons, and -- in one afternoon -- two wrong turns inside a staleness check, once by decoding a source in the wrong codepage and once by preserving line endings so a regex anchored on `$` never matched.
- **Prose in markdown is never hard-wrapped.** One paragraph is one line.
- **No personal references, anywhere a repository can keep them.** No name, no initials, no email -- in source, documents, commit messages, issue bodies or the register. Write the ROLE: *the author*, *a person*, *the maintainer*, *a watched run*. The register's observation rows need only that a human watched, never which human, and `observe.py`'s own example says `--observer maintainer` for that reason. This is not fastidiousness: it is PII in a repository that may not stay private, and git history is permanent, so the cost of getting it wrong cannot be edited away later -- which is why it is a rule rather than a preference.
- **What a commit message must CARRY is the host repository's policy, not this file's** -- a trailer, a ticket reference, a sign-off. The rule above it travels; this one would have to be rewritten by every consumer, so it is theirs to state.

  There is a second reason, and it is the better one: **it was a rule the kit could not enforce and had no way to learn had been overridden.** On one consumer's machine a local `commit-msg` hook strips those lines, so the tracked rule and the actual history disagreed silently for as long as both existed -- the same shape as a check that cannot fail. A rule whose violation is invisible to the thing stating it belongs to whoever can see the violation.

## 7. Changing the kit from inside a project

The kit is a submodule. A change to it and a project's acceptance of that change are **two separate acts**, deliberately.

    # edit inside kit/, then
    git -C kit commit -am "..."   &&  git -C kit push
    git add kit                   &&  git commit -m "kit/ to <sha>: ..."
    git push --recurse-submodules=check

The last flag refuses if the commit this project pins is not on a remote another consumer can fetch -- which is the classic submodule failure. To take a newer kit: `git -C kit pull`, run the checks, then commit the new gitlink.

**EVERY consumer has to accept the change, not just the one you were working in.** A kit improvement that only one project pins is a kit that has forked in practice: the other keeps measuring with the old one, and nothing reports it. Bumping the second consumer is also the only test some changes get -- a project fact that leaked into the kit is invisible until a second project reads it, which is how one leaked table was found in its first minute. Where the other checkouts live is a machine fact, so it belongs in `kit.local.toml`, not here.

**Retiring what the kit replaced.** A consumer's own scripts do not vanish when the kit gains their successor: a successor landing and an original leaving are two acts, the same as above. The convention, and it is the same in every project:

1. **Tag once, up front** -- an annotated `archive/pre-kit-scripts` on the last commit holding every script. A tag is a permanent named pointer that cannot drift, and it can point at any commit, so there is no reason to carry superseded scripts through the whole migration. Recover one with `git show archive/pre-kit-scripts:<path>`.
2. **Then delete family by family, as each move lands.** Before deleting anything, check that the kit does the WHOLE of its job -- not the headline measurement, the whole job. A successor that reproduces every row and quietly drops a `--detail` flag has not superseded anything; it has moved the useful part and left the diagnostic behind. Three scripts survived this check for exactly that reason.
3. **Record where each script went, and the MEASUREMENT that made deleting it safe** -- a successor's name on its own does not say anybody checked. This project kept that in a retirement census while the migration ran, and turned it into one generated document when it finished: a census exists to catch drift between a table and a tree, and there is no drift left to catch once nothing moves again.

**Nothing in `kit/` may name a target.** If a tool needs a project's fact, the fact is passed in -- as an argument, or out of `kit.toml`. That line is a path test, which is why the kit is one folder: a fact that leaks into it travels to every other project and is wrong there. One did, and it took a second consumer's first minute to find it.

## 8. What to distrust

**Distrust the verifier before the thing it verifies.** Every instrument has been wrong at least once, and each time the code it accused was innocent. That is section 6's rule 3, and it is the frame for everything below.

**The findings themselves are in the wiki, because each is a measurement with a blind spot, which is what section 5 says an observation is.** They were written out here as well, and three of them existed in both places -- which is this section's own *second copy of one measurement* happening inside the section that names it. What is left here is the index:

| distrust | the finding |
|---|---|
| a second copy of one measurement | `drifted-second-copy` -- a drifted copy does not go quiet, it manufactures a finding phrased in the vocabulary of the thing measured |
| a total that quietly lost a component | `absence-reads-as-zero` -- a pattern matching nothing because its target is gone is indistinguishable from a target that measured nothing |
| a search that found everything | `destroyed-pattern-matches-everything` -- the inverse, and it fails OPEN, which is the expensive direction |
| a match rule stricter than its subject | `match-rule-stricter-than-its-subject` -- `NOT FOUND` is a claim about the rule as often as about the binary; ask what the tool has ever found |
| a tool's own docstring | `docstring-is-an-unrun-claim` -- the only claim about a program that nothing executes, and an omission in one is worse than an error |
| a green check you have not read | `exemption-that-cannot-fail` -- including a check whose SCOPE is a constant, which claims to have checked everything |
| a deleted config, as much as a deleted module | `config-is-a-dependency` -- the import graph is the smallest dependency graph and the only one with a tool |
| a successor that reproduced the headline | `successor-keeps-the-headline` -- a differential test over a passing corpus cannot call the modes that only speak when something fails |

**Two more belong to rules rather than to findings, and are stated where the rule is.** Prose holding a path or a number goes stale silently -- section 4, and a path belongs in `kit.toml` while a measured number belongs in the register or a generated file. And a guess that was never asked about: [`SETUP.md`](SETUP.md) records why the installer ranks nothing by file count, which is confidently wrong on any reconstruction because a release is complete and a reconstruction is not.

### Where a moved tool's answer CHANGED

Five did, and each is a repair rather than a regression. They are listed here because a changed number with no explanation is how a measurement loses its authority:

| instrument | what changed | why |
|---|---|---|
| `mapcmp` | one more unit measured; a neighbour went from "short" to exact | its segment list was missing a row -- see above |
| `coverage` | a program's verified bytes came back | it was reading zero from an archived tool |
| `rtl.py entries` | 350 entry points became 346 | its length table let three scans run into the NEXT segment and attribute entry points to the wrong one |
| `emit` | generated headers now name the binary and the offset | the provenance gate wants that before an emitter can be retired; the const bodies are byte-identical |
| `spans` | one part aligns 24 bytes more | two density gates formulated differently. The SAME spans are reported, two of them shorter -- no span is lost, so no work is hidden |

## 9. Environment traps, each of which has cost real time

These are facts about the tools a session is driven WITH, so a new project
inherits them on day one.

- **A DOUBLED backslash in a shell command is halved before the shell sees it.** The command carries one level of backslash escaping whose only escape is the backslash itself: `\\` becomes `\`, every other `\x` passes through. Measured: N backslashes arrive as ceil(N/2), while `\'`, `\"`, `\t`, `\n` are untouched. A lone backslash is safe, so raw Windows paths are fine; only doubling breaks -- and doubling is exactly what a Python literal needs for one backslash. Two failures follow and they look unrelated: a generated script gets a broken string literal (`'\\n'` arrives as a real newline INSIDE the quotes), and a `\\` beside a quote becomes `\` + quote, which the shell reads as an escaped quote and then reports `unexpected EOF` at the wrong line.

  **So: write a script with a file-writing tool and run it.** Do not inline it in a shell command. Build a backslash as `chr(92)`, and pass prose to a CLI through a file rather than an argument.

  This has cost this corpus a file -- one emitter sat with a literal newline inside a string literal, so it never compiled and never produced its output -- and on 23 Aug 2026 it bit **four times in one session**, once silently: a fix that appeared to apply and did nothing, because the anchor it searched for had been mangled the same way.

- **A shell may rewrite an argument that starts with a slash into a path.** `--sw=/GS` then compiles nothing and reports success; `gh api /repos/...` fails the same way. Prefix with `MSYS_NO_PATHCONV=1`, use a different shell, or call the tool from Python's `subprocess`.

- **A DOUBLE-QUOTED shell argument has `$NAME` substituted out of it, and an unset name substitutes to NOTHING.** This corpus's prose is full of compiler directives, so the sequences at risk are the ones it most needs to write down: `{$N+}` arrives as `{+}`, `{$G-}` as `{-}`, `$E` and `$S-` vanish outright. On 24 Aug 2026 it wrote `The fix that did it was {+} on P5S2` into the register, in a resolution whose whole subject was that `$N` and `$E` are different things.

  **What makes it worse than the backslash trap is that the damage reads as a typo.** A mangled path fails loudly; a missing `$N` leaves a grammatical sentence that a person will read as fact, in a file nothing re-derives. Nothing downstream can catch it, because the record IS the measurement.

  So: **prose with a `$` in it goes to a tool through a file, never through an argument.** Single quotes also protect it, but they are one edit away from failing and they cannot hold a single quote, so the file is the habit worth having -- and it is the same habit section 9's first entry already asks for, for the same reason.

- **The FIX for all three above is one habit: write the text to a file and hand the tool the path.** A script goes in a file and is run; prose goes in a file and is passed with `--body-file` or its equivalent; a pattern goes in a file, or the tool is asked to print what it received. Everything below is a reason that habit exists.

  **A quoting form can leave a search with an EMPTY pattern, which matches every line of every file.** Measured on 1 Sep 2026: the same pattern that correctly found nothing as a bare argument reported the condition present in EVERY file when written inside a nested substitution, because the quoting that builds it is not applied there and the search received zero bytes.

  **This is the one in this section that fabricates rather than breaks.** A halved backslash and a substituted `$NAME` damage the thing you are writing; an empty pattern damages what you are READING, and it fails OPEN -- reporting the condition found, everywhere, which is an actionable answer rather than an obviously empty one. It cost a session a near-miss: two groups of files scanned with the two different forms appeared to divide cleanly along a property, the division agreed with a theory already held, and it justified a bulk rewrite of four documents that turned out to have nothing wrong with them. **The corpus had divided along which command measured it.**

  So, positively: **give a scan its pattern as a plain argument or out of a file, ask it to print what it matched on when the answer matters, and confirm any surprising split with a tool that answers by a different route.** Re-running the same command more carefully returns the same wrong answer forever. The general form is in the wiki as `destroyed-pattern-matches-everything`.

- **Something in this environment has twice multiplied every line break in a markdown file** -- 91% blank lines in one document, 58% in another. The cause was never found. `tools/repairdoc.py` in a host repo diagnoses and repairs it, and proves content preservation before writing.

**Two of these have mechanisms rather than warnings, which is the only thing that has ever stopped a blind spot recurring**: an encoding auditor that PARSES rather than pattern-matches -- a line-based regex reported 32 sites of which 16 were artefacts while missing 4 real ones -- and a linter that refuses non-ASCII bytes in a DOS source.
