r"""Which unaligned spans can editing close, and which are addresses that moved.

    python kit/tools/pascal/spanwhy.py SPANS.toml 006
    python kit/tools/pascal/spanwhy.py SPANS.toml            all parts
    python kit/tools/pascal/spanwhy.py SPANS.toml 006 --show  print the pairs

THE THIRD ANSWER THE COVERAGE WALK CANNOT GIVE. `spans.py` says a span is either
re-expressed assembler or a different statement shape, and that it cannot tell
them apart. There is a third case and it is neither: a span whose every
difference is an ADDRESS. A far call carries its target as segment and offset,
and a reference to a global carries a DGROUP displacement; until our segments
are the original's sizes and our data segment its layout, both differ -- and no
edit to the routine containing them changes that.

It matters because the two need opposite decisions. A real difference is work.
An address difference is a span to leave alone until the layout converges, and
counting it as work sends the next session to read a routine that is already
correct.

THE RULE. A differing instruction pair is an ADDRESS difference when the two
decode to the same mnemonic, occupy the same number of bytes, and every byte
that differs lies in one contiguous run that does NOT include the first byte.
That is the shape of a changed displacement or immediate inside an unchanged
opcode: `9A 4800 EE01` against `9A 4800 2402` is one far call to two segments,
and `8A 85 2F93` against `8A 85 2B93` is one load from two DGROUP offsets.

WHY IT IS NOT JUST "IS IT A CALL". The first version of this rule accepted only
calls and jumps, and it classified every span in one part as real work -- while
the largest two were dominated by far-call targets AND absolute data
displacements, and the data ones failed the test because a MOV is not a call.
The mnemonic is the wrong thing to look at; where the differing bytes SIT inside
the instruction is the right thing.

AND THE ANSWER MOST SPANS ACTUALLY GET IS "THE DEFECT IS UPSTREAM". The
coverage walk forgives short runs of differing bytes, so it does not open a span
until the images have drifted far enough to stop matching at all -- which is
downstream of the instruction whose LENGTH changed. Reading from the span's
start therefore reads correct code. On this target's part 006, twelve of
twenty-one spans traced back to just THREE length changes, between 4 and 1,391
bytes earlier, so the work is three edits and not twelve.

THE `addresses` VERDICT HAS NEVER FIRED ON THIS TARGET, and that is stated here
rather than left for somebody to assume it was tested. It is reachable -- a far
call differing in both segment and offset is four same-length bytes, which the
walk's tolerance does not forgive, so such a span exists -- but an upstream
length change is found first in every span measured so far. Treat a run of
zeroes in that column as untested rather than as evidence.

AND A VERDICT IS TRIAGE, NOT PROOF. The anchor can fail two ways that both end
in a wrong verdict rather than an error. A short probe is not distinctive -- a
sixteen-byte window matched a different routine with the same prologue and frame
size, and 189 bytes of one part's spans were called real when hand-pairing
showed every difference was an absolute address -- so a probe that matches more
than once is now refused. But a LONG probe over a routine that opens with a run
of absolute addresses may not locate at all, and then this falls back to an
earlier prologue and reports that routine's drift instead. Before acting on a
large verdict, pair the two routines by hand from the addresses printed.

WHAT IT CANNOT TELL YOU. A run of two differing bytes at the end of an
instruction is an address here and could be a changed constant -- `ADD AX,$28`
against `ADD AX,$2A` passes this rule and is a real defect. So a span reported
as addresses is a span whose differences are all CONSISTENT with relocation, not
one proved to be. Read the pairs with `--show` before believing a large one, and
treat a span whose differing immediates are small integers as suspect: see the
wiki observation `Borland Pascal emits one instruction per operator`.
"""
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[0]))
import project                                    # noqa: E402
from substrate import align, disasm               # noqa: E402

try:
    import tomllib
except ModuleNotFoundError:                       # pragma: no cover -- 3.11+
    import tomli as tomllib                       # type: ignore

SPAN = re.compile(r"([0-9a-f]{4}):([0-9a-f]{4})\.\.([0-9a-f]{4})\s+(\d+) byte")


