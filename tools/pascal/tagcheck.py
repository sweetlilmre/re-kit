"""Comments that carry reverse-engineering apparatus without saying so.

    python kit/tools/pascal/tagcheck.py src/*.PAS src/*.ASM
    python kit/tools/pascal/tagcheck.py src/*.PAS --quiet
    python kit/tools/pascal/tagcheck.py src/*.PAS --count

WHAT IT IS FOR. A reconstruction's source carries two kinds of prose that read
alike and serve opposite readers: the EVIDENCE for how something was learned,
and the EXPLANATION of what it does. A stripped copy meant for the second
reader has to lose the first, and no pattern can tell them apart -- the split is
a judgement, so it is written down as a tag.

Tagging is keep-by-default, which is the cheap way round: on the corpus this was
built for, half the comments carry no apparatus at all and never need touching.
The cost of keep-by-default is that a NEW untagged comment leaks. This is the
instrument for that, and it is the reason the arrangement is safe rather than
merely convenient.

## What counts as a tell

Only mechanical ones -- a `segment:offset`, a `DS:$` address, the name of a
measuring tool, a `~~withdrawn~~` marker. Never prose style. A tool that
guessed at tone would cry wolf until it was ignored, and an instrument nobody
runs is worse than none.

## What is exempt, and why each

* **`[re]` paragraphs.** They are removed by the stripper, so what they hold
  cannot leak. This is the tag the tool exists to encourage.
* **`[1.39b]` paragraphs.** The original author's own words, quoted. They are
  the best explanation in such a tree and are kept deliberately.

**`[reading]` IS NOT EXEMPT, AND THAT IS THE POINT.** It marks a claim resting
only on someone's reading of the instructions, and it is KEPT in the stripped
copy so inferences stay visible and countable. Kept means it can leak, so it is
held to the same standard as untagged prose.

## The blind spot

It reports what a comment SAYS, never what the code does, so a paragraph can be
clean here and still be wrong about the program. And it stops at the text: a
trimmed prefix that forms a compiler directive changes what compiles and is
invisible to every reading of it. Only building the stripped copy sees that.
Run both.
"""

import io
import re
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import clean                                                      # noqa: E402

# The tells. Mechanical, every one -- a thing no explanation of behaviour needs.
TELLS = (
    (re.compile(r'\b[0-9a-fA-F]{4}:[0-9a-fA-F]{4}\b'), 'a segment:offset'),
    (re.compile(r'\bDS:\$[0-9a-fA-F]{2,4}\b'), 'a DS: address'),
    (re.compile(r'\b\w+\.py\b'), 'a measuring tool'),
    (re.compile(r'~~'), 'a withdrawn claim'),
    # Added after the first pilot leaked a stack-frame table: the paragraph
    # held no address and no tool name, so nothing above matched it, and a
    # reader of the stripped copy met `[BP+$0c] @Result` with no frame
    # anywhere in sight. A frame slot is apparatus by definition -- it
    # describes the call, not the behaviour.
    (re.compile(r'\[BP[-+]'), 'a stack frame slot'),
)
EXEMPT = re.compile(r'^\s*\[(?:re|1\.39b)\]', re.I)
COMMENT = re.compile(r'\{[^{}]*\}', re.S)


def paragraphs(text, asm):
    """(line number, paragraph) for every comment paragraph in the file.

    Pascal splits a { } comment on blank lines; assembler has no such grain, so
    a run of consecutive `;` lines is one paragraph and a trailing comment on a
    line of code is its own.
    """
    if not asm:
        for m in COMMENT.finditer(text):
            start = text[:m.start()].count('\n') + 1
            body = m.group(0)[1:-1]
            off = 0
            for para in re.split(r'\n[ \t]*\n', body):
                yield start + body[:off].count('\n'), para
                off += len(para) + 2
        return
    run, first = [], 0
    for n, line in enumerate(text.split('\n'), 1):
        s = line.strip()
        if s.startswith(';'):
            if not run:
                first = n
            run.append(s[1:].lstrip())
            continue
        if run:
            yield first, '\n'.join(run)
            run = []
        if ';' in line:                      # a trailing note on a code line
            yield n, line.split(';', 1)[1].strip()
    if run:
        yield first, '\n'.join(run)


def check(path):
    """What LEAKS, which is not the same as what a comment contains.

    THE FIRST BUILD OF THIS TOOL SCANNED THE SOURCE AND CRIED WOLF: 2,296 hits
    across 34 files, and nearly all of them were address prefixes the stripper
    already removes on its own. An instrument that reports work already done is
    one nobody runs.

    So it strips first, with the stripper's own code rather than a second copy
    of the rules, and scans what comes out. What survives is what a reader of
    the stripped copy would actually meet.
    """
    text = io.open(path, encoding='utf-8', errors='replace').read()
    asm = pathlib.Path(path).suffix.upper() in ('.ASM', '.INC')
    text, _, _, _ = clean.clean_text(text.replace('\r\n', '\n'), asm=asm)
    hits = []
    for n, para in paragraphs(text, asm):
        if not para.strip() or EXEMPT.match(para):
            continue
        for pat, what in TELLS:
            m = pat.search(para)
            if m:
                hits.append((n, what, m.group(0), ' '.join(para.split())[:70]))
                break
    return hits


def main(argv):
    files = [a for a in argv if not a.startswith('--')]
    if not files:
        raise SystemExit(__doc__)
    quiet, count = '--quiet' in argv, '--count' in argv
    total = 0
    for f in files:
        hits = check(f)
        total += len(hits)
        if hits and not count:
            if not quiet:
                print("%s" % pathlib.Path(f).name)
            for n, what, tok, body in hits:
                print("  %-5d %-18s %-12s %s"
                      % (n, what, tok[:12], body))
    print()
    print("%d untagged paragraph(s) carry apparatus across %d file(s)"
          % (total, len(files)))
    if total:
        print("Tag each `[re]` if it is evidence, or rewrite it if it is not.")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
