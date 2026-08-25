r"""Count a part's floating-point sites on both sides, and name the units that differ.

    python kit/tools/pascal/fpusites.py SPANS.toml 003
    python kit/tools/pascal/fpusites.py SPANS.toml           every part

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
"""
import collections
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


if __name__ == "__main__":
    if not sys.argv[1:]:
        raise SystemExit(__doc__)
    main(sys.argv[1:])
