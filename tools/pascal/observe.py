"""Record what a person saw when they ran a harness, so it stops being prose.

Rungs R2 ("it runs") and R3 ("a viewer sees no difference") are the only nodes
on the fidelity ladder whose instrument is a person watching a screen. The ladder
had to declare both instruments MISSING, and the measurement behind that is
blunt: 29 harnesses exist, 29 are built in run/, and there is no record of any
result anywhere in the repo. Four parts once "built" and had never been run.

The rule is that a human observation may make a rung green, but only
once it is recorded as a dated claim naming who ran what. The observation is
the instrument; THE RECORD IS THE RATCHET. This is that record.

THREE RULES THIS TOOL ENFORCES, each from a measured failure:

  R3 REQUIRES THE PART TIER. A scene harness cannot judge palette or
  cross-scene state, and the docs enumerate why: one scene shows the wrong
  colours alone because it inherits what the previous scene left behind;
  another must reset the video mode afterwards because the PART DRIVER does
  that and not the scene. So a scene-tier observation caps at R2.

  AN OBSERVATION IS ABOUT ONE BUILD. It stores the commit it was made at and a
  hash of the sources the harness actually depends on -- its own file plus the
  units in its `uses` clause. When those change the observation goes STALE and
  is reported, never failed. Voiding it on any edit would drop every
  behavioural rung to R0 and make the ladder useless; failing on it would call
  an ordinary edit a regression.

  STALENESS IS A GAP IN KNOWLEDGE, NOT A REGRESSION IN CODE. So `achieved`
  holds the last measured rung and the ratchet reads it, while `confirmed_at`
  holds the commit and the report reads that. An unverified claim is visible as
  unverified without the ratchet failing on an edit -- which is the wedge issue
  the ratchet's design had to avoid.

  A RENAME IS NOT A CHANGE, AND THE BINARY IS WHAT SAYS SO. The staleness rule
  above hashes the SOURCES an observation depends on, which is the right question
  -- "might this have changed?" -- and the wrong answer when the change was a
  rename. Renaming fifteen units and their identifiers marked six R3 rows stale
  on one target while every built executable stayed byte-identical, so six
  watched runs read as unverified for a change that provably could not alter
  what anybody saw.

  `--reaffirm` closes that without fabricating a run. It requires a passing
  `[artefact.KEY]` row -- whole-binary identity against the original, RECOMPUTED
  rather than read back -- and updates the source fingerprint while leaving the
  DATE and the OBSERVER alone. What it records is exactly what is true: a person
  watched this, and the binary has not changed since. An observation now also
  stores that binary's hash, so the second re-affirmation is a comparison rather
  than an argument.

  A RETIRED HARNESS IS SUPERSEDED, NOT DELETED AND NOT STALE FOR EVER. When a
  harness stops existing -- most often because the thing it wrapped became a
  program of its own -- its row can never be refreshed, so it reports STALE at
  every run from then on. Seven such rows on one target were enough to train a
  reader to skim the report, which is the failure this whole tool exists to
  prevent. `--supersede` records the successor and the date, changes NO measured
  field, and moves the row out of the stale count. It refuses unless the old
  harness is really gone AND the successor already has an observation of its own,
  because retiring a row whose knowledge nothing replaced hides exactly the gap
  the register is for.

`invisible` is a first-class outcome, not a synonym for `ran`. A harness that
omits a setup call can run a scene CORRECTLY AND INVISIBLY -- one ran entirely
in 80x25 text, "indistinguishable from a hang".

    python kit/tools/pascal/observe.py status.toml --report
    python kit/tools/pascal/observe.py status.toml --harness TPART5 --tier part \\
        --outcome matches --observer maintainer --date 2026-08-20 \
        --against NEUROSIS_005.exe
    python kit/tools/pascal/observe.py status.toml --supersede TPART5 \
        --by NEUR5 --date 2026-08-27 --write
    python kit/tools/pascal/observe.py status.toml --reaffirm NEUR5 --date 2026-08-27 --write

THE OBSERVER FIELD RECORDS THAT A PERSON WATCHED, NEVER WHICH PERSON. A role --
`maintainer`, `reviewer` -- carries everything the record needs, because the
point of this tool is to refuse a run nobody made and a role asserts exactly
that. A name or an email here is PII in a repository that may not stay private,
and it cannot be edited out of history afterwards.
"""
import hashlib
import io
import os
import pathlib
import re
import subprocess
import sys


