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

**[`WORKING.md`](WORKING.md) first, and it is the only one of these you read at the start of a session.** It is the method: where things are, what to work on, the loop, the checks, the standing rules, and the environment traps. Sections 1, 2, 2a and 4 are about a page.

The rest are reached when you have a question:

| when you want | read |
|---|---|
| the instrument that answers one question | [`INSTRUMENTS.md`](INSTRUMENTS.md) -- a lookup table, not reading |
| what a given program is and what it claims to do | [`tools/README.md`](tools/README.md) -- generated from the tools themselves |
| what has been learnt about reading these binaries | [`wiki/index.md`](wiki/index.md) |
| what a word means | [`wiki/CONTEXT.md`](wiki/CONTEXT.md), the METHOD's vocabulary, which travels with this folder. A host repository's own `CONTEXT.md` keeps only the words for its target -- read both before arguing about any of them |
| why a decision that looks wrong was made | [`docs/adr/`](docs/adr/) |
| how to install this into a project | [`SETUP.md`](SETUP.md) |

## Where the scripts this replaced went

A consumer's own scripts are **archived**, not lost. Each project that adopts the kit tags its tree before the deletions begin, with an annotated tag called `archive/pre-kit-scripts` on the last commit that held every script:

    git show archive/pre-kit-scripts:<path>          recover one
    git log --oneline archive/pre-kit-scripts -1     what it points at

A tag is a permanent named pointer that cannot drift, and it can point at any commit -- so there is no reason to carry superseded scripts through a whole migration. Where each one went is recorded in a generated document in the host repository, together with the measurement that made deleting it safe. `WORKING.md` section 7 has the convention in full, including the check that has to pass before anything is deleted.

The decisions behind it: *the kit travels as one folder*, and *tag the archive,
then delete what the toolkit superseded* -- a tag can point at any commit, so
there is no reason to carry superseded scripts through a whole migration.
