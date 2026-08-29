r"""Comments in a sibling's source that carry knowledge, with the code they annotate.

    python kit/tools/pascal/harvest.py v1.39b
    python kit/tools/pascal/harvest.py v1.39b --unit PLAYMOD
    python kit/tools/pascal/harvest.py v1.39b --all      keep what the filters drop

WHAT IT IS FOR. A sibling implementation's comments are the author saying what
the code is for, in the author's own words, at the moment of writing it. That is
a class of evidence a reconstruction cannot produce for itself: bytes say what a
routine DOES and never say why, and an inline note beside a mixing loop --
"Añade el incremento fraccionario" -- names a step that no disassembly recovers.

**They are also mostly worthless in bulk.** One release tree here holds 2,512
comments, of which the great majority are section rules, restatements of the
declaration beside them, commented-out code and compiler directives. Reading all
of them to find the fifty that matter is the job this does.

## What it drops, and why each rule earns its place

  * **compiler directives** -- `{$I-}`, `{$R+}`. Not prose at all.
  * **rules and boxes** -- a line of dashes, equals or CP437 box characters.
    They separate; they do not say anything.
  * **commented-out code**, detected by Pascal punctuation and assignment. It is
    the previous version of the program, not a description of this one -- but
    see below, because a disabled ROUTINE is a different thing from a disabled
    line.
  * **restatements**, where the words are the identifier beside them with the
    capitals split. `{ Channel state definition. }` over `TCanal` adds nothing a
    reader did not just read.
  * **duplicates**. The same sentence appears beside forty declarations in a
    table; it is worth reading once.

## A disabled routine is where the best comments hide

Pascal's two comment forms do not nest, so `(* ... *)` around a routine turns the
whole thing -- code, and every `{ }` note inside it -- into ONE comment. On this
corpus that hid the single most valuable passage in the tree: the mixing loop,
commented out and preserved, with the author's line-by-line notes still attached
to the instructions they explain.

Read as one comment it is ten thousand characters of noise and every filter here
drops it. So a span past `INNER_MIN` is opened up and the comments inside it are
harvested in its place, marked `(disabled)`. They annotate code that does not run
in the sibling -- and in a reconstruction that code may well be live, which is
exactly why they are worth having.

## What it keeps, and what it tells you about each

Everything else, with the line of code it annotates -- the same line for a
trailing comment, the next code line for one that stands alone. An unattached
comment is kept and marked, because a block comment over a routine is often the
most valuable thing in the file.

Each is tagged with the language, because the two are worth different things.
This corpus's English comments are mostly interface documentation, which a
reconstruction usually recovers on its own. Its Spanish comments are the working
notes -- and they cluster in exactly the place documentation never reaches, the
inline assembler.

## What it cannot do

**It cannot tell you a comment is true.** A sibling is a different version, and a
note describing a routine that changed is worse than no note. Every line this
prints is a candidate for a person to check against the code it would be placed
beside, in the version it would be placed in.
"""

import re
import sys
import pathlib
import collections

DIRECTIVE = re.compile(r'^\{\$')
# A file header is a form, not knowledge. Every unit in a tree carries the same
# eight fields and none of them says anything about the code.
BOILERPLATE = re.compile(
    r'^(MODULE|AUTHOR|DESCRIPTION|MODIFICATIONS|HISTORY|PURPOSE|NOTES|VERSION|'
    r'RUTINA|ROUTINE|ENTRADAS|SALIDAS|PARAMETERS|RETURNS)\s*:|'
    r'^\(C\)|^Copyright|^\d{1,2}[-/][A-Za-z]{3}[-/]\d{2,4}', re.I)
RULE = re.compile(r'^[\s\-=_*~.·+|/\\#<>─-╿▀-▟]*$')
CODEY = re.compile(r':=|\bBEGIN\b|\bEND\b;|\bIF\b.*\bTHEN\b|\bPROCEDURE\b|'
                   r'\bFUNCTION\b|\bVAR\b\s*$|\)\s*;\s*$', re.I)
WORD = re.compile(r"[A-Za-zÀ-ÿ]{2,}")
# **A SHARED WORD IS NOT EVIDENCE.** The first version of this list held `no`,
# `si`, `es`, `en`, `byte` and `buffer`, and it labelled "No filtering.", "Byte
# size filters." and "Size of the buffer" as Spanish. Those words exist in both
# languages, so each one only adds noise. What is left is function words English
# does not have, and a comment needs an accent or TWO of them to count.
SPANISH_ONLY = re.compile(
    r'\b(el|la|los|las|del|que|para|por|con|una|uno|este|esta|esto|como|'
    r'mas|hay|ser|desde|hasta|cuando|donde|porque|pero|sobre|entre|cada|'
    r'todo|toda|otro|otra|muestra|puntero|volumen|canal|tabla|palabra|salto|'
    r'rutina|rutinas|comando|comandos|comienzo|valor|tiempo|siguiente|'
    r'primero|ultimo|nada|tocar|meto|leo|vuelvo|pasado|llegado|apuntando)\b',
    re.I)
