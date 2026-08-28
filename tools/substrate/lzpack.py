#!/usr/bin/env python3
r"""Pack an MZ executable the way LZEXE 0.91 did, and compare against the original.

    python lzpack.py EXE PACKED            pack EXE, compare against PACKED
    python lzpack.py EXE PACKED --out F    ...and keep the result
    python lzpack.py --tokens FILE         dump any LZ91 file's token stream
    python lzpack.py --selftest PATH ...   re-compress every LZ91 file under PATH
                                           (files or directories), to show the
                                           encoder is not fitted to one sample

PACKED is an existing LZEXE 0.91 file. It is needed for two things: the
comparison, and the 344-byte decompressor stub, which is LZEXE's own machine
code and is copied verbatim rather than invented. So this reproduces a packed
file you already have; it cannot pack from nothing.

THE INVERSE OF `unlzexe.py`, and the last gate on the fidelity ladder. Unpacking
gets you an image to measure against; it does not tell you whether your rebuild
would have produced the FILE that shipped. LZEXE itself is a 1989 third-party
packer that a project may not have and should not have to go and fetch, so the
packer is written out instead.

WRITTEN FOR the DemoVT 1.31b reconstruction, where the target ships as an
LZEXE-packed `NEUROSIS.008` inside the Psycho Neurosis demo and 1:1 against the
UNPACKED image was the ceiling until this existed. It closed that gate: source
-> TPC -> EXE -> packed -> the shipped file, byte for byte.

============================================================================
THE ENCODER, and every rule here was MEASURED against the original's own
token stream rather than taken from a description of the format.
============================================================================

`unlzexe.py` documents the bitstream. It does not say how LZEXE CHOSE among the
encodings, and a packer needs exactly that. The method was to decode the
original's 21,020 tokens, then run candidate matchers against them and count how
long a prefix agreed. That turns "what would a packer do" into a measurement.

  * PLAIN GREEDY LONGEST MATCH, NEAREST ON A TIE. Cost-based lazy matching
    agrees for 198 tokens; a pure nearest-match rule agrees for 56. Plain greedy
    agrees for 3,724 -- and then for all 21,018 once the window below is right.
    LZEXE is not clever, and trying to be clever is measurably wrong: a lazy
    matcher beats it by 3,029 bits and reproduces nothing.

  * THE SEARCH WINDOW IS 7,939 = 0x2000 - 253, the format's maximum distance
    LESS the maximum match length. This was the whole puzzle, and it is a
    derived constant rather than a fitted one -- it is exactly the ring buffer
    minus the longest match that can be taken out of it, which is what a 1989
    ring-buffer matcher would enforce. The tell: at output offset 10,569 the
    original spends 12 bits on a 2-byte match at distance 146 while a 5-byte
    match sits at distance 8,019, so it never saw the better one.

    NEUROSIS.008 ALONE CANNOT PIN THE VALUE -- the largest distance it uses is
    7,931, so anything in 7,932..7,940 reproduces it. The ten other LZ91 files
    listed under --selftest settle it: MAKESTR.EXE and DEMOVT.EXE both use a
    distance of 7,939, which is the largest in any of the ten, and 7,944 breaks
    four files. A window of 0x1F00 was the first guess and it is WRONG -- it
    reproduces this target but fails two of the others.

  * THE ENCODING FOR A GIVEN (length, distance) IS FORCED, so no preference had
    to be discovered: length 2..5 within 255 goes short (12 bits), length 3..9
    goes long (18), length 10 and up goes ext (26). Where short and long both
    fit, short is cheaper and the original always takes it. Length 2 beyond 255
    is not encodable at all and becomes a literal.

  * ON A TIE THE NEAREST MATCH WINS -- the comparison is strictly greater as
    the chain is walked from nearest outwards. This is not a detail: taking the
    FARTHEST of equal-length matches instead reproduces NONE of the eleven
    files, not one.

MINIMUM MATCH IS TWO BYTES, and the match search keys on two bytes.

VALIDATED ON TEN OTHER LZEXE 0.91 FILES, which is the only defence against
having fitted the rules to one file. `--selftest` finds every LZ91 file in the
tree, unpacks each, re-compresses the image and compares token streams.
**NINE OF THE ELEVEN reproduce exactly**, NEUROSIS.008 among them -- 63,040
bytes and 23,696 tokens for the largest, DemoVT 1.51's own DEMOVT.EXE.
(EXAMPLE.EXE and PASTST.EXE are byte-identical to each other, so the eleven are
ten distinct images.)

THE TWO THAT DO NOT ARE BOTH A TAIL EFFECT, and it is recorded rather than
smoothed over:

    BIN2DB.EXE     11 bytes from the end: the original takes its 11-byte match
                   at distance 254 where distances 12 through 17 all give the
                   same 11 bytes. So at the tail it does NOT prefer the nearest.
    PMODETST.EXE    2 bytes from the end: the original emits two literals where
                   a 2-byte match sits at distance 5.

Both are within the last 11 bytes of the image, both are the final match
decision before end-of-stream, and neither is explained by the rules above. A
binary-search-tree match finder would produce exactly this -- which of several
equal-length matches you get depends on tree shape, not distance -- but that is
a hypothesis, not a reading of LZEXE. It does not affect this target: the tail
of NEUROSIS.008 reproduces exactly.

============================================================================
WHAT IS COMPUTED HERE AND WHAT IS COPIED -- read this before believing a result
============================================================================

COMPUTED from our own build, and these are the claim:

    the compressed bitstream    30,480 bytes   the encoder above
    the relocation table           855 bytes   linear deltas, LZ91's escapes
    the MZ header's sizes                      lastsize, nblocks, hdrsize, cs

DERIVED, and two of these were open questions until the stub was disassembled:

    the segment-step tokens                    emitted at the first token
                                               boundary where the stub's DI
                                               reaches 0xA000, then DI resets
                                               to (DI & 15) + 0x2000. Read off
                                               the handler at stub offset 0xd1,
                                               not fitted -- and DEMOVT.EXE,
                                               63,040 bytes with its step at
                                               0xA00D, reproduces on that rule
                                               alone.
    the tail rule                              no match with fewer than 3 bytes
                                               left. See MIN_TAIL.

COPIED from the reference packed file, and no reimplementation could produce
them:

    the decompressor stub          344 bytes   LZEXE's own machine code, and
                                               its head holds the original
                                               entry point, stack, and the
                                               comp/inc/dec paragraph counts
                                               that describe THIS image
    ss:sp, ip in the MZ header                 the stub's own frame
    minalloc, maxalloc                         LZEXE's allocation arithmetic,
                                               not yet derived

So a byte-identical result proves the ENCODER and the relocation packing, not
the 32-byte header. That is stated plainly rather than smoothed over, because
"we reproduced the packed file" would otherwise read as a stronger claim than
the evidence supports. The 31,335 bytes of stream and table are 98.8% of the
file and they are the part a packer has to get right.

ONE THING IS STILL OPEN, and it is one token in one file. `BIN2DB.EXE`, 11 bytes
from the end, takes its 11-byte match at DISTANCE 254 -- which is neither the
nearest nor the farthest of the 11-length matches available there. They run from
distance 12 to distance 3,569, and 254 sits arbitrarily among them. So at that
point LZEXE searched a PROPER SUBSET of the candidates and the subset is not
explained by anything here.

WHAT HAS BEEN RULED OUT for it, so a later session need not re-run these:

    indexing only token-start positions    fails immediately on all 11 files
                                           (30 of 2,285 on BIN2DB) -- LZEXE
                                           does index every position
    a cap on how late a match source may
    sit in the image (len-252/253/254)     breaks all 11
    preferring the FARTHEST on a tie       breaks all 11 -- nearest is right
                                           everywhere else
    a longer minimum tail (4 or 5)         breaks BCCTST.EXE and NEUROSIS.008,
                                           which end in 3-byte matches

A hash structure whose chain order is not position order would explain it -- a
binary search tree, where which of several equal-length matches you get depends
on tree shape -- but that is a hypothesis and is labelled one. It does not affect
the DemoVT target, whose own tail reproduces exactly.
"""
import struct
import sys
import bisect
import pathlib

