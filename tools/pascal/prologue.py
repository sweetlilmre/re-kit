r"""Read a routine's prologue: what the source declared, and which switch built it.

    python kit/tools/pascal/prologue.py SPANS.toml 001
    python kit/tools/pascal/prologue.py SPANS.toml 001 --seg 1012
    python kit/tools/pascal/prologue.py SPANS.toml 002 108b:00bf..03bd

THE PROLOGUE IS TWO MEASUREMENTS AND THIS PRINTS BOTH. `ENTER n,0` versus
`PUSH BP / MOV BP,SP` names the unit's `$G` switch, which is a UNIT property --
so one routine answers it for every routine beside it. The OPERAND is the
declared locals plus the code generator's temporaries -- and a temporary is
not always below the last declaration, because a `for` limit that is not a
constant becomes one and is read every iteration -- which constrains the
source's `var` block before a single statement is read. See the wiki
observation `The frame is bigger than your locals account for`.

WITH A RANGE it switches to one routine and enumerates every BP-relative slot
that routine touches, with reference counts, in BOTH addressing forms. That
list is what recovers a declaration order: Borland allocates first-declared
nearest `BP` and does not align locals, so an ODD offset means a one-byte local
was declared before it, and a slot with no references at all is a declaration
the original made and never read. Two such blocks were transcribed into one
reconstruction on this evidence, and leaving them out had put every later local
at the wrong offset.

**A PROLOGUE SCAN IS A GUESS AND THIS ONE SAYS SO.** `C8 xx xx 00` occurs
inside data and inside longer instructions, so every candidate is checked
against the segment's own CALL targets and reported as `called` or `unproven`.
Unproven is not wrong -- a routine reached only through a procedure variable or
a VMT has no direct CALL -- but it is the column to distrust. Routines with no
locals and no frame at all are INVISIBLE here, which is the technique's blind
spot and the reason this is not a function lister.

COMPARING THE TWO BUILDS IS THE POINT, so where the config names a built
harness this locates each original routine's body in it and prints our frame
beside the original's. A row where the frames differ is a routine whose
declarations are wrong, and it is worth more than the same row's byte count.
"""
import io
import re
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[0]))
import project                                    # noqa: E402
from substrate import align                       # noqa: E402
from substrate import disasm                      # noqa: E402

try:
    import tomllib
except ModuleNotFoundError:                       # pragma: no cover -- 3.11+
    import tomli as tomllib                       # type: ignore

# `PUSH BP` then `MOV BP,SP`. Borland emits 89 E5; other assemblers 8B EC, and
# both appear in one image because the RTL was not built by the same compiler.
G_MINUS = (b"\x55\x89\xe5", b"\x55\x8b\xec")
# mod=01, r/m=110 -- [BP+disp8] -- across all eight reg fields.
MOD8 = (0x46, 0x4e, 0x56, 0x5e, 0x66, 0x6e, 0x76, 0x7e)
# mod=10, r/m=110 -- [BP+disp16].
MOD16 = (0x86, 0x8e, 0x96, 0x9e, 0xa6, 0xae, 0xb6, 0xbe)


def call_targets(code):
    """Offsets this segment CALLs directly, as a set.

    Near calls only: `E8 rel16` relative to the next instruction. A far call
    names a segment we are not looking at, and a call through a register or a
    VMT names nothing a scan can see -- which is why an unmatched prologue is
    reported as unproven rather than dropped.
    """
    out = set()
    for m in re.finditer(rb"\xe8(..)", code, re.S):
        at = m.start()
        rel = int.from_bytes(code[at + 1:at + 3], "little", signed=True)
        dst = at + 3 + rel
        if 0 <= dst < len(code):
            out.add(dst)
    return out


def prologues(code):
    """(offset, frame bytes, form) for every routine-looking prologue.

    `form` is '$G+' for ENTER and '$G-' for the PUSH BP pair. A frame of None
    means the PUSH BP form with no `SUB SP` after it -- a framed routine with no
    locals, which says nothing about the declarations and everything about $G.
    """
    found = []
    for m in re.finditer(rb"\xc8(..)\x00", code, re.S):
        n = int.from_bytes(code[m.start() + 1:m.start() + 3], "little")
        found.append((m.start(), n, "$G+"))
    for pat in G_MINUS:
        for m in re.finditer(re.escape(pat), code):
            at = m.start()
            tail = code[at + 3:at + 6]
            n = None
            if tail[:2] == b"\x83\xec":            # SUB SP, imm8
                n = tail[2]
            elif tail[:2] == b"\x81\xec":          # SUB SP, imm16
                n = int.from_bytes(code[at + 5:at + 7], "little")
            found.append((at, n, "$G-"))
    return sorted(found)


