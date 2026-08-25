r"""Pair the original's absolute data references with ours, and report the shift.

    python kit/tools/pascal/dsmap.py SPANS.toml 003
    python kit/tools/pascal/dsmap.py SPANS.toml 003 --all   every site, not a summary

WHY A COVERAGE WALK CANNOT ANSWER THIS. A global that sits four bytes out of
place changes two bytes of every instruction that reads it, and the walk's
tolerance forgives a two-byte hole -- until a run of consecutive references
leaves it nothing to resynchronise on, and then it gives up for hundreds of
bytes and reports them as a code difference. On this target's part 003 that
produced a 476-byte span whose every difference was one four-byte shift.

So this measures the shift directly. For each absolute `[disp16]` reference in
the original's user segments it finds our copy of the same instruction -- by
anchoring on the bytes BEFORE it, which must match uniquely -- and reports our
displacement beside the original's. Grouped by delta, the output names the
regions: a delta of zero is data in the right place, and a block of one non-zero
delta is a run of variables whose predecessor is the wrong SIZE.

READ IT AS A BOUNDARY, NOT A LIST. The useful reading is where the delta
CHANGES: the highest original offset with delta 0 and the lowest with delta N
bracket the declaration that is wrong, and its unit is whichever one owns that
range. One boundary is worth more than a hundred rows.

AND IT DECODES FROM PROLOGUES, not from the segment base. Decoding from the base
starts in the middle of whatever instruction happens to be there, and doing so
manufactured eleven spurious pairs on the first part measured. The prologue is
the one address in a code segment that is certainly an instruction boundary.

A NOTE ON WHAT THAT DID NOT EXPLAIN, because the first draft of this docstring
claimed it did. A cluster of thirty-eight sites reporting one large shift LOOKED
like a decoding artefact and was written up as one before it was checked; it
survived the fix, and reading two of the sites showed `CMP BYTE PTR [$E903],0`
and `MOV WORD PTR [$E906],AX` -- genuine references, genuinely shifted. A tidy
explanation for a suspicious number is not a measurement.

WHAT IT CANNOT DO. An instruction whose preceding bytes are not unique is
skipped rather than guessed -- see spanwhy.py for what taking the first match
costs -- so the site count is a lower bound. And a reference the original makes
inside code we transcribed differently has no counterpart at all; those show as
unpaired.
"""
import collections
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[0]))
import project                                    # noqa: E402
from substrate import align, disasm               # noqa: E402

try:
    import tomllib
except ModuleNotFoundError:                       # pragma: no cover -- 3.11+
    import tomli as tomllib                       # type: ignore

# mod=00, r/m=110 is the absolute disp16 form; A1/A3 are the AX short forms.
SHORT = (0xA0, 0xA1, 0xA2, 0xA3)


ENTRY = re.compile(b"\xc8..\x00|\x55\x89\xe5|\x55\x8b\xec", re.S)


def sites(md, img, lo, hi):
    """Every absolute data reference in [lo, hi), as (address, disp offset).

    THE WALK STARTS AT EACH PROLOGUE, not at the segment base. Decoding from the
    base is decoding from the middle of whatever instruction happens to be
    there, and the first version of this did exactly that -- eleven spurious
    pairs on the first part measured.

    Overlapping walks are deduplicated by address, so a routine reached from two
    prologue candidates costs nothing.
    """
    out = {}
    for m in ENTRY.finditer(img[lo:hi]):
        start = lo + m.start()
        for at, raw, txt in disasm.walk(md, img[start:hi], 0):
            a = start + at
            if a in out:
                break                    # already decoded from here on
            if not txt:
                continue
            if raw[0] in SHORT and len(raw) == 3:
                out[a] = 1
            elif len(raw) >= 4 and (raw[1] & 0xC7) == 0x06 and "0x" in txt:
                out[a] = 2
            else:
                out[a] = None
    return [(a, d) for a, d in sorted(out.items()) if d]


def main(argv):
    cfgpath, part = argv[0], argv[1]
    show_all = "--all" in argv
    cfg = tomllib.load(open(cfgpath, "rb"))
    root = project.find()
    built = root / project.get("layout.built", quiet=True)
    rel = project.get("target.release", quiet=True)
    first = project.get("target.first_para", quiet=True)
    spec = cfg["part"][part]
    oi, _ = align.load_image((root / rel[part]).read_bytes())
    mi, _ = align.load_image((built / spec["exe"]).read_bytes())
    md = disasm.decoder()
    segs = list(spec["segs"]) + [spec["rtl"]]

    pairs, unpaired, ambiguous = [], 0, 0
    for k in range(len(segs) - 1):
        lo, hi = (segs[k] - first) * 16, (segs[k + 1] - first) * 16
        for at, doff in sites(md, oi, lo, hi):
            probe = oi[max(lo, at - 16):at]
            if len(probe) < 16:
                unpaired += 1
                continue
            off, _ = align.locate(probe, mi)
            if off < 0:
                unpaired += 1
                continue
            second, _ = align.locate(probe, mi[off + 1:])
            if second >= 0:
                ambiguous += 1
                continue
            a = int.from_bytes(oi[at + doff:at + doff + 2], "little")
            b = int.from_bytes(mi[off + 16 + doff:off + 16 + doff + 2], "little")
            pairs.append((segs[k], at - lo, a, b))

    print("%d reference(s) paired; %d unpaired, %d skipped as ambiguous"
          % (len(pairs), unpaired, ambiguous))
    by_delta = collections.Counter()
    for _, _, a, b in pairs:
        by_delta[b - a] += 1
    print("\nshift    sites   the original's offsets that carry it")
    for d in sorted(by_delta, key=lambda d: -by_delta[d]):
        offs = sorted({a for _, _, a, b in pairs if b - a == d})
        span = "$%04X..$%04X" % (offs[0], offs[-1]) if offs else ""
        print("  %+5d  %5d   %s  (%d distinct)" % (d, by_delta[d], span, len(offs)))

    # the boundary: for each delta, the highest offset carrying the delta below it
    order = sorted({a for _, _, a, _ in pairs})
    delta_of = {}
    for _, _, a, b in pairs:
        delta_of.setdefault(a, set()).add(b - a)
    print("\nwhere the shift CHANGES, lowest offset first:")
    prev = None
    for a in order:
        ds = delta_of[a]
        cur = sorted(ds)[0] if len(ds) == 1 else None
        if cur != prev:
            print("  $%04X  shift %s%s" % (a, "%+d" % cur if cur is not None
                                           else "AMBIGUOUS %s" % sorted(ds),
                                           "" if prev is None else
                                           "   <-- changed from %+d" % prev))
            prev = cur
    if show_all:
        print("\nevery site:")
        for seg, at, a, b in sorted(pairs, key=lambda r: (r[2], r[0], r[1])):
            print("  %04x:%04x   $%04X -> $%04X  (%+d)" % (seg, at, a, b, b - a))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    main(sys.argv[1:])