MIN_MATCH = 2
MAX_MATCH = 253           # ext carries len-1 in a byte, and 254 would collide
MAX_DIST = 0x2000         # what the long/ext encoding can express
WINDOW = MAX_DIST - MAX_MATCH   # 7,939 -- see the header; NOT 0x1F00
STUB_LEN = 0x158          # 344 bytes of LZEXE decompressor
CONTROL = (0x00, 0xF0)    # the lo/hi the original uses for segstep and eos

# THE SEGMENT STEP, read off the stub rather than guessed. Its handler at stub
# offset 0xd1 is
#
#     mov bx,di / and di,0Fh / add di,2000h    ; DI := (DI & 15) + 0x2000
#     shr bx,4 / mov ax,es / add ax,bx / sub ax,200h / mov es,ax
#
# so it renormalises ES:DI to keep DI at or above 0x2000, preserving the linear
# address. THAT FLOOR IS WHY 0x2000 IS THE DISTANCE LIMIT: the back-reference is
# `mov al, es:[bx+di]` with BX forced into 0xE000..0xFFFF by `or bh,0E0h`, i.e. a
# 16-bit negative offset of -0x2000..-1, so DI must never drop below 0x2000 or
# the read wraps out of the segment. The encoder emits a step at the first token
# boundary where DI has reached SEGSTEP_DI, which leaves 0x6000 of headroom
# before DI would overflow 0xFFFF.
SEGSTEP_DI = 0xA000
DI_FLOOR = 0x2000
MIN_TAIL = 3              # no match is attempted with fewer bytes than this left

