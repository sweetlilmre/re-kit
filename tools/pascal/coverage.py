"""How much of a target is accounted for, computed from the tree rather than recited.

    python kit/tools/pascal/coverage.py LINK.toml UNITS.toml

WHAT IT ADDS to the per-unit table it reads: that table says how far each unit
agrees and says nothing about the segments NOBODY HAS STARTED. This is the
complement -- every byte the original has against every byte accounted for -- so
a segment absent from the unit config shows up as untranscribed rather than as
silence.

IT PARSES ANOTHER TOOL'S PRINTED OUTPUT, which is fragile by nature: the row
shape is the contract and nothing enforces it. That is inherited, and worth
fixing the day the per-unit instrument grows a machine-readable mode.
"""
import io, re, subprocess, sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import project                                    # noqa: E402

try:
    import tomllib
except ModuleNotFoundError:                       # pragma: no cover -- 3.11+
    import tomli as tomllib                       # type: ignore

args = project.positionals(sys.argv[1:], ("--part",))
PART = project.option(sys.argv[1:], "part")
if len(args) < 2:
    sys.stdout.write("usage: coverage.py LINK.toml UNITS.toml [--part NNN]"
                     + chr(10))
    raise SystemExit(2)

ROOT = pathlib.Path(args[0]).resolve().parent
while not (ROOT / 'kit.toml').exists() and ROOT != ROOT.parent:
    ROOT = ROOT.parent

with io.open(args[0], 'rb') as fh:
    LINK = tomllib.load(fh)

# ONE PART'S LAYOUT, not `the` layout. Everything segment-keyed below --
# the order, the program's own segment, the data-only segments, the block
# config -- describes ONE part, and a target with nine parts has nine
# answers for each. `layout`, `lists` and `unitname` stay top-level: a
# document path, the runtime's unit names and an abbreviation do not
# change from one part to the next.
try:
    SPEC = project.layout(LINK, PART)
except project.Missing as exc:
    raise SystemExit(project.complain(exc) and 2)

# every segment and its size, from the layout document -- authoritative on it
# THE DENOMINATOR IS A DOCUMENT, and this said KeyError when a project had
# not written one -- in one consumer the key was absent, in another it named
# a file that did not exist. Both are "this project cannot be measured yet",
# which is an answer, and a traceback is not a way to give it.
named = LINK.get('layout')
if not named:
    raise SystemExit(
        "  %s does not say `layout` -- the document listing every segment"
        " and its size, which is this measurement's denominator. Without"
        " it there is no total to be a fraction of." % args[0])
doc = ROOT / named
if not doc.is_file():
    raise SystemExit(
        "  %s names `layout` = %s, and no such file exists. The"
        " denominator has to be read from somewhere." % (args[0], named))
txt = doc.read_text(encoding='utf-8', errors='replace')
seg = {int(m.group(1), 16): int(m.group(2))
       for m in re.finditer(r'^\| `([0-9a-f]{4})` \| (\d+) \|', txt, re.M)}

# The runtime's own segments, JOINED from the one segment list rather than kept
# as a second copy keyed the other way round. A second copy of this very
# measurement is what had drifted between two other instruments; see link.toml.
_rtl = {n.upper() for n in LINK['lists']['rtl']}
RTL = {seg: name.title() for seg, name in project.segments(SPEC)
       if name.upper() in _rtl}
DATA = {d['segment']: d['why'] for d in SPEC.get('data', ())}

# what verify.py reports, parsed from its own output
# The per-unit table comes from the kit's instrument now. This still
# parses another tool's printed output, which is fragile by nature -- the row
# shape is the contract and nothing enforces it. Moving this into the kit is
# where that gets fixed; until then the parse is unchanged and so is the answer.
out = subprocess.run([sys.executable,
                      str(pathlib.Path(__file__).resolve().parent / 'units.py'),
                      args[1]],
                     capture_output=True, text=True,
                     encoding='utf-8', cwd=str(ROOT)).stdout
done, partial = {}, {}
for line in out.splitlines():
    m = re.match(r'^(\w+)\s+([0-9a-f]{4})\s+(\d+)\s+(.*)$', line)
    if not m:
        continue
    name, s, size, res = m.group(1), int(m.group(2), 16), int(m.group(3)), m.group(4)
    if res.startswith('IDENTICAL') or res.startswith('identical'):
        done[s] = (name, size)
    else:
        p = re.search(r'agrees to \+([0-9a-f]+)', res)
        if p:
            partial[s] = (name, int(p.group(1), 16))

