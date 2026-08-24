"""Which routines in a segment are HAND-WRITTEN ASSEMBLER rather than compiled.

Borland Pascal's code generator will not do certain things, ever, and its
built-in assembler does them freely. This scores each routine on six such
signals and prints which ones fired, so the verdict is a list of evidence
rather than a number somebody has to trust.

WHY IT EXISTS. A reconstruction that transcribes hand assembler as Pascal
cannot converge -- the algorithm is not the same algorithm -- and the routine
that taught this corpus the lesson had been read as Pascal for weeks because
its prologue is an ENTER with BP-relative locals. That is not a tell in either
direction: Borland emits its standard frame for an `assembler` procedure that
declares locals, so hand-written code with locals is indistinguishable from
compiled code at the entry point. Every signal here is a thing found INSIDE a
body.

WHAT IT WILL NOT DO. It will not give a routine a probability. Each signal is
reported by name with its evidence, and the verdict is the count -- because the
signals are not independent in any way anybody has measured, and multiplying
them together would invent a precision this has no claim to. `suspect` means
one signal fired and a person should read the routine.

THE SIGNALS, and what each one rests on:

    direction   the store/load direction bit over two-byte register-to-register
                ops. An assembler has one operand order in the source and one
                rule for encoding it; a code generator picks whichever side its
                tree walk made the destination. Wants a count before it speaks,
                and it is the ONLY signal here that can speak for the ABSENCE
                of hand assembler.
    bpscratch   BP written by anything but the prologue. The code generator
                will not clobber its own frame pointer.
    stringops   STOS/LODS/MOVS/SCAS/CMPS or a REP prefix, outside the
                compiler's own value-parameter copy. Move and FillChar are far
                calls into the runtime; they are never inlined.
    segscratch  a value PARKED in a segment register -- `MOV ES, reg` putting a
                general value in and a later `MOV reg, ES` taking it back -- so
                a general register can be borrowed as an index.
    rawinsn     LOOP, JCXZ, XLAT, LAHF, SAHF, STD -- instructions the code
                generator has no construct that emits.
    regargs     a register read before it is written, in the routine's opening
                instructions. No Pascal CALLER can pass an argument in a
                register, so this convicts the caller too.

THREE THINGS THAT LOOK LIKE SIGNALS AND ARE NOT, each measured rather than
reasoned, and each of which produced a false `assembler` verdict before it was
understood:

  * THE COMPILER'S VALUE-PARAMETER COPY. A structured or String value parameter
    is copied into the frame by inline code, and in NEUROSIS.002's DrawText
    that code is:

        MOV BX,SS / MOV ES,BX / MOV BX,DS / CLD / LEA DI,[BP-100h]
        LDS SI,[BP+4] / LODSB / STOSB / XCHG CX,AX / XOR CH,CH
        REP MOVSB / MOV DS,BX

    a segment register read into a general register, a CLD, two string
    instructions and a REP -- on a routine that took a String by value and did
    nothing else unusual. It fired on FOUR compiled routines at IDENTICAL
    offsets, which is what gave it away: a hand-written idiom does not recur to
    the byte across unrelated routines. `copy_prologue` finds it and three
    signals are gated behind it.

  * CLD AND XCHG. Both are in that copy, so both are compiler instructions and
    neither appears in the tables below.

  * PORT I/O. `Port[]` and `PortW[]` compile to IN and OUT, so a routine full
    of them says nothing.

WHAT IT CANNOT SEE:

  * A SHORT ROUTINE MAY HAVE NO EVIDENCE AT ALL, and `no evidence` is a
    different claim from `pascal`. Length is not evidence: an 88-byte hand
    assembler routine with no qualifying op in it at all was called `pascal` by
    an earlier version of this that treated size as having spoken.
  * IT CANNOT NAME THE ASSEMBLER. Borland's built-in assembler and an
    externally assembled `{$L}` object both score as hand-written, which is
    correct and is all this claims. Which one it was is a question for a
    rebuild.
  * A ROUTINE'S BOUNDS COME FROM A PROLOGUE SCAN, so they inherit that scan's
    blind spots -- a routine with NO PROLOGUE AT ALL is invisible here, and
    those exist and are among the most obviously hand-written code in any
    Borland binary. A data table that looks like a prologue gets scored as if
    it were code, so the `called` / `unproven` mark is printed for the same
    reason `prologue.py` prints it.
  * THE LAST ROUTINE IN A SEGMENT overshoots, because its end is the segment's
    end. A body that is too long dilutes a ratio rather than inventing one.

USAGE

    handasm.py SPANS.toml [PART...] [--seg=XXXX] [--min-ops=N] [--all]
    handasm.py SPANS.toml --expect EXPECT.toml     validate against known
                                                   ground truth

`--expect` is how this gets tested, and the expectations live in the HOST
because they are facts about one binary. The file names routines somebody has
already established by hand:

    [expect]
    asm    = ["002 108b:0461"]
    pascal = ["002 108b:0422"]

and the run reports agreement per row, so a signal that stops working is caught
by something other than the person who wrote it.
"""
import io
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[0]))
import project                                    # noqa: E402
import prologue                                   # noqa: E402
import x87                                        # noqa: E402
from substrate import disasm                      # noqa: E402