# Both invocation styles are first-class, so both need a path. parents[1]
# is kit/tools, which is where `project` lives; parents[0] is this tier's
# own folder, which Python only adds by itself when the file is run as a
# script -- so without it `from pascal import ratchet` cannot find the
# sibling `register`.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[0]))
import register                                   # noqa: E402
import project                                    # noqa: E402

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover -- 3.11+ per pyproject.toml
    tomllib = None

TIERS = ("scene", "part")
# R2 outcomes describe whether it ran at all; R3 outcomes describe what a
# viewer saw. `invisible` belongs to R2 and is deliberately not `ran`.
OUTCOMES = {
    "ran": "R2", "hung": "R0", "crashed": "R0", "invisible": "R0",
    "matches": "R3", "differs": "R2",
}




def toml_str(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def head_commit(root="."):
    try:
        out = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"],
                             capture_output=True, text=True, encoding="utf-8")
        return out.stdout.strip()[:12] if out.returncode == 0 else "unknown"
    except OSError:
        return "unknown"


def harness_sources(harness, src="src"):
    """The harness's own file plus every unit in its `uses` clause.

    Precise on purpose. Hashing all of src/ would mark every observation stale
    on any edit anywhere, which is the over-broad answer that was rejected.
    """
    root = pathlib.Path(src)
    own = root / (harness.upper() + ".PAS")
    if not own.exists():
        return []
    files = [own]
    text = io.open(own, encoding="ascii", newline="").read()
    m = re.search(r"\buses\b(.*?);", text, re.S | re.I)
    if m:
        for name in re.split(r"[,\s]+", m.group(1)):
            name = name.strip()
            if not name:
                continue
            for cand in (root / (name.upper() + ".PAS"),):
                if cand.exists():
                    files.append(cand)
    return files


def fingerprint(files):
    h = hashlib.sha256()
    for path in sorted(files):
        h.update(io.open(path, "rb").read())
    return h.hexdigest()[:16] if files else ""


def dump(status):
    """Serialisation is register.py's job, one writer for every tool, so no
    tool can drop a section another tool owns."""
    return register.dump(status)


def record(status, args):
    harness = args["harness"]
    tier, outcome = args["tier"], args["outcome"]
    if tier not in TIERS:
        return "tier must be one of %s" % "/".join(TIERS)
    if outcome not in OUTCOMES:
        return "outcome must be one of %s" % "/".join(sorted(OUTCOMES))
    rung = OUTCOMES[outcome]
    if rung == "R3" and tier != "part":
        return ("%s claims R3 from the %s tier. R3 requires the PART tier: a "
                "scene harness cannot judge palette or cross-scene state."
                % (harness, tier))
    if outcome == "matches" and not args.get("against"):
        return "an R3 claim must name the original it was compared against"

    files = harness_sources(harness)
    if not files:
        return "no source found for harness %s in src/" % harness
    row = {
        "harness": harness, "tier": tier, "outcome": outcome, "achieved": rung,
        "observer": args["observer"], "date": args["date"],
        "confirmed_at": head_commit(), "fingerprint": fingerprint(files),
        "against": args.get("against", ""), "note": args.get("note", ""),
    }
    # The hash of the binary that was watched, where the register knows it. This
    # is what makes a later --reaffirm a comparison instead of an argument, and
    # recording it now costs nothing.
    art = status.get("artefact", {}).get(harness, {})
    if art.get("sha256"):
        row["binary"] = art["sha256"]
    status.setdefault("observation", {})[harness] = row
    return None


