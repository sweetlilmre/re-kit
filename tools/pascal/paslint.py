"""Catch the Pascal defects that cost the most time to diagnose from a compiler
error, because the compiler reports them somewhere other than where they are.

  nested braces   TP7 does NOT nest { } comments -- the first } closes it, so a
                  {?} or { blank } written INSIDE a block comment silently ends
                  it and the rest of the comment is parsed as code. The error
                  then appears dozens of lines later and looks unrelated.

  stray close     more } than {, usually a } used decoratively inside a comment.

  reserved words  identifiers that collide with something TP7 already means.
                  OFFSET is an assembler operator, so a parameter called Offset
                  produces "Syntax error" inside an asm block; Text is a
                  built-in type.

  DSeg addresses  Mem[DSeg:$XXXX] or Ptr(DSeg, $XXXX) reaching into our OWN
                  data segment at an address copied out of the original. This
                  one compiles, runs, and silently does nothing useful: the
                  address is where the data sits in the ORIGINAL's DGROUP, and
                  Turbo Pascal decides where ours goes. It cost a whole scene
                  -- part 003 scene 2 loaded its waypoint table to $B250, the
                  array it should have filled stayed zero, and the star tube
                  neither moved nor ran to length. Name the variable instead.
                  Mem[$A000:...] and Mem[VirtScrSeg:...] are fine; those are
                  addresses we do not own and cannot name.

Run it before reaching for the compiler:

    python tools/paslint.py
"""
import re
import sys
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import project                                    # noqa: E402

# Identifiers that are fine in Pascal generally but bite in specific contexts.
RESERVED = {
    "offset": "OFFSET is an operator in TP7's inline assembler",
    "text":   "Text is a built-in file type",
    "seg":    "Seg is a built-in function",
    "ofs":    "Ofs is a built-in function",
    "ptr":    "Ptr is a built-in function",
    "addr":   "Addr is a built-in function",
    "mem":    "Mem is a built-in array",
    "port":   "Port is a built-in array",
}

DECL = re.compile(r"(?im)^\s*(?:procedure|function)\s+\w+\s*\(([^)]*)\)")

# Mem[DSeg : $B250]  /  MemW[DSeg:X]  /  Ptr(DSeg, $B250)
DSEG = re.compile(r"(?i)\b(Mem[WL]?\s*\[\s*DSeg\s*:|Ptr\s*\(\s*DSeg\s*,)")


def strip_comments(src):
    """Blank out { } and (* *) comments, keeping line numbering intact."""
    out = list(src)
    i, n = 0, len(src)
    while i < n:
        if src[i] == "{":
            j = src.find("}", i)
            j = n if j < 0 else j + 1
        elif src.startswith("(*", i):
            j = src.find("*)", i)
            j = n if j < 0 else j + 2
        else:
            i += 1
            continue
        for k in range(i, j):
            if out[k] != "\n":
                out[k] = " "
        i = j
    return "".join(out)


