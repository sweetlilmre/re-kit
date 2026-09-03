"""The project's answers to the kit's questions.

THE KIT HOLDS NO PROJECT FACTS. That is what makes it portable, and it means
every program in it needs somewhere to look up the facts it cannot contain: the
paths of a host repository, and the things a person read out of a target's
binaries once. That somewhere is a file at the host's root, and this module is
the only reader of it.

    kit.toml           committed. Relative paths, and target facts.
    kit.local.toml     NOT committed. Machine paths, which may never appear in
                       a committed file. Overrides kit.toml key by key.

**A person does not hand-write either.** A setup wizard writes them when the
kit is installed into a project -- decided on the map's kit/record ticket -- so
this module only ever reads.

TWO RULES, both from that ticket, and both are the reason this file is small:

  * **AN EXPLICIT ARGUMENT ALWAYS WINS.** Passing a path on the command line
    stays legal for ever; the answers file is what a program falls back to. So
    every accessor here takes an `override` and returns it untouched.

  * **A MEASURED VALUE NEVER LIVES HERE.** Coverage, byte-match lengths,
    observations and rungs are measured, and they live in the status register
    where a ratchet can guard them. What belongs here is what somebody READ:
    a segment list out of a unit header, the paragraph a disassembler calls the
    start of an image, where the sources are. The test is measured-versus-read,
    not path-versus-value. It matters: a coverage number pasted into a
    documented command line sat two below the truth for days, which is exactly
    the staleness the ratchet exists to prevent.

WHY IT PRINTS. Layout knowledge held in prose has drifted three times in one
day in this project's own host repository -- an install command that never
worked, a check that could never pass, and a docstring promising a config file
that did not exist. So a program says which value it used and where it came
from, and a disagreement with the tree is visible rather than silent.
"""
import io
import os
import pathlib
import sys

try:
    import tomllib
except ModuleNotFoundError:                 # pragma: no cover -- 3.11+
    import tomli as tomllib                 # type: ignore

ANSWERS = "kit.toml"
LOCAL = "kit.local.toml"


class Missing(Exception):
    """No answers file, or no answer. Carries a line fit to print as-is."""


def find(start=None):
    """The host root: the nearest directory at or above `start` with kit.toml.

    Walking up rather than assuming the current directory means a program runs
    from anywhere inside the project, which is how these tools are used.
    """
    here = pathlib.Path(start or os.getcwd()).resolve()
    for d in [here] + list(here.parents):
        if (d / ANSWERS).is_file():
            return d
    return None


def load(start=None):
    """(answers, provenance). The local file overrides, key by key and one
    level deep, because a machine path is a leaf and nothing here nests
    deeper than a section."""
    root = find(start)
    if root is None:
        raise Missing("no %s found at or above %s -- the kit is not installed "
                      "into this project yet" % (ANSWERS, os.getcwd()))
    data, where = {}, {}
    for name in (ANSWERS, LOCAL):
        path = root / name
        if not path.is_file():
            continue
        with io.open(path, "rb") as fh:
            loaded = tomllib.load(fh)
        for section, body in loaded.items():
            if isinstance(body, dict):
                data.setdefault(section, {}).update(body)
                for k in body:
                    where["%s.%s" % (section, k)] = name
            else:
                data[section] = body
                where[section] = name
    data["_root"] = root
    return data, where


def get(key, override=None, start=None, quiet=False):
    """One answer, by dotted key -- `layout.src`, `target.first_para`.

    An explicit override is returned untouched and unannounced: the caller
    said what it wanted and does not need telling.
    """
    if override is not None:
        return override
    data, where = load(start)
    section, _, name = key.partition(".")
    try:
        value = data[section][name]
    except (KeyError, TypeError):
        raise Missing("%s does not answer `%s` -- add it, or pass the value "
                      "on the command line" % (ANSWERS, key))
    if not quiet:
        sys.stdout.write("  using    %s = %r  (%s)\n"
                         % (key, value, where.get(key, ANSWERS)))
    return value


