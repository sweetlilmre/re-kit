r"""Check the `DS:$xxxx` addresses written in comments against the declarations.

    python kit/tools/pascal/dsverify.py src/UNIT.PAS
    python kit/tools/pascal/dsverify.py src/*.PAS
    python kit/tools/pascal/dsverify.py src/*.PAS --quiet   only the disagreements
    python kit/tools/pascal/dsverify.py src/*.PAS --map build/VTMAIN.MAP
    python kit/tools/pascal/dsverify.py src/*.PAS --map build/VTMAIN.MAP --fix
    python kit/tools/pascal/dsverify.py src/*.PAS --map MAP --fix --chain
    python kit/tools/pascal/dsverify.py src/*.PAS --map MAP --prose [--fix]

**PREFER `--map` WHENEVER A LINK EXISTS.** It settles absolutely what the rest of
this tool can only settle relatively: the linker's own map lists every public
symbol with its DGROUP offset, so each comment is checked against the address the
linker actually assigned rather than against its neighbours. Anything the map
names needs no reasoning at all -- and on a byte-exact reconstruction the map's
address IS the original's address.

Its reach is the catch: only INTERFACE declarations are public in a Turbo Pascal
unit, so implementation-section variables never appear and fall back to the
relative check. Run both; they answer for different declarations.

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

## `--fix`, and what it deliberately will not touch

With a map, a disagreeing comment has a known right answer, so `--fix` rewrites
the `DS:$xxxx` token in place. It changes comments and nothing else, and the
rebuild afterwards is what proves that.

It refuses two kinds of claim rather than guessing:

  * **a name declared with an address in more than one file.** The linker
    publishes one symbol per name; two units declaring `CtrlBlock` -- one the
    variable, one an import of it -- cannot be told apart from the map alone, and
    rewriting the wrong one would replace a stale address with a confident lie.
  * **anything the linker does not name**, which is every implementation-section
    declaration. Those keep the relative check and nothing more.

**It cannot fix prose.** An address written into a sentence -- "$0998 + 80 is what
puts it at $09e8" -- is invisible to this and stays behind, so a fixed
declaration can end up next to a paragraph that still argues from the old number.
The tool reports how many such mentions remain; reconciling them is by hand.

## `--prose`, for the addresses a declaration fixer cannot reach

Correcting a declaration's comment leaves every SENTENCE that cites the old
number untouched, and those sentences are the worse half of the problem: prose
that argues from an address reads as corroboration for it. After 224 declarations
were corrected on one corpus, **416 prose lines still quoted an address that had
moved.**

`--prose` pairs a variable's name with the address written beside it:

    `UsingGUS` ($0bce), `TicksPerSecond` ($0bcc) and `DriverTicks` ($0bd0)

Each name is matched to the nearest address that FOLLOWS it, and only when the
two are close together. Distance is the whole safeguard. A line may name a
variable and then discuss a different address entirely --

    `Busy` is at $001A, so the five bytes between them start at $001B.

-- where $001A belongs to `Busy` and $001B belongs to nothing. A rule that paired
every address with the nearest preceding name would rewrite the second one.

**It reports; it does not decide.** Roughly half the mentions on that corpus name
no variable at all -- a bare address in a sentence, an address table, an offset
inside a routine -- and no rule can attribute those. They are listed as needing a
person, and they stay that way.

## What the two modes are each blind to

The relative check cannot see a run of addresses that drifted TOGETHER. The map
check cannot see anything the linker did not publish. Neither subsumes the other,
and a claim both are silent about is unverified -- which is the honest reading,
not a pass.

## What it cannot see

A `var` is not in the image at all, so no comparison in the kit can check where
one lives -- this is the ONLY check those addresses get, and it is a relative
one. Two claims that were copied forward together stay consistent with each
other and are reported as fine. Anchors are what settle those, and anchors come
from instructions.
"""

import io
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


