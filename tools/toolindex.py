"""The toolkit's inventory, generated from the tools rather than typed beside them.

WHY THIS EXISTS. `tools/README.md` and `WORKING.md` both carried a hand-written
count of the programs here. Measured on 1 Sep 2026: both said "forty-nine" and
there were 73, one README table summed to 52 while naming 51, and **17 tools
were named in neither document** -- every one of them added over six days while
the inventory sat still. The inventory was not merely wrong; nothing existed
that could have kept it right, which is the difference between a mistake and a
defect.

The rule it breaks is already written down -- a measured value never goes in a
document -- and a count of files is as measured as a byte comparison. So this
generates the inventory the way the wiki's indexes are generated, and `--check`
belongs on the list a session runs before committing.

WHAT IT DOES NOT DO. It does not describe what a tool is FOR beyond the tool's
own first docstring line, and it does not group tools by the question you have.
That grouping is judgement, it lives in `WORKING.md`, and it stays hand-written:
generating it would mean inventing a taxonomy out of file paths, which is how a
listing gets mistaken for a decision. What this removes from those documents is
only the arithmetic.

WHY IT LIVES HERE and not in `wikitools/`. That folder looks after the OKF
bundle. This looks after the toolkit, which puts it beside the other programs
that are about the kit or the environment rather than about a target.

    python kit/tools/toolindex.py            print the inventory
    python kit/tools/toolindex.py --write    write it into tools/README.md
    python kit/tools/toolindex.py --check    fail if what is written is stale
"""
import io
import pathlib
import re
import sys

BEGIN = "<!-- generated:inventory -->"
END = "<!-- /generated:inventory -->"

# Folder order is the dependency order, not alphabetical: substrate knows
# nothing about Pascal, pascal builds on it, wikitools is neither, and the root
# holds what is about the kit itself.
ORDER = ("substrate", "pascal", "wikitools", "")

BLURB = {
    "substrate": "Reading DOS and 16-bit binaries. Should work against a C or assembler target too.",
    "pascal": "True only of Borland Pascal: `.TPU` structure, DGROUP layout, RTL byte patterns.",
    "wikitools": "Looking after the wiki bundle: conformance, our profile, and the generators.",
    "": "About the kit or the session rather than about any target.",
}

SKIP_PARTS = ("__pycache__",)


def summary(path):
    """The tool's own first docstring line, or a stated absence.

    Deliberately the FIRST LINE and not a summary of the file: the line is the
    tool's own claim about itself, so a wrong entry here is a wrong docstring,
    which is a defect in one place rather than a disagreement between two.
    """
    text = io.open(path, encoding="utf-8", newline="").read()
    # The prefix group is not decoration. Two tools open with `r"""` and the
    # first version of this matched only `"""`, so it reported them as having
    # no docstring -- and would have written that claim into the README as a
    # generated fact. A generator's extraction is as much a measurement as
    # anything it prints, and this one was wrong about the files rather than
    # the files being wrong.
    m = re.search(r'^\s*(?:#![^\n]*\n)?\s*[rRuUbBfF]*"""(.*?)(?:\n|""")', text, re.S)
    if m is None:
        return None
    line = " ".join(m.group(1).split()).strip()
    return line or None


def collect(root):
    found = {}
    for path in sorted(root.rglob("*.py")):
        if any(p in SKIP_PARTS or p.endswith(".egg-info") for p in path.parts):
            continue
        folder = path.parent.name if path.parent != root else ""
        found.setdefault(folder, []).append((path.stem, summary(path)))
    return found


def render(found):
    total = sum(len(v) for v in found.values())
    lines = [BEGIN,
             "",
             "**%d programs.** This table is generated from each tool's own first"
             " docstring line by `toolindex.py`; `WORKING.md` groups them by the"
             " question you have, which is the useful way in." % total,
             ""]
    for folder in ORDER:
        rows = found.get(folder)
        if not rows:
            continue
        name = (folder + "/") if folder else "beside them"
        lines.append("### `%s` -- %d" % (name, len(rows)))
        lines.append("")
        lines.append("%s" % BLURB.get(folder, ""))
        lines.append("")
        lines.append("| tool | what it says it does |")
        lines.append("|---|---|")
        for stem, text in rows:
            if text is None:
                lines.append("| `%s` | **no module docstring** |" % stem)
            else:
                lines.append("| `%s` | %s |" % (stem, text.replace("|", "\\|")))
        lines.append("")
    lines.append(END)
    return "\n".join(lines) + "\n"


def main(argv):
    here = pathlib.Path(__file__).resolve().parent
    found = collect(here)
    block = render(found)
    readme = here / "README.md"

    # A tool with no docstring is reported OUT LOUD rather than only as a table
    # cell, because the cell is easy to skim past and the claim is strong: this
    # kit's convention is that every tool carries the finding that produced it.
    # It is also where this program's own extraction bug showed, so a silent
    # count here would hide the next one.
    missing = [stem for rows in found.values() for stem, text in rows if text is None]
    if missing:
        sys.stdout.write("  %d tool(s) with no first docstring line: %s\n"
                         % (len(missing), ", ".join(sorted(missing))))

    if "--write" not in argv and "--check" not in argv:
        sys.stdout.write(block)
        return 0

    text = io.open(readme, encoding="utf-8", newline="").read()
    if BEGIN not in text or END not in text:
        sys.stdout.write("%s carries no %s marker -- add it where the inventory "
                         "should go\n" % (readme.name, BEGIN))
        return 1
    head, rest = text.split(BEGIN, 1)
    new = head + block.rstrip("\n") + rest.split(END, 1)[1]

    if new == text:
        sys.stdout.write("tools/README.md inventory is current -- %d program(s)\n"
                         % sum(len(v) for v in found.values()))
        return 0
    if "--check" in argv:
        sys.stdout.write("tools/README.md inventory is STALE -- regenerate with "
                         "toolindex.py --write\n")
        return 1
    io.open(readme, "w", encoding="utf-8", newline="\n").write(new)
    sys.stdout.write("tools/README.md inventory rewritten -- %d program(s)\n"
                     % sum(len(v) for v in found.values()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
