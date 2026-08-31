"""Comment nesting and the directive set: the two things a comment edit breaks.

    python kit/tools/pascal/braces.py src/*.PAS
    python kit/tools/pascal/braces.py src/P2SOLID.PAS --quiet
    python kit/tools/pascal/braces.py src/*.PAS --directives > after.txt

WHAT IT IS FOR. Editing comments is supposed to be the safe kind of change, and
in a reconstruction it is the dangerous kind: **four of this method's recorded
hazards are code changes made while editing a comment, and two of them produced
no diagnostic of any kind.** Both silent ones were comment edits that
accidentally created or destroyed a **compiler directive** -- `{ [re] $G+}` is
286 codegen quietly off, and a trimmed prefix leaving `{$FFFF ... }` is far
calls quietly on. Both compile clean and change every byte downstream.

Nothing else catches this class before the build. A stripper's self-check blanks
every comment in both copies before comparing, so it is structurally blind to a
directive. The compiler reports a nesting defect dozens of lines from its cause,
if at all -- and a nesting defect that happens to still compile reports nothing.

So this reads the file the way the compiler reads it and answers two questions.

## 1. Does a comment nest, and is every comment closed

**Pascal comments do not nest.** A comment opened with `{` ends at the next `}`
and a comment opened with `(*` ends at the next `*)`. So a `{` while already
inside a `{ }` comment means that comment ended early at some `}` further on,
and everything between is being parsed as CODE.

The most common way to write one is to mention a directive in prose:

    { The unit needs {$A-} because a Word sits at an odd offset }
                            ^ the comment ends HERE, at this brace's partner

## 2. AND THE TWO FORMS ARE NOT INTERCHANGEABLE -- THIS IS THE POINT

`{` inside a `(* *)` comment is **legal and deliberate**, and any tool that
flags it is worse than no tool. `(* *)` is the only way to write a directive
inside prose, so a corpus that documents its directives carefully uses that
form precisely where the risk is:

    (* 286 CODE ON. This unit had no {$G+} at all, so it took the command
       line's default and emitted MOV SP,BP / POP BP. *)

That is one comment, correctly written, and the `{$G+}` in it is prose. A
scanner that counted braces alone would report it as a directive -- so the
directive list below counts only what is a directive **where it appears**:
outside any comment. Getting this backwards turns the instrument into a source
of false positives in exactly the files someone was most careful with.

## The directive set is the output to diff

A directive is `{$...}` or `(*$...*)` at top level. The list is printed per
file, in order, with line numbers, because **the check is a comparison**: take
it before an edit and after, and the sets must match. That is the only
mechanical way to see a directive that was created or destroyed by prose.

    braces.py src/*.PAS --directives > before.txt
    ... edit ...
    braces.py src/*.PAS --directives > after.txt
    diff before.txt after.txt

**FIX A NESTING DEFECT BEFORE READING THE DIRECTIVE LIST**, because after one
the list is worthless -- and the reason is the whole point of the tool. A probe
written to break this reported the nesting defect and then **zero directives in
a file that has one**: with the comment ending early, its remaining prose was
read as code, an apostrophe in it opened a string literal, and the scan ran on
to the next quote several routines later. That is not a flaw in the scan. It is
what the compiler does with the same bytes, which is why the defect matters and
why nothing downstream of one can be trusted.

## Assembler files

`;` runs to end of line and braces mean nothing, so a `{$L FOO.OBJ}` inside an
assembler comment is prose twice over. Comments are removed first and any brace
left over is reported as suspicious, because there is no legitimate reason for
one to survive.

Exit status is 1 if anything was found, so it can gate a batch.
"""

import io
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import clean                                                      # noqa: E402


def scan(text):
    """(nested, unclosed, directives) reading the text as the compiler does.

    A hand-written scanner rather than a regex, because the answer depends on
    STATE: whether a `{` opens a comment, is prose inside `(* *)`, or sits in a
    string literal is decided by what came before it, and that is exactly what
    a regex cannot carry.
    """
    nested, directives = [], []
    state, opened, i, line, n = None, 0, 0, 1, len(text)

    while i < n:
        ch = text[i]
        if ch == '\n':
            line += 1
            i += 1
            continue

        if state is None:
            if ch == '{':
                state, opened = '{', line
                if text[i + 1:i + 2] == '$':
                    end = text.find('}', i)
                    directives.append(
                        (line, text[i:end + 1] if end >= 0 else text[i:i + 24]))
                i += 1
                continue
            if text.startswith('(*', i):
                state, opened = '(*', line
                if text[i + 2:i + 3] == '$':
                    end = text.find('*)', i)
                    directives.append(
                        (line, text[i:end + 2] if end >= 0 else text[i:i + 24]))
                i += 2
                continue
            if ch == "'":
                # A STRING, and it has to be skipped: `'{'` is not a comment.
                # Pascal doubles a quote to escape it, which a plain scan for
                # the next quote handles correctly -- the pair reads as a close
                # followed by a reopen, and lands in the same place.
                i += 1
                while i < n and text[i] != "'":
                    if text[i] == '\n':
                        line += 1
                    i += 1
                i += 1
                continue
            i += 1
            continue

        if state == '{':
            if ch == '}':
                state = None
                i += 1
                continue
            if ch == '{':
                nested.append((line, '{', context(text, i)))
                i += 1
                continue
            i += 1
            continue

        # state == '(*'  -- and a `{` in here is LEGAL, see the docstring
        if text.startswith('*)', i):
            state = None
            i += 2
            continue
        if text.startswith('(*', i):
            nested.append((line, '(*', context(text, i)))
            i += 2
            continue
        i += 1

    return nested, (opened if state else None), directives


def context(text, i, span=34):
    """The characters either side of a defect, for a report a person can read."""
    lo, hi = max(0, i - span), min(len(text), i + span)
    return ' '.join(text[lo:hi].split())


def check(path):
    """(nested, unclosed, directives) for one file, assembler or Pascal."""
    text = io.open(path, encoding='utf-8', errors='replace').read()
    if clean.is_asm(path, text):
        # Comments away first, then any brace at all is suspicious: nothing in
        # an assembler source has a reason to carry one.
        bare = clean.magic.strip(text, asm=True)
        hits = [(bare[:k].count('\n') + 1, ch, context(bare, k))
                for k, ch in enumerate(bare) if ch in '{}']
        return hits, None, []
    return scan(text)


def main(argv):
    files = [a for a in argv if not a.startswith('--')]
    if not files:
        raise SystemExit(__doc__)
    quiet = '--quiet' in argv
    only_directives = '--directives' in argv
    bad = 0

    for f in files:
        nested, unclosed, directives = check(f)
        name = pathlib.Path(f).name
        if only_directives:
            for ln, d in directives:
                print("%-16s %-5d %s" % (name, ln, d))
            continue

        problems = len(nested) + (1 if unclosed else 0)
        bad += problems
        if problems or not quiet:
            print("%s" % name)
        for ln, what, ctx in nested:
            print("  %-5d NESTED %-3s Pascal comments do not nest: ...%s..."
                  % (ln, what, ctx))
        if unclosed:
            print("  UNCLOSED COMMENT, opened at line %d" % unclosed)
        if not quiet:
            print("  %d directive(s): %s"
                  % (len(directives),
                     ", ".join("%d:%s" % d for d in directives) or "none"))

    if not only_directives:
        print()
        print("%d problem(s) in %d file(s)" % (bad, len(files)))
        if bad:
            print("A nesting defect can still compile. Fix it before the build "
                  "tells you something else.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
