r"""Assemble one module with every installed assembler and report its segment.

    python kit/tools/pascal/asmgen.py CONFIG.toml MODULE.ASM
    python kit/tools/pascal/asmgen.py CONFIG.toml MODULE.ASM tasm tasm410
    python kit/tools/pascal/asmgen.py CONFIG.toml MODULE.ASM --against REF.OBJ
    python kit/tools/pascal/asmgen.py CONFIG.toml MODULE.ASM --include TBL.INC

THE ASSEMBLER'S HALF OF `codegen.py`. That tool drives a probe UNIT through
each installed Pascal compiler and diffs what they emit; this drives a MODULE
through each installed assembler and does the same. `build.py` already
assembles, but only as part of a whole build -- it has no way to answer "give
me the object this one file produces", which is what reconstructing a
hand-written module needs on every iteration.

**WHY IT EARNS ITS PLACE.** Reassembling a module to byte-identity is a loop:
emit source, assemble, compare, adjust. Doing that through `build.py` means
staging a whole project and wiping the build directory each time; doing it by
hand means a DOSBox config per attempt. Neither is a measurement anybody
repeats forty times. With `--against` this prints the answer directly -- how
many bytes of the reference object's segment the emitted source reproduces.

**WHAT IT MEASURED, and the facts are the assembler's rather than any
target's.** Reconstructing a 35,716-byte hand-written module against TASM 2.01:

  * `.186` is not optional and its absence does not read as a CPU problem.
    `shr r,imm` is an 80186 instruction and TASM's 8086 default rejects it as
    `Rotate count out of range`, which sounds like a bad operand.

  * A FORWARD `jmp` is sized 3 bytes on pass 1, and when pass 2 finds it
    reaches in 2 the assembler emits the short form FOLLOWED BY A NOP -- `eb
    01 90`, not `eb 01`. `jmp short` gives two bytes. A backward `jmp` has the
    opposite hazard: the distance is known, the short form is chosen, and a
    near `e9` in the original comes back two bytes shorter. So a
    reconstruction states every jump distance and lets the assembler choose
    nothing. One unstated forward jump was a whole segment's worth of drift.

  * A bracket holding only a number is read as an IMMEDIATE at any magnitude,
    not just a small one: `[20h]` warns `[Constant] assumed to mean immediate
    constant` and then refuses the instruction. `ds:[20h]` assembles.

  * A symbol name comes back UPPERCASED in the object's PUBDEF records, so a
    case-sensitive lookup that joins emitted labels to assembled addresses
    silently drops every label containing a-f.

  * LEDATA RECORD FRAMING IS NOT SOURCE-CONTROLLABLE, and it is worth knowing
    before anybody spends a day trying. Read out of TASM 2.01 itself, whose
    OMF writer decides the flush at

        mov si,[base] / sub si,cx / add si,03feh / cmp di,si / ja flush

    so the threshold is `base - cx + 1022`, with 1011 and 1014 in the sibling
    emitters for their own header overheads. It is deterministic in the bytes
    appended and the fixups pending, and in NOTHING ELSE: a pure-data module
    emitted as `db` rows of 2, 4, 8, 16, 32 or 64 bytes flushes at 996 every
    time, because the append is byte by byte, and zero-byte statements -- an
    EQU, a comment -- are inert. Fixup density does move it, and predictably:
    0 fixups gives 996, one per 8 bytes gives 976, one per 2 bytes gives 968,
    at which point the FIXUPP record has reached 1016 of its own 1024 ceiling.

    The consequence for a reconstruction: if the segment, the fixup addresses,
    their location types and their encoding all match the target and the
    framing still does not, no source-side variable remains to try. The
    difference is in the assembler binary, and a version string is not a
    build.

Assemblers come from `toolchain.<name>` in the local config, the same answers
`build.py` invokes, so this cannot disagree with the build about what is
installed. Flags come from `[assembler].flags` unless `--flags` overrides.

IT USES ITS OWN WORK DIRECTORY, not the build's staging, so it does not
collide with `build.py` or `codegen.py` the way those two collide with each
other. A module is assembled from INSIDE that directory, because an include is
resolved relative to the current directory and passing a path instead of a
name changes what resolves.
"""
import pathlib
import shutil
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[0]))
import project                                    # noqa: E402
import build                                      # noqa: E402
from substrate import omf                         # noqa: E402

WORKDIR = "asmwork"


