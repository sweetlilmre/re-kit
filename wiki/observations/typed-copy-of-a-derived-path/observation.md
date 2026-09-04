---
type: Observation
title: The typed copy of a derived answer goes stale where nothing can fail
description: A machine path was typed into a committed build config as well as being answered in the ignored one; three installs were renamed, the answer that invokes the compiler was corrected and the typed copy was not, because nothing compiles through it -- and in the same generated list the derived neighbour was right while the typed one had been wrong for as long as it existed.
tags: [tooling, verification, drift, toolchain, blind-spot]
measured_on: 2026-09-04
timestamp: 2026-09-04T00:00:00Z
---

# The typed copy of a derived answer goes stale where nothing can fail

Two files named the same directory. One was the machine-specific answers file, which git ignores and a person edits when an install moves. The other was the committed build config, which typed the same path beside the compiler it belongs to, for a PATH line.

Three installs were renamed. The answers file was corrected -- it had to be, because the compiler is invoked through it and a wrong path there stops the build. The committed copy was not, and could not have been noticed, because **nothing compiles through it**: every invocation the generated batch file writes is fully qualified, so the PATH line it feeds is read by nobody during a build. Fifteen entries across five configs were stale for as long as the rename was old, and every check passed throughout.

The sibling consumer's four entries were correct the whole time, which is the part that makes this measurable rather than anecdotal. Same tool, same mechanism, and the difference was only whether that repository had been through a rename.

## Why it works

**The duplicate lives on the side where being wrong is free.** A path used to LAUNCH something fails loudly and immediately. The same path used only to decorate an environment fails at a moment nobody is watching -- here, at an interactive prompt, where a person types the compiler's name and gets `Bad command or file name`. That prompt is used occasionally and by one person, so the failure never accumulates into a report.

**Correcting the live copy makes the dead one harder to find, not easier.** After the rename the two copies disagreed, and the disagreement was invisible because only one of them is ever exercised. A reader comparing them would have caught it; nothing compares them, and there is no reason anybody would look at the decorative one while the build is passing.

**The asymmetry showed up inside one function, which is the tell worth remembering.** The code that assembles that PATH line took the assembler's directory by SPLITTING the answer that invokes the assembler, and the compiler's by reading the typed config value:

    path = [comp.get("binpath")]                  # typed, and stale
    tasm = machine("toolchain.tasm", ...)
    path.append(tasm.rsplit(SEP, 1)[0])           # derived, and right

Two entries, one list, one of each. The derived one had never been wrong and the typed one had never been right. The function's own comment said the entries come "from the same answers the build compiles with, so the interactive prompt cannot disagree with the build about which compiler is installed" -- so the intent was already written down, and half implemented.

## Blind spot

**Deriving fixes the duplicate, not every embedded path.** The same corpus has a compiler switch line carrying `/UBIN;.;C:\TP701\UNITS` -- a machine path inside a value that is otherwise a measured build input, taken verbatim from the original's own config. Nothing can derive that, because the switch line is data about the ORIGINAL and not about this machine. A rename would break it the same way, and only a build would say so.

**A derivation is only as good as the answer it derives from.** It moves the single point of truth; it does not create one. If the answers file is wrong, the build fails first and loudly, which is the right order -- but a project that had no such answer and only the typed copy would be made worse by this change, not better.

**The failing surface here was an interactive prompt, and that is why it survived.** The general form is a copy whose only consumer is a human doing something occasional. There is no check to add that would have caught it, short of comparing the two copies -- which is the fix, expressed as code.

## Cost

One helper, and the deletion of the duplicated key from every config. The test that it is safe is cheap and worth insisting on: **compute the derived value for every entry in every consumer and compare it against the typed one before changing anything.** The result should be *identical everywhere the typed value is correct* and different only where it is known stale. Measured here: 4 identical in one consumer, 15 changed in the other, 0 underivable.

If it is not identical where the config is right, the derivation is wrong and the typed value was carrying something the answer does not.

The rule worth writing at the top: **a machine path belongs in the file a machine's owner edits, and everywhere else it should be derived from there.** A second copy is not merely redundant -- it is redundant in the place where nothing can tell you it has gone wrong.

## Example

A 16-bit Pascal reconstruction toolkit shared by two consumers, 4 Sep 2026. Raised by a person reading a config: the machine answers file said one compiler lived at `C:\TP600` while the committed build config still said `C:\TP6`, and that config's own comment recorded a related incident -- a stale path once making the build report SUCCESS without compiling, because DOS sets no errorlevel for a command it cannot find.

That incident was real and was NOT this one. It belonged to the answer that invokes the compiler, and it had been fixed. The typed copy was the leftover of the same rename, in the one place that compiles nothing, so it had survived the fix that corrected its siblings. Distinguishing the two took reading which of them the generated batch file actually uses: all 32 invocations in it were fully qualified, 30 of one compiler and 2 of the assembler, and not one bare name that would need a PATH at all.

Derived, both consumers still build byte-identical -- 0 differing bytes in the linked image, in three trees across two repositories -- and the generated PATH line now names a directory that exists.
