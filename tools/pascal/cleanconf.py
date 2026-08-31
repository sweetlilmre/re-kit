"""Write a build config for the STRIPPED source tree, from the real one.

    python kit/tools/pascal/cleanconf.py build.toml cleanbuild.toml --src src-clean
    python kit/tools/pascal/cleanconf.py build.toml cleanbuild.toml --src src-clean \\
        --build build-clean
    python kit/tools/pascal/cleanconf.py build.toml cleanbuild.toml --src src-clean --check

WHY THIS IS NOT A COPY. The documentation transform needs a second build --
the stripped tree must compile to the same bytes, and building it is the ONLY
check that sees a comment edit which landed on a compiler directive. That
second build wants the same config with the source directory changed.

Changing it by hand is a trap with a name. A build config names its source
directory in MORE than one place: the top-level `src`, plus every staging path
that spells it out -- `[stage] alongside`, `verbatim`, `[stage.subdirs]`. Miss
one and the clean build **silently stages the ORIGINAL sources for that group
and passes**, which is the worst possible outcome: a green gate over a tree that
was never tested. Two corpora have that shape today and one of them missed a
path on the first attempt.

And a hand-made copy DRIFTS. The compiler switches, the link order and the
8.3 name map are measured facts with long notes attached; two copies of them go
out of step the first time one is corrected, and nothing compares them.

So this rewrites the real config, TEXTUALLY, keeping every comment exactly
where it was -- the notes are most of the value in such a file -- and then
refuses to write anything unless every remaining mention of the old directory
is inside a comment.

## What it rewrites, and nothing else

A quoted path in a VALUE position: `"src"` becomes `"src-clean"`, and any
`"src/..."` becomes `"src-clean/..."`. Comment lines are left alone, so a note
explaining why `src/asm` is staged as a folder still says `src/asm` and still
reads correctly -- it is describing the arrangement, not configuring it.

`--build` additionally renames the staging directory. Worth doing: two builds
sharing one staging directory means a clean build that REFUSED leaves the
previous build's staged sources in place, and the next thing to read them
cannot tell. Different directories make that visible instead.

## The guard is the point

`--check` regenerates and compares without writing, so a stale clean config is
a failing check rather than a thing somebody remembers to redo after editing the
real one. Run it in the gate: the two configs must never disagree about anything
but their paths.
"""

import io
import re
import sys
import pathlib

# A quoted value naming the source tree, in the two shapes a config uses: the
# bare directory and a path under it. Anchored on the quote so a bare word
# inside prose can never match.
#
# BOTH QUOTE CHARACTERS, and that is not tidiness. TOML has basic strings
# ("...") and literal strings ('...'), a config may use either, and a version of
# this that knew only about double quotes would fail to rewrite a
# single-quoted path AND fail to report it -- the exact shape of a check that
# cannot fail. Found by testing the guard rather than by reading it.
VALUE = (r'(?P<q>["\'])(?P<dir>%s)(?P<rest>/[^"\']*)?(?P=q)')


def rewrite(text, old, new, old_build=None, new_build=None):
    """Return (text, sites) with every quoted `old` path repointed at `new`.

    A comment line is never touched: its `src/asm` is describing the staging
    arrangement rather than setting it, and rewriting prose would make the
    notes lie about the tree they document.
    """
    pat = re.compile(VALUE % re.escape(old))
    bpat = (re.compile(VALUE % re.escape(old_build))
            if old_build else None)
    out, sites = [], 0

    for line in text.split('\n'):
        if line.lstrip().startswith('#'):
            out.append(line)
            continue

        def sub(m, to=new):
            q = m.group('q')
            return '%s%s%s%s' % (q, to, m.group('rest') or '', q)

        got = pat.sub(sub, line)
        if bpat is not None:
            got = bpat.sub(lambda m: sub(m, new_build), got)
        if got != line:
            sites += 1
        out.append(got)
    return '\n'.join(out), sites


def leaks(text, old):
    """Non-comment lines still naming `old` -- the defect this refuses to ship.

    THIS IS THE WHOLE GUARD. A missed staging path does not fail the build; it
    stages the original tree for that group and passes, so nothing downstream
    can tell. The only place to catch it is here, before the file exists.

    CASE-INSENSITIVE, WHERE THE REWRITE IS NOT, and the asymmetry is deliberate:
    these are DOS paths on a case-insensitive filesystem, so `"SRC/gen"` would
    stage the original tree perfectly happily. Rewriting it would be this tool
    guessing that a differently-spelled directory means the same one; REFUSING
    it hands a real ambiguity to a person. Rewrite conservatively, refuse loudly.
    """
    bad = []
    pat = re.compile(VALUE % re.escape(old), re.I)
    for n, line in enumerate(text.split('\n'), 1):
        if line.lstrip().startswith('#'):
            continue
        if pat.search(line):
            bad.append((n, line.strip()[:96]))
    return bad


def main(argv):
    args, opts, rest = [], {}, list(argv)
    while rest:
        a = rest.pop(0)
        if a in ('--src', '--build', '--old', '--old-build'):
            if not rest:
                raise SystemExit("%s needs a value" % a)
            opts[a.lstrip('-')] = rest.pop(0)
        elif not a.startswith('--'):
            args.append(a)
    if len(args) != 2 or 'src' not in opts:
        raise SystemExit(__doc__)

    real, clean = pathlib.Path(args[0]), pathlib.Path(args[1])
    old = opts.get('old', 'src')
    new = opts['src']
    old_build, new_build = opts.get('old-build', 'build'), opts.get('build')

    text = io.open(real, encoding='utf-8', newline='').read()
    crlf = '\r\n' in text
    body = text.replace('\r\n', '\n')

    got, sites = rewrite(body, old, new, old_build if new_build else None,
                         new_build)
    bad = leaks(got, old)
    if bad:
        print("%s still names '%s' in %d place(s) that are not comments:"
              % (clean.name, old, len(bad)))
        for n, line in bad:
            print("  %5d  %s" % (n, line))
        raise SystemExit(
            "refusing to write: a missed staging path does not fail a build, "
            "it stages the ORIGINAL sources for that group and passes.")

    banner = ("# GENERATED by kit/tools/pascal/cleanconf.py from %s -- DO NOT "
              "EDIT.\n#\n# Every fact here belongs to %s; this copy differs "
              "only in the paths that\n# name the source tree. Change %s and "
              "regenerate.\n#\n"
              % (real.name, real.name, real.name))
    got = banner + got

    if '--check' in argv:
        if not clean.exists():
            raise SystemExit("%s does not exist -- generate it first"
                             % clean.name)
        have = io.open(clean, encoding='utf-8', newline='').read()
        if have.replace('\r\n', '\n') != got:
            raise SystemExit(
                "%s is STALE: it differs from what %s generates now. "
                "Regenerate it." % (clean.name, real.name))
        print("%s matches %s: %d path(s) repointed at '%s'"
              % (clean.name, real.name, sites, new))
        return 0

    io.open(clean, 'w', encoding='utf-8', newline='').write(
        got.replace('\n', '\r\n') if crlf else got)
    print("%s written from %s: %d line(s) repointed, src '%s' -> '%s'%s"
          % (clean.name, real.name, sites, old, new,
             ", build '%s' -> '%s'" % (old_build, new_build)
             if new_build else ""))
    print("no non-comment line still names '%s'" % old)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
