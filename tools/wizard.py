"""Install the kit into a project: propose, confirm, write.

    python kit/tools/wizard.py                propose, and ask what it cannot see
    python kit/tools/wizard.py --check        propose, and DIFF against the
                                              kit.toml already there

THERE IS NO --write, and a line here claimed one for as long as this docstring
existed. Nothing wrote it: `--write` appeared once in this file, in that line,
so the documented command proposed, exited 0, and left no file -- which reads
exactly like a wizard that ran. kit.toml is written by hand from what this
program prints, which is consistent with the paragraph below: a program that
does not decide has no business writing the answers either.

THIS PROGRAM PROPOSES. IT DOES NOT DECIDE. A prototype that decided got two
answers wrong on the first real project it met -- it proposed a target's RELEASE
sources over the reconstruction's, and a release executable over the unpacked
measurement target -- and both errors came from the same place: **it ranked
candidates by how many files they held.** A release is complete and a
reconstruction by definition is not, so file count favours the wrong answer, and
favours it more strongly the more work is left to do.

So there is no file count here. Candidates are ranked by the KIND of evidence
behind them, strongest first:

    NAMED BY A SCRIPT   a program in this project already says this path. The
                        facts were written down before we arrived: one build
                        harness said `SRC = ROOT / 'v1.31b' / 'src'` and another
                        module said exactly which file the reference image is.
                        Nothing beats this.
    CONVENTIONAL NAME   `status.toml`, `build/`, `kit/wiki` -- a name the kit
                        itself defined, so finding it is not a guess.
    SHAPE ONLY          a directory that merely contains the right sort of file.
                        Reported as weak, and never proposed alone where a
                        stronger candidate exists.

**A value with only SHAPE-ONLY evidence is a question, not a proposal.** That is
the whole lesson of the prototype.

WHAT IT NEVER GUESSES, because no listing implies them: the paragraph a
disassembly calls the start of the load image, and which sources are being
WRITTEN as against read for reference. Those are asked, by ROLE.

TWO MODES, and it says which it is in:

    ADOPTING   the project has scripts of its own to read. Propose from them.
    NEW        it has none, so there is nothing to read and everything to ask.

Whichever mode, `--check` is the test that matters: run it on a project whose
right answers are already known and see whether the proposal agrees. Adopting a
project you cannot check is how a wizard is confidently wrong in private.
"""
import io
import os
import pathlib
import re
import sys

try:
    import tomllib
except ModuleNotFoundError:                       # pragma: no cover -- 3.11+
    import tomli as tomllib                       # type: ignore

# What a project MUST answer to hold a measurement at all. Deliberately tiny:
# every other key the kit reads is optional for some real project, and a
# required list that grows is a list nobody can satisfy. The test for adding
# one is NOT "many instruments want it" -- `layout.built` is wanted by thirteen
# and a project that links nothing still has no answer for it. It is: WITHOUT
# THIS, NOTHING IN THE PROJECT CAN HOLD A MEASUREMENT.
REQUIRED = {
    "layout.register": "the ratchet, the observations and the plan live here; "
                       "without it five instruments exit 2 and no result in "
                       "this project is held by anything",
}

ROLE = "named as a role by a script"
NAMED, CONVENTION, SHAPE = "named by a script", "conventional name", "shape only"

# WEAKER THAN SHAPE, because a derived tree has the same shape as the tree it
# was derived from -- that is what makes it derived. A build directory holds
# staged copies of the sources and a clean copy holds regenerated ones, so
# "holds .PAS files" is true of all three and cannot separate them. Ranked
# below SHAPE rather than dropped: a project whose sources really do live in a
# directory named this way still gets an answer, just last.
DERIVED = "shape only, and it looks like a derived copy"
STRENGTH = {ROLE: 4, NAMED: 3, CONVENTION: 2, SHAPE: 1, DERIVED: 0}

# A variable whose NAME says what the path is FOR. This is the project telling
# you the role, which is the one thing a directory listing never does -- and it
# is the difference between a reconstruction's sources and a probe directory
# that three of the same scripts also mention.
ROLE_NAMES = {
    "layout.src": ("SRC", "SOURCE", "SOURCES", "SRCDIR"),
    "target.image": ("IMAGE", "ORIG", "ORIGINAL", "REF", "REFIMG", "TARGET"),
    "layout.build": ("BUILD", "BUILDDIR", "OUT"),
    "layout.built": ("RUN", "BUILT", "INSTALL", "INSTALLDIR"),
    "layout.exempt": ("EXEMPT", "EXEMPTIONS"),
}

