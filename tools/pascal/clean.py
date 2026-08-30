r"""Copy a reconstruction's source and strip the reverse-engineering apparatus.

    python kit/tools/pascal/clean.py src clean-src
    python kit/tools/pascal/clean.py src clean-src --dry
    python kit/tools/pascal/clean.py src clean-src --report

WHY A SECOND COPY. A reconstruction's source answers "how do we know this byte
is right". Every address, every operand delta, every note on which instrument
caught what is there because the reconstruction needed it -- and none of it is
what a reader wanting to understand the PROGRAM has come for. The two audiences
want opposite things from the same file, and no single copy serves both.

So this makes the second copy mechanically, from the first. **A script and not a
hand edit**, because the reconstruction keeps moving and a hand-made copy drifts
away from it the day after it is made.

## What it removes, and nothing else

**Address-only comments.** `{ 0322..032d }`, `{ 1642:0004 }`, `{ DS:$09ee }` --
a comment whose entire content is addresses says where a thing is in a binary
nobody reading this copy is looking at. On one corpus these are 1,900 of 4,184
comments, so removing them is most of the job by volume.

**Address prefixes.** `{ 0a4d..0a57 -- and NOT `Tempo := CurSpeed` ... }` keeps
everything after the dash and loses the span. The sentence is about the program;
the span is about the image.

**A `segment:offset` prefix with no dash after it.** `{ 1b24:003a -> AND AL,0FBh }` becomes `{ -> AND AL,0FBh }`: the site is
apparatus and the note explains the instruction. Only the two-part form is
trimmed this way, never a bare offset -- `{ 0000 RETF 6 }` is a routine table
where the number IDENTIFIES the entry, and losing it leaves a row naming
nothing.

`{ DS:$02d2  the FilterOff key }` goes the same way and for the same reason: the
`DS:` says outright that what follows is an address, so it cannot be a length or
a row label either.

That distinction is the whole rule, and it is about NOTATION rather than about
value. A `segment:offset` or a `DS:$` prefix announces itself as a place in
someone else's binary. A bare four-digit number might be a place, or a length, or
a row label, and this tool cannot tell which -- so it is never touched.

**On ANY line of a block comment, not just the first.** The common shape here is
a rule of dashes, then the address on the line below it:

    { -------------------------------------------------------------------
      12ba:0007 -- UnCanal. Mix one channel into its own buffer.

Matching only at the start of the comment left every one of those untouched, and
they are the headline of the routine -- the first line a reader sees. Found by
reading the output rather than by any check, which is the argument for reading
it.

That is all it does, and the restraint is deliberate. It would be easy to drop
whole paragraphs by scoring them for words like "operand" or "byte-identical",
and easy to be wrong: the paragraphs that explain a self-modifying instruction, a
fixed-point invariant or a compiler's evaluation order use exactly that
vocabulary and are the most valuable prose in the tree. **A stripper that guesses
deletes the best comments first.** Anything past a bare address is left for a
person, and `--report` lists what was left so the reading has a worklist.

## What it must never touch

Effect codes like `{ E 2x }` and `{ 0 xy }`, field offsets like `{ +$002 }`,
frame slots like `{ [BP-2] }`, and anything carrying a `[1.39b]` marker -- those
last are the original author's words, which are the point of the exercise. The
token grammar below admits only whole addresses, so a two-character effect code
cannot look like one.

## It does not own the whole directory

The output directory may hold things this tool did not write -- a README, a
diagram, notes. **They are left alone.** An earlier version deleted the
directory and rebuilt it, which is the obvious way to avoid stale files and
also destroys the only hand-written page in the copy the moment the tool runs
again.

So generated files are overwritten and everything else is kept. Anything in the
directory that did not come from a source file is listed at the end of the run,
which is how a stale leftover stays visible without being deleted for you.

## It checks itself, every run

A stripper edits by pattern and a pattern can reach further than intended. So
after writing each file this compares the two copies with **all** comments
removed from both -- if a single line of code differs, the run fails and says
which line. That is cheap, it is exact, and it is the only thing standing
between a regex and a silently altered program.

The check is not optional and there is no flag to skip it.

## AND THE CHECK HAS ONE BLIND SPOT: `{$` IS A DIRECTIVE, NOT A COMMENT

The comparison blanks every `{ ... }` in both copies, which is what makes it
immune to wording. It is therefore also immune to a `{$A+}` -- so damage to a
compiler directive is the one edit this tool can make that its own check will
never report, and directives are exactly the comments that change the program.

Two ways it can happen, both measured on this corpus and both fixed above:
trimming a prefix off `{ DS:$0582 -- $FFFF means ... }` leaves `{$FFFF ... }`,
which the compiler reads as the far-calls directive; and a repair applied
without first testing that anything was trimmed rewrites `{$A+}` itself into
`{ $A+}`, silently disabling all eighteen of them.

**So build the stripped copy.** Point a second build config at it and compare
the linked image: that is the only check that sees this class of defect, it is
one command, and on this corpus it came back 0 differing bytes over a
63,040-byte load image.

## What this copy is not

**It is not the reconstruction of record.** That stays where it is; this copy is
documentation, and a reader who wants to know what the bytes are should go back
to the source it came from. But it SHOULD build, and building it is the only
way to know the stripper has not changed the program.
"""

