"""Disassemble one address in both images, side by side, on a VERIFIED anchor.

    sitedump.py SPANS.toml PART SEG:OFF[,SEG:OFF...] [--show=N] [--back=N]

WHY THIS EXISTS AND WHY THE VERIFICATION IS THE POINT. Reading a coverage span
means seeing the same instruction in both images, which means finding our copy
of the original's address -- and our copy is not at the same offset, because
everything ahead of it may be a different size. The obvious way is to align a
window and index into it. That is what a scratch version of this tool did, and
it accepted any window whose match SCORE reached the anchor length: sixteen
bytes out of a thousand-and-twenty-four counted as located.

It therefore anchored in the wrong routine and printed a confident side-by-side
of two unrelated pieces of code. Three separate investigations in one session
were derailed by it, and each was caught only by noticing that a constant in
the "our" column could not possibly belong to the routine under study -- a
palette ramp reading +27 and 89 entries where the source plainly said +19 and
221. Nothing in the output said the alignment was weak.

So this tool states the anchor's requirement and checks it: the bytes
immediately BEFORE the address must match EXACTLY in both images. That is what
makes the following bytes comparable. A window score is a similarity measure
and cannot substitute -- similar routines exist, and a palette ramp in one unit
looks very like a palette ramp in another.

If no anchor verifies, this says so and prints nothing else. An honest refusal
is the useful answer; a plausible wrong dump is not.
"""
import sys, tomllib
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
import project                                       # noqa: E402
from substrate import align, disasm                  # noqa: E402

MIN_ANCHOR = 8          # fewer identical bytes than this proves nothing
MAX_ANCHOR = 0x400      # how far back to look for one


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    cfgpath, part, want = argv[0], argv[1], [w for w in argv[2].split(",") if w]
    show = back = None
    for a in argv[3:]:
        if a.startswith("--show="):
            show = int(a.split("=", 1)[1], 0)
        elif a.startswith("--back="):
            back = int(a.split("=", 1)[1], 0)
    show = show if show is not None else 0x30
    back = back if back is not None else MAX_ANCHOR

    cfg = tomllib.load(open(cfgpath, "rb"))
    root = project.find()
    first = project.get("target.first_para", quiet=True)
    spec = cfg["part"][part]
    orig, _ = align.load_image(
        (root / project.get("target.release", quiet=True)[part]).read_bytes())
    mine, _ = align.load_image(
        (root / project.get("layout.built", quiet=True) / spec["exe"]).read_bytes())
    segs = sorted(set(list(spec["segments"]) + [spec["end_at"]]))
    md = disasm.decoder()
    rc = 0

    for w in want:
        s, o = w.split(":")
        seg, off = int(s, 16), int(o, 16)
        if seg not in segs:
            print("\n=== %04x:%04x -- segment not in %s ===" % (seg, off, cfgpath))
            rc = 1
            continue
        b = (seg - first) * 16
        hit = anchor(orig, mine, b, off, back)
        if hit is None:
            print("\n=== %04x:%04x -- NO VERIFIED ANCHOR ===" % (seg, off))
            print("    No run of %d+ bytes before this address is identical in"
                  " both images," % MIN_ANCHOR)
            print("    so nothing here can be compared instruction by"
                  " instruction. Widen with")
            print("    --back, or read the original alone -- but do not trust a"
                  " score-based match.")
            rc = 1
            continue
        d, at, n = hit
        note = ""
        if n > 1:
            note = ("  -- AMBIGUOUS, %s places in our image carry these same"
                    " bytes" % ("9+" if n > 8 else str(n)))
            rc = 1
        print("\n=== %04x:%04x (anchored on %d identical byte(s) before it)%s ==="
              % (seg, off, d, note))
        if n > 1:
            print("    The right column may be a DIFFERENT occurrence of the"
                  " same pattern.")
            print("    Widen the anchor with --back, or confirm any reading"
                  " here by measurement.")
        dump(md, orig[b + off - d:b + off + show],
             mine[at:at + d + show], off - d)
    return rc


def anchor(orig, mine, base, off, back):
    """Find our copy of `off` by a UNIQUE exact match of the bytes preceding it.

    Returns (length, index into `mine`, occurrences). Longest run wins -- a
    longer identical run is stronger evidence -- and the count is carried out
    so the caller can say when it is more than one.

    EXACTNESS IS NOT UNIQUENESS, and that distinction cost a wrong conclusion.
    An earlier version of this function accepted any exact match and reported
    it without qualification. In a `case` dispatch whose seven arms each begin

        LEA DI,[BP-x] / PUSH SS / PUSH DI / LES DI,[BP-y] / PUSH ES / PUSH DI

    an eight-byte anchor matches all seven, the aligner returns whichever it
    prefers, and the dump then compares one arm against another. It read as
    the original calling a handler directly where we called through a
    procedure variable; naming the routines directly measured 6 bytes WORSE,
    which is how the ambiguity was found rather than by the tool saying so.
    """
    best = None
    for d in range(MIN_ANCHOR, back, 8):
        if off - d < 0:
            break
        w = orig[base + off - d:base + off - d + align.WINDOW]
        if len(w) < MIN_ANCHOR:
            break
        at, _score = align.locate(w, mine)
        if at < 0:
            continue
        pat = orig[base + off - d:base + off]
        if pat != mine[at:at + d]:
            continue
        n, i = 0, mine.find(pat)
        while i >= 0 and n < 9:
            n += 1
            i = mine.find(pat, i + 1)
        best = (d, at, n)                       # keep going: prefer a longer run
        if n == 1:                              # unique already; longer adds nothing
            return best
    return best


def dump(md, a, b, start):
    left = {ad: t or "??" for ad, _, t in disasm.walk(md, a, start)}
    right = {ad: t or "??" for ad, _, t in disasm.walk(md, b, start)}
    for ad in sorted(set(left) | set(right)):
        x, y = left.get(ad, "??"), right.get(ad, "??")
        print("  %s %04x %-34s | %s" % ("*" if x != y else " ", ad, x, y))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
