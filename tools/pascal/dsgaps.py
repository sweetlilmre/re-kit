r"""Sort the `DS:$XXXX` addresses a reconstruction's comments record, and print
the GAP between each and the next.

    python kit/tools/pascal/dsgaps.py src/UNIT.PAS
    python kit/tools/pascal/dsgaps.py src/*.PAS --min 64

WHAT THIS MECHANISES. A long reconstruction accumulates addresses in its
comments -- `{ DS:$5BCC -- entry 0 is the translation }` beside one array,
`{ DS:$632F, stride 7 }` beside the next. Individually each is a note. Sorted,
they are a map of the ORIGINAL's data segment, and **the gap between two
consecutive addresses is the size of whatever is declared at the first one**.

That is a measurement of the binary, not of our build, which is what makes it
worth having: it prices every declaration against what the original had room
for, without a linker map and without compiling anything.

HOW TO READ IT. Take each row's gap and compare it with the size of the
declaration the comment sits on:

  gap == declared size     confirmed; nothing to do
  gap MUCH larger          something undeclared sits after it, OR the
                           declaration is a POINTER where the original has the
                           array inline -- a four-byte declaration against a
                           gap of thousands is the loudest signal this produces
  gap smaller              the declaration is too big, or the NEXT address is
                           a folded subscript displacement rather than a real
                           address (see below)

The check that a whole run is sound is that it TILES: each address plus its
size should be the next address, and the last should land where the following
unit's block begins. A run that tiles end to end is one where every size is
right.

BLIND SPOTS, AND THE FIRST IS THE DANGEROUS ONE.

**A comment is a record of a past measurement, not a measurement.** These go
stale, and two comments in one file can disagree about the same variable -- on
the corpus this was written for, one array had two addresses recorded 2,048
bytes apart and the one beside the declaration was the wrong one. Prefer an
address recorded beside the CODE THAT USES a variable, and let tiling arbitrate.

**Some recorded `DS:` values are not addresses at all.** Borland folds an
array's low bounds into the addressing displacement, so a disassembly shows the
array's address MINUS the fold, and that number looks exactly like an address.
A gap that is negative or absurd usually means one of its two endpoints is a
folded base. The tell is that the discrepancy factorises into a bound times a
stride.

**It cannot see what nobody has written a comment about**, so it is strongest on
a mature reconstruction and silent on an unread unit. It is a way of harvesting
work already done.

**And it says nothing about our build.** Pair it with `dsmap.py`, which
compares our data references against the original's and reports the shift.
"""
import collections
import io
import pathlib
import re
import sys

ADDR = re.compile(r"DS:\$([0-9A-Fa-f]{4})")


def collect(paths):
    """Every DS: address in these files, with where it was written."""
    seen = collections.defaultdict(list)
    for path in paths:
        p = pathlib.Path(path)
        if not p.is_file():
            sys.stdout.write("  no such file: %s\n" % path)
            continue
        text = io.open(p, encoding="ascii", errors="replace").read()
        for n, line in enumerate(text.split("\n"), 1):
            for m in ADDR.finditer(line):
                seen[int(m.group(1), 16)].append((p.name, n, line.strip()))
    return seen


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        sys.stdout.write(__doc__ or "")
        return 0
    least = 0
    if "--min" in argv:
        i = argv.index("--min")
        least = int(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]

    seen = collect(argv)
    if not seen:
        sys.stdout.write("  no DS:$XXXX comments found in %d file(s)\n" % len(argv))
        return 1

    addrs = sorted(seen)
    sys.stdout.write("%d distinct address(es) across %d file(s)\n\n"
                     % (len(addrs), len(argv)))
    sys.stdout.write("  %-8s %-8s %s\n" % ("address", "gap", "where it was recorded"))

    duplicated = []
    for i, a in enumerate(addrs):
        gap = (addrs[i + 1] - a) if i + 1 < len(addrs) else None
        if gap is not None and gap < least:
            continue
        where = seen[a][0]
        note = "%s:%d" % (where[0], where[1])
        sys.stdout.write("  $%04X    %-8s %s\n"
                         % (a, str(gap) if gap is not None else "(last)", note))
        if len(seen[a]) > 1:
            duplicated.append(a)

    if duplicated:
        sys.stdout.write("\n  %d address(es) recorded in more than one place -- "
                         "check they agree:\n" % len(duplicated))
        for a in duplicated:
            sys.stdout.write("    $%04X\n" % a)
            for name, n, line in seen[a]:
                sys.stdout.write("      %s:%d  %s\n" % (name, n, line[:88]))

    sys.stdout.write("\n  A GAP IS THE SIZE OF WHAT IS DECLARED AT THAT ADDRESS.\n"
                     "  A four-byte declaration against a gap of thousands is a\n"
                     "  pointer where the original has the array inline.\n"
                     "  Absurd or negative gaps: one endpoint is probably a FOLDED\n"
                     "  subscript base, not an address.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
