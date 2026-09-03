"""Run the universal check list, reading each status off the TOOL.

WHY THIS EXISTS, and it is not convenience. A shell reports the exit status of
the LAST command in a pipeline, so `tool | tail -1` exits with tail's status,
which is 0 whether the tool passed or failed. Measured on 2 Sep 2026: a
close-out ran thirteen checks that way and reported *0 non-zero exits*. One of
them had been exiting 1 throughout, and the whole list was declared clean on
that basis. The printed lines were true and the verdict was invented, which is
why it survived a read-through -- the failing tool's complaint was on a line
tail had discarded.

That trap is written down in WORKING.md section 9, and writing it down did not
stop the same loop being retyped by hand four times in one later session. So
the list is a program: it captures a return code on the line that produced it,
never through a pipe, and prints the summary separately.

WHAT IT IS NOT. It is not a new checking policy. Every entry here is an entry
of section 4's list, in section 4's order, and the tools that section names as
deliberately absent -- braces, tagcheck, dsverify, unitorder, cleanconf, clean
-- stay absent: each belongs to a job rather than to a session, and running one
where that job is not underway reports on something nobody is doing.

    python kit/tools/checklist.py                 the list, minus the slow one
    python kit/tools/checklist.py --probes B.toml  include probecheck, which
                                                  costs a DOSBox run per probe
                                                  per compiler
    python kit/tools/checklist.py --quiet          summary lines only

NO PATHS AND NO NUMBERS, which is section 4's point about its own list: the
answers file says where a build writes, so `measured.toml` is resolved through
`layout.build` rather than spelled here. A host repository with checks of its
own adds them to its agent file, not to this program.

ONE ENTRY IS A GIT COMMAND rather than a tool, and section 4 says explicitly
that wrapping it in Python would add a tool measuring nothing the command does
not. That objection is to a dedicated wrapper, and this is not one: the runner
already exists, the command costs nothing to include, and it has to run in the
kit as well as the host because a submodule has its own index the host's run
cannot see. Nine tracked-but-ignored files once travelled in the kit for a day,
visible only to the SECOND consumer. It is labelled where it runs so the output
stays auditable.
"""
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import project                                    # noqa: E402

KIT = pathlib.Path(__file__).resolve().parent

# Section 4's list, in section 4's order. A pair of (label, argv-tail); the
# measured.toml path is filled in from the project's own answer.
CHECKS = (
    ("wikitools/okfcheck", ("wikitools/okfcheck.py",)),
    ("wikitools/kbprofile", ("wikitools/kbprofile.py",)),
    ("wikitools/glossary", ("wikitools/glossary.py",)),
    ("pascal/markers --emit", ("pascal/markers.py", "--emit", "@MEASURED@")),
    ("pascal/ratchet --measured", ("pascal/ratchet.py", "--measured", "@MEASURED@")),
    ("pascal/observe --report", ("pascal/observe.py", "--report")),
    ("pascal/artefact --check", ("pascal/artefact.py", "--check")),
    ("pascal/plan --report", ("pascal/plan.py", "--report")),
    ("pascal/shared_asm --gate", ("pascal/shared_asm.py", "--gate")),
    ("pascal/routines", ("pascal/routines.py",)),
    ("pascal/paslint", ("pascal/paslint.py",)),
    ("pascal/asmaudit", ("pascal/asmaudit.py",)),
    ("encaudit", ("encaudit.py",)),
    ("eolcheck", ("eolcheck.py",)),
    ("toolindex --check", ("toolindex.py", "--check")),
)


def run(root, label, tail, quiet):
    """One check. The return code is bound on the line that produced it."""
    argv = [sys.executable, str(KIT / tail[0])] + list(tail[1:])
    done = subprocess.run(argv, cwd=str(root), capture_output=True,
                          text=True, encoding="utf-8", errors="replace")
    rc = done.returncode
    out = (done.stdout or "") + (done.stderr or "")
    print("  %-30s exit=%d" % (label, rc))
    if rc != 0 or not quiet:
        for line in out.splitlines():
            if line.startswith("  using "):
                continue
            if rc != 0 or not quiet:
                print("        " + line)
    return rc, out


def tracked_but_ignored(root, quiet):
    """git's own answer, run in the host AND in the kit.

    Two runs, because a submodule keeps its own index: the host's run cannot
    see inside it, and a .gitignore added after the fact does nothing to a file
    already tracked -- so the commit that looks like the fix is the commit that
    hides it.
    """
    bad = 0
    for where in (root, KIT.parent):
        cmd = ["git", "ls-files", "-i", "-c", "--exclude-standard"]
        done = subprocess.run(cmd, cwd=str(where), capture_output=True,
                              text=True, encoding="utf-8", errors="replace")
        names = [n for n in (done.stdout or "").splitlines() if n.strip()]
        label = "git ls-files -i -c  (%s)" % where.name
        print("  %-30s %s" % (label, "%d file(s)" % len(names) if names else "clean"))
        for n in names:
            print("        " + n)
        bad += len(names)
    return bad


def main(argv):
    try:
        root = project.find()
        if root is None:
            raise project.Missing(
                "no kit.toml found at or above %s -- run this from a host root"
                % pathlib.Path.cwd())
        build = project.path("layout.build", quiet=True)
    except project.Missing as exc:
        return project.complain(exc)

    quiet = "--quiet" in argv
    probes = None
    if "--probes" in argv:
        at = argv.index("--probes")
        if at + 1 >= len(argv):
            print("--probes needs the build config that drives the compilers")
            return 2
        probes = argv[at + 1]

    measured = str((build / "measured.toml"))
    print("checklist -- %s" % root)

    failed = []
    for label, tail in CHECKS:
        tail = tuple(measured if a == "@MEASURED@" else a for a in tail)
        rc, _ = run(root, label, tail, quiet)
        if rc != 0:
            failed.append((label, rc))

    if probes:
        rc, _ = run(root, "pascal/probecheck",
                    ("pascal/probecheck.py", probes), quiet)
        if rc != 0:
            failed.append(("pascal/probecheck", rc))
    else:
        print("  %-30s SKIPPED -- pass --probes CONFIG.toml" % "pascal/probecheck")

    stray = tracked_but_ignored(root, quiet)

    print("")
    if failed:
        print("%d of %d check(s) non-zero:" % (len(failed), len(CHECKS)))
        for label, rc in failed:
            print("  %-30s exit=%d" % (label, rc))
    else:
        print("every check exited 0")
    if stray:
        print("%d tracked file(s) the ignore rules claim to exclude" % stray)
    if not probes:
        print("probecheck was NOT run: safe on a day nobody touched a probe.")
    return 1 if (failed or stray) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
