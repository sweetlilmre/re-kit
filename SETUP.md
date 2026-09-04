# Installing the kit into a project

Two things happen here, and only one of them is mechanical.

    kit/tools/wizard.py       proposes, and says what its evidence is
    you                       decide, because the evidence runs out

`wizard.py` never writes anything and never decides. It surfaces
candidates ranked by the KIND of evidence behind them, asks about what no
directory listing can imply, and reports the keys it cannot answer at all rather
than leaving them silent.

## Do this

    python kit/tools/wizard.py           propose, and ask what it cannot see
    python kit/tools/wizard.py --check   propose, and DIFF against the kit.toml already here

**There is no `--write`, and this file claimed one for as long as it existed.**
`kit.toml` is written BY HAND from what the program prints. The documented
command proposed, exited 0 and left no file -- which reads exactly like a wizard
that ran, so nothing about running it said otherwise. `wizard.py`'s own
docstring had already retracted the claim; this copy of it had not.

That is also the consistent arrangement rather than a missing feature: a
program whose whole stance is that it does not decide has no business writing
the answers.

Then paste the stanza into the project's agent file -- `CLAUDE.md` or
`AGENTS.md` -- **appending, never rewriting**. An agent file is usually a router
for a project with its own history in it, and flattening one to install a tool
is not a trade worth making.

## What it means by evidence, strongest first

| evidence | what it is |
|---|---|
| **named as a role by a script** | a variable in this project's own code says what the path is FOR: `SRC = ROOT / 'src'`. Nothing beats this, because the variable's NAME is the project stating the role -- the one thing a listing never tells you. |
| **named by a script** | some program here mentions this path. Good, but a mention is not a role: two directories were each named by three scripts and only one of them was the sources. |
| **conventional name** | `status.toml`, `build/`, `kit/wiki` -- names the kit itself defined, so finding one is not a guess. |
| **shape only** | a directory that merely holds the right sort of file. Reported as weak, and **turned into a question** rather than proposed. |

**There is no file count anywhere in this.** An earlier version ranked by it and
proposed a target's RELEASE sources over the reconstruction's -- because a
release is complete and a reconstruction by definition is not, so counting files
favours the wrong answer, and favours it more strongly the more work is left to
do. That is the single sharpest thing this program knows.

## What you have to decide, every time

- **which sources you are WRITING**, as against reading for reference. Where two
  candidates tie on evidence, it asks, and says which tied -- because whichever
  won a tie won it by accident.
- **the paragraph your disassembly calls the start of the load image.** Never
  guessable.
- **which variant to measure against.** Where numbered originals have variants
  alongside them, it says so and refuses to choose: one of them may be a
  disassembly aid somebody made rather than a release, and measuring against the
  wrong one silently changes every result afterwards.
- **which built files are yours.** A build directory holding more than one
  family of executable gets a question with no default, because a glob that
  matches copies of the originals makes a compare tool measure an original
  against itself **and pass**.

## If you are an agent doing this

The mechanical half is above. Your half is reading this project's own programs
and understanding what they mean -- which is why this is not a shell script.
`wizard.py` can find that one of this project's scripts mentions a file under
`ref/`; only reading it tells you that the file is the measurement target, and
that an `.EXE` sitting beside it is a build artefact rather than a second one.

So: run `--check` first if there is a `kit.toml` already, read the project's
scripts for anything the report calls weak or tied, propose your reading with the
evidence, and let the person decide. **Do not answer a question the report asked
-- those are the ones nobody can answer from the tree, including you.**

## The test that matters

`--check` on a project whose right answers are already known. Measured on 3 Sep
2026, across three consumers:

    the multi-part target       6 of 6    0 disagreements
    the one-target consumer     6 of 6    0 disagreements
    its later version           6 of 6    0 disagreements

**What the denominator is, because it moves.** It counts only keys the wizard
actually proposes a value for. Two categories are deliberately outside it: a key
it ASKS about, because the answer is not in the tree, and a key the project sets
that this wizard has no proposal for at all. Neither is a judgement, so scoring
either would grade the tool on a question it never answered.

That second exclusion was missing until 3 Sep 2026, and it is why this section
used to claim **8 of 8** and **5 of 5**. Nothing regressed: the projects grew
keys the wizard proposes nothing for -- five of which it names in its own
`wanted by` list -- and each new one was counted as a failure. The figure read
6 of 13 by the time anybody looked.

