r"""Count a part's floating-point sites on both sides, and name the units that differ.

    python kit/tools/pascal/fpusites.py SPANS.toml 003
    python kit/tools/pascal/fpusites.py SPANS.toml           every part
    python kit/tools/pascal/fpusites.py SPANS.toml 003 --diff WHERE the counts part

WHAT MAKES THIS MEASURABLE. Under `{$E+}` -- Borland's default -- every 80x87
instruction ships with its `WAIT ESC` prefix overwritten by a two-byte
`INT $34..$3E`, so what is in the file is emulator traps and a count of them is a
count of floating-point sites. Under `{$N-}` there are NONE: the compiler emits
no 80x87 instructions at all and every `Real` operation becomes a far call into
the software six-byte-Real library. **A trap is positive evidence of $N+, not
evidence against it** -- which is the opposite of how it reads the first time,
and the reason this tool exists.

So a part whose trap count is lower than the original's has a unit compiled
`$N-` that the original compiled `$N+`, and the ORIGINAL's per-segment column
names it: the segment with the traps is the unit that wants the switch. Found
four such units on one target in a single run, worth 890 bytes of coverage
across two parts -- and the same switch has twice turned out to be the pacing
defect as well, because the two libraries are not equally fast.

NOTHING HERE IS ABOUT GAINING A COPROCESSOR. Both builds run Turbo Pascal's
emulator over the same traps. `$N` decides which CODE is emitted, never whether
an FPU is present, and `$E` is not involved.

OUR SIDE IS REPORTED AS A TOTAL ONLY, deliberately. The segment map in the
config is the ORIGINAL's, and attributing our trap addresses to it is only sound
where the two layouts agree -- on a part whose units are the wrong size it
produces a per-segment column that looks authoritative and is fiction. An
earlier version printed one anyway and it had to be discounted in the same
commit that used its totals. The totals are layout-independent, so they are what
this prints.

`--diff` LOCALISES A COUNT DIFFERENCE WITHOUT NEEDING EITHER LAYOUT. A count
says a unit has the wrong switch; it does not say where, and the obvious next
step -- pair our trap addresses against the original's segment list -- is the
fiction above. So this diffs the two streams of trap NUMBERS instead. Each trap
carries which 80x87 escape opcode it replaced (`INT $35` is `ESC D9`), so the
sequence of numbers is a fingerprint of the floating-point operations in order,
and it survives every address shift between the two builds. `difflib` over those
two sequences reports each run our build has too many or too few of, with the
address on both sides, and the original's address falls inside whichever segment
the map does name -- so the unit is identified from the ORIGINAL's layout, which
is the one the config is entitled to describe.

WHY THIS IS WORTH A MODE OF ITS OWN: the coverage walk cannot see this class at
all. Measured on part 006, where P6S1 recomputed two `Abs` calls the original
had already stored in variables -- two extra `ESC D9` sites and six extra bytes
-- `spans.py` reported **9229 of 10160 aligned either way**, byte for byte the
same number, because the extra instructions sat inside a stretch the walk had
already given up on. The trap count moved from 98 to 96 and matched exactly.
A defect invisible to the byte walk and exact to this one is the reason to keep
both.

BLIND SPOT, AND IT IS THE ONE THAT MATTERS: the diff assumes the two builds lay
their units down in the SAME ORDER. Where they do not, a moved unit reads as a
long MISSING run followed by a long EXTRA one, and neither names a defect --
the operations are all present, in a different place. Measured: on a part whose
units are known to be in the wrong order the report was `MISSING 32`, `EXTRA
15`, `MISSING 3`, `EXTRA 8`, netting to the true -12 but localising nothing.
The tell is a run far larger than the net difference. Fix the ORDER first, with
`dsmap.py` and `dgimage.py`, and come back to this. A single run whose length
equals the net difference is the case this mode answers, and it answered two
parts in one session that way.
"""
import collections
import difflib
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