def assemble(cfg, root, asm, module, includes=(), flags=None, timeout=300):
    """Assemble `module` with assembler `asm`. Returns (obj bytes, log, error).

    The work directory is wiped on entry, so a stale object from the previous
    attempt cannot be read as this one's result -- the failure `build.py`
    guards with `del *.TPU` and the reason it does.
    """
    exe = build.machine("toolchain." + asm)
    dosbox = build.machine("dosbox.exe")
    hdd = build.machine("dosbox.hdd")
    sep = "\\" if "\\" in exe else "/"
    bindir = exe.rsplit(sep, 1)[0]

    work = pathlib.Path(root) / WORKDIR
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    name = pathlib.Path(module).name.upper()
    shutil.copyfile(module, work / name)
    for inc in includes:
        shutil.copyfile(inc, work / pathlib.Path(inc).name.upper())

    stem = name.rsplit(".", 1)[0]
    if flags is None:
        flags = cfg.get("assembler", {}).get("flags", "/m2")
    drive = cfg.get("drive", "D")
    conf = work / "DOSBOX.CONF"
    conf.write_text("\n".join([
        "# GENERATED by kit/tools/pascal/asmgen.py -- mounts only, so no",
        "# machine path is ever committed. Do not edit it.",
        "",
        "[autoexec]",
        "mount C %s" % hdd,
        "mount %s %s" % (drive, work),
        "set PATH=%%PATH%%;%s" % bindir,
        "%s:" % drive,
        "TASM %s %s > ASM.LOG" % (flags, name),
        "echo DONE >> ASM.LOG",
    ]) + "\n", encoding="ascii")

    try:
        subprocess.run([dosbox, "-conf", str(conf), "-silent", "-exit"],
                       cwd=str(work), timeout=timeout,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return None, "", "TIMEOUT -- dosbox-x did not exit"

    log = work / "ASM.LOG"
    text = log.read_text(encoding="latin1", errors="replace") if log.exists() else ""
    if not text:
        return None, "", "no log produced -- the autoexec did not run"
    # DOS leaves errorlevel at zero for a command it cannot find, so the text
    # is the only evidence. Both spellings, for the reason build.py records.
    for line in text.splitlines():
        if "Bad command or filename" in line or "Bad command or file name" in line:
            return None, text, "DOS could not run the assembler: " + line.strip()
    if "DONE" not in text:
        return None, text, "the assembler did not finish"
    obj = work / (stem + ".OBJ")
    if not obj.exists():
        return None, text, "no OBJ produced"
    return obj.read_bytes(), text, None


USAGE = ("usage: asmgen.py CONFIG.toml MODULE.ASM [ASSEMBLER...] "
         "[--against REF.OBJ] [--include FILE]... [--flags STR]\n")


def segment_of(path):
    """The first code segment's bytes, via the substrate reader."""
    code, _ = omf.code_and_fixups(pathlib.Path(path))
    return code


def main(argv):
    rest = [a for a in project.positionals(argv, ("--against", "--flags", "--include"))
            if not a.startswith("-")]
    if len(rest) < 2:
        sys.stdout.write(USAGE)
        return 2
    cfgpath, module = rest[0], rest[1]
    asms = rest[2:] or ["tasm"]

    import tomllib
    cfg = tomllib.loads(pathlib.Path(cfgpath).read_text(encoding="utf-8"))
    root = pathlib.Path(cfgpath).resolve().parent

    against = project.option(argv, "--against")
    flags = project.option(argv, "--flags")
    # --include may repeat, which project.option cannot express
    includes = [argv[i + 1] for i, a in enumerate(argv)
                if a == "--include" and i + 1 < len(argv)]

    ref = None
    if against:
        ref = segment_of(against)
        sys.stdout.write("reference %s: segment %d byte(s)\n" % (against, len(ref)))

    stem = pathlib.Path(module).name.upper().rsplit(".", 1)[0]
    worst = 0
    for asm in asms:
        obj, log, err = assemble(cfg, root, asm, module, includes, flags)
        sys.stdout.write("\n=== %s ===\n" % asm)
        if err or obj is None:
            sys.stdout.write(log[-1500:] + "\n")
            sys.stdout.write("FAILED: %s\n" % (err or "no object returned"))
            worst = 1
            continue
        seg = segment_of(root / WORKDIR / (stem + ".OBJ"))
        sys.stdout.write("OBJ %d byte(s), segment %d byte(s)\n" % (len(obj), len(seg)))
        if ref is None:
            continue
        n = min(len(ref), len(seg))
        diff = sum(1 for i in range(n) if ref[i] != seg[i]) + abs(len(ref) - len(seg))
        if diff == 0:
            sys.stdout.write("SEGMENT IDENTICAL to %s\n" % against)
        else:
            sys.stdout.write("%d byte(s) differ from %s (%.2f%% identical)\n"
                             % (diff, against, 100.0 * (n - diff) / n if n else 0.0))
            worst = 1
    return worst


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
