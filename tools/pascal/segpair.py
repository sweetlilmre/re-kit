r"""Pair OUR segments to the ORIGINAL's by content, and report the ORDER.

    python kit/tools/pascal/segpair.py SPANS.toml 003
    python kit/tools/pascal/segpair.py SPANS.toml            every part
    python kit/tools/pascal/segpair.py --pair OLD.EXE NEW.EXE

TWO DRIVERS, ONE ENGINE. The config form pairs a REBUILD against the original
it is a rebuild of. `--pair` pairs any two MZ files against each other and
needs no config, no project and no segment list: both sides' segment starts
come from their own relocation targets, the same reading `substrate/segmap.py`
prints. That is the form to reach for on the FIRST day of a new version --
where the question is not "did my build land" but "which of this version's
segments is which of the last one's, and which are new".

WHAT `--pair` ADDS THAT THE CONFIG FORM CANNOT SAY. A rebuild has one segment
per original segment by construction, so the config form only ever reports a
pairing or a miss. Two RELEASES do not: a version can add a unit, drop one, or
split one, so `--pair` reports the unmatched segments on BOTH sides as findings
in their own right -- a right-hand segment nothing paired with is new code, and
that is usually the first thing worth reading.

THE SIMILARITY COLUMN IS NOT A DIFF. It is the share of K-grams the two
segments share, so 100% means "no window of eight bytes is unique to either",
which a recompile of unchanged source against a moved DGROUP will not reach.
Read it as a ranking, and confirm a claim of "unchanged" with a byte walk.

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


def relocation_sites(raw):
    """File offsets of every relocated WORD in an MZ file."""
    hdr = struct.unpack_from("<14H", raw, 0)
    nreloc, first = hdr[3], hdr[4] * 16
    out = []
    for i in range(nreloc):
        off, seg = struct.unpack_from("<HH", raw, hdr[12] + i * 4)
        fa = first + seg * 16 + off
        if fa + 2 <= len(raw):
            out.append(fa)
    return out, first


def masked(raw):
    """The load image with every relocated word zeroed.

    WITHOUT THIS, A CROSS-BINARY SIMILARITY IS NOISE. A relocated word holds a
    load-time segment value, so every one of them differs between two links of
    the same source -- and an eight-byte window is destroyed by a single
    differing byte. Measured on this corpus: an unchanged unit compared across
    two RELEASES scored 22% unmasked and 96% masked, and the unmasked figure
    would have been read as a rewritten unit. The same reasoning is `rtl.py`'s,
    and the same reasoning the compare engine's `.OBJ` rule rests on: where a
    byte's value is decided later, its value is not evidence.

    Its BLIND SPOT is the other half of the problem and there is no cheap fix
    for it: a DGROUP displacement is a plain 16-bit constant, not a relocation,
    so a unit whose data merely MOVED still scores below one whose code did.
    Read a middling score as "look at this", never as "this changed".
    """
    sites, _ = relocation_sites(raw)
    buf = bytearray(raw)
    for fa in sites:
        buf[fa:fa + 2] = b"\0\0"
    return bytes(buf)


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


def pair_files(old_path, new_path, floor=0.10):
    """Pair two MZ files' segments against each other, by content.

    Neither side is privileged: both segment lists come from the files' own
    relocation targets, and the assignment is the same global best-first one
    the config driver uses. Prints one row per LEFT segment, then the RIGHT
    segments nothing claimed -- which on a version bump is the new code.
    """
    def segments_of(path):
        raw = pathlib.Path(path).read_bytes()
        starts = our_segments(raw)
        # MASKED, and see `masked()` for why an unmasked cross-binary score is
        # not a measurement. The segment STARTS are read from the unmasked
        # file, because zeroing the words is exactly what would erase them.
        image, _ = align.load_image(masked(raw))
        out = []
        for j, s in enumerate(starts):
            lo = s * 16
            hi = starts[j + 1] * 16 if j + 1 < len(starts) else len(image)
            out.append((s, hi - lo, grams(image[lo:hi])))
        return out

    left = segments_of(old_path)
    right = segments_of(new_path)

    pairs = sorted(((score(l[2], r[2]), i, j)
                    for i, l in enumerate(left)
                    for j, r in enumerate(right)), reverse=True)
    lmap, taken = {}, set()
    for n, i, j in pairs:
        if n < floor or i in lmap or j in taken:
            continue
        lmap[i] = (j, n)
        taken.add(j)

    print("%s  ->  %s" % (pathlib.Path(old_path).name,
                          pathlib.Path(new_path).name))
    print("    %-9s %-7s  %-9s %-7s  %s"
          % ("left", "bytes", "right", "bytes", "same"))
    order_ok = True
    last = -1
    for i, (seg, size, _fp) in enumerate(left):
        if i not in lmap:
            print("    %04x      %-7d  %-9s %-7s  %s"
                  % (seg, size, "NOT FOUND", "-", "-"))
            continue
        j, n = lmap[i]
        rseg, rsize, _ = right[j]
        flag = ""
        if j < last:
            flag, order_ok = "   <-- OUT OF ORDER", False
        last = j
        print("    %04x      %-7d  %04x      %-7d  %3d%%%s"
              % (seg, size, rseg, rsize, int(100 * n), flag))

    spare = [right[j] for j in range(len(right)) if j not in taken]
    if spare:
        print("    %d right-hand segment(s) NOTHING PAIRED WITH -- new code:"
              % len(spare))
        for seg, size, _ in spare:
            print("        %04x      %-7d" % (seg, size))
    if not order_ok:
        print("    the pairing is NOT monotonic: the link order changed, or a"
              " weak row took the wrong partner. Check the low percentages"
              " before believing a reordering.")
    return lmap


def main(argv):
    if argv[0] == "--pair":
        # NO PROJECT AND NO CONFIG on this path, deliberately: the
        # two files are the whole input, so the tool runs in a
        # checkout whose kit.toml still answers for another target.
        pair_files(argv[1], argv[2])
        return
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
