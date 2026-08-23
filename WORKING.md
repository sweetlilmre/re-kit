# How we work

**Read this first, at the start of every session.** It is the method; it holds no fact about any particular target. What is true of the target you are working on is in the host repository's own agent file and in `kit.toml`.

**It is longer than it should be, and the honest response is to say which part you read.** Sections 1, 2, 2a and 4 are the session: where things are, what to work on, the loop, and the checks. Sections 3 and 8 are REFERENCE -- forty-seven instruments and what to distrust -- consulted when you have a question, not read through. Sections 5, 6, 7 and 9 are the rules and the traps, and they repay one careful reading each. A document read at the start of every session is one whose length is a defect, so it is worth knowing that the first four sections are about a page.

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

## 2a. The loop, once you have picked something up

Sections 2, 4, 5 and 7 each describe a piece of a session. This is how they join, because knowing each piece is not the same as knowing the order.

    plan.py --report                     what to work on -- the first open one
    spans.py SPANS.toml PART             where the rebuild does NOT line up
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

### What tells you the loop is working

The plan shrinks, the coverage walk's spans shrink, and the ratchet does not fall. Nothing else is evidence, and in particular a green check list is not: it is the floor, not the goal.

## 3. Which instrument answers which question

**Forty-seven programs, and you will use six of them.** The list is long because it accumulated from two real targets; it is grouped below by the question you actually have, and the questions are in the order they come up. If two instruments could answer one, prefer the stricter: a rule that forgives less is a measurement that claims less.

### Getting in at all

| the question | the instrument |
|---|---|
| is this file packed? | `substrate/fingerprint.py` -- and what wrote it |
| unpack it | `substrate/unlzexe.py` (LZEXE 0.91) |
| is the file bigger than its load image? | `substrate/mzinfo.py` |
| split the image from what is appended to it | `substrate/split.py` |
| what are the segments? | `substrate/segmap.py`, from the relocations |
| what does the debug info say? | `substrate/tddump.py`, `substrate/symbols.py` |
| what text is in there? | `substrate/strings.py` |

### Reading a segment before writing any Pascal

| the question | the instrument |
|---|---|
| tell me four cheap things about this segment | `pascal/survey.py` -- far returns as a routine signature, string ABSENCE as evidence, far calls out, and `CALLF [DI+nn]` sites giving the VMT layout |
| where do routines probably start? | `pascal/rtl.py entries` |
| where is the runtime, and what is in it? | `pascal/rtl.py match`, then `rtl.py find` |
| this code is undecodable INT 34h noise | `pascal/x87.py survey`, then `x87.py fix` |
| what numbers is it loading? | `pascal/x87.py const` |
| what is this Mode-X plane really a picture of? | `substrate/modex.py` |

### Building it

| the question | the instrument |
|---|---|
| build it | `pascal/build.py CONFIG.toml` |
| will the compiler hate my source? | `pascal/paslint.py` -- run it FIRST; a nested-comment defect is reported dozens of lines from its cause |
| what does this unit use but never declare? | `pascal/undeclared.py` |
| do two compilers disagree about this construct? | `pascal/codegen.py` -- put it in a probe unit and measure, rather than arguing |
| turn compiled-in data back into typed constants | `pascal/emit.py` |

### Measuring what came out

| the question | the instrument |
|---|---|
| does this ROUTINE match, byte for byte? | `pascal/routines.py` |
| does this compiled UNIT match its segment? | `pascal/units.py`, and `--detail` / `--all` once it does not |
| does a `{$L}` object module match? | `pascal/objcheck.py`, on the object's OWN relocations |
| which blocks of a half-written segment are right? | `pascal/blockcmp.py` |
| does every LINKED segment match? | `pascal/linkcmp.py`, `pascal/mapcmp.py` for the lengths |
| did the linker put the units in the original's order? | `pascal/linkorder.py` |
| does the initialised data match? | `pascal/dgroup.py` |
| **which bytes of the original do NOT line up at all?** | `pascal/spans.py` |
| how much of the whole thing is accounted for? | `pascal/coverage.py` |
| is our whole build the original's bytes? | `pascal/artefact.py --check` |
| is this build output still the source it was built from? | `pascal/staged.py`, and every instrument that can refuses a stale one |

**`spans.py` is the one to reach for when a check is green and the rebuild still misbehaves.** Every other instrument above measures something somebody DECLARED, so a routine nobody declared is not a failure in its scheme -- it is not a row at all. That walk is where absence has somewhere to appear.

### Keeping the record honest