def map_publics(path):
    """{NAME: dgroup offset} for every public the linker put in DGROUP.

    The map names DGROUP by its paragraph in the segment table -- the row whose
    class is DATA -- and then lists publics as `PARA:OFFSET NAME`. Only the rows
    in that paragraph are data; the rest are code, and a code offset compared
    against a data address would be nonsense that looks like a finding.
    """
    text = pathlib.Path(path).read_text(encoding='ascii', errors='replace')
    m = re.search(r'^\s*([0-9A-F]+)H\s+[0-9A-F]+H\s+[0-9A-F]+H\s+\S+\s+DATA\s*$',
                  text, re.M)
    if not m:
        raise SystemExit("%s names no DATA segment -- build with the map switch" % path)
    para = int(m.group(1), 16) // 16

    # **A NAME CAN APPEAR TWICE.** Turbo Pascal publishes unqualified names, so two
    # units may each export a `FilterIsOn` and the map lists both, at different
    # addresses. Keeping the first silently -- which is what setdefault does --
    # made this tool report twelve confident "the LINKER says" lines for the wrong
    # variable. A duplicated name carries no answer and is dropped.
    seen = {}
    for seg, off, name in re.findall(
            r'^\s*([0-9A-F]{4}):([0-9A-F]{4})\s+(\w+)\s*$', text, re.M):
        if int(seg, 16) == para:
            seen.setdefault(name.upper(), set()).add(int(off, 16))
    return {n: a.pop() for n, a in seen.items() if len(a) == 1}


def map_length(path):
    """How long DGROUP is, so a larger number can be ruled out as an address."""
    text = pathlib.Path(path).read_text(encoding='ascii', errors='replace')
    m = re.search(r'^\s*[0-9A-F]+H\s+[0-9A-F]+H\s+([0-9A-F]+)H\s+\S+\s+DATA\s*$',
                  text, re.M)
    return int(m.group(1), 16) if m else None


def against_map(path, decls, publics, quiet=False, skip=()):
    """Check each claim against the address the linker assigned. Absolute."""
    name = pathlib.Path(path).name
    bad = checked = 0
    for d in decls:
        if d['addr'] is None:
            continue
        if d['name'].upper() in skip:
            # Declared with an address in more than one file. The map holds one
            # symbol of that name and it may be the OTHER one -- a unit's private
            # pointer to a structure another unit publishes reads exactly like a
            # stale address here, and is not one.
            if not quiet:
                print("%s:%-5d %-16s $%04X  ambiguous -- the name is declared twice"
                      % (name, d['line'], d['name'], d['addr']))
            continue
        real = publics.get(d['name'].upper())
        if real is None:
            continue
        checked += 1
        if real != d['addr']:
            bad += 1
            print("%s:%-5d %-16s claims $%04X, the LINKER says $%04X  <-- %+d"
                  % (name, d['line'], d['name'], d['addr'], real, d['addr'] - real))
        elif not quiet:
            print("%s:%-5d %-16s $%04X  confirmed by the map"
                  % (name, d['line'], d['name'], d['addr']))
    return bad, checked


def ambiguous(files):
    """Names declared WITH an address in more than one file -- unsafe to rewrite."""
    seen = {}
    for f in files:
        for d in scan(f):
            if d['addr'] is not None:
                seen.setdefault(d['name'].upper(), set()).add(f)
    return {n for n, fs in seen.items() if len(fs) > 1}


def fix(path, publics, skip, chain=False):
    """Rewrite the DS addresses. Comments only.

    Two sources, and the second is not a weaker version of the first. The linker
    names only what a unit exports, and it cannot name a symbol two units both
    export -- a duplicated name is dropped, because it carries no answer. The
    relative chain has the opposite reach: it knows nothing absolutely, but once
    its NEIGHBOURS are anchored it computes the one address that fits between
    them, duplicated name or not. On this corpus the map settled 207 claims and
    left `DMAStop` -- published twice, at two addresses -- and the chain then put
    each of the two where its neighbours require. Run the map pass first; the
    chain pass is only as good as the anchors around it.
    """
    # newline='' THROUGHOUT. A CRLF source tree read through Python's default
    # newline translation and written back comes out LF, which rewrites every
    # line in the file -- eleven real changes buried in a diff of fourteen
    # thousand, and a reviewer with no way to see them.
    p = pathlib.Path(path)
    with io.open(p, encoding='utf-8', errors='replace', newline='') as fh:
        lines = fh.read().split('\n')
    changed = 0
    decls = scan(path)
    wanted = {}
    if chain:
        report(path, decls, quiet=True, fixes=wanted)
    for d in decls:
        if d['addr'] is None:
            continue
        # SKIP GUARDS THE MAP LOOKUP ONLY. An ambiguous name has no answer in the
        # map and must never take one from it -- but the chain computes from its
        # NEIGHBOURS, which do not care that the name is duplicated. Letting
        # --chain waive the guard altogether rewrote a private pointer with the
        # address of the published structure it points AT.
        real = None
        if d['name'].upper() not in skip:
            real = publics.get(d['name'].upper())
        if real is None:
            real = wanted.get(d['line'])
        if real is None or real == d['addr']:
            continue
        i = d['line'] - 1
        m = ADDR.search(lines[i])
        was = m.group(1)
        # Keep the tree's own spelling: same width, same case.
        now = ("%0*X" if was.upper() == was else "%0*x") % (len(was), real)
        lines[i] = lines[i][:m.start(1)] + now + lines[i][m.end(1):]
        changed += 1
    if changed:
        with io.open(p, 'w', encoding='utf-8', newline='') as fh:
            fh.write('\n'.join(lines))
    return changed