# Paths a project's own scripts mention. Deliberately loose: this only has to
# surface a candidate, and a human or an agent decides what it means.
PATH_LITERAL = re.compile(r"""['"]([A-Za-z0-9_.][A-Za-z0-9_./\\-]{2,60})['"]""")

SKIP_DIRS = {".git", "kit", "__pycache__", ".venv", "build", "node_modules"}


def keys_the_kit_asks_for(kit):
    """Every answer key the kit's own programs look up.

    Read out of the source rather than listed here, because a list here would go
    stale the moment an instrument needed a new answer -- which is exactly how
    this program came to propose five keys for a project holding thirteen.
    """
    pat = re.compile(r"project\.(?:get|path|paths)\(\s*['\"]([a-z_]+\.[a-z_]+)['\"]")
    found = {}
    for f in pathlib.Path(kit).rglob("*.py"):
        if "__pycache__" in f.parts or f.name == "wizard.py":
            continue
        text = io.open(f, encoding="utf-8", errors="replace").read()
        for m in pat.finditer(text):
            found.setdefault(m.group(1), set()).add(f.name)
    return found


def project_scripts(root):
    """This project's own programs -- not the kit's."""
    out = []
    for p in root.rglob("*.py"):
        parts = set(p.parts)
        if parts & SKIP_DIRS:
            continue
        out.append(p)
    return out


def literals(root):
    """Every path-shaped string this project's scripts mention, and who said it.

    THIS IS THE MECHANICAL HALF of "read the project's scripts". It finds the
    strings; deciding that `ref/vt1.31b.bin` is a measurement target and
    `MAKESTR.EXE` is a build artefact is the reading, and a person or an agent
    does that.
    """
    said = {}
    for script in project_scripts(root):
        text = io.open(script, encoding="utf-8", errors="replace").read()
        for m in PATH_LITERAL.finditer(text):
            s = m.group(1).replace("\\", "/").strip("/")
            if s and not s.startswith("http"):
                said.setdefault(s.lower(), set()).add(script.name)
    return said


def roles(root, scripts):
    """{variable name: {paths it is assigned}}, from simple assignments.

    Deliberately shallow: `NAME = ... 'a' ... 'b'` collects a and b. A path
    built from pieces -- `ROOT / 'v1.31b' / 'src'` -- is exactly the shape that
    matters and is exactly what this catches, by joining the pieces in order.
    """
    out = {}
    pat = re.compile(r"^\s*([A-Z][A-Z0-9_]{1,14})\s*=\s*(.+)$", re.M)
    for script in scripts:
        text = io.open(script, encoding="utf-8", errors="replace").read()
        for m in pat.finditer(text):
            name, rhs = m.group(1), m.group(2)
            bits = [b for b in re.findall(r"['\"]([^'\"]{1,40})['\"]", rhs)
                    if "/" in b or "." in b or b.isidentifier() or "-" in b]
            if not bits:
                continue
            joined = "/".join(b.strip("/") for b in bits).lower()
            out.setdefault(name, set()).add(joined)
            for b in bits:
                out.setdefault(name, set()).add(b.strip("/").lower())
    return out


def role_says(role_map, key, rel):
    """Which role-named variables name this path."""
    rel = rel.replace("\\", "/").lower()
    hits = []
    for name in ROLE_NAMES.get(key, ()):
        for said in role_map.get(name, ()):
            if said == rel or rel.endswith("/" + said) or said.endswith("/" + rel):
                hits.append(name)
                break
    return hits


def named_by(said, rel):
    """Which scripts name this path, whole or as a tail of a longer one."""
    rel = rel.replace("\\", "/").lower()
    who = set(said.get(rel, ()))
    for s, scripts in said.items():
        if s and (rel.endswith("/" + s) or s.endswith("/" + rel) or s == rel):
            who |= scripts
    # a path built up from pieces: 'v1.31b' and 'src' said separately
    bits = [b for b in rel.split("/") if b]
    if len(bits) > 1 and all(b in said for b in bits):
        for b in bits:
            who |= said[b]
    return sorted(who)


