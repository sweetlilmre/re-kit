# The toolkit

Reusable programs with no project facts in them. Three folders, decided in [Draw the tooling package boundary](https://github.com/sweetlilmre/PsychoNeurosis/issues/9).

| folder | what it holds | tier |
|---|---|---|
| `substrate/` | Reading DOS and 16-bit binaries: MZ headers, LZEXE, segments, relocation tables. Should work against a C or assembler target too. | substrate |
| `pascal/` | Facts true only of Borland Pascal: `.TPU` structure, DGROUP layout, RTL byte patterns. | pascal |
| `wikitools/` | Looking after the wiki itself: OKF conformance, our stricter profile, and the generators. | neither |

The migration that filled these folders is finished. **Forty-seven programs, and the originals they came from are archived** under each consumer's `archive/pre-kit-scripts` tag; the record of where each one went, and the measurement that made deleting it safe, is one generated document in the host repository -- `docs/32-tool-disposition.md` here. Ten scripts stayed behind deliberately -- a project's own data carvers, its harness generator, a reference-path helper -- and each says why in the same table.

**Every move was verified against the original before the original went.** Mostly that meant identical output; where a tool produced a file it meant a byte-identical file; where it produced a build it meant all 35 executables byte-identical. Five of the moves changed their answer, and every one of those was a repair -- see `WORKING.md` section 8 on what to distrust, which is where they are recorded.

| folder | what it holds |
|---|---|
| `substrate/` (11) | `align` the comparison engine; `fingerprint`, `mzinfo`, `split`, `unlzexe` for getting into a file; `segmap`, `symbols`, `tddump`, `strings` for reading one; `omf` for an object module; `modex` for unchained VGA |
| `pascal/` (29) | the instruments that measure a rebuild -- `routines`, `units`, `objcheck`, `blockcmp`, `linkcmp`, `mapcmp`, `linkorder`, `dgroup`, `spans`, `coverage`, `artefact`; the ones that read a binary before you write any Pascal -- `survey`, `rtl`, `x87`, `emit`; `build` which makes what the rest measure; the register's own -- `plan`, `ratchet`, `observe`, `markers`, `marker`, `register`, `staged`; and the source checks `paslint`, `asmaudit`, `undeclared`, `shared_asm`, `codegen` |
| `wikitools/` (3) | `okfcheck` for conformance and nothing more, `kbprofile` for our profile and the generators, `glossary` for the avoid-lists |
| beside them (4) | `project` reads the answers and is the only thing that does; `wizard` installs the kit; `encaudit` and `repairdoc` are facts about the tools a session is driven WITH, which every project inherits on day one |

`WORKING.md` section 3 groups all of them by the question you actually have, which is the useful way in. This table is the inventory.

**Every copy carries the finding that produced it in its docstring**, and several carry a correction to what was believed before -- `align.py` names the two location strategies that failed, `rtl.py` names the assumption about smart-linked offsets that does not hold, `x87.py` says out loud that a trap-rewritten file is a disassembly aid and not a variant of the original. The wiki carries the general form: `verifier-blind-to-absence` for the coverage walk, `one-routine-two-units` for shared assembler, `plausible-and-wrong` for the compare rules.

**A NEW generic tool is born here; only a tool that already existed is copied.** Copy-and-adjust exists to keep working originals working, and a tool written today has no original to protect. Writing one in `tools/` and copying it the same day duplicates it from birth -- which happened once, on 23 Aug 2026, and put two rows in the retirement census for one tool before it was collapsed. The project-specific half of such a tool is DATA passed in, not a second script: `shared_asm.py` takes the psycho repository's exemptions from `src/asm/shared-exempt.txt`.

## Two rules that shaped this

**One compare tool, not four.** Four scripts across the two repos compare bytes and differ *only* in which differences they accept -- a zero for a `.TPU`'s pending fixup, whatever an `.OBJ` records as a relocation, an isolated one- or two-byte run, an address inside a known DGROUP window. So the **allowed-difference rule is passed in, never built in.** Baking it in hides how strict a measurement was; passing it in makes that readable at the call site.

**"Needs no disassembler" is a note on a tool, not a folder.** Eight tools qualify and they are the cheap, portable half -- but they span both tiers, so filing them together by what they *don't* need would split things that belong side by side.

## Running it

    uv venv .venv
    uv pip install --python .venv/Scripts/python.exe pyyaml

**`pyyaml` is the whole dependency, and the kit is NOT installed as a package.** Every tool puts its own directory on `sys.path` and is run by its path, which is what lets a freshly cloned project run one before it has installed anything -- issue #39's deliberate choice, and the reason there are no console entry points either.

`pyproject.toml` beside this file stays, and it is a DECLARATION rather than an instruction: it is where the dependency and the three package folders are written down, and a future consumer that wants `from substrate import align` in a script of its own has what it needs to install it. Nothing does that today, in either consumer.

**So the install is not documented as a step, because nothing tested it and it broke for a day without one check going red** (psycho #49). Measured on 23 Aug 2026: the entire check list runs to identical numbers in a virtual environment holding `pyyaml` and nothing else. If the install becomes load-bearing, it needs a check on the same day, not afterwards.

Then, from the repo root:

    .venv/Scripts/python.exe kit/tools/wikitools/okfcheck.py kit/wiki
    .venv/Scripts/python.exe kit/tools/wikitools/kbprofile.py kit/wiki
    .venv/Scripts/python.exe kit/tools/wikitools/kbprofile.py kit/wiki --write

`okfcheck.py` checks only what the OKF spec requires. `kbprofile.py` checks our house rules and regenerates the parts of the wiki that are generated. Keeping them apart is deliberate: if `okfcheck.py` ever rejects a document only our template dislikes, we have quietly redefined a portable format as ours.

**A note about `okfcheck.py`, so nobody "fixes" it.** It contains no project facts at all. It implements the published OKF spec and nothing else, so anyone using OKF could run it unchanged. Do not wire it into this repo's layout.