TRAP = re.compile(b"\xcd[\x34-\x3e]", re.S)


def stream(img):
    """Every trap in load order: (offset, INT number)."""
    return [(m.start(), img[m.start() + 1]) for m in TRAP.finditer(img)]


def where(off, segs, first):
    """Name the ORIGINAL segment an offset falls in, as SEG:OFF."""
    for k in range(len(segs) - 1):
        base = (segs[k] - first) * 16
        if base <= off < (segs[k + 1] - first) * 16:
            return "%04x:%04x" % (segs[k], off - base)
    base = (segs[-1] - first) * 16
    if off >= base:
        return "%04x:%04x" % (segs[-1], off - base)
    return "  before:%05x" % off


def diff(orig, mine, segs, first):
    """Report each run of traps the two streams do not share.

    The comparison is over the INT NUMBERS only -- addresses shift between the
    two builds and the numbers do not -- so a report here is a claim about the
    floating-point OPERATIONS, not about where they sit.
    """
    o, m = stream(orig), stream(mine)
    sm = difflib.SequenceMatcher(None, [n for _, n in o], [n for _, n in m],
                                 autojunk=False)
    runs = [op for op in sm.get_opcodes() if op[0] != "equal"]
    if not runs:
        print("           the two trap streams are IDENTICAL, opcode for opcode")
        return
    for tag, i1, i2, j1, j2 in runs:
        if tag in ("delete", "replace") and i2 > i1:
            at = where(o[i1][0], segs, first)
            print("           MISSING %d at original %s  (int %s)"
                  % (i2 - i1, at,
                     " ".join("%02x" % n for _, n in o[i1:i2][:8])))
        if tag in ("insert", "replace") and j2 > j1:
            near = where(o[i1][0], segs, first) if i1 < len(o) else "end"
            print("           EXTRA   %d in ours at +%05x, original side %s  (int %s)"
                  % (j2 - j1, m[j1][0], near,
                     " ".join("%02x" % n for _, n in m[j1:j2][:8])))


def main(argv):
    cfg = tomllib.load(open(argv[0], "rb"))
    argv = list(argv)
    show = "--diff" in argv
    argv = [a for a in argv if a != "--diff"]
    want = argv[1:]
    root = project.find()
    built = root / project.get("layout.built", quiet=True)
    rel = project.get("target.release", quiet=True)
    first = project.get("target.first_para", quiet=True)
    parts = want or [p for p in cfg["part"] if p in rel]

    for part in parts:
        spec = cfg["part"][part]
        orig, _ = align.load_image((root / rel[part]).read_bytes())
        mine, _ = align.load_image((built / spec["exe"]).read_bytes())
        segs = list(spec["segs"]) + [spec["rtl"]]

        per, user = collections.Counter(), 0
        for m in TRAP.finditer(orig):
            a = m.start()
            for k in range(len(segs) - 1):
                if (segs[k] - first) * 16 <= a < (segs[k + 1] - first) * 16:
                    per["%04x" % segs[k]] += 1
                    user += 1
                    break
        o_total = len(TRAP.findall(orig))
        m_total = len(TRAP.findall(mine))
        verdict = ""
        if m_total < o_total:
            verdict = ("   <-- %d FEWER: a unit is $N- that the original built $N+"
                       % (o_total - m_total))
        elif m_total > o_total:
            verdict = ("   <-- %d MORE: a unit is $N+ that the original built $N-"
                       % (m_total - o_total))
        print("part %-7s original %3d, ours %3d%s" % (part, o_total, m_total, verdict))
        print("           the original's %d user-code site(s), by segment: %s"
              % (user, ", ".join("%s x%d" % (k, v) for k, v in sorted(per.items()))
                 or "none"))
        if show:
            diff(orig, mine, segs, first)


if __name__ == "__main__":
    if not sys.argv[1:]:
        raise SystemExit(__doc__)
    main(sys.argv[1:])
