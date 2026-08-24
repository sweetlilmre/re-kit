r"""Decode a range of a 16-bit real-mode image, addressed the way its code is.

    python kit/tools/substrate/disasm.py FILE 1012:0004..02bb
    python kit/tools/substrate/disasm.py FILE --file 0x4870..0x48d0
    python kit/tools/substrate/disasm.py FILE 1012:0004+0x40 --first-para 0x1000

THE ENGINE, in the sense `align.py` is: one linear decode with the awkward parts
handled, and callers that know what they are looking at. `pascal/x87.py disasm`
is the caller that resolves Borland's emulator traps; nothing here knows what a
trap is, and nothing here knows what a compiler is.

WHY IT EXISTS. This kit measured rebuilds for two targets with no disassembler
in it at all -- every instrument byte-scans, which is why they are cheap and
portable, and it worked until somebody had to answer *what is this code doing*.
Then it got hand-rolled, twice in one session, which is the signal a tool is
missing. It also unblocks one that was already here: `x87.py fix` documents that
its sites must be "addresses a disassembler has confirmed are instruction
starts", and the kit supplied no way to produce them.

ADDRESSING IS THE POINT, not the decoding. `capstone` decodes; what costs time by
hand is that everything worth reading is written down as `SEG:OFF` -- in a unit
header, a plan row, a source comment -- while a file is a flat run of bytes, and
converting between them needs the MZ header's own paragraph count plus the
paragraph a person decided the image loads at. Getting that wrong by one
paragraph produces a confident disassembly of the wrong sixteen bytes.

**A LINEAR DECODE IS A GUESS ABOUT WHERE INSTRUCTIONS START.** Data between
routines, jump tables and the tail of a segment all decode into something, and
that something looks like code. Start at an address a person or another
instrument has a reason to believe in, and treat a run of nonsense as evidence
you are in data rather than as an instruction mix. When the decoder cannot make
an instruction at all, this prints the byte and advances one -- reported, never
skipped silently, because a hole is the interesting part.

CAPSTONE IS A DEPENDENCY AND ITS ABSENCE IS AN ERROR, never an empty result.
A missing decoder that returned nothing would be indistinguishable from a range
holding nothing, which is the failure `absence-reads-as-zero` is about.
"""
import io
import re
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import project                                    # noqa: E402


def decoder():
    """capstone in 16-bit mode, or a refusal that names the cure."""
    try:
        import capstone
    except ImportError:
        raise SystemExit(
            "disasm needs capstone, and cannot report an empty range instead:\n"
            "    uv pip install --python .venv/Scripts/python.exe capstone")
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_16)
    md.detail = False
    return md


def image_base(blob):
    """Where the load image starts, out of the MZ header's own paragraph count.

    Not a constant: the header is `e_cparhdr` paragraphs long and 0x20 is only
    the common case. A hardcoded 0x200 or 0x20 here would be a second copy of a
    number the file already carries.
    """
    if blob[:2] not in (b"MZ", b"ZM"):
        raise ValueError("not an MZ image -- no header to read a base from")
    return int.from_bytes(blob[8:10], "little") * 16


def image_end(blob):
    """One past the last byte of the load image, ignoring anything appended."""
    pages = int.from_bytes(blob[4:6], "little")
    rem = int.from_bytes(blob[2:4], "little")
    end = pages * 512
    if rem:
        end = end - 512 + rem
    return min(end, len(blob))


def offset_of(blob, seg, off, first_para):
    """File offset of SEG:OFF, given the paragraph the image loads at."""
    return image_base(blob) + (seg - first_para) * 16 + off


# capstone 5.0.7 prints the 32-bit mnemonic for two one-byte opcodes even in
# CS_MODE_16: 0x98 comes back as `cwde` and 0x99 as `cdq`, where a 16-bit decode
# is CBW and CWD. Only the mnemonic is wrong -- every operand around them decodes
# 16-bit correctly -- which is what makes it dangerous: the listing reads as
# plausible 386 code. Copied into a Borland BASM block, `CDQ` assembles as the
# two bytes 66 99 and the transcription is one byte longer than the original for
# a reason nothing else reports. Measured on capstone 5.0.7 by decoding the bare
# bytes: b"" -> `cdq`, b"" -> `cwde`, while b"÷û" -> `idiv bx`
# and b"Áë" -> `shr bx, 2` confirm the mode itself is right.
NARROW = {"cwde": "cbw", "cdq": "cwd"}


