"""Assembler that appears in more than one unit should be ONE TEXT.

Borland Pascal duplicates an included procedure into every unit that includes
it, and that is how a 1990s author shared a routine between units without
exporting it: `{$I}`, not a shared unit. A shared unit would change the emitted
code at every call site -- an imported routine is reached with a far call --
so the rebuild of a duplicated routine has to duplicate it too, from one text.

Which means a rebuild can quietly hold two copies of one routine, and a
per-routine byte check cannot notice: it compares each DECLARED routine against
the binary it names, so a routine written out twice is two passing rows, and a
routine re-expressed in Pascal in one of the two units is no row at all. This
reads the source instead and reports assembler bodies that are duplicated
between units rather than shared.

    python kit/tools/pascal/shared_asm.py SRCDIR
    python kit/tools/pascal/shared_asm.py SRCDIR --exempt exempt.txt

It REPORTS and exits 0 unless --gate is passed, because whether a duplicate can
become one text is a fact about the routine and not something a tool can see:
three copies of one routine in the psycho corpus have three different
declarations -- `far` in a shared unit, an untyped `var` parameter, a typed
pointer -- so there is no single text to share. Cases like that go in the
exempt file, one `UNIT.Routine` per line with `#` comments, and a project that
wants the rule enforced passes --gate.

This one was WRITTEN HERE, not copied. The map's copy-and-adjust rule protects
tools that already existed; a new generic tool has no original to freeze, so
writing it in `tools/` first and copying it here would duplicate it from birth
-- which is what happened on the first attempt, complete with two rows in the
census for one tool. Project facts stay out of it: the psycho repository keeps
its exemptions in `src/asm/shared-exempt.txt` and passes them in.

Two mechanics of writing the include, both measured 23 Aug 2026 and recorded
here because the tool exists to push people towards it:

  * the include must carry the WHOLE procedure, header and all. Turbo Pascal 7
    answers `Error 118: Include files are not allowed here` to a `{$I}` inside
    an `asm` block. At declaration level it compiles.
  * a `}` closes a `{ }` comment, so an include whose own header comment quotes
    a directive needs `(* *)` delimiters, or the block ends at the first quoted
    directive and the prose after it is parsed as code.
"""
import io
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import project                                    # noqa: E402

MARKER = re.compile(r"@asm\s+(\d{3})\s+([0-9a-fA-F]{4}):([0-9a-fA-F]{4})"
                    r"(?:\s*\+(\d+))?(?:\s+(\w+))?")
HEADER = re.compile(r"\s*(?:procedure|function)\s+(\w+)")
INCLUDE = re.compile(r"\{\$I\s+([A-Za-z0-9_./]+)\s*\}")
COMMENT = re.compile(r"\{[^{}]*\}", re.S)

# Fewer instructions than this and agreement means nothing: a routine that sets
# a video mode is two instructions and every program has one.
TRIVIAL = 8


def strip_comments(text):
    """Blank out `{ }` and `(* *)` comments, KEEPING every newline.

    Line numbers have to survive: `bodies` finds an include or a header by
    looking a few lines below a marker, so a strip that shortened the file
    would move every marker away from what it points at.

    This exists because the scan is otherwise fooled by its own subject
    matter. `HEADER` matches a leading-whitespace `procedure`, and these
    sources are full of indented equivalent-Pascal inside comment blocks --
    P2VIEW.PAS has a commented `procedure SetRGB(Col, R, G, B : Byte);` eight
    lines above the real one. Those blocks happened not to contain an `asm`
    line, which is the only reason the old scan got the right answer.
    """
    out = []
    i, n = 0, len(text)
    while i < n:
        if text[i] == "{":
            j = text.find("}", i)
            j = n if j < 0 else j + 1
        elif text.startswith("(*", i):
            j = text.find("*)", i)
            j = n if j < 0 else j + 2
        else:
            out.append(text[i])
            i += 1
            continue
        out.append("".join(c if c == "\n" else " " for c in text[i:j]))
        i = j
    return "".join(out)


def normalise(text):
    """The instructions, with the commentary and the layout taken out.

    Identifier names are KEPT, because the assembler references them: two
    bodies that differ only in what they call the source pointer are two bodies
    waiting to drift apart, and that is worth a line of output.
    """
    text = COMMENT.sub(" ", text)
    return [" ".join(l.split()).upper() for l in text.split("\n")
            if " ".join(l.split())]


def implementations(lines):
    """Routine -> its assembler, for headers that actually open a body.

    A marker may sit above an INTERFACE declaration, a long way from the body,
    with other declarations in between -- so taking the first `asm` after the
    header a marker points at can hand nine routines the same body, and did.
    Bodies are found from the headers that open one: nothing but a var or const
    block may stand between a header and its `asm`.
    """
    out = {}
    for j, line in enumerate(lines):
        h = HEADER.match(line)
        if not h:
            continue
        k = j + 1
        while k < len(lines) and not HEADER.match(lines[k]):
            if lines[k] == "asm":
                break
            k += 1
        if k >= len(lines) or lines[k] != "asm":
            continue                      # a declaration, not a body
        try:
            end = next(x for x in range(k, len(lines)) if lines[x] == "end;")
        except StopIteration:
            continue
        out.setdefault(h.group(1), normalise("\n".join(lines[k + 1:end])))
    return out


