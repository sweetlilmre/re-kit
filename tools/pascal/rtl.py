r"""The Borland runtime, and where its routines and yours actually start.

    python kit/tools/pascal/rtl.py match REF REF_SEG REF_LEN OTHER...
    python kit/tools/pascal/rtl.py find RTL.toml
    python kit/tools/pascal/rtl.py entries LINK.toml [SEG...]

THREE SCRIPTS, ONE TOOL, and the order above is the order you use them in.
`match` finds the runtime block in each binary and says how far it agrees with a
reference; `find` names individual routines inside it by pattern; `entries`
enumerates likely procedure starts anywhere in an image by prologue shape. Two of
them already shared code -- the pattern search imported the masking and the
offset arithmetic from the matcher -- so they were one tool in two files.

**A CORRECTED ASSUMPTION SITS AT THE HEART OF THIS.** The first idea was that
smart-linking preserves RTL offsets across binaries, so one offset-to-name table
would name the runtime everywhere. It holds only for a stable core -- Halt,
GetMem, FreeMem -- and everything above that shifts, so naming by offset
mislabels most of them. `find` therefore takes each routine's BODY from a
reference and searches for it, and a routine whose pattern matches more than
once is not reported at all.

RELOCATION TARGETS ARE MASKED TO ZERO before any comparison. A relocated word
holds a load-time segment value that differs per binary, so unmasked they are
differences with no meaning; masked, two copies of the same routine compare
equal. This is the same reasoning the compare engine's `.OBJ` rule rests on:
where a byte's value is decided later, its value is not evidence.

TWO ANCHORS THE PATTERN SEARCH CANNOT CONFIRM ITSELF, and they are asserted
rather than found: offset 0 is the system init by construction, because the
block starts there; and Halt sits at a fixed offset in every binary of one
corpus, checked on a ten-byte prefix because its longer body diverges on near
call displacements. Both are recorded as assumptions in the output's own terms.
"""
import argparse
import io
import json
import struct
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import project                                    # noqa: E402
from substrate import align                       # noqa: E402
from substrate.mzinfo import parse                # noqa: E402

try:
    import tomllib
except ModuleNotFoundError:                       # pragma: no cover -- 3.11+
    import tomli as tomllib                       # type: ignore

PROBE = 256          # bytes of the block's head used to find it elsewhere
SIG = 24             # bytes of a routine's body used as its pattern


def masked_image(h):
    """Image bytes with every relocation target zeroed.

    A relocated word holds a load-time segment value, which differs per binary
    for reasons that say nothing about the code. Zeroing them is what makes two
    copies of one routine compare equal.
    """
    raw = bytearray(h["raw"])
    base = h["hdrsize"]
    for i in range(h["nreloc"]):
        off, seg = struct.unpack_from("<HH", raw, h["reloff"] + i * 4)
        fa = base + seg * 16 + off
        if fa + 2 <= len(raw):
            raw[fa:fa + 2] = b"\0\0"
    return bytes(raw)


def seg_file_offset(h, seg, first_para):
    return h["hdrsize"] + (seg * 16) - first_para * 16


def common_prefix(a, b):
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i


# ---------------------------------------------------------------------------


def match(ref, ref_seg, ref_len, others, first_para):
    rh = parse(pathlib.Path(ref))
    rmask = masked_image(rh)
    roff = seg_file_offset(rh, ref_seg, first_para)
    rtl = rmask[roff:roff + ref_len]
    probe = rtl[:PROBE]

    print("reference %s seg %04x file+%#x len %#x"
          % (pathlib.Path(ref).name, ref_seg, roff, ref_len))
    for p in others:
        h = parse(pathlib.Path(p))
        mask = masked_image(h)
        # NOT an exact find(). Relocation masking handles the far pointers, and
        # for years this then matched a 256-byte probe byte for byte -- which
        # CANNOT succeed across two differently-linked binaries and never once
        # did. Measured on this corpus: the RTL head diverges at +0x07, seven
        # bytes in, on a DGROUP *offset* the mask does not touch because it is
        # not a relocation, and again at +0x0c on a near-call displacement the
        # smart linker places differently in every part. The tool reported
        # `RTL prologue NOT FOUND`, which reads as "no runtime here" rather
        # than "my rule is too strict" -- absence indistinguishable from zero.
        # align.locate is the engine built for exactly this tolerance.
        name = pathlib.Path(p).name
        idx, _ = align.locate(probe, mask[:h["imagesize"]], align.holes, None)
        if idx < 0:
            print("  %-22s RTL prologue NOT FOUND" % name)
            continue
        seg = (idx - h["hdrsize"] + first_para * 16) // 16
        other = mask[idx:h["imagesize"]]
        cp = common_prefix(rtl, other)
        n = min(len(rtl), len(other))
        same = sum(1 for i in range(n) if rtl[i] == other[i])
        print("  %-22s seg %04x file+%#08x avail %-6d "
              "identical prefix %-6d overall %.1f%% of %d"
              % (name, seg, idx, len(other), cp, 100.0 * same / n, n))
    return 0


