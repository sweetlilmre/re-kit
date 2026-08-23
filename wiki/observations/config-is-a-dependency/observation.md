---
type: Observation
title: A script breaks and nothing in the import graph explains it
description: Four surviving scripts were broken by a migration's own deletions, and two depended on a config file rather than a module -- so the check everybody runs, "who imports this", could not see them.
tags: [tooling, migration, dependencies, verification]
timestamp: 2026-08-23T00:00:00Z
---

# A script breaks and nothing in the import graph explains it

You are retiring superseded tools. Before deleting one you check who imports it, repoint those, and delete. Later a tool that had nothing to do with any of it fails -- on a missing file, or worse, on a plausible-looking wrong answer.

**The import graph is the smallest of the dependency graphs, and it is the only one with a tool.** A script also depends on things a parser cannot see:

* a **configuration file** it names -- a `.conf`, a `.cfg`, a table of paths;
* **another program it runs**, by path or by name, and the SHAPE of what that prints;
* a **generated file** whose format it assumes;
* the **directory layout** it computes from its own location.

Every one of those is a dependency; none appears in an `import`. So "who imports this" answers a question narrower than the one being asked, and it answers it confidently.

## Why it works

Deletion is the only operation where an unnoticed dependency is guaranteed to surface later rather than immediately, and it surfaces in whatever way that dependency happens to fail. A missing module raises on import, at once, loudly. A missing config raises when the program reaches it, which may be after it has already done work. A missing PROGRAM does not raise at all if the caller was written to tolerate a bad answer.

Which means the loudness of the failure has nothing to do with the severity of the mistake, and the quietest case is the one that keeps producing numbers.

## Blind spot

**A grep for the filename is better and still not enough.** It finds a config named as a literal; it misses one assembled from parts, one reached through a variable, and one named in a document a person will follow.

**Checking that a script still IMPORTS is not checking that it still works.** Two of the four here imported cleanly and were broken anyway. The only sufficient check is running the thing, which is why an instrument nobody can run on this machine is a real limit on what a migration can promise.

**A script already broken before you touched it will be blamed on you, and sometimes should not be.** One of these had stopped working when a path moved weeks earlier, and its retirement row still said it was fine. Establishing whether a tool ran BEFORE the change is part of the work.

## Cost

Running each surviving tool once, per deletion, and reading the output rather than the exit code. That is more expensive than a grep and is the only thing that actually answers the question.

## Example

A toolkit migration across two repositories, 23 Aug 2026. Fifty-nine scripts were retired; **four surviving ones were broken by those deletions**, and the four failed in four different ways:

| what broke | how it depended | how it failed |
|---|---|---|
| nine scripts importing one module | `import` | on import, at once, loudly |
| a compiler-codegen probe | a committed `.conf` its build helper named | on a missing file, when it got there |
| a coverage instrument | ran another tool and parsed its output | **not at all** -- it read zero and carried on |
| the coverage walk | `import` of an archived module | on import -- and it had been the driver of the top open investigation |

Only the first was caught by checking importers, because checking importers was the check. The `.conf` case needed the file restored from the archive tag before an honest comparison could even be made, and the third produced a plausible total for as long as nobody ran the tool it had lost. [1]

# Citations

[1] The resolutions of [Tag the archive, then delete what the toolkit superseded](https://github.com/sweetlilmre/PsychoNeurosis/issues/36) and [The thirty-two scripts still outside the kit](https://github.com/sweetlilmre/PsychoNeurosis/issues/50), which record each of the four and what it cost.
