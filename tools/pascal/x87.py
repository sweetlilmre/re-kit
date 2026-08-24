r"""The x87 emulator traps: survey them, rewrite them, and read what they load.

    python kit/tools/pascal/x87.py survey FILE...
    python kit/tools/pascal/x87.py fix FILE --sites SITES.json --out FILE
    python kit/tools/pascal/x87.py const PART SEG OFF KIND [OFF KIND ...]

THREE SCRIPTS, ONE TOOL, and they belong together because they are three steps
of one job. `survey` asks whether a file's traps are what we think they are;
`fix` rewrites them so a disassembler can decode the code at all; `const` reads
the numbers the decoded instructions turn out to be loading. Doing the third
without the first is how a wrong theory becomes a table of plausible constants.

WHY ANY OF IT IS NEEDED. Borland compiles `$E+` floating point by emitting the
REAL x87 encoding and then letting the linker overwrite the two-byte `WAIT ESC`
prefix with a two-byte `INT n`. Instruction lengths stay identical, which is
precisely what lets the runtime patch the traps back at startup when a 387 is
present -- and it is also why a disassembler shown the shipped bytes sees `INT
34h` where the program means `FLD`.

    CD n        n in 34..3B   ->  9B  D8+(n-0x34)      ESC, reg or BP operand
    CD 3C b                   ->  9B  2E  b+0x40       CS-relative ESC
    CD 3D                     ->  90  9B               standalone FWAIT
    CD 3E                     ->  left alone           the RTL's own entry

THE ENCODING TABLE IS EMPIRICAL, derived from one 1994 binary, and `survey` is
how it stays honest: if the theory holds, the byte after each `CD 3x` must be a
valid modrm, and the distribution of those bytes should look like operands
rather than noise. Run it on a new target before trusting `fix` there.

**A PATCHED FILE IS A DISASSEMBLY AID, NOT A VARIANT OF THE ORIGINAL.** This is
worth stating where the tool lives, because one project spent real effort on the
theory that its `_fpu` files were period variants. They were its own output.
Whatever `fix` writes is ours; the shipped bytes carry the traps.

`fix` REFUSES TO PATCH ON A BYTE MATCH ALONE. Sites come in as addresses a
disassembler has confirmed are instruction starts, because `CD 34` occurs inside
data and inside longer instructions, and a flat scan patches those too.
"""
import argparse
import io
import json
import struct
import sys
import pathlib
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import project                                    # noqa: E402
from substrate.mzinfo import parse                # noqa: E402
from substrate import disasm as _disasm           # noqa: E402

LO, HI = 0x34, 0x3E

# The formats, and BOTH NAMES for the 4-byte one. The tool this came from keyed
# it as `single` while its own docstring described the operand as "FADD/FCOMP
# float ptr" -- which is what a disassembler prints, so it is the word a reader
# has in front of them, and asking for it raised KeyError. Both work now.
#
# real48 is the odd one and is not an x87 format at all: it is the software Real
# that Turbo Pascal variables live in, so it turns up in stack slots and DGROUP
# rather than as an x87 operand.
SIZES = {"single": 4, "float": 4, "double": 8, "ext80": 10, "real48": 6}


# ---------------------------------------------------------------------------
# survey


def modrm_len(op, modrm):
    """Extra bytes a 16-bit modrm consumes after the opcode."""
    mod, rm = modrm >> 6, modrm & 7
    if mod == 3:
        return 0
    if mod == 0:
        return 2 if rm == 6 else 0
    return 1 if mod == 1 else 2


def survey(paths):
    """Count the trap sites per vector, and show what follows each.

    The point is the `common next` column. If the emulator theory holds, those
    bytes are modrm operands and cluster the way operands do; if they were
    arbitrary, the table would be flat and the theory wrong.
    """
    for p in paths:
        h = parse(pathlib.Path(p))
        raw, base = h["raw"], h["hdrsize"]
        code = raw[base:h["imagesize"]]

        vec = Counter()
        follow = {v: Counter() for v in range(LO, HI + 1)}
        sites = []
        i = 0
        while i < len(code) - 2:
            if code[i] == 0xCD and LO <= code[i + 1] <= HI:
                v, nxt = code[i + 1], code[i + 2]
                vec[v] += 1
                follow[v][nxt] += 1
                if len(sites) < 3:
                    sites.append((base + i, code[i:i + 8]))
                i += 2
                continue
            i += 1

        print("")
        print("=== %s ===  %d trap sites" % (h["file"], sum(vec.values())))
        for v in sorted(vec):
            esc = 0xD8 + (v - LO)
            tops = " ".join("%02xx%d" % (b, n)
                            for b, n in follow[v].most_common(3))
            print("  INT %02X -> ESC %02X?  %4d sites   common next: %s"
                  % (v, esc, vec[v], tops))
        print("  sample sites:")
        for off, b in sites:
            print("    file+%#07x  %s" % (off, b.hex(" ")))
    return 0


# ---------------------------------------------------------------------------
# fix


def file_offset(h, seg, off, first_para):
    return h["hdrsize"] + (seg * 16 + off) - first_para * 16