try:
    import tomllib
except ModuleNotFoundError:                       # pragma: no cover -- 3.11+
    import tomli as tomllib                       # type: ignore


# ---------------------------------------------------------------- the signals

# Opcodes whose reg,reg form differs only in the direction bit. The low member
# of each pair is `r/m <- reg`, the store direction; `| 0x02` is the load.
STORE = (0x88, 0x89, 0x00, 0x01, 0x08, 0x09, 0x10, 0x11, 0x18, 0x19,
         0x20, 0x21, 0x28, 0x29, 0x30, 0x31, 0x38, 0x39)
LOAD = tuple(o | 0x02 for o in STORE)

# How many qualifying ops before `direction` is allowed an opinion, and the
# store share at which it fires. The share sits well above the highest
# compiled routine measured on this corpus and well below an assembler's.
MIN_OPS = 8
STORE_FIRES = 0.90

# How far into a body to look for the compiler's value-parameter copy.
COPY_REACH = 48

OP_MOV_FROM_SREG = 0x8c        # MOV r/m16, sreg
OP_MOV_TO_SREG = 0x8e          # MOV sreg, r/m16
PREFIX_REP = (0xf2, 0xf3)

STRING_INSN = frozenset(("stosb", "stosw", "lodsb", "lodsw", "movsb", "movsw",
                         "scasb", "scasw", "cmpsb", "cmpsw"))

# CLD is NOT here, and that is a correction rather than an omission -- see the
# module docstring. XCHG is absent for the same reason.
RAW_INSN = frozenset(("loop", "loope", "loopne", "jcxz", "xlatb", "xlat",
                      "lahf", "sahf", "std"))

ARG_REGS = ("bx", "cx", "dx", "si", "di")
OPENING = 16          # instructions at the top of a body that `regargs` reads

# Sub-registers share a slot, so a write to CL is a write to CX as far as "was
# this register set before it was read" is concerned. Without this the
# compiler's own `XOR CH,CH` followed by a read of CX reads as an
# uninitialised register, and `regargs` fires on the copy loop.
FAMILY = {}
for _wide, _parts in (("ax", "ah al"), ("bx", "bh bl"), ("cx", "ch cl"),
                      ("dx", "dh dl")):
    FAMILY[_wide] = _wide
    for _p in _parts.split():
        FAMILY[_p] = _wide


def family(name):
    return FAMILY.get(name, name)