**Those figures were 6/6, 4/6 and 3/6 an hour earlier**, and the five
disagreements were real: the wizard proposed a probe directory and a build
directory as the SOURCE root, and a derived `clean-src` copy for a file that
lives in `src`. It could not tell a source tree from a staged copy of one --
and it cannot be told by counting, since one consumer has the same 29 `.PAS`
in both. They are fixed; what matters here is that they were invisible until
the false misses stopped sitting beside them.

**Adopting a project you cannot check is how a wizard is confidently wrong in
private.**

## What comes after the wizard

`kit.toml` answers where things ARE. It does not describe the target's LAYOUT,
and most instruments need that too -- so a project with a perfect `kit.toml` can
still run almost nothing. This section is the order the files are needed in, and
it was measured by scaffolding a new target and running the tools until each one
stopped.

| # | file | needed before | who reads it |
|---|---|---|---|
| 1 | `kit.toml` | anything | everything |
| 2 | the **register** (`status.toml` by convention) | any check | `plan`, `observe`, `artefact`, `ratchet`, `routines` |
| 3 | the **layout config** | any link instrument | `mapcmp`, `linkorder`, `linkbytes`, `dgroup`, `coverage`, `segdoc` |
| 4 | the **units config** | per-unit measurement | `units`, `coverage` |
| 5 | a **blocks** or **objmodules** config | measuring a program segment or a `{$L}` module | `blockcmp`, `objcheck` |

**The register is created, not written by hand**: `ratchet.py <register> --write`
writes an empty one. Until it exists the reporting instruments refuse, which is
deliberate -- they used to answer *no observations recorded, stated rather than
implied* for a file that was not there, so a new target passed every check on its
first day and nothing said why.

### The layout config

One table per part, because a target may have one program or nine, and the six
instruments above read the same shape either way. **A one-target project is not
a special case with its own keys; it is a table with one row.**

    # Project-wide, above the parts.
    layout   = "docs/00-map.md"   # the segment/size document `coverage` measures
                                  # against; `segdoc.py` generates one
    [lists]
    rtl   = ["System", "Crt"]     # the runtime's units -- not yours to transcribe
    noseg = []                    # units that emit no code segment
    [unitname]                    # source name -> linker-map name, where they
                                  # differ; empty when nothing is abbreviated

    [part."000"]
    map        = "build/MAIN.MAP" # this part's linker map
    main_unit  = "MAIN"           # the unit its dependency walk starts from
    program_seg = 0x1000          # the segment its PROGRAM compiles into
    end_at     = 0x1caa           # the bound that closes the last segment below
    dgroup_at  = 0x1caa           # where DGROUP starts
    # Optional, both read only by `coverage`:
    program_blocks = "blocks/1000.toml"   # the program emits no unit, so it
                                          # is measured block by block
    data = [ { segment = 0x1caa, why = "constants only, no code" } ]
    segments = [
      { segment = 0x1000, name = "MAIN" },
      { segment = 0x106e, name = "GFX"  },
    ]

**`segments` is ascending and complete**, because each segment's extent is the
NEXT entry's base. That is why there is no length column: a length table beside
an address table is two copies of one measurement, and they drift.

**`end_at` and `dgroup_at` are two facts, not one.** `end_at` closes the segment
walk; `dgroup_at` is where the data group begins. They are equal only when the
segment list happens to include the runtime. One consumer lists its RTL segments
and one deliberately excludes them, and an instrument reading one for the other
measured every part short by the size of its runtime -- to the byte.

**`program_seg` is named, never taken as `segments[0]`.** Position means "the
program" only by coincidence of link order, and a target that measures its
program separately leaves it out of the list entirely.

Fill it from the linker map once you can build: the map's segment table gives
every address and name, its first CODE segment is `main_unit`, and its `DATA`
line gives `dgroup_at`.

### The units config

One row per compiled unit and the segment it must rebuild. Read by `units.py`,
and by `coverage.py`, which shells out to it.

    sources  = "src"              # so a STALE build is refused rather than measured
    rewrites = ["tp6_far"]       # source rewrites applied before the staleness test

    [unit.GFX]
    segment = 0x106E
    length  = 380                 # the ORIGINAL's code length -- the segment's
                                  # extent LESS the linker's zero padding, so a
                                  # unit may compile shorter and only the
                                  # overlap is compared

    [unit.SOUNDDEV]
    segment = 0x1BFF
    length  = 4291
    object  = "SOUNDDEV.OBJ"     # links a {$L} module -- see below
    # file  = "SOUNDDEV.TPU"     # optional; defaults to <NAME>.TPU

