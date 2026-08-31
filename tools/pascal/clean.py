r"""Copy a reconstruction's source and strip the reverse-engineering apparatus.

    python kit/tools/pascal/clean.py src clean-src
    python kit/tools/pascal/clean.py src clean-src --dry
    python kit/tools/pascal/clean.py src clean-src --report
    python kit/tools/pascal/clean.py src clean-src --exclude asm/shared-exempt.txt

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

**ANY SEGMENT REGISTER, NOT JUST DS.** `CS:$002C` names a constant sitting in
the original's CODE segment and is an address by exactly the same argument, but
knowing only `DS:` left 70 of them across 19 files that neither this tool nor
the checker could see. `ES:` and `SS:` are admitted for the same reason before a
corpus produces one. In Pascal these forms appear only in comments -- the
language writes `Mem[Seg:Ofs]` with no `$` -- and in assembler a real override
is `es:[00CCh]`, also without one, so the pattern cannot reach code.

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

## THE TREE IS A TREE, AND ONLY ONE CORPUS EVER SAID OTHERWISE

An earlier version walked `src.iterdir()` and skipped anything that was not a
file, **silently**. On a flat corpus that is correct and invisible; on a tree it
copies the units and leaves the hand-written assembler, the generated tables,
the harnesses and the batch file behind, and says nothing about having done so.
The stripped copy then cannot build, and the first thing that tells you is the
compiler failing on a missing include.

So the walk recurses and relative paths are preserved. A directory is created
on demand, and **a file this tool does not understand is copied BYTE FOR BYTE**:
only `.PAS`, `.ASM` and `.INC` carry comments in a grammar it knows. A `.BAT` or
a tool's data file has braces and semicolons that mean something else entirely,
and processing one as Pascal is how a stripper edits a file it was never
pointed at.

## AN INSTRUMENT'S OWN INPUT IS NOT DOCUMENTATION: `--exclude`

Some files in a reconstruction's source tree are apparatus by NATURE rather than
by tagging -- a comparison tool's exemption list, say. They document nothing
about the program, nothing in the build reads them, and their content is a claim
about the measuring rather than about the subject. A tag cannot reach them,
because they are not comments.

`--exclude` takes a path relative to the source root, repeatable, matched as a
glob against the relative path in POSIX form (`asm/shared-exempt.txt`,
`*/scratch/*`). An excluded file is reported as such and not written, so a reader
of the run can see the decision rather than inferring it from an absence -- which
is the same reason the verbatim copies are reported by name.

Excluding a `.PAS`, `.ASM` or `.INC` is refused outright. Those are the sources
the stripped copy exists to carry, the build needs every one of them, and a tool
that will silently leave a unit out is the flat-walk defect wearing a flag.

## AND THE LINE ENDINGS ARE THE INPUT'S, NOT THIS TOOL'S

The final write used to be `new.replace('\n', '\r\n')`, unconditionally. A
corpus whose sources are CRLF on disk cannot see that; one whose sources are LF
-- because `.gitattributes` marks them `-text` and they were authored that way
-- gets a copy that differs from its origin in every line of every file, which
makes any diff between the two trees noise and hides the one line that matters.

Each file is written with the endings it was read with. Preserving is the only
rule that is right on both corpora, and a bulk line-ending change is a hazard
in its own right: it rewrites every file in the tree for no measured gain.

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
import fnmatch
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import magic                                                      # noqa: E402

# An address, in every form this method writes one.
TOKEN = (r'(?:[0-9a-fA-F]{4}:[0-9a-fA-F]{4}'      # segment:offset
         r'|(?:DS|CS|ES|SS):\$[0-9a-fA-F]{2,4}'   # a segmented address
         r'|\[BP[-+]\$?[0-9A-Fa-f]{1,4}h?\]'      # a stack frame slot
         r'|[0-9a-fA-F]{4})')                     # a bare offset
SPAN = r'%s(?:\s*\.\.\s*%s)?' % (TOKEN, TOKEN)
# **AN ARROW IS A JOINER, exactly as a comma is.** `{ 1000:0038 -> 1436:0000 }`
# is a call site and the routine it reaches: two citations, no prose. Without
# the arrow admitted here the address-only rule does not fire, the leading half
# is trimmed instead, and the comment survives as `{ -> 1436:0000 }` -- which is
# apparatus wearing a punctuation mark. 82 of them on one corpus, 23 in a single
# file.
JOINER = r'(?:[ \t]*(?:->|[,/])[ \t]*|\s+)'
ONLY = re.compile(r'^\s*(?:%s)(?:%s(?:%s))*\s*$' % (SPAN, JOINER, SPAN))
# **THE BYTES AT THAT ADDRESS ARE APPARATUS TOO.** `{ DS:$0962  7f }` loses
# its prefix and leaves `{ 7f }` beside `= 127` -- the same number twice, once
# in a base the reader did not ask for. Anything left that is only hex pairs
# is the image quoted back, not a note about the code.
BYTES = re.compile(r'^\s*[0-9a-fA-F]{2}(?:\s+[0-9a-fA-F]{2})*\s*$')
LEAD = re.compile(r'^[ \t]*(?:%s)(?:[\s,/]+(?:%s))*[ \t]*--[ \t]*'
                  % (SPAN, SPAN), re.M)
# A segment:offset and then a note, with no dash between them. Two-part form
# only: a bare offset may be identifying a row rather than citing a site.
SITE_TOKEN = (r'(?:[0-9a-fA-F]{4}:[0-9a-fA-F]{4}'      # segment:offset
              r'|(?:DS|CS|ES|SS):\$[0-9a-fA-F]{2,4}'   # a segmented address
              r'|\[BP[-+]\$?[0-9A-Fa-f]{1,4}h?\])')     # a frame slot
# **THE PREFIX ENDS WHERE THE CITATIONS DO**, and this is a SCAN rather than a
# regex on purpose. A run of sites may be joined by a comma, a slash, a range or
# the word `and`, and expressing "a run of those, then prose" as one pattern
# needs a quantifier inside a lookahead. Written that way it did not merely
# mis-match: on this corpus it hung, because the optional halves of the span
# backtrack against each other. Three separate leaks came from trying:
#
#     `{ .. 116a:0010 }`      a range read as a prefix and a note
#     `{ / 1b24:02f0 }`       a slash-joined pair, the first taken
#     `{ and DS:$0c18. ... }` an `and`-joined pair, likewise
#
# One cause, and every one of them found by reading the stripped copy rather
# than by anything failing.
# NO `^` ON EITHER OF THESE: `.match(s, pos)` already anchors at pos, and a
# `^` in the pattern goes on meaning the START OF THE STRING -- so the
# continuation never matched and every run stopped after its first citation,
# which is the very thing the scan was written to fix.
CITE = re.compile(r'[ \t]*%s' % SITE_TOKEN)
BARE_RANGE = re.compile(r'[ \t]*[0-9a-fA-F]{4}[ \t]*\.\.[ \t]*[0-9a-fA-F]{4}')
TAIL = re.compile(r'[0-9a-fA-F]{4}')
# `->` joins a run here too, and it is safe: the scan only advances past a
# joiner when a CITATION follows it, so `{ 1b24:003a -> AND AL,0FBh }` still
# stops at the arrow and keeps the note, exactly as the docstring promises.
JOIN = re.compile(r'(?:[ \t]*(?:->|[,/])[ \t]*|[ \t]*\.\.[ \t]*'
                  r'|[ \t]+and[ \t]+|[ \t]+)')


def cite_run(text):
    """How much of `text` is a leading run of citations, and nothing else.

    Returns the offset where the prose starts, or 0 if the line does not open
    with a citation at all. A trailing stop or comma goes with the run: a
    citation may be punctuated, as in `{ 1880:0077. Returns ... }`.
    """
    m = CITE.match(text)
    if m is None:
        # **A BARE RANGE OPENS A CITATION; A BARE OFFSET DOES NOT.**
        # `{ 005b..0076.  RETF 2.  Hand-written ... }` cites a span inside the
        # unit's own segment, where naming the segment every time would be
        # noise. Two bare offsets joined by dots can only be that. ONE bare
        # offset stays refused, because `{ 0000 RETF 6 }` is a routine-table
        # row where the number identifies the entry.
        m = BARE_RANGE.match(text)
    if not m:
        return 0
    end = m.end()
    while True:
        j = JOIN.match(text, end)
        if not j:
            break
        m = CITE.match(text, j.end())
        if m is None and text[end:j.end()].strip() == '..':
            # **A BARE OFFSET IS A CITATION DIRECTLY AFTER A RANGE DOT**, and
            # nowhere else. `154d:0000..04e1` names one span in the compact
            # form, and refusing the tail leaves the whole thing untrimmed.
            # Anywhere else four hex digits might be a row label or a length,
            # which is why they are never taken on their own.
            m = TAIL.match(text, j.end())
        if not m:
            break
        end = m.end()
    if end < len(text) and text[end] in '.,':
        end += 1
    rest = text[end:]
    if not rest.strip():          # nothing but citations: the dropper's job
        return 0
    if not rest[:1].isspace():    # `1642:0004abc` is not a prefix
        return 0
    return len(text) - len(rest.lstrip(' \t'))


# **PASCAL HAS TWO COMMENT FORMS AND THE SECOND ONE IS WHERE THE DANGEROUS
# PROSE LIVES.** `{ }` and `(* *)` are both comments and neither nests in the
# other, so a corpus uses `(* *)` for exactly one reason: it is the only way to
# WRITE a compiler directive inside prose. `(* 286 CODE ON. this unit had no
# {$G+} ... *)` is a sentence; the same words inside braces would end the
# comment at the directive's own closing brace.
#
# So the form is not a style choice, it is a workaround -- and it clusters
# around directives, which are the highest-risk comments in any reconstruction.
# Knowing only `{ }` meant a paragraph in `(* *)` could not be tagged (the tag
# was never read), could not be stripped, and was invisible to the checker that
# counts what leaks. Measured on the corpus that found it: 18 blocks, 75
# paragraphs, **16 carrying apparatus**, and 5 directives written inside them.
COMMENT = re.compile(r'\{[^{}]*\}|\(\*.*?\*\)')
COMMENT_ALL = re.compile(r'\{[^{}]*\}|\(\*.*?\*\)', re.S)

# The only extensions whose comment grammar this tool knows. Everything else in
# the tree is carried across byte for byte -- see the docstring.
SOURCE = ('.PAS', '.ASM', '.INC')


def delims(hit):
    """(opener, body, closer) for whichever comment form this is."""
    if hit[:1] == '{':
        return '{', hit[1:-1], '}'
    return '(*', hit[2:-2], '*)'


def is_asm(path, text=None):
    """Is this an ASSEMBLER source? Decided by CONTENT where the suffix cannot.

    `.INC` says nothing about grammar. In one corpus `COSTAB.INC` is TASM while
    `BLITCLIP.INC`, `SETPAL.INC` and `SETRGB.INC` are Pascal includes -- and
    taking all four for assembler applied the `;`-run paragraph grain to Pascal,
    where `;` ends a statement. That reported **0 problems over three files full
    of apparatus**, which is the shape of a check that cannot fail.

    So: `.ASM` is assembler and `.PAS` is not, both by definition; an `.INC` is
    read, and the first line that is not blank decides. An assembler file opens
    with a `;` banner, a Pascal one with `{` or `(*` or code.
    """
    suffix = pathlib.Path(path).suffix.upper()
    if suffix == '.ASM':
        return True
    if suffix != '.INC':
        return False
    if text is None:
        text = io.open(path, encoding='utf-8', errors='replace').read()
    for line in text.split('\n'):
        if line.strip():
            return line.lstrip().startswith(';')
    return False


# **THE TAGS.** A paragraph opening `[re]` is apparatus and is stripped; one
# opening `[reading]` is a claim resting only on someone's reading of the
# instructions and is KEPT, so a reader can tell the author's fact from an
# inference at a glance and so the inferences can be counted. `[1.39b]` is the
# release's own words and predates both.
RE_TAG = re.compile(r'^\s*\[re\]\s*', re.I)

# Stands in for a comment removed whole, until the line pass decides whether
# the LINE goes with it. Not a character any DOS source contains.
GONE = '\x00'


def drop_tagged_pascal(text):
    """Remove `[re]` paragraphs from every { } comment. Returns (text, n).

    THE GRAIN IS THE BLANK LINE, which is how these comments are already
    written -- 499 of the tangled ones are multi-paragraph. Working per
    paragraph means a comment that is half evidence and half explanation does
    not have to be split in two first, and the 2,121 comments carrying no
    apparatus at all are never touched.
    """
    n = 0

    def one(m):
        nonlocal n
        op, body, cl = delims(m.group(0))
        paras = re.split(r'\n[ \t]*\n', body)
        # **A TAGGED PARAGRAPH CARRIES ITS CONTINUATIONS**, which are the
        # blocks indented under it -- a frame layout, a table, a quoted
        # listing. They are separate paragraphs by the blank-line rule and
        # belong to the tag by the indentation, and the first pilot unit
        # leaked exactly this: the tag went on the prose and the indented
        # table under it stayed behind, alone and unexplained.
        keep, drop_to = [], None
        for q in paras:
            lead = len(q) - len(q.lstrip(' '))
            if RE_TAG.match(q):
                drop_to = lead
                continue
            if drop_to is not None and q.strip() and lead > drop_to:
                continue
            drop_to = None
            keep.append(q)
        n += len(paras) - len(keep)
        if not keep or not ''.join(keep).strip():
            # **NOTHING BUT APPARATUS: THE COMMENT GOES, AND SO DO ITS LINES.**
            # A sentinel rather than an empty string, because a comment that
            # occupied whole lines otherwise leaves them behind as blanks --
            # and a routine header then floats a blank line above its own
            # declaration, everywhere a marker was stripped. The line pass in
            # `clean_text` removes any line that is nothing but sentinels and
            # strips the rest, which is the only way to tell a line this tool
            # emptied from a blank line somebody wrote.
            return GONE
        if len(keep) == len(paras):
            return m.group(0)
        out = '\n\n'.join(keep)
        if out.lstrip()[:1] == '$':  # `{$` is a DIRECTIVE, not a comment
            out = ' ' + out.lstrip()
        # A CLOSER SHOULD NOT SIT AGAINST A WORD. Where the tagged paragraph was
        # the comment's LAST, the delimiter it used to stand clear of comes back
        # hard against the final full stop -- `...closing brace.*)`. The
        # original spaced it; keeping that costs one character and the stripped
        # copy is prose somebody reads.
        if out[-1:] not in ('', ' ', '\t', '\n'):
            out += ' '
        return op + out + cl

    return COMMENT_ALL.sub(one, text), n


def drop_tagged_asm(text):
    """Remove runs of `; [re] ...` lines. Returns (text, n).

    A .ASM file has no blank-line paragraphs inside a comment, so the tag sits
    after the `;` and a run of consecutive comment lines goes together: the
    continuation lines of one tagged note carry no tag of their own. A line
    holding code with a trailing comment is never dropped -- only whole
    comment lines.

    **AND THE SEPARATOR THE RUN SAT BETWEEN GOES WITH IT.** A bare `;` ends a
    paragraph, so a tagged one is normally fenced by two of them -- drop the
    run and the fences meet, leaving `;` followed by `;` in the stripped copy.
    This is the assembler's version of the blank line a removed `{ }` comment
    used to leave behind, and it matters for the same reason: the stripped copy
    IS the product, and a column of doubled separators is visible noise in it.

    Only an adjacency this pass CREATED is collapsed -- the previous emitted
    line being a bare `;` and a drop having just ended. Two separators somebody
    wrote deliberately are left alone.
    """
    out, n, dropping, just_dropped = [], 0, False, False
    for line in text.split('\n'):
        s = line.strip()
        if s.startswith(';'):
            after = s[1:].lstrip()
            if RE_TAG.match(after):
                dropping, n, just_dropped = True, n + 1, True
                continue
            if dropping and after and not after.startswith('['):
                n += 1                      # continuation of the tagged note
                continue
        if (just_dropped and s == ';' and out and out[-1].strip() == ';'):
            # THE RUN ENDS HERE, and saying so is not optional: an earlier
            # version skipped this line without clearing `dropping`, so the run
            # went on eating the NEXT paragraph -- two paragraphs of real
            # documentation, removed silently. The self-check cannot see it,
            # because only comments changed. Reading the stripped copy is what
            # caught it, for the third time in this effort.
            dropping, just_dropped = False, False
            continue
        dropping, just_dropped = False, False
        out.append(line)
    return '\n'.join(out), n


def asm_comment_at(line):
    """Where the `;` comment starts on an assembler line, or -1.

    Quote-aware, because `DB 'a;b'` is not a comment and blanking from that
    semicolon would delete a string's second half from the stripped copy while
    the self-check -- which blanks comments in BOTH copies -- stayed happy.
    """
    quote = None
    for k, ch in enumerate(line):
        if quote:
            if ch == quote:
                quote = None
        elif ch in '"\'':
            quote = ch
        elif ch == ';':
            return k
    return -1


def clean_asm_addresses(text):
    """Apply the address rules to `;` comments. Returns (text, dropped, trimmed).

    **THE TAG CANNOT REACH THESE, WHICH IS WHY THE PASS EXISTS.** A tag drops
    whole comment LINES, deliberately -- a line of code with a trailing note is
    never removed, or a stripper would delete code. But hand-written assembler
    documents itself per instruction, and in a reconstruction that means a
    column of addresses:

        push    bp                      ; 1102:0391
        mov     eax,[bp+08h]            ; 1102:0394  A

    Twenty-six of those in one file, none of them taggable and every one of
    them apparatus. Without this pass they stay in the stripped copy for good
    and the tree-wide count can never reach zero, which is the destination.

    The rules are the ones already used on `{ }`: a comment that is nothing but
    addresses goes with its trailing whitespace, and a leading run of citations
    is trimmed off a comment that also says something. Nothing else is touched.
    """
    dropped = trimmed = 0
    out = []
    for line in text.split('\n'):
        k = asm_comment_at(line)
        if k < 0:
            out.append(line)
            continue
        code, body = line[:k], line[k + 1:]
        if not code.strip():          # a whole comment line: the tag's job
            out.append(line)
            continue
        if ONLY.match(body) or BYTES.match(body):
            dropped += 1
            out.append(code.rstrip())
            continue
        cut = LEAD.sub('', body)
        run = cite_run(cut)
        if run:
            cut = ' ' + cut[run:]
        if cut != body:
            # **AND WHAT IS LEFT MAY ITSELF BE THE IMAGE QUOTED BACK.**
            # `; 12C5:0ADC  F3 66 A5` trims to ` F3 66 A5`, which is the
            # instruction's own encoding beside the instruction -- the same
            # thing twice, once in a base the reader did not ask for. The
            # Pascal side gets this for free by running its trim and its drop
            # as two passes over the text; this one does both in a single walk,
            # so it has to look again.
            if BYTES.match(cut):
                dropped += 1
                out.append(code.rstrip())
                continue
            trimmed += 1
            out.append(code + ';' + cut.rstrip())
            continue
        out.append(line)
    return '\n'.join(out), dropped, trimmed


def clean_text(text, asm=False):
    """Return (text, dropped, trimmed) with the apparatus removed.

    TWO PASSES, AND THE SPLIT IS THE SAFETY. Prefix trimming runs over the whole
    text so it reaches a block comment spanning twenty lines; DROPPING runs line
    by line, so it can only ever remove a comment that sits alone on its line.
    A dropper allowed to match across lines would delete a paragraph the moment
    its first line looked like an address.
    """
    dropped = trimmed = 0
    # THE TAG PASS RUNS FIRST, and it is the one that answers the ask:
    # apparatus is what a person MARKED, not what a pattern guessed.
    # The address dropper below survives as a complement -- it clears
    # the pure citations for free, three quarters of them, and leaves
    # the tangled prose to the tags.
    text, tagged = (drop_tagged_asm(text) if asm
                    else drop_tagged_pascal(text))

    # THE SAME ADDRESS RULES, ON THE OTHER COMMENT SYNTAX. The brace passes
    # below cannot see a `;` comment, so an assembler file's per-instruction
    # address column survived every one of them.
    if asm:
        text, d, t = clean_asm_addresses(text)
        dropped += d
        trimmed += t

    def prefix(m):
        nonlocal trimmed
        op, body, cl = delims(m.group(0))
        # **THE QUOTE IS PROTECTED; THE CITATION IN FRONT OF IT IS NOT.** This
        # used to refuse the whole comment whenever it mentioned the release,
        # which shielded `{ 1723:03cf  [1.39b] "Reset the GF1" }` -- address and
        # all -- from a trim that would only ever have taken the address. The
        # trims below reach a LEADING run of citations and nothing else, so
        # they cannot touch the author's words wherever those words sit.
        #
        # Dropping a whole comment is different, and that still refuses: see
        # `one` below, where a quoted comment is never removed entirely.
        # A single space, not nothing: the opening brace would otherwise sit
        # against the first word.
        cut = LEAD.sub('', body)
        cut = '\n'.join((' ' + ln[cite_run(ln):]) if cite_run(ln) else ln
                        for ln in cut.split('\n'))
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
            # Any non-space start, not just `$`: trimming a prefix off
            # `{ 188f:0003  [BP+06h] -- Ofs(P) }` leaves `{Ofs(P)`, which reads
            # as a typo. `$` additionally MUST have the space, because `{$` is
            # a compiler directive rather than a comment at all.
            if cut[:1] not in ('', ' ', '\t', '\n'):
                cut = ' ' + cut
            trimmed += 1
            return op + cut + cl
        return m.group(0)

    text = COMMENT_ALL.sub(prefix, text)

    def one(m):
        nonlocal dropped, trimmed
        body = delims(m.group(0))[1]
        if '1.39b' in body:                  # the author's words: never touched
            return m.group(0)
        if ONLY.match(body) or BYTES.match(body):
            dropped += 1
            return ''
        return m.group(0)

    out = []
    for line in text.split('\n'):
        if GONE in line:
            # A line that held nothing but a removed comment goes entirely;
            # one that also held code keeps the code and loses the gap.
            if not line.replace(GONE, '').strip():
                continue
            line = line.replace(GONE, '').rstrip()
        new = COMMENT.sub(one, line)
        # A line that held nothing but its comment goes with it; a line of code
        # keeps its indentation and loses the trailing blank.
        if new.strip() or not line.strip():
            out.append(new.rstrip() if new != line else line)
        elif not line.strip():
            out.append(line)
    # Dropping a trailing comment leaves behind the whitespace that
    # separated it from the code. Nothing in Pascal reads it, and a file
    # meant to be read should not carry it.
    return '\n'.join(q.rstrip() for q in out), dropped, trimmed, tagged


def survivors(text):
    """Comments still mentioning an address -- the worklist a person needs."""
    hits = []
    for n, line in enumerate(text.split('\n'), 1):
        for m in COMMENT.finditer(line):
            body = ' '.join(delims(m.group(0))[1].split())
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
    # `--exclude` TAKES A VALUE, so the positionals cannot be sieved out of
    # argv by their leading dashes alone: the pattern that follows it would be
    # read as the destination directory, and two sources with an odd name is
    # not a mistake this should make quietly.
    args, skip, rest = [], [], list(argv)
    while rest:
        a = rest.pop(0)
        if a == '--exclude':
            if not rest:
                raise SystemExit("--exclude needs a path, relative to the "
                                 "source root")
            skip.append(rest.pop(0))
        elif a.startswith('--exclude='):
            skip.append(a.split('=', 1)[1])
        elif not a.startswith('--'):
            args.append(a)
    if len(args) != 2:
        raise SystemExit(__doc__)
    src, dst = pathlib.Path(args[0]), pathlib.Path(args[1])
    dry, report = '--dry' in argv, '--report' in argv
    for pat in skip:
        if pathlib.PurePosixPath(pat).suffix.upper() in SOURCE:
            raise SystemExit(
                "--exclude %s names a source file, which this refuses: the "
                "stripped copy exists to carry those and the build needs "
                "every one." % pat)

    if not dry:
        dst.mkdir(parents=True, exist_ok=True)

    files = drop = trim = left = tags = copied = excluded = 0
    written = set()
    for f in sorted(src.rglob('*')):
        if not f.is_file():
            continue
        rel = f.relative_to(src)
        if any(fnmatch.fnmatch(rel.as_posix(), pat) for pat in skip):
            # Reported, not merely absent: a reader of the run sees the
            # decision rather than having to notice a gap.
            excluded += 1
            print("%-24s excluded" % rel.as_posix())
            continue
        written.add(rel)
        out = dst / rel
        if not dry:
            out.parent.mkdir(parents=True, exist_ok=True)
        # A file whose comment grammar this tool does not know is carried
        # across untouched -- bytes, so neither its encoding nor its line
        # endings are this tool's to decide.
        if f.suffix.upper() not in SOURCE:
            copied += 1
            print("%-24s carried across verbatim" % rel.as_posix())
            if not dry:
                out.write_bytes(f.read_bytes())
            continue
        raw = io.open(f, encoding='utf-8', errors='replace', newline='').read()
        text = raw.replace('\r\n', '\n')
        # WHAT THIS FILE HAD IS WHAT IT GETS BACK. Decided per file: a tree may
        # legitimately hold both, and a tool that normalises rewrites the lot.
        crlf = '\r\n' in raw
        asm = is_asm(f, text)
        new, d, t, g = clean_text(text, asm=asm)
        rest = survivors(new)
        files += 1
        drop += d
        trim += t
        tags += g
        left += len(rest)
        print("%-24s tagged %4d  dropped %4d  trimmed %3d  addressed %3d"
              % (rel.as_posix(), g, d, t, len(rest)))
        if report:
            for n, body in rest[:8]:
                print("      %5d  %s" % (n, body))
        if code_only(text, asm) != code_only(new, asm):
            before, after = code_only(text, asm), code_only(new, asm)
            for x, y in zip(before, after):
                if x != y:
                    raise SystemExit(
                        "%s: THE CODE CHANGED, which this must never do.\n"
                        "  was : %s\n  now : %s"
                        % (rel.as_posix(), x[:78], y[:78]))
            raise SystemExit("%s: the code changed length, %d -> %d"
                             % (rel.as_posix(), len(before), len(after)))

        if not dry:
            io.open(out, 'w', encoding='utf-8', newline='').write(
                new.replace('\n', '\r\n') if crlf else new)

    print()
    print("%d file(s): %d [re] paragraph(s) removed, %d address-only\n         comment(s) dropped, %d prefix(es) trimmed"
          % (files, tags, drop, trim))
    print("%d comment(s) still mention an address -- those need a person" % left)
    print("%d file(s) carried across verbatim, %d excluded" % (copied, excluded))
    print("every file verified: not one line of code differs")

    if not dry and dst.exists():
        kept = [q.relative_to(dst).as_posix() for q in sorted(dst.rglob('*'))
                if q.is_file() and q.relative_to(dst) not in written]
        if kept:
            print("kept, not generated by this tool: %s" % ", ".join(kept))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