def prose_addresses(files):
    """Bare `$xxxx` mentions outside a declaration -- what --fix cannot reach."""
    n = 0
    for f in files:
        for line in pathlib.Path(f).read_text(encoding='utf-8',
                                              errors='replace').splitlines():
            if DECL.match(line.rstrip()):
                continue
            n += len(re.findall(r'\$[0-9a-fA-F]{4}\b', line))
    return n


# A name and an address are a pair only when NOTHING BUT PUNCTUATION separates
# them, on either side. Both orders occur and they are not interchangeable:
#
#     `UsingGUS` ($0bce), `TicksPerSecond` ($0bcc)     name first
#     $0c6e ChainPtr   $0c72 Complain                  address first, in a table
#
# **DISTANCE ALONE IS NOT ENOUGH, AND THE FAILURE IS SILENT.** English puts
# things in parallel:
#
#     `LoopMod` then `ForceLoopMod` is $02c8 then $02c9
#
# Here $02c8 belongs to LoopMod and $02c9 to ForceLoopMod, but ForceLoopMod is
# the NEARER name to $02c8. A proximity rule rewrites the first address with the
# second variable's value and produces a sentence that is wrong in a new way.
# This tool did exactly that before the rule was tightened.
#
# Requiring a gap free of letters keeps the two forms above and rejects every
# sentence with a verb in it. That loses real mentions -- "Frac at $0018" is a
# true one and goes unfixed -- and losing them is the right trade: an unfixed
# mention is a known unknown, and a mis-rewritten one is a new false fact.
PAIR_WINDOW = 24
LETTER = re.compile(r'[A-Za-z]')
NAME_TOKEN = re.compile(r'\b([A-Za-z_]\w{2,})\b')
ADDR_TOKEN = re.compile(r'\$([0-9a-fA-F]{4})\b')


def prose_claims(path, addresses, limit=None):
    """(line, name, cited, correct) for each prose mention that disagrees.

    `addresses` maps a declared name to the address the map or the chain gives
    it. A mention is only checkable when the line names a variable this file
    declares; everything else is reported as needing a person.
    """
    out, orphan = [], 0
    with io.open(path, encoding='utf-8', errors='replace', newline='') as fh:
        lines = fh.read().split('\n')
    for n, line in enumerate(lines, 1):
        if DECL.match(line.rstrip()):
            continue                       # --fix and --chain own the declarations
        addrs = []
        for am in ADDR_TOKEN.finditer(line):
            # A VALUE IS NOT AN ADDRESS. `$ffff` beside `GUSIrq` is the constant
            # the variable holds, and DGROUP is not that long -- so anything past
            # the end of the data segment cannot be an address in it.
            if limit is not None and int(am.group(1), 16) >= limit:
                continue
            # AN ASSIGNED NUMBER IS A VALUE. `StepVal := $1000` is code, and
            # $1000 is what the variable HOLDS, not where it lives.
            if line[:am.start(1) - 1].rstrip().endswith((':=', '=')):
                continue
            # A RANGE IS NOT A CLAIM ABOUT ONE VARIABLE. `$0018..$001d` describes
            # a span; rewriting either end leaves a sentence that says nothing.
            if line[am.end():am.end() + 2] == '..' or line[max(0, am.start(1) - 3):
                                                           am.start(1) - 1] == '..':
                continue
            addrs.append(am)
        # EACH ADDRESS IS CLAIMED ONCE, by the one name it is adjacent to.
        # Assigning per NAME instead lets two names claim one address and the
        # loser's rewrite lands on the winner's span.
        paired, owner = set(), {}
        for nm in NAME_TOKEN.finditer(line):
            # EXACT CASE. `Guard` is a variable and `guard` is an English word,
            # and this tree's prose is full of the second. Matching case-blind
            # paired the noun in "the poll re-entrancy guard" with the address
            # in the next column of a table.
            # EVERY name competes for an address, not only the ones we can
            # resolve. A name this file cannot resolve -- one declared in two
            # units, say -- is still the rightful owner of the address beside
            # it, and letting a further-away KNOWN name win puts that name's
            # value onto its neighbour's number.
            real = addresses.get(nm.group(1))
            for am in addrs:
                if am.end() <= nm.start():
                    gap, d = line[am.end():nm.start()], nm.start() - am.end()
                else:
                    gap, d = line[nm.end():am.start()], am.start() - nm.end()
                if d > PAIR_WINDOW or LETTER.search(gap):
                    continue
                key = (d, 0 if am.end() <= nm.start() else 1)
                if am.start(1) not in owner or key < owner[am.start(1)][0]:
                    owner[am.start(1)] = (key, nm.group(1), am.group(1), real)
        for col, (_, name, cited, real) in owner.items():
            paired.add(col)
            if real is not None and real != int(cited, 16):
                out.append((n, col, name, cited.lower(), real))
        for m in addrs:
            if m.start(1) not in paired:
                orphan += 1
    return out, orphan