import io
import re
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import magic                                                      # noqa: E402

# An address, in every form this method writes one.
TOKEN = (r'(?:[0-9a-fA-F]{4}:[0-9a-fA-F]{4}'      # segment:offset
         r'|DS:\$[0-9a-fA-F]{2,4}'                # a data address
         r'|[0-9a-fA-F]{4})')                     # a bare offset
SPAN = r'%s(?:\s*\.\.\s*%s)?' % (TOKEN, TOKEN)
ONLY = re.compile(r'^\s*(?:%s)(?:[\s,/]+(?:%s))*\s*$' % (SPAN, SPAN))
LEAD = re.compile(r'^[ \t]*(?:%s)(?:[\s,/]+(?:%s))*[ \t]*--[ \t]*'
                  % (SPAN, SPAN), re.M)
# A segment:offset and then a note, with no dash between them. Two-part form
# only: a bare offset may be identifying a row rather than citing a site.
SITE_TOKEN = r'(?:[0-9a-fA-F]{4}:[0-9a-fA-F]{4}|DS:\$[0-9a-fA-F]{2,4})'
SITE = re.compile(r'^[ \t]*%s(?:[\s,/]+%s)*[ \t]+(?=\S)'
                  % (SITE_TOKEN, SITE_TOKEN), re.M)
COMMENT = re.compile(r'\{[^{}]*\}')


def clean_text(text):
    """Return (text, dropped, trimmed) with the apparatus removed.

    TWO PASSES, AND THE SPLIT IS THE SAFETY. Prefix trimming runs over the whole
    text so it reaches a block comment spanning twenty lines; DROPPING runs line
    by line, so it can only ever remove a comment that sits alone on its line.
    A dropper allowed to match across lines would delete a paragraph the moment
    its first line looked like an address.
    """
    dropped = trimmed = 0

    def prefix(m):
        nonlocal trimmed
        body = m.group(0)[1:-1]
        if '1.39b' in body:
            return m.group(0)
        # A single space, not nothing: the opening brace would otherwise sit
        # against the first word.
        cut = SITE.sub(' ', LEAD.sub('', body))
        # **`{$` IS A COMPILER DIRECTIVE, NOT A COMMENT.** Trimming a prefix can
        # leave the brace against a `$` that was mid-sentence -- `{ DS:$0582 --
        # $FFFF means ... }` becomes `{$FFFF means ... }`, which Turbo Pascal
        # reads as the far-calls directive and the rest as its argument. The
        # stripped copy then compiles differently from the source it came from,
        # and NOTHING HERE WOULD SAY SO: the self-check below blanks every
        # comment in both copies, directives included, so this is invisible to
        # exactly the instrument meant to catch it.
        if cut != body:
            # Only once something was actually trimmed -- applied unconditionally
            # this rewrites `{$A+}` itself, which is a directive and not a prefix
            # this tool has any business touching.
            if cut[:1] == '$':
                cut = ' ' + cut
            trimmed += 1
            return '{' + cut + '}'
        return m.group(0)

    text = re.compile(r'\{[^{}]*\}', re.S).sub(prefix, text)

    def one(m):
        nonlocal dropped, trimmed
        body = m.group(0)[1:-1]
        if '1.39b' in body:                  # the author's words: never touched
            return m.group(0)
        if ONLY.match(body):
            dropped += 1
            return ''
        return m.group(0)

    out = []
    for line in text.split('\n'):
        new = COMMENT.sub(one, line)
        # A line that held nothing but its comment goes with it; a line of code
        # keeps its indentation and loses the trailing blank.
        if new.strip() or not line.strip():
            out.append(new.rstrip() if new != line else line)
        elif not line.strip():
            out.append(line)
    return '\n'.join(out), dropped, trimmed


