"""The four cheap measurements on one segment, in one command.

    python kit/tools/pascal/survey.py CONFIG.toml 165a
    python kit/tools/pascal/survey.py CONFIG.toml 165a 2832   an explicit size

RENAMED from `census.py`, its name in the repository it came from -- and that
name already belonged to the kit's script-retirement census. The two share
nothing at all, and a table keyed by basename cannot hold both: the retirement
census reported this file as a row about itself, and it was very nearly archived
on the strength of a successor that is an unrelated program of the same name.

WHY THIS EXISTS. Four scans settled almost everything structural in `17cf` and `116e`,
and all four are greps rather than disassembly:

  FAR RETURNS      the FRAMED ones, and the stack-cleanup count is a SIGNATURE. `RETF 4`
                   is Self alone, `RETF 8` is Self plus one pointer-sized parameter,
                   `RETF 12` is Self plus two. Reading them is far cheaper than finding
                   the entry points and much harder to get wrong.
  PRINTABLE STRINGS  their ABSENCE is evidence. `17cf`'s missing `WriteLn` was found this
                   way: no strings in 2,832 bytes means no text was ever written.
  FAR CALLS OUT    which other segments this one leans on, with a count each. A routine
                   the release calls three times and this segment calls once is a
                   routine 1.31 does not have.
  VIRTUAL SITES    `CALLF [DI+nn]` and `[BX+nn]`, in address order, which is how the VMT
                   layout gets read off the code. `116e`'s extra virtual method was found
                   because four sites landed on +$14 where the release's declaration order
                   puts +$10.

**A MISSING CALL PROVES A MISSING ROUTINE FAR MORE CHEAPLY THAN SEARCHING FOR THE
ROUTINE.** That is the whole thesis of this file.
"""

import io
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import project                                    # noqa: E402

try:
    import tomllib
except ModuleNotFoundError:                       # pragma: no cover -- 3.11+
    import tomli as tomllib                       # type: ignore


def segment_lengths(config):
    """Each segment's code length, read out of the unit config.

    This was a 27-entry constant whose own comment said "keep in step with
    verify.py's UNITS" -- two copies of one measurement, with a note asking
    somebody to remember. The unit config already holds it, so the second copy
    is gone. A segment the config does not name needs its size on the command
    line, which is the honest answer: this tool cannot know the extent of
    something nothing has claimed yet.
    """
    with io.open(config, "rb") as fh:
        cfg = tomllib.load(fh)
    return {u["segment"]: u["length"] for u in cfg.get("unit", {}).values()
            if "segment" in u and "length" in u}


def load(image, first_para, seg, size):
    blob = Path(image).read_bytes()
    base = struct.unpack_from("<H", blob, 8)[0] * 16
    off = base + (seg - first_para) * 16
    return blob[off:off + size]


def returns(d):
    """Far returns that FOLLOW A FRAME, in address order.

    `c9`/`5d` is LEAVE or POP BP first, and that anchor is what makes this
    certain -- a CA or CB byte after one is a return, not data.

    IT IS ALSO WHAT THIS CANNOT SEE, and the consequence matters more than
    the requirement. A routine that reads its parameters off `ss:[bx+n]`
    after `mov bx,sp` builds no frame and ends in a bare RETF -- the shape
    hand-written assembler and the runtime's own units use. This scan is
    blind to every one of them.

    Measured on one 16-bit Pascal rebuild: 2 framed returns in a 1,568-byte
    runtime segment holding roughly thirty assembler routines. The count was
    printed as a census and read as "a unit of very few routines whose bodies
    call nothing", which is a false inference drawn straight off it.

    So `frameless()` reports the rest as a BOUND, and neither number is
    called a census any more.
    """
    out = []
    for m in re.finditer(rb"[\xc9\x5d](\xca|\xcb)", d):
        i = m.start()
        if d[i + 1] == 0xCA:
            out.append((i, struct.unpack_from("<H", d, i + 2)[0]))
        else:
            out.append((i, None))
    return out


def frameless(d):
    """Candidate frameless returns -- an UPPER BOUND, never a count.

    A bare RETF cannot be told from a CA or CB byte sitting in DATA without
    a decoder, so widening the anchored scan would trade a silent undercount
    for a silent overcount. This bounds it instead, and says so.

    TWO CLASSES, REPORTED SEPARATELY, because their strength differs:

      * `RETF nn` whose operand is EVEN and no greater than 32. A stack
        cleanup pops whole words and a routine taking more than sixteen of
        them is rare, so this is a real filter -- on one runtime segment it
        kept operands 2, 4 and 8 and rejected 180, 2539, 4075, 5634, 5770
        and 8056, every one of which is plainly data.
      * a BARE RETF, which has no operand to filter on and is therefore the
        weakest signal here. One 272-byte segment holds nine such bytes and
        cannot hold nine routines.

    Returns (framed_excluded_offsets, sized, bare).
    """
    anchored = {i + 1 for i in range(len(d) - 1)
                if d[i] in (0xC9, 0x5D) and d[i + 1] in (0xCA, 0xCB)}
    sized, bare = [], []
    for i, b in enumerate(d):
        if i in anchored:
            continue
        if b == 0xCA and i + 2 < len(d):
            n = struct.unpack_from("<H", d, i + 1)[0]
            if n % 2 == 0 and n <= 32:
                sized.append((i, n))
        elif b == 0xCB:
            bare.append(i)
    return anchored, sized, bare


def strings(d, minlen=4):
    out = []
    for m in re.finditer(rb"[\x20-\x7e]{%d,}" % minlen, d):
        out.append((m.start(), m.group().decode("latin-1")))
    return out