def slots(code):
    """Every negative BP-relative slot the code touches, with reference counts.

    Both addressing forms, because a scan that reads only `disp8` misses the
    larger frames entirely -- and a slot that looks untouched because the scan
    could not see it is indistinguishable from a declaration nobody reads,
    which is exactly the thing this is used to find.
    """
    hits = {}
    for i in range(len(code) - 1):
        if code[i] in MOD8 and code[i + 1] >= 0x80:
            hits[code[i + 1] - 256] = hits.get(code[i + 1] - 256, 0) + 1
    for i in range(len(code) - 2):
        if code[i] in MOD16:
            v = int.from_bytes(code[i + 1:i + 3], "little", signed=True)
            if -0x8000 < v < 0:
                hits[v] = hits.get(v, 0) + 1
    return hits


def params(code):
    """Positive BP-relative slots -- the parameters and the return address."""
    hits = {}
    for i in range(len(code) - 1):
        if code[i] in MOD8 and 0 < code[i + 1] < 0x80:
            hits[code[i + 1]] = hits.get(code[i + 1], 0) + 1
    return hits


def segment(blob, seg, nxt, first):
    base = disasm.image_base(blob) + (seg - first) * 16
    return blob[base:base + (nxt - seg) * 16]


def ours_frame(chunk, ours):
    """The frame our build gives the routine whose body is `chunk`.

    Located by CONTENT, never by address: the two builds do not agree on link
    order, and anchoring by offset produced two wrong answers by hand before
    this existed. The prologue itself is excluded from the search, because a
    differing frame is precisely what we are looking for and would stop the
    body being found.
    """
    body = chunk[8:8 + align.WINDOW]
    if len(body) < align.ANCHOR:
        return None, 0
    at, got = align.locate(body, ours, align.holes, None)
    if at < 0 or got < align.MINIMUM:
        return None, got
    back = ours[max(0, at - 0x40):at]
    best = None
    for off, n, form in prologues(back):
        best = (n, form)
    return best, got


def report_segment(part, seg, code, ours, min_frame):
    calls = call_targets(code)
    rows = prologues(code)
    print("  segment %04x -- %d byte(s), %d prologue candidate(s)"
          % (seg, len(code), len(rows)))
    g_plus = sum(1 for _, _, f in rows if f == "$G+")
    if rows:
        print("     $G reads %s: %d ENTER, %d PUSH BP"
              % ("$G+" if g_plus else "$G-", g_plus, len(rows) - g_plus))
    dropped = 0
    for off, n, form in rows:
        if n is not None and n < min_frame:
            dropped += 1
            continue
        proof = "called" if off in calls else "unproven"
        mine = ""
        if ours is None:
            pass
        elif proof == "unproven":
            # WITHHELD ON PURPOSE. Comparing a candidate nothing calls is how
            # this tool manufactured a finding: on part 002 it read `ENTER $8e`
            # out of a data table at 108b:2edf, located 64 bytes of that table
            # in the rebuild, and printed `ours: same` -- a confident agreement
            # about a routine that does not exist. A comparison is only as good
            # as the claim that there is something there to compare.
            mine = "   ours: withheld, nothing calls this"
        else:
            end = min(len(code), off + 0x200)
            got, _ = ours_frame(code[off:end], ours)
            if got is None:
                mine = "   ours: not located"
            elif got[0] != n or got[1] != form:
                mine = ("   ours: %s %s   <-- DIFFERS"
                        % (got[1], "$%02x" % got[0] if got[0] is not None
                           else "no locals"))
            else:
                mine = "   ours: same"
        print("     %04x:%04x  %-4s %-11s %-9s%s"
              % (seg, off, form,
                 "$%02x" % n if n is not None else "no locals", proof, mine))
    if dropped:
        print("     %d candidate(s) below --min=$%02x not shown"
              % (dropped, min_frame))


