#!/usr/bin/env python3
"""Read an Intel OMF .OBJ and report which bytes of its code are FIXUPS.

    from substrate import omf
    code, fixups = omf.code_and_fixups(path)
    fields = omf.fields(path)          # {offset: length}

WHY THIS EXISTS. A .TPU-shaped model of an unresolved reference is "the
byte is 00" -- true of a Turbo Pascal .TPU, where the compiler leaves a hole
for the linker. It is NOT true of an assembled module: TASM resolves what it
can and leaves an ADDEND. `DW OFFSET @@G1Table` inside the module comes out as
the offset from the module's own start, and `MOV AX,Volumes[2]` comes out as
the displacement 2 -- both correct, both waiting on a base the linker adds, and
both a flat mismatch against a binary where the linker already ran.

So for a unit that links an object module the fixup mask cannot be guessed from
the bytes; it has to be read from the object file, which records it exactly.
That is what this does, and it makes the measurement of 1a17's assembler half
stricter than the .TPU heuristic rather than looser: a byte is excused only if
the assembler said it was a relocation, not merely because it happens to be
zero.

Only the records needed for that are decoded, and unknown records are skipped
by their length field, which is what the format is designed for.

    80 THEADR    89 LNAMES    90 PUBDEF    98 SEGDEF
    A0/A1 LEDATA    A2/A3 LIDATA    9C/9D FIXUPP

LIDATA IS NOT OPTIONAL. It is repeated initialised data -- an assembler's
encoding of a `dup` -- and skipping it fails twice in silence: the bytes it
covers come back as ZERO, so an image is the right length with holes in it,
and every FIXUPP after it is placed against a stale record offset. Measured
on GoldPlay's GOLDPLAY.OBJ, where two LIDATA records cover 1784 bytes.
"""
import sys
import pathlib


def records(blob):
    """Yield (type, payload) for each OMF record. The checksum byte is dropped."""
    i = 0
    while i + 3 <= len(blob):
        rectype = blob[i]
        length = int.from_bytes(blob[i + 1:i + 3], "little")
        payload = blob[i + 3:i + 2 + length]        # the last byte is the checksum
        yield rectype, payload
        i += 3 + length
    return


def _lidata(body, j, wide):
    """Expand one LIDATA data block. Returns (bytes, next_j).

    A block is a repeat count (2 bytes, or 4 when the record is the 32-bit
    variant), then a block count. A block count of zero means a
    length-prefixed literal follows; anything else means that many nested
    blocks do. The whole content repeats `repeat` times.
    """
    n = 4 if wide else 2
    repeat = int.from_bytes(body[j:j + n], "little")
    j += n
    blocks = int.from_bytes(body[j:j + 2], "little")
    j += 2
    if blocks == 0:
        ln = body[j]
        j += 1
        chunk = bytes(body[j:j + ln])
        j += ln
    else:
        chunk = b""
        for _ in range(blocks):
            part, j = _lidata(body, j, wide)
            chunk += part
    return chunk * repeat, j


def code_and_fixups(path):
    """Return (code, fixups) for the object's first code segment.

    `code` is the concatenated LEDATA, `fixups` is a set of byte offsets inside
    it that a FIXUPP record covers. A FIXUPP's LOCAT field gives the location
    type (2 bits of the first byte plus the low nibble) and an offset relative
    to the LEDATA record it follows, which is why the two are tracked together.
    """
    blob = pathlib.Path(path).read_bytes()
    code = bytearray()
    fixups = set()
    data_start = 0                      # where the current LEDATA landed in `code`

    for rectype, p in records(blob):
        if rectype in (0xA0, 0xA1, 0xA2, 0xA3):         # LEDATA / LIDATA
            wide = rectype in (0xA1, 0xA3)
            j = 0
            j += 2 if wide else 1                       # segment index
            offset = int.from_bytes(p[j:j + 4 if wide else j + 2], "little")
            j += 4 if wide else 2
            if rectype in (0xA0, 0xA1):
                data = bytes(p[j:])
            else:                                       # LIDATA: expand the dup
                data = b""
                while j < len(p):
                    chunk, j = _lidata(p, j, wide)
                    data += chunk
            data_start = offset
            if len(code) < offset:
                code.extend(b"\x00" * (offset - len(code)))
            code[offset:offset + len(data)] = data
        elif rectype in (0x9C, 0x9D):                   # FIXUPP
            j = 0
            while j < len(p):
                b = p[j]
                if not b & 0x80:                        # THREAD, not a fixup
                    j += 2 if (b & 0x40) else 2
                    # a thread's field is 1 byte plus an index; indices are
                    # 1 byte below 0x80 and 2 above, which the loop below reads
                    idx = p[j - 1]
                    if idx & 0x80:
                        j += 1
                    continue
                locat = (b << 8) | p[j + 1]
                loc = (locat >> 10) & 7
                data_off = locat & 0x3FF
                j += 2
                fixdat = p[j]
                j += 1
                if not fixdat & 0x80:                   # frame not a thread
                    frame = (fixdat >> 4) & 7
                    if frame in (0, 1, 2):
                        j += 2 if p[j] & 0x80 else 1
                if not fixdat & 0x08:                   # target not a thread
                    j += 2 if p[j] & 0x80 else 1
                if fixdat & 0x04:                       # P bit clear -> displacement
                    pass
                else:
                    j += 4 if (rectype == 0x9D) else 2
                size = {0: 1, 1: 2, 2: 2, 3: 4, 4: 1, 5: 2, 9: 4, 11: 6, 13: 4}.get(loc, 2)
                at = data_start + data_off
                for k in range(size):
                    fixups.add(at + k)
    return bytes(code), fixups


