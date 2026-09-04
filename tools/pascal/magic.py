r"""Raw numbers in the reconstruction that a sibling's source gives a NAME.

    python kit/tools/pascal/magic.py --ref v1.39b src/*.PAS
    python kit/tools/pascal/magic.py --ref v1.39b src/*.PAS --min 8
    python kit/tools/pascal/magic.py --ref v1.39b src/PLAYMOD.PAS --value 0x2100

WHAT IT IS FOR. A reconstruction reads a number out of an instruction and writes
it down as a number, because that is what was measured. A sibling implementation
of the same program wrote the same number as a NAME. The name is not decoration:
it says what the value MEANS, and it says how many other places must change if it
ever changes. `MaxChannels` and `16` compile identically and read completely
differently -- and on this corpus a literal `8` left in three places where the
constant said 16 displaced fourteen units that had no defect of their own.

So this pairs every literal in the target against every named constant in the
reference, and reports where the two agree.

## `--unique` is the setting that makes it usable

Without it the report is mostly noise, and the noise has a shape: a small number
is named by many things. On one corpus 553 matches came back, of which the top
twenty values each carried between two and a dozen candidate names -- `8` was
`DevBits` and eleven others. A match that offers a dozen names offers none.

`--unique` keeps only the values that exactly ONE constant in the reference
claims. That inverts the ratio: what survives is the odd number, the one the
author bothered to name because it could not be guessed -- a port offset, a
timeout, a magic word, a table size.

Run `--unique` first. Fall back to the full list only for a specific value, with
`--value`, once you have a reason to care about it.

## It proposes; it never decides

**A match is a coincidence until a person reads it.** Small numbers collide with
everything: 1 is a true value, an array base, a first tick and a channel count.
That is why `--min` defaults to 8 and why the output shows the line -- the point
is to put a candidate in front of a reader, not to rename anything.

Three kinds of false match are worth expecting:

  * **the same number, a different meaning.** `$40` is a volume ceiling, a sample
    flag and a pattern's row count in one program.
  * **a number the reference names but this version changed.** A count is data,
    and data measures one version only -- the release's `MaxOutputFreq` is 45000
    where this target holds 44000. A name that does not match the value is worse
    than no name.
  * **a literal inside hand-written assembler**, where the original author was
    writing bytes rather than expressions and a name may never have existed.

## What it reads, and what it deliberately ignores

Comments are stripped before the search, along with string literals and character
codes. **An address in a comment is not a magic number**, and a tree that
documents every variable's address in prose has hundreds of them; leaving them in
buries the real matches under commentary. Directives -- `{$I-}`, `{$R-}` -- go
with the comments.

The reference side takes both plain constants (`MaxChannels = 16;`) and typed
ones (`TimerHz : Word = 16000;`), because the second kind carries just as much
meaning and a sibling release is full of them.
"""

import io
import re
import sys
import pathlib
import collections

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from source import strip                                          # noqa: E402

# `Name = 123;` and `Name : Type = $ff;` -- both are names for a value.
CONST = re.compile(
    r'^\s{0,8}([A-Za-z_]\w*)\s*(?::\s*\w+\s*)?=\s*(\$[0-9A-Fa-f]+|-?\d+)\s*;',
    re.M)
NUMBER = re.compile(r'(?<![\w$.])(\$[0-9A-Fa-f]+|\d+)(?![\w.])')
EQU = re.compile(r'^\s*([A-Za-z_]\w*)\s+EQU\s+(\$?[0-9A-Fa-f]+|-?\d+)\s*$',
                 re.M | re.I)
DECLARED = re.compile(r'[A-Za-z_]\w*\s*(?::\s*\w+\s*)?=\s*(?:\$[0-9A-Fa-f]+|-?\d+)\s*;')


def value(tok):
    return int(tok[1:], 16) if tok.startswith('$') else int(tok)


def named(paths):
    """{value: {name, ...}} for every constant the reference source declares."""
    out = collections.defaultdict(set)
    for p in paths:
        text = strip(pathlib.Path(p).read_text(encoding='utf-8', errors='replace'),
                     asm=str(p).upper().endswith('.ASM'))
        for name, tok in CONST.findall(text) + EQU.findall(text):
            try:
                out[value(tok)].add(name)
            except ValueError:
                pass
    return out


def literals(path, floor):
    """(line, value, text) for each bare number in the target's code."""
    raw = io.open(path, encoding='utf-8', errors='replace', newline='').read()
    code = strip(raw, asm=str(path).upper().endswith('.ASM'))
    lines = raw.split('\n')
    for n, line in enumerate(code.split('\n'), 1):
        # A DECLARATION IS THE NAME. Skip the whole line, and skip it wherever the
        # declaration sits -- Pascal allows several on one line, and anchoring at
        # the line start reported a target's OWN constants as unnamed literals.
        if DECLARED.search(line) or EQU.match(line):
            continue
        for tok in NUMBER.findall(line):
            v = value(tok)
            if v >= floor:
                yield n, v, lines[n - 1].strip()


def main(argv):
    ref = None
    floor, only = 8, None
    unique = "--unique" in argv
    for i, a in enumerate(argv):
        if a == "--ref" and i + 1 < len(argv):
            ref = argv[i + 1]
        if a == "--min" and i + 1 < len(argv):
            floor = int(argv[i + 1], 0)
        if a == "--value" and i + 1 < len(argv):
            only = int(argv[i + 1], 0)
    files = [a for i, a in enumerate(argv)
             if not a.startswith("--") and (i == 0 or argv[i - 1] not in
                                            ("--ref", "--min", "--value"))]
    if not ref or not files:
        raise SystemExit(__doc__)

    refs = sorted(pathlib.Path(ref).rglob("*.PAS")) + \
        sorted(pathlib.Path(ref).rglob("*.pas"))
    names = named(refs)
    print("%d named constant value(s) in %d reference file(s)"
          % (len(names), len(refs)))
    print()

    hits = 0
    for f in files:
        for line, v, text in literals(f, floor):
            if only is not None and v != only:
                continue
            if v not in names:
                continue
            if unique and len(names[v]) != 1:
                continue
            hits += 1
            print("%s:%-5d %-8s %s" % (pathlib.Path(f).name, line,
                                       "$%X" % v if v > 255 else str(v),
                                       ", ".join(sorted(names[v]))))
            print("      %s" % text[:78])
    print()
    print("%d literal(s) the reference names" % hits)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