# `derive()` STOOD HERE, and it is gone rather than kept for safety. It
# turned a one-row `target.original` into a `target.image`, so a project with
# one original could state its path once while eight instruments still asked
# the narrow key. Those eight ask `original()` below now, so the derivation
# had no callers -- and a fallback left in place after its callers stop asking
# is a second way to answer one question, which is the drift this module
# exists to prevent. Retiring the key it fed is the whole point of the change,
# so keeping the bridge would have kept the key.


def original(part=None, override=None, start=None, quiet=False):
    """The binary an instrument should read, from `target.original`.

    THE GENERAL FORM, and `target.image` was the narrowing. A map from part to
    path covers a project with one original and a project with nine; an image
    cannot be turned into a map, because the part is exactly what an image does
    not carry. So the eight instruments that used to ask for an image ask here.

    Resolution order, and every step is deliberate:

      * AN EXPLICIT OVERRIDE WINS, untouched and unannounced. Four of the eight
        already accept `--original` and that must keep working.
      * A NAMED PART is looked up in the map. If the map has no such row, this
        refuses and lists the parts it does have -- a part number that is right
        for the source tree and absent from the answers file is a real gap, and
        naming the alternatives is what makes it fixable.
      * NO PART, and a map with exactly ONE row, uses that row. A project with
        one original states its path once and its instruments need no argument.
      * NO PART, and a map with SEVERAL rows, REFUSES. Choosing a part on an
        instrument's behalf is how the wrong original gets measured against
        silently, and the result still looks correct -- which is the failure
        `target.release` exists to prevent one level up. An instrument that
        wants "the image" has no answer in a nine-part project, and saying so
        is more useful than picking one.
    """
    if override is not None:
        return pathlib.Path(override)
    originals = get("target.original", start=start, quiet=True)
    if not isinstance(originals, dict) or not originals:
        raise Missing("%s answers `target.original` with no rows -- it maps a "
                      "part to the binary that part was read out of" % ANSWERS)
    known = ", ".join(sorted(originals))
    if part is None:
        if len(originals) != 1:
            raise Missing(
                "this project has %d originals, so `the image` has no answer "
                "-- name a part. %s answers: %s"
                % (len(originals), ANSWERS, known))
        part, value = next(iter(originals.items()))
        why = "target.original, its only row, part %s" % part
    else:
        part = str(part)
        if part not in originals:
            raise Missing(
                "%s has no original for part %s -- it answers: %s"
                % (ANSWERS, part, known))
        value = originals[part]
        why = "target.original, part %s" % part
    if not quiet:
        sys.stdout.write("  using    original = %r  (%s)\n" % (value, why))
    root = find(start)
    return (pathlib.Path(root) / value) if root else pathlib.Path(value)


def path(key, override=None, start=None, quiet=False):
    """An answer that is a path, resolved against the HOST ROOT rather than the
    working directory -- so a program run from a subdirectory still finds it."""
    value = get(key, override, start, quiet)
    if override is not None:
        return pathlib.Path(value)
    root = find(start)
    return (pathlib.Path(root) / value) if root else pathlib.Path(value)


def products(build=None, start=None, quiet=True):
    """Where the build's products are: `layout.output`, or the staging dir.

    A build may write its .OBJ, .TPU, .MAP and .EXE into a subdirectory of the
    staging directory instead of leaving them among the sources it was given --
    `[stage] output` in the build config, `layout.output` here. Every instrument
    that reads a PRODUCT has to look there; the ones that read a staged SOURCE
    must not, which is why this is a separate answer rather than a redefinition
    of `layout.build`.

    Unset, this returns what it was passed, so a project that has never split
    the two is unaffected and needs no answer added.

    THE FAILURE IT PREVENTS was not subtle, and that is worth recording: the
    first tool to go unconverted read no .MAP files at all and reported ten of
    ten parts as having the WRONG UNIT ORDER. Loud, and in the safe direction.
    A tool that had instead found nothing and called it agreement would have
    read as ten passes.
    """
    try:
        return path("layout.output", start=start, quiet=quiet)
    except Missing:
        return build


