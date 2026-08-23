# How we work

**Read this first, at the start of every session.** It is the method; it holds no fact about any particular target. What is true of the target you are working on is in the host repository's own agent file and in `kit.toml`.

It is deliberately short. A document read at the start of every session is one whose length is a defect.

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

## 3. Which instrument answers which question

One comparison engine, several instruments. Each supplies its own allowed-difference rule **and** its own location strategy, because both belong to the artefact rather than to the comparison.

| the question | the instrument |
|---|---|
| does this ROUTINE match, byte for byte? | `pascal/routines.py` |
| does this compiled UNIT match the segment it rebuilds? | `pascal/units.py` |
| does a `{$L}` object module match, judged by its own relocations? | `pascal/objcheck.py` |
| does every LINKED segment match, and where did the variables go? | `pascal/linkcmp.py` |
| which blocks of a half-written segment are right? | `pascal/blockcmp.py` |
| which bytes of the original do NOT line up at all? | `substrate/align.py`, via a caller |
| is this build output still the source it was built from? | `pascal/staged.py` |
| is any hand-written assembler duplicated between units? | `pascal/shared_asm.py` |
| what does the debug info say? | `substrate/tddump.py` |
| what does an `.OBJ` record as a relocation? | `substrate/omf.py` |
| how do I BUILD any of it? | `pascal/build.py CONFIG.toml` |

`pascal/build.py` is the odd one out: it MAKES the thing the others measure rather than measuring anything. It stages sources under 8.3 names, drives a real Turbo Pascal under DOSBox-X and reads the log back, taking the compiler, its switch line, the name map, the ordering strategy and the dialect from a config per target. Note the word: a **harness** in this vocabulary is a small program that runs one piece of the subject so a person can watch it, so the thing that builds those is not one.

`tools/README.md` says which tier each belongs to and why. If two instruments could answer a question, prefer the stricter one: a rule that forgives less is a measurement that claims less.

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
    $V kit/tools/census.py
    $V kit/tools/pascal/shared_asm.py --gate
    $V kit/tools/pascal/routines.py

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
- **Commits carry** `Co-authored-by: Claude <noreply@anthropic.com>`.

## 7. Changing the kit from inside a project

The kit is a submodule. A change to it and a project's acceptance of that change are **two separate acts**, deliberately.

    # edit inside kit/, then
    git -C kit commit -am "..."   &&  git -C kit push
    git add kit                   &&  git commit -m "kit/ to <sha>: ..."
    git push --recurse-submodules=check

The last flag refuses if the commit this project pins is not on a remote another consumer can fetch -- which is the classic submodule failure. To take a newer kit: `git -C kit pull`, run the checks, then commit the new gitlink.

**Retiring what the kit replaced.** A consumer's own scripts do not vanish when the kit gains their successor: a successor landing and an original leaving are two acts, the same as above. The convention, and it is the same in every project:

1. **Tag once, up front** -- an annotated `archive/pre-kit-scripts` on the last commit holding every script. A tag is a permanent named pointer that cannot drift, and it can point at any commit, so there is no reason to carry superseded scripts through the whole migration. Recover one with `git show archive/pre-kit-scripts:<path>`.
2. **Then delete family by family, as each move lands.** Before deleting anything, check that the kit does the WHOLE of its job -- not the headline measurement, the whole job. A successor that reproduces every row and quietly drops a `--detail` flag has not superseded anything; it has moved the useful part and left the diagnostic behind. Three scripts survived this check for exactly that reason.
3. **`census.py`'s `archived` state is the record**, and it names the successor. The tidy alternative -- deleting the row -- discards the only note of where the script went.

**Nothing in `kit/` may name a target.** If a tool needs a project's fact, the fact is passed in -- as an argument, or out of `kit.toml`. That line is a path test, which is why the kit is one folder: a fact that leaks into it travels to every other project and is wrong there. One did, and it took a second consumer's first minute to find it.

## 8. What to distrust

- **A verifier more than the thing it verifies.** See rule 3. Every instrument in the table above has been wrong at least once, and each time the code it accused was innocent.
- **A tool's own docstring.** Two here promised a config file that did not exist and a usage line nobody could run. If a docstring claims a mechanism, look for the mechanism.
- **Prose holding a path or a number.** It goes stale silently. A path belongs in `kit.toml`, a measured number in the register.
- **A guess that was never asked about.** A wizard proposing a project's sources by file count is confidently wrong on any reconstruction, because a release is complete and a reconstruction is not.
- **A green check you have not read the output of.** One check here could never pass and said so in a line nobody read; another passed on nothing at all after its path moved.

## 9. Environment traps, each of which has cost real time

These are facts about the tools a session is driven WITH, so a new project
inherits them on day one.

- **A DOUBLED backslash in a shell command is halved before the shell sees it.** The command carries one level of backslash escaping whose only escape is the backslash itself: `\\` becomes `\`, every other `\x` passes through. Measured: N backslashes arrive as ceil(N/2), while `\'`, `\"`, `\t`, `\n` are untouched. A lone backslash is safe, so raw Windows paths are fine; only doubling breaks -- and doubling is exactly what a Python literal needs for one backslash. Two failures follow and they look unrelated: a generated script gets a broken string literal (`'\\n'` arrives as a real newline INSIDE the quotes), and a `\\` beside a quote becomes `\` + quote, which the shell reads as an escaped quote and then reports `unexpected EOF` at the wrong line.

  **So: write a script with a file-writing tool and run it.** Do not inline it in a shell command. Build a backslash as `chr(92)`, and pass prose to a CLI through a file rather than an argument.

  This has cost this corpus a file -- one emitter sat with a literal newline inside a string literal, so it never compiled and never produced its output -- and on 23 Aug 2026 it bit **four times in one session**, once silently: a fix that appeared to apply and did nothing, because the anchor it searched for had been mangled the same way.

- **A shell may rewrite an argument that starts with a slash into a path.** `--sw=/GS` then compiles nothing and reports success; `gh api /repos/...` fails the same way. Prefix with `MSYS_NO_PATHCONV=1`, use a different shell, or call the tool from Python's `subprocess`.

- **Something in this environment has twice multiplied every line break in a markdown file** -- 91% blank lines in one document, 58% in another. The cause was never found. `tools/repairdoc.py` in a host repo diagnoses and repairs it, and proves content preservation before writing.

**Two of these have mechanisms rather than warnings, which is the only thing that has ever stopped a blind spot recurring**: an encoding auditor that PARSES rather than pattern-matches -- a line-based regex reported 32 sites of which 16 were artefacts while missing 4 real ones -- and a linter that refuses non-ASCII bytes in a DOS source.
