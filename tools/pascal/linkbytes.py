"""Every byte of the LINKED image that differs, by unit, with context.

    python kit/tools/pascal/linkbytes.py LINK.toml
    python kit/tools/pascal/linkbytes.py LINK.toml --only PLAYMOD
    python kit/tools/pascal/linkbytes.py LINK.toml --runs        aligned insert/delete
    python kit/tools/pascal/linkbytes.py LINK.toml --at 0x02e0   both DGROUPs, one address

WHAT IT IS FOR, AND WHY linkcmp.py IS NOT IT. `linkcmp.py` CLASSIFIES a linked
difference -- is this operand a variable address in the wrong place, and by how
much -- and that is the right instrument while whole regions are adrift, because a
delta repeated four hundred times is one cause. It is the wrong one at the end. Once
a unit is down to single figures its classifier has too little to go on: it pairs an
operand with whichever variable is nearest within its tolerance, and near the end
that is a guess. Two of this corpus's last twenty differences were reported under
deltas of -35 and +6656, and both were something else entirely.

This tool classifies nothing. It prints the differing bytes and four bytes either
side, and lets you read the instruction.

    PLAYMOD      +10b2  o 80 u 7f   o 26807d1d807209c43e / u 26807d1d7f7209c43e

That line is a clamp whose constant changed between versions, and no amount of delta
arithmetic would have said so.

## The three modes and when each is right

**Default** is the endgame instrument: a flat list, one line per differing byte. Use
it when the counts are small enough to read. On this corpus it went from unusable to
the only thing worth running somewhere around fifty total differences.

**`--runs`** aligns the two segments with difflib and reports insert/delete runs
instead of substitutions. Use it while a segment still has MISSING or EXTRA code,
where a flat byte list is meaningless because everything after the first gap is
shifted. It is the only mode that can tell you a routine is absent rather than wrong.
Its blind spot is the mirror image: it happily reports paragraph PADDING as a
fifteen-byte deletion, and did so for four sessions on this corpus. A run of zeros at
the end of a segment is alignment, not code.

**`--at`** dumps both DGROUP images around one address. This is the third thing that
gets hand-written every time, usually to answer "is our variable where the original's
is", and it wants an address you got from an instruction rather than from a symbol.

## What it needs, and the order it needs it in

A linker map, which means `/GD` in the compiler switches, and a link order that is
already right. Both are upstream: with the order wrong every unit's base is wrong and
every byte differs, which is a true statement and a useless one. If this tool reports
thousands of differences, it is not the tool to be running -- see `mapcmp.py` for
sizes and `dgroup.py` for the data layout, in that order.

The original's segment bases come from LINK.toml; ours come from the map. Segments
named in LINK.toml's `skip` list -- the runtime library -- are not ours to compare.
"""

import re
import sys
import difflib
import tomllib

sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1]))
import project                                                    # noqa: E402


def load_image(raw):
    """The load image of an MZ file, and its DGROUP-relative base."""
    if raw[:2] not in (b'MZ', b'ZM'):
        return raw
    return raw[int.from_bytes(raw[8:10], 'little') * 16:]


def map_segments(text):
    """{NAME: start} for every CODE segment the linker map names."""
    out = {}
    for m in re.finditer(r'([0-9A-Fa-f]{4,6})H\s+([0-9A-Fa-f]{4,6})H\s+'
                         r'[0-9A-Fa-f]{4,6}H\s+(\w+)\s+CODE', text):
        out[m.group(3).upper()] = int(m.group(1), 16)
    return out


def map_dgroup(text):
    """The paragraph DGROUP was linked at, read from any public data symbol."""
    m = re.search(r'([0-9A-Fa-f]{4}):[0-9A-Fa-f]{4}\s+\w+', text)
    return int(m.group(1), 16) if m else None


def extents(segments, end_at, first_para):
    """(name, base, length) for each declared segment, in address order."""
    out = []
    for i, s in enumerate(segments):
        nxt = segments[i + 1]['segment'] if i + 1 < len(segments) else end_at
        out.append((s['name'].upper(),
                    (s['segment'] - first_para) * 16,
                    (nxt - s['segment']) * 16))
    return out


def report_bytes(name, a, b):
    diffs = [i for i in range(min(len(a), len(b))) if a[i] != b[i]]
    for i in diffs:
        lo, hi = max(0, i - 4), i + 5
        print("%-13s +%04x  o %02x u %02x   o %s / u %s"
              % (name, i, a[i], b[i], a[lo:hi].hex(), b[lo:hi].hex()))
    return len(diffs)


def report_runs(name, a, b):
    n = 0
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal' or max(i2 - i1, j2 - j1) < 3:
            continue
        pad = all(x == 0 for x in a[i1:i2]) and j2 == j1
        print("%-13s %-7s orig +%04x..%04x (%3d)  ours (%3d)%s"
              % (name, tag, i1, i2, i2 - i1, j2 - j1,
                 "   <- zeros; probably paragraph padding" if pad else ""))
        n += max(i2 - i1, j2 - j1)
    return n


def main(argv):
    cfg = tomllib.load(open(argv[0], "rb"))
    root = project.find()
    build = root / project.get("layout.build")
    only = None
    at = None
    runs = "--runs" in argv
    for i, a in enumerate(argv):
        if a == "--only" and i + 1 < len(argv):
            only = argv[i + 1].upper()
        if a == "--at" and i + 1 < len(argv):
            at = int(argv[i + 1], 0)

    first = project.get("target.first_para")
    orig = load_image((root / project.get("target.image")).read_bytes())
    # The map's name is `link.toml`'s `map_file`, which dgroup.py and mapcmp.py
    # both read from there. This tool held its own copy of the value, which is a
    # second copy of one answer -- and the copy named one target's map, so the
    # tool was silently mapless in any other project.
    named = cfg.get("map_file")
    mapfile = (root / named) if named else None
    if mapfile is not None and not mapfile.exists():
        mapfile = build / named.replace(chr(92), '/').rsplit('/', 1)[-1]
    text = mapfile.read_text() if mapfile is not None and mapfile.exists() else None
    exe = exe_path = None
    for p in build.glob("*.EXE"):
        exe_path = p
        exe, text = load_image(p.read_bytes()), text or (p.with_suffix(".MAP")).read_text()
    if exe is None or text is None:
        raise SystemExit("need a linked .EXE and its .MAP in %s -- build with /GD" % build)
    project.fresh(exe_path)

    if at is not None:
        od = (project.get("target.dgroup_para", quiet=True) or 0) * 16
        ug = map_dgroup(text)
        if ug is None:
            raise SystemExit("the map names no data symbol -- cannot locate DGROUP")
        ud = ug * 16
        print("original DGROUP +%04x: %s" % (at, orig[od + at:od + at + 32].hex()))
        print("ours     DGROUP +%04x: %s" % (at, exe[ud + at:ud + at + 32].hex()))
        return 0

    ours = map_segments(text)
    skip = {s.upper() for s in cfg.get("skip", ["DOS", "OBJECTS", "SYSTEM"])}
    total = 0
    for name, base, length in extents(cfg["segments"], cfg["end_at"], first):
        if name in skip or name not in ours or (only and name != only):
            continue
        a = orig[base:base + length]
        b = exe[ours[name]:ours[name] + length]
        total += (report_runs if runs else report_bytes)(name, a, b)
    print("%d differing byte(s) in the linked image" % total)
    return 0


if __name__ == "__main__":
    if not sys.argv[1:]:
        raise SystemExit(__doc__)
    try:
        sys.exit(main(sys.argv[1:]))
    except project.Stale as exc:
        raise SystemExit('STALE: %s' % exc)