def patch(raw, pos):
    """(new bytes, what it became) for the trap at `pos`, or None.

    None means "not a recognised trap", and the caller reports it rather than
    guessing -- a site a disassembler named but this does not recognise is a
    disagreement worth seeing, not a byte to overwrite.
    """
    if raw[pos] != 0xCD:
        return None
    n = raw[pos + 1]
    if 0x34 <= n <= 0x3B:
        return bytes([0x9B, 0xD8 + (n - 0x34)]), "ESC %02X" % (0xD8 + n - 0x34)
    if n == 0x3C:
        b = raw[pos + 2]
        if not (0x98 <= b <= 0x9F):
            return None
        # WAIT, CS: override, ESC -- the operand is a code-segment literal.
        return bytes([0x9B, 0x2E, b + 0x40]), "ESC %02X CS-relative" % (b + 0x40)
    if n == 0x3D:
        return bytes([0x90, 0x9B]), "FWAIT"
    return None


def fix(exe, sites_file, out, first_para):
    h = parse(pathlib.Path(exe))
    raw = bytearray(h["raw"])
    sites = json.loads(io.open(sites_file, encoding="utf-8").read())

    applied, skipped = 0, []
    for s in sites:
        seg, off = (int(x, 16) for x in s.split(":"))
        res = patch(raw, file_offset(h, seg, off, first_para))
        if res is None:
            skipped.append(s)
            continue
        new, _ = res
        pos = file_offset(h, seg, off, first_para)
        raw[pos:pos + len(new)] = new
        applied += 1

    pathlib.Path(out).write_bytes(bytes(raw))
    print("%s: patched %d/%d sites -> %s"
          % (pathlib.Path(exe).name, applied, len(sites), out))
    if skipped:
        print("  skipped (not a recognised trap): %s" % ", ".join(skipped))
    return 1 if skipped else 0


# ---------------------------------------------------------------------------
# disasm


def disasm(exe, spec, first_para, sites_out=None):
    """Decode a range with the traps resolved AS WE REACH THEM.

    THE POINT IS NOT LEGIBILITY, IT IS THAT NOBODY NEEDS A PATCHED FILE. Until
    this existed the only way to read `$E+` floating point was to run `fix` and
    disassemble the copy -- and a copy on disk outlives the session that made
    it, gets found by the next reader, and gets mistaken for a variant of the
    original. That has happened on one project three times, twice as an
    elaborate theory and once inside a correction of the first two. A decode
    that resolves traps in memory and MARKS every line it resolved leaves
    nothing behind to be mistaken for anything.

    IT ALSO CLOSES THE LOOP `fix` WAS MISSING. `fix` refuses to patch on a byte
    match, and rightly -- `CD 34` occurs inside data and inside longer
    instructions -- so it wants sites "a disassembler has confirmed are
    instruction starts". The kit had no disassembler, so that input could not be
    produced with the kit alone. A linear decode reaches an instruction start by
    construction, so the traps it walks into are exactly the confirmed set:
    `--sites` writes them out in the form `fix` reads.

    A trap this does not RECOGNISE is left as the `INT` it is and counted. That
    includes `INT 3Eh`, which is the RTL's own dispatch entry and not an x87
    instruction at all, so leaving it alone is correct rather than a shortfall.
    """
    h = parse(pathlib.Path(exe))
    raw = bytearray(h["raw"])

    seg, off, length = disasm_range(spec)
    if seg is None:
        raise SystemExit("this wants a SEG:START..END range -- the traps are "
                         "recorded that way and so is everything that cites "
                         "them")
    at = file_offset(h, seg, off, first_para)
    if length is None:
        length = 0x80

    md = _disasm.decoder()
    marked, unknown, sites = set(), [], []
    pos = at
    end = at + length
    # Walk one instruction at a time: a trap has to be RESOLVED before the
    # decoder is asked for the instruction, and the decoder is what says where
    # the next one begins. Patching the whole range up front would patch data.
    while pos < end:
        res = patch(raw, pos) if raw[pos] == 0xCD else None
        addr = off + (pos - at)
        if raw[pos] == 0xCD and LO <= raw[pos + 1] <= HI and res is None:
            unknown.append((addr, raw[pos + 1]))
        if res is not None:
            new, _ = res
            raw[pos:pos + len(new)] = new
            # EVERY address the patch covers, not just its first. A two-byte
            # trap becomes `9B Dx`, which decodes as WAIT at +0 and the x87
            # instruction at +1 -- so marking only the trap's own address flags
            # the WAIT and leaves `FILD` looking like something the file
            # contains. That is the one line a reader would misread, so it is
            # the one line the mark has to reach.
            marked.update(range(addr, addr + len(new)))
            sites.append("%04x:%04x" % (seg, addr))
        step = None
        for ins in md.disasm(bytes(raw[pos:end]), addr):
            step = ins.size
            break
        pos += step or 1

    data = raw[at:at + length]
    holes = _disasm.render(md, data, off, seg, marked)
    # `sites`, not `marked`: marked holds every BYTE a patch covers, so using it
    # here reported 14 traps for a range holding 6. A count is a measurement and
    # the wrong set is how one silently becomes a different measurement.
    print("  %d trap(s) resolved, %d left as INT" % (len(sites), len(unknown)))
    for addr, n in unknown:
        why = ("the RTL's own dispatch entry, not an x87 instruction"
               if n == 0x3E else "not a recognised trap encoding")
        print("    %04x:%04x  INT %02Xh -- %s" % (seg, addr, n, why))
    if sites_out:
        io.open(sites_out, "w", encoding="utf-8", newline="\n").write(
            json.dumps(sites, indent=2) + "\n")
        print("  %d confirmed site(s) -> %s  (feed it to `x87.py fix --sites`)"
              % (len(sites), sites_out))
    return 0 if not holes else 0