class Proposal(object):
    def __init__(self):
        self.rows = []          # (key, value, evidence, why)
        self.questions = []     # (key, question, default)

    def offer(self, key, value, evidence, why, witnesses=1):
        self.rows.append((key, value, evidence, why, witnesses))

    def ask(self, key, question, default=None):
        self.questions.append((key, question, default))

    def best(self, key):
        got = self.candidates(key)
        return got[0] if got else None

    def candidates(self, key):
        """Strongest evidence first, then MOST WITNESSES.

        Two paths can both be named by a script and not be equally believable:
        one project's reconstruction sources are named by three of its scripts
        including its build harness, and its release sources by one -- which is
        the script its own census marks as unable to run. Counting the
        witnesses is what separates them, and without it the right answer loses
        a coin toss.
        """
        seen, got = set(), []
        for r in self.rows:
            if r[0] != key:
                continue
            v = tuple(r[1]) if isinstance(r[1], list) else r[1]
            if v in seen:            # a case-insensitive filesystem offers
                continue             # the same file twice
            seen.add(v)
            got.append(r)
        return sorted(got, key=lambda r: (-STRENGTH[r[2]], -r[4]))

    def keys(self):
        out = []
        for key, _, _, _, _ in self.rows:
            if key not in out:
                out.append(key)
        return out


def dirs_with(root, suffixes):
    for d in [root] + [p for p in root.rglob("*") if p.is_dir()]:
        if set(d.parts) & SKIP_DIRS:
            continue
        if any(f.suffix.upper() in suffixes for f in d.iterdir() if f.is_file()):
            yield d


def selects(root, have, key, mine, theirs):
    """True/False if both values are FILE SELECTORS that can be resolved.

    A selector can be spelled as a literal list or as a glob, and the two
    spellings can pick exactly the same file. Compared as text they never
    match: `['VTMAIN.EXE']` against `VTMAIN*.EXE` was reported as a
    disagreement in two consumers, in both of which the glob selects that one
    file and nothing else.

    That is not the wizard being wrong, and scoring it as a miss buries the
    disagreements that ARE real -- which is the whole value of this check.
    So the comparison is on what each selects. Returns None when the
    directory to resolve against is unknown, and the caller falls back to
    comparing text, because a selector nothing can expand is just a string.
    """
    if not key.endswith("_pattern") or mine is None or theirs is None:
        return None
    where = have.get("layout.built") or have.get("layout.build")
    if not where or not (root / where).is_dir():
        return None

    def hits(v):
        out = set()
        for pat in (v if isinstance(v, list) else [v]):
            out |= {q.name for q in (root / where).glob(str(pat))}
        return out

    a, b = hits(mine), hits(theirs)
    return None if not (a or b) else a == b


def derived_copy(rel, siblings):
    """Why `rel` looks like a copy of another candidate, or "".

    Three shapes, all measured in real consumers rather than imagined:

      * a BUILD or staging directory, which holds the sources copied in to
        be compiled -- one consumer has 29 .PAS in `src` and the same 29 in
        `build`, so counting files cannot separate them either;
      * a CLEAN copy, `x-clean` or `clean-x` beside `x` -- a regenerable
        documentation tree that is never hand-edited, so proposing it as the
        source root points every instrument at a file the next regeneration
        overwrites;
      * a PROBE directory of compiler test programs, which is Pascal that
        was never part of the target.

    Naming rather than content, deliberately. Content cannot decide it: a
    staged copy is byte-identical to its original, which is the point of
    staging. What separates them is what the project CALLS them.
    """
    name = rel.rsplit("/", 1)[-1].lower()
    if name.startswith("build") or name in ("out", "stage", "staging"):
        return "a build or staging directory holds the sources it compiles"
    for other in siblings:
        o = other.rsplit("/", 1)[-1].lower()
        if o != name and name in (o + "-clean", "clean-" + o):
            return "looks like a regenerated copy of %s" % other
    if name in ("probe", "probes"):
        return "compiler probes are Pascal the target never contained"
    return ""


