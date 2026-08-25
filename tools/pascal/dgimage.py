r"""Compare the two builds' INITIALISED data byte for byte, and say where they part.

    python kit/tools/pascal/dgimage.py SPANS.toml 003
    python kit/tools/pascal/dgimage.py SPANS.toml              every part
    python kit/tools/pascal/dgimage.py SPANS.toml 003 --runs   the longest differing runs
    python kit/tools/pascal/dgimage.py SPANS.toml 003 0x100 0x180   dump a range side by side

THE THIRD INSTRUMENT, and it exists because the other two are blind to the same
thing. `spans.py` walks CODE segments, so wrong DATA costs it nothing -- 12.5KB
of a shape table was carved from the wrong file offset on one target and the
coverage number never moved. `dsmap.py` pairs data REFERENCES, so it cannot see
data nothing references -- and the bytes that go missing are very often exactly
that: a band of a table nobody draws, a file record nobody reads, a zeroed
27th slot.

WHAT IT READS. Everything from the DGROUP paragraph to the end of the load image
is the initialised part of the data segment, written into the EXE where it can
simply be compared. The paragraph is found from the runtime's own prologue --
`MOV DX,<DGROUP> / MOV DS,DX` -- so no map file is needed.

HOW TO USE THE OUTPUT. Two numbers and one address:

  * the two LENGTHS. A shorter one of ours is data the original has and we do
    not, and the difference is usually a round number with a meaning: 128 is an
    untyped `file`, 4 a pointer, 2 a Word. Three separate defects on one target
    were found by reading that difference alone.
  * the FIRST DIFFERING OFFSET. Work from the lowest divergence upwards; a
    single missing declaration displaces everything after it, so the first one
    is the only one worth reading.
  * whether ours RESYNCHRONISES at a fixed shift. If it does, the gap is one
    missing or extra block of that size and nothing else is wrong; if it does
    not, the CONTENT differs and it is a carve or a value problem.

A REMAINING DIFFERENCE OF TWO BYTES IS PROBABLY THE HARNESS. A test harness that
does a `WriteLn` puts its line terminator in the data segment; on this target it
lands past everything else and displaces nothing. Anything a harness declares
BEFORE that, though, sits at the FRONT of the uninitialised region and moves
every variable in the part under test -- see the note on EXIT_PROC in the
harness generator.
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[0]))
import project                                    # noqa: E402
from substrate import align                       # noqa: E402

try:
    import tomllib
except ModuleNotFoundError:                       # pragma: no cover -- 3.11+
    import tomli as tomllib                       # type: ignore

PROLOGUE = re.compile(b"\xba(..)\x8e\xda", re.S)


def dgroup(img):
    """The initialised data segment, from the runtime prologue's DGROUP value."""
    m = PROLOGUE.search(img)
    if not m:
        return None
    return img[int.from_bytes(img[m.start() + 1:m.start() + 3], "little") * 16:]


def report(part, a, b, runs=False, lo=None, hi=None):
    n = min(len(a), len(b))
    note = ""
    if len(a) != len(b):
        note = ("   <-- ours is %d byte(s) %s" %
                (abs(len(a) - len(b)), "SHORT" if len(b) < len(a) else "LONG"))
    print("part %-7s original %6d bytes, ours %6d%s" % (part, len(a), len(b), note))

    first = next((i for i in range(n) if a[i] != b[i]), None)
    if first is None and len(a) == len(b):
        print("           identical")
        return
    total = sum(1 for i in range(n) if a[i] != b[i])
    print("           %d byte(s) differ; first at $%04X"
          % (total, first if first is not None else n))
    if first is not None:
        for shift in (128, -128, 132, -132, 4, -4, 2, -2, 6, -6, 10, -10, 24, -24):
            if 0 <= first - shift and a[first:first + 64] == b[first - shift:first - shift + 64]:
                print("           ours RESYNCHRONISES at a shift of %+d -- one block of "
                      "that size, not a content problem" % -shift)
                break
        else:
            print("           no fixed shift resynchronises it: the CONTENT differs, "
                  "not just the position")
    if runs:
        out, i = [], 0
        while i < n:
            if a[i] != b[i]:
                j = i
                while j < n and a[j] != b[j]:
                    j += 1
                out.append((i, j - i))
                i = j
            else:
                i += 1
        out.sort(key=lambda r: -r[1])
        print("           %d differing run(s); the longest:" % len(out))
        for s, l in out[:8]:
            print("             $%04X  %5d byte(s)" % (s, l))
    if lo is not None and hi is not None:
        for i in range(lo, min(hi, n), 16):
            x, y = a[i:i + 16].hex(), b[i:i + 16].hex()
            print("  %04x  %-32s %-32s %s" % (i, x, y, "" if x == y else "<<"))


def main(argv):
    cfg = tomllib.load(open(argv[0], "rb"))
    rest = [x for x in argv[1:] if not x.startswith("--")]
    runs = "--runs" in argv
    part = rest[0] if rest else None
    lo = int(rest[1], 0) if len(rest) > 2 else None
    hi = int(rest[2], 0) if len(rest) > 2 else None
    root = project.find()
    built = root / project.get("layout.built", quiet=True)
    rel = project.get("target.release", quiet=True)
    parts = [part] if part else [p for p in cfg["part"] if p in rel]
    for p in parts:
        a = dgroup(align.load_image((root / rel[p]).read_bytes())[0])
        b = dgroup(align.load_image((built / cfg["part"][p]["exe"]).read_bytes())[0])
        if a is None or b is None:
            print("part %-7s no runtime prologue found -- cannot locate DGROUP" % p)
            continue
        report(p, a, b, runs, lo, hi)


if __name__ == "__main__":
    if not sys.argv[1:]:
        raise SystemExit(__doc__)
    main(sys.argv[1:])
