r"""Pair OUR segments to the ORIGINAL's by content, and report the ORDER.

    python kit/tools/pascal/segpair.py SPANS.toml 003
    python kit/tools/pascal/segpair.py SPANS.toml            every part

THE QUESTION NOTHING ELSE ANSWERS: which of our segments is which of theirs.
Every other instrument here is handed that pairing rather than establishing it.
`spans.py` walks each original segment and locates our copy of it, but reports
only how much lined up -- so a unit sitting at the wrong segment number still
matches, and the walk says nothing about where it sat. `dgimage.py` and
`dsmap.py` see the DATA order. Nothing reported the CODE order, and it was
being done by hand off `segmap.py` output and a column of subtraction.

WHY THE ORDER IS A MEASUREMENT. A `uses` clause fixes both layouts and fixes
them opposite ways round -- code segments follow it forwards, DGROUP runs back
down it (see the wiki's `dgroup-order-reverses-uses`). So the code order is an
independent reading of the same source fact, and the two together pin a clause
that either alone leaves ambiguous. On one part the data order was already
right and the code order was not, which no single instrument could have said.

WHAT IT PRINTS, and the two columns are different claims:

  * LOCATED -- where our copy of that original segment actually starts, found
    by content with `align.locate`. This is the honest answer and it does not
    care what either side numbered the segment.
  * SIZE -- the original's paragraph count against ours. The original's comes
    from the NEXT segment's address, so it is the code length rounded up to a
    paragraph; ours is measured the same way, from our own segment starts, so
    the two are on one footing.

A TRANSPOSITION IS THE FINDING, and the coverage walk will not corroborate it.
Two units whose located order is swapped against the original's is a clause in
the wrong order. Measured: one part reports 99.6% aligned with five of its
eight units transposed, because the walk locates each segment by CONTENT and a
unit at the wrong segment number matches just as well. What the order costs is
the DATA layout -- DGROUP runs back down the same clause -- and every absolute
reference that depends on it. So a row here is confirmed or refuted by
`dgimage.py`, never by the walk.

BLIND SPOTS.

A segment we have not written yet cannot be located, and `NOT FOUND` is
reported as exactly that rather than folded into the order -- an absent unit
would otherwise read as a transposition of everything after it.

The SIZE columns are only comparable where the config's segment list is
COMPLETE. A missing row inflates its neighbour by the missing segment's size,
because each length is the next address minus its own -- the failure the
distrust list calls a drifted second copy, and it manufactures findings rather
than going quiet. So a size that disagrees by roughly another unit's worth is
a reason to check the config before believing the row.

And the order is read from our segment STARTS, which come from relocation
targets: a segment nothing refers to has no relocation naming it and does not
appear. That is rare in linked Pascal and it is not impossible.
"""
import pathlib
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[0]))
import project                                    # noqa: E402
from substrate import align                       # noqa: E402

try:
    import tomllib
except ModuleNotFoundError:                       # pragma: no cover -- 3.11+
    import tomli as tomllib                       # type: ignore


def our_segments(raw):
    """Our segment starts, in paragraphs, from the relocation targets.

    The same reading `substrate/segmap.py` prints: a relocated image names
    every segment it refers to, so the distinct target values ARE the layout.
    """
    hdr = struct.unpack_from("<14H", raw, 0)
    nreloc, first = hdr[3], hdr[4] * 16
    # SEGMENT 0 IS ALWAYS A CANDIDATE. It is where the load image starts, and
    # nothing has to relocate to it -- so reading the candidate set from
    # relocation targets alone loses the program's own segment, which made the
    # byte-identical control parts report their main body as NOT FOUND.
    seen = {0}
    for i in range(nreloc):
        off, seg = struct.unpack_from("<HH", raw, hdr[12] + i * 4)
        fa = first + seg * 16 + off
        if fa + 2 <= len(raw):
            seen.add(struct.unpack_from("<H", raw, fa)[0])
    return sorted(seen)


K = 8


def grams(buf):
    """The set of K-byte windows in `buf` -- a shift-invariant fingerprint."""
    return {bytes(buf[i:i + K]) for i in range(max(0, len(buf) - K + 1))}


def score(a, b):
    """Shared K-grams as a share of the smaller fingerprint.

    WITHDRAWN, and recorded here rather than in an appendix because the wrong
    version passed every control: this was first written as POSITIONAL
    similarity -- bytes equal at equal offsets -- on the reasoning that two
    unrelated blocks of x86 give a few percent and a unit against its own
    earlier self stays well above that. It does not. One length difference
    early in a unit misaligns everything after it, so a unit that is largely
    right scores at the noise floor, and three of one part's scene units came
    out NOT FOUND while the byte walk was reporting 87% aligned for the part.

    The control parts could not catch it. They rebuild BYTE IDENTICAL, so
    positional and shift-invariant scoring agree perfectly on them -- a
    control only exercises the case it contains, and every one of these
    contained zero internal shift. The tell was an instrument disagreeing with
    a measurement nobody doubted.

    K-grams are shift-invariant, which is the property the job actually needs:
    a moved routine still contributes its windows.
    """
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


