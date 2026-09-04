# The toolkit

Reusable programs with no project facts in them, in three folders. The boundary they draw was decided deliberately and is a path test: a file here that names a target's binary, a segment address or a machine path is in the wrong place.

| folder | what it holds | tier |
|---|---|---|
| `substrate/` | Reading DOS and 16-bit binaries: MZ headers, LZEXE, segments, relocation tables. Should work against a C or assembler target too. | substrate |
| `pascal/` | Facts true only of Borland Pascal: `.TPU` structure, DGROUP layout, RTL byte patterns. | pascal |
| `wikitools/` | Looking after the wiki itself: OKF conformance, our stricter profile, and the generators. | neither |

The migration that filled these folders is finished, and **the originals the tools came from are archived** under each consumer's `archive/pre-kit-scripts` tag; the record of where each one went, and the measurement that made deleting it safe, is one generated document in the host repository -- `docs/32-tool-disposition.md` here. Ten scripts stayed behind deliberately -- a project's own data carvers, its harness generator, a reference-path helper -- and each says why in the same table.

**Every move was verified against the original before the original went.** Mostly that meant identical output; where a tool produced a file it meant a byte-identical file; where it produced a build it meant all 35 executables byte-identical. Five of the moves changed their answer, and every one of those was a repair -- see `WORKING.md` section 8 on what to distrust, which is where they are recorded.

<!-- generated:inventory -->

**78 programs.** This table is generated from each tool's own first docstring line by `toolindex.py`; `WORKING.md` groups them by the question you have, which is the useful way in.

### `substrate/` -- 13

Reading DOS and 16-bit binaries. Should work against a C or assembler target too.

| tool | what it says it does |
|---|---|
| `align` | Which bytes of an original do NOT line up against a rebuild of it. |
| `disasm` | Decode a range of a 16-bit real-mode image, addressed the way its code is. |
| `fingerprint` | Identify a binary's appended payload and the toolchain that built it. |
| `lzpack` | Pack an MZ executable the way LZEXE 0.91 did, and compare against the original. |
| `modex` | De-interleave four Mode-X planes into one linear image. |
| `mzinfo` | Parse a DOS MZ header, and say whether the file is bigger than its image. |
| `omf` | Read an Intel OMF .OBJ and report which bytes of its code are FIXUPS. |
| `segmap` | Derive the real-mode segment layout of a 16-bit MZ image from its fixups. |
| `split` | Split each demo part into a clean MZ image plus its appended payload. |
| `strings` | Dump printable strings, optionally restricted to the EXE load image. |
| `symbols` | Extract Borland Pascal symbolic debug info (magic 0x52FB) name pools. |
| `tddump` | Dump Borland Turbo Debugger debug info appended to a DOS MZ executable. |
| `unlzexe` | Unpack an LZEXE 0.91 ('LZ91') compressed MZ executable. |

### `pascal/` -- 55

True only of Borland Pascal: `.TPU` structure, DGROUP layout, RTL byte patterns.