def disasm_range(spec):
    """SEG:START..END or SEG:START+LEN -> (seg, start, length or None)."""
    return _disasm.parse_range(spec)


# ---------------------------------------------------------------------------
# const


def ext80(b):
    """Intel 80-bit extended: 64-bit significand with an EXPLICIT leading bit.

    Unlike float and double, the integer bit is stored rather than implied, so
    this cannot be handed to struct and has to be assembled by hand.
    """
    m = int.from_bytes(b[:8], "little")
    se = int.from_bytes(b[8:10], "little")
    sign = -1 if se >> 15 else 1
    exp = se & 0x7FFF
    if exp == 0 and m == 0:
        return 0.0 * sign
    return sign * m * 2.0 ** (exp - 16383 - 63)


def real48(b):
    """Borland's 6-byte Real: an 8-bit exponent, then a 39-bit significand."""
    e = b[0]
    if e == 0:
        return 0.0
    m = int.from_bytes(b[1:6], "little")
    sign = -1 if m >> 39 else 1
    frac = m & ((1 << 39) - 1)
    return sign * (1 + frac / float(1 << 39)) * 2.0 ** (e - 129)


def decode(b, kind):
    if kind in ("single", "float"):
        return struct.unpack("<f", b)[0]
    if kind == "double":
        return struct.unpack("<d", b)[0]
    if kind == "ext80":
        return ext80(b)
    if kind == "real48":
        return real48(b)
    raise ValueError(kind)


def const(part, seg, pairs, first_para):
    """Read constants a code segment loads, by offset and format.

    WHICH FILE a part is measured against is the project's answer, and it is
    not always the plain one: where a target keeps a trap-rewritten copy for
    disassembly, that is what the offsets in the notes refer to. This was
    `work/split/NEUROSIS_{part}_fpu.exe` with a fallback, spelled out inside
    the tool.
    """
    try:
        originals = project.get("target.original")
    except project.Missing as exc:
        return project.complain(exc)
    if part not in originals:
        print("  no original recorded for part %r -- have %s"
              % (part, ", ".join(sorted(originals))))
        return 2
    h = parse(project.find() / originals[part])
    base = h["hdrsize"] + (seg - first_para) * 16
    for off, kind in pairs:
        if kind not in SIZES:
            print("  no format called %r -- have %s"
                  % (kind, ", ".join(sorted(SIZES))))
            return 2
        b = h["raw"][base + off: base + off + SIZES[kind]]
        print("  %04X:$%04X  %-7s %-30s = %r"
              % (seg, off, kind, b.hex(" "), decode(b, kind)))
    return 0


# ---------------------------------------------------------------------------


def main(argv):
    ap = argparse.ArgumentParser(prog="x87.py", add_help=True)
    sub = ap.add_subparsers(dest="cmd")

    s = sub.add_parser("survey", help="count and characterise the trap sites")
    s.add_argument("files", nargs="+")

    f = sub.add_parser("fix", help="rewrite confirmed traps to real x87")
    f.add_argument("exe")
    f.add_argument("--sites", required=True,
                   help="JSON list of 'seg:off' strings a disassembler confirmed")
    f.add_argument("--out", required=True)

    d = sub.add_parser("disasm", help="decode a range with the traps resolved")
    d.add_argument("exe")
    d.add_argument("range", metavar="SEG:START..END")
    d.add_argument("--sites", help="write the confirmed trap sites here, in the "
                                   "form `fix --sites` reads")

    c = sub.add_parser("const", help="decode the constants the code loads")
    c.add_argument("part")
    c.add_argument("seg")
    c.add_argument("rest", nargs="+", metavar="OFF KIND")

    args = ap.parse_args(argv)
    if not args.cmd:
        ap.print_help()
        return 2

    first = project.get("target.first_para", quiet=True)
    if args.cmd == "survey":
        return survey(args.files)
    if args.cmd == "fix":
        return fix(args.exe, args.sites, args.out, first)
    if args.cmd == "disasm":
        return disasm(args.exe, args.range, first, args.sites)
    if args.cmd == "const":
        rest = args.rest
        if len(rest) % 2:
            print("  each offset needs a format after it")
            return 2
        pairs = [(int(rest[i], 16), rest[i + 1]) for i in range(0, len(rest), 2)]
        return const(args.part, int(args.seg, 16), pairs, first)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
