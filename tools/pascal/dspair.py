r"""Pair every displacement operand by INSTRUCTION POSITION, not by content.

    python kit/tools/pascal/dspair.py SPANS.toml PART
    python kit/tools/pascal/dspair.py SPANS.toml PART --seg=108b
    python kit/tools/pascal/dspair.py SPANS.toml PART --bp        # stack slots
    python kit/tools/pascal/dspair.py SPANS.toml PART --min=0x300  # hide the low ones

WHAT IT DOES, AND THE PRECONDITION THAT MAKES IT SOUND. Two builds of the same
segment, disassembled in parallel. Wherever an instruction at code offset X
carries a memory displacement on both sides and the two differ, this prints
(theirs, ours) and the shift between them. Runs of consecutive addresses that
carry the same shift are collapsed to one line, so a variable moved by n bytes
is one row however many times the segment reads it.

THE PRECONDITION IS THAT EVERY ROUTINE IS ALREADY THE RIGHT LENGTH. Check it
first, segment by segment, with `progseg.py --prologues=SEG`. Only then is the
instruction at offset X on one side the counterpart of the instruction at
offset X on the other, and only then does a differing operand mean a MISPLACED
OBJECT rather than a drifted address. Run this across a length defect and every
row below it is fiction -- the same failure mode as a masked instruction diff,
for the same reason.

WHY IT BEATS PAIRING BY CONTENT. `dsmap.py` pairs DGROUP references by matching
the shapes around them, which works with no precondition at all and is the
right tool when the code has not converged. The price is that it cannot pair
everything: on one 1,287-byte case it paired 153 references, left 213 unpaired
and skipped 128 as ambiguous, and two of the shifts it did report were
mispairings large enough to look like whole missing arrays. Position pairs
everything or nothing, and says which.

WHAT THE SHIFTS MEAN. A single shift carried by a long contiguous run of THEIR
addresses is one object at the wrong address, and the run's extent is that
object's extent. Where the shift CHANGES is a boundary: read the profile
bottom-up, because a variable at the wrong address moves everything above it
and fixing the lowest one first is the only order that converges. A shift of +0
above a shifted block means the block is misplaced rather than mis-sized, which
narrows it to declaration ORDER. And a run of one address with a shift nothing
else shares is usually not a layout defect at all: check whether the operand is
a runtime entry point (Round against Trunc are 31 bytes apart in TP 7.00's
System segment) before assuming it is data.

--bp SWITCHES TO STACK SLOTS: negative displacements off BP, which is the same
measurement for a routine's locals. There the shifts name declaration order,
alignment (`{$A-}` -- a word at an ODD offset cannot be A-plus) and the
compiler's own hidden temporaries. Read that profile the same way, and expect
one more thing: two arms of an if-statement emitted in the opposite order show
up as a block of slots each paired against the other arm's, which is a branch
sense and not a layout defect.
"""
import collections
import io
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import project                                    # noqa: E402

try:
    import tomllib
except ModuleNotFoundError:                       # pragma: no cover -- 3.11+
    import tomli as tomllib                       # type: ignore

try:
    from capstone import Cs, CS_ARCH_X86, CS_MODE_16
    from capstone.x86 import X86_OP_MEM
except ImportError:                               # pragma: no cover
    Cs = None


def load(path):
    d = pathlib.Path(path).read_bytes()
    return d[int.from_bytes(d[8:10], "little") * 16:]


def scan(md, buf, lo, hi, bp):
    """offset -> displacement, for every DS- (or BP-) relative operand."""
    out = {}
    for i in md.disasm(bytes(buf[lo:hi]), 0):
        for op in i.operands:
            if op.type != X86_OP_MEM or op.mem.segment or not op.mem.disp:
                continue
            d = op.mem.disp
            negative = d < 0
            if negative == bool(bp):
                out[i.address] = d if bp else (d & 0xFFFF)
    return out