def detailed():
    """capstone in 16-bit mode WITH operand detail.

    `disasm.decoder()` turns detail off, which is right for a listing and not
    enough here: `regargs` has to ask which registers an instruction reads and
    writes, and that is only in the detailed form. A second engine is cheaper
    than making every other caller pay for the detail.
    """
    try:
        import capstone
    except ImportError:
        raise SystemExit(
            "handasm needs capstone, and cannot report an empty scan instead:\n"
            "    uv pip install --python .venv/Scripts/python.exe capstone")
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_16)
    md.detail = True
    return md


def resolve_traps(code):
    """Borland's 80x87 emulator traps turned back into 80x87 instructions.

    UNDER `{$E+}` EVERY FLOATING-POINT INSTRUCTION SHIPS AS `INT 34h..3Dh`, and
    those two bytes are not the instruction they replaced, so a linear decode
    across them DESYNCHRONISES and the garbage after them decodes as a
    plausible instruction mix. Not a hypothetical: `scasw` was reported in the
    middle of a compiled routine's floating-point arithmetic and read as a
    hand-assembler string operation, on bytes that are really `WAIT` and
    `FDIV`.

    Reuses `x87.patch`, which is the one place that knows what a Borland trap
    becomes; a second copy of that table here would be the drifted second copy
    the wiki has an observation about. Returns (code, how many were resolved).
    """
    out = bytearray(code)
    n = 0
    i = 0
    while i < len(out) - 1:
        if out[i] == 0xCD:
            new = x87.patch(bytes(out), i)
            if new is not None:
                out[i:i + len(new[0])] = new[0]
                n += 1
                i += len(new[0])
                continue
        i += 1
    return bytes(out), n


def direction(code):
    """(store, load) counts of two-byte register-direct ops.

    Length two and mod=11 together are what make a byte pair unambiguous: a
    longer form carries a displacement whose bytes could be anything, and a
    memory operand has only one legal direction so it carries no signal.
    """
    store = load = 0
    md = disasm.decoder()
    for _, raw, _ in disasm.walk(md, code, 0):
        if len(raw) == 2 and (raw[1] >> 6) == 3:
            if raw[0] in STORE:
                store += 1
            elif raw[0] in LOAD:
                load += 1
    return store, load


def copy_prologue(md, code):
    """How many bytes of the body are the compiler's value-parameter copy.

    Returns the offset one past the copy, or 0 if there is none. The test is
    deliberately narrow -- a `MOV r16, SS` or `MOV r16, DS` inside the opening
    bytes, then a REP string op within a short reach of it -- because a loose
    test here silently blinds the three signals it gates.
    """
    seg_read = None
    for ins in md.disasm(bytes(code[:COPY_REACH]), 0):
        if (ins.bytes[0] == OP_MOV_FROM_SREG and len(ins.bytes) >= 2
                and (ins.bytes[1] >> 6) == 3
                and ins.op_str.split(",")[-1].strip() in ("ss", "ds")):
            seg_read = ins.address
        if seg_read is not None and ins.bytes[0] in PREFIX_REP:
            return ins.address + ins.size
    return 0