COSTS = {"lit": 9, "short": 12, "long": 18, "ext": 26}


def packed_path(p):
    """The existing LZ91 file: the comparison target, and the source of the stub."""
    q = pathlib.Path(p)
    if not q.is_file():
        raise SystemExit("no such packed file: %s" % q)
    blob = q.read_bytes()
    if blob[0x1C:0x20] != b"LZ91":
        raise SystemExit("%s is not an LZ91 file (no 'LZ91' at 0x1c)" % q)
    return q, blob


# ---------------------------------------------------------------------------
# Reading an MZ file


def mz(blob):
    """(load image, relocation linear targets, header fields) of an MZ file."""
    (lastsize, nblocks, nreloc, hdrsize, minalloc, maxalloc,
     ss, sp, _chk, ip, cs, lfarlc, _ovno) = struct.unpack_from("<13H", blob, 2)
    total = (nblocks - 1) * 512 + (lastsize or 512)
    image = blob[hdrsize * 16:total]
    lin = []
    for i in range(nreloc):
        o, s = struct.unpack_from("<HH", blob, lfarlc + i * 4)
        lin.append(s * 16 + o)
    return image, sorted(lin), dict(ss=ss, sp=sp, ip=ip, cs=cs,
                                    minalloc=minalloc, maxalloc=maxalloc)


# ---------------------------------------------------------------------------
# The bit stream


class BitWriter:
    r"""LZEXE's stream: 16-bit words consumed LSB first, bytes BETWEEN words.

    THE REFILL MUST BE EAGER, mirroring the decoder exactly. `unlzexe.py`'s own
    docstring records the trap from the other side: the stub does

        SHR BP,1 / DEC DX / JNZ + / LODSW / MOV BP,AX / MOV DL,10h

    so when the sixteenth bit is taken the next bit-word is pulled from the
    stream IMMEDIATELY, and a literal byte belonging to that bit is read from
    after it. Emitting the next word lazily -- when the following bit is needed
    -- puts the literal where the decoder expects the word, and the stream
    drifts about seventy bytes in. So `bit()` allocates the next word slot the
    moment the current one fills, and `byte()` appends after it.
    """

    def __init__(self):
        self.buf = bytearray()
        self._slot()

    def _slot(self):
        self.wpos = len(self.buf)
        self.buf += b"\0\0"
        self.n = 0
        self.acc = 0

    def bit(self, b):
        if b:
            self.acc |= 1 << self.n
        self.n += 1
        if self.n == 16:
            struct.pack_into("<H", self.buf, self.wpos, self.acc)
            self._slot()

    def byte(self, v):
        self.buf.append(v & 0xFF)

    def done(self):
        """Flush the part-filled word. Unused high bits stay zero."""
        struct.pack_into("<H", self.buf, self.wpos, self.acc)
        return bytes(self.buf)


