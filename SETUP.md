# Installing the kit into a project

Two things happen here, and only one of them is mechanical.

    kit/tools/wizard.py       proposes, and says what its evidence is
    you                       decide, because the evidence runs out

`wizard.py` never writes without confirmation and never decides. It surfaces
candidates ranked by the KIND of evidence behind them, asks about what no
directory listing can imply, and reports the keys it cannot answer at all rather
than leaving them silent.

## Do this

    python kit/tools/wizard.py           propose; writes nothing
    python kit/tools/wizard.py --check   propose, and diff against the kit.toml already here
    python kit/tools/wizard.py --write   write, confirming each value

Then paste the stanza into the project's agent file -- `CLAUDE.md` or
`AGENTS.md` -- **appending, never rewriting**. An agent file is usually a router
for a project with its own history in it, and flattening one to install a tool
is not a trade worth making.

## What it means by evidence, strongest first

| evidence | what it is |
|---|---|
| **named as a role by a script** | a variable in this project's own code says what the path is FOR: `SRC = ROOT / 'v1.31b' / 'src'`. Nothing beats this, because the variable's NAME is the project stating the role -- the one thing a listing never tells you. |
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
`wizard.py` can find that `refpath.py` mentions `ref/vt1.31b.bin`; only reading it
tells you that this is the measurement target and that `MAKESTR.EXE` beside it is
a build artefact.

So: run `--check` first if there is a `kit.toml` already, read the project's
scripts for anything the report calls weak or tied, propose your reading with the
evidence, and let the person decide. **Do not answer a question the report asked
-- those are the ones nobody can answer from the tree, including you.**

## The test that matters

`--check` on a project whose right answers are already known. Both existing
consumers pass it: one agrees on 8 of 8 proposed keys with 3 correctly asked, the
other on 5 of 5 with one key it recommends the project add -- a key that project
genuinely needed, because a check there was failing for want of it.

**Adopting a project you cannot check is how a wizard is confidently wrong in
private.**
