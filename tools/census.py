"""Census of every script in both repos, and where each one is in its retirement.

WHY THIS IS A TOOL AND NOT A DOCUMENT. The hand-written script classification
(issue #2) was right when it was written and is now wrong in three places: it
counted 55 files where there are 60, it lists `emit_p6text.py` as broken after
it was repaired, and it lists `pairmap.py` as importing `refpath` below the line
that uses it, which is no longer true -- the import is at line 12 and the use at
line 17. A hand-maintained inventory that drifts is issue #15's class-4 defect
exactly: a measurement read as a finding. So this counts instead.

THE LIFECYCLE THIS TRACKS. The originals in `tools/` and in the VangeliSTracker
repo are frozen and keep working; the toolkit is built beside them by copy and
adjust; and once a toolkit tool supersedes an original, the original is archived.
"Copy and adjust, never refactor the originals" is therefore TRANSITIONAL, not
permanent, and the states below are that transition:

    superseded   a toolkit tool has replaced it. Names its successor. Still on
                 disk, because a successor landing and an original leaving are
                 two acts.
    archived     DELETED, and recoverable from the archive tag. The terminal
                 state, and the ONLY one that expects no file on disk. Names
                 its successor, so the record of where a script went outlives
                 the script.
    carry        should be copied across, not done yet.
    decline      will not be carried, with a reason. Dead scripts, spent
                 one-shots, and project-specific drivers.
    unknown      not yet triaged. Reported loudly, because an untriaged script
                 is the thing a stale document hides.

`archived` was missing until the first deletions needed it, though the sentence
above always described it. Its absence had a real cost waiting: with no state
meaning gone, every deletion reports a stale table entry, and the tidy response
-- delete the row -- discards the one record of which tool replaced it.

NOTHING UNEXPLAINED, IN EITHER DIRECTION. A script on disk with no triage entry
is reported. A triage entry naming a script that no longer exists is reported,
UNLESS it is archived, which is exactly that claim made deliberately. An
archived row whose file is still there is reported too: the deletion did not
happen. Both fail the run. That is the mechanism issue #15 named for this defect class,
and it is the only reason this file can be trusted where the document could not.

PATHS. The TABLE's location comes from the project's answers, because a table of
one project's scripts is project data and this file lives in the kit. It sat
beside this tool until the second consumer existed and reported 32 problems, all
of them the other project's rows.

The sibling repo lives at a machine-specific path, so it is NEVER named
in this committed file -- it comes from the local config, per the rule that put
`docs/continuation.md` out of the index. Pass roots on the command line, or set
them in the untracked local config.

    python kit/tools/census.py --root tools
    python kit/tools/census.py --root tools --root D:/elsewhere/scripts
"""
import ast
import io
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[0]))
import project                                    # noqa: E402

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover -- 3.11+ per pyproject.toml
    tomllib = None

# WHERE THE TABLE IS is the project's business, not this file's. It sat beside
# this tool until 23 Aug 2026, which meant a table of ONE project's scripts
# travelled with the kit: the second consumer to exist reported 32 problems
# within a minute, every one of them the other project's rows.
def table_path(override=None):
    return project.path("census.table", override)
STATES = ("superseded", "archived", "carry", "decline", "unknown")


def load_table(TABLE):
    if not TABLE.exists():
        return {}
    with io.open(TABLE, "rb") as fh:
        return tomllib.load(fh).get("script", {})


def parses(path):
    try:
        ast.parse(io.open(path, encoding="utf-8", newline="").read())
        return True
    except (SyntaxError, UnicodeDecodeError):
        return False


def opt_table(argv):
    """--table PATH, for a caller that would rather say than be asked."""
    return argv[argv.index("--table") + 1] if "--table" in argv else None