def runs(pairs):
    """Collapse consecutive THEIR-addresses carrying one shift into one row."""
    out = []
    for (theirs, ours, seg), n in sorted(pairs.items(), key=lambda kv: (kv[0][2], kv[0][0])):
        shift = ours - theirs
        if out and out[-1]["seg"] == seg and out[-1]["shift"] == shift \
                and 0 <= theirs - out[-1]["hi"] <= 0x40:
            out[-1]["hi"] = theirs
            out[-1]["n"] += n
            continue
        out.append({"seg": seg, "shift": shift, "lo": theirs, "hi": theirs, "n": n})
    return out


def main(argv):
    args = [a for a in argv if not a.startswith("-")]
    if len(args) < 2 or Cs is None:
        sys.stdout.write(__doc__ or "")
        if Cs is None:
            sys.stdout.write("\ncapstone is not installed: uv pip install capstone\n")
        return 2
    bp = "--bp" in argv
    only = None
    # NO FLOOR BY DEFAULT, and the reason is a bug this tool had for one hour.
    # It shipped with a $0300 floor to cut small immediates misread as
    # displacements, and its first validation run reported "every displacement
    # matches" over a defect it had been written to find: two LongInts at $01FE
    # and $0202, 12,800 bytes out of place, both under the floor. A filter that
    # hides a whole address range is not noise reduction, it is a blind spot --
    # and low DGROUP is where initialised data and the first BSS live. Pass
    # --min if a particular segment is noisy; do not make it the default again.
    floor = 0
    for a in argv:
        if a.startswith("--seg="):
            only = int(a.split("=")[1], 16)
        elif a.startswith("--min="):
            floor = int(a.split("=")[1], 0)

    with io.open(args[0], "rb") as fh:
        cfg = tomllib.load(fh)["part"]
    part = args[1]
    if part not in cfg:
        print("part %s is not in %s" % (part, args[0]))
        return 2
    spec = cfg[part]

    try:
        root = project.find()
        release = project.get("target.release")
        built = root / project.get("layout.built")
        first = project.get("target.first_para", quiet=True) or 0x1000
    except project.Missing as exc:
        return project.complain(exc)

    ours_path = built / spec["exe"]
    if not ours_path.exists():
        print("%s is not built" % spec["exe"])
        return 1
    A, B = load(root / release[part]), load(ours_path)

    md = Cs(CS_ARCH_X86, CS_MODE_16)
    md.detail = True
    segs = list(spec["segments"])
    pairs = collections.Counter()
    for k, s in enumerate(segs):
        if only is not None and s != only:
            continue
        lo = (s - first) * 16
        hi = ((segs[k + 1] if k + 1 < len(segs) else spec["end_at"]) - first) * 16
        da, db = scan(md, A, lo, hi, bp), scan(md, B, lo, hi, bp)
        for at, theirs in da.items():
            ours = db.get(at)
            if ours is None or ours == theirs:
                continue
            if not bp and abs(theirs) < floor:
                continue
            pairs[(theirs, ours, "%04x" % s)] += 1

    if not pairs:
        print("part %-6s every %s displacement matches"
              % (part, "BP-relative" if bp else "DS-relative"))
        return 0

    print("part %-6s %d differing %s displacement site(s)"
          % (part, sum(pairs.values()), "BP-relative" if bp else "DS-relative"))
    print("  READ THIS BOTTOM-UP: the lowest wrong address moves everything")
    print("  above it, and fixing it in any other order does not converge.")
    print("  And check progseg.py --prologues=SEG first -- across a routine of")
    print("  the wrong LENGTH every row below the defect is fiction.")
    print("")
    def name(v):
        return "[BP-$%04X]" % -v if v < 0 else "$%04X" % v

    for r in runs(pairs):
        span = name(r["lo"]) if r["lo"] == r["hi"] \
            else ("%s..%s" % (name(r["lo"]), name(r["hi"])))
        print("  seg %s  %-25s  theirs -> ours %+7d   x%d"
              % (r["seg"], span, r["shift"], r["n"]))
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