def body_signals(code, frame_form):
    """The five body signals over one routine. Returns (fired, copy extent).

    Three of the five are GATED on the compiler's value-parameter copy, which
    emits string instructions, a CLD and a segment-register read of its own.
    `regargs` is not gated but ABANDONED when a copy is present: the copy uses
    BX, CX, SI and DI before the body does, so there is nothing left to learn
    from which register was read first.
    """
    md = detailed()
    frame = 4 if frame_form == "$G+" else 3
    copy = copy_prologue(md, code)
    skip = max(frame, copy)
    fired = {}

    parked = set()          # general registers whose value went into ES
    written = set()
    n = 0
    for ins in md.disasm(bytes(code), 0):
        m = ins.mnemonic
        at = ins.address
        regs_r, regs_w = ins.regs_access()
        names_w = {family(md.reg_name(r)) for r in regs_w}
        names_r = {family(md.reg_name(r)) for r in regs_r}

        if at >= skip:
            if m in STRING_INSN or ins.bytes[0] in PREFIX_REP:
                fired.setdefault("stringops", "%s at +%04x" % (m, at))
            if m in RAW_INSN:
                fired.setdefault("rawinsn", "%s at +%04x" % (m, at))

            # A value PARKED in a segment register needs BOTH halves: `MOV ES,
            # reg` putting a general value in and a later `MOV reg, ES` taking
            # it back. One half alone is the compiler re-establishing a
            # segment, which `MOV r16, SS` and `MOV r16, DS` are every time.
            if (ins.bytes[0] == OP_MOV_TO_SREG and len(ins.bytes) >= 2
                    and (ins.bytes[1] >> 6) == 3 and m == "mov"
                    and ins.op_str.startswith("es,")):
                parked.add(ins.op_str.split(",")[-1].strip())
            if (ins.bytes[0] == OP_MOV_FROM_SREG and len(ins.bytes) >= 2
                    and (ins.bytes[1] >> 6) == 3
                    and ins.op_str.endswith("es")
                    and ins.op_str.split(",")[0].strip() in parked):
                fired.setdefault("segscratch",
                                 "%s %s at +%04x -- put there by an earlier "
                                 "MOV ES" % (m, ins.op_str, at))

            # `POP BP` is the EPILOGUE, not a clobber, and it fired on nine
            # routines before that was noticed -- every `$G-` routine ends
            # with one, and a body bounded by the next prologue always
            # contains its own. A genuine park shows up as the WRITE that put
            # something else in BP, which is the tell worth keeping.
            if ("bp" in names_w
                    and m not in ("leave", "enter", "pop", "ret", "retf")):
                fired.setdefault("bpscratch",
                                 "%s %s at +%04x" % (m, ins.op_str, at))

        if at >= frame and n < OPENING and not copy:
            for r in ARG_REGS:
                if r in names_r and r not in written:
                    fired.setdefault(
                        "regargs",
                        "%s read at +%04x before any write" % (r.upper(), at))
        written |= names_w
        n += 1
    return fired, copy


def score(code, frame_form, min_ops=MIN_OPS):
    """(verdict, fired, note) for one routine body."""
    code, traps = resolve_traps(code)
    store, load = direction(code)
    fired, copy = body_signals(code, frame_form)
    total = store + load
    if total >= min_ops and store / total >= STORE_FIRES:
        fired["direction"] = "%d of %d store direction" % (store, total)

    # LENGTH IS NOT EVIDENCE. Only `direction` can speak for the ABSENCE of
    # hand assembler, and only once it has a count; a long routine that
    # happened to fire nothing is `no evidence`, not `pascal`.
    if len(fired) >= 2:
        verdict = "assembler"
    elif len(fired) == 1:
        verdict = "suspect"
    elif total >= min_ops:
        verdict = "pascal"
    else:
        verdict = "no evidence"

    bits = ["direction %d/%d" % (store, total) if total else "no direction ops"]
    if copy:
        bits.append("value-param copy to +%04x" % copy)
    if traps:
        bits.append("%d x87 trap(s) resolved" % traps)
    return verdict, fired, ", ".join(bits)


def locate(code, window=64):
    """Store-direction share per window, to find an `asm` BLOCK inside Pascal.

    A routine's overall ratio assumes the whole body came from one producer,
    and a Pascal procedure with an `asm ... end` block in it did not. Such a
    routine sits BETWEEN the two bands -- above every compiled routine
    measured and below an assembler's -- and the average hides where the
    block is. Walking the body in windows puts it back.

    A window with no qualifying op prints nothing rather than zero, because
    "no evidence here" and "all load direction here" are different facts and
    printing 0% for the first is the `absence-reads-as-zero` mistake.
    """
    md = disasm.decoder()
    marks = []
    for at, raw, _ in disasm.walk(md, code, 0):
        if len(raw) == 2 and (raw[1] >> 6) == 3:
            if raw[0] in STORE:
                marks.append((at, 1))
            elif raw[0] in LOAD:
                marks.append((at, 0))
    out = []
    for lo in range(0, len(code), window):
        hits = [v for at, v in marks if lo <= at < lo + window]
        if not hits:
            out.append((lo, None, 0))
            continue
        out.append((lo, sum(hits) / len(hits), len(hits)))
    return out