| tool | what it says it does |
|---|---|
| `artefact` | The artefact-tier instrument: is our whole build the original's bytes? |
| `asmaudit` | Report where the assembler-transcription rule is not yet met. |
| `asmgen` | Assemble one module with every installed assembler and report its segment. |
| `blockcmp` | Verify a segment BLOCK BY BLOCK, which is the only honest measure of a |
| `braces` | Comment nesting and the directive set: the two things a comment edit breaks. |
| `build` | Stage Pascal sources under 8.3 names, drive a real Turbo Pascal under |
| `clean` | Copy a reconstruction's source and strip the reverse-engineering apparatus. |
| `cleanconf` | Write a build config for the STRIPPED source tree, from the real one. |
| `codegen` | Compile one probe unit with every installed compiler and diff the code. |
| `coverage` | How much of a target is accounted for, computed from the tree rather than recited. |
| `dgimage` | Compare the two builds' INITIALISED data byte for byte, and say where they part. |
| `dgroup` | Compare our INITIALISED DGROUP image against the original's, block by block. |
| `dsgaps` | Sort the `DS:$XXXX` addresses a reconstruction's comments record, and print |
| `dsmap` | Pair the original's absolute data references with ours, and report the shift. |
| `dspair` | Pair every displacement operand by INSTRUCTION POSITION, not by content. |
| `dsverify` | Check the `DS:$xxxx` addresses written in comments against the declarations. |
| `emit` | Emit compiled-in data back out as Borland Pascal typed constants. |
| `fpusites` | Count a part's floating-point sites on both sides, and name the units that differ. |
| `framehist` | Compare the MULTISET of stack-frame sizes in two builds. |
| `handasm` | Which routines in a segment are HAND-WRITTEN ASSEMBLER rather than compiled. |
| `harvest` | Comments in a sibling's source that carry knowledge, with the code they annotate. |
| `linkbytes` | Every byte of the LINKED image that differs, by unit, with context. |
| `linkcmp` | Compare every linked code segment against the original's, and read the |
| `linkorder` | Predict our link order from the `uses` graph, and diff it against the original's. |
| `magic` | Raw numbers in the reconstruction that a sibling's source gives a NAME. |
| `mapcmp` | Compare build/VTMAIN.MAP's segment lengths against the original's, ON THE SAME FOOTING. |
| `marker` | One reader for the routine markers in a Pascal tree. |
| `markers` | Read every routine marker in a Pascal tree, and account for all of them. |
| `objcheck` | Measure a `{$L}` object module STRICTLY, against the object's own relocations. |
| `observe` | Record what a person saw when they ran a harness, so it stops being prose. |
| `paslint` | Catch the Pascal defects that cost the most time to diagnose from a compiler |
| `plan` | The plan: what to fix, in what order, and where that is written down. |
| `probecheck` | Every probe still compiles, and still yields a measurement. |
| `progseg` | The main program is a table of every unit's entry-point offsets. Compare it. |
| `prologue` | Read a routine's prologue: what the source declared, and which switch built it. |
| `ratchet` | The ratchet: a lock that rises by itself and will not fall quietly. |
| `register` | The status register's one serializer, so no tool can drop another's section. |
| `routines` | Byte-diff every declared assembler routine against the original binary. |
| `rtl` | The Borland runtime, and where its routines and yours actually start. |
| `segdoc` | The segment table of a map document, computed from the layout config. |
| `segpair` | Pair OUR segments to the ORIGINAL's by content, and report the ORDER. |
| `shared_asm` | Assembler that appears in more than one unit should be ONE TEXT. |
| `sitedump` | Disassemble one address in both images, side by side, on a VERIFIED anchor. |
| `source` | Source text, reduced to the code -- the one thing three tools need in common. |
| `spanclass` | Classify every remaining span WITHOUT needing to align our image. |
| `spans` | Which bytes of an original do NOT line up against our build, and where. |
| `spanwhy` | Which unaligned spans can editing close, and which are addresses that moved. |
| `staged` | Is a build output still the source it was built from? |
| `survey` | The four cheap measurements on one segment, in one command. |
| `tagcheck` | Comments that carry reverse-engineering apparatus without saying so. |
| `undeclared` | List identifiers each reconstruction unit uses but never declares. |
| `unitorder` | Does our build link its units in the ORIGINAL's order? The walk cannot tell. |
| `units` | Compare each compiled unit's code against the original segment it rebuilds. |
| `verdiff` | What CHANGED between the same segment in two builds of one program. |
| `x87` | The x87 emulator traps: survey them, rewrite them, and read what they load. |

### `wikitools/` -- 3

Looking after the wiki bundle: conformance, our profile, and the generators.

| tool | what it says it does |
|---|---|
| `glossary` | Turn the glossary's `_Avoid_` lists into a check, because writing a term |
| `kbprofile` | Our stricter profile on top of OKF, plus the generators that stop drift. |
| `okfcheck` | OKF v0.1 conformance check -- and NOTHING more than conformance. |

### `beside them` -- 7

About the kit or the session rather than about any target.

| tool | what it says it does |
|---|---|
| `checklist` | Run the universal check list, reading each status off the TOOL. |
| `encaudit` | Find text I/O that relies on the locale encoding instead of stating one. |
| `eolcheck` | Every file a DOS tool reads must be CRLF. Nothing was checking. |
| `project` | The project's answers to the kit's questions. |
| `repairdoc` | Repair a markdown document whose line breaks have been multiplied. |
| `toolindex` | The toolkit's inventory, generated from the tools rather than typed beside them. |
| `wizard` | Install the kit into a project: propose, confirm, write. |

