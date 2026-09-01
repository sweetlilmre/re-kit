---
type: Observation
title: A tool's docstring is the only claim about it that nothing executes
description: Every other statement a program makes is tested by running it. The docstring is prose, so a usage line nobody can run, a config file that does not exist, an operand format the tool's own table rejects, and a subcommand the argument parser registers but the docstring omits all survive indefinitely. Measured across one toolkit -- four such defects, three of them promising a mechanism that was absent and one omitting a subcommand two documents instruct you to use.
tags: [tooling, verification, documentation, drift, measurement]
measured_on: one reverse-engineering toolkit, 74 programs
timestamp: 2026-09-01T00:00:00Z
---

# A tool's docstring is the only claim about it that nothing executes

A program's code is checked constantly, by the simple mechanism of being run. Its docstring is checked by nobody.

**So when a docstring claims a mechanism, look for the mechanism.** The claims that survive longest are the ones that sound most like documentation: a usage line, a named config file, an operand format, a list of subcommands.

Four shapes, all measured on one toolkit:

| the docstring said | what was true |
|---|---|
| it reads a named config file | no such file existed anywhere |
| here is the command to run it | nobody could run that line as written |
| operands take this format | the tool's own table could not decode it, so asking by the documented name raised an error |
| it has these three subcommands | the argument parser registers four, and the missing one is the one two other documents instruct you to use |

## Why it works

A docstring is written at the moment of most knowledge and read at the moment of least, which is exactly the trade that makes it valuable. The cost is that it is also written *once*, while the code beside it changes on every subsequent day.

The asymmetry is the whole point:

- **Code that stops being true stops working.** A renamed function raises; a changed signature raises; a deleted file raises when something opens it.
- **Prose that stops being true reads the same as prose that is true.** There is no failing state, so there is no signal, so there is no repair.

**And the fourth row is worse than the other three**, because it is an omission rather than an error. A docstring that lists three subcommands where four exist contains no false sentence at all -- every word of it is accurate. Nothing a reader could check would reveal the gap, and a reader who trusts it simply never learns the fourth exists. **An incomplete list is a false claim that no proofreading catches**, which is why the enumeration has to come from the code rather than from memory.

## Blind spot

**Reading a docstring against its code catches a lie and not an omission.** You can verify every claim it makes and still be missing what it does not mention -- which was the most consequential of the four here.

**A generated document inherits the problem and hides it better.** The instinct is to generate the description from the code, and it is right, but the extractor is then the unchecked thing. One inventory generator built for exactly this purpose reported two tools as having **no docstring at all**: both open with a *raw* string literal and the pattern matched only the plain form. Had that run written its output, the generated document would have carried two false claims **with the authority of having been generated**. A generator's extraction is as much a measurement as anything it prints.

**Nothing here scales to a check.** A tool could compare a docstring's usage lines against the argument parser, and that would catch two of the four rows; the config-file claim and the operand format need a person who knows what the mechanism should look like.

## Cost

One read of the docstring against the code, at the moment you are about to trust it. That is normally the moment you reach for the tool -- which is the cheapest possible time, because you are already there.

## Example

A toolkit of 74 programs whose stated convention is that **every tool carries the finding that produced it in its docstring** -- which makes the docstrings load-bearing and is the reason these matter rather than being untidy.

The subcommand case is the one to remember. Two separate documents instruct the reader to run the tool's disassembly subcommand; the tool's own usage block lists three subcommands and that is not one of them. Both documents are right and the docstring is not wrong, only short -- so a reader following the docstring concludes the instruction elsewhere is stale, which inverts who is trusted.

## Citations

- The four defects above, in one toolkit's own programs.
- [A file is generated only while something compares it against its generator](../generated-means-checked/observation.md) -- the same problem for generated files, and why generating a description does not by itself make it true.
- [The addresses written in comments are the only claims nothing checks](../comments-are-unchecked-claims/observation.md) -- the same asymmetry inside source comments, where it is checkable because an address can be verified against a declaration. A docstring's claims mostly cannot.
- [Documentation defects are invisible to every check and visible on the first read-through](../walk-the-path-a-reader-takes/observation.md) -- the method that finds these, which is to walk a reader's question rather than to review a file.
