"""Report where the assembler-transcription rule is not yet met.

The rule (docs/continuation.md, and project memory as transcribe-asm-verbatim)
is that hand-written assembler goes in verbatim and carries three things:

  1. the assembler itself;
  2. a comment on EVERY line saying what that instruction does;
  3. a block comment above holding the equivalent Pascal, labelled as
     reference only.

This checks 2 and 3 mechanically. It cannot check 1 -- that needs the binary --
so a unit passing this is not the same as a unit that has been audited.

Reporting only: it never fails a build. Parts 001, 002 and 004-007 have not
been swept yet and are expected to show up here.

    python kit/tools/pascal/asmaudit.py            every unit
    python kit/tools/pascal/asmaudit.py PART3      only names containing PART3
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import project                                    # noqa: E402
LOOKBACK = 50          # lines above `asm` to search for the equivalent-Pascal block


def audit(path):
    lines = path.read_text(encoding="ascii", errors="replace").split("\n")
    in_asm = False
    in_comment = False
    uncommented = []
    missing_equiv = []
    blocks = 0
    owner = None

    for n, line in enumerate(lines, 1):
        s = line.strip()

        if re.match(r"^(procedure|function)\s", s):
            owner = s.rstrip(";")

        if s == "asm":
            in_asm = True
            blocks += 1
            above = "\n".join(lines[max(0, n - 1 - LOOKBACK):n - 1])
            if "EQUIVALENT PASCAL" not in above:
                missing_equiv.append((n, owner))
            continue

        if not in_asm:
            continue

        # A comment may SPAN LINES inside an asm body, and its continuation
        # lines carry no brace of their own. Counting braces rather than
        # looking for one on the line is the difference between reading a
        # block header and accusing it: this check reported ten lines of
        # prose in one routine as uncommented instructions, which pushes an
        # author towards worse comments to satisfy the gate.
        if in_comment:
            if "}" in s:
                in_comment = False
            continue

        if s == "end;":
            in_asm = False
            in_comment = False
            continue
        if not s or s.startswith("{"):
            if s.count("{") > s.count("}"):
                in_comment = True
            continue
        if "{" not in line:
            uncommented.append((n, s))
        elif line.count("{") > line.count("}"):
            in_comment = True

    return blocks, uncommented, missing_equiv


def main():
    want = sys.argv[1].upper() if len(sys.argv) > 1 else ""
    clean, dirty = [], []
    # The source directory is the project's answer, not this file's constant.
    try:
        src = project.path("layout.src")
    except project.Missing as exc:
        return project.complain(exc)

    # rglob, so a source moved into a subdirectory is still audited. See the
    # note in paslint.py: a shrinking scope reports clean.
    for path in sorted(src.rglob("*.PAS")):
        if want and want not in path.name.upper():
            continue
        blocks, uncommented, missing = audit(path)
        if not blocks:
            continue
        if uncommented or missing:
            dirty.append((path, blocks, uncommented, missing))
        else:
            clean.append((path, blocks))

    for path, blocks, uncommented, missing in dirty:
        print("%s  (%d asm block%s)" % (path.name, blocks, "" if blocks == 1 else "s"))
        for n, owner in missing:
            print("    line %-5d no equivalent-Pascal block   %s" % (n, owner or "?"))
        for n, text in uncommented:
            print("    line %-5d uncommented   %s" % (n, text))
        print("")

    for path, blocks in clean:
        print("%-22s clean  (%d asm block%s)"
              % (path.name, blocks, "" if blocks == 1 else "s"))

    print("\n%d unit(s) meet the rule, %d do not." % (len(clean), len(dirty)))


if __name__ == "__main__":
    main()