# ---------------------------------------------------------------- the reports

def routines(code):
    """(lo, hi, frame form, called) per routine, bounded by the next prologue."""
    cands = prologue.prologues(code)
    calls = prologue.call_targets(code)
    out = []
    for k, cand in enumerate(cands):
        at, form = cand[0], cand[2]
        hi = cands[k + 1][0] if k + 1 < len(cands) else len(code)
        out.append((at, hi, form, at in calls))
    return out


def report(seg, code, min_ops, show_all):
    rows = routines(code)
    print("  segment %04x -- %d byte(s), %d routine(s)"
          % (seg, len(code), len(rows)))
    withheld = 0
    for lo, hi, form, called in rows:
        # A CANDIDATE NOTHING CALLS IS NOT NECESSARILY CODE. The prologue scan
        # endorses data -- the wiki's `prologue-scan-endorses-data` is the
        # account -- and scoring a table's bytes produces a confident verdict
        # about something that was never an instruction. Withheld by default
        # for the same reason `prologue.py` withholds, and `--all` shows them.
        if not called and not show_all:
            withheld += 1
            continue
        verdict, fired, note = score(code[lo:hi], form, min_ops)
        if not show_all and verdict in ("pascal", "no evidence"):
            continue
        mark = "called  " if called else "unproven"
        print("    %04x:%04x  %-11s %-8s %5d byte(s)  %s"
              % (seg, lo, verdict, mark, hi - lo, note))
        for name in sorted(fired):
            print("        %-11s %s" % (name, fired[name]))
    if withheld:
        print("      (%d candidate(s) nothing calls, withheld -- --all shows "
              "them)" % withheld)


def expectations(cfg, spec_of, blob_of, first, min_ops=MIN_OPS):
    """Validate the signals against routines somebody established by hand."""
    exp = cfg.get("expect", {})
    want = [(k, v) for k in ("asm", "pascal") for v in exp.get(k, [])]
    if not want:
        print("no [expect] rows -- nothing to validate against")
        return 1
    agree = disagree = quiet = unreachable = 0
    print("%-22s %-10s %-12s %s"
          % ("routine", "expected", "verdict", "evidence"))
    print("-" * 82)
    for kind, key in want:
        part, addr = key.split()
        seg_s, off_s = addr.split(":")
        seg, off = int(seg_s, 16), int(off_s, 16)
        spec = spec_of(part)
        bounds = list(spec["segs"]) + [spec["rtl"]]
        k = spec["segs"].index(seg)
        code = prologue.segment(blob_of(part), seg, bounds[k + 1], first)
        rows = [r for r in routines(code) if r[0] == off]
        if not rows:
            # NOT a disagreement. The prologue scan cannot bound a routine
            # that has no prologue, this tool says so in its docstring, and
            # counting a documented blind spot as a failure would make the
            # self-test red for something no signal got wrong.
            print("%-22s %-10s %-12s %s" % (key, kind, "unreachable",
                                            "no prologue -- the scan cannot "
                                            "bound this routine"))
            unreachable += 1
            continue
        lo, hi, form = rows[0][0], rows[0][1], rows[0][2]
        verdict, fired, note = score(code[lo:hi], form, min_ops)
        if verdict in ("no evidence", "suspect"):
            tag, quiet = "quiet", quiet + 1
        elif (verdict == "assembler") == (kind == "asm"):
            tag, agree = "agrees", agree + 1
        else:
            tag, disagree = "DISAGREES", disagree + 1
        print("%-22s %-10s %-12s %s  [%s]"
              % (key, kind, verdict, ",".join(sorted(fired)) or note, tag))
    print("-" * 82)
    print("%d agree, %d disagree, %d too quiet to say, %d unreachable"
          % (agree, disagree, quiet, unreachable))
    if unreachable:
        print("unreachable rows are the prologue-scan blind spot, not a "
              "failure -- see the docstring")
    return 1 if disagree else 0