def reaffirm(status, key, date, root="."):
    """Re-affirm an observation whose SOURCES moved but whose BINARY did not.

    Every refusal below is the point of the flag: this must never become a way of
    making a stale row look fresh.
    """
    import hashlib

    rows = status.get("observation", {})
    if key not in rows:
        return "%s has no observation to re-affirm" % key
    row = rows[key]
    art = status.get("artefact", {}).get(key)
    if not art:
        return ("%s has no [artefact.%s] row, so nothing here says the binary is "
                "unchanged. Re-affirming would be a guess -- re-run it instead."
                % (key, key))

    ours = pathlib.Path(root) / art.get("ours", "")
    orig = pathlib.Path(root) / art.get("original", "")
    if not ours.exists() or not orig.exists():
        return "cannot read %s or %s" % (art.get("ours"), art.get("original"))
    a, b = ours.read_bytes(), orig.read_bytes()
    now = hashlib.sha256(a).hexdigest()
    if a != b or now != art.get("sha256"):
        return ("the artefact for %s does not hold right now -- the build differs "
                "from the original, or from what was recorded. Fix that first: a "
                "re-affirmation on a failing artefact asserts the opposite of the "
                "truth." % key)

    was = row.get("binary")
    if was and was != now:
        return ("%s was observed against a DIFFERENT binary (%s, now %s). The "
                "executable changed since somebody watched it, which is exactly "
                "what staleness is for. Re-run it." % (key, was[:12], now[:12]))

    files = harness_sources(row.get("harness", key))
    if not files:
        return ("no source found for %s, so its fingerprint cannot be brought up "
                "to date" % key)
    row["binary"] = now
    row["reaffirmed_on"] = date
    row["fingerprint"] = fingerprint(files)
    row["confirmed_at"] = head_commit(root)
    return None if was else "FIRST"


def supersede(status, old, new, date):
    """Retire a row whose harness no longer exists. Measured fields UNTOUCHED.

    Every refusal below is the point of the flag rather than an obstacle to it:
    a tool that let anything be retired would be a way of making the report look
    finished.
    """
    rows = status.get("observation", {})
    if old not in rows:
        return "%s has no observation to supersede" % old
    if rows[old].get("superseded_by"):
        return ("%s is already superseded by %s on %s"
                % (old, rows[old]["superseded_by"], rows[old].get("superseded_on", "?")))
    if harness_sources(old):
        return ("%s still has source in src/, so its row is STALE rather than "
                "retired -- refresh it with a run instead. Superseding a harness "
                "that still exists hides a gap that can be closed." % old)
    if not harness_sources(new):
        return "no source found for %s in src/, so it cannot be the successor" % new
    if new not in rows:
        return ("%s has no observation of its own, so superseding %s would leave "
                "the register showing no gap where there is one. Observe %s "
                "first." % (new, old, new))
    rows[old]["superseded_by"] = new
    rows[old]["superseded_on"] = date
    return None


def report(status):
    rows = status.get("observation", {})
    if not rows:
        sys.stdout.write("  no observations recorded. Every harness is at R0, "
                         "stated rather than implied.\n")
        return 0
    stale = retired = 0
    for key in sorted(rows):
        row = rows[key]
        now = fingerprint(harness_sources(row.get("harness", key)))
        fresh = now and now == row.get("fingerprint")
        if row.get("superseded_by"):
            # Retired deliberately, so it is neither fresh nor a gap. Counted
            # apart from stale on purpose: a number that mixes the two cannot be
            # read, and the stale count is the one somebody has to act on.
            retired += 1
            suffix = ("   SUPERSEDED by %s on %s"
                      % (row["superseded_by"], row.get("superseded_on", "?")))
        elif fresh:
            suffix = ""
        else:
            stale += 1
            suffix = ("   STALE, source changed since "
                      + str(row.get("confirmed_at", "?")))
        sys.stdout.write("  %-8s %-5s %-9s %-4s %s %s%s\n"
                         % (row.get("harness", key), row.get("tier", "?"),
                            row.get("outcome", "?"), row.get("achieved", "?"),
                            row.get("date", "?"), row.get("observer", "?"),
                            suffix))
    sys.stdout.write("  %d observation(s), %d stale%s. Stale is a gap in "
                     "KNOWLEDGE, not a regression -- reported, never failed.\n"
                     % (len(rows), stale,
                        ", %d superseded" % retired if retired else ""))
    return 0


