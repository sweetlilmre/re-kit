#!/usr/bin/env python3
r"""Pack an MZ executable the way LZEXE 0.91 did, and compare against the original.

    python kit/tools/substrate/lzpack.py EXE PACKED            pack EXE, compare against PACKED
    python kit/tools/substrate/lzpack.py EXE PACKED --out F    ...and keep the result
    python kit/tools/substrate/lzpack.py --tokens FILE         dump any LZ91 file's token stream
    python kit/tools/substrate/lzpack.py --selftest PATH ...   re-compress every LZ91 file under PATH
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
THE ENCODER IS A PORT OF LZEXE'S OWN, not a model of it
============================================================================

`tokenize()` is LZEXE 0.91's `LZCOMP` from `lzss.asm`, ported line for line.

    LZEXE source code, Copyright (c) 1989-1990 Fabrice Bellard, MIT licence.
    Published by its author at https://bellard.org/lzexe/ -- the archive is
    lzexe91-src.zip, and LICENSE inside it is the MIT text. This file carries
    that notice because the algorithm below is derived from that source.

IT REPRODUCES EVERY LZ91 FILE TESTED, TOKEN FOR TOKEN -- twelve of twelve, from
4,176 to 63,040 bytes, spanning three unrelated authors: the DemoVT 1.31b target
`NEUROSIS.008`, DemoVT 1.51's own tools, and Borland's `INTRFC.EXE` from the
Turbo Pascal 7.01 distribution. `--selftest` re-runs that.

HOW THIS FILE GOT HERE, because the history is the useful part and the first
version of it shipped. The rules were originally REVERSE-ENGINEERED by decoding
the target's own stream into tokens and scoring candidate matchers by how long a
prefix each reproduced. That worked: greedy longest match, nearest on a tie, in a
7,939-byte window got eleven of twelve files exactly. Then the source turned up,
and it corrected three things the measurement had got wrong or right by accident:

  * A "no match with fewer than 3 bytes left" rule had been MEASURED and
    bracketed, and it does not exist. What exists is that the compare length is
    never clamped to the remaining input -- only the emitted length is -- so near
    the end of a file the search runs into stale ring content and often picks a
    distance too far to encode a 2-byte match. The invented rule was a
    description of that effect that happened to fit.
  * THE SEGMENT STEP resets `SEGSIZE` to zero. The reverse-engineered version
    reset a running counter to `(DI & 15) + 0x2000`, reasoning from the stub's
    handler, and it agreed with every file to hand only because no file needs
    more than one step.
  * THE 7,939 WINDOW is right but not for the reason given. It is not
    "0x2000 minus the longest match" as a rule; the first read simply lands at
    ring offset `BUFSIZE-LENMAX` with the write pointer `LENMAX` ahead of the
    coding pointer, so that much history is what the ring leaves behind it.

The measured rules also could not reproduce the last token of `BIN2DB.EXE`, and
no rule of that shape could: it takes an 11-byte match at distance 254 where
every distance from 12 to 3,569 gives the same bytes. The port gets it right for
free, because the reason is the unclamped compare reading ring content that was
never overwritten.

WORTH KEEPING FROM ALL THAT: measuring against one artefact gets you a long way
and tells you honestly how far, but it cannot distinguish a rule from a
coincidence that fits. Where the source exists, read the source.

============================================================================
WHAT IS COMPUTED HERE AND WHAT IS COPIED -- read this before believing a result
============================================================================

COMPUTED from our own build, and these are the claim:

    the compressed bitstream    30,480 bytes   the encoder above
    the relocation table           855 bytes   linear deltas, LZ91's escapes
    the MZ header's sizes                      lastsize, nblocks, hdrsize, cs

DERIVED by the port, and each was an open question before the source was read:

    the segment-step tokens                    emitted when the running total of
                                               emitted lengths reaches 0xA000,
                                               which then resets to zero
    the tail behaviour                         falls out of the unclamped
                                               compare; there is no rule

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

NOTHING IS KNOWN TO BE UNREPRODUCED. `--selftest` still distinguishes
OUTPUT-EQUIVALENT from WRONG -- two token streams can decode to the same bytes,
so that distinction stays worth reporting -- but every file tested reproduces
the stream itself.

WHAT REMAINS COPIED IS THE HEADER ARITHMETIC, not the compression: `minalloc`,
`maxalloc` and the stub's own `ss:sp`/`ip`. `exepack.asm` and `lzexe.pas` in the
same archive hold that logic and porting it would close the last 376 bytes; it
has not been done.
"""
import struct
import sys
import bisect
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import project                                                    # noqa: E402

