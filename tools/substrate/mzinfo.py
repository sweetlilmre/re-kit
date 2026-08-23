"""Parse a DOS MZ header, and say whether the file is bigger than its image.

Reports the load-image extent against the physical file size, which is how an
appended non-EXE payload shows up -- a music module, overlay data, or debug
information. See the wiki observation `The file is bigger than its load image`
for what each cause looks like.

Nothing here knows anything about any particular target: a filename in, a
header out.
"""
import struct
import sys
from pathlib import Path

FIELDS = "sig lastpage pages nreloc hdrpara minalloc maxalloc ss sp csum ip cs reloff ovno"


def parse(path: Path):
    raw = path.read_bytes()
    v = struct.unpack_from("<2sHHHHHHHHHHHHH", raw, 0)
    h = dict(zip(FIELDS.split(), v))
    h["file"] = path.name
    h["filesize"] = len(raw)
    h["hdrsize"] = h["hdrpara"] * 16
    h["imagesize"] = (h["pages"] - 1) * 512 + (h["lastpage"] or 512)
    h["overlay_bytes"] = len(raw) - h["imagesize"]
    h["entry"] = h["cs"] * 16 + h["ip"]  # relative to load segment
    h["lzexe"] = raw[0x1C:0x20] in (b"LZ91", b"LZ90")
    h["raw"] = raw
    return h


def main(paths):
    hdr = f"{'file':<14}{'filesize':>9}{'image':>9}{'overlay':>9}{'hdr':>6}{'reloc':>7}{'cs:ip':>12}{'ss:sp':>12}{'minalloc':>9}  pack"
    print(hdr)
    print("-" * len(hdr))
    for p in paths:
        h = parse(Path(p))
        print(
            f"{h['file']:<14}{h['filesize']:>9}{h['imagesize']:>9}{h['overlay_bytes']:>9}"
            f"{h['hdrsize']:>6}{h['nreloc']:>7}"
            f"{h['cs']:>7X}:{h['ip']:04X}{h['ss']:>7X}:{h['sp']:04X}"
            f"{h['minalloc']*16:>9}  {'LZEXE' if h['lzexe'] else '-'}"
        )


if __name__ == "__main__":
    main(sys.argv[1:])
