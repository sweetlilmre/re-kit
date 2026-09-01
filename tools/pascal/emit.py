r"""Emit compiled-in data back out as Borland Pascal typed constants.

    python kit/tools/pascal/emit.py EMIT.toml
    python kit/tools/pascal/emit.py EMIT.toml --only P3SINE.INC
    python kit/tools/pascal/emit.py EMIT.toml --check    compare, write nothing

**RUN `--check` BEFORE REGENERATING.** What this writes can be hand-edited after
the fact -- most often by a documentation pass, which touches the prose at the
top and not the config that produced it -- and regenerating then silently
reverts that work. See `check()` for the case this is drawn from and why no other
instrument in a reconstruction can see it.

WHY THIS IS NEEDED AT ALL, and it is the reason the reconstruction is not just a
skeleton: anything in DGROUP's INITIALISED region was a typed constant in the
original source -- `const X : T = (...)`. A plain `var` lands in BSS and is not
stored in the executable at all. So data readable out of the file image must
have been declared with an initialiser, and without those declarations the
source compiles to a different binary.

**THE NESTED-PARENTHESIS RULE.** A multidimensional typed constant needs nested
parentheses per row -- `((x, y, z), (x, y, z), ...)` -- and Turbo Pascal rejects
a flat list for one. Getting this wrong produces a compiler error a long way
from its cause, which is why the formatter takes a group size rather than
leaving each caller to lay rows out.

WHAT IS GENERATED SAYS SO, AND SAYS WHAT MADE IT. That is not politeness: the
emitter is often the only record of which binary a table came from and at which
offset, so a generated file that does not name its source cannot have its
emitter retired. One project made that a per-file gate before deleting any
emitter, and six passed it.

WHAT IS THE PROJECT'S: every offset, every length, every type name, and the
prose at the top of each file. All of it lives in the config, because all of it
would have to be rewritten for another binary. What is here is the formatter and
the reading.
"""
import io
import re
import shutil
import struct
import sys
import tempfile
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import project                                    # noqa: E402
from substrate.mzinfo import parse                # noqa: E402

try:
    import tomllib
except ModuleNotFoundError:                       # pragma: no cover -- 3.11+
    import tomli as tomllib                       # type: ignore

PER_LINE = 12

# How to read one element, and how wide it is.
READERS = {
    "byte":  (1, lambda raw, at: raw[at]),
    "word":  (2, lambda raw, at: struct.unpack_from("<H", raw, at)[0]),
    "int":   (2, lambda raw, at: struct.unpack_from("<h", raw, at)[0]),
}


def fmt_array(name, typ, values, per_line=PER_LINE, hexfmt=False, group=None):
    """One typed constant, laid out so Turbo Pascal will accept it.

    `group` is the nested-parenthesis rule: group=3 emits ((x, y, z), ...),
    which is what a multidimensional constant requires and what a flat list of
    the same numbers is rejected for.
    """
    def one(v):
        return "$%04X" % v if hexfmt else str(v)

    lines = ["  %s : %s = (" % (name, typ)]
    if group is None:
        for i in range(0, len(values), per_line):
            body = ", ".join(one(v) for v in values[i:i + per_line])
            lines.append("    " + body
                         + ("," if i + per_line < len(values) else ""))
    else:
        rows = [values[i:i + group] for i in range(0, len(values), group)]
        per = max(1, per_line // (group + 1))
        for i in range(0, len(rows), per):
            body = ", ".join("(" + ", ".join(one(v) for v in r) + ")"
                             for r in rows[i:i + per])
            lines.append("    " + body + ("," if i + per < len(rows) else ""))
    lines.append("  );")
    return "\n".join(lines)


def dgroup_base(root, originals, part, seg, first_para):
    h = parse(root / originals[part])
    return h["raw"], h["hdrsize"] + seg * 16 - first_para * 16


def values_of(raw, base, spec):
    """One array's values, per its element type and stride.

    `stride` covers the case a group of elements is read together -- three
    signed words per point, say -- where the count is points and not numbers.
    """
    width, read = READERS[spec["element"]]
    per = spec.get("group", 1)
    out = []
    for i in range(spec["count"]):
        at = base + spec["offset"] + i * width * per
        for k in range(per):
            out.append(read(raw, at + k * width))
    return out


def code_only(data):
    """The file with every Pascal comment removed, for comparing DATA alone.

    Nested braces are stripped from the inside out, because Turbo Pascal does not
    nest `{ }` and a lone inner brace would otherwise swallow the rest of a file.
    """
    text = data.decode("latin-1")
    while True:
        stripped = re.sub(r"\{[^{}]*\}", "", text, flags=re.S)
        if stripped == text:
            break
        text = stripped
    return re.sub(r"\s+", " ", text).strip()


def check(cfg_path):
    """Regenerate into a temporary directory and compare against the tree.

    WHY A GENERATED FILE NEEDS THIS AT ALL. The banner this tool writes -- named
    binary, named offset, `do not edit` -- is a claim about the RELATIONSHIP
    between a config and a file, and nothing else in a reconstruction measures
    relationships. A build reads one file and answers a question about that file;
    so does a byte comparison, and so does a whole-binary artefact check. None of
    them asks whether the generator still produces what is committed.

    That is not theoretical. On one project every one of seven generated includes
    had been hand-edited months earlier to strip reverse-engineering apparatus
    out of the documentation copy, and the emitters were not given the same edit
    -- so running one would have reverted a closed ticket, in seven files at
    once, and the only thing preventing it was nobody happening to run it. It
    stayed invisible because the divergence was comment-only and the data
    identical: comments reach no compiler, so the build stayed byte-identical and
    every artefact row went on holding. The wiki carries the general form under
    `generated-means-checked`.

    THE TWO KINDS OF DIFFERENCE ARE NOT THE SAME WEIGHT, which is why this
    classifies rather than just diffing. Comments-only means the config and the
    tree disagree about wording, and either side may be the one to keep -- a
    judgement for whoever knows why the edit was made. A DATA difference means a
    byte-identical build is resting on committed copies this tool no longer
    produces, and regenerating over them would move real bytes.

    It writes nothing, so it is safe to run before deciding anything.
    """
    with io.open(cfg_path, "rb") as fh:
        cfg = tomllib.load(fh)
    try:
        root = project.find()
        tree = root / cfg["out"]
    except project.Missing as exc:
        return project.complain(exc)

    names = [spec["name"] for spec in cfg["file"]]
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="emitcheck-"))
    try:
        rc = emit(cfg_path, out_override=tmp, quiet=True)
        if rc:
            return rc
        bad = data_bad = 0
        sys.stdout.write("regenerated into a temporary directory and compared "
                         "against %s\n\n" % tree.as_posix())
        for name in names:
            a, b = tree / name, tmp / name
            if not a.exists():
                sys.stdout.write("  %-16s MISSING from the tree\n" % name)
                bad += 1
                continue
            av, bv = a.read_bytes(), b.read_bytes()
            if av == bv:
                sys.stdout.write("  %-16s identical\n" % name)
                continue
            bad += 1
            if code_only(av) == code_only(bv):
                sys.stdout.write("  %-16s DIFFERS in comments only -- the data "
                                 "is identical, so no build changes\n" % name)
            else:
                data_bad += 1
                sys.stdout.write("  %-16s DIFFERS IN THE DATA -- this changes "
                                 "what the compiler sees\n" % name)
        sys.stdout.write("\n  %d of %d file(s) differ from what this config "
                         "produces.\n" % (bad, len(names)))
        if data_bad:
            sys.stdout.write(
                "  %d of them differ in DATA. Do not regenerate over the tree "
                "until that is\n  understood: a byte-identical build may be "
                "resting on the committed copies.\n" % data_bad)
        elif bad:
            sys.stdout.write(
                "  All comment-only. Either the tree was edited by hand and this "
                "config needs\n  the same edit, or the config changed and the "
                "tree needs regenerating. They\n  disagree, and regenerating "
                "would overwrite the tree's wording without saying so.\n")
        else:
            sys.stdout.write("  The tree is exactly what this config writes.\n")
        return 1 if bad else 0
    finally:
        shutil.rmtree(str(tmp), ignore_errors=True)