def bodies(src, pattern="*.PAS"):
    """UNIT.Routine -> (address, assembler) for assembler written out in a unit.

    A marker followed by a `{$I}` is a SHARED routine and is skipped: there is
    one text, which is the state this check exists to reach, so counting each
    including unit's copy would report the fix as the fault.

    Pascal sources are read as ASCII on purpose -- they are read by a 1990s DOS
    tool, so a byte above 127 in one is a defect, not an encoding to guess at.
    """
    out = {}
    for path in sorted(pathlib.Path(src).glob(pattern)):
        raw = io.open(path, encoding="ascii", newline="").read()
        # RAW for the marker scan, STRIPPED for body detection. An
        # `@asm` marker lives inside a `{ }` comment and a `{$I}` is a
        # directive in one, so scanning stripped text finds neither --
        # it reported 0 routines out of 59. Bodies want the opposite,
        # because a comment can hold an indented `procedure` line.
        # strip_comments keeps the line count, so both index alike.
        lines = raw.split("\n")
        impl = implementations(strip_comments(raw).split("\n"))
        for i, line in enumerate(lines):
            m = MARKER.search(line)
            if not m:
                continue
            name = m.group(5)
            shared = False
            for j in range(i + 1, min(i + 6, len(lines))):
                if INCLUDE.search(lines[j]):
                    shared = True
                    break
                h = HEADER.match(lines[j])
                if h:
                    name = name or h.group(1)
                    break
            if shared or name is None or name not in impl:
                continue
            out["%s.%s" % (path.stem, name)] = (
                "%s:%s" % (m.group(2), m.group(3)), impl[name])
    return out


def include_bodies(incdir):
    """STEM.Routine -> (label, assembler) for every routine an include holds.

    THE POINT OF THIS: without it the check has a hole exactly where its own
    fix lives. A marker followed by `{$I}` is skipped as shared -- correctly,
    or the cure would be reported as the disease -- but that means an include's
    body is never compared against anything, so a unit that writes out its own
    copy of a routine an include already carries pairs with nobody and passes.

    In the psycho corpus P3MORPH.SetPalette768 was exactly that case: the same
    nine instructions as SETPAL.INC, carrying its own line in the project's
    exempt file, and deleting that line changed the reported count by nothing.
    An exemption that cannot fail is worse than no exemption, because it reads
    like a check.

    An include has no `@asm` marker of its own -- the marker stays at the
    including site, where the address is -- so these are collected by their
    bodies alone and labelled with the file they came from.
    """
    out = {}
    if incdir is None:
        return out
    for path in sorted(pathlib.Path(incdir).glob("*.INC")):
        raw = io.open(path, encoding="ascii", newline="").read()
        for name, body in implementations(
                strip_comments(raw).split("\n")).items():
            out["%s.%s" % (path.stem, name)] = (path.name, body)
    return out


def duplicates(found, exempt=()):
    """Pairs in different units whose assembler is the same text."""
    exempt = set(exempt)
    names = sorted(found)
    out = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if a.split(".")[0] == b.split(".")[0]:
                continue                  # same unit, not this tool's business
            if a in exempt and b in exempt:
                continue
            if len(found[a][1]) < TRIVIAL:
                continue
            if found[a][1] == found[b][1]:
                out.append((a, b))
    return out


def read_exempt(path):
    names = []
    for line in io.open(path, encoding="utf-8", newline="").read().split("\n"):
        line = line.split("#")[0].strip()
        if line:
            names.append(line)
    return names


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    named = [a.split("=", 1)[1] for a in argv if a.startswith("--exempt=")]
    try:
        if not args:
            args = [str(project.path("layout.src"))]
        if not named:
            named = [str(project.path("layout.exempt"))]
    except project.Missing as exc:
        return project.complain(exc)
    exempt = read_exempt(named[0]) if named else []
    found = bodies(args[0])
    nunits = len(found)
    try:
        incdir = str(project.path("layout.includes"))
    except project.Missing:
        incdir = None
    incs = include_bodies(incdir)
    found.update(incs)
    dups = duplicates(found, exempt)
    print("%d routine(s) with assembler written out in a unit" % nunits)
    if incdir is None:
        print("  layout.includes is NOT SET, so no include is being compared: "
              "a unit that writes out its own copy of a routine an include "
              "already carries will not be reported")
    else:
        print("%d routine(s) in %d include(s), compared against them"
              % (len(incs), len(set(k.split(".")[0] for k in incs))))
    for a, b in dups:
        print("  DUPLICATED: %s (%s) and %s (%s) are the same %d instructions"
              % (a, found[a][0], b, found[b][0], len(found[a][1])))
        print("              one text in an include, included by both, unless "
              "their declarations cannot be shared")
    if exempt:
        print("  %d name(s) exempt" % len(exempt))
    print("\n%d duplicate(s)" % len(dups))
    return 1 if (dups and "--gate" in argv) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