**`object` is not optional decoration.** A unit that links an assembled module
cannot be measured by the zero rule at all -- TASM leaves an ADDEND where the
compiler leaves a zero, so the assembler half reads as a wall of differences.
Undeclared, two such units reported 89% and 49% in a target whose whole load
image was byte-identical. Declaring it builds the forgiveness mask from the
object file's real relocation table, and hands the strict check to `objcheck`.

**An absent row is not a pass.** A unit with no row here is not measured and
nothing says so.

### The objmodules config

Where each `{$L}` module lands inside its unit's segment. Read by `objcheck.py`,
which is the STRICTER half of the pair above -- it reads the relocations out of
the object file rather than forgiving a class of byte.

    sources  = "src"
    rewrites = ["tp6_far"]

    [module.SOUNDDEV]
    segment = 0x1BFF
    length  = 4304                # the segment's EXTENT here, NOT the trimmed
                                  # code length units.toml carries
    from    = 0x0746              # where the module starts inside the segment
    to      = 0x10C4              # first byte past it; the tail beyond is linker
                                  # padding and is checked to be zero
    # unit   = "SOUNDDEV.TPU"    # optional; defaults to <NAME>.TPU
    # object = "SOUNDDEV.OBJ"    # optional; defaults to <NAME>.OBJ

**`length` is the extent, not the trimmed length.** `objcheck` reads `to` to the
end as padding, so a trimmed length puts `to` past the end and it indexes off the
segment.

**`from` and `to` are derivable, not guesswork.** Locate the module by its opening
24 bytes -- which are code, not a fixup -- inside your own `.TPU`, then subtract
where that unit's code starts in the same file. Searching the ORIGINAL image
instead may fail: the image has its relocations applied while the `.TPU` still
carries the addends.

### A blocks config

For a segment no `.TPU` describes -- typically the PROGRAM, which compiles into
the .EXE and so emits no unit. Read by `blockcmp.py`, and named from the layout
config's `program_blocks`.

    segment = 0x1000              # the segment being measured
    length  = 1745                # its whole extent
    unit    = "VTMAIN.EXE"        # the LINKED image, not a .TPU
    strip_header = true           # so the segment starts at the load image's start
    at      = 0x0000              # its position, known rather than searched
    window  = 200                 # how far to search when `at` is absent

    rule    = "linked"            # `linked` or `pending`
    varbase = 0x0C70              # DGROUP offsets at or above this may differ
    # segment_delta = -7          # forgive a segment word this many paragraphs
                                  # off; OMIT to forgive none

    [[block]]
    name = "the leading constants"
    from = 0x0000
    to   = 0x00F8

**Blocks can be derived from your own linker map** -- the leading constants, then
one per public symbol in the segment, the last running to the end. Every boundary
is then a symbol your build emitted rather than an address read by eye.

**Set the rule to forgive nothing until something needs forgiving.** `varbase` at
the top of the segment and no `segment_delta` means no byte is excused. Copying
another target's numbers puts values in your config that nothing in your target
measured; if a difference appears you want it REPORTED, and you can set a real
boundary then.

### The RTL config

Names the runtime's routines in every binary from one reference. Read by
`rtl.py find`; the other two subcommands take arguments instead of a config.

    reference     = "003"         # the part whose bodies become the patterns
    out           = "work/sites/rtlnames.json"
    anchor_prefix = 10            # bytes of an anchor's prefix to check

    [base]                        # where the runtime starts in EACH part -- the
    "000" = 0x1213                # same paragraph the layout config calls
    "001" = 0x1543                # `end_at` when the RTL is excluded

    [known]                       # offset -> name, CONFIRMED, in the reference
    "0000" = "RTL_SystemInit"
    "0116" = "RTL_Halt"

    [anchor]                      # optional: offsets whose body is matched by
    "0000" = "RTL_SystemInit"      # PREFIX rather than in full, for a routine
                                  # whose tail differs between parts

**`[known]` is evidence, not a guess**: a pattern matching more than once is not
reported, so a name here means one body matched in one place.