def emit(w, kind, ln, dist):
    if kind == "lit":
        w.bit(1)
        w.byte(ln)                       # for a literal, ln carries the byte
        return
    if kind == "short":
        w.bit(0)
        w.bit(0)
        w.bit(((ln - 2) >> 1) & 1)       # the decoder reads the HIGH bit first
        w.bit((ln - 2) & 1)
        w.byte(0x100 - dist)
        return
    span = 0x10000 - dist
    lo = span & 0xFF
    hi = (span & 0x1F00) >> 5
    if kind == "long":
        w.bit(0)
        w.bit(1)
        w.byte(lo)
        w.byte(hi | (ln - 2))            # ln 3..9 -> 1..7, never 0
        return
    if kind == "ext":
        w.bit(0)
        w.bit(1)
        w.byte(lo)
        w.byte(hi)                       # low three bits zero -> read a length
        w.byte(ln - 1)
        return
    if kind in ("segstep", "eos"):
        w.bit(0)
        w.bit(1)
        w.byte(CONTROL[0])
        w.byte(CONTROL[1])
        w.byte(1 if kind == "segstep" else 0)
        return
    raise AssertionError(kind)


# ---------------------------------------------------------------------------
# The matcher


def encoding(ln, dist):
    """The one encoding LZEXE uses for a (length, distance), or None."""
    if ln < MIN_MATCH:
        return None
    if 2 <= ln <= 5 and dist <= 255:
        return "short"
    if 3 <= ln <= 9:
        return "long"
    if ln >= 10:
        return "ext"
    return None                          # length 2 beyond 255: not encodable


def tokenize(img, window=WINDOW):
    """Greedy longest match, nearest on a tie, within `window`. See the header."""
    n = len(img)
    index = {}
    for i in range(n - 1):
        index.setdefault(img[i] << 8 | img[i + 1], []).append(i)

    toks = []
    p = 0
    di = 0                                # the stub's destination offset
    while p < n - 1:
        if di >= SEGSTEP_DI:
            toks.append(("segstep", 0, 0))
            di = (di & 0xF) + DI_FLOOR
        lst = index.get(img[p] << 8 | img[p + 1], ())
        j = bisect.bisect_left(lst, p) - 1
        limit = min(MAX_MATCH, n - p)
        floor = p - window
        best_len, best_dist = 0, 0
        while j >= 0 and lst[j] >= floor:
            s = lst[j]
            j -= 1
            k = 2
            while k < limit and img[s + k] == img[p + k]:
                k += 1
            if k > best_len:              # strictly greater: ties keep NEAREST
                best_len, best_dist = k, p - s
                if best_len == limit:
                    break
        # THE TAIL RULE: with fewer than MIN_TAIL bytes left no match is
        # attempted at all, however good one looks. Measured, and bracketed from
        # both sides -- 3 reproduces every file that reaches its tail, while 4
        # breaks the ones ending in a 3-byte match (BCCTST.EXE) and 5 breaks
        # NEUROSIS.008 too. Without it PMODETST.EXE takes a 2-byte match at
        # distance 5 where the original spends two literals.
        kind = encoding(best_len, best_dist) if (n - p) >= MIN_TAIL else None
        if kind is None:
            toks.append(("lit", img[p], 0))
            p += 1
            di += 1
        else:
            toks.append((kind, best_len, best_dist))
            p += best_len
            di += best_len
    while p < n:                          # the last byte can never start a match
        toks.append(("lit", img[p], 0))
        p += 1
    toks.append(("eos", 0, 0))
    return toks


def compress(img, window=WINDOW):
    toks = tokenize(img, window)
    w = BitWriter()
    for kind, a, b in toks:
        emit(w, kind, a, b)
    return w.done(), toks


# ---------------------------------------------------------------------------
# The relocation table


def pack_relocs(linear):
    """LZ91's table: byte deltas between LINEAR targets, 0 escaping to a word.

    The decoder keeps (seg, off), adds each delta to `off` and normalises by
    moving 0x10 of offset into 1 of segment -- which preserves seg*16+off. So
    every delta is simply the gap between consecutive LINEAR addresses, and the
    0x0000 escape adds 0xFFF to the segment, i.e. 0xFFF0 to the linear address.
    """
    out = bytearray()
    prev = 0
    for lin in linear:
        gap = lin - prev
        prev = lin
        while gap > 0xFFFF:               # step the segment forward
            out.append(0)
            out += struct.pack("<H", 0)
            gap -= 0xFFF0
        if gap == 0:
            raise SystemExit("two relocations at the same address -- cannot encode")
        if gap <= 0xFF:
            out.append(gap)
        else:
            out.append(0)
            out += struct.pack("<H", gap)
    out.append(0)
    out += struct.pack("<H", 1)           # terminator
    return bytes(out)


