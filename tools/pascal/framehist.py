r"""Compare the MULTISET of stack-frame sizes in two builds.

    python kit/tools/pascal/framehist.py SPANS.toml PART
    python kit/tools/pascal/framehist.py SPANS.toml 001 --all

WHY THIS EXISTS BESIDE `prologue.py`, WHICH ALREADY READS FRAMES. That tool
pairs each routine in the original with the one in our build that rebuilds it,
and reports the frames side by side. It is the better instrument whenever it
can pair -- it names the routine. But it deliberately WITHHOLDS a pairing when
the two bodies differ too much to be confident, and reports `not located`. On a
part with a dozen of those, `prologue.py` can no longer answer the one question
you have after editing a declaration: DID THE FRAME I JUST FIXED COME OUT RIGHT?

This tool answers that without pairing anything. It counts frame sizes across
the whole image. If the original contains one `ENTER $182` and so do we, then
that frame exists somewhere in our build -- which is all you need to confirm a
declaration list, because a frame size is a property of the declarations and
not of the routine's identity.

So the two are complementary, not redundant:

    prologue.py   names the routine, needs a pairing, silent when bodies differ
    framehist.py  never names anything, needs no pairing, always answers

Read a MISSING row as a declaration list that is too small somewhere, and a
surplus row as one that is too big. A pair of rows that are equal and opposite
-- one missing at $14 and one surplus at $12 -- is usually ONE routine two
bytes short, not two separate defects.

BLIND SPOT, AND IT MATTERS: this scans for the byte pattern of `ENTER imm16,0`
and cannot tell code from data. Any `C8 xx yy 00` in a table or a string counts,
so large or implausible operands are usually false positives -- treat anything
above a few thousand bytes as data until a disassembly says otherwise. It is
also blind to `{$G-}` routines entirely, which use `PUSH BP / MOV BP,SP / SUB
SP,n` and are not counted here at all; use `prologue.py` for a unit built that
way. And a count that matches is not proof the frames are on the RIGHT
routines -- two routines can swap frames and this sees nothing.
"""
import collections
import io
import pathlib
import sys

try:
    import tomllib
except ModuleNotFoundError:                       # Python < 3.11
    import tomli as tomllib                       # type: ignore

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import project                                    # noqa: E402

# Anything larger than this is treated as data rather than a real frame. Real
# BP7 frames are bounded by the 64K stack and in practice by a few strings.
PLAUSIBLE = 0x2000


def frames(blob):
    """Every `ENTER imm16, 0` operand in the image, as a multiset."""
    counts = collections.Counter()
    i = 0
    while True:
        i = blob.find(b"\xc8", i)
        if i < 0 or i + 4 > len(blob):
            break
        # ENTER takes imm16 then imm8; Borland only ever emits a zero level.
        if blob[i + 3] == 0:
            counts[blob[i + 1] | (blob[i + 2] << 8)] += 1
        i += 1
    return counts


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        sys.stdout.write(__doc__ or "")
        return 0
    show_all = "--all" in argv
    argv = [a for a in argv if not a.startswith("--")]
    if len(argv) < 2:
        sys.stdout.write("usage: framehist.py SPANS.toml PART [--all]\n")
        return 2

    with io.open(argv[0], "rb") as fh:
        cfg = tomllib.load(fh)
    part = argv[1]
    spec = cfg["part"].get(part)
    if spec is None:
        sys.stdout.write("  no segments recorded for part %s\n" % part)
        return 1
    try:
        root = project.find()
        release = project.get("target.release")
        built = root / project.get("layout.built")
    except project.Missing as exc:
        return project.complain(exc)

    ours_path = built / spec["exe"]
    if not ours_path.exists():
        sys.stdout.write("  %s is not built -- nothing to compare\n" % spec["exe"])
        return 1

    orig = frames((root / release[part]).read_bytes())
    ours = frames(ours_path.read_bytes())

    sys.stdout.write("part %s vs %s\n" % (part, spec["exe"]))
    sys.stdout.write("  %-9s %-9s %-7s\n" % ("frame", "original", "ours"))

    differ = skipped = 0
    for size in sorted(set(orig) | set(ours)):
        if orig[size] == ours[size] and not show_all:
            continue
        if size > PLAUSIBLE and not show_all:
            skipped += 1
            continue
        note = ""
        if orig[size] != ours[size]:
            differ += 1
            note = "MISSING" if ours[size] < orig[size] else "surplus"
        sys.stdout.write("  $%-8X %-9d %-7d %s\n"
                         % (size, orig[size], ours[size], note))

    sys.stdout.write("\n  %d frame size(s) differ in count\n" % differ)
    if skipped:
        sys.stdout.write("  %d implausible operand(s) over $%X skipped as data"
                         " -- pass --all to see them\n" % (skipped, PLAUSIBLE))
    sys.stdout.write("  a missing row is a declaration list too small; a surplus"
                     " one is too big.\n"
                     "  equal and opposite rows are usually ONE routine, not two"
                     " defects.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
