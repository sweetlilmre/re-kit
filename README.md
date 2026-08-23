# The kit

**This folder is the portable half of a reverse-engineering effort.** Bring it
into a project, and it brings the method with it.

    kit/
      tools/    the reusable programs -- no project facts in any of them
      wiki/     the field manual, which grows every time a binary is read

**Everything outside this folder is the record**: where THIS project has got
to. `status.toml`, `docs/`, `src/`, the target's own binaries and notes. The
record does not travel; a new target gets its own.

The line between them is a path test, which is the reason this folder exists:
if a file under `kit/` names a target's binary, a segment address or a machine
path, it is in the wrong place. Project facts reach the kit by being **passed
in** -- as an argument, or out of the project's answers file.

## Why one folder rather than two

Every way of sharing the kit with another project operates on ONE path: a git
submodule mounts one directory, a subtree grafts one prefix, a path install
points at one project. Two sibling folders would mean doing it twice, and the
moment that happens they can drift -- a project running the tools from one
version of the kit and the wiki from another, with nothing able to detect it.

It is also a cheap step towards the kit having its own repository, and
forecloses nothing: a submodule mounts at a path, so this path stays the same
if that happens.

## Reading order

`tools/README.md` says what each program is for and which tier it belongs to.
`wiki/index.md` lists what has been learnt about reading these binaries, and
`wiki/CONTEXT.md` holds the METHOD's vocabulary and travels with this folder; a host repository's own `CONTEXT.md` keeps only the words for its target. Read both before arguing about any of them.

## Where the scripts this replaced went

A consumer's own scripts are **archived**, not lost. Each project that adopts the kit tags its tree before the deletions begin, with an annotated tag called `archive/pre-kit-scripts` on the last commit that held every script:

    git show archive/pre-kit-scripts:<path>          recover one
    git log --oneline archive/pre-kit-scripts -1     what it points at

A tag is a permanent named pointer that cannot drift, and it can point at any commit -- so there is no reason to carry superseded scripts through a whole migration. `census.py`'s `archived` state records where each one went, and names its successor. `WORKING.md` section 7 has the convention in full, including the check that has to pass before anything is deleted.

Decided in [The kit travels as one folder](https://github.com/sweetlilmre/PsychoNeurosis/issues/43)
and [Tag the archive, then delete what the toolkit superseded](https://github.com/sweetlilmre/PsychoNeurosis/issues/36),
on the map [The toolkit and wiki become the RE drivers](https://github.com/sweetlilmre/PsychoNeurosis/issues/29).