def fields(path):
    """{offset: length} -- each FIXUPP field as one entry rather than a byte
    set.

    A caller that has to know how LONG a field is used to get that by running
    this file and parsing its verbose output with a regex. The information was
    always here; only the shape was missing.
    """
    _, marked = code_and_fixups(path)
    out, run = {}, None
    for off in sorted(marked):
        if run is not None and off == run + out[run]:
            out[run] += 1
        else:
            run, out[run := off] = off, 1
    return out


LOC_SIZE = {0: 1, 1: 2, 2: 2, 3: 4, 4: 1, 5: 2, 9: 4, 11: 6, 13: 4}
LOC_NAME = {0: "lobyte", 1: "offset", 2: "base", 3: "pointer", 4: "hibyte",
            5: "offset-loader", 9: "offset32", 11: "pointer32",
            13: "offset32-loader"}


def layout(path):
    """Everything needed to EMIT source rather than to compare an image.

        {"segments": [(name, length, attr)],
         "publics":  {offset: name},
         "extents":  [(kind, start, length)],     # kind is LEDATA or LIDATA
         "fixups":   [{at, size, loc, loc_name, rel, frame, target, disp}]}

    code_and_fixups answers "is this byte excused"; that is the right question
    for a same-shape comparison and the wrong one for reconstruction. A gap
    BETWEEN extents is uninitialised space that a `dup (?)` left, and a fixup's
    location type says whether the operand is a near offset, a segment base or
    a far pointer -- which is what decides how the line is written.
    """
    blob = pathlib.Path(path).read_bytes()
    lnames, segments, publics, extents, fixups = [], [], {}, [], []
    data_start = 0

    for rectype, p in records(blob):
        if rectype == 0x96:                                     # LNAMES
            i = 0
            while i < len(p):
                n = p[i]
                lnames.append(p[i + 1:i + 1 + n].decode("latin-1"))
                i += 1 + n
        elif rectype in (0x98, 0x99):                           # SEGDEF
            wide = rectype == 0x99
            ln = int.from_bytes(p[1:5 if wide else 3], "little")
            nm = p[5 if wide else 3] if len(p) > (5 if wide else 3) else 0
            segments.append((lnames[nm - 1] if 0 < nm <= len(lnames) else "?",
                             ln, p[0]))
        elif rectype in (0x90, 0x91):                           # PUBDEF
            i = 2
            while i < len(p) - 3:
                n = p[i]
                name = p[i + 1:i + 1 + n].decode("latin-1")
                i += 1 + n
                if i + 3 > len(p):
                    break
                publics[int.from_bytes(p[i:i + 2], "little")] = name
                i += 3
        elif rectype in (0xA0, 0xA1, 0xA2, 0xA3):               # LEDATA / LIDATA
            wide = rectype in (0xA1, 0xA3)
            j = 2 if wide else 1
            off = int.from_bytes(p[j:j + (4 if wide else 2)], "little")
            j += 4 if wide else 2
            if rectype in (0xA0, 0xA1):
                ln = len(p) - j
                kind = "LEDATA"
            else:
                ln, kind = 0, "LIDATA"
                while j < len(p):
                    chunk, j = _lidata(p, j, wide)
                    ln += len(chunk)
            data_start = off
            extents.append((kind, off, ln))
        elif rectype in (0x9C, 0x9D):                           # FIXUPP
            j = 0
            while j < len(p):
                b = p[j]
                if not b & 0x80:                                # THREAD
                    j += 1
                    j += 2 if p[j] & 0x80 else 1
                    continue
                locat = (b << 8) | p[j + 1]
                loc = (locat >> 10) & 7
                rel = "segrel" if (locat >> 14) & 1 else "selfrel"
                at = data_start + (locat & 0x3FF)
                j += 2
                fixdat = p[j]
                j += 1
                frame = target = None
                if not fixdat & 0x80:
                    frame = (fixdat >> 4) & 7
                    if frame in (0, 1, 2):
                        j += 2 if p[j] & 0x80 else 1
                if not fixdat & 0x08:
                    target = fixdat & 3
                    j += 2 if p[j] & 0x80 else 1
                disp = None
                if not fixdat & 0x04:
                    n = 4 if rectype == 0x9D else 2
                    disp = int.from_bytes(p[j:j + n], "little")
                    j += n
                fixups.append({"at": at, "size": LOC_SIZE.get(loc, 2),
                               "loc": loc, "loc_name": LOC_NAME.get(loc, "?%d" % loc),
                               "rel": rel, "frame": frame, "target": target,
                               "disp": disp})

    return {"segments": segments, "publics": publics,
            "extents": extents, "fixups": fixups}