def check(path):
    # read as BYTES first: a non-ASCII byte is itself a defect here, and
    # decoding with errors="replace" would hide it behind U+FFFD
    raw = path.read_bytes()
    problems = []

    # ---- non-ASCII bytes. A DOS file is read by a 1990s tool, so an em dash
    # or a curly quote pasted in from prose becomes two or three bytes that
    # Turbo Pascal sees as garbage -- inside a comment it may even close it.
    # Every .PAS/.ASM/.INC in both repos is pure ASCII today; keep it that way.
    for n, bline in enumerate(raw.split(b"\n"), 1):
        hi = [b for b in bline if b > 127]
        if hi:
            problems.append((n, "non-ASCII byte%s %s -- DOS sources are ASCII "
                                "only; write '--' not an em dash, \"\" not curly "
                                "quotes" % ("s" if len(hi) > 1 else "",
                                            " ".join(hex(b) for b in hi[:6]))))

    src = raw.decode("ascii", errors="replace")

    # ---- comment nesting
    #
    # A BRACE INSIDE A STRING LITERAL IS NOT A COMMENT, and this check used to
    # think it was. The first source in either project to write one -- a DOS
    # tool that GENERATES Pascal, so its strings are full of `{` and `}` --
    # produced two confident false positives, and the tempting fix was to
    # reshape the source until the linter went quiet. That is the wrong way
    # round: a checker that cannot read the language it checks has to learn,
    # because the alternative is source written to suit tooling.
    #
    # Turbo Pascal's rule is small enough to implement exactly: `{ }` and
    # `(* *)` are comments, `'...'` is a string with `''` as an embedded quote,
    # and each construct is inert inside the others.
    depth, line = 0, 1
    in_str = False
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if ch == "\n":
            line += 1
            # An unterminated string cannot span a line in TP7, so a newline
            # ends one. Saying so here keeps one bad quote from swallowing the
            # rest of the file and reporting nothing at all.
            in_str = False
        elif in_str:
            if ch == "'":
                in_str = False
        elif depth:
            if ch == "}":
                depth = 0
            elif ch == "{":
                # The check this whole scanner exists for, and it has caught a
                # real defect twice: TP7 does not nest, so the comment ended at
                # the FIRST close and everything after it is code.
                problems.append((line, "nested '{' inside a { } comment -- "
                                       "TP7 does not nest, the comment ended early"))
        elif ch == "'":
            in_str = True
        elif ch == "{":
            depth = 1
        elif ch == "}":
            problems.append((line, "stray '}' -- more closes than opens"))
        elif ch == "(" and src[i + 1:i + 2] == "*":
            # (* *) is the other comment form. Skipped rather than nested-
            # checked: TP7 does not nest these either, but nothing in either
            # project uses them and a check nobody exercises is a check nobody
            # trusts.
            j = src.find("*)", i + 2)
            if j < 0:
                problems.append((line, "unterminated (* *) comment"))
                break
            line += src.count("\n", i, j)
            i = j + 1
        i += 1
    if depth:
        problems.append((line, "unterminated { } comment at end of file"))

    # ---- parameter names that collide
    for m in DECL.finditer(src):
        ln = src[:m.start()].count("\n") + 1
        for part in m.group(1).split(";"):
            names = part.split(":")[0]
            for ident in re.findall(r"[A-Za-z_]\w*", names):
                why = RESERVED.get(ident.lower())
                if why:
                    problems.append((ln, "parameter '%s': %s" % (ident, why)))

    # ---- hard-coded addresses in our own data segment
    code = strip_comments(src)
    for m in DSEG.finditer(code):
        ln = code[:m.start()].count("\n") + 1
        problems.append((ln, "%s... addresses our own DGROUP at an offset "
                             "taken from the original -- Turbo Pascal decides "
                             "that layout, so this writes to the wrong place. "
                             "Name the variable and use it."
                         % m.group(1).replace(" ", "")))

    return problems


def main(argv):
    # The source directory is the project's answer. It was `ROOT / "src"`, a
    # constant, and that had already gone wrong in the second consumer: its
    # sources are under v1.31b/src, so running this reported "0 problem(s) in 0
    # file(s)" and passed. A check that cannot fail is worse than none.
    try:
        src = project.path("layout.src")
    except project.Missing as exc:
        return project.complain(exc)
    # RECURSIVE. A non-recursive glob here checked 63 files, then a project
    # moved 23 test harnesses into src/test/ and it checked 40 -- reporting
    # "0 problems" both times. A check whose SCOPE can shrink without saying
    # so is worse than no check, because the clean report is what gets read.
    files = [src / a for a in argv] if argv else sorted(src.rglob("*.PAS"))
    total = 0
    for f in files:
        probs = check(f)
        if probs:
            print("\n=== %s ===" % f.name)
            for ln, msg in probs:
                print("  line %4d  %s" % (ln, msg))
            total += len(probs)
    print("\n%d problem(s) in %d file(s)" % (total, len(files)))
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
