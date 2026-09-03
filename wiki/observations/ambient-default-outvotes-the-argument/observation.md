---
type: Observation
title: A tool that takes one fact by argument and another from the environment measures a chimera
description: Point an instrument at another target's config and it obeys the argument for the fact you passed and the ambient environment for every fact you did not. The two halves then describe different targets, and the result is not an error but a plausible number. Measured in one toolkit -- six instruments, two different conventions for finding the project root, and one that reported 1 of 30 positions agree when the honest answer was that the question was incoherent.
tags: [tooling, verification, measurement, blind-spot, configuration]
measured_on: one reverse-engineering toolkit, six instruments across three targets
timestamp: 2026-09-03T00:00:00Z
---

# A tool that takes one fact by argument and another from the environment measures a chimera

An instrument that reads a config path from `argv` looks like it has been told what to measure. It has been told **part** of what to measure. Every other input it needs -- the source directory, the build directory, the original binary -- it still finds the way it always did, by searching upward from the current directory for the project's answers file.

Pass it a config belonging to a different project and both mechanisms work perfectly. The config comes from where you pointed; everything else comes from where you are standing.

**The output is a measurement of a target that does not exist.**

## Why it works

The two halves fail differently, and only one of them fails loudly.

- **A wrong path raises.** A missing file, an unreadable map, a segment beyond the end of an image -- these stop the tool.
- **A wrong pairing computes.** One target's segment order against another target's source tree is a well-formed question with a real answer. Nothing in it is missing. The answer is simply about nothing.

So the defect selects for survival: it appears only in the cases where every individual input is valid, which is exactly the case a reviewer waves through.

**The measured instance.** An instrument that predicts a linker's segment order from `uses` clauses was handed a sibling project's layout config while run from the wrong directory. It took the segment order from the argument and the Pascal sources from the ambient answers file, and printed:

```
1 of 30 positions agree
```

Thirty rows of a comparison table, one column from each of two unrelated programs. The number is false, the table is well-formed, and there is no warning anywhere in the output. It was caught **only** because the correct answer happened to be memorable -- 30 of 30 the day before. Had the honest figure been 27, the hunt would have gone looking for a cause in the source.

**Two conventions in one toolkit.** The same kit resolved the project root two different ways, and nobody had noticed the disagreement because each tool was self-consistent:

| how the root was found | tools | behaves when pointed elsewhere |
|---|---|---|
| walk up from the **config path** given in `argv` | the coverage and DGROUP instruments | correct -- the config drags its own project with it |
| walk up from the **current directory** | the link-order instrument | wrong -- the config and the tree come from different projects |

The first is right, and it is right for a reason worth naming - **a config file knows which project it belongs to, and a working directory does not.**

## Blind spot

**A tool with a single source of truth cannot exhibit this, so auditing tools one at a time will not find it.** The defect is a relationship between two inputs. Read the argument handling and it looks correct; read the environment lookup and it looks correct.

**Refusing is often impossible.** The instrument cannot tell that a config and a source tree are unrelated -- both exist, both parse, both describe a Pascal program with segments. Only the *provenance* differs, and provenance is precisely what neither input carries. The fix is not a check inside the tool; it is deriving every path from the same root.

**Verifying in the other project does not save you, if you verify from the wrong directory.** The pairing failure and the "I ran the unchanged copy" failure look identical from outside -- both produce a number, and neither mentions which files it used. Two separate attempts at verification here were invalid for two different reasons before one was valid.

**Printing the resolved inputs is the cheap mitigation and it is not a check.** Every one of these tools announces the file it chose, on a line beginning `using`. That line was present, correct, and ignored -- because a tool that announces its inputs still looks exactly like a tool that is working.

## Cost

Deriving the root from the config path rather than the cwd is a three-line change per tool, and it is not detectable by any test that runs a tool in its own project -- which is every test that exists. The cost is in noticing, not in fixing.

## Example

Six instruments in one toolkit read a layout config. Five resolved at least one further input from the ambient environment. The one that mattered paired a 30-segment order with the wrong source tree and reported a 1-of-30 agreement as fact.

The general shape, worth carrying to any toolkit - **when a tool accepts one input explicitly, ask where it gets the rest.** If the answer is "from wherever it is run", it has two masters, and the quiet case is the dangerous one.

## Citations

- Six instruments, three targets, one toolkit; the link-order instrument's 1-of-30 report.
- [Every declared routine matches, and the rebuild still behaves differently](../verifier-blind-to-absence/observation.md) -- an instrument silent about what it never looked at. Here the instrument is not silent, it is confident, which is the harder case.
- [A tool's docstring is the only claim about it that nothing executes](../docstring-is-an-unrun-claim/observation.md) -- the usage line that tells you to pass a config is itself unchecked, and it does not mention the inputs the tool takes from elsewhere.