def find(config, first_para):
    """Name RTL routines in every binary by pattern, from one reference.

    The per-binary RTL base, the reference binary and the confirmed
    offset-to-name table are all the project's -- each one was a constant.
    """
    with io.open(config, "rb") as fh:
        cfg = tomllib.load(fh)
    try:
        originals = project.get("target.original")
        root = project.find()
    except project.Missing as exc:
        return project.complain(exc)

    bases = {k: int(v, 16) if isinstance(v, str) else v
             for k, v in cfg["base"].items()}
    known = {int(k, 16): v for k, v in cfg["known"].items()}
    ref = cfg["reference"]

    def load(part):
        h = parse(root / originals[part])
        return (masked_image(h), seg_file_offset(h, bases[part], first_para),
                h["imagesize"])

    rmask, roff, _ = load(ref)
    sigs = {name: rmask[roff + off:roff + off + SIG]
            for off, name in known.items()}

    out = {}
    for part in bases:
        if part not in originals:
            print("%s: no original recorded -- skipped" % part)
            continue
        mask, base, size = load(part)
        rtl = mask[base:size]
        found = {}
        for name, sig in sigs.items():
            if len(set(sig)) <= 2:          # too bland to identify anything
                continue
            hits = []
            i = rtl.find(sig)
            while i >= 0 and len(hits) < 3:
                hits.append(i)
                i = rtl.find(sig, i + 1)
            if len(hits) == 1:
                found[hits[0]] = name
        # The two anchors the search cannot confirm on its own. See the header.
        for off, name in cfg.get("anchor", {}).items():
            off = int(off, 16)
            if off == 0:
                found.setdefault(0, name)
                continue
            prefix = cfg.get("anchor_prefix", 10)
            if base + off + prefix <= size:
                if mask[base + off:base + off + prefix] == \
                        rmask[roff + off:roff + off + prefix]:
                    found.setdefault(off, name)

        out[part] = found
        pairs = ",".join("%x=%s" % (o, n) for o, n in sorted(found.items()))
        print("%s: %2d routines located" % (part, len(found)))
        print("    %s" % pairs)

    where = cfg.get("out")
    if where:
        p = root / where
        p.parent.mkdir(parents=True, exist_ok=True)
        io.open(p, "w", encoding="utf-8", newline="\n").write(json.dumps(
            {k: {"%x" % o: n for o, n in v.items()} for k, v in out.items()},
            indent=1))
        print("  wrote %s" % where)
    return 0


def entries(config, want, first_para):
    """Likely procedure entry points, by prologue shape.

    Two prologues, and a framed routine has one of them:

        55 89 E5              PUSH BP / MOV BP,SP        no locals
        C8 nn nn 00           ENTER nn,0                 with locals

    LIKELY, not certain: either sequence occurs inside data and inside longer
    instructions, so this narrows a search rather than answering it.
    """
    with io.open(config, "rb") as fh:
        cfg = tomllib.load(fh)
    try:
        image = project.path("target.image")
    except project.Missing as exc:
        return project.complain(exc)

    d = pathlib.Path(image).read_bytes()
    hs = struct.unpack_from("<H", d, 8)[0] * 16
    img = d[hs:]

    # Each segment's extent comes from the ONE segment list, with the next
    # segment's address bounding each -- rather than a second table of lengths,
    # which is what had drifted between two other instruments.
    segs = [(s["segment"], s["name"]) for s in cfg["segments"]]
    bounds = segs + [(cfg["end_at"], None)]
    extents = [(a, (b - a) * 16) for (a, _), (b, _) in zip(bounds, bounds[1:])]

    total = 0
    for seg, size in extents:
        if want and ("%04x" % seg) not in want:
            continue
        base = seg * 16 - first_para * 16
        found = []
        i = 0
        while i < size - 3:
            b = img[base + i:base + i + 4]
            if len(b) < 4:
                break
            if b[:3] == b"\x55\x89\xe5":
                found.append((i, "PUSH BP"))
                i += 3
                continue
            if b[0] == 0xC8 and b[3] == 0x00:
                found.append((i, "ENTER $%03x"
                              % struct.unpack_from("<H", b, 1)[0]))
                i += 4
                continue
            i += 1
        total += len(found)
        print("== %04x  (%d bytes)  %d entry points" % (seg, size, len(found)))
        if want:
            for off, kind in found:
                print("     %04x:%04x  %s" % (seg, off, kind))
    if not want:
        print("")
        print("total entry points found: %d" % total)
    return 0


# ---------------------------------------------------------------------------


def main(argv):
    ap = argparse.ArgumentParser(prog="rtl.py")
    sub = ap.add_subparsers(dest="cmd")

    m = sub.add_parser("match", help="find the RTL block and measure agreement")
    m.add_argument("ref")
    m.add_argument("ref_seg")
    m.add_argument("ref_len")
    m.add_argument("others", nargs="+")

    f = sub.add_parser("find", help="name RTL routines by pattern")
    f.add_argument("config")

    e = sub.add_parser("entries", help="likely procedure starts, by prologue")
    e.add_argument("config")
    e.add_argument("segs", nargs="*")

    args = ap.parse_args(argv)
    if not args.cmd:
        ap.print_help()
        return 2
    first = project.get("target.first_para", quiet=True)
    if args.cmd == "match":
        return match(args.ref, int(args.ref_seg, 16), int(args.ref_len, 16),
                     args.others, first)
    if args.cmd == "find":
        return find(args.config, first)
    if args.cmd == "entries":
        return entries(args.config, args.segs, first)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