def propose(root):
    p = Proposal()
    scripts = project_scripts(root)
    said = literals(root)
    role_map = roles(root, scripts)
    adopting = bool(scripts)

    # --- the sources ----------------------------------------------------
    candidates = {d.relative_to(root).as_posix() or "."
                  for d in dirs_with(root, {".PAS"})}
    for d in dirs_with(root, {".PAS"}):
        rel = d.relative_to(root).as_posix() or "."
        who = named_by(said, rel)
        as_role = role_says(role_map, "layout.src", rel)
        if as_role:
            p.offer("layout.src", rel, ROLE,
                    "a script calls it %s" % ", ".join(as_role), len(who) or 1)
        elif who:
            p.offer("layout.src", rel, NAMED,
                    "named by " + ", ".join(who[:3]), len(who))
        else:
            why = derived_copy(rel, candidates)
            if why:
                p.offer("layout.src", rel, DERIVED, why)
            else:
                p.offer("layout.src", rel, SHAPE, "holds .PAS files")

    # --- conventional names the kit itself defined ----------------------
    if (root / "status.toml").is_file():
        p.offer("layout.register", "status.toml", CONVENTION,
                "the register's conventional name")
    else:
        # ASKED, NOT SKIPPED, and this was a real gap. The offer above used to
        # be the only mention of the key, so a project with no register yet was
        # never asked for one -- and a register is the one answer a fresh
        # project is GUARANTEED not to have. Five instruments want it and all
        # five exit 2 without it, so this silence read as consent and two
        # consumers installed the kit with no ratchet at all.
        p.ask("layout.register",
              "no register here yet -- what should the status register be "
              "called? It holds the ratchet, the observations and the plan, "
              "and five instruments refuse to run without it",
              "status.toml")

        # ASKED, NOT LISTED, AND ONLY FOR A NEW PROJECT. Tagging the apparatus
        # as you write it costs one marker. Deciding it afterwards means
        # re-deriving one judgement per paragraph from prose alone, and more
        # than half of that apparatus carries no mechanical tell -- so no
        # instrument can find what nobody marked. A day-one decision belongs
        # in the questions, not in the list of keys this program cannot answer.
        p.ask("layout.tagged",
              "will this project keep a stripped copy of its sources, for a "
              "reader who wants the PROGRAM rather than the evidence? Say true "
              "and tag the apparatus as you write it -- WORKING.md section 2a. "
              "Left until later, the same judgement has to be made again from "
              "the prose, and mostly without an instrument to check it",
              "true")
    if (root / "kit" / "wiki").is_dir():
        p.offer("layout.wiki", "kit/wiki", CONVENTION, "the kit brought it")
    for name in ("build", "out"):
        if (root / name).is_dir():
            p.offer("layout.build", name, CONVENTION,
                    "a build directory's conventional name")

    # --- the measurement target, which some projects do not have ---------
    # A project with ONE original has an image. A project with nine parts has a
    # per-part map instead, and proposing an image for it is a wrong answer
    # dressed as a helpful one.
    for pat in ("*.bin", "*.BIN", "*.exe", "*.EXE", "*.[0-9][0-9][0-9]"):
        for f in root.rglob(pat):
            if set(f.parts) & SKIP_DIRS or f.stat().st_size < 4096:
                continue
            rel = f.relative_to(root).as_posix()
            who = named_by(said, rel)
            as_role = role_says(role_map, "target.image", rel)
            if as_role:
                p.offer("target.image", rel, ROLE,
                        "a script calls it %s" % ", ".join(as_role),
                        len(who) or 1)
            elif who:
                p.offer("target.image", rel, NAMED,
                        "named by " + ", ".join(who[:3]), len(who))

    # --- where a finished build is installed -----------------------------
    for name in ("run", "bin", "dist", "build"):
        d = root / name
        if not d.is_dir():
            continue
        as_role = role_says(role_map, "layout.built", name)
        if as_role:
            p.offer("layout.built", name, ROLE,
                    "a script calls it %s" % ", ".join(as_role))
        elif name == "run":
            p.offer("layout.built", name, CONVENTION,
                    "the conventional name for finished output")
        elif name == "build" and any(f.suffix.upper() == ".EXE"
                                     for f in d.iterdir() if f.is_file()):
            # `build` and `built` CAN be one directory, and on a project that
            # links in place they are. Only run/bin/dist were considered, so
            # such a project was offered nothing, `built_pattern` was
            # unreachable -- it is only asked once `built` is chosen -- and
            # routines.py plus every span instrument exited 2. SHAPE evidence
            # deliberately: it is weak, so the report turns it into a question
            # rather than proposing a directory that also stages sources.
            p.offer("layout.built", name, SHAPE,
                    "holds .EXE, though it also stages sources")

    # --- which of the files in it are OURS -------------------------------
    built = p.best("layout.built")
    if built:
        exes = sorted({f.stem for f in (root / built[1]).glob("*")
                       if f.suffix.upper() == ".EXE"})
        prefixes = sorted({re.sub(r"[0-9].*$", "", s) for s in exes} - {""})
        if len(prefixes) > 1:
            # More than one family in there. Choosing wrong makes a compare
            # tool measure an original against itself and PASS, which is the
            # worst kind of wrong, so it is asked and never guessed.
            p.ask("layout.built_pattern",
                  "%s holds more than one family of executable (%s) -- which "
                  "glob selects OURS, not copies of the originals?"
                  % (built[1], ", ".join(p2 + "*" for p2 in prefixes)),
                  None)     # no default: a wrong glob PASSES, silently
        elif prefixes:
            p.offer("layout.built_pattern", prefixes[0] + "*.EXE", SHAPE,
                    "the only family of .EXE in %s" % built[1])

    # --- the shared-assembler exemptions, genuinely optional -------------
    src = p.best("layout.src")
    # EVERY MATCH, NOT THE FIRST. This broke on the first hit, and rglob walks
    # alphabetically -- so in a project holding both `clean-src/shared-exempt`
    # and `src/shared-exempt`, the regenerated copy won on sort order alone.
    # Pointing an exempt list at a derived tree puts edits in a file the next
    # regeneration overwrites.
    for cand in sorted(root.rglob("*exempt*")):
        if not (cand.is_file() and not set(cand.parts) & SKIP_DIRS):
            continue
        rel = cand.relative_to(root).as_posix()
        holder = rel.rsplit("/", 1)[0] if "/" in rel else "."
        why = derived_copy(holder, candidates)
        if why:
            p.offer("layout.exempt", rel, DERIVED,
                    "its name says exempt, but %s" % why)
        elif src and holder == src[1]:
            p.offer("layout.exempt", rel, NAMED,
                    "its name says exempt, and it sits in the source root")
        else:
            p.offer("layout.exempt", rel, CONVENTION, "its name says exempt")

    # THE RETIREMENT CENSUS IS GONE and its two proposals went with it. Worth
    # noting how they survived it: this file DERIVES its question list from the
    # kit's own source, so a key no tool reads can never be asked about -- but
    # the PROPOSALS are hand-written, and those outlived the tool they were for
    # by exactly as long as it took somebody to run --check. A derived list and a
    # hand-maintained hint table have different half-lives.

    # --- one original, or several? ---------------------------------------
    parts = {}
    for f in root.rglob("*"):
        if not f.is_file() or set(f.parts) & SKIP_DIRS:
            continue
        m = re.search(r"[_.]([0-9]{3})(_[a-z]+)?\.(exe|bin)$", f.name, re.I)
        if m:
            parts.setdefault(m.group(1), []).append(
                (f.relative_to(root).as_posix(), m.group(2) or ""))
    if len(parts) > 2:
        variants = sorted({v for rows in parts.values() for _, v in rows if v})
        note = ("" if not variants else
                "  NOTE: %s variant(s) exist alongside the plain files (%s). "
                "Which to measure against is a DECISION about the measurement, "
                "not a detail -- one of them may be this project's own "
                "disassembly aid rather than a release."
                % (len(variants), ", ".join(variants)))
        p.ask("target.original",
              "%d numbered originals found, so this wants a [target.original] "
              "MAP keyed by part, not one image.%s" % (len(parts), note),
              None)

    # --- what no listing can imply ---------------------------------------
    p.ask("target.first_para",
          "what paragraph does your disassembly call the start of the load "
          "image?", "0x1000")
    for key in p.keys():
        got = p.candidates(key)
        if not got:
            continue
        top = got[0]
        tied = [c for c in got[1:]
                if STRENGTH[c[2]] == STRENGTH[top[2]] and c[4] == top[4]]
        if top[2] == SHAPE:
            p.ask(key, "%s has only weak evidence -- which is it, and are you "
                       "WRITING it or reading it for reference?" % key, top[1])
        elif tied:
            # Nothing separates the leaders, so whichever won, won by accident.
            p.ask(key, "%s: nothing separates %s -- which are you WRITING?"
                  % (key, " and ".join([top[1]] + [c[1] for c in tied[:2]])),
                  top[1])
    images = p.candidates("target.image")
    if not images:
        # NO CANDIDATE AT ALL is the FRESH project's branch: nothing here names
        # an original yet, which is why there is nothing to rank. It asked for
        # `target.image` and so sent every new single-image project to the
        # narrow key -- the same shape as the register, one answer over.
        p.ask("target.original",
              "which file is the measurement target -- the original you are "
              "rebuilding -- and which three-digit part do its @asm markers "
              "carry? The answer is a [target.original] table keyed by that "
              "part. Every instrument reads this map; there is no "
              "single-image key, so one original states its path in a "
              "one-row table",
              '{ "000" = "ref/YOUR-ORIGINAL.bin" }')
    elif len(images) > 2 and not any(c[2] == ROLE for c in images):
        # Several candidates and nothing calling any of them the target: this is
        # very likely a project with SEVERAL originals, which wants a map.
        p.ask("target.original",
              "%d candidate originals and no script calls any of them the "
              "target. The answer is a [target.original] map keyed by the "
              "three-digit part each one's @asm markers carry -- one row per "
              "original. This is the shape the kit's instruments read; there "
              "is no single-image key to fall back on."
              % len(images), None)
    else:
        # ONE ORIGINAL, AND THE MAP IS STILL THE ANSWER TO WRITE. Four
        # instruments read `target.original` -- emit, routines, rtl and x87 --
        # and this program mentioned it only for a project with several
        # numbered parts, so a single-image project was told about the narrow
        # key and never about the general one. `target.image` has since been
        # retired outright: it asked "the original", which a project with
        # several cannot answer, so there is one key rather than two and no
        # derivation between them.
        #
        # ASKED, not offered, because the part number is a decision even when
        # it carries no information: a marker's part field is three digits
        # whatever the project's shape, so somebody has to say which three.
        # `000` is the default and the only reason to choose otherwise is
        # provenance -- a part that shipped under a number of its own.
        winner = images[0][1]
        p.rows = [r for r in p.rows if r[0] != "target.image"]
        p.ask("target.original",
              "one original (%s) -- which three-digit part do its @asm markers "
              "carry? The answer is a [target.original] table keyed by that "
              "part -- one row, and the path is stated once" % winner,
              '{ "000" = "%s" }' % winner)
    # NO BRANCH WRITES `target.image`, and this is what makes that true
    # rather than a property of three branches each remembering. The key was
    # retired: it asked "the original", which a project with nine of them
    # cannot answer, and every instrument reads `target.original` now.
    p.rows = [r for r in p.rows if r[0] != "target.image"]
    return p, adopting


