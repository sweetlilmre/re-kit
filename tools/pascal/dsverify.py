r"""Check the `DS:$xxxx` addresses written in comments against the declarations.

    python kit/tools/pascal/dsverify.py src/UNIT.PAS
    python kit/tools/pascal/dsverify.py src/*.PAS
    python kit/tools/pascal/dsverify.py src/*.PAS --quiet   only the disagreements

WHAT IT IS FOR. A reconstruction records where a variable lives by writing the
address in a comment beside it, and those comments become the map everybody
reads. **Nothing checks them.** The compiler never sees them, no comparison
reads them, and a byte-exact rebuild is completely silent about them -- so an
address copied forward from a previous version of the target survives every
instrument in the kit and goes on being quoted. One corpus carried 526 of these
claims with no check of any kind; six were found stale by hand, two of them
naming an address that by then belonged to a different variable.

## The check needs no base address, which is the point

An absolute check would need each unit's DGROUP base, which means linking, a map
and a layout model. This does something weaker and far more useful: it reads the
addresses as a SEQUENCE and asks whether they are consistent with each other.

    OutPtr   : Pointer = nil;   { DS:$0310 }
    ModRec   : PSampleBuffer = nil;   { DS:$0314 }

A `Pointer` is four bytes, so those two agree. When they do not --

    MixChan  : Word    = 0;     { DS:$030a }
    ChanRec  : PModRawChan = nil;   { DS:$030c }
    OutPtr   : Pointer = nil;   { DS:$0310 }

-- `ChanRec` is four bytes and `$0310 - $030c` is four, but `MixChan` is two and
`$030c - $030a` is two, so this run is internally consistent and WRONG ONLY IF an
anchor says so. That is the honest limit of the technique and it is stated here
rather than hidden: **a run of stale addresses copied together stays consistent.**
What this catches is the common case -- one comment updated, its neighbours not,
or one carried forward into a version where a declaration was inserted ahead of
it. Both leave a gap that no declaration accounts for.

## It has to model the padding, or it invents findings

**Turbo Pascal word-aligns every constant wider than a byte**, so a `Byte`
followed by a `Word` occupies three bytes and not two. The first version of this
tool did not know that and reported fifteen alignment pads as stale addresses --
in a tree whose own source comments state the rule outright, beside the very
declarations being flagged. A checker that does not model the layout does not
find errors, it manufactures them, and the manufactured ones are indistinguishable
from real ones until each is opened by hand.

So a size of one aligns to one and everything else to two, an array takes its
element's alignment, and a claimed address is checked against a cursor that pads
the same way the compiler does.

**A claimed address is trusted going forward, even when it disagrees.** After a
mismatch the cursor is reset to what the comment says rather than to what was
computed, so one wrong address reports once instead of dragging every address
after it into the report. A cascade would bury the second real error.

## Reading the output

    PLAYMOD.PAS:465   MixChan     claims $030A, declarations give $0312  <-- -8

**It never says which of the two is wrong**, because it cannot. The claim and the
declarations disagree; resolving it means finding the anchor with a READER behind
it -- an instruction that names the address -- and correcting outward from there.

Sizes it knows are what a DGROUP is mostly made of: the scalar types, any
pointer, `string[n]` and the Dos unit's string types, and `array[a..b] of
<scalar>`. Anything else -- a record, an object, an enumeration, a type declared
in another unit -- is UNVERIFIABLE and breaks the chain rather than being guessed
at. That is not caution for its own sake: an unknown name gives away neither the
size nor the ALIGNMENT, since a record starts even and a small enumeration is one
byte and starts anywhere. Assuming either reported real declarations as stale.

## What it cannot see

A `var` is not in the image at all, so no comparison in the kit can check where
one lives -- this is the ONLY check those addresses get, and it is a relative
one. Two claims that were copied forward together stay consistent with each
other and are reported as fine. Anchors are what settle those, and anchors come
from instructions.
"""

import re
import sys
import pathlib

SCALARS = {
    'byte': 1, 'shortint': 1, 'boolean': 1, 'char': 1,
    'word': 2, 'integer': 2,
    'longint': 4, 'pointer': 4, 'real': 6, 'single': 4, 'double': 8,
}

DECL = re.compile(
    r'^\s{2,}([A-Za-z_]\w*)\s*:\s*([^=;]+?)\s*(?:=\s*.*?)?;\s*(?:\{([^}]*)\})?\s*$')
ADDR = re.compile(r'DS:\$([0-9A-Fa-f]{2,4})')
ARRAY = re.compile(r'^array\s*\[\s*(.+?)\s*\.\.\s*(.+?)\s*\]\s*of\s+(\w+)$', re.I)
SECTION = re.compile(r'^\s*(const|var)\s*$', re.I)
STRING = re.compile(r'^string\s*\[\s*(\d+)\s*\]$', re.I)

# Turbo Pascal's Dos unit, whose string types read like pointer names and are not.
DOSSTR = {'pathstr': 80, 'dirstr': 68, 'namestr': 9, 'extstr': 5, 'comstr': 128}


def number(text, consts):
    """A bound, which may be a literal, a $hex, or a constant this file declares."""
    text = text.strip()
    if text.startswith('$'):
        return int(text[1:], 16)
    if re.fullmatch(r'-?\d+', text):
        return int(text)
    if text.lower() in consts:
        return consts[text.lower()]
    m = re.fullmatch(r'(\w+)\s*-\s*(\d+)', text)
    if m and m.group(1).lower() in consts:
        return consts[m.group(1).lower()] - int(m.group(2))
    return None


