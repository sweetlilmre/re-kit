"""The artefact-tier instrument: is our whole build the original's bytes?

The register had rows for routines (byte-locked via markers), for what a
person watched, and for the plan -- but an R7 claim, "this rebuilt
executable is byte-identical to the 1994 binary", had no slot. It lived in
prose, so an edit that quietly broke the identity would fail nothing. This
is the slot, and the check.

An artefact row is MEASURED here, never hand-edited. Two comparisons
exist, because the artefacts differ (the wiki's zero-byte lesson applies
at file scale too):

  file        every byte of both files
  load-image  our whole file against the original's MZ load image -- for
              originals that carry appended debug info the loader never
              reads and a rebuild does not regenerate
  image       BOTH sides' headers stripped, and only the bytes DOS loads
              compared -- for a rebuild whose program bytes are identical
              and whose MZ header is not

`image` was added because two consumers had a result neither other mode
could hold. Their rebuilds' program bytes were identical to the originals'
-- every differing byte fell inside the MZ header, in a relocation table a
linker is free to order differently -- so `file` refused the row and
`load-image`, which truncates rather than skips a header, refused it too. An
R7 claim that no mode can record is a claim that lives in prose, which is
the exact condition this instrument was written to end.

ITS BLIND SPOT IS THE HEADER, and that is the trade rather than an
oversight. `image` cannot see a wrong entry point, a wrong initial stack, a
wrong minimum allocation or a relocation the loader will apply to the wrong
word -- every one of which breaks the program while leaving the compared
bytes equal. A row recorded with `image` says the program bytes match; it
does not say the file runs. Use `file` where a rebuild can reproduce the
header, and expect the weaker claim when it cannot.

The check re-hashes both sides every run: a claim is only as good as the
bytes on disk today. A mismatch on a recorded row FAILS, with the escape
where it always is -- lower the target with a reason, never edit the
measurement.

    python kit/tools/pascal/artefact.py status.toml --check
    python kit/tools/pascal/artefact.py status.toml --record TPSYCHO \\
        --ours run/TPSYCHO.EXE --original bin/PSYCHO.EXE --compare file --write
"""
import hashlib
import io
import os
import struct
import subprocess
import sys

import pathlib

# Both invocation styles are first-class, so both need a path. parents[1]
# is kit/tools, which is where `project` lives; parents[0] is this tier's
# own folder, which Python only adds by itself when the file is run as a
# script -- so without it `from pascal import ratchet` cannot find the
# sibling `register`.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[0]))
import register                                   # noqa: E402
import project                                    # noqa: E402

COMPARES = ("file", "load-image", "image")


def head_commit():
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"],
                             capture_output=True, text=True, encoding="utf-8")
        return out.stdout.strip()[:12] if out.returncode == 0 else "unknown"
    except OSError:
        return "unknown"


def load_image(path):
    d = io.open(path, "rb").read()
    cblp, cp = struct.unpack_from("<HH", d, 2)
    return d[:(cp - 1) * 512 + (cblp or 512)]


def program_image(path):
    """Only the bytes DOS loads: the declared image, minus the MZ header.

    load_image() above truncates a file to its declared length and keeps the
    header; this skips it. The two are different questions and the names are
    one word apart, so the docstrings carry the difference: that one is about
    bytes appended AFTER the image, this one about the header BEFORE it.
    """
    d = io.open(path, "rb").read()
    cblp, cp = struct.unpack_from("<HH", d, 2)
    hdr = struct.unpack_from("<H", d, 8)[0] * 16
    return d[hdr:(cp - 1) * 512 + (cblp or 512)]


def sides(row):
    if row["compare"] == "image":
        # BOTH sides, unlike the other two modes: the header is excluded from
        # the claim, so excluding it from one side only would compare a
        # program against a header and call the difference a mismatch.
        return program_image(row["ours"]), program_image(row["original"])
    ours = io.open(row["ours"], "rb").read()
    orig = (load_image(row["original"]) if row["compare"] == "load-image"
            else io.open(row["original"], "rb").read())
    return ours, orig


def record(status, key, ours, original, compare):
    if compare not in COMPARES:
        return "compare must be one of %s" % "/".join(COMPARES)
    for p in (ours, original):
        if not os.path.exists(p):
            return "%s does not exist" % p
    row = {"ours": ours, "original": original, "compare": compare}
    a, b = sides(row)
    if a != b:
        return ("%s: the bytes DIFFER (%d vs %d bytes) -- an artefact row "
                "records a measured identity, and this is not one" %
                (key, len(a), len(b)))
    row["sha256"] = hashlib.sha256(a).hexdigest()
    row["achieved"] = "R7"
    row["target"] = "R7"
    row["measured_at"] = head_commit()
    status.setdefault("artefact", {})[key] = row
    return None


def check(status):
    rows = status.get("artefact", {})
    if not rows:
        sys.stdout.write("  no artefact rows. Nothing claims R7, stated "
                         "rather than implied.\n")
        return 0
    failures = 0
    for key in sorted(rows):
        row = rows[key]
        try:
            a, b = sides(row)
        except OSError as e:
            sys.stdout.write("  FAIL %-8s cannot read a side: %s\n" % (key, e))
            failures += 1
            continue
        ok = a == b and hashlib.sha256(a).hexdigest() == row.get("sha256")
        if ok:
            sys.stdout.write("  %-8s %-10s %s == %s  R7 holds\n"
                             % (key, row["compare"], row["ours"],
                                row["original"]))
        else:
            failures += 1
            sys.stdout.write(
                "  FAIL %-8s NO LONGER IDENTICAL to %s. The R7 claim was "
                "measured at %s; to accept a regression, lower the target "
                "with a reason -- do not edit the row.\n"
                % (key, row["original"], row.get("measured_at", "?")))
    sys.stdout.write("  %d artefact(s), %d failing.\n" % (len(rows), failures))
    return 1 if failures else 0


def main(argv):
    # A flag's VALUE is not a positional -- see project.positionals.
    args = project.positionals(argv[1:], ('--record', '--ours', '--original', '--compare'))
    if not args and any(a.startswith("--") for a in argv[1:]):
        # A flag but no register: ask the project where its register is.
        try:
            args = [str(project.path("layout.register"))]
        except project.Missing as exc:
            return project.complain(exc)
    if not args:
        sys.stdout.write(
            "usage: artefact.py <status.toml> --check\n"
            "       artefact.py <status.toml> --record KEY --ours EXE"
            " --original BIN --compare file|load-image [--write]\n")
        return 2
    path = args[0]
    status = register.load(path)

    def opt(name, default=None):
        flag = "--" + name
        return argv[argv.index(flag) + 1] if flag in argv else default

    if "--check" in argv:
        return check(status)
    if opt("record"):
        err = record(status, opt("record"), opt("ours", ""),
                     opt("original", ""), opt("compare", ""))
        if err:
            sys.stdout.write("  REFUSED: %s\n" % err)
            return 1
        if "--write" in argv:
            register.write(path, status)
            sys.stdout.write("  recorded %s in %s\n" % (opt("record"), path))
        else:
            sys.stdout.write("  ok -- not written, pass --write\n")
        return 0
    return main([argv[0]])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
