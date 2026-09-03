"""Classify every remaining span WITHOUT needing to align our image.

Every earlier attempt at this question asked "what do the two images do
differently here", which needs an anchor, and an anchor is exactly what is
missing at the interesting sites. This asks a question about the ORIGINAL
alone: does the span fall inside a 9A far-call instruction? Decoding the
original's segment linearly from its first routine gives instruction
boundaries with no alignment at all, so nothing here can be misled by a weak
or ambiguous match.

A span inside a far call's operand is the harness floor -- our runtime sits at
a different paragraph because our main program is a different size -- and
nothing in the source reaches it.
"""
import sys, tomllib, re, subprocess, collections
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import project                                     # noqa: E402
from substrate import align                        # noqa: E402
import capstone                                    # noqa: E402

SPAN = re.compile(r"([0-9a-f]{4}):([0-9a-f]{4})\.\.([0-9a-f]{4})\s+(\d+) byte")
CFG = sys.argv[1] if len(sys.argv) > 1 else "spans.toml"
cfg = tomllib.load(open(CFG, "rb"))
root = project.find(); first = project.get("target.first_para", quiet=True)
rel = project.get("target.release", quiet=True)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_16)
tot = collections.Counter()

for part in sys.argv[2:] or list(cfg["part"]):
    spec = cfg["part"][part]
    orig, _ = align.load_image((root / rel[part]).read_bytes())
    segs = project.seg_addrs(spec)
    got = subprocess.run([sys.executable, str(pathlib.Path(__file__).resolve().parent / "spans.py"),
                          CFG, part, "--min=1"],
                         capture_output=True, text=True, encoding="utf-8")
    per = collections.Counter(); other = []
    for s, lo_s, hi_s, n_s in SPAN.findall(got.stdout):
        seg, lo, n = int(s, 16), int(lo_s, 16), int(n_s)
        if seg not in segs:
            per["outside the segment list"] += n; continue
        i = segs.index(seg)
        b = (seg - first) * 16
        size = ((segs[i+1] if i+1 < len(segs) else spec["end_at"]) - seg) * 16
        data = orig[b:b + size]
        # decode linearly and find the instruction containing `lo`
        # DECODE-FREE: is there a 9A close enough behind that this span falls
        # inside its five bytes? A linear decode from the segment base drifts
        # through data and padding -- it reported `rcr [bp+si+0x31a7],0x8a`,
        # and 0x31a7 is a runtime ADDRESS, so the "instruction" was three bytes
        # into a far call's operand. This asks only about bytes.
        far = any(lo - k >= 0 and data[lo - k] == 0x9A and lo < lo - k + 5
                  for k in range(0, 5))
        if far:
            per["far-call operand"] += n
        else:
            # A HINT, NOT A FACT, and it is labelled so. This decodes from 24
            # bytes back, which is not an instruction boundary, so it can drift
            # and name an instruction that is not there. It reported
            # `mov word ptr [0x65a9], 0x40` at 108b:1ec8 on one target; Ghidra
            # put that instruction at 1ec6 and our copy at 1eca, so the span was
            # the tail of a four-byte code-size difference and not a store at
            # all. Confirm any reading here against a disassembler that knows
            # where the function starts.
            hit = None
            for ins in md.disasm(data[max(0, lo - 24):lo + 8], max(0, lo - 24)):
                if ins.address <= lo < ins.address + ins.size:
                    hit = ins
            per["OTHER"] += n
            other.append("%04x:%04x %d  ~%s" % (seg, lo, n,
                         ("%s %s" % (hit.mnemonic, hit.op_str)) if hit else "(no decode)"))
    print("part %s" % part)
    for k, v in per.most_common():
        print("   %-24s %3d byte(s)" % (k, v))
        tot[k] += v
    if other:
        print("       (a leading ~ is a decode from a GUESSED boundary: a hint,"
              " not a fact)")
    for o in other:
        print("       %s" % o)
print("\nALL PARTS")
for k, v in tot.most_common():
    print("   %-24s %3d byte(s)" % (k, v))
