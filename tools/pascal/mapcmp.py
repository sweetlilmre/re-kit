"""Compare build/VTMAIN.MAP's segment lengths against the original's, ON THE SAME FOOTING.

THE FOOTING IS THE POINT. Three numbers get confused here and mixing any two of them
manufactures a gap that is not there:

  * `verify.py`'s size  -- the CODE bytes in a .TPU. Excludes the padding a segment
    carries, so it reads SHORT of the segment by up to 15.
  * our map's `Length`  -- the linked segment's exact code length. Also excludes
    padding: the linker pads by starting the NEXT segment on a paragraph.
  * the original's size -- read off the segment ADDRESSES, so it is always the code
    length rounded UP to a paragraph.

So the honest comparison rounds OUR length up to a paragraph too, which is what the
original's addresses already did. Doing it any other way puts every unit in the program
15 bytes "short" and buries the four that really are.

A surviving gap is a WORK LIST rather than a defect: Turbo Pascal smart-links per
routine, so each gap names a reference our program does not yet make and the linker
found it for free.
"""
import io
import re
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import project                                    # noqa: E402

try:
    import tomllib
except ModuleNotFoundError:                       # pragma: no cover -- 3.11+
    import tomli as tomllib                       # type: ignore




def read_link(path):
    """The original's segment list, its RTL set, and where the last one ends.

    All three were constants here. The segment list was ALSO a constant in the
    link-order tool, and the two had drifted: this one was missing VTSHELL, so
    that unit's length was never compared and the headline count was 28 of 29
    with nothing saying so. One list now, read by both.
    """
    with io.open(path, "rb") as fh:
        cfg = tomllib.load(fh)
    segs = [(s["segment"], s["name"]) for s in cfg["segments"]]
    return segs, set(cfg["lists"]["rtl"]), cfg["end_at"]


def orig_lengths(segs, end_at):
    """Each segment's length: the NEXT one's address minus its own.

    So the list has to be complete and in order, and the last entry needs the
    end of the image -- which is why `end_at` is a separate answer rather than a
    row with no name in it.
    """
    out = {}
    bounds = segs + [(end_at, None)]
    for (seg, name), (nxt, _) in zip(bounds, bounds[1:]):
        if name:
            out[name] = (nxt - seg) * 16
    return out


def map_lengths(path):
    out = {}
    for line in path.read_text(encoding='ascii', errors='replace').splitlines():
        m = re.match(r'\s*([0-9A-F]+)H\s+([0-9A-F]+)H\s+([0-9A-F]+)H\s+(\S+)\s+CODE\s*$',
                     line)
        if m:
            out[m.group(4)] = int(m.group(3), 16)
    return out


def main(argv=()):
    args = [a for a in argv if not a.startswith('-')]
    if not args:
        sys.stdout.write("usage: mapcmp.py LINK.toml" + "\n")
        return 2
    segs, rtl, end_at = read_link(args[0])
    root = pathlib.Path(args[0]).resolve().parent
    while not (root / 'kit.toml').exists() and root != root.parent:
        root = root.parent
    with io.open(args[0], 'rb') as fh:
        mp = root / tomllib.load(fh)['map_file']
    if not mp.exists():
        sys.stdout.write("  no %s -- build with the linker map switch first"
                         % mp + "\n")
        return 2
    ours, orig = map_lengths(mp), orig_lengths(segs, end_at)

    rows = []
    for _, name in segs:
        if not name:
            continue
        o = orig[name]
        n = ours.get(name)
        if n is None:
            rows.append((o, name, None, o, 'ABSENT -- nothing references this unit'))
            continue
        # round ours up to a paragraph, which is what the original's addresses did
        padded = (n + 15) & ~15
        gap = o - padded
        if gap > 0:
            note = 'short -- %d byte(s) of routines nothing references' % gap
        elif gap < 0:
            note = 'LONGER than the original by %d -- see the CMDLINE note' % -gap
        else:
            note = 'exact'
        if name in rtl:
            note += '   (RTL, out of scope)'
        rows.append((gap, name, n, o, note))

    print("%-14s %8s %8s %8s  %s" % ("unit", "ours", "padded", "original", "verdict"))
    print("-" * 88)
    # largest gap first: that is the work list's own order
    for gap, name, n, o, note in sorted(rows, key=lambda r: -abs(r[0])):
        print("%-14s %8s %8s %8d  %s" % (
            name, '--' if n is None else n,
            '--' if n is None else (n + 15) & ~15, o, note))

    live = [r for r in rows if r[0] and r[1] not in rtl]
    print("-" * 88)
    print("%d unit(s) exact; %d with a live gap, %d byte(s) in total" % (
        len(rows) - len([r for r in rows if r[0]]),
        len(live), sum(abs(r[0]) for r in live)))


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]) or 0)