def align_of(size, elem=None):
    """Turbo Pascal pads to an even address for anything wider than a byte."""
    return 1 if (elem or size) == 1 else 2


def width(typename, consts):
    """(bytes, alignment), or (None, 1) for a type this tool will not guess at."""
    t = typename.strip().rstrip(';').strip()
    low = t.lower()
    if low in SCALARS:
        return SCALARS[low], align_of(SCALARS[low])
    if low in DOSSTR:
        return DOSSTR[low], 1
    m = STRING.match(t)
    if m:
        return int(m.group(1)) + 1, 1               # the length byte, then the text
    if low.startswith('p') and re.fullmatch(r'p[a-z_]\w*', low):
        return 4, 2                                 # PFoo -- a pointer by convention
    if low.startswith('^'):
        return 4, 2
    m = ARRAY.match(t)
    if m:
        lo, hi = number(m.group(1), consts), number(m.group(2), consts)
        each = SCALARS.get(m.group(3).lower())
        if lo is None or hi is None or each is None:
            return None, 1
        return (hi - lo + 1) * each, align_of(each, each)
    # A named type this tool cannot size. Its ALIGNMENT is unknown too, and that
    # is not a detail: a record starts even and a small enumeration is one byte
    # and starts anywhere, and the NAME does not say which. Guessing `2` here
    # reported two enumerations at odd addresses as stale. Unknown means unknown.
    return None, None


def consts_in(text):
    """`Name = 123;` and `Name = $ff;` -- the bounds an array may be written with."""
    out = {}
    for m in re.finditer(r'^\s+([A-Za-z_]\w*)\s*=\s*(\$?[0-9A-Fa-f]+)\s*;',
                         text, re.M):
        v = m.group(2)
        try:
            out[m.group(1).lower()] = int(v[1:], 16) if v.startswith('$') else int(v)
        except ValueError:
            pass
    return out


def scan(path):
    """Every declaration in the file, in order, with its size and claimed address."""
    text = pathlib.Path(path).read_text(encoding='utf-8', errors='replace')
    consts = consts_in(text)
    out, sections = [], []
    for n, line in enumerate(text.splitlines(), 1):
        if SECTION.match(line):
            sections.append(n)
            continue
        m = DECL.match(line.rstrip())
        if not m:
            continue
        if re.search(r'absolute', line, re.I):
            continue                    # an overlay occupies none of its own space
        name, typ, comment = m.group(1), m.group(2), m.group(3) or ''
        if typ.lower().strip() in ('record', 'object') or '(' in typ:
            continue
        a = ADDR.search(comment)
        size, alignment = width(typ, consts)
        head = line.split(';')[0]
        out.append({'line': n, 'name': name, 'size': size, 'align': alignment,
                    'init': '=' in head[head.index(':'):],
                    'section': bool(sections) and sections[-1] > (out[-1]['line']
                                                                 if out else 0),
                    'addr': int(a.group(1), 16) if a else None})
    return out


def report(path, decls, quiet=False):
    """Walk the declarations with a cursor that pads the way the compiler does."""
    name = pathlib.Path(path).name
    # TWO STREAMS, NOT ONE. Turbo Pascal puts typed constants in the initialised
    # data area and plain variables in the uninitialised one, so a unit's
    # declarations interleave in the source and do NOT interleave in DGROUP.
    # Walked as a single sequence this reported every crossing as a disagreement
    # -- six of them, all spurious, all at a `var` following a `const`.
    cursor = {True: None, False: None}
    broken = {True: False, False: False}
    bad = 0
    for d in decls:
        s = d['init']
        if d['size'] is None and d['addr'] is None:
            broken[s] = True
            continue

        if d['addr'] is not None:
            if d['align'] is None:
                # Cannot check where it starts without knowing what it aligns to.
                if not quiet:
                    print("%s:%-5d %-16s $%04X  unverifiable -- unknown type"
                          % (name, d['line'], d['name'], d['addr']))
                cursor[s], broken[s] = d['addr'], True
                continue
            if cursor[s] is not None and not broken[s]:
                at = cursor[s]
                if d['section']:
                    at += -at % 2       # each const/var section starts even
                want = at + (-at % d['align'])
                if want != d['addr']:
                    bad += 1
                    print("%s:%-5d %-16s claims $%04X, declarations give $%04X"
                          "  <-- %+d" % (name, d['line'], d['name'], d['addr'],
                                         want, d['addr'] - want))
                elif not quiet:
                    print("%s:%-5d %-16s $%04X  ok"
                          % (name, d['line'], d['name'], d['addr']))
            elif not quiet:
                print("%s:%-5d %-16s $%04X  %s" % (
                    name, d['line'], d['name'], d['addr'],
                    "chain restarts -- an unknown size preceded it" if broken[s]
                    else "first in this file"))
            # Trust the comment going forward, so one bad address reports once.
            cursor[s] = d['addr'] + (d['size'] or 0)
            broken[s] = d['size'] is None
        elif cursor[s] is not None:
            if d['section']:
                cursor[s] += -cursor[s] % 2
            cursor[s] += (-cursor[s] % d['align']) + d['size']
    return bad


def main(argv):
    quiet = "--quiet" in argv
    files = [a for a in argv if not a.startswith("--")]
    if not files:
        raise SystemExit(__doc__)
    total, claims = 0, 0
    for f in files:
        decls = scan(f)
        claims += sum(1 for d in decls if d['addr'] is not None)
        total += report(f, decls, quiet)
    print()
    print("%d address claim(s) checked, %d disagree with the declarations"
          % (claims, total))
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
