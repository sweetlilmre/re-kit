"""The four cheap measurements on one segment, in one command.

    python kit/tools/pascal/survey.py CONFIG.toml 165a
    python kit/tools/pascal/survey.py CONFIG.toml 165a 2832   an explicit size

RENAMED from `census.py`, its name in the repository it came from -- and that
name already belonged to the kit's script-retirement census. The two share
nothing at all, and a table keyed by basename cannot hold both: the retirement
census reported this file as a row about itself, and it was very nearly archived
on the strength of a successor that is an unrelated program (#50).

WHY THIS EXISTS. Four scans settled almost everything structural in `17cf` and `116e`,
and all four are greps rather than disassembly:

  FAR RETURNS      a routine census, and the stack-cleanup count is a SIGNATURE. `RETF 4`
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
    """Far returns, in address order. `c9`/`5d` is LEAVE or POP BP first."""
    out = []
    for m in re.finditer(rb"[\xc9\x5d](\xca|\xcb)", d):
        i = m.start()
        if d[i + 1] == 0xCA:
            out.append((i, struct.unpack_from("<H", d, i + 2)[0]))
        else:
            out.append((i, None))
    return out


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
    if len(sys.argv) < 3:
        print("usage: survey.py CONFIG.toml SEG [SIZE]")
        return 2
    config, seg = sys.argv[1], int(sys.argv[2], 16)
    try:
        image = project.path("target.image")
        first = project.get("target.first_para", quiet=True)
    except project.Missing as exc:
        return project.complain(exc)
    if len(sys.argv) > 3:
        size = int(sys.argv[3])
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
    print("\n-- FAR RETURNS (%d)  -- the routine census; the count is a signature" % len(r))
    for i, n in r:
        print("     %04x  RETF %s" % (i, "" if n is None else n))
    from collections import Counter
    print("     counts: %s" % dict(Counter(n for _, n in r)))

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
    main()
