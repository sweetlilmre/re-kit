"""Does our build link its units in the ORIGINAL's order? The walk cannot tell.

    unitorder.py SPANS.toml [PART...]

WHY NOTHING ELSE ANSWERS THIS. A coverage walk locates each segment by CONTENT,
so it finds every unit wherever the linker put it and scores it aligned. Two of
the first target's seven parts had their units in a different order from the
1994 binaries -- one with a shared unit sixth instead of second, another with
four units in almost the reverse order -- and both walked at 99.7% or better
throughout. The order is invisible to the instrument that matters most, and it
decides where every global lives, which is why the initialised data image was
the only thing complaining.

HOW IT MEASURES. The compiler's own map file gives each unit's segment length;
the spans file gives the original's segment boundaries, whose differences are
the original's lengths. Compared IN ORDER, with a tolerance, the sequence of
lengths is a fingerprint: a unit in the wrong place shows up as two lengths
that cannot be reconciled. This needs a map, so the build must pass /GD (or
whatever the dialect's map switch is).

TWO ROWS HAVE NO COUNTERPART and must be dropped, or every part reads as a
mismatch. A harness is a program plus a driver unit; the original's main body
IS the program, so neither the harness's own segment nor the driver unit it
calls has anything to pair with. Getting this wrong reported six of seven parts
broken when only two were.

WHAT TO DO WITH A MISMATCH. Turbo Pascal's link order is a reverse DFS
post-order over the `uses` graph, and THE WALK STARTS AT THE PROGRAM -- so the
program's clause, not the unit's, decides where shared units land. A unit named
in the program's clause is visited early, finishes early, and lands LATE in
code; leave it out and let the one unit that needs it pull it in, and it lands
directly after that unit. Reordering the intermediate unit's own clause does
nothing, which is worth knowing before trying it.
"""
import sys, tomllib, re, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import project                                    # noqa: E402


def lengths_from_map(path):
    """(name, padded length) per CODE segment, in address order."""
    rows = []
    for line in path.read_text(encoding="ascii", errors="replace").splitlines():
        m = re.match(r"\s*([0-9A-F]+)H\s+([0-9A-F]+)H\s+([0-9A-F]+)H\s+(\S+)\s+CODE",
                     line)
        if m:
            rows.append((int(m.group(1), 16), m.group(4),
                         (int(m.group(3), 16) + 15) // 16 * 16))
    rows.sort()
    return [(n, s) for _, n, s in rows]


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    cfg = tomllib.load(open(argv[0], "rb"))["part"]
    parts = argv[1:] or list(cfg)
    bad = 0
    for part in parts:
        spec = cfg[part]
        mp = pathlib.Path("build") / spec["exe"].replace(".EXE", ".MAP")
        if not mp.exists():
            print("part %-7s no map at %s -- is the map switch on?" % (part, mp))
            bad += 1
            continue
        segs = list(spec["segs"]) + [spec["rtl"]]
        want = [(segs[i + 1] - segs[i]) * 16 for i in range(len(segs) - 1)]

        # THE PROGRAM'S OWN SEGMENT IS NOT A UNIT, and it has to come off BOTH
        # sides or the counts cannot be compared. This used to be done on our
        # side alone, by dropping any map entry whose name matched the
        # executable's stem -- which worked only while the program IDENTIFIER
        # differed from the file name. Three parts depended on that luck, and
        # renaming two of them so the identifier finally matched the stem broke
        # the comparison for both: 2 units against the original's 3, on a target
        # where every byte of both was identical.
        #
        # Positionally it is unambiguous. The map lists code segments in address
        # order and the program is always first, so it is ours[0]; and it is in
        # `want` only when the config's segment list starts at the load image's
        # first paragraph.
        first = project.get("target.first_para", quiet=True) or 0x1000
        if spec["segs"][0] == first:
            want = want[1:]
        ours = [(n, s) for n, s in lengths_from_map(mp)
                if n != "System"
                and not (n.endswith("Main") or n.endswith("Intro"))]
        ours = ours[1:]
        if len(ours) != len(want):
            print("part %-7s MISMATCH -- %d unit(s) against the original's %d"
                  % (part, len(ours), len(want)))
            print("     original %s" % want)
            print("     ours     %s" % ["%s=%d" % o for o in ours])
            bad += 1
            continue
        off = [i for i, (o, w) in enumerate(zip(ours, want))
               if abs(o[1] - w) > max(200, w * 0.06)]
        if off:
            print("part %-7s MISMATCH at position(s) %s"
                  % (part, ", ".join(str(i) for i in off)))
            print("     original %s" % want)
            print("     ours     %s" % ["%s=%d" % o for o in ours])
            bad += 1
        else:
            print("part %-7s order matches, %d unit(s)" % (part, len(ours)))
    print("\n%d part(s) checked, %d with the wrong unit order" % (len(parts), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
