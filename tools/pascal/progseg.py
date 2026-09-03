r"""The main program is a table of every unit's entry-point offsets. Compare it.

    python kit/tools/pascal/progseg.py SPANS.toml
    python kit/tools/pascal/progseg.py SPANS.toml 001
    python kit/tools/pascal/progseg.py SPANS.toml 001 --prologues=1107

WHAT IT MEASURES AND WHY NOTHING ELSE DOES. A compiled main body is almost
nothing but far calls: the unit-initialisation chain, one per unit in reverse of
the link order, then each scene, each helper, the runtime exit. Every one of
those calls names a segment AND AN OFFSET, so segment 1000 is a table of every
unit's entry points, written by the compiler, in a form that cannot drift.
Comparing it byte for byte checks all of them at once.

The instruments beside it cannot. A coverage walk locates each segment's content
wherever it sits -- which is what makes it robust and is exactly why it is blind
to ARRANGEMENT -- and it counts the ORIGINAL's bytes, so bytes the rebuild has
and the original does not are invisible to it by construction. A segment-size
check rounds to a paragraph, hiding one to fifteen bytes. And a total that
balances hides an ordering: two errors of eight and nine bytes in opposite
directions inside one unit leave every total nearly right.

On the first target this found, in one pass over seven programs: a routine
defined last behind a forward declaration where the original has it mid-segment;
five programs carrying their exit TWICE, because a closing end-dot already emits
the runtime exit and an explicit terminating call emits it again; three missing
the 286 switch, which is per-file and is not inherited from a unit; a unit four
paragraphs short; and another thirteen bytes long. See the wiki observation
"The main program is a list of every unit's entry-point offsets".

THE PROLOGUES OPTION IS THE LOCALISER. This says a unit is wrong and by how
much, never where. Given a segment it takes every prologue -- ENTER imm,0 and
PUSH BP / MOV BP,SP -- on both sides and prints the PER-ROUTINE drift, so an
error is attributed to one routine and, crucially, two errors that cancel are
separated. Read that before editing: fixing one of a cancelling pair alone makes
every downstream measurement worse, because the other stops being hidden and the
unit changes size.

A PROLOGUE SCAN IS A GUESS. The byte patterns occur in data and inside longer
instructions, and a routine with no frame at all is invisible to it, so the
routine count is a hint. When the two sides disagree on how MANY prologues there
are, the pairing below it is meaningless and this says so rather than printing a
drift column nobody should trust.

AND DO NOT DIFF A WHOLE UNIT with a masked instruction diff. Once the offsets
have drifted it pairs your instruction with whatever sits at the drifted address,
not with its counterpart; acting on such a pairing produced two individually
plausible changes that were both wrong and both measurably worse. Localise with
this, then diff one routine anchored on its own prologue.
"""
import io
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import project                                    # noqa: E402

try:
    import tomllib
except ModuleNotFoundError:                       # pragma: no cover -- 3.11+
    import tomli as tomllib                       # type: ignore

FAR_CALL = 0x9A


def load(path):
    d = pathlib.Path(path).read_bytes()
    return d, int.from_bytes(d[8:10], "little") * 16


def call_targets(buf, end):
    """Offsets reached by a near CALL inside this segment."""
    out = set()
    for i in range(max(0, end - 3)):
        if buf[i] == 0xE8:
            rel = int.from_bytes(buf[i + 1:i + 3], "little", signed=True)
            t = i + 3 + rel
            if 0 <= t < end:
                out.add(t)
    return out


def prologues(buf, end):
    """Routine starts: a prologue that something in the segment CALLS.

    THE FILTER IS NOT OPTIONAL. C8 xx xx 00 and 55 8B EC occur inside data and
    inside longer instructions, and an unfiltered scan pairs the two sides by
    INDEX -- so one false positive in a different place on each side shifts
    every row below it and invents two large cancelling errors that are not
    there. That happened on a segment whose program-segment references were
    byte-identical, which is how it was caught. Keeping only candidates that are
    the target of a near CALL removes them; the unit initialisation section is
    kept as well, because nothing inside the segment calls it -- the program's
    init chain does, from outside.
    """
    targets = call_targets(buf, end)
    out = []
    for i in range(max(0, end - 3)):
        if buf[i] == 0xC8 and buf[i + 3] == 0x00:
            pass
        elif buf[i:i + 3] in (b"\x55\x8b\xec", b"\x55\x89\xe5"):
            pass
        else:
            continue
        if i in targets or buf[i:i + 5] in (b"\x55\x8b\xec\xc9\xcb",
                                            b"\x55\x89\xe5\xc9\xcb"):
            out.append(i)
    return out


def enclosing_call(buf, at):
    """If `at` is inside a far call operand, return (offset, segment)."""
    for back in (1, 2, 3, 4):
        i = at - back
        if i >= 0 and buf[i] == FAR_CALL:
            return (int.from_bytes(buf[i + 1:i + 3], "little"),
                    int.from_bytes(buf[i + 3:i + 5], "little"))
    return None