def report(part, spec, orig, mine, raw_mine, first):
    segs = list(spec["segs"]) + [spec["rtl"]]
    ours = our_segments(raw_mine)

    # SCORED AGAINST OUR SEGMENT STARTS, not searched for freely. An earlier
    # version used align.locate and it reported one unit at an offset that was
    # not a segment start at all, and two units at the SAME offset -- then
    # printed `order matches`. A candidate set of our own segment boundaries
    # cannot produce either, because a code segment begins on a paragraph and
    # two units cannot begin on the same one.
    cand = [s * 16 for s in ours]
    table = []
    for k in range(len(segs) - 1):
        lo = (segs[k] - first) * 16
        hi = (segs[k + 1] - first) * 16
        body = orig[lo:hi]
        table.append([segs[k], (hi - lo) // 16, -1, 0.0, len(body), grams(body)])

    # A GLOBAL ASSIGNMENT, best score first, not a best-candidate per row.
    # Greedy per row let a weak claim take a segment a strong one wanted and
    # then reported both as out of order -- on a part that rebuilds BYTE
    # IDENTICAL, which is what the control parts are in the config for.
    # OUR side is fingerprinted over each segment's OWN extent -- its start to
    # the next start -- so a unit is compared with a unit and not with a window
    # of whatever length the original's happened to be.
    ourg = {}
    for j, s in enumerate(ours):
        lo = s * 16
        hi = ours[j + 1] * 16 if j + 1 < len(ours) else len(mine)
        ourg[lo] = grams(mine[lo:hi])
    pairs = sorted(((score(r[5], ourg[at]), at, i)
                    for i, r in enumerate(table) for at in cand),
                   reverse=True)
    taken, done = set(), set()
    for n, at, i in pairs:
        if n < 0.10 or at in taken or i in done:
            continue
        table[i][2], table[i][3] = at, n
        taken.add(at)
        done.add(i)

    def our_size(at):
        para = at // 16
        after = [s for s in ours if s > para]
        return (after[0] - para) if after else None

    print("part %s" % part)
    print("    %-9s %-5s  %-12s %-5s  %-8s %s"
          % ("original", "size", "ours", "size", "same", "order"))

    order = sorted((r[2], r[0]) for r in table if r[2] >= 0)
    rank = {seg: i for i, (_, seg) in enumerate(order)}
    bad = unpaired = 0
    for i, (seg, osize, at, got, length, _fp) in enumerate(table):
        if at < 0:
            why = "NOT FOUND"
            print("    %04x      %-5s  %-12s %-5s  %-8s %s"
                  % (seg, "%03x" % osize, why, "-", "-",
                     "cannot be ordered"))
            unpaired += 1
            continue
        want = len([r for r in table[:i] if r[2] >= 0])
        ok = rank[seg] == want
        if not ok:
            bad += 1
        print("    %04x      %-5s  %04x:0000    %-5s  %3d%%     %s"
              % (seg, "%03x" % osize, at // 16,
                 ("%03x" % our_size(at)) if our_size(at) else "?",
                 int(100 * got),
                 "ok" if ok else "<-- position %d, expected %d"
                 % (rank[seg], want)))

    if bad:
        print("    %d segment(s) OUT OF ORDER -- a uses clause is wrong" % bad)
        print("    THE COVERAGE WALK WILL NOT SHOW THIS. It locates each segment"
              " by content, so a unit at the wrong segment number still matches:"
              " one part reports 99.6% aligned with five of its eight units in"
              " the wrong order. What a wrong order costs is the DATA layout --"
              " DGROUP runs back down the same clause -- and every absolute"
              " reference that depends on it. Read dgimage.py next, not spans.py.")
    elif unpaired:
        print("    the %d paired segment(s) are in the original's order; the %d"
              " above are NOT a pass" % (len(table) - unpaired, unpaired))
    else:
        print("    order matches the original's")


def main(argv):
    cfg = tomllib.load(open(argv[0], "rb"))
    want = argv[1:]
    root = project.find()
    built = root / project.get("layout.built", quiet=True)
    rel = project.get("target.release", quiet=True)
    first = project.get("target.first_para", quiet=True)
    parts = want or [p for p in cfg["part"] if p in rel]

    for part in parts:
        spec = cfg["part"][part]
        orig, _ = align.load_image((root / rel[part]).read_bytes())
        raw_mine = (built / spec["exe"]).read_bytes()
        mine, _ = align.load_image(raw_mine)
        report(part, spec, orig, mine, raw_mine, first)


if __name__ == "__main__":
    if not sys.argv[1:]:
        raise SystemExit(__doc__)
    main(sys.argv[1:])
