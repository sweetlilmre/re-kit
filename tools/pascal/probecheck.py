r"""Every probe still compiles, and still yields a measurement.

    python kit/tools/pascal/probecheck.py CONFIG.toml
    python kit/tools/pascal/probecheck.py CONFIG.toml PROBEDIR
    python kit/tools/pascal/probecheck.py CONFIG.toml --gate

**WHY A PROBE NEEDS A CHECK AT ALL.** A probe is a measurement, and a project
cites it the way it cites a binary: a resolved investigation says "probe/X.PAS
is the record", a source comment says "four bytes here are not reachable from
Pascal, and probe/SEGOFS.PAS says so rather than a guess". Nothing else in the
tree recompiles them. A probe that has stopped compiling, or that compiles and
yields nothing, turns every one of those citations back into an assertion --
and it does it silently, because a probe is only ever run by hand and only when
somebody has a new question.

TWO THINGS ARE CHECKED, and the second is the one that found something:

  COMPILES     the compiler accepts the unit and writes a .TPU.
  MEASURABLE   codegen's `code_of` locates compiled code in that .TPU.

The second can fail while the first passes, and then `codegen.py` compares one
empty extraction against another and prints IDENTICAL CODE. `code_of` finds the
code by looking for the first routine's frame prologue, on the documented
assumption that every routine in a probe has a frame -- and a probe asking a
question about frameless code breaks that assumption exactly when the answer
matters most. It printed the miss as `code found at +0000`, because the report
formats `at or 0` and `None or 0` is 0.

Empty is therefore reported as NO CODE and never as agreement. This tool exists
to say which of a project's probes can still answer their question, per
compiler, in one table.

IT IS SLOW AND CANNOT BE OTHERWISE: one DOSBox run per probe per compiler, a
few seconds each. That is the price of the measurement being real.

IT SHARES THE STAGING DIRECTORY with the build and with codegen, and wipes it,
so only one of the three may run at a time.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[0]))
import project                                    # noqa: E402
import build                                      # noqa: E402
import codegen                                    # noqa: E402


def probes(where):
    return sorted(pathlib.Path(where).glob("*.PAS"))


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("-")]
    if not args:
        sys.stdout.write("usage: probecheck.py CONFIG.toml [PROBEDIR]\n")
        return 2
    cfg = build.read_config(args[0])

    root = pathlib.Path(args[0]).resolve().parent
    while not (root / "kit.toml").exists() and root != root.parent:
        root = root.parent

    if len(args) > 1:
        where = pathlib.Path(args[1])
    else:
        try:
            where = pathlib.Path(str(project.path("layout.probes")))
        except project.Missing as exc:
            return project.complain(exc)
    found = probes(where)
    if not found:
        sys.stdout.write("  no probe unit in %s\n" % where.as_posix())
        return 2

    staging = root / cfg.get("build", "build")
    if cfg.get("subdir"):
        staging = staging / cfg["subdir"]
    which = [k for k, v in cfg["compiler"].items() if isinstance(v, dict)]

    sys.stdout.write("%-14s %s\n" % ("probe", "  ".join("%-9s" % c
                                                        for c in which)))
    sys.stdout.write("-" * (15 + 11 * len(which)) + "\n")
    problems = []
    for p in found:
        cells = []
        for c in which:
            blob, _ = codegen.compile_with(cfg, root, staging, c, p)
            if blob is None:
                cells.append("NO BUILD")
                problems.append("%s does not compile with %s" % (p.name, c))
                continue
            at, code = codegen.code_of(blob)
            if at is None or not code:
                cells.append("NO CODE")
                problems.append(
                    "%s compiles with %s and yields no code -- code_of finds "
                    "no frame prologue, so any comparison of it is empty "
                    "against empty" % (p.name, c))
            else:
                cells.append("%d b" % len(code))
        sys.stdout.write("%-14s %s\n"
                         % (p.name, "  ".join("%-9s" % x for x in cells)))

    sys.stdout.write("\n")
    for x in problems:
        sys.stdout.write("  %s\n" % x)
    sys.stdout.write("%d probe(s) x %d compiler(s), %d problem(s)\n"
                     % (len(found), len(which), len(problems)))
    return 1 if (problems and "--gate" in argv) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
