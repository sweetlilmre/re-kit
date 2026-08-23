"""Byte-diff every declared assembler routine against the original binary.

THE RULE this checks is that hand-written assembler is transcribed verbatim
rather than re-expressed. That is a claim about BYTES, so it can be checked
mechanically: build the reconstruction, find each declared routine in the built
executable, and compare it against the same routine in the original.

    python kit/tools/pascal/routines.py
    python kit/tools/pascal/routines.py --emit build/measured.toml
    python kit/tools/pascal/routines.py --probe

WHAT CANNOT MATCH, AND WHY IT IS FORGIVEN. Relative jumps and calls are
self-relative, so they DO match and are compared. What cannot match is any
absolute 16-bit address, because the compiler put our variables at different
DGROUP offsets than the original's:

    A1 dd dd        MOV AX,[disp16]
    BE dd dd        MOV SI,OFFSET Something
    83 7E FB 00     CMP BYTE PTR [BP-5],0

So an isolated run of one or two differing bytes is taken as one such
displacement -- two for an absolute address, one for a frame-relative local --
and skipped; three or more is an opcode change and stops the walk. That rule is
`align.holes`, and it is passed in rather than built in, which is the whole
point of there being one comparison engine.

The heuristic is deliberately tight. A transcription error nearly always
changes an opcode, a register field or an instruction length, and any of those
shifts every byte after it, so it shows as a long run rather than hiding in a
hole.

WHERE THE ROUTINE ENDS is Borland's business, not the comparison's: `returns()`
below is handed to the walk as a terminator, and the walk knows nothing about
x86.

WHERE THE LOCK LIVES. The lengths are NOT a dict in this file. `--emit` writes
what was measured and the ratchet holds it in the status register, where a
lowering is a visible data change with a reason attached and a rise happens by
itself. A lock pasted into a tool sits stale-low until somebody pastes again --
measured in this project: a coverage number sat two below the truth for days.
"""
import io
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[0]))
import project                                    # noqa: E402
import marker                                     # noqa: E402
from substrate import align                       # noqa: E402

try:
    import tomllib
except ModuleNotFoundError:                       # pragma: no cover -- 3.11+
    import tomli as tomllib                       # type: ignore

# How much of the original to pull in when looking for a routine. Nothing in
# hand-written 16-bit assembler comes close to this.
WINDOW = 0x400

# Both near and far returns occur -- shared units are far procedures ending
# CB / CA, a part's own primitives are near ones ending C9 C2 nn nn.
RETS = {0xCB: 1, 0xCA: 3, 0xC3: 1, 0xC2: 3}

# C3 and C2 are near returns and both turn up constantly as operand bytes, so
# they only count as a terminator when they follow the LEAVE or POP BP that
# closes a framed procedure. Without that guard the C2 in `FE C2` (INC DL) cut
# a 64-byte routine off at 37.
FRAME_END = (0xC9, 0x5D)


def returns(orig, mine, i):
    """A routine's end, as Borland writes one: (size, definite) or None.

    CB and CA end a routine outright. C3 and C2 are provisional -- remembered,
    and used only if the walk runs out without a definite one, which is what
    the frameless `assembler` procedures need since they close with a bare C3.
    """
    size = RETS.get(orig[i])
    if not size or orig[i:i + size] != mine[i:i + size]:
        return None
    definite = orig[i] in (0xCB, 0xCA) or (i > 0 and orig[i - 1] in FRAME_END)
    return (size, definite)


def originals(quiet=False):
    """part -> the binary it was read out of.

    Which file that is, is a fact about the TARGET: this demo's parts have an
    `_fpu` variant, which is this project's own disassembly aid rather than a
    1994 release, and the choice of which to measure against belongs in the
    project's answers rather than in a dict here.
    """
    return project.get("target.original", quiet=quiet)


def built(quiet=False):
    """OUR builds only, as (name, bytes).

    A directory of originals kept for side-by-side running would pass
    trivially against itself and prove nothing, so the pattern is stated by the
    project and names only its own harnesses.
    """
    root = project.path("layout.built", quiet=quiet)
    pattern = project.get("layout.built_pattern", quiet=quiet)
    return [(p.name, p.read_bytes()) for p in sorted(root.glob(pattern))]


def locked(register):
    """key -> the length that lined up when it was last measured."""
    if not pathlib.Path(register).is_file():
        return {}
    with io.open(register, "rb") as fh:
        data = tomllib.load(fh)
    return {k: v.get("matched") for k, v in data.get("routine", {}).items()
            if isinstance(v, dict) and v.get("matched") is not None}


def candidates(image, seg, first_para, images, limit=3):
    """Offsets in a segment that a built image DOES line up against.

    Behind `--probe`, because it is slow and because it is only ever wanted
    after the declared address was not found in any built image. The usual
    cause of that is the right segment with a wrong offset, so: walk the first
    4KB of the segment in the original, anchor every offset against every
    built image, and report the few alignments the comparison gets furthest
    into.

    Two filters, and each removes a whole class of false answer:

      * an alignment that never STOPS inside the window is shared-unit or RTL
        code, identical in both builds by construction. Real, and not the lost
        routine -- and long enough to drown it in the ranking.
      * an offset whose score is no better than the offset one byte before it
        is the tail of a better alignment, not a start of its own. Without
        this the report is a smear of every suffix of one hit.

    The scan stops at 4KB because it cannot know the unit's real extent, and
    past the end sit the shared units and the RTL. A probe into a unit larger
    than that reports less than it could, which is the safe direction.
    """
    base = (seg - first_para) * 16
    scored = {}
    for ofs in range(0, 0x1000):
        chunk = image[base + ofs:base + ofs + WINDOW]
        if len(chunk) <= align.ANCHOR:
            break
        anchor = bytes(chunk[:align.ANCHOR])
        for _, img in images:
            at = img.find(anchor)
            if at < 0:
                continue
            got, _, _ = align.walk(chunk, img[at:at + len(chunk)],
                                   align.holes, None)
            if got < len(chunk) and got > scored.get(ofs, 0):
                scored[ofs] = got
    starts = [(o, g) for o, g in scored.items()
              if g >= align.MINIMUM and g > scored.get(o - 1, 0)]
    starts.sort(key=lambda t: (-t[1], t[0]))
    return starts[:limit]