# LZEXE's own constants, from lzss.asm's DATA segment.
BUFSIZE = 0x2000          # the ring buffer -- BUFSIZE equ 2000h
LENMAX = 253              # the longest match -- LENMAX equ 253
TABSIZE = 4096            # hash buckets -- TABSIZE equ 4096
TABAND = 0xFFF            # and the 12-bit mask over the 2-byte key
RIEN = BUFSIZE            # the end-of-chain sentinel (RIEN equ BUFSIZE*2, in words)
CMPLEN = LENMAX - 1       # `mov cx,LENMAX-1` before the repz cmpsb
SEGLIMIT = 0xA000         # `cmp SEGSIZE,0A000h`

# WHERE THE 7,939 COMES FROM. The first read lands at ring offset
# BUFSIZE-LENMAX and the write pointer runs LENMAX ahead of the coding
# pointer, so the history behind it is BUFSIZE-LENMAX bytes. It is the ring's
# geometry, not a tuned window.
WINDOW = BUFSIZE - LENMAX

STUB_LEN = 0x158          # 344 bytes of LZEXE decompressor
CONTROL = (0x00, 0xF0)    # the lo/hi LZEXE writes for segstep and eos

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


def tokenize(img):
    """LZEXE 0.91's own LZCOMP, ported from lzss.asm. See the module header.

    A PORT, NOT A MODEL. Everything here mirrors the assembler line for line,
    including the parts that look like accidents, because the accidents are what
    a byte-exact reproduction needs:

      * THE CHAIN IS A HASH CHAIN, newest-first, despite the source calling its
        arrays RSON and DAD. `InsertNode` pushes at the head, so walking it is
        walking backwards in time -- which is why the nearest match wins a tie.
      * THE KEY IS ONLY 12 BITS of the two-byte word (`and ax,TABAND`), so a
        bucket mixes positions whose second byte differs in its high nibble.
        Those fail the compare; they cost time and change nothing.
      * `cmp cx,ax / jae` TAKES A CANDIDATE ONLY IF STRICTLY LONGER, so ties
        keep the one found first -- the most recent.
      * THE COMPARE LENGTH IS ALWAYS CMPLEN, never clamped to the input that is
        left. Only the EMITTED length is clamped, by `cmp ax,LENREST` in the
        main loop. So near the end of a file the compare runs off the data and
        into whatever the ring still holds, and the match it picks depends on
        that stale content. This is not a defect to tidy up: it decides the
        final token of BIN2DB.EXE, and modelling the ring as zero-padded
        instead reproduces that file while breaking three others.
      * ON END OF INPUT NO BYTE IS WRITTEN -- `dec LENREST` and the pointers
        advance anyway, so the ring keeps its old content at those positions.
        That is the stale content above.
      * `DeleteNode` CUTS THE CHAIN rather than unlinking one node, discarding
        the node and every older one in that bucket at once. Sound only because
        head insertion keeps each bucket ordered by position.
    """
    n = len(img)
    tbuf = bytearray(BUFSIZE + LENMAX + 1)
    rson = [RIEN] * (BUFSIZE + TABSIZE + 1)
    dad = [RIEN] * (BUFSIZE + 1)

    def bucket(r):
        return BUFSIZE + 1 + ((tbuf[r] | (tbuf[r + 1] << 8)) & TABAND)

    def insert(r):
        q = bucket(r)
        head = rson[q]
        rson[r] = head
        dad[head] = r
        rson[q] = r
        dad[r] = q

    def delete(s):
        q = dad[s]
        if q != RIEN:
            rson[q] = RIEN
            dad[s] = RIEN

    def testmatch(r):
        """MATCHLEN and MATCHPOS for the coding position, then insert it."""
        best = CMPLEN                     # `mov ax,LENMAX-1`
        node = bucket(r)
        found = None
        full = False
        mine = int.from_bytes(bytes(tbuf[r + 1:r + 1 + CMPLEN]), "big")
        while True:
            node = rson[node]
            if node == RIEN:
                break
            x = mine ^ int.from_bytes(bytes(tbuf[node + 1:node + 1 + CMPLEN]), "big")
            if x == 0:                    # repz cmpsb ran out: a complete match
                found, full = node, True
                break
            # the leading equal bytes, and then cx as the instruction leaves it
            common = (CMPLEN * 8 - x.bit_length()) // 8
            cx = CMPLEN - common - 1
            if cx < best:                 # strictly better only
                best, found = cx, node
        matchlen = LENMAX if full else CMPLEN - best
        matchpos = ((r - found) & (BUFSIZE - 1)) if found is not None else 0
        insert(r)
        return matchlen, matchpos

    pos = 0
    di = WINDOW                           # the first read lands here
    si = 0                                # and the write pointer, LENMAX ahead
    got = 0
    for i in range(LENMAX):
        if pos >= n:
            break
        tbuf[di + i] = img[pos]
        pos += 1
        got += 1
    lenrest = got
    matchlen, matchpos = testmatch(di)

    toks = []
    segsize = 0
    while True:
        if matchlen > lenrest:            # only the EMITTED length is clamped
            matchlen = lenrest
        if matchlen < 2 or (matchlen == 2 and matchpos >= 256):
            toks.append(("lit", tbuf[di], 0))
            matchlen = 1                  # `mov MatchLen,1`
        elif matchlen <= 5 and matchpos < 256:
            toks.append(("short", matchlen, matchpos))
        elif matchlen <= 9:
            toks.append(("long", matchlen, matchpos))
        else:
            toks.append(("ext", matchlen, matchpos))

        segsize += matchlen
        if segsize >= SEGLIMIT:
            toks.append(("segstep", 0, 0))
            segsize = 0                   # `mov SEGSIZE,0` -- NOT a DI reset

        for k in range(matchlen):
            if k:                         # the first byte skips it (jmp S3AA0)
                insert(di)
            delete(si)
            if pos < n:
                b = img[pos]
                pos += 1
                tbuf[si] = b
                if si < LENMAX - 1:       # the wrap-around copy at TBUF+BUFSIZE
                    tbuf[si + BUFSIZE] = b
            else:
                lenrest -= 1              # and the ring keeps its old byte
            si = (si + 1) & (BUFSIZE - 1)
            di = (di + 1) & (BUFSIZE - 1)

        matchlen, matchpos = testmatch(di)
        if lenrest <= 0:
            break
    toks.append(("eos", 0, 0))
    return toks