def emit(cfg_path, only=None, out_override=None, quiet=False):
    with io.open(cfg_path, "rb") as fh:
        cfg = tomllib.load(fh)
    try:
        root = project.find()
        originals = project.get("target.original")
        first = project.get("target.first_para", quiet=True)
        out_dir = out_override or (root / cfg["out"])
    except project.Missing as exc:
        return project.complain(exc)

    out_dir.mkdir(parents=True, exist_ok=True)
    total = 0
    for spec in cfg["file"]:
        if only and spec["name"] != only:
            continue
        raw, base = dgroup_base(root, originals, spec["part"],
                                int(spec["segment"]), first)
        body = []
        for arr in spec["array"]:
            vals = values_of(raw, base, arr)
            if arr.get("comment_offset", True):
                body.append("  { DS:$%04X }" % arr["offset"])
            body.append(fmt_array(arr["name"], arr["type"], vals,
                                  arr.get("per_line", PER_LINE),
                                  arr.get("hex", False), arr.get("group")))
            total += len(vals)
        # The header names the emitter and the binary. A generated file that
        # does not say where its bytes came from cannot have its emitter
        # retired, because the emitter is then the only record.
        head = spec["header"].rstrip("\n")
        head += ("\n  Generated by kit/tools/pascal/emit.py from %s at "
                 "DS:$%04X -- do not edit. }"
                 % (originals[spec["part"]], int(spec["segment"])))
        text = head + "\n\nconst\n" + "\n".join(body) + "\n"
        io.open(out_dir / spec["name"], "w", encoding="ascii",
                newline="\n").write(text)

    # THE FILES THIS RUN WROTE, and not a listing of the directory. It used to
    # walk out_dir, which presents every neighbour as though this config had
    # produced it -- on a target where a second emitter writes into the same
    # folder that reads as an overlap between two tools, and one reader spent a
    # detour ruling out a conflict that was never there. A report that names
    # more than it measured is the same defect as one that measures nothing.
    if not quiet:
        for spec in cfg["file"]:
            if only and spec["name"] != only:
                continue
            f = out_dir / spec["name"]
            n = len(io.open(f, encoding="ascii",
                            errors="replace").read().splitlines())
            print("%s  %5d lines" % (f, n))
        print("")
        print("%s values emitted" % format(total, ","))
    return 0


def main(argv):
    args = [a for a in argv if not a.startswith("-")]
    if not args:
        sys.stdout.write("usage: emit.py EMIT.toml [--only FILE.INC] "
                         "[--check]" + "\n")
        return 2
    if "--check" in argv:
        return check(args[0])
    only = None
    if "--only" in argv:
        only = argv[argv.index("--only") + 1]
    return emit(args[0], only)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
