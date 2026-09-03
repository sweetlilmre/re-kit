"""Compare our INITIALISED DGROUP image against the original's, block by block.

RISK 1 HAS NEVER BEEN MEASURABLE UNTIL NOW, and this is the instrument. A `.TPU`
comparison cannot see a variable address at all -- every DGROUP reference is a pending
fixup that `verify.py` deliberately excuses -- so where a global is declared could not
change any measurement the project made. The LINKED image is different: the linker
lays every unit's data down in one flat DGROUP, in link order, and the part of it that
is INITIALISED is written into the EXE where it can simply be read.

    original   segment `1caa`, 3,184 bytes   (the image's tail, after every CODE seg)
    ours       the DATA segment, from build/VTMAIN.MAP

Only TYPED CONSTANTS appear there -- a plain `var` is reserved space and is not stored
-- so this measures the layout of the initialised part only. That is still most of what
risk 1 is about, because a typed constant's position pins its neighbours: the same
spacing argument that fixed `19a0`'s twenty-eight ports works here on the whole program
at once, and it works on DATA rather than on code.

WHAT THE OUTPUT MEANS. Each of our 16-byte blocks is looked up in the original. A block
found at the SAME offset is a variable in the right place. A block found at a DIFFERENT
offset is a variable in the wrong place, and the shift is how far out its unit is. A
block found NOWHERE is data the original has not got -- or ours holding a different
value, which is a transcription question rather than a layout one.

    python kit/tools/pascal/dgroup.py LINK.toml               the summary
    python kit/tools/pascal/dgroup.py LINK.toml -v            every block
    python kit/tools/pascal/dgroup.py SPANS.toml --part 003   one part of many
"""
import re
import struct
import io
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import project                                    # noqa: E402

try:
    import tomllib
except ModuleNotFoundError:                       # pragma: no cover -- 3.11+
    import tomli as tomllib                       # type: ignore

BLOCK = 16


def orig_image(image, dgroup_seg, first_para):
    p = pathlib.Path(image).read_bytes()
    hdr = struct.unpack_from('<H', p, 8)[0] * 16
    # Everything after the DGROUP segment in the file is initialised DGROUP,
    # because it is the LAST segment in the image. That is a property of the
    # link, so which segment it is comes from the config -- it was 0x1caa as a
    # literal here, and the same number was the boundary marker in two other
    # tools' segment lists.
    return p[hdr + (dgroup_seg - first_para) * 16:]


def our_image(mapfile, exe):
    mp = pathlib.Path(mapfile).read_text(encoding='ascii', errors='replace')
    m = re.search(r'^\s*([0-9A-F]+)H\s+[0-9A-F]+H\s+[0-9A-F]+H\s+DATA\s+DATA\s*$',
                  mp, re.M)
    if not m:
        raise SystemExit("no DATA line in %s -- build with the map switch" % mapfile)
    start = int(m.group(1), 16)
    p = pathlib.Path(exe).read_bytes()
    hdr = struct.unpack_from('<H', p, 8)[0] * 16
    return p[hdr + start:]


def ladder(orig, ours, win=12):
    """The DELTA LADDER: where our DGROUP starts running short, and by how much.

    THIS IS THE OUTPUT TO READ. Every window of the original that is DISTINCTIVE --
    unique in the original, and not a run of one byte -- is looked up in ours, and the
    offset difference is recorded. Runs of the same difference collapse into one row,
    so each row is a stretch of DGROUP that agrees on its placement and each STEP
    between rows is a unit whose data is the wrong size. The step is the number of
    bytes to find, and the two offsets bracket where to look.

    Anchors were curated by hand first and that was the wrong shape: the useful thing
    is not which unit owns a byte, it is WHERE THE DELTA CHANGES, and the image can
    find those itself.
    """
    seen = {}
    for i in range(len(orig) - win + 1):
        seen[orig[i:i + win]] = None if orig[i:i + win] in seen else i

    rows = []
    for i in range(0, len(orig) - win + 1, 4):
        w = orig[i:i + win]
        if len(set(w)) < 4 or seen.get(w) != i:
            continue                      # not distinctive, or not unique
        at = ours.find(w)
        if at < 0 or ours.find(w, at + 1) >= 0:
            continue                      # absent, or ambiguous on our side
        d = at - i
        if rows and rows[-1][2] == d:
            rows[-1][1] = i
        else:
            rows.append([i, i, d])
    return rows