in_scope = {k: v for k, v in seg.items() if k not in RTL and k not in DATA}
total = sum(in_scope.values())
done_bytes = sum(sz for _, sz in done.values())
part_bytes = sum(n for _, n in partial.values())

print("IN SCOPE: %d segments, %d bytes" % (len(in_scope), total))
print("  excluded: %s (Borland RTL, %d bytes), %s (%d bytes)"
      % (', '.join('%04x' % k for k in RTL), sum(seg[k] for k in RTL),
         ', '.join('%04x' % k for k in DATA),
         sum(seg[k] for k in DATA if k in seg)))
print()
print("COMPLETE  %2d unit(s)  %6d bytes" % (len(done), done_bytes))
print("PARTIAL   %2d unit(s)  %6d bytes" % (len(partial), part_bytes))
for s, (n, b) in sorted(partial.items()):
    print("             %-9s %04x  %d of %d (%d%%)"
          % (n, s, b, seg[s], 100 * b // seg[s]))
print()
covered = done_bytes + part_bytes
print("COVERED   %6d of %d bytes  = %.1f%%" % (covered, total, 100.0 * covered / total))
print()
untouched = {k: v for k, v in in_scope.items() if k not in done and k not in partial}

# 1000 IS THE PROGRAM, so it compiles into the .EXE rather than to a .TPU and
# verify.py -- which compares a .TPU's code against a segment -- has nothing to
# list it as. It is measured by `progcmp.py` instead, and that number is asked
# for here rather than assumed, so this total is the whole program.
# THE PROGRAM SEGMENT IS NAMED, not taken as segments[0]. Position meant
# `the program` only because one target happens to link its program
# first, and the segment list does not have to contain it at all -- in a
# nine-part target it is deliberately absent, because it emits no unit and
# another instrument measures it. Read positionally there, this named a
# real unit segment as the program, popped it out of NOT STARTED and
# measured it with the wrong tool, and every printed total stayed
# plausible.
PROGRAM_SEG = SPEC.get('program_seg')
if PROGRAM_SEG is None:
    raise SystemExit(
        "  this part does not say `program_seg` -- the segment its program"
        " compiles into. It used to be read as the FIRST entry of the"
        " segment list, which is only the program by coincidence of link"
        " order, and is not in that list at all when another instrument"
        " measures it.")
prog = untouched.pop(PROGRAM_SEG, None)
if prog is not None:
    # THE PROGRAM IS MEASURED BLOCK BY BLOCK, not by prefix: it is the one
    # segment the per-unit table has nothing to say about, because a program
    # emits no .TPU.
    #
    # THIS WAS SILENTLY READING ZERO. It shelled out to progcmp.py, which a migration
    # archived in favour of blockcmp with a config -- and the parse simply found
    # no match, so `n` fell back to 0 and the program's verified bytes dropped
    # out of the total with nothing said. A regex that returns None on a missing
    # tool is indistinguishable from a tool that measured nothing. It refuses
    # now.
    blocks = SPEC.get('program_blocks')
    if not blocks:
        raise SystemExit("  %s does not say `program_blocks` -- the program's "
                         "own block config is needed to measure it" % args[0])
    got = subprocess.run([sys.executable,
                          str(pathlib.Path(__file__).resolve().parent
                              / 'blockcmp.py'), blocks],
                         capture_output=True, text=True,
                         encoding='utf-8', cwd=str(ROOT))
    m = re.search(r'(\d+) of (\d+) byte\(s\) of segment ([0-9a-f]+) transcribed',
                  got.stdout)
    if not m:
        raise SystemExit("  could not read a transcribed count out of "
                         "blockcmp %s:%s%s" % (blocks, chr(10), got.stdout
                                               or got.stderr))
    n = int(m.group(1))
    print("THE PROGRAM: %04x, %d bytes in the segment -- %d verified block by block"
          % (PROGRAM_SEG, prog, n))
    covered += n
    print()
    print("COVERED, WITH THE PROGRAM  %6d of %d bytes  = %.1f%%"
          % (covered, total, 100.0 * covered / total))
    print()
if untouched:
    print("NOT STARTED: %d segments, %d bytes" % (len(untouched), sum(untouched.values())))
    for k in sorted(untouched, key=lambda x: -untouched[x]):
        print("   %04x  %5d" % (k, untouched[k]))
else:
    print("NOT STARTED: none. Every segment is transcribed.")