class Stale(Exception):
    """A build product older than something it was built from."""


def fresh(artifact, sources=None, start=None):
    """Refuse a build product older than the sources it was built from.

    EVERY INSTRUMENT IN THE KIT READS AN ARTEFACT OFF DISK AND CANNOT TELL A
    FRESH ONE FROM A STALE ONE. That is not a hypothetical. In this project's
    own host repository a build failed six times in a row while four separate
    measurements reported the image byte-identical and the packed output
    byte-identical -- all four reading the last .EXE that HAD compiled, which
    was genuinely exact, for source that no longer existed.

    The build refused loudly every time and said exactly the right thing:
    "NOTHING WAS INSTALLED, so anything in the output directory is STALE and
    any measurement of it is meaningless." It was read through a grep for
    `error|fatal`, which that sentence does not contain. **A warning that has
    to be read is not a guard**; the instrument that consumes the artefact is
    the only place a check cannot be skipped by accident.

    So this is a comparison of modification times, and it belongs here rather
    than in any one tool because they all need it and none of them owns it:

        artifact   the product about to be measured
        sources    what it was built from -- files, or directories to walk.
                   Defaults to `layout.src`, which is the answer every host
                   already has.

    A missing artefact raises too, and with the same reasoning: the alternative
    is a tool that finds nothing and reports agreement, which the note on
    `products` above records as the failure that reads as ten passes.

    IT IS DELIBERATELY A TIMESTAMP AND NOT A HASH. A hash of the sources would
    be exact and needs somewhere to keep the manifest, which is a second thing
    to go stale. A file older than its inputs is wrong under every build
    system, and false alarms cost one rebuild.
    """
    artifact = pathlib.Path(artifact)
    if not artifact.exists():
        raise Stale("%s does not exist -- there is nothing to measure. Build "
                    "first, and read what the build says." % artifact)

    if sources is None:
        sources = paths("layout.src", start=start, quiet=True)
    if isinstance(sources, (str, pathlib.Path)):
        sources = [sources]

    newest, when = None, 0.0
    for s in sources:
        s = pathlib.Path(s)
        for f in ([s] if s.is_file() else sorted(s.rglob("*"))):
            if f.is_file() and f.stat().st_mtime > when:
                newest, when = f, f.stat().st_mtime

    if newest is not None and when > artifact.stat().st_mtime:
        raise Stale(
            "%s is OLDER than %s, so it was not built from the sources on "
            "disk and measuring it means nothing.\n"
            "  Rebuild. If the build refused, that is the finding -- read its "
            "output in full rather than filtering it." % (artifact, newest))
    return artifact


def paths(key, override=None, start=None, quiet=False):
    """An answer that is a list of paths -- census roots, for instance."""
    value = get(key, override, start, quiet)
    if isinstance(value, str):
        value = [value]
    root = find(start)
    return [(pathlib.Path(root) / v) if root else pathlib.Path(v)
            for v in value]


def positionals(argv, valued=()):
    """The real positional arguments: not a flag, and not a FLAG'S VALUE.

    Every program here used to do `[a for a in argv if not a.startswith("--")]`,
    which reads the value of `--coverage 76` as a positional. That is not a
    style point: `ratchet.py --coverage 76` took "76" as the name of the status
    register, loaded nothing, and reported `coverage 0 -> 76` as a RISE -- a
    measurement invented out of a missing file, in the one tool whose whole
    purpose is refusing to let a measurement slip. With `--write` it would have
    created a file called `76`.

    So a caller names the flags that take a value, and their values are skipped.
    """
    out, skip = [], False
    for a in argv:
        if skip:
            skip = False
            continue
        if a.startswith("--"):
            skip = a in valued or a.lstrip("-") in valued
            continue
        out.append(a)
    return out


def complain(exc):
    """Print a Missing as one line and nothing else. A program pointed at
    nothing should say so, not stack-trace at somebody who has just installed
    the kit."""
    sys.stdout.write("  %s\n" % exc)
    return 2