def farcalls(d):
    """`9a` lo hi seg seg -- direct far calls, grouped by target with a count.

    The target segment is a FIXUP, so in the unpacked image it is already relocated and
    absolute; report it as-is and compare against the map."""
    hits = {}
    for m in re.finditer(rb"\x9a", d):
        i = m.start()
        if i + 5 > len(d):
            continue
        ofs, tseg = struct.unpack_from("<HH", d, i + 1)
        hits.setdefault((tseg, ofs), []).append(i)
    return hits


# 16-BIT MODRM rm VALUES ARE NOT THE REGISTER NUMBERS, and getting that wrong made this
# scan report zero sites in a segment with eight of them. `FF /3` is CALLF m16:16, so the
# reg field is 011 and the byte is 0x58 + rm: 100 = [SI], 101 = [DI], 110 = [BP],
# 111 = [BX]. **`ff 5f` is [BX], not [DI]** -- the natural guess from the 32-bit encoding,
# and wrong. `26 8b 3d ff 5d 14` is what a virtual call actually looks like.
RM16 = {0x04: "SI", 0x05: "DI", 0x06: "BP", 0x07: "BX"}


def virtuals(d):
    """Virtual method calls. Turbo Pascal emits `26 8b 3d` -- `MOV DI,ES:[DI]`, fetching
    the VMT pointer from the object's offset 0 -- then `CALLF [DI+slot]`, with the VMT in
    DGROUP so the call itself needs no segment prefix. Only the CALLF is matched here, and
    **the displacement IS the VMT slot.**"""
    out = []
    for m in re.finditer(rb"\xff([\x5c-\x5f])", d):
        i = m.start()
        out.append((i, RM16[d[i + 1] & 7], d[i + 2]))
    for m in re.finditer(rb"\xff([\x9c-\x9f])", d):
        i = m.start()
        out.append((i, RM16[d[i + 1] & 7], struct.unpack_from("<H", d, i + 2)[0]))
    return sorted(out)


def main():
    # POSITIONALS THROUGH project.positionals, never by index into sys.argv.
    # This read sys.argv[1..3] directly, so the moment it grew a flag the flag
    # landed in a positional slot -- `survey.py CONFIG SEG --part=001` raised
    # on int("--part=001"). The shared parser knows which flags carry a value
    # and skips those values, which is the bug its own docstring records from
    # ratchet.py reading "76" as the name of the status register.
    argv = sys.argv[1:]
    args = project.positionals(argv, valued=("part",))
    part = None
    for i, a in enumerate(argv):
        if a.startswith("--part="):
            part = a.split("=", 1)[1]
        elif a == "--part" and i + 1 < len(argv):
            part = argv[i + 1]
    if len(args) < 2:
        print("usage: survey.py CONFIG.toml SEG [SIZE] [--part N]")
        return 2
    config, seg = args[0], int(args[1], 16)
    try:
        # One segment of ONE image, so it needs one binary -- and which binary
        # is a question a multi-part project answers with a part.
        image = project.original(part)
        first = project.get("target.first_para", quiet=True)
    except project.Missing as exc:
        return project.complain(exc)
    if len(args) > 2:
        size = int(args[2])
    else:
        lengths = segment_lengths(config)
        if seg not in lengths:
            print("  %s does not name segment %04x -- pass its size"
                  % (config, seg))
            return 2
        size = lengths[seg]
    d = load(image, first, seg, size)
    print("== %04x  %d bytes" % (seg, size))

    r = returns(d)
    print("\n-- FAR RETURNS, FRAMED (%d)  -- certain, and NOT a census" % len(r))
    for i, n in r:
        print("     %04x  RETF %s" % (i, "" if n is None else n))
    from collections import Counter
    print("     counts: %s" % dict(Counter(n for _, n in r)))

    # THE BOUND, PRINTED BESIDE THE COUNT. The scan above is anchored on a
    # frame, so it cannot see a routine that builds none -- and printing only
    # its number named a partial population as though it were the whole one.
    _, sized, bare = frameless(d)
    print("\n-- FRAMELESS CANDIDATES  -- an UPPER BOUND, not a count")
    print("     %d x RETF nn, operand even and <= 32" % len(sized))
    print("     %d x bare RETF, which has no operand to filter on" % len(bare))
    if sized:
        print("     %s" % "  ".join("%04x/%d" % (i, n) for i, n in sized[:12]))
    print("     A frameless routine reads its parameters off ss:[bx+n] and ends")
    print("     in a bare RETF, so the framed scan cannot see it. A CA or CB byte")
    print("     inside DATA cannot be told from a return without a decoder, so")
    print("     this over-counts. Read it as direction and magnitude.")

    s = strings(d)
    print("\n-- PRINTABLE STRINGS (%d)  -- an absence is evidence" % len(s))
    for i, t in s[:40]:
        print("     %04x  %r" % (i, t))

    f = farcalls(d)
    print("\n-- FAR CALLS OUT (%d distinct targets)" % len(f))
    for (tseg, ofs), sites in sorted(f.items(), key=lambda kv: -len(kv[1])):
        print("     %04x:%04x  x%-3d  from %s" % (
            tseg, ofs, len(sites), " ".join("%04x" % a for a in sites[:8])))

    v = virtuals(d)
    print("\n-- VIRTUAL CALL SITES (%d), in address order -- this is the VMT layout" % len(v))
    for i, reg, n in v:
        print("     %04x  CALLF [%s+%02x]" % (i, reg, n))
    slots = Counter("[%s+%02x]" % (reg, n) for _, reg, n in v)
    print("     slots: %s" % dict(sorted(slots.items())))


if __name__ == "__main__":
    # main() returns 2 on a usage error and on a missing answer, and those
    # were being discarded -- the process exited 0 whatever happened, so a
    # session reading the status of this tool could never see it fail.
    sys.exit(main() or 0)
