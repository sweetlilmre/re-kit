# Which instrument answers which question

**Reference, not reading.** Nothing here is a step; it is a lookup table, grouped
by the question you actually have, with the questions in the order they come up.
Open it when you have one of those questions and close it again.

**It is a SELECTION, not a census.** `tools/README.md` carries the generated
inventory of every program; this names the ones a session reaches for. A tool
missing from here is not a tool that does not exist.

**If two instruments could answer one question, prefer the stricter.** A rule
that forgives less is a measurement that claims less.

**You will use about six of them.** The list is long because it accumulated from two real targets.

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
| what did the source DECLARE, and which `$G` built it? | `pascal/prologue.py` -- the frame form names the unit's switch, the operand constrains the `var` block, and a range prints every BP slot the routine touches, including the ones it never reads |
| how big is each global, and is anything declared as a pointer that the original has inline? | `pascal/dsgaps.py` -- sorts the `DS:$XXXX` addresses the sources' own comments record and prints the GAP to the next, which is the size of whatever sits at the first. A four-byte declaration against a gap of thousands is a pointer where the array belongs. It measures the ORIGINAL, needs no build, and its blind spot is that a folded subscript base looks exactly like an address |
| a gap nothing references, so there is no displacement to read -- how big is it? | BISECT ON THE SHIFT. Declare a size, rebuild, and read `dsmap`'s shift for the blocks ABOVE it: the shift is a continuous function of the size, so two builds bracket it and a third lands it. On one part 128 gave +30 and 98 gave 0. Cheaper than any amount of reading, and it works precisely where the gap-and-stride methods cannot |
| how much uninitialised data are we short overall? | the MZ header's `minalloc` field, in paragraphs, on both binaries -- it is the loader's BSS request, so the difference is the exact shortfall and it moves by precisely what you add. A cheap feedback loop that needs no disassembly, and `SS` moves with it as a second reading |
| did the frame I just fixed come out right, when `prologue.py` says `not located`? | `pascal/framehist.py` -- it compares the MULTISET of `ENTER` operands and needs no pairing, so it still answers when bodies differ too much to pair. A missing row is a declaration list too small, a surplus one too big, and equal-and-opposite rows are usually ONE routine rather than two defects |
| where is the runtime, and what is in it? | `pascal/rtl.py match`, then `rtl.py find` |
| what does this code actually DO? | `substrate/disasm.py FILE SEG:A..B` -- a linear decode, addressed the way the code is written down |
| this code is undecodable INT 34h noise | `pascal/x87.py disasm` -- resolves the traps IN MEMORY and marks every line it resolved, so no patched copy is left on disk to be mistaken for the original later. `survey` first on a new target; `fix` only when a file on disk is genuinely wanted, and `disasm --sites` is what feeds it |
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
| **and where is the defect that opened the span?** | `pascal/spanwhy.py` -- the walk forgives short differences, so a span OPENS downstream of the instruction whose length changed; this traces back to it, and on one part twelve spans came from three causes |
| **is a global where the original put it?** | `pascal/dsmap.py` -- pairs every absolute data reference with ours and reports the SHIFT; a run of one non-zero shift means the declaration before it is the wrong size, and the boundary names the unit |
| **which unit has the wrong $N?** | `pascal/fpusites.py` -- under $E+ an 80x87 instruction ships as INT $34..$3E, and $N- emits none at all, so a trap COUNT lower than the original's names a unit compiled $N- that should be $N+; the original's per-segment column says which |
| **is the initialised data identical?** | `pascal/dgimage.py` -- compares the two DGROUP images byte for byte. The other two instruments are blind to the same thing: the coverage walk reads CODE, and dsmap pairs REFERENCES, so data nothing references is invisible to both -- which is exactly what tends to go missing |
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
| does a claimed compiler difference survive a measurement? | `pascal/codegen.py` -- one probe, every compiler |
| do the probes still compile, and still yield a measurement? | `pascal/probecheck.py` -- a probe is cited like a binary and nothing else re-runs it |
| is the transcription rule met? | `pascal/asmaudit.py` |
| is the wiki valid? | `wikitools/okfcheck.py`, `wikitools/kbprofile.py`, `wikitools/glossary.py` |
| does any tool leave an encoding to the locale? | `encaudit.py` |
| a document's line breaks got multiplied | `repairdoc.py` |
| install the kit into a new project | `wizard.py` -- see `SETUP.md` |

### The two that are not instruments

`substrate/disasm.py` is an engine with a CLI attached: one linear decode with the awkward parts handled -- the MZ header's own paragraph count, `SEG:OFF` addressing, and a byte that decodes to nothing reported rather than ending the walk, because capstone's own iterator STOPS there and a stop looks like the end of the range. It knows nothing about any compiler; `pascal/x87.py disasm` is the caller that knows what a Borland trap is. **A linear decode is a guess about where instructions start**, so begin at an address something had a reason to believe in, and read a run of nonsense as data rather than as an instruction mix.

`substrate/align.py` is the ENGINE, not a tool: one comparison in three shapes -- how far agreement reaches, how many bytes of two blocks differ, and every place they disagree -- with four allowed-difference rules and two location strategies, all passed in because both belong to the artefact rather than to the comparison. Nothing runs it directly; seven instruments above are callers. `substrate/omf.py` is a reader in the same sense: it says which bytes of an `.OBJ`'s code are fixups, and `objcheck.py` is what asks. `pascal/register.py` is the register's one serializer, so no tool can drop another's section, and `project.py` is the only reader of the answers files.

`pascal/build.py` MAKES the thing the others measure rather than measuring anything. Note the word: a **harness** in this vocabulary is a small program that runs one piece of the subject so a person can watch it, so the thing that builds those is not one.

`tools/README.md` says which tier each belongs to and why.
