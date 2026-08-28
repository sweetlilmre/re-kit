r"""What CHANGED between the same segment in two builds of one program.

    python kit/tools/pascal/verdiff.py OLD.EXE 154d NEW.EXE 173d
    python kit/tools/pascal/verdiff.py OLD.EXE 154d NEW.EXE 173d --all
    python kit/tools/pascal/verdiff.py OLD.EXE NEW.EXE --pairs PAIRS.toml

THE QUESTION IT ANSWERS, and nothing else here answers it: a reconstruction of
version N is finished and version N+1 is the new target, so most of the source
is already right and the job is to find the DELTA. Every other instrument in
this tier compares a REBUILD against the original it is a rebuild of, and
answers "did my build land". This one compares two ORIGINALS -- or a finished
build of the old one against the new one, which is the same comparison -- and
answers "what did the author change".

WHY A HISTOGRAM OF DELTAS AND NOT A LIST OF DIFFERENCES. Two versions of one
unit differ in three unrelated ways at once, and a flat list buries the useful
one under the other two:

  * a RECORD grew, so every field access past the insertion moves by the same
    amount. Shows up as one byte differing inside a ModRM displacement, and
    the SAME delta at dozens of sites.
  * DGROUP moved, so every absolute data reference moves. Two bytes, one
    delta, again at dozens of sites.
  * the CODE actually changed. Anything else -- and it is the only kind worth
    reading a disassembly for.

So the sites are bucketed by delta and the buckets are printed largest first.
A bucket of forty sites at +$20 is one field inserted in one record, and it is
worth more than the forty lines it replaces. MEASURED, first use: the whole of
one loader's divergence from its predecessor was two buckets -- +$20 at every
`Song.` field access and +$a8 at its one string constant -- and the third
bucket, holding two sites, was the entire real change.

RELOCATIONS ARE MASKED ON BOTH SIDES before anything is compared, for the
reason `segpair.masked` gives: a relocated word holds a load-time segment
value, so unmasked it is a difference with no meaning, at every far call.

WHAT IT CANNOT SEE, and the second one has bitten:

  * WHICH FIELD moved. A delta bucket says a record grew by N bytes somewhere
    below the lowest displacement in the bucket; it cannot say where. Pair it
    with the type's VMT size word, which names the new total exactly.
  * A CHANGE THAT DID NOT MOVE ANYTHING. Two same-length instructions swapped,
    or a constant changed to another of the same width, appear as an ordinary
    bucket of one -- correct, but indistinguishable at a glance from an
    off-by-one displacement. The `--all` listing is what to read then.
  * ALIGNMENT IS DIFFLIB'S. Where the two versions genuinely diverge for a
    long stretch, difflib will pair whatever it can, and a coincidental match
    inside the divergence splits one real change into several. A bucket whose
    sites are dense in one address range is a candidate for that, not
    necessarily a systematic shift.
"""
import pathlib
import struct
import sys
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[0]))
import project                                    # noqa: E402
from substrate import align                       # noqa: E402
from segpair import masked, our_segments          # noqa: E402


def segment(path, seg, first):
    """(bytes of that segment, its paragraph extent) from an MZ file.

    The extent is the NEXT relocation-target segment's address minus this one's
    -- the same reading `segmap.py` prints -- so a caller never has to hand a
    length in, and a segment nothing refers to is folded into its predecessor,
    which is the documented blind spot of reading a layout this way.
    """
    raw = pathlib.Path(path).read_bytes()
    starts = our_segments(raw)
    image, _ = align.load_image(masked(raw))
    rel = seg - first
    if rel not in starts:
        raise SystemExit("  %s has no segment %04x -- its segment starts are "
                         "%s" % (pathlib.Path(path).name, seg,
                                 " ".join("%04x" % (s + first)
                                          for s in starts)))
    j = starts.index(rel)
    lo = rel * 16
    hi = starts[j + 1] * 16 if j + 1 < len(starts) else len(image)
    return image[lo:hi]


def deltas(old, new):
    """Every difference between two segments, as (offset, old, new) triples.

    `align.regions` supplies the alignment -- difflib, with its fixup rules --
    and this reads the two sides of each gap back out. The `mask` and zero
    rules there are about a REBUILD's pending fixups and cannot fire between
    two finished binaries, so what comes back is every gap difflib found.
    """
    import difflib
    sm = difflib.SequenceMatcher(None, old, new, autojunk=False)
    out, oi, ni = [], 0, 0
    for a, b, n in sm.get_matching_blocks():
        if a > oi or b > ni:
            out.append((oi, old[oi:a], new[ni:b]))
        oi, ni = a + n, b + n
    return out