<!-- /generated:inventory -->

`INSTRUMENTS.md` groups the ones a session reaches for by the question you actually have, which is the useful way in. **It is a selection and not a census** -- it named 55 of 73 when this was written, which is the right shape for a routing table and the wrong shape for an inventory. The table above is the inventory, and it is generated: run `toolindex.py --write` after adding a tool, and `--check` fails if it was not.

**Every copy carries the finding that produced it in its docstring**, and several carry a correction to what was believed before -- `align.py` names its two location strategies and the candidate positions that failed under them, `rtl.py` names the assumption about smart-linked offsets that does not hold, `x87.py` says out loud that a trap-rewritten file is a disassembly aid and not a variant of the original. The wiki carries the general form: `verifier-blind-to-absence` for the coverage walk, `one-routine-two-units` for shared assembler, `plausible-and-wrong` for the compare rules.

**A NEW generic tool is born here; only a tool that already existed is copied.** Copy-and-adjust exists to keep working originals working, and a tool written today has no original to protect. Writing one in `tools/` and copying it the same day duplicates it from birth -- which happened once, on 23 Aug 2026, and put two rows in the retirement census for one tool before it was collapsed. The project-specific half of such a tool is DATA passed in, not a second script: `shared_asm.py` takes its exemptions from a file the host repository names, not from a list inside the tool.

## Two rules that shaped this

**One compare tool, not four.** Four scripts across the two repos compare bytes and differ *only* in which differences they accept -- a zero for a `.TPU`'s pending fixup, whatever an `.OBJ` records as a relocation, an isolated one- or two-byte run, an address inside a known DGROUP window. So the **allowed-difference rule is passed in, never built in.** Baking it in hides how strict a measurement was; passing it in makes that readable at the call site.

**"Needs no disassembler" is a note on a tool, not a folder.** Eight tools qualify and they are the cheap, portable half -- but they span both tiers, so filing them together by what they *don't* need would split things that belong side by side.

## Running it

    uv venv .venv
    uv pip install --python .venv/Scripts/python.exe pyyaml

**`pyyaml` is the whole dependency, and the kit is NOT installed as a package.** Every tool puts its own directory on `sys.path` and is run by its path, which is what lets a freshly cloned project run one before it has installed anything -- a deliberate choice, and the reason there are no console entry points either: an entry point would put an install where there is currently no step, which is a real cost for a kit whose whole point is being dropped into a project and used.

`pyproject.toml` beside this file stays, and it is a DECLARATION rather than an instruction: it is where the dependency and the three package folders are written down, and a future consumer that wants `from substrate import align` in a script of its own has what it needs to install it. Nothing does that today, in either consumer.

**So the install is not documented as a step, because nothing tested it and it broke for a day without one check going red.** The rule that came out of it is worth more than the incident: **a capability documented as working and exercised by nothing is worse than one not offered at all.** That break cost an adopter their first ten minutes, and every check was green throughout. Measured on 23 Aug 2026: the entire check list runs to identical numbers in a virtual environment holding `pyyaml` and nothing else. If the install becomes load-bearing, it needs a check on the same day, not afterwards.

Then, from the repo root:

    .venv/Scripts/python.exe kit/tools/wikitools/okfcheck.py kit/wiki
    .venv/Scripts/python.exe kit/tools/wikitools/kbprofile.py kit/wiki
    .venv/Scripts/python.exe kit/tools/wikitools/kbprofile.py kit/wiki --write

`okfcheck.py` checks only what the OKF spec requires. `kbprofile.py` checks our house rules and regenerates the parts of the wiki that are generated. Keeping them apart is deliberate: if `okfcheck.py` ever rejects a document only our template dislikes, we have quietly redefined a portable format as ours.

**A note about `okfcheck.py`, so nobody "fixes" it.** It contains no project facts at all. It implements the published OKF spec and nothing else, so anyone using OKF could run it unchanged. Do not wire it into this repo's layout.