def differing_run(a, b):
    """The contiguous run of differing byte positions, or None if not one run."""
    if len(a) != len(b):
        return None
    at = [i for i in range(len(a)) if a[i] != b[i]]
    if not at or at[0] == 0:
        return None
    if at[-1] - at[0] + 1 != len(at):
        return None
    return at[0], at[-1]


ENTRY = re.compile(b"\xc8..\x00|\x55\x89\xe5|\x55\x8b\xec", re.S)


def entries_before(orig, base, lo):
    """Every routine prologue at or before `lo`, NEAREST FIRST.

    ANCHORING ANYWHERE ELSE DESYNCHRONISES THE WALK, and silently. A version of
    this searched backwards for any window of bytes that matched and took the
    FARTHEST one that did; `align.locate` matches happily in the middle of an
    instruction, so the walk decoded from the wrong byte and reported
    differences that were neither in the span nor real -- `fidivr` against
    `add bh` in a routine with no floating point in it. A prologue is the one
    address in a code segment that is certainly an instruction boundary.

    Nearest first and then outwards, because a prologue candidate can be a
    false positive: `C8 xx xx 00` occurs inside data and inside longer
    instructions, which is the blind spot `prologue-scan-endorses-data`
    records. A candidate our image does not contain is simply skipped.
    """
    return [m.start() for m in ENTRY.finditer(orig[base: base + lo + 1])][::-1]


def anchor(orig, base, lo, image):
    """Our copy of the routine containing `lo`, found by its prologue.

    THE PROBE MUST BE LONG, AND THE REASON IS A MEASUREMENT. `align.locate`
    returns the FIRST match, and a short window of a routine's opening bytes is
    not distinctive: a sixteen-byte probe matched a different routine with the
    same prologue and frame size, and 189 bytes of one part's spans were
    reported as real differences when pairing them by hand showed every one was
    an absolute address. So the longest window that still fits before the span
    is tried first, and a probe that matches in MORE THAN ONE place is refused
    outright rather than resolved by taking the first.
    """
    for start in entries_before(orig, base, lo):
        if lo - start > 0x800:
            break
        for win in (0x40, 0x30, 0x20, 0x18):
            if win > lo - start + 4:
                continue
            probe = orig[base + start: base + start + win]
            off, _ = align.locate(probe, image)
            if off < 0:
                continue
            second, _ = align.locate(probe, image[off + 1:])
            if second >= 0:
                continue                      # not distinctive: try a longer one
            return off, start
    return -1, 0


def classify(md, orig, mine, base, lo, hi):
    """Verdict for one span, plus the differing pairs INSIDE it.

    TWO RULES THAT ARE ONLY OBVIOUS AFTER GETTING THEM WRONG.

    The walk must be IN SYNC when it reaches the span, and it is in sync only
    while every instruction pair before it has the same length. A version that
    ignored this anchored several hundred bytes upstream and reported the first
    difference it met on the way -- in a different routine, outside the span,
    and usually the reason that routine has a span of its own. If the lengths
    part company before `lo` there is nothing this tool can say about `hi`, and
    saying so is the honest answer.

    A LENGTH CHANGE BEFORE THE SPAN IS THE ANSWER, NOT A FAILURE. The coverage
    walk forgives short runs of differing bytes, so it does not open a span
    until the two images have drifted far enough to stop matching at all --
    which is DOWNSTREAM of the instruction whose length changed. Where that
    instruction is is the useful output, and on one part it ran between 4 and
    1,391 bytes earlier than the span the walk named.

    And it stops at the first real difference INSIDE the span. One is all a
    span needs to be work, and past it the walk has come apart: a version that
    kept going reported 85 differing instructions inside a 79-byte span, which
    is more pairs than the span has instructions.
    """
    off, start = anchor(orig, base, lo, mine)
    if off < 0:
        return "no prologue to anchor on", []
    span = hi - start
    A = list(disasm.walk(md, orig[base + start: base + start + span], start))
    B = list(disasm.walk(md, mine[off: off + span], start))
    pairs = []
    for a, b in zip(A, B):
        if a[0] >= hi:
            break
        if len(a[1]) != len(b[1]):
            pairs.append((a, b, None))
            if a[0] < lo:
                return "upstream %d" % (lo - a[0]), pairs
            return "real", pairs
        if a[1] == b[1] or a[0] < lo:
            continue
        run = differing_run(a[1], b[1])
        same = a[2] and b[2] and a[2].split()[0] == b[2].split()[0]
        pairs.append((a, b, run))
        if not (run and same):
            return "real", pairs
    if not pairs:
        return "no difference inside the span -- the anchor absorbed it", []
    return "addresses", pairs