def report(part, spec, blob, ours, first):
    segs = list(spec["segments"])
    hi = segs[0] if segs[0] > first else segs[1]
    size = (hi - first) * 16
    a = blob[:size]
    if ours is None:
        print("part %-6s %s is not built" % (part, spec["exe"]))
        return 1
    b = ours[:size]
    diff = [i for i in range(size) if a[i] != b[i]]
    if not diff:
        print("part %-6s program segment BYTE-IDENTICAL (%d bytes)" % (part, size))
        return 0
    print("part %-6s %d of %d program byte(s) differ" % (part, len(diff), size))
    seen = {}
    for i in diff:
        call = enclosing_call(a, i)
        if call is None:
            seen[("raw", i)] = 1
            continue
        off, seg = call
        mine = enclosing_call(b, i)
        key = (seg, off, mine[1] if mine else None, mine[0] if mine else None)
        seen[key] = seen.get(key, 0) + 1
    for key in sorted(seen, key=str):
        if key[0] == "raw":
            print("      +%04x  not inside a far call -- read the bytes" % key[1])
            continue
        seg, off, myseg, myoff = key
        if seg == myseg:
            print("      segment %04x: entry offset %04x, ours %04x  (%+d)"
                  % (seg, off, myoff, myoff - off))
        else:
            print("      segment %04x at %04x, ours %04x at %04x -- the SEGMENT "
                  "moved, so a unit before it is the wrong size"
                  % (seg, off, myseg, myoff))
    return 1


def localise(part, spec, blob, ours, first, seg):
    segs = list(spec["segments"]) + [spec["end_at"]]
    if seg not in segs:
        print("segment %04x is not among part %s's segments" % (seg, part))
        return 2
    k = segs.index(seg)
    size = (segs[k + 1] - seg) * 16
    a = blob[(seg - first) * 16:][:size]
    at = ours.find(bytes(a[:16]))
    if at < 0:
        print("cannot locate segment %04x in the rebuild by content" % seg)
        return 1
    b = ours[at:][:size]
    pa, pb = prologues(a, size), prologues(b, size)
    print("segment %04x: %d prologue(s) in the original, %d in ours"
          % (seg, len(pa), len(pb)))
    if len(pa) != len(pb):
        print("  THE COUNTS DIFFER, so the pairing below would be meaningless.")
        print("  A prologue scan is a guess: the patterns occur in data and")
        print("  inside longer instructions, and a routine with no frame is")
        print("  invisible. Read the two lists and pair them by hand.")
        print("  original %s" % [hex(x) for x in pa])
        print("  ours     %s" % [hex(x) for x in pb])
        return 1
    # The empty unit-initialisation section is the compiler's LAST output for
    # the unit. Anything after it was linked in from an .OBJ, where a prologue
    # scan is guessing at hand-written code and a one-byte row means nothing.
    init = None
    for i, at in enumerate(pa):
        if a[at:at + 5] in (b"\x55\x8b\xec\xc9\xcb", b"\x55\x89\xe5\xc9\xcb"):
            init = i
    bad = ext = 0
    for i in range(len(pa) - 1):
        la, lb = pa[i + 1] - pa[i], pb[i + 1] - pb[i]
        if la == lb:
            continue
        tail = init is not None and i >= init
        print("  routine at %04x is %+d byte(s) in ours (%d against %d)%s"
              % (pa[i], lb - la, lb, la, "   [past the init -- .OBJ]" if tail else ""))
        if tail:
            ext += 1
        else:
            bad += 1
    if not bad and not ext:
        print("  every routine length matches")
    if ext:
        print("")
        print("  %d row(s) are AT OR PAST the unit initialisation section, which is"
              % ext)
        print("  the compiler's last output -- everything after it came from an")
        print("  .OBJ, where this scan is guessing at hand-written code. A one-byte")
        print("  row there is noise; do not chase it.")
    if bad:
        print("")
        print("  %d routine(s) differ. If two differ in OPPOSITE directions they"
              % bad)
        print("  are cancelling: fixing one alone makes every total worse.")
    return 1 if bad else 0


def main(argv):
    args = [a for a in argv if not a.startswith("-")]
    if not args:
        sys.stdout.write(__doc__ or "")
        return 2
    want_pro = None
    for a in argv:
        if a.startswith("--prologues="):
            want_pro = int(a.split("=")[1], 16)

    with io.open(args[0], "rb") as fh:
        cfg = tomllib.load(fh)
    parts = args[1:] or list(cfg["part"])

    try:
        root = project.find()
        release = project.get("target.release")
        built = root / project.get("layout.built")
        first = project.get("target.first_para", quiet=True) or 0x1000
    except project.Missing as exc:
        return project.complain(exc)

    bad = 0
    for part in parts:
        spec = cfg["part"][part]
        blob, hdr = load(root / release[part])
        blob = blob[hdr:]
        op = built / spec["exe"]
        ours = None
        if op.exists():
            o, oh = load(op)
            ours = o[oh:]
        if want_pro is not None:
            bad += localise(part, spec, blob, ours, first, want_pro)
        else:
            bad += report(part, spec, blob, ours, first)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
