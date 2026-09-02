"""Predict our link order from the `uses` graph, and diff it against the original's.

TP6 LAYS SEGMENTS OUT IN REVERSE DFS POST-ORDER over the `uses` graph, with each
unit's clauses walked in DECLARATION order and the interface clause before the
implementation one. That rule is not documented anywhere; it was derived here by
simulating candidate rules against a real `--sw=/GS` map and keeping the one that
reproduced all thirty-two entries exactly. Reverse PRE-order also looks plausible and
is wrong -- it transposes VTCMD/FILEUTIL/CMDLINE, which is the cheapest way to tell
the two apart if this ever needs re-deriving.

WHY IT MATTERS TWICE OVER. The order fixes the segment NUMBERS, so `1a17` only really
becomes segment `1a17` when the order is the original's (risk 3). And the same order
lays out DGROUP, so it has to be right before any variable address can be compared
(risk 1).

WHAT THE TOOL IS FOR is the CONSTRAINT check rather than the prediction. The original's
order is known exactly -- it is the segment addresses read backwards -- so every
`uses` edge in the tree can be tested against it: if U uses V then V must finish before
U. An edge that fails is a dependency the original CANNOT have had, and that is a
finding about the original's source rather than about our order. Back edges are exempt:
a cycle's back edge is skipped by the DFS, which is why SongUnit finishes AFTER the two
loader units it uses.

    python v1.31b/linkorder.py            check the constraints and diff the order
"""
import io
import re
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import project                                    # noqa: E402

try:
    import tomllib
except ModuleNotFoundError:                       # pragma: no cover -- 3.11+
    import tomli as tomllib                       # type: ignore




def uses_graph(src, unitname):
    """unit name -> its uses, interface clause first, in declaration order."""
    g = {}
    for f in sorted(src.glob('*.PAS')):
        t = f.read_text(encoding='latin-1')
        t = re.sub(r'\{[^}]*\}', ' ', t, flags=re.S)
        t = re.sub(r'\(\*.*?\*\)', ' ', t, flags=re.S)
        deps = []
        for m in re.finditer(r'\buses\b(.*?);', t, re.S | re.I):
            for u in m.group(1).split(','):
                u = u.strip().upper()
                if u and u not in deps:
                    deps.append(u)
        name = unitname.get(f.stem.upper(), f.stem.upper())
        g[name] = [unitname.get(d, d) for d in deps]
    # the RTL units we never compile, so the walk terminates
    for rtl in ('DOS', 'OBJECTS', 'SYSTEM'):
        g.setdefault(rtl, [])
    return g


def predict(g, root):
    """Reverse DFS post-order. `grey` is what makes a back edge a no-op.

    `root` is the main program unit and is REQUIRED. It used to default to one
    target's, and the single caller never passed it -- so the default was not a
    fallback, it was the value, and this tool answered a documented question
    wrongly in any project that was not that one.
    """
    finished, grey, order = set(), set(), []

    def walk(u):
        grey.add(u)
        for v in g.get(u, []):
            if v not in finished and v not in grey:
                walk(v)
        grey.discard(u)
        finished.add(u)
        order.append(u)

    walk(root)
    out = list(reversed(order))
    return out + ['SYSTEM']      # the RTL is appended, never reached by a `uses`


def check_constraints(g, order, noseg):
    """Every `uses` edge the original's order forbids. Back edges excluded."""
    pos = {n: i for i, n in enumerate(reversed(order))}        # finish index
    bad = []
    for u, deps in g.items():
        if u not in pos:
            continue
        for v in deps:
            if v not in pos or v in noseg:
                continue
            # a back edge: V also (transitively) uses U, so the DFS skips this one
            if u in g.get(v, []):
                continue
            if pos[v] > pos[u]:
                bad.append((u, v, pos[u], pos[v]))
    return bad


def read_link(path):
    """The unit-name map, the no-segment set and the original's order.

    All three were constants. The order was ALSO a constant in the map-length
    tool, as (segment, name) pairs, and the two had drifted -- see link.toml's
    header for what that cost. One list, read by both.
    """
    with io.open(path, "rb") as fh:
        cfg = tomllib.load(fh)
    main_unit = cfg.get("main_unit")
    if not main_unit:
        raise SystemExit(
            "%s does not answer `main_unit` -- the program unit the dependency\n"
            "walk starts from. It was a default parameter in this tool naming one\n"
            "target's main program, and the only caller never passed it, so the\n"
            "default was always the answer. Add it as a top-level key."
            % path)
    return (cfg["unitname"],
            set(cfg["lists"]["noseg"]),
            [s["name"] for s in cfg["segments"]],
            main_unit)


def main(argv=()):
    args = [a for a in argv if not a.startswith('-')]
    if not args:
        sys.stdout.write("usage: linkorder.py LINK.toml" + chr(10))
        return 2
    unitname, noseg, order, main_unit = read_link(args[0])
    try:
        src = project.path("layout.src")
    except project.Missing as exc:
        return project.complain(exc)
    g = uses_graph(src, unitname)

    print("=== `uses` edges the ORIGINAL'S ORDER FORBIDS ===")
    bad = check_constraints(g, order, noseg)
    if not bad:
        print("  none -- every dependency in the tree can be satisfied by the")
        print("  original's order, so the order is reachable from the uses clauses.")
    for u, v, fu, fv in bad:
        print("  %-14s uses %-14s but %s finishes at %d and %s only at %d"
              % (u, v, u, fu, v, fv))
        print("  %14s %s CANNOT be a dependency of %s in the original."
              % ('', v, u))

    print()
    print("=== PREDICTED order vs the ORIGINAL'S ===")
    ours = [u for u in predict(g, main_unit) if u not in noseg]
    print("%-4s %-16s %-16s" % ("", "predicted", "original"))
    for i in range(max(len(ours), len(order))):
        a = ours[i] if i < len(ours) else ''
        b = order[i] if i < len(order) else ''
        print("%-4d %-16s %-16s %s" % (i, a, b, '' if a == b else '  <-- differs'))
    same = sum(1 for a, b in zip(ours, order) if a == b)
    print("\n%d of %d positions agree" % (same, len(order)))


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]) or 0)