def fix_prose(path, claims):
    """Rewrite only the paired mentions. Comments only, right to left."""
    p = pathlib.Path(path)
    with io.open(p, encoding='utf-8', errors='replace', newline='') as fh:
        lines = fh.read().split('\n')
    for n, col, name, cited, real in sorted(claims, reverse=True):
        i = n - 1
        assert lines[i][col:col + len(cited)].lower() == cited, "moved under us"
        now = ("%04X" if cited.upper() == cited else "%04x") % real
        lines[i] = lines[i][:col] + now + lines[i][col + len(cited):]
    if claims:
        with io.open(p, 'w', encoding='utf-8', newline='') as fh:
            fh.write('\n'.join(lines))
    return len(claims)


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


def report(path, decls, quiet=False, fixes=None):
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
                    if fixes is not None:
                        fixes[d['line']] = want
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
    mapfile = None
    for i, a in enumerate(argv):
        if a == "--map" and i + 1 < len(argv):
            mapfile = argv[i + 1]
    files = [a for i, a in enumerate(argv)
             if not a.startswith("--") and (i == 0 or argv[i - 1] != "--map")]
    if not files:
        raise SystemExit(__doc__)

    publics = map_publics(mapfile) if mapfile else None

    if "--prose" in argv:
        if publics is None:
            raise SystemExit("--prose needs --map: the addresses come from it")
        skip = ambiguous(files)
        dgroup_len = map_length(mapfile)
        total = orphans = 0
        for f in files:
            known = {}
            chain = {}
            report(f, scan(f), quiet=True, fixes=chain)
            for d in scan(f):
                if d['addr'] is None or d['name'].upper() in skip:
                    continue
                known[d['name']] = publics.get(d['name'].upper(), d['addr'])
            claims, orphan = prose_claims(f, known, dgroup_len)
            orphans += orphan
            for n, _, name, cited, real in claims:
                print("%s:%-5d %-16s the prose says $%s, %s is at $%04X"
                      % (pathlib.Path(f).name, n, name, cited, name, real))
            if "--fix" in argv:
                total += fix_prose(f, claims)
            else:
                total += len(claims)
        print()
        print("%d paired mention(s) %s"
              % (total, "rewritten" if "--fix" in argv else "disagree"))
        print("%d mention(s) name no variable -- a person has to read those"
              % orphans)
        return 1 if total and "--fix" not in argv else 0

    if "--fix" in argv:
        if publics is None:
            raise SystemExit("--fix needs --map: without it there is no right answer")
        skip = ambiguous(files)
        total = sum(fix(f, publics, skip, "--chain" in argv) for f in files)
        print("%d comment(s) rewritten to the linker's addresses" % total)
        print("%d name(s) skipped as ambiguous: %s"
              % (len(skip), ", ".join(sorted(skip)) or "none"))
        print("%d bare $xxxx mention(s) remain in prose, which --fix cannot reach"
              % prose_addresses(files))
        return 0
    total, claims, anchored = 0, 0, 0
    for f in files:
        decls = scan(f)
        claims += sum(1 for d in decls if d['addr'] is not None)
        if publics is not None:
            bad, n = against_map(f, decls, publics, quiet, ambiguous(files))
            total += bad
            anchored += n
        else:
            total += report(f, decls, quiet)
    print()
    if publics is not None:
        print("%d claim(s), %d of them named by the linker, %d disagree with it"
              % (claims, anchored, total))
        print("the other %d are not public -- run without --map for the relative check"
              % (claims - anchored))
    else:
        print("%d address claim(s) checked, %d disagree with the declarations"
              % (claims, total))
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