def classify(o, n):
    """(kind, delta, old value) for one gap. `delta` is None where no number.

    A ModRM displacement is ONE byte and a data reference is TWO, and those two
    widths carry almost every systematic difference between two builds. Anything
    else is called `code` and is left for a person to read.
    """
    if len(o) == 1 and len(n) == 1:
        # UNSIGNED, MODULO 256, and that is a correction rather than a choice.
        # A one-byte gap is AMBIGUOUS: it is a ModRM disp8 whose field moved,
        # or it is the LOW HALF of a 16-bit data reference whose high half
        # happened not to change. $0c02 -> $0caa differs in one byte only, and
        # read as a signed displacement that is -$58. The first run of this
        # tool reported `disp8 -$58 x48` against HEAPS -- a record shrinking by
        # 88 bytes, in a unit whose source turned out to be unchanged -- beside
        # a `word +$a8` bucket that was the same shift seen through its other
        # half. Two buckets, one cause, and the invented one was the larger.
        # So the delta is reported mod 256 and the caller reconciles it with
        # the word buckets; `report` prints the signed reading beside it.
        return ("byte", (n[0] - o[0]) & 0xFF, o[0])
    if len(o) == 2 and len(n) == 2:
        ov = struct.unpack("<H", o)[0]
        nv = struct.unpack("<H", n)[0]
        d = nv - ov
        return ("word", d - 0x10000 if d > 0x8000 else
                d + 0x10000 if d < -0x8000 else d, ov)
    return ("code", None, None)


def report(oldpath, oldseg, newpath, newseg, first, show_all=False):
    old = segment(oldpath, oldseg, first)
    new = segment(newpath, newseg, first)
    gaps = deltas(old, new)

    buckets = defaultdict(list)
    code = []
    for off, o, n in gaps:
        kind, d, val = classify(o, n)
        if kind == "code":
            code.append((off, o, n))
        else:
            buckets[(kind, d)].append((off, val))

    same = len(old) - sum(len(o) for _, o, _ in gaps)
    print("%s %04x (%d bytes)  ->  %s %04x (%d bytes)"
          % (pathlib.Path(oldpath).name, oldseg, len(old),
             pathlib.Path(newpath).name, newseg, len(new)))
    print("    %d of %d old bytes align; %d gap(s)"
          % (same, len(old), len(gaps)))

    if buckets:
        # Which byte deltas are congruent to a word delta. Such a bucket is
        # almost certainly the low half of the SAME data-reference shift, not a
        # field displacement -- see `classify`.
        wordmod = {d & 0xFF: d for (k, d) in buckets if k == "word"}
        print("    SYSTEMATIC SHIFTS, largest bucket first:")
        for (kind, d), sites in sorted(buckets.items(),
                                       key=lambda kv: -len(kv[1])):
            # THE OLD VALUE IS THE POINT, not the site address. A bucket of
            # displacements says a record grew; the SMALLEST old displacement
            # in it bounds where the growth was inserted, because a field
            # BELOW the insertion does not move and so is not in the bucket.
            # Printing only site addresses hid that, and the insertion point
            # was being recovered by hand from a disassembly.
            vals = sorted({v for _, v in sites})
            if kind == "byte":
                shown = "+$%-4x" % d if d < 128 else "+$%-4x" % d
                note = ""
                if d in wordmod:
                    note = ("   <-- congruent to word +$%x: the LOW HALF of "
                            "that shift, not a field" % wordmod[d])
                elif d > 128:
                    note = "   (as signed: -$%x)" % (256 - d)
            else:
                shown = ("+$%-4x" % d) if d >= 0 else ("-$%-4x" % -d)
                note = ""
            print("      %-5s %s x%-4d  old $%x..$%x   %s%s"
                  % (kind, shown, len(sites), vals[0], vals[-1],
                     " ".join("%04x:$%x" % s for s in sites[:6])
                     + (" ..." if len(sites) > 6 else ""), note))

    if code:
        print("    REAL CHANGES -- %d site(s) that are not a shift:" % len(code))
        for off, o, n in (code if show_all else code[:24]):
            print("      %04x  old %-24s new %s"
                  % (off, o.hex() or "-", n.hex() or "-"))
        if not show_all and len(code) > 24:
            print("      ... %d more; pass --all" % (len(code) - 24))
    else:
        print("    NO real changes: every difference is a shift. This unit's"
              " SOURCE is unchanged.")
    return buckets, code


def main(argv):
    flags = [a for a in argv if a.startswith("--")]
    pos = [a for a in argv if not a.startswith("--")]
    if len(pos) != 4:
        raise SystemExit(__doc__)
    first = project.get("target.first_para", quiet=True)
    report(pos[0], int(pos[1], 16), pos[2], int(pos[3], 16), first,
           show_all="--all" in flags)


if __name__ == "__main__":
    if not sys.argv[1:]:
        raise SystemExit(__doc__)
    main(sys.argv[1:])
