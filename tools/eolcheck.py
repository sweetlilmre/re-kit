"""Every file a DOS tool reads must be CRLF. Nothing was checking.

    eolcheck.py [DIR...]

The rule is not new and it is not mine: a reconstruction measured by byte
comparison against 1990s executables cannot let anything rewrite a byte of the
files those tools read. The first target's .gitattributes states it plainly --
"DOS FILES ARE CRLF, BYTE FOR BYTE. Anything a 1990s DOS tool reads or IS --
.PAS, .ASM, .INC, .BAT, .CFG, and the binaries" -- and marks each of those
extensions `-text` so git stores whatever is on disk.

WHICH IS EXACTLY WHY IT NEEDED A CHECK. `-text` means git will not normalise
them, so a file written with Unix endings STAYS wrong, silently, and nothing
downstream complains until a DOS tool chokes on it. A batch file added to that
target was written with bare LF and DOSBox's shell mis-parsed a line, reporting
a program as missing when it was sitting in the same directory. The rule was
documented, the extension was listed, and the violation still shipped -- so
prose in .gitattributes is not enforcement.

WHICH EXTENSIONS, THOUGH -- AND THE ANSWER IS NARROWER THAN THE RULE. The first
version of this checked .BAT, .CFG, .ASM and .INC and found eight files: every
hand-written .ASM and three generated .INC, all bare LF, all of which have been
compiling and assembling for the whole project. That target's Pascal sources are
LF on disk too, deliberately -- they were authored that way, Turbo Pascal reads
them regardless, and its own CLAUDE.md says not to convert them in bulk for no
measured gain.

So TPC and TASM tolerate LF and DOSBox's SHELL does not, and the default here is
.BAT alone: the one consumer measured to care. Pass extensions to widen it. A
check that flags eight working files to catch one broken one trains its reader
to ignore it.
"""
import sys
import pathlib

DEFAULT_EXT = (".BAT",)
SKIP_DIRS = {".git", "build", "run", "work", "__pycache__", ".venv"}


def offenders(roots, exts):
    for root in roots:
        for p in sorted(pathlib.Path(root).rglob("*")):
            if not p.is_file() or p.suffix.upper() not in exts:
                continue
            if any(part in SKIP_DIRS for part in p.parts):
                continue
            data = p.read_bytes()
            bare = data.count(b"\n") - data.count(b"\r\n")
            if bare:
                yield p, bare, data.count(b"\r\n")


def main(argv):
    exts = tuple(a.upper() if a.startswith(".") else "." + a.upper()
                 for a in argv if a.startswith(".")) or DEFAULT_EXT
    roots = [a for a in argv if not a.startswith(".")] or ["."]
    bad = 0
    for p, bare, crlf in offenders(roots, exts):
        print("  %-44s %d bare LF, %d CRLF" % (p.as_posix(), bare, crlf))
        bad += 1
    print("%d file(s) a DOS tool reads carry Unix line endings%s"
          % (bad, "" if bad else " -- checked " + ", ".join(exts)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