def main(argv):
    # A flag's VALUE is not a positional -- see project.positionals.
    # Every flag that TAKES A VALUE has to be listed, or that value is
    # read as the register path. --against was missing and worked only
    # because it is conventionally written after the path.
    args = project.positionals(argv[1:], ('--harness', '--tier',
                                          '--outcome', '--observer',
                                          '--date', '--note',
                                          '--evidence', '--against',
                                          '--supersede', '--by',
                                          '--reaffirm'))
    if not args and any(a.startswith("--") for a in argv[1:]):
        # A flag but no register: ask the project where its register is.
        try:
            args = [str(project.path("layout.register"))]
        except project.Missing as exc:
            return project.complain(exc)
    if not args:
        sys.stdout.write("usage: observe.py <status.toml> --report\n"
                         "       observe.py <status.toml> --harness X --tier "
                         "scene|part --outcome ... --observer who --date YYYY-MM-DD\n"
                         "       observe.py <status.toml> --supersede OLD --by "
                         "NEW --date YYYY-MM-DD\n"
                         "       observe.py <status.toml> --reaffirm KEY --date "
                         "YYYY-MM-DD\n")
        return 2
    path = args[0]
    status = register.load(path)

    def opt(name, default=None):
        flag = "--" + name
        return argv[argv.index(flag) + 1] if flag in argv else default

    if "--report" in argv:
        return report(status)

    if opt("reaffirm"):
        key, date = opt("reaffirm"), opt("date")
        if not date:
            sys.stdout.write("  missing: --date -- a re-affirmation is a dated "
                             "claim that the binary has not changed\n")
            return 2
        err = reaffirm(status, key, date)
        first = err == "FIRST"
        if err and not first:
            sys.stdout.write("  REFUSED: %s\n" % err)
            return 1
        if first:
            sys.stdout.write("  %s had no recorded binary hash: it was observed "
                             "before that was stored, so this rests on the "
                             "artefact row alone. The hash is recorded now.\n"
                             % key)
        if "--write" in argv:
            io.open(path, "w", encoding="utf-8", newline="\n").write(dump(status))
            sys.stdout.write("  %s re-affirmed -- binary unchanged, date and "
                             "observer untouched\n" % key)
        else:
            sys.stdout.write("  would re-affirm %s -- pass --write\n" % key)
        return 0

    if opt("supersede"):
        old_h, new_h, date = opt("supersede"), opt("by"), opt("date")
        missing = [n for n, v in (("--by", new_h), ("--date", date)) if not v]
        if missing:
            sys.stdout.write("  missing: %s -- retiring a row is a dated claim "
                             "about what replaced it\n" % ", ".join(missing))
            return 2
        err = supersede(status, old_h, new_h, date)
        if err:
            sys.stdout.write("  REFUSED: %s\n" % err)
            return 1
        if "--write" in argv:
            io.open(path, "w", encoding="utf-8", newline="\n").write(dump(status))
            sys.stdout.write("  %s superseded by %s in %s\n"
                             % (old_h, new_h, path))
        else:
            sys.stdout.write("  would supersede %s by %s -- pass --write\n"
                             % (old_h, new_h))
        return 0

    if not opt("harness"):
        return report(status)

    fields = {k: opt(k) for k in ("harness", "tier", "outcome", "observer",
                                  "date", "against", "note")}
    missing = [k for k in ("harness", "tier", "outcome", "observer", "date")
               if not fields.get(k)]
    if missing:
        sys.stdout.write("  missing: %s -- an observation is only evidence if "
                         "it is dated and says who ran what\n"
                         % ", ".join(missing))
        return 2

    err = record(status, fields)
    if err:
        sys.stdout.write("  REFUSED: %s\n" % err)
        return 1
    if "--write" in argv:
        io.open(path, "w", encoding="utf-8", newline="\n").write(dump(status))
        sys.stdout.write("  recorded %s in %s\n" % (fields["harness"], path))
    else:
        sys.stdout.write("  would record %s -- pass --write\n" % fields["harness"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