def main(argv):
    args = [a for a in argv if not a.startswith("-")]
    if not args:
        sys.stdout.write("usage: handasm.py SPANS.toml [PART...] [--seg=XXXX] "
                         "[--min-ops=N] [--all]\n"
                         "       handasm.py SPANS.toml --expect EXPECT.toml\n")
        return 2
    want_seg = None
    min_ops = MIN_OPS
    show_all = "--all" in argv
    expect = None
    at_spec = None
    win = 64
    for a in argv:
        if a.startswith("--locate="):
            at_spec = a.split("=", 1)[1]
        if a.startswith("--window="):
            win = int(a.split("=")[1], 0)
        if a.startswith("--seg="):
            want_seg = int(a.split("=")[1], 16)
        if a.startswith("--min-ops="):
            min_ops = int(a.split("=")[1], 0)
        if a.startswith("--expect="):
            expect = a.split("=", 1)[1]
    if "--expect" in argv:
        i = argv.index("--expect")
        if i + 1 < len(argv):
            expect = argv[i + 1]
            args = [a for a in args if a != expect]

    with io.open(args[0], "rb") as fh:
        cfg = tomllib.load(fh)
    try:
        root = project.find()
        release = project.get("target.release")
        first = project.get("target.first_para", quiet=True)
    except project.Missing as exc:
        return project.complain(exc)

    cache = {}

    def blob_of(part):
        if part not in cache:
            cache[part] = (root / release[part]).read_bytes()
        return cache[part]

    def spec_of(part):
        return cfg["part"][part]

    if expect:
        with io.open(expect, "rb") as fh:
            ecfg = tomllib.load(fh)
        return expectations(ecfg, spec_of, blob_of, first, min_ops)

    if at_spec:
        part = args[1]
        seg_s, off_s = at_spec.split(":")
        seg, off = int(seg_s, 16), int(off_s, 16)
        spec = spec_of(part)
        bounds = list(spec["segs"]) + [spec["rtl"]]
        k = spec["segs"].index(seg)
        code = prologue.segment(blob_of(part), seg, bounds[k + 1], first)
        rows = [r for r in routines(code) if r[0] == off]
        if not rows:
            print("no routine candidate at %04x:%04x" % (seg, off))
            return 1
        lo, hi = rows[0][0], rows[0][1]
        body, traps = resolve_traps(code[lo:hi])
        print("%04x:%04x..%04x -- %d byte(s), %d x87 trap(s) resolved"
              % (seg, lo, hi, hi - lo, traps))
        print("store-direction share per %d bytes; a run near 100%% is an "
              "asm block" % win)
        for at, share, n in locate(body, win):
            if share is None:
                print("    %04x:%04x   --      no qualifying op"
                      % (seg, lo + at))
                continue
            bar = "#" * int(round(share * 20))
            print("    %04x:%04x  %3d%%  %-20s  %d op(s)"
                  % (seg, lo + at, round(share * 100), bar, n))
        return 0

    for part in (args[1:] or sorted(cfg["part"])):
        spec = cfg["part"].get(part)
        if spec is None:
            print("no segments recorded for part %s" % part)
            continue
        bounds = list(spec["segs"]) + [spec["rtl"]]
        print("part %s" % part)
        for k, seg in enumerate(spec["segs"]):
            if want_seg is not None and seg != want_seg:
                continue
            code = prologue.segment(blob_of(part), seg, bounds[k + 1], first)
            report(seg, code, min_ops, show_all)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