def compress(img):
    toks = tokenize(img)
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


def replay(toks):
    """The image a token stream produces, without going through a bitstream.

    THIS IS WHAT SEPARATES "not byte-identical" FROM "wrong". Two different
    token streams can decode to the same bytes -- a match into a uniform region
    reads the same at several distances -- so a stream that does not reproduce
    the original's is not necessarily incorrect, and saying so requires
    checking. `--selftest` reports that difference rather than flattening both
    into a failure.
    """
    out = bytearray()
    for kind, a, b in toks:
        if kind == "lit":
            out.append(a)
        elif kind in ("short", "long", "ext"):
            for _ in range(a):
                out.append(out[len(out) - b])
    return bytes(out)


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
    equivalent = 0
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
            same_bytes = replay(merged) == image
            if same_bytes:
                equivalent += 1
            note = ("%s -- %d of %d, then ours %s vs %s at offset %d (%d from the end)"
                    % ("OUTPUT-EQUIVALENT" if same_bytes else "WRONG",
                       n, len(theirs), merged[n] if n < len(merged) else None,
                       theirs[n] if n < len(theirs) else None, at, len(image) - at))
        print("%-26s %7d %7d  %s" % (pathlib.Path(path).name, len(image), len(theirs), note))
    print()
    print("%d of %d file(s) reproduce the token stream exactly" % (good, len(paths)))
    if equivalent:
        print("%d more decode to the identical image by a different route -- see BIN2DB"
              % equivalent)
        print("in the module header. Not a correctness failure; a fidelity one.")
    wrong = len(paths) - good - equivalent
    print("%d file(s) actually WRONG" % wrong)
    return 0 if wrong == 0 else 1


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

    # The packer is the LAST measurement in the chain and the one whose verdict
    # gets quoted, so it refuses a stale input rather than reporting a perfect
    # match for an .EXE that predates the source on disk.
    try:
        project.fresh(exepath)
    except Exception as exc:                                       # noqa: BLE001
        if type(exc).__name__ == 'Stale':
            raise SystemExit("STALE: %s" % exc)
        pass

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