def read_existing(root):
    f = root / "kit.toml"
    if not f.is_file():
        return None
    with io.open(f, "rb") as fh:
        data = tomllib.load(fh)
    flat = {}
    for section, body in data.items():
        if isinstance(body, dict):
            for k, v in body.items():
                flat["%s.%s" % (section, k)] = v
        else:
            flat[section] = body
    return flat


def main(argv):
    root = pathlib.Path(next((a for a in argv if not a.startswith("-")),
                             os.getcwd())).resolve()
    p, adopting = propose(root)

    print("kit setup -- %s" % root)
    print("MODE: %s\n" % ("ADOPTING -- %d script(s) of its own to read"
                          % len(project_scripts(root)) if adopting
                          else "NEW -- no scripts to read, so everything is asked"))

    print("PROPOSED, strongest evidence first:")
    for key in p.keys():
        best = p.best(key)
        others = [r for r in p.rows if r[0] == key and r is not best]
        value = best[1] if isinstance(best[1], str) else "%d entry(s)" % len(best[1])
        print("  %-18s %-30s %-18s %s" % (key, value, best[2], best[3]))
        for r in others[:3]:
            v = r[1] if isinstance(r[1], str) else "%d entry(s)" % len(r[1])
            print("  %-18s   also: %-26s %-18s %s" % ("", v, r[2], r[3]))

    print("\nASKED -- %d, and none of them is guessable:" % len(p.questions))
    for key, q, default in p.questions:
        print("  %-18s %s%s" % (key, q, "  [%s]" % default if default else ""))

    kit = pathlib.Path(__file__).resolve().parent
    wanted = keys_the_kit_asks_for(kit)
    covered = set(p.keys()) | {k for k, _, _ in p.questions}
    gap = sorted(set(wanted) - covered)
    if gap:
        print("\nTHE KIT ALSO ASKS FOR THESE, and this program does neither "
              "propose nor ask about them:")
        for key in gap:
            print("  %-22s wanted by %s" % (key, ", ".join(sorted(wanted[key]))))
        print("  A gap here is a to-do, not a silence -- a config missing one of"
              " these fails on the command that needs it.")
    # AGAINST THE PROJECT'S OWN ANSWERS, not against what this program asked
    # about. Testing coverage here was a check that could not fail: the same
    # change that makes the register always ASKED makes it always covered, so
    # the branch was dead on the day it was written. What is worth refusing is
    # an INSTALLED config that does not answer a required key -- the condition
    # two consumers were actually in.
    installed = read_existing(root)
    if installed is not None:
        unanswered = sorted(k for k in REQUIRED if k not in installed)
        if unanswered:
            # Reported apart from the to-do list above, and the difference is
            # the whole point. That list ran to twelve keys, most genuinely
            # optional, and the one meaning "this project has no ratchet" read
            # exactly like the one meaning "no shared assembler".
            print("\nREQUIRED, AND THIS PROJECT'S kit.toml DOES NOT ANSWER "
                  "IT -- nothing here can hold a measurement:")
            for key in unanswered:
                print("  %-22s %s" % (key, REQUIRED[key]))
            return 2

    if "--check" in argv:
        have = read_existing(root)
        if have is None:
            print("\nCHECK: no kit.toml here to compare against")
            return 1
        print("\nCHECK against the kit.toml already here:")
        agree = 0
        asked = {k for k, _, _ in p.questions}
        judged = 0
        recommended = []
        unproposed = []
        for key in sorted(set(have) | set(p.keys())):
            best = p.best(key)
            mine = best[1] if best else None
            theirs = have.get(key)
            if best is None and key in asked:
                # Not a disagreement: this value is not guessable, which is why
                # it is asked. Reporting it as a miss would make the tool look
                # wrong for being right.
                print("  %-18s %-28s asked, not guessed" % (key, str(theirs)[:28]))
                continue
            judged += 1
            picked = selects(root, have, key, mine, theirs)
            if picked is not None:
                ok = picked
            elif isinstance(mine, list) or isinstance(theirs, list):
                ok = sorted(mine or []) == sorted(theirs or [])
            else:
                ok = str(mine) == str(theirs)
            if ok and best:
                agree += 1
            if ok:
                note = "agrees"
            elif theirs is None:
                # Not a disagreement: the project says nothing, so this
                # is a RECOMMENDATION. One found a real gap -- a project
                # whose census could not run for want of this very key.
                note = "MISSING here; recommend %s (%s)" % (mine, best[2])
                recommended.append(key)
                judged -= 1        # a recommendation is not a judgement
            elif best is None:
                # NOT A JUDGEMENT EITHER, for the same reason as `asked`
                # above: the wizard made no claim about this key, so
                # counting it as a miss scores the tool on questions it
                # never answered. It read "PROPOSED None (not proposed)",
                # which says no proposal was made and then counts it as a
                # wrong one.
                #
                # This is why the figure drifted from a documented 8 of 8
                # to 6 of 13 without the wizard getting worse: the projects
                # grew keys it has no proposal for -- five of which it
                # names in its own `wanted by` list -- and each new one
                # became a counted failure.
                note = "present here; this wizard proposes nothing for it"
                unproposed.append(key)
                judged -= 1
            else:
                note = "PROPOSED %s" % (mine,)
            print("  %-18s %-28s %s" % (key, str(theirs)[:28], note))
        print("\n  %d of %d proposed key(s) agree" % (agree, judged))
        if recommended:
            print("  %d key(s) this project does not answer at all: %s"
                  % (len(recommended), ", ".join(recommended)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