ACCENT = re.compile(r'[áéíóúüñ¿¡ÁÉÍÓÚÑ]')


def spanish(text):
    return bool(ACCENT.search(text)) or len(SPANISH_ONLY.findall(text)) >= 2


def comments(path):
    """(line, text, attached-code) for every comment in one file."""
    raw = path.read_bytes().decode('cp437', errors='replace')
    lines = raw.split('\n')
    asm = path.suffix.upper() in ('.ASM', '.INC')

    spans = []
    for m in re.finditer(r'\{[^}]*\}|\(\*.*?\*\)', raw, re.S):
        spans.append((m.start(), m.end(), m.group(0)))
    if asm:
        for m in re.finditer(r';[^\n]*', raw):
            spans.append((m.start(), m.end(), m.group(0)))
    spans.sort()

    starts = [0]
    for line in lines:
        starts.append(starts[-1] + len(line) + 1)

    # A `(* *)` wrapped around a routine swallows every `{ }` inside it. Past
    # this length, treat the span as a REGION and harvest what is inside.
    INNER_MIN = 400
    opened = []
    for a, b, text in spans:
        if b - a < INNER_MIN or not re.search(r'\{[^}]*\}', text):
            opened.append((a, b, text, False))
            continue
        for m in re.finditer(r'\{[^}]*\}', text):
            opened.append((a + m.start(), a + m.end(), m.group(0), True))
    spans = sorted(opened)

    out = []
    for a, b, text, inner in spans:
        n = max(i for i in range(len(starts)) if starts[i] <= a)
        before = lines[n][:a - starts[n]].strip()
        after = ''
        if not before:                       # a comment on its own -- look ahead
            for j in range(n + 1, min(n + 6, len(lines))):
                cand = lines[j].strip()
                if cand and not cand.startswith(('{', ';', '(*')):
                    after = cand
                    break
        out.append((n + 1, text, before or after, bool(before), inner))
    return out


def body(text):
    """The words inside the delimiters."""
    t = text.strip()
    for a, b in (('{', '}'), ('(*', '*)')):
        if t.startswith(a):
            t = t[len(a):]
            if t.endswith(b):
                t = t[:-len(b)]
    if t.startswith(';'):
        t = t.lstrip(';')
    return ' '.join(t.split())


def restates(text, code):
    """True when the comment is the identifier beside it, spelt out."""
    if not code:
        return False
    ident = re.findall(r'[A-Za-z_]\w*', code)[:2]
    split = set()
    for i in ident:
        split |= {w.lower() for w in re.findall(r'[A-Z]?[a-z]+|[A-Z]+', i)}
    words = {w.lower() for w in WORD.findall(text)}
    return bool(words) and len(words - split) <= 1


def main(argv):
    # A tool that decodes CP437 will print characters a legacy console cannot
    # encode, and it dies on the first box-drawing character it meets. Say the
    # output encoding rather than inherit it.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                              # noqa: BLE001
        pass

    keep_all = "--all" in argv
    unit = None
    for i, a in enumerate(argv):
        if a == "--unit" and i + 1 < len(argv):
            unit = argv[i + 1].upper()
    roots = [a for i, a in enumerate(argv)
             if not a.startswith("--") and (i == 0 or argv[i - 1] != "--unit")]
    if not roots:
        raise SystemExit(__doc__)

    # A root may be a directory to walk or a single file to read. Naming the
    # files is how you restrict a harvest to the units a target actually has --
    # a sibling tree carries whole subsystems the target never included, and
    # their comments are noise however good they are.
    files = []
    for r in roots:
        q = pathlib.Path(r)
        if q.is_file():
            files.append(q)
            continue
        for ext in ("*.PAS", "*.ASM", "*.INC"):
            files += sorted(q.rglob(ext))

    seen = set()
    total = kept = 0
    per = collections.Counter()
    for f in files:
        if unit and f.stem.upper() != unit:
            continue
        rows = []
        for n, text, code, inline, inner in comments(f):
            total += 1
            t = body(text)
            if not keep_all:
                if DIRECTIVE.match(text.strip()) or RULE.match(t) or len(t) < 8:
                    continue
                if len(WORD.findall(t)) < 2 or BOILERPLATE.match(t):
                    continue
                if CODEY.search(t):
                    continue
                if restates(t, code):
                    continue
                if t.lower() in seen:
                    continue
                seen.add(t.lower())
            rows.append((n, t, code, inline, inner))
        if not rows:
            continue
        print("=" * 78)
        print("%s  --  %d kept" % (f.as_posix(), len(rows)))
        print("=" * 78)
        for n, t, code, inline, inner in rows:
            lang = "es" if spanish(t) else "en"
            print("%-5d %s %s %s%s" % (n, lang, "|" if inline else ">",
                                        "(disabled) " if inner else "", t[:100]))
            if code:
                print("          %s" % code[:88])
            kept += 1
            per[f.stem.upper()] += 1
        print()

    print("%d of %d comment(s) kept" % (kept, total))
    for name, c in per.most_common(12):
        print("  %-12s %d" % (name, c))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