def main(argv=()):
    verbose = '-v' in argv
    # project.positionals, NOT the naive filter this used. Adding a flag that
    # carries a value to `[a for a in argv if not a.startswith('-')]` puts the
    # VALUE in the positionals -- `--part 003` would have made "003" the config
    # path. That is the bug project.positionals was written for, recorded in
    # its own docstring from ratchet.py reading "76" as the register's name.
    args = project.positionals(argv, ("--part",))
    part = project.option(argv, "part")
    if not args:
        sys.stdout.write("usage: dgroup.py LINK.toml [--part NNN] [-v]"
                         + chr(10))
        return 2
    root = pathlib.Path(args[0]).resolve().parent
    while not (root / 'kit.toml').exists() and root != root.parent:
        root = root.parent
    with io.open(args[0], 'rb') as fh:
        link = tomllib.load(fh)
    try:
        # One image, one map, one boundary -- so one part, resolved once.
        # This tool used to be narrow THREE times over: it took the image
        # from a single-target answer and the map and the segment cap from
        # top-level keys, so naming a part fixed one third of the question
        # and left the other two pointing at whichever target the config
        # happened to describe.
        image = project.original(part)
        first = project.get("target.first_para", quiet=True)
        spec = project.layout(link, part)
    except project.Missing as exc:
        return project.complain(exc)
    mapfile = root / spec['map']
    if not mapfile.exists():
        sys.stdout.write("  no %s -- build with the map switch first%s"
                         % (mapfile, chr(10)))
        return 2
    # WHERE DGROUP STARTS IS ITS OWN FACT, not the segment walk's bound.
    # This read `end_at`, and the two coincide only when the segment list
    # happens to include the runtime library. One target lists its RTL
    # segments, so its bound lands AFTER them, which is where DGROUP
    # begins; another deliberately excludes them, so the same key lands
    # BEFORE the runtime and this measured the RTL as part of DGROUP --
    # every part short by exactly the runtime's size, and every printed
    # figure plausible.
    project.fresh(mapfile.with_suffix('.EXE'))
    dg = spec.get('dgroup_at')
    if dg is None:
        sys.stdout.write(
            "  this part does not say `dgroup_at` -- the paragraph its"
            " DGROUP begins at. It is not the same fact as `end_at`,"
            " which closes the segment walk, and the two are equal only"
            " when the segment list includes the runtime library."
            + chr(10))
        return 2
    orig, ours = (orig_image(image, dg, first),
                  our_image(mapfile, mapfile.with_suffix('.EXE')))
    print("initialised DGROUP:  ours %d bytes, original %d -- %+d" % (
        len(ours), len(orig), len(ours) - len(orig)))
    print()

    rows = ladder(orig, ours)
    print("THE DELTA LADDER -- each STEP is a unit whose data is the wrong size.")
    print("%-20s %10s   %s" % ("original range", "delta", "what it means"))
    print("-" * 78)
    prev = None
    for lo, hi, d in rows:
        note = 'placed correctly' if d == 0 else 'ours is %d byte(s) low' % -d
        if prev is not None and d != prev:
            note += '   <-- STEP of %d byte(s) just above %04x' % (prev - d, lo)
        print("%04x .. %04x %14d   %s" % (lo, hi, d, note))
        prev = d
    print()

    # where does each of our blocks appear in the original?
    same = moved = absent = 0
    rows = []
    for off in range(0, len(ours) - BLOCK + 1, BLOCK):
        blk = ours[off:off + BLOCK]
        if blk == orig[off:off + BLOCK]:
            same += 1
            rows.append((off, 'same', 0))
            continue
        # a run of one repeated byte matches everywhere and says nothing
        if len(set(blk)) == 1:
            rows.append((off, 'flat', None))
            continue
        at = orig.find(blk)
        if at < 0:
            absent += 1
            rows.append((off, 'absent', None))
        else:
            moved += 1
            rows.append((off, 'moved', at - off))

    if verbose:
        for off, kind, delta in rows:
            note = {'same': 'in place', 'flat': 'a run of one byte -- no evidence',
                    'absent': 'NOT IN THE ORIGINAL AT ALL'}.get(kind)
            if kind == 'moved':
                note = 'in the original at %+d (%04x)' % (delta, off + delta)
            print(" %04x  %-7s %s" % (off, kind, note))
        print()

    print("%d block(s) in place, %d moved, %d absent, %d uninformative" % (
        same, moved, absent, len(rows) - same - moved - absent))

    # the shifts, grouped: one shift shared by many blocks is one unit out of place
    from collections import Counter
    shifts = Counter(d for _, k, d in rows if k == 'moved')
    if shifts:
        print()
        print("SHIFTS, most blocks first -- each is a run of DGROUP in the wrong place:")
        for d, n in shifts.most_common(12):
            print("   %+7d  %3d block(s) = %d bytes" % (d, n, n * BLOCK))

    # the contiguous in-place prefix is the honest headline: it is how far the
    # layout agrees before anything moves.
    pre = 0
    for off, kind, delta in rows:
        if kind not in ('same', 'flat'):
            break
        pre = off + BLOCK
    print()
    print("the layout agrees for the first %d byte(s)" % pre)


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except project.Stale as exc:
        raise SystemExit('STALE: %s' % exc)