def main(argv):
    args = project.positionals(argv[1:], ("--emit",))
    probe = "--probe" in argv
    try:
        src = args[0] if args else project.path("layout.src")
        images = built()
        origs = originals()
        register = project.path("layout.register")
    except project.Missing as exc:
        return project.complain(exc)
    if not images:
        sys.stdout.write("  nothing built -- build the harnesses first\n")
        return 1

    rows, bad_markers = marker.read(src)
    for name, line, why in bad_markers:
        sys.stdout.write("%s:%d  %s\n" % (name, line, why))
    if not rows:
        sys.stdout.write("  no @asm markers found under %s\n" % src)
        return 1

    want = locked(register)
    measured = {}
    bad = new = unconfirmed = 0

    sys.stdout.write("%-18s %-16s %-10s %6s %5s\n"
                     % ("routine", "source", "original", "bytes", "holes"))
    sys.stdout.write("-" * 66 + "\n")

    for mk in rows:
        path = origs.get(mk.part)
        if path is None:
            sys.stdout.write("%-18s %-16s part %s has no original in the "
                             "answers file\n"
                             % (mk.name, pathlib.Path(mk.path).name, mk.part))
            bad += 1
            continue
        blob = (project.find() / path).read_bytes()
        image, hdr = align.load_image(blob)
        first = project.get("target.first_para", quiet=True)
        base = (mk.seg - first) * 16 + mk.off
        orig = image[base:base + (mk.span or WINDOW)]

        # BEST fit across every built image, not first fit: the same routine
        # can appear in several harnesses, and the one that goes furthest is
        # the one that actually holds it.
        stop = None if mk.span else returns
        best = (-1, None, 0)
        for image_name, img in images:
            where, got = align.locate(orig, img, align.holes, stop)
            if where >= 0 and got > best[2]:
                best = (where, image_name, got)
        at, image_name, _ = best
        if at < 0:
            note = ("address unconfirmed" if mk.unsure
                    else "NOT FOUND in any built image")
            sys.stdout.write("%-18s %-16s %s %s   %s\n"
                             % (mk.name, pathlib.Path(mk.path).name, mk.part,
                                mk.where, note))
            unconfirmed += 1 if mk.unsure else 0
            bad += 0 if mk.unsure else 1
            if probe:
                for cand, got in candidates(image, mk.seg, first, images):
                    sys.stdout.write("        try %04x:%04x -- %d bytes "
                                     "line up\n" % (mk.seg, cand, got))
            continue

        img = dict(images)[image_name]
        matched, holes, ended = align.walk(
            orig, img[at:at + len(orig)], align.holes, stop)
        if mk.span:
            ended = matched >= mk.span      # a fragment is judged on length
        measured[mk.key] = matched

        lock = want.get(mk.key)
        note = ""
        if not ended:
            note = ("  SHORT -- %d of %d declared" % (matched, mk.span)
                    if mk.span else "  NO RET -- alignment not believed")
            bad += 1
        elif lock is None:
            note = "  (not locked)"
            new += 1
        elif matched < lock:
            note = "  SHORTER than the locked %d -- REGRESSION" % lock
            bad += 1
        elif matched > lock:
            note = "  longer than the locked %d" % lock

        sys.stdout.write("%-18s %-16s %s %s %6d %5d  %-11s%s\n"
                         % (mk.name, pathlib.Path(mk.path).name, mk.part,
                            mk.where, matched, len(holes), image_name, note))
        if lock is not None and matched < lock:
            k = matched
            sys.stdout.write("      diverges at +%03X:  orig %s\n"
                             % (k, orig[k:k + 8].hex()))
            sys.stdout.write("      %18s built %s\n"
                             % ("", img[at + k:at + k + 8].hex()))

    sys.stdout.write("-" * 66 + "\n")
    sys.stdout.write("%d routine(s): %d locked, %d not locked, %d "
                     "unconfirmed, %d failing.\n"
                     % (len(rows), len(rows) - new - bad - unconfirmed, new,
                        unconfirmed, bad))

    if "--emit" in argv:
        out = pathlib.Path(argv[argv.index("--emit") + 1])
        out.parent.mkdir(parents=True, exist_ok=True)
        text = ["# Measured by routines.py. Not hand-written, not committed."]
        for key in sorted(measured):
            text.append("[routine.%r]" % key)
            text.append("matched = %d" % measured[key])
        io.open(out, "w", encoding="utf-8", newline="\n").write(
            "\n".join(text) + "\n")
        sys.stdout.write("  measured %d routine(s) -> %s\n"
                         % (len(measured), out))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
