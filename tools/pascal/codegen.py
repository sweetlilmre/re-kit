r"""Compile one probe unit with every installed compiler and diff the code.

    python kit/tools/pascal/codegen.py CONFIG.toml PROBE.PAS
    python kit/tools/pascal/codegen.py CONFIG.toml PROBE.PAS tp6 tp7

RENAMED from `probe.py`. There were two unrelated tools under that name, one in
each consumer, and #17 decided both would be renamed rather than one -- else an
older document's mention of "probe" stays ambiguous. The other is
`substrate/fingerprint.py`, which answers what is appended to a file and what
wrote it. This one answers whether two Turbo Pascal releases emit the same code.

**WHY IT EARNS ITS PLACE.** A claimed compiler difference is cheap to assert and
expensive to chase through a reconstruction. Put the construct in a probe unit
instead, drive it through each compiler, and compare the bytes: the answer
arrives in seconds and it is a measurement rather than an argument. Five of six
such claims in one target turned out to be wrong.

The probe holds one routine per divergence worth settling. What the file
contains is the project's business; how it is driven is not, which is why the
file is an argument and the compilers come from the build config.

IT SHARES THE STAGING DIRECTORY with the build and wipes it on entry, so only
one of them can run at a time. That is inherited rather than chosen, and it is
the reason `build.py` documents the same constraint.
"""
import io
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[0]))
import project                                    # noqa: E402
import build                                      # noqa: E402


def compile_with(cfg, root, staging, compiler, probe, extra=""):
    """Compile the probe with one compiler and return its unit's bytes."""
    comp = cfg["compiler"][compiler]
    tpc = build.machine("toolchain." + compiler, comp.get("exe"))
    build.wipe(staging)
    text = io.open(probe, encoding="utf-8", errors="replace").read()
    text = build.DIALECTS[comp.get("dialect", "")](text)
    enc = cfg["stage"]["encoding"]
    name = pathlib.Path(probe).name.upper()
    (staging / name).write_text(build.dos_text(text, enc), encoding=enc,
                                errors="replace")
    log = cfg.get("log", "BUILD.LOG")
    switches = (comp.get("switches", "") + extra).strip()
    (staging / "BUILD.BAT").write_text("\r\n".join([
        "@echo off",
        "echo === codegen probe > %s" % log,
        "%s %s %s >> %s" % (tpc, switches, name, log),
        "exit",
    ]) + "\r\n", encoding="ascii")
    conf = staging / "DOSBUILD.CFG"
    build.write_conf(cfg, staging, conf, compiler)
    logname = log.split("\\")[-1]
    out, err = build.run_dosbox(root, conf, staging / logname,
                               int(cfg.get("timeout", 180)))
    unit = staging / (pathlib.Path(name).stem + ".TPU")
    if not unit.exists():
        return None, err or out
    return unit.read_bytes(), out


def code_of(blob):
    """The compiled code, located by the first routine's prologue.

    Every routine in a probe has a frame, so the code starts at the first
    `C8 nn nn 00` (ENTER) or `55 8B EC`. Rather than parse the `.TPU` format --
    which differs between releases, and parsing it would make this tool care
    about the very thing it is comparing -- take from that prologue onwards,
    which is what the comparison needs.
    """
    for i in range(len(blob) - 4):
        if blob[i] == 0xC8 and blob[i + 3] == 0x00:
            return i, blob[i:]
        if blob[i:i + 3] == b"\x55\x8b\xec":
            return i, blob[i:]
    return None, b""


def hexdump(b, base=0, limit=None):
    out = []
    b = b[:limit] if limit else b
    for i in range(0, len(b), 16):
        row = b[i:i + 16]
        out.append("%04x  %-47s  %s" % (
            base + i, " ".join("%02x" % c for c in row),
            "".join(chr(c) if 32 <= c < 127 else "." for c in row)))
    return "\n".join(out)


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("-")]
    if len(args) < 2:
        sys.stdout.write("usage: codegen.py CONFIG.toml PROBE.PAS "
                         "[COMPILER...]\n")
        return 2
    cfg = build.read_config(args[0])
    probe = pathlib.Path(args[1])
    if not probe.exists():
        sys.stdout.write("  no probe unit at %s\n" % probe)
        return 2

    root = pathlib.Path(args[0]).resolve().parent
    while not (root / "kit.toml").exists() and root != root.parent:
        root = root.parent
    staging = root / cfg.get("build", "build")
    if cfg.get("subdir"):
        staging = staging / cfg["subdir"]
    out = probe.resolve().parent / "out"

    declared = [k for k, v in cfg["compiler"].items() if isinstance(v, dict)]
    which = [a for a in args[2:] if a in declared] or declared
    codes = {}
    for c in which:
        blob, log = compile_with(cfg, root, staging, c, probe)
        if blob is None:
            sys.stdout.write("=== %s: DID NOT COMPILE\n%s\n" % (c, log))
            return 1
        out.mkdir(parents=True, exist_ok=True)
        (out / ("PROBE_%s.TPU" % c)).write_bytes(blob)
        at, code = code_of(blob)
        codes[c] = code
        sys.stdout.write("=== %-5s %s  %d bytes, code found at +%04x\n"
                         % (c, build.machine("toolchain." + c,
                                             cfg["compiler"][c].get("exe")),
                            len(blob), at or 0))

    sys.stdout.write("\n")
    ref = which[0]
    for c in which[1:]:
        a, b = codes[ref], codes[c]
        same = a == b
        sys.stdout.write("%-5s vs %-5s : %s\n"
                         % (ref, c, "IDENTICAL CODE" if same else "DIFFERS"))
        if same:
            continue
        n = min(len(a), len(b))
        first = next((i for i in range(n) if a[i] != b[i]), n)
        sys.stdout.write("  first difference at code offset +%04x "
                         "(lengths %d / %d)\n" % (first, len(a), len(b)))
        lo = max(0, first - 16)
        sys.stdout.write("  --- %s\n%s\n" % (ref, hexdump(a[lo:lo + 64], lo)))
        sys.stdout.write("  --- %s\n%s\n" % (c, hexdump(b[lo:lo + 64], lo)))

    sys.stdout.write("\ncode, %s:\n%s\n" % (ref, hexdump(codes[ref][:400])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