def report_routine(part, seg, lo, hi, code):
    body = code[lo:hi]
    pro = prologues(body[:8])
    frame = pro[0][1] if pro and pro[0][0] == 0 else None
    form = pro[0][2] if pro and pro[0][0] == 0 else "?"
    print("  %04x:%04x..%04x -- %d byte(s), %s %s"
          % (seg, lo, hi, hi - lo, form,
             "frame $%02x (%d bytes)" % (frame, frame) if frame is not None
             else "no frame operand"))
    p = params(body)
    if p:
        print("     parameters and return address, [BP+n]:")
        for k in sorted(p):
            print("        [BP+$%02x]  %d reference(s)" % (k, p[k]))
    s = slots(body)
    # THE FRAME BOUNDS THE ENUMERATION, and without that bound this tool once
    # printed fifteen thousand rows and a NEGATIVE temporary count. The disp16
    # form is two arbitrary bytes after a common modrm, so it matches inside
    # immediates and inside data; a hit below the frame cannot be a local of
    # this routine whatever it looks like. Discarded rather than trusted, and
    # COUNTED rather than dropped quietly -- a silent cap reads as coverage.
    outside = 0
    if frame is not None:
        keep = {k: v for k, v in s.items() if -frame <= k <= -2}
        outside = len(s) - len(keep)
        s = keep
    if not s:
        print("     no BP-relative locals touched")
        return
    print("     locals, [BP-n] -- first declared is nearest BP:")
    lo_slot = min(s)
    for off in range(-2, lo_slot - 2, -2):
        n = s.get(off, 0)
        note = "" if n else "   <-- NEVER TOUCHED"
        print("        [BP-$%02x]  %d reference(s)%s" % (-off, n, note))
    if frame is not None:
        declared = -lo_slot
        # NOT "and the rest is declared". A TOUCHED slot can be the code
        # generator's too: a `for` loop whose limit is not a constant is
        # evaluated once into a temporary, and that temporary is then read on
        # every iteration -- so it looks exactly like a declared local, and
        # transcribing it AS one produces both it and the compiler's, putting
        # the frame over. Three routines in one segment were built that way
        # before this line was rewritten. The bytes beyond the lowest touched
        # slot are a LOWER BOUND on the temporaries, never the whole of them.
        print("     %d byte(s) of frame; the lowest slot touched is [BP-$%02x], "
              "so AT LEAST %d byte(s) are the code generator's -- and a "
              "TOUCHED slot may be its temporary too, so the declarations may "
              "stop higher than this"
              % (frame, declared, frame - declared))
    if outside:
        print("     %d apparent slot(s) below the frame discarded as noise -- "
              "the disp16 form matches inside immediates and data" % outside)


def main(argv):
    args = [a for a in argv if not a.startswith("-")]
    if len(args) < 2:
        sys.stdout.write("usage: prologue.py SPANS.toml PART [SEG:LO..HI] "
                         "[--seg=XXXX] [--min=N]\n")
        return 2
    min_frame = 0
    want_seg = None
    for a in argv:
        if a.startswith("--min="):
            min_frame = int(a.split("=")[1], 0)
        if a.startswith("--seg="):
            want_seg = int(a.split("=")[1], 16)

    with io.open(args[0], "rb") as fh:
        cfg = tomllib.load(fh)
    part = args[1]
    spec = cfg["part"].get(part)
    if spec is None:
        print("no segments recorded for part %s" % part)
        return 1

    try:
        root = project.find()
        release = project.get("target.release")
        built = root / project.get("layout.built")
        first = project.get("target.first_para", quiet=True)
    except project.Missing as exc:
        return project.complain(exc)

    blob = (root / release[part]).read_bytes()
    ours_path = built / spec["exe"]
    ours = ours_path.read_bytes() if ours_path.exists() else None
    if ours is None:
        print("  %s is not built -- reporting the original only" % spec["exe"])

    bounds = project.seg_bounds(spec)
    print("part %s vs %s" % (part, spec["exe"]))

    if len(args) > 2:
        seg_s, rng = args[2].split(":")
        seg = int(seg_s, 16)
        a_s, b_s = rng.split("..")
        k = project.seg_addrs(spec).index(seg)
        code = segment(blob, seg, bounds[k + 1], first)
        report_routine(part, seg, int(a_s, 16), int(b_s, 16), code)
        return 0

    for k, seg in enumerate(project.seg_addrs(spec)):
        if want_seg is not None and seg != want_seg:
            continue
        code = segment(blob, seg, bounds[k + 1], first)
        report_segment(part, seg, code, ours, min_frame)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