def main(argv):
    cfgpath = argv[0]
    want = [a for a in argv[1:] if not a.startswith("--")]
    show = "--show" in argv
    cfg = tomllib.load(open(cfgpath, "rb"))
    root = project.find()
    built = root / project.get("layout.built", quiet=True)
    rel = project.get("target.release", quiet=True)
    first = project.get("target.first_para", quiet=True)
    parts = want or [p for p in cfg["part"] if p in rel]
    md = disasm.decoder()
    here = pathlib.Path(__file__).resolve()

    for part in parts:
        spec = cfg["part"][part]
        orig, _ = align.load_image((root / rel[part]).read_bytes())
        mine, _ = align.load_image((built / spec["exe"]).read_bytes())
        # THE ENCODING IS STATED because this is our own script's stdout, and
        # the RETURN CODE IS CHECKED because the regex below cannot tell a
        # crashed spans.py from a part with no spans -- both give it nothing.
        got = subprocess.run([sys.executable, str(here.parent / "spans.py"),
                              cfgpath, part], capture_output=True, text=True,
                             encoding="utf-8")
        if got.returncode != 0:
            print("part %-7s spans.py FAILED (exit %d) -- this is not a "
                  "measurement:\n%s" % (part, got.returncode,
                                        got.stderr.strip()))
            continue
        rows = SPAN.findall(got.stdout)
        if not rows:
            print("part %-7s spans.py ran and reported no span -- and that is not "
                  "the same as none: check its output by hand" % part)
            continue
        real, addr, up, other = [], [], [], []
        nreal, naddr = 0, 0
        for seg_s, lo_s, hi_s, n_s in rows:
            seg, lo, hi, n = (int(seg_s, 16), int(lo_s, 16),
                              int(hi_s, 16), int(n_s))
            base = (seg - first) * 16
            verdict, pairs = classify(md, orig, mine, base, lo, hi)
            row = (seg, lo, n, len(pairs), pairs)
            if verdict == "real":
                real.append(row)
                nreal += n
            elif verdict.startswith("upstream "):
                up.append((row, int(verdict.split()[1])))
                nreal += n
            elif verdict == "addresses":
                addr.append(row)
                naddr += n
            else:
                other.append((row, verdict))
        print("\npart %s -- %d span(s): %d byte(s) editable, %d byte(s) are "
              "addresses that moved" % (part, len(rows), nreal, naddr))
        for title, rowset in (("REAL differences -- editing can close these", real),
                              ("ADDRESSES ONLY -- leave until the layout converges",
                               addr)):
            if not rowset:
                continue
            print("  %s:" % title)
            for seg, lo, n, ndiff, pairs in rowset:
                print("    %04x:%04x  %4d byte(s)  %d differing instruction(s)"
                      % (seg, lo, n, ndiff))
                if show:
                    for a, b, _ in pairs:
                        print("        %04x  %-18s %-26s | %-18s %s"
                              % (a[0], a[1].hex(), a[2] or "",
                                 b[1].hex(), b[2] or ""))
        if up:
            print("  THE DEFECT IS UPSTREAM OF THE SPAN -- read from the address"
                  " shown, not from the span's start:")
            for (seg, lo, n, nd, pairs), back in sorted(
                    up, key=lambda r: -r[0][2]):
                a, b, _ = pairs[-1]
                print("    %04x:%04x  %4d byte(s)  first length change %d"
                      " byte(s) earlier, at %04x:%04x"
                      % (seg, lo, n, back, seg, a[0]))
                if show:
                    print("        %04x  %-18s %-26s | %-18s %s"
                          % (a[0], a[1].hex(), a[2] or "",
                             b[1].hex(), b[2] or ""))
        for (seg, lo, n, ndiff, pairs), verdict in other:
            print("  %04x:%04x  %4d byte(s)  -- %s" % (seg, lo, n, verdict))


if __name__ == "__main__":
    if not sys.argv[1:]:
        raise SystemExit(__doc__)
    main(sys.argv[1:])