# ---------------------------------------------------------------------------
# Building the packed file


def build(exe, ref):
    """Pack `exe`, taking LZEXE's stub and frame fields from packed file `ref`."""
    image, linear, _fields = mz(exe)

    stream, toks = compress(image)
    while len(stream) % 16:                # pad the compressed data to a paragraph
        stream += b"\0"

    table = pack_relocs(linear)

    # The stub, verbatim. Its own head words describe THIS image -- the original
    # entry point and stack, and the comp/inc/dec paragraph counts -- so they are
    # only right while our compressed data is the same length as the original's.
    rhdrpara = struct.unpack_from("<H", ref, 8)[0]
    rcs = struct.unpack_from("<H", ref, 0x16)[0]
    rstub = rhdrpara * 16 + rcs * 16
    stub = ref[rstub:rstub + STUB_LEN]
    rcomp = struct.unpack_from("<H", ref, rstub + 8)[0]
    if len(stream) // 16 != rcomp:
        print("  NOTE compressed data is %d paragraphs, the stub says %d --"
              % (len(stream) // 16, rcomp))
        print("       the stub's comp/inc/dec describe the original's stream, so a")
        print("       different length makes them wrong and the file will not run.")

    hdrsize = 2                            # 32 bytes; LZEXE writes no reloc table
    body = stream + stub + table
    total = hdrsize * 16 + len(body)

    hdr = bytearray(hdrsize * 16)
    hdr[0:2] = b"MZ"
    struct.pack_into("<H", hdr, 2, total % 512)
    struct.pack_into("<H", hdr, 4, (total + 511) // 512)
    struct.pack_into("<H", hdr, 6, 0)                       # nreloc: none
    struct.pack_into("<H", hdr, 8, hdrsize)
    # COPIED, not derived -- see the header. minalloc/maxalloc are LZEXE's
    # allocation arithmetic and ss:sp/ip are the stub's own frame.
    for off in (10, 12, 14, 16, 20):
        struct.pack_into("<H", hdr, off, struct.unpack_from("<H", ref, off)[0])
    struct.pack_into("<H", hdr, 22, len(stream) // 16)      # cs: the stub's para
    struct.pack_into("<H", hdr, 24, 0x1C)                   # lfarlc
    hdr[0x1C:0x20] = b"LZ91"

    return bytes(hdr) + body, toks, len(stream), len(table), len(stub)


# ---------------------------------------------------------------------------
# Reading a packed file back -- the token dump, and the round trip


def decode(blob):
    """Walk an LZ91 stream, returning (image, tokens)."""
    hdrpara = struct.unpack_from("<H", blob, 8)[0]
    cs = struct.unpack_from("<H", blob, 0x16)[0]
    stub = hdrpara * 16 + cs * 16
    comp = struct.unpack_from("<H", blob, stub + 8)[0]
    p = (hdrpara + cs - comp) * 16

    word = struct.unpack_from("<H", blob, p)[0]
    p += 2
    left = 16

    def bit():
        nonlocal word, p, left
        b = word & 1
        word >>= 1
        left -= 1
        if left == 0:
            word = struct.unpack_from("<H", blob, p)[0]
            p += 2
            left = 16
        return b

    def byte():
        nonlocal p
        v = blob[p]
        p += 1
        return v

    out = bytearray()
    toks = []
    while True:
        if bit():
            v = byte()
            toks.append(("lit", v, 0))
            out.append(v)
            continue
        if not bit():
            ln = ((bit() << 1) | bit()) + 2
            span = byte() | 0xFF00
            kind = "short"
        else:
            lo = byte()
            hi = byte()
            span = lo | ((hi & 0xF8) << 5) | 0xE000
            ln = (hi & 0x07) + 2
            kind = "long"
            if ln == 2:
                ln = byte()
                if ln == 0:
                    toks.append(("eos", 0, 0))
                    break
                if ln == 1:
                    toks.append(("segstep", 0, 0))
                    continue
                ln += 1
                kind = "ext"
        toks.append((kind, ln, 0x10000 - span))
        span -= 0x10000
        for _ in range(ln):
            out.append(out[len(out) + span])
    return bytes(out), toks


def dump_tokens(path):
    blob = pathlib.Path(path).read_bytes()
    if blob[0x1C:0x20] != b"LZ91":
        raise SystemExit("%s is not an LZ91 file" % path)
    image, toks = decode(blob)
    kinds = {}
    for k, a, b in toks:
        kinds[k] = kinds.get(k, 0) + 1
    print("%s" % path)
    print("  decodes to %d bytes in %d tokens" % (len(image), len(toks)))
    for k in ("lit", "short", "long", "ext", "segstep", "eos"):
        if k in kinds:
            print("    %-8s %6d" % (k, kinds[k]))
    for k in ("short", "long", "ext"):
        sel = [(a, b) for kk, a, b in toks if kk == k]
        if sel:
            print("    %-8s len %d..%d  dist %d..%d"
                  % (k, min(x[0] for x in sel), max(x[0] for x in sel),
                     min(x[1] for x in sel), max(x[1] for x in sel)))
    bits = sum(COSTS[k] for k, _, _ in toks if k in COSTS)
    print("  stream cost %d bits = %d bytes of token payload" % (bits, bits // 8))
    pos = 0
    for i, (k, a, _b) in enumerate(toks):
        if k == "segstep":
            print("  segment step at token %d, output offset %d (0x%x)" % (i, pos, pos))
        pos += 1 if k == "lit" else (a if k in ("short", "long", "ext") else 0)
    return 0


# ---------------------------------------------------------------------------
# The comparison


def compare(ours, theirs, toks, nstream, ntable, nstub):
    print("  packed  %d bytes" % len(ours))
    print("  original %d bytes" % len(theirs))
    print()
    print("           computed: %d bytes of stream + %d of relocations = %d"
          % (nstream, ntable, nstream + ntable))
    print("           copied:   %d of stub + 32 of header = %d"
          % (nstub, nstub + 32))
    print()

    if ours == theirs:
        print("  BYTE-IDENTICAL to the original packed file.")
        return True

    if len(ours) != len(theirs):
        print("  SIZE DIFFERS by %+d bytes" % (len(ours) - len(theirs)))
    diffs = [i for i in range(min(len(ours), len(theirs))) if ours[i] != theirs[i]]
    print("  %d differing byte(s)" % len(diffs))
    if not diffs:
        return False
    first = diffs[0]
    # which region?
    where = ("the 32-byte header" if first < 32
             else "the compressed stream" if first < 32 + nstream
             else "the stub" if first < 32 + nstream + nstub
             else "the relocation table")
    print("  first difference at 0x%x, in %s" % (first, where))
    print("    ours 0x%02x  original 0x%02x" % (ours[first], theirs[first]))

    if first >= 32 + nstream and first < 32 + nstream + nstub:
        print("    -- the stub is copied verbatim, so this means the reference and")
        print("       the comparison target are different files.")
    if 32 <= first < 32 + nstream:
        _img, theirtoks = decode(bytes(theirs))
        n = 0
        for a, b in zip(toks, theirtoks):
            if a != b:
                break
            n += 1
        print("    token streams agree for %d of %d tokens" % (n, len(theirtoks)))
        if n < len(theirtoks) and n < len(toks):
            pos = 0
            for k, a, _ in toks[:n]:
                pos += 1 if k == "lit" else (a if k in ("short", "long", "ext") else 0)
            print("    first differing token %d at output offset %d (0x%x):"
                  % (n, pos, pos))
            print("      ours     %s" % (toks[n],))
            print("      original %s" % (theirtoks[n],))
    return False


def selftest(paths):
    """Re-compress every LZ91 file given and check the token stream reproduces.

    THIS IS THE DEFENCE AGAINST FITTING THE RULES TO ONE FILE. The encoder was
    derived by measuring NEUROSIS.008's own stream, and rules derived from one
    sample reproduce that sample by construction. So it is run against every
    other LZEXE 0.91 file to hand.

    Every token compared is ours, the segment steps included.
    """
    print("%-26s %7s %7s  %s" % ("file", "image", "tokens", "reproduces?"))
    good = 0
    for path in paths:
        blob = pathlib.Path(path).read_bytes()
        if blob[0x1C:0x20] != b"LZ91":
            print("%-26s  not an LZ91 file -- skipped" % pathlib.Path(path).name)
            continue
        image, theirs = decode(blob)
        # NOTHING IS FED IN FROM THE ORIGINAL ANY MORE. Until the segment-step
        # rule was read off the stub, this had to be given the original's own
        # step positions, which weakened the test to "everything except the
        # steps". The whole stream is ours now, control tokens included.
        merged = tokenize(image)

        if merged == theirs:
            good += 1
            note = "YES, all %d tokens" % len(theirs)
        else:
            n = 0
            for a, b in zip(merged, theirs):
                if a != b:
                    break
                n += 1
            at = 0
            for k, a, _b in merged[:n]:
                at += 1 if k == "lit" else (a if k in ("short", "long", "ext") else 0)
            note = ("no -- %d of %d, then ours %s vs %s at offset %d (%d bytes from the end)"
                    % (n, len(theirs), merged[n] if n < len(merged) else None,
                       theirs[n] if n < len(theirs) else None, at, len(image) - at))
        print("%-26s %7d %7d  %s" % (pathlib.Path(path).name, len(image), len(theirs), note))
    print()
    print("%d of %d file(s) reproduce exactly" % (good, len(paths)))
    return 0 if good == len(paths) else 1


def find_lz91(roots):
    """Every LZ91 file under `roots`, smallest first -- for --selftest with no args."""
    out = []
    for r in roots:
        rp = pathlib.Path(r)
        if not rp.exists():
            raise SystemExit("no such path: %s" % rp)
        # A FILE NAMED DIRECTLY IS KEPT. rglob on a file yields nothing, so an
        # earlier version silently dropped every path that was not a directory
        # -- and a self-test that quietly tests fewer files than you asked for is
        # worse than one that fails.
        candidates = sorted(rp.rglob("*")) if rp.is_dir() else [rp]
        for f in candidates:
            if not f.is_file():
                continue
            try:
                head = f.open("rb").read(0x20)
            except OSError:
                continue
            if len(head) >= 0x20 and head[:2] in (b"MZ", b"ZM") and head[0x1C:0x20] == b"LZ91":
                out.append(f)
    return sorted(out, key=lambda f: f.stat().st_size)


def main(argv):
    args, out, exe, packed, tokens = [], None, None, None, None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--out":
            out = argv[i + 1]
            i += 2
        elif a == "--exe":
            exe = argv[i + 1]
            i += 2
        elif a == "--packed":
            packed = argv[i + 1]
            i += 2
        elif a == "--tokens":
            tokens = argv[i + 1]
            i += 2
        elif a == "--selftest":
            i += 1
            rest = []
            while i < len(argv) and not argv[i].startswith("-"):
                rest.append(argv[i])
                i += 1
            if not rest:
                raise SystemExit("--selftest needs paths: files or directories to search for LZ91 files")
            return selftest(find_lz91(rest))
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        else:
            args.append(a)
            i += 1

    if tokens:
        return dump_tokens(tokens)

    if exe is None and args:
        exe = args.pop(0)
    if packed is None and args:
        packed = args.pop(0)
    if not exe or not packed:
        print("need two files: an unpacked EXE to pack, and an existing LZ91")
        print("file to compare against and take the decompressor stub from.")
        print("    python lzpack.py EXE PACKED")
        return 2
    exepath = pathlib.Path(exe)
    if not exepath.is_file():
        raise SystemExit("no such EXE: %s" % exepath)
    refpath, ref = packed_path(packed)

    print("packing   %s" % exepath)
    print("stub from %s" % refpath)
    blob, toks, nstream, ntable, nstub = build(exepath.read_bytes(), ref)

    # Prove the packer before comparing it: our own file must decode back to the
    # image we fed in. A byte-identical result would imply this, but a
    # NON-identical one still has to be either right or wrong, and this says which.
    image, _lin, _f = mz(exepath.read_bytes())
    back, _ = decode(blob)
    if back == image:
        print("round trip: our packed file decodes back to the input image exactly")
    else:
        print("ROUND TRIP FAILED: %d of %d bytes recovered -- the packer is WRONG"
              % (sum(1 for a, b in zip(back, image) if a == b), len(image)))
        return 1

    print()
    ok = compare(blob, ref, toks, nstream, ntable, nstub)

    if out:
        pathlib.Path(out).write_bytes(blob)
        print("\nwrote %s" % out)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