def survivors(text):
    """Comments still mentioning an address -- the worklist a person needs."""
    hits = []
    for n, line in enumerate(text.split('\n'), 1):
        for m in COMMENT.finditer(line):
            body = ' '.join(m.group(0)[1:-1].split())
            if '1.39b' in body:
                continue
            if re.search(r'[0-9a-fA-F]{4}:[0-9a-fA-F]{4}|DS:\$', body):
                hits.append((n, body[:88]))
    return hits


def code_only(text, asm):
    """The file with every comment blanked -- what must not change."""
    return [ln.strip() for ln in
            magic.strip(text, asm=asm).split('\n') if ln.strip()]


def main(argv):
    args = [a for a in argv if not a.startswith('--')]
    if len(args) != 2:
        raise SystemExit(__doc__)
    src, dst = pathlib.Path(args[0]), pathlib.Path(args[1])
    dry, report = '--dry' in argv, '--report' in argv

    if not dry:
        dst.mkdir(parents=True, exist_ok=True)

    files = drop = trim = left = 0
    written = set()
    for f in sorted(src.iterdir()):
        if not f.is_file():
            continue
        raw = io.open(f, encoding='utf-8', errors='replace', newline='').read()
        text = raw.replace('\r\n', '\n')
        new, d, t = clean_text(text)
        rest = survivors(new)
        files += 1
        drop += d
        trim += t
        left += len(rest)
        print("%-16s dropped %4d  trimmed %3d  still addressed %3d"
              % (f.name, d, t, len(rest)))
        if report:
            for n, body in rest[:8]:
                print("      %5d  %s" % (n, body))
        asm = f.suffix.upper() in ('.ASM', '.INC')
        if code_only(text, asm) != code_only(new, asm):
            before, after = code_only(text, asm), code_only(new, asm)
            for x, y in zip(before, after):
                if x != y:
                    raise SystemExit(
                        "%s: THE CODE CHANGED, which this must never do.\n"
                        "  was : %s\n  now : %s" % (f.name, x[:78], y[:78]))
            raise SystemExit("%s: the code changed length, %d -> %d"
                             % (f.name, len(before), len(after)))

        written.add(f.name)
        if not dry:
            io.open(dst / f.name, 'w', encoding='utf-8', newline='').write(
                new.replace('\n', '\r\n'))

    print()
    print("%d file(s): %d address-only comment(s) dropped, %d prefix(es) trimmed"
          % (files, drop, trim))
    print("%d comment(s) still mention an address -- those need a person" % left)
    print("every file verified: not one line of code differs")

    if not dry and dst.exists():
        kept = [q.name for q in sorted(dst.iterdir())
                if q.is_file() and q.name not in written]
        if kept:
            print("kept, not generated by this tool: %s" % ", ".join(kept))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