def main(argv):
    roots = [argv[i + 1] for i, a in enumerate(argv) if a == "--root"]
    if not roots:
        # The project's answers hold this repository's script folders in
        # kit.toml and any machine-specific root in kit.local.toml, which is
        # the mechanism this docstring used to promise and did not have.
        try:
            roots = [str(p) for p in project.paths("census.roots")]
        except project.Missing as exc:
            return project.complain(exc)

    found = {}
    for root in roots:
        for path in sorted(pathlib.Path(root).rglob("*.py")):
            found.setdefault(path.name, []).append(path)

    try:
        table = load_table(table_path(opt_table(argv)))
    except project.Missing as exc:
        return project.complain(exc)
    problems, rows = [], []

    for name in sorted(found):
        entry = table.get(name, {})
        state = entry.get("state", "unknown")
        if state not in STATES:
            problems.append("%s: state %r is not one of %s"
                            % (name, state, "/".join(STATES)))
        if state == "unknown":
            problems.append("%s: untriaged. Every script needs a state -- an "
                            "untriaged one is what a stale document hides." % name)
        if state in ("superseded", "archived") and not entry.get("successor"):
            problems.append("%s: marked %s but names no successor" % (name, state))
        if state == "archived":
            # A successor is allowed to CARRY THE ORIGINAL'S NAME -- linkcmp.py
            # and build.py both do -- and this table is keyed by basename, so
            # "archived but still on disk" has to mean "an ORIGINAL is still on
            # disk", not "a file of that name exists". Without the distinction
            # the two tools that kept their name can never be archived at all.
            outside = [str(q) for q in found[name] if "kit" not in q.parts]
            if outside:
                problems.append("%s: marked archived but an original is still "
                                "on disk: %s. Archived means deleted and "
                                "recoverable from the tag."
                                % (name, ", ".join(outside)))
        if state == "decline" and not entry.get("reason"):
            problems.append("%s: marked decline but gives no reason" % name)
        broken = [str(p) for p in found[name] if not parses(p)]
        if broken:
            problems.append("%s: does not parse: %s" % (name, ", ".join(broken)))
        rows.append((name, state, len(found[name]),
                     entry.get("successor") or entry.get("reason") or ""))

    for name in sorted(table):
        if name in found:
            continue
        # ARCHIVED is the one state that EXPECTS no file. It is the terminal
        # state this file's own header always described -- "once a toolkit tool
        # supersedes an original, the original is archived" -- and it was
        # missing from STATES until the first deletions needed it. A row that
        # merely names a successor is not enough: without a state meaning gone,
        # every deletion turns into a report of a stale table entry, and the
        # honest response would have been to delete the row and lose the record
        # of where the script went.
        if table[name].get("state") == "archived":
            rows.append((name, "archived", 0, table[name].get("successor", "")))
            continue
        problems.append("%s: in the census table but not on disk. A triage "
                        "entry outliving its script is how the last "
                        "inventory went stale." % name)

    counts = {}
    for _, state, _, _ in rows:
        counts[state] = counts.get(state, 0) + 1

    sys.stdout.write("SCRIPTS, by where they are in the retirement\n")
    for state in STATES:
        if counts.get(state):
            sys.stdout.write("  %-11s %3d\n" % (state, counts[state]))
    dup = [n for n, _, c, _ in rows if c > 1]
    sys.stdout.write("  %d distinct name(s) across %d file(s); %d name(s) in "
                     "more than one repo%s\n"
                     % (len(rows), sum(c for _, _, c, _ in rows), len(dup),
                        (": " + ", ".join(dup)) if dup else ""))

    if "--list" in argv:
        sys.stdout.write("\n")
        for name, state, n, note in rows:
            sys.stdout.write("  %-22s %-11s %s%s\n"
                             % (name, state, "x%d " % n if n > 1 else "   ", note))

    if problems:
        sys.stdout.write("\n")
        for p in problems:
            sys.stdout.write("  %s\n" % p)
    sys.stdout.write("\n%d problem(s)\n" % len(problems))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