| the question | the instrument |
|---|---|
| what is the state of every artefact? | `pascal/plan.py --report`, `pascal/ratchet.py` |
| record what I saw when I ran it | `pascal/observe.py` |
| read the markers, measure coverage | `pascal/markers.py` (`marker.py` is its reader) |
| is hand-written assembler duplicated between units? | `pascal/shared_asm.py` |
| is the transcription rule met? | `pascal/asmaudit.py` |
| is the wiki valid? | `wikitools/okfcheck.py`, `wikitools/kbprofile.py`, `wikitools/glossary.py` |
| does any tool leave an encoding to the locale? | `encaudit.py` |
| a document's line breaks got multiplied | `repairdoc.py` |
| install the kit into a new project | `wizard.py` -- see `SETUP.md` |

### The two that are not instruments

`substrate/align.py` is the ENGINE, not a tool: one comparison in three shapes -- how far agreement reaches, how many bytes of two blocks differ, and every place they disagree -- with four allowed-difference rules and two location strategies, all passed in because both belong to the artefact rather than to the comparison. Nothing runs it directly; seven instruments above are callers. `substrate/omf.py` is a reader in the same sense: it says which bytes of an `.OBJ`'s code are fixups, and `objcheck.py` is what asks. `pascal/register.py` is the register's one serializer, so no tool can drop another's section, and `project.py` is the only reader of the answers files.

`pascal/build.py` MAKES the thing the others measure rather than measuring anything. Note the word: a **harness** in this vocabulary is a small program that runs one piece of the subject so a person can watch it, so the thing that builds those is not one.

`tools/README.md` says which tier each belongs to and why.

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
    $V kit/tools/encaudit.py

    git ls-files -i -c --exclude-standard              # in the host AND in kit/

**Not a program, deliberately.** That last line names every file git tracks that the ignore rules claim to exclude, and a `.gitignore` added after the fact does nothing to a file already tracked -- so the commit that looks like the fix is the commit that hides it. It has to run in the kit as well as the host, because a submodule has its own index and the host's run cannot see inside it. Nine such files travelled in the kit for a day, and only the SECOND consumer could see them: the host they were committed from holds them in its working tree and reports clean. Wrapping one git command in Python would add a tool that measures nothing the command does not.

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
- **Commits carry** `Co-authored-by: Claude <noreply@anthropic.com>`.

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

- **A verifier more than the thing it verifies.** See rule 3. Every instrument in the table above has been wrong at least once, and each time the code it accused was innocent.
- **A tool's own docstring.** Two here promised a config file that did not exist and a usage line nobody could run; a third described an operand format its own table could not decode, so asking for it by the name the docstring used raised an error. If a docstring claims a mechanism, look for the mechanism.
- **Prose holding a path or a number.** It goes stale silently. A path belongs in `kit.toml`, a measured number in the register.
- **A guess that was never asked about.** A wizard proposing a project's sources by file count is confidently wrong on any reconstruction, because a release is complete and a reconstruction is not.
- **A green check you have not read the output of.** One check here could never pass and said so in a line nobody read; another passed on nothing at all after its path moved -- it reported *0 problem(s) in 0 file(s)* in a repository whose sources sat one directory away.
- **A SECOND COPY OF ONE MEASUREMENT.** Two instruments each held the original's segment list, both said they came from the layout document, and nothing kept them in step. One was missing a segment -- so that unit was never compared, and because each length is computed as the NEXT segment's address minus its own, the gap also inflated its neighbour by exactly the missing segment's size. The tool reported that neighbour as *"short -- 144 byte(s) of routines nothing references"*, which reads like an observation about the runtime and was entirely an artefact. **A drifted copy does not merely go quiet; it manufactures findings.**
- **A REGEX OVER ANOTHER TOOL'S OUTPUT.** One instrument shelled out to a second and parsed a number out of what it printed. The second was archived, so the parse matched nothing, the count fell back to zero, and 1,616 verified bytes dropped out of a coverage total in silence. **A pattern that returns nothing on a MISSING TOOL is indistinguishable from a tool that measured nothing.** It refuses now. Where one instrument must read another, it must be able to tell absence from zero.
- **A DELETED CONFIG, as much as a deleted module.** Four surviving scripts were broken by this migration's own deletions, and two of those depended on a `.conf` file rather than on an import -- so nothing about the import graph would have caught them. One had stopped running entirely and its census row still read `carry`.

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

- **Something in this environment has twice multiplied every line break in a markdown file** -- 91% blank lines in one document, 58% in another. The cause was never found. `tools/repairdoc.py` in a host repo diagnoses and repairs it, and proves content preservation before writing.

**Two of these have mechanisms rather than warnings, which is the only thing that has ever stopped a blind spot recurring**: an encoding auditor that PARSES rather than pattern-matches -- a line-based regex reported 32 sites of which 16 were artefacts while missing 4 real ones -- and a linter that refuses non-ASCII bytes in a DOS source.