def walk(md, data, start):
    """Decode `data` as instructions beginning at address `start`.

    Yields (address, bytes, text) with text None where nothing decodes. The loop
    is written out rather than left to capstone's own iterator because that
    iterator STOPS at the first byte it cannot make an instruction of, and a
    stop looks exactly like the end of the range. Advancing one byte and saying
    so is the difference between a hole and a silence.
    """
    pos = 0
    while pos < len(data):
        made = False
        for ins in md.disasm(bytes(data[pos:]), start + pos):
            text = NARROW.get(ins.mnemonic, ins.mnemonic)
            text = text + (" " + ins.op_str if ins.op_str else "")
            yield ins.address, bytes(ins.bytes), text
            pos = ins.address - start + ins.size
            made = True
        if not made:
            yield start + pos, bytes(data[pos:pos + 1]), None
            pos += 1


def render(md, data, start, seg=None, mark=(), out=None):
    """Print a decode. `mark` is a set of addresses to flag as rewritten.

    A caller that PATCHED bytes before decoding must say which addresses it
    touched, and they are flagged in the output with `~`. That is not decoration.
    A caller here rewrites Borland's emulator traps into the x87 instructions
    they stand for, and a reader shown `fild` with no mark will conclude the file
    contains `fild` -- a mistake that has cost one project three sessions and an
    argument with its own maintainer. The bytes column shows what was DECODED,
    so a marked line's bytes are not the file's bytes either.
    """
    out = out or sys.stdout
    holes = 0
    for addr, raw, text in walk(md, data, start):
        flag = "~" if addr in mark else " "
        where = ("%04x:%04x" % (seg, addr)) if seg is not None else "%06x" % addr
        if text is None:
            holes += 1
            text = "(no instruction)"
        out.write("%s %s  %-20s %s\n" % (flag, where, raw.hex(), text))
    if mark:
        out.write("  ~ = decoded from REWRITTEN bytes; the file holds "
                  "something else at that address\n")
    if holes:
        out.write("  %d byte(s) decoded to nothing -- data, a bad start "
                  "address, or an instruction the range cuts in half at its "
                  "end\n" % holes)
    return holes


RANGE = re.compile(r"^(?:([0-9a-fA-F]{1,4}):)?"
                   r"([0-9a-fA-Fx]+)(?:(\.\.|\+)([0-9a-fA-Fx]+))?$")


def parse_range(spec):
    """`SEG:A..B`, `SEG:A+LEN`, `A..B` or `A+LEN`. Returns (seg, a, length)."""
    m = RANGE.match(spec)
    if not m:
        raise ValueError("cannot read %r as SEG:START..END or START..END"
                         % spec)
    seg_s, a_s, kind, b_s = m.groups()
    base = 16 if seg_s else 0          # a segmented offset is always hex
    a = int(a_s, 16 if base or a_s.lower().startswith("0x") else 0)
    seg = int(seg_s, 16) if seg_s else None
    if b_s is None:
        return seg, a, None
    b = int(b_s, 16 if not b_s.lower().startswith("0x") else 0)
    return seg, a, (b - a) if kind == ".." else b


def slice_for(blob, spec, first_para, flat=False):
    """(bytes, start address, segment or None) for a range spec."""
    seg, a, length = parse_range(spec)
    if seg is None or flat:
        at = a
        start = a
    else:
        if first_para is None:
            raise ValueError(
                "a SEG:OFF range needs the paragraph the image loads at. "
                "kit.toml answers it as target.first_para, or pass "
                "--first-para")
        at = offset_of(blob, seg, a, first_para)
        start = a
    if length is None:
        length = min(0x80, image_end(blob) - at)
    return blob[at:at + length], start, (None if flat else seg)


def main(argv):
    args = project.positionals(argv, ("--first-para",))
    rest = [a for a in args if not a.startswith("-")]
    if len(rest) < 2:
        sys.stdout.write("usage: disasm.py FILE SEG:START..END [--file] "
                         "[--first-para N]\n")
        return 2
    path, spec = rest[0], rest[1]
    flat = "--file" in argv

    fp = None
    for a in argv:
        if a.startswith("--first-para="):
            fp = int(a.split("=", 1)[1], 0)
    if fp is None:
        idx = [i for i, a in enumerate(argv) if a == "--first-para"]
        if idx and idx[0] + 1 < len(argv):
            fp = int(argv[idx[0] + 1], 0)
    if fp is None and not flat:
        fp = project.get("target.first_para", quiet=True)

    with io.open(path, "rb") as fh:
        blob = fh.read()
    try:
        data, start, seg = slice_for(blob, spec, fp, flat)
    except ValueError as exc:
        sys.stdout.write("%s\n" % exc)
        return 2
    if not data:
        sys.stdout.write("that range is empty -- %s holds %d byte(s)\n"
                         % (path, len(blob)))
        return 1
    render(decoder(), data, start, seg)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
