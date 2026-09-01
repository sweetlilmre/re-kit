---
type: Observation
title: A name is a claim, and it should be no stronger than the evidence that produced it
description: Reconstruction names things from USE -- a writer and a reader together say what a byte means. Some things have no use to name them after -- a variable written and never read, a structure field the program never touches. The temptation is a behavioural name anyway, and a wrong name is the only wrong thing in a reconstruction that no build, no comparison and no verifier can ever fail. Name it for its provenance instead, and shape the name so a reader can see which kind it is.
tags: [reverse-engineering, naming, documentation, verification, measurement]
timestamp: 2026-08-29T00:00:00Z
---

# A name is a claim, and it should be no stronger than the evidence that produced it

Most naming in a reconstruction is safe because it is measured. A byte with one writer and one reader is named by that pair: written straight after a file is opened, read to decide whether the file gets closed, and `SongOpen` is not a guess but a summary. Every arm of the evidence is in the image and any later contradiction shows up as a use that does not fit.

**Some things have no use to name them after**, and they are common:

* a variable a command-line switch sets and **nothing anywhere reads**
* a published structure's field the program only reads (see [A field nothing in the image writes is an input, not a switch that was never wired up](../no-writer-means-input/observation.md))
* an on-disk record's field the loader skips over -- present in the layout, absent from the code

These are the ones to be careful with, because the pressure to name them is highest exactly where the evidence is weakest. A `Filler2 : array[1..14] of Byte` is an eyesore and an `Rut_0bc6` looks unfinished, and both are honest.

## Why a wrong name is the worst thing to get wrong

Everything else in a byte-exact reconstruction is checked by something. A wrong constant changes a byte. A wrong declaration order moves an address. A wrong type changes an instruction. The build fails, or the comparison reports it, or the next tool downstream does.

**A name is checked by nothing.** It compiles, it matches, it packs identically, and it is read by every future reader as if it were measured -- because everything around it was. It is the one place where a guess can enter a reconstruction and never come out.

## Name it for its provenance, and let the name say so

The rule is not "leave it unnamed". It is that when you cannot name a thing for what it DOES, name it for what you can demonstrate, and choose a form that does not overclaim.

Measured, three ways, on one 1994 player:

| Evidence available | Named | Not named |
|---|---|---|
| one writer, one reader | `SongOpen` -- what the pair means | |
| a switch writes it, nothing reads it | `NxOption` -- the switch reached us | `NoExtended`, `NoXms` -- what `nx` *probably* stood for |
| a published format specification | `Ffi`, `MasterVol`, `UltraClick` -- the spec's own field names | names invented to look like the neighbours |

The middle row is the whole point. `NxOption` claims exactly one fact and it is a fact: the command line said `nx`. `NoExtended` claims to know what the feature was going to do, and there is no instruction anywhere that says. Both names read equally well; only one of them can be wrong.

The third row is the same rule with a stronger source. A specification is real evidence and it is a *different kind* from an instruction -- so the declaration says which it is, in the comment, at the field. Where the two disagree the binary wins, and that sentence only means something if a reader can tell which fields came from where.

## The tell that you are about to overclaim

You are writing a name and the justification in your head is a plausible expansion of an abbreviation, a neighbouring field's convention, or what the program *would sensibly* do. None of those are observations. When the reason you can give for a name is not a line of the image or a line of a document, the name is a hypothesis and the declaration should say so in the comment rather than bury it in the identifier.

Two corollaries worth stating:

* **Do not name a large unread region field by field.** A 768-byte published control block with three unread stretches got three fillers, not thirty invented names -- inventing them would put guesses into precisely the part other programs depend on. Fillers there are the accurate record.
* **A name derived from an address is a placeholder and should look like one.** `Rut_0bc6` is ugly on purpose: it cannot be mistaken for a finding, and it sorts every remaining unknown together.

## See also

* [A field nothing in the image writes is an input, not a switch that was never wired up](../no-writer-means-input/observation.md)
* [A filler declaration records what you have not looked at, not what is not there](../filler-is-not-a-finding/observation.md)
* [A compare tool's number is plausible, and it is wrong](../plausible-and-wrong/observation.md)
* [The same bytes answer to two different addresses](../two-names-one-address/observation.md)
