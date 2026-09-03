r"""Which bytes of an original do NOT line up against our build, and where.

    python kit/tools/pascal/spans.py SPANS.toml
    python kit/tools/pascal/spans.py SPANS.toml 001
    python kit/tools/pascal/spans.py SPANS.toml 001 --same
    python kit/tools/pascal/spans.py SPANS.toml --min=32

THE COMPLEMENT OF THE PER-ROUTINE CHECK, and the reason both exist: that check
answers "does each routine I declared match?", so a routine nobody declared is
not a failure in its scheme -- it is not a row at all. This walks EVERY byte of
every user segment and reports the spans that cannot be aligned, so absence has
somewhere to appear. See the wiki observation `Every declared routine matches,
and the rebuild still behaves differently`.

The engine has held `align.spans()` since the compare tools were consolidated;
what was missing was a way to RUN it, and an equivalent of `--same`. That gap is
why the script this replaces survived two rounds of deletion.

**AN UNALIGNED SPAN IS NOT PROOF OF LOST ASSEMBLER.** It is one of two things,
and the tool cannot tell them apart:

  * hand assembler re-expressed as Pascal -- the class a declaration-driven
    check cannot see, because an inline block inside a compiled routine has no
    prologue of its own; or
  * compiled code with a different statement shape or different locals, which
    may be behaviourally right and is where a pacing gap hides.

So a span says WHERE to look, never what you will find. Two spans of the same
length in one part were, on one run, one lost hand-written routine and one
deliberate deviation.

`--same` ASKS WHETHER THE CODE IS ALREADY SOMEWHERE ELSE. A span that turns up
inside another built harness is code that WAS transcribed, in another unit --
which changes the job from "write this" to "share what exists". Our own harness
is skipped: by construction the span did not align there.

WHICH ORIGINAL TO MEASURE AGAINST IS A DIFFERENT ANSWER HERE, and getting it
wrong is quiet. A per-routine check may compare against a trap-rewritten copy so
x87 sites read as tolerated holes; a coverage walk must use the SHIPPED bytes,
because our build carries the traps exactly as the release does and the rewritten
copy would show a two-byte hole at every FPU op and drown an x87-heavy region in
noise. Hence a separate key: `target.release`, not `target.original`.
"""
import io
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[0]))
import project                                    # noqa: E402
import routines                                   # noqa: E402
from substrate import align                       # noqa: E402

try:
    import tomllib
except ModuleNotFoundError:                       # pragma: no cover -- 3.11+
    import tomli as tomllib                       # type: ignore

MIN_SPAN = 16
# A span found in another harness has to be long enough that the match is the
# code and not a coincidence of prologues.
ELSEWHERE = 24


def elsewhere(chunk, own_exe, images):
    """Which OTHER built harness already contains this original code.

    (image name, bytes that line up) or (None, 0). Our own harness is skipped:
    the span did not align there by construction, and a partial hit inside it is
    the divergence already being reported.
    """
    others = [(n, b) for n, b in images if n != own_exe]
    best = (None, 0)
    for name, image in others:
        at, _ = align.locate(image and chunk, image, align.holes, None)
        if at < 0:
            continue
        got, _, _ = align.walk(chunk, image[at:at + len(chunk)],
                               align.holes, None)
        if got > best[1]:
            best = (name, got)
    return best if best[1] >= ELSEWHERE else (None, 0)


def part_report(part, spec, blob, ours, images, min_span, same):
    hdr = int.from_bytes(blob[8:10], "little") * 16
    first = project.get("target.first_para", quiet=True)
    bounds = project.seg_bounds(spec)
    total = matched_total = 0
    found = []
    for k, seg in enumerate(project.seg_addrs(spec)):
        base = hdr + (seg - first) * 16
        size = (bounds[k + 1] - seg) * 16
        data = blob[base:base + size]
        total += size
        pos, gap_start, after = 0, None, -1
        while pos < len(data):
            chunk = data[pos:pos + align.WINDOW]
            if len(chunk) < align.ANCHOR:
                # THE TAIL, AND IT USED TO BE THROWN AWAY. A run shorter than
                # ANCHOR cannot be searched for -- there is nothing to anchor on
                # -- and this loop used to `break` here, so the last nine bytes
                # of EVERY segment were neither counted as matched nor reported
                # as a gap. That is exactly where a unit's initialisation section
                # sits, and four parts of the first target were hiding real
                # defects there while the walk read 100.0%: a missing five-byte
                # init section, a redundant store inside another one, and two
                # units whose code ran past where the original's stopped.
                #
                # It does not need searching. The previous window aligned, so we
                # already know where in the rebuild the next byte belongs --
                # compare from there, with the same allowances.
                got = 0
                if after >= 0:
                    got, _, _ = align.walk(chunk, ours[after:after + len(chunk)],
                                           align.holes, None)
                if got:
                    if gap_start is not None:
                        found.append((seg, gap_start, pos))
                        gap_start = None
                    matched_total += got
                if got < len(chunk) and gap_start is None:
                    gap_start = pos + got
                pos = len(data)
                break
            at, got = align.locate(chunk, ours, align.holes, None)
            if got >= align.MINIMUM and at >= 0:
                if gap_start is not None:
                    found.append((seg, gap_start, pos))
                    gap_start = None
                matched_total += got
                pos += got
                after = at + got
            else:
                if gap_start is None:
                    gap_start = pos
                pos += 1
                after = -1
        if gap_start is not None:
            found.append((seg, gap_start, len(data)))

    print("part %s vs %s: %d of %d segment byte(s) aligned (%.1f%%)"
          % (part, spec["exe"], matched_total, total,
             100.0 * matched_total / max(1, total)))
    shown = 0
    for seg, a, b in sorted(found, key=lambda s: s[1] - s[2]):
        if b - a < min_span:
            continue
        note = ""
        if same:
            base = hdr + (seg - first) * 16
            chunk = blob[base + a:base + min(b, a + align.WINDOW)]
            where, got = elsewhere(chunk, spec["exe"], images)
            if where:
                note = "  -- %d byte(s) of it are already in %s" % (got, where)
        print("  %04x:%04x..%04x  %5d byte(s) unaligned%s"
              % (seg, a, b, b - a, note))
        shown += 1
    if not shown:
        print("  no unaligned span >= %d bytes" % min_span)


def main(argv):
    args = [a for a in argv if not a.startswith("-")]
    if not args:
        sys.stdout.write("usage: spans.py SPANS.toml [PART...] [--same] "
                         "[--min=N]" + "\n")
        return 2
    with io.open(args[0], "rb") as fh:
        cfg = tomllib.load(fh)
    same = "--same" in argv
    min_span = cfg.get("min_span", MIN_SPAN)
    for a in argv:
        if a.startswith("--min="):
            min_span = int(a.split("=")[1])

    try:
        root = project.find()
        release = project.get("target.release")
        built = root / project.get("layout.built")
    except project.Missing as exc:
        return project.complain(exc)

    parts = args[1:] or sorted(cfg["part"])
    images = routines.built(quiet=True)
    for p in parts:
        spec = cfg["part"].get(p)
        if spec is None:
            print("no segments recorded for part %s" % p)
            continue
        if p not in release:
            print("part %s has no release binary in the answers file" % p)
            continue
        blob = (root / release[p]).read_bytes()
        ours = (built / spec["exe"]).read_bytes()
        part_report(p, spec, blob, ours, images, min_span, same)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
