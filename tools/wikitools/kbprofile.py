"""Our stricter profile on top of OKF, plus the generators that stop drift.

Three jobs, and the third is the one that earns this file:

  CHECK    the fields our template settled on are present, and
           `example: none yet` is written out rather than left blank.

  REFUSE   a hub that states an unqualified rule. This is the failure mode
           the hub design exists to prevent: if the hub says "forgive zeros"
           without naming an artefact, it has stated ONE artefact's rule as
           a general truth and demoted the others to footnotes nobody
           reads. The zero rule was re-implemented wrongly "within an hour
           of reading" the header documenting that exact failure twice, so
           one hop away is not far enough. This check is the mechanism that
           replaces the advice.

  GENERATE the hub's discriminator table and each index.md, from the
           children's frontmatter. A hand-written summary beside a child's
           full rule is a second copy and it WILL drift; generating it is
           the same principle OKF already applies to index.md.

Encoding, per CLAUDE.md: utf-8 explicitly on read and write, and newline
'\n' on write, because Python defaults to CRLF on Windows and documents in
this repo are LF (.gitattributes enforces it).

    python kit/tools/wikitools/kbprofile.py kit/wiki
    python kit/tools/wikitools/kbprofile.py kit/wiki --write
"""
import io
import pathlib
import re
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import project                                    # noqa: E402

# Overrides taken this run, printed at the end. A heuristic may gate only if it
# offers an explicit override, and an override must never pass SILENTLY -- both
# halves of that rule come from the decision that made a blind spot a mechanism.
OVERRIDES = []

# Observations whose witness is `unrecorded`. Counted and printed, never
# gated: 32 pages name no target anywhere, several of them written
# deliberately generic, and inventing a witness for those would be a claim
# formatted like a measurement -- which nothing downstream can catch, because
# it reads exactly like one that was measured. `unrecorded` is the honest
# value and this counter is what stops it becoming invisible.
UNRECORDED = []

# Observations with no `Blind spot` section. COUNTED AND NEVER GATED, and the
# distinction is the whole point. Section 5 requires an observation to carry
# its blind spot, so a gate would look like the right answer -- but a gate is
# satisfied by a ritual sentence ("this may not hold for other compilers"),
# which is a blind spot in form and nothing in substance. That is the shape
# `exemption-that-cannot-fail` describes, arriving through the rule meant to
# prevent it. A count cannot be satisfied by writing nothing, so it stays
# honest as the number falls -- and being unable to name one is diagnostic:
# either the instrument's range is not understood yet, or the page is a
# definition rather than an observation.
NO_BLIND_SPOT = []

# The tag vocabulary, loaded from the bundle's own tags.txt. Empty means the
# file is absent, and then the check does not run -- a bundle without the file
# is not failed, because the vocabulary is this profile's convention and not
# OKF's. It is loaded rather than hardcoded for the reason every list here is:
# a second copy of it in this file would drift from the tree it describes.
VOCAB = set()


def load_vocab(root):
    """Read the tag vocabulary. A missing file disables the check, loudly."""
    path = root / "tags.txt"
    if not path.exists():
        return set(), None
    words = set()
    for line in io.open(path, encoding="utf-8", newline="").read().split("\n"):
        line = line.split("#", 1)[0].strip()
        if line:
            words.add(line)
    return words, path

BEGIN = "<!-- generated:discriminator -->"
END = "<!-- /generated:discriminator -->"

# Frontmatter keys, by document type.
REQUIRED_FRONTMATTER = {
    "Observation": ("type", "title", "description", "tags", "measured_on",
                    "timestamp"),
    "Procedure": ("type", "title", "description", "tags", "timestamp"),
    "Artefact Answer": ("type", "title", "description", "identify", "holding",
                        "order", "artefact", "tier", "ladder_node", "tags",
                        "timestamp"),
    # Documents that are not techniques but still live in the bundle. Registered
    # rather than skipped by filename: OKF reserves only index.md and log.md, so
    # everything else is a concept document and should declare what it is.
    "Orientation": ("type", "title", "description", "tags", "timestamp"),
    "Glossary": ("type", "title", "description", "tags", "timestamp"),
}

# Body headings an artefact answer must carry. `Decides` is retired and
# `Disasm` folded into Cost when the template was settled.
REQUIRED_SECTIONS = {
    "Artefact Answer": ("What to do", "Why it works", "Blind spot", "Cost",
                        "Example", "Withdrawn", "Citations"),
    "Observation": (),
    "Procedure": (),
    "Orientation": (),
    "Glossary": (),
}

TIERS = ("substrate", "pascal")

# A hub must not state a rule. These are the imperative openings that turn a
# discriminator into a rule; they are only a defect OUTSIDE the generated
# table and outside a sentence that names an artefact.
RULE_VERBS = ("forgive", "excuse", "ignore", "skip", "mask", "accept")
# The verbs are matched in their BARE form only, as whole words. A rule being
# STATED is imperative or normative -- "forgive zeros", "the tool must ignore
# them" -- and both are bare. A verb carrying an -s is third person, so it has
# a subject and is DESCRIBING what some tool or program does: "a walk that
# forgives short runs hides this", "parameters the routine ignores". Matching
# the stem as a substring caught both of those and they are not rules; it is
# the same class of false positive as a rule verb inside quotation marks, and
# the same kind of fix. Two documents were failing this check on descriptive
# prose before the distinction was drawn.
RULE_VERB_RE = re.compile(r"\b(?:%s)\b" % "|".join(RULE_VERBS))
ARTEFACT_WORDS = ("`.tpu`", "`.obj`", "linked image", "artefact", "which",
                  "depend", "invert", "tasm", "turbo pascal")


def split_doc(path):
    text = io.open(path, encoding="utf-8", newline="").read()
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    return yaml.safe_load(parts[1]) or {}, parts[2]


def headings(body):
    return [m.group(1).strip() for m in re.finditer(r"^#+\s+(.*)$", body, re.M)]


def check_doc(path, rel):
    fm, body = split_doc(path)
    kind = str(fm.get("type", "")).strip()
    problems = []
    if kind not in REQUIRED_FRONTMATTER:
        return ["%s: unknown type %r for our profile" % (rel, kind)]

    for key in REQUIRED_FRONTMATTER[kind]:
        val = fm.get(key)
        if val is None or (isinstance(val, str) and not val.strip()):
            problems.append("%s: missing frontmatter key `%s`" % (rel, key))

    # A tag outside the vocabulary. This exists because every tag merge this
    # bundle has needed was a SECOND SPELLING of a tag already in use --
    # includes/include, code-generation/codegen, linker/linking -- and nothing
    # would have stopped the next one. A tag used ONCE is not the defect and is
    # not refused: most single-use tags name one specific thing, and merging by
    # how similar two words look is how a real distinction gets destroyed.
    if VOCAB:
        for tag in (fm.get("tags") or []):
            if str(tag) not in VOCAB:
                problems.append(
                    "%s: tag %r is not in the vocabulary -- add it to "
                    "tags.txt deliberately, or use an existing one" % (rel, str(tag)))

    have = headings(body)
    for want in REQUIRED_SECTIONS[kind]:
        if not any(h.lower() == want.lower() for h in have):
            problems.append("%s: missing section `%s`" % (rel, want))

    if kind == "Artefact Answer":
        tier = str(fm.get("tier", "")).strip()
        if tier and tier not in TIERS:
            problems.append("%s: tier %r is not one of %s"
                            % (rel, tier, "/".join(TIERS)))
        # The example field is mandatory but `none yet` is legal -- what is
        # NOT legal is leaving it blank, because a silent blank reads as
        # fine while `none yet` reads as what it is.
        block = section_text(body, "Example")
        if block is not None and not block.strip():
            problems.append("%s: `Example` is blank -- write `none yet` if there is none"
                            % rel)

    if kind == "Observation":
        if str(fm.get("measured_on", "")).strip() == "unrecorded":
            UNRECORDED.append(rel)
        if not re.search(r"^#+ *Blind spot", body, re.M):
            NO_BLIND_SPOT.append(rel)

    if kind == "Observation" and is_hub(path):
        allowed = [str(a) for a in (fm.get("hub_rule_allow") or [])]
        for problem, sentence in check_hub_states_no_rule(rel, body):
            excused = next((a for a in allowed if a.lower() in sentence.lower()), None)
            if excused is None:
                problems.append(problem)
            else:
                OVERRIDES.append((rel, excused))

    if kind == "Artefact Answer":
        # The hub's table is GENERATED from these two keys, so a rule verb
        # here reaches the hub and bypasses check_hub_states_no_rule, which
        # deliberately skips the generated block. That was a real hole: the
        # one place rules ended up was the one place exempt from the check.
        for key in ("identify", "description"):
            val = str(fm.get(key, "")).lower()
            if RULE_VERB_RE.search(val) is not None:
                problems.append(
                    "%s: `%s` feeds the hub's table and states a rule -- it must "
                    "say how to RECOGNISE this artefact, not what to do about it"
                    % (rel, key))
    return problems


def section_text(body, name):
    m = re.search(r"^#+\s+" + re.escape(name) + r"\s*$(.*?)(?=^#+\s|\Z)",
                  body, re.M | re.S)
    return None if m is None else m.group(1)


def check_index_lists_everything(root):
    """Every document directory must be linked from the wiki's OWN index.md.

    THE ONE INDEX NOTHING GENERATED. This file already generates a hub's
    index.md from its children, on the stated principle that a hand-written
    summary beside a child's full rule is a second copy and will drift. The
    wiki's top-level index.md is hand-written and was never covered by that,
    so it drifted exactly as predicted: four observations were absent from it
    for four days, which for a reader is the same as their not existing.

    It is a CHECK and not a generator, deliberately -- but the reason stated
    here was overstated, and measuring it is what corrected it. The claim was
    that the index is "ordered by argument". Measured across 83 entries: it is
    chronological in 88% of adjacent pairs, with TEN deliberate inversions
    where related observations were pulled together -- identifying assembler
    beside reading the line table, the two switches with a frame signature, the
    two cases of a second measurement agreeing wrongly.

    So the order is chronological WITH local grouping, and the grouping is the
    part worth protecting: generating this file would flatten those ten
    decisions and nothing would report the loss. The overstatement mattered
    because a reader told the file is "ordered by argument" goes looking for an
    organising scheme that is not there, and concludes the index is broken
    rather than that the description was.

    What can be mechanical is the coverage: no document may be missing.

    A missing entry is reported WITH the line to add, because the reason this
    goes unnoticed is that writing the entry means opening the document again
    and paraphrasing it, and anything asking for that at the wrong moment gets
    deferred.
    """
    idx = root / "index.md"
    if not idx.exists():
        return ["index.md is missing from %s" % root.as_posix()]
    text = io.open(idx, encoding="utf-8", newline="").read()
    problems = []
    for d in sorted(p for p in root.glob("*/*") if p.is_dir()):
        doc = d / "observation.md"
        if not doc.exists():
            continue
        link = "%s/%s/observation.md" % (d.parent.name, d.name)
        if link in text:
            continue
        fm, _ = split_doc(doc)
        problems.append(
            "index.md does not list %s -- add: * [%s](%s) - %s"
            % (d.name, fm.get("title", d.name), link,
               (fm.get("description") or "")[:80]))
    return problems


def is_hub(path):
    """Does this observation HAVE artefact answers under it?

    A HUB is an observation with children, and the no-rule check below exists
    only for a hub: its children hold rules that INVERT by artefact, so a rule
    stated in the hub is a rule stated for the wrong half of the corpus. An
    observation with no children is a single page, and stating its rule is the
    whole job -- there is nowhere else for it to go.

    The check was applied to every `type: Observation` instead, which on this
    corpus is 77 documents of which 3 are hubs. It had therefore been able to
    fail 74 pages for doing what they exist to do, and it did fail two of them.
    It only failed two because the verb list is narrow, which is luck rather
    than design: a check misaimed at a whole type is quiet in proportion to how
    little it looks for, so the near-miss reads like a working check.

    Uses the same definition of a child as `generate` -- a sibling `.md` whose
    type is `Artefact Answer` -- deliberately, rather than a second rule about
    filenames. Two copies of one definition drift, and a drifted copy of THIS
    one would change which documents get checked without changing any message.
    """
    for sibling in sorted(path.parent.glob("*.md")):
        if sibling.name in ("index.md", "log.md") or sibling == path:
            continue
        fm, _ = split_doc(sibling)
        if str(fm.get("type", "")).strip() == "Artefact Answer":
            return True
    return False


def check_hub_states_no_rule(rel, body):
    """Refuse a hub sentence that gives an instruction without an artefact.

    Returns (problem, sentence) pairs rather than strings, because the caller
    may excuse one and needs the sentence to match an override against.

    THIS IS A HEURISTIC OVER PROSE, and the standing rule for those is that a
    heuristic may only REPORT unless it offers an explicit, recorded override --
    an overridable gate beats a warning, because a warning gets ignored. This
    check gated without one for its whole life, which was a known inconsistency
    written on a ticket and nowhere in the code, so nothing in a checkout could
    tell you the rule was being broken. A page may now carry `hub_rule_allow`
    in its frontmatter, listing substrings of the sentences it is permitted to
    state, with the reason in prose beside them.

    Every override is PRINTED and counted in the summary. This check has
    produced a false positive before, so an override that accumulated quietly
    would turn each one into a permanent exemption nobody re-reads -- which is
    what an exemption list does to a check.
    """
    outside = body
    if BEGIN in outside and END in outside:
        head, rest = outside.split(BEGIN, 1)
        outside = head + rest.split(END, 1)[1]
    problems = []
    for raw in re.split(r"(?<=[.!?])\s+|\n", outside):
        s = raw.strip()
        if not s or s.startswith(("|", "#", "-", ">")):
            continue
        low = s.lower()
        # A rule verb inside quotation marks is a rule being DISCUSSED, not
        # stated -- '"forgive zeros" silently assumes the first case' is the
        # hub doing its job. Strip quoted spans before looking.
        unquoted = re.sub(r'"[^"]*"', " ", low)
        if RULE_VERB_RE.search(unquoted) is None:
            continue
        if any(w in low for w in ARTEFACT_WORDS):
            continue
        problems.append((
            "%s: the hub states a rule without naming an artefact -- %r"
            % (rel, s[:70]), s))
    return problems


def render_discriminator(children):
    rows = ["| if you are looking at | how to tell | detail |",
            "|---|---|---|"]
    for fm, stem in children:
        # `holding` and `summary` are explicit keys. An earlier version derived
        # the first column by stripping a prefix off the title, which was both
        # brittle and LOSSY -- it silently dropped the backticks around `.TPU`.
        rows.append("| %s | %s | [%s](./%s.md) |"
                    % (fm.get("holding", stem), fm.get("identify", ""),
                       stem, stem))
    return "\n".join(rows)


def generate(root, write):
    root = pathlib.Path(root)
    changed = []
    for hub in sorted(root.rglob("observation.md")):
        children = []
        for path in sorted(hub.parent.glob("*.md")):
            if path.name in ("observation.md", "index.md"):
                continue
            fm, _ = split_doc(path)
            if str(fm.get("type", "")).strip() == "Artefact Answer":
                children.append((fm, path.stem))
        # Explicit order. Alphabetical put the linked image FIRST, which is
        # backwards: the three artefacts sit at three points of one pipeline
        # and reading them in that order is what explains the inversion.
        children.sort(key=lambda c: (int(c[0].get("order", 99)), c[1]))
        table = render_discriminator(children)
        text = io.open(hub, encoding="utf-8", newline="").read()
        if BEGIN not in text or END not in text:
            # A hub with no artefact answers has no table to route to, so
            # there is nothing to generate and it is not stale. Reporting it
            # anyway made this check exit 1 for every single-page observation
            # in the bundle, permanently, while --write printed "regenerated"
            # and wrote nothing -- it `continue`s here. A red check nobody can
            # ever turn green is worse than no check.
            if children:
                changed.append((hub,
                                "hub has artefact answers but no "
                                "generated:discriminator markers"))
            continue
        head, rest = text.split(BEGIN, 1)
        _, tail = rest.split(END, 1)
        new = head + BEGIN + "\n" + table + "\n" + END + tail
        if new != text:
            changed.append((hub, "discriminator table is stale"))
            if write:
                io.open(hub, "w", encoding="utf-8", newline="\n").write(new)

        # index.md for the observation directory
        idx = hub.parent / "index.md"
        # The banner is part of the GENERATED text, so it is compared like every
        # other line and cannot drift from the truth of itself. A generated file
        # that does not say so is one a person edits without being warned; a file
        # that says so with nothing comparing it is worse, because the claim is
        # about a RELATIONSHIP and no build measures relationships. Here the
        # comparison below is what makes the banner honest.
        lines = ["<!-- generated by kbprofile.py from the children's frontmatter."
                 " Edits are overwritten; change a child and regenerate. -->",
                 "",
                 "# " + str(split_doc(hub)[0].get("title", hub.parent.name)), ""]
        lines.append("* [%s](observation.md) - the discriminator: which artefact are you holding?"
                     % split_doc(hub)[0].get("title", "observation"))
        for fm, stem in children:
            lines.append("* [%s](%s.md) - %s" % (fm.get("title", stem), stem,
                                                 fm.get("identify", "")))
        body = "\n".join(lines) + "\n"
        if not idx.exists() or io.open(idx, encoding="utf-8", newline="").read() != body:
            changed.append((idx, "index.md is stale or missing"))
            if write:
                io.open(idx, "w", encoding="utf-8", newline="\n").write(body)
    return changed


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    write = "--write" in argv
    if not args:
        try:
            args = [str(project.path("layout.wiki"))]
        except project.Missing as exc:
            return project.complain(exc)
    root = pathlib.Path(args[0])

    global VOCAB
    VOCAB, vocab_path = load_vocab(root)
    if vocab_path is None:
        sys.stdout.write("  no tags.txt in this bundle -- tag vocabulary NOT checked\n")

    problems = []
    docs = 0
    for path in sorted(root.rglob("*.md")):
        if path.name in ("index.md", "log.md"):
            continue
        docs += 1
        problems.extend(check_doc(path, path.relative_to(root).as_posix()))

    problems.extend(check_index_lists_everything(root))

    changed = generate(root, write)

    if NO_BLIND_SPOT:
        sys.stdout.write("  %d observation(s) carry no `Blind spot` section -- "
                         "reported, not gated, because a gate accepts a"
                         " ritual one\n"
                         % len(NO_BLIND_SPOT))
    if UNRECORDED:
        sys.stdout.write("  %d observation(s) have measured_on: unrecorded -- "
                         "a finding with no witness anybody can re-check\n"
                         % len(UNRECORDED))
    for rel, excused in OVERRIDES:
        sys.stdout.write("  %s: rule sentence allowed by hub_rule_allow (%r)\n"
                         % (rel, excused[:60]))
    for p in problems:
        sys.stdout.write("  " + p + "\n")
    for path, why in changed:
        verb = "regenerated" if write else "STALE"
        sys.stdout.write("  %s: %s (%s)\n"
                         % (path.relative_to(root).as_posix(), why, verb))
    sys.stdout.write("%d profile problem(s) in %d document(s); %d generated file(s) %s"
                     % (len(problems), docs, len(changed),
                        "rewritten" if write else "out of date"))
    sys.stdout.write(("; %d override(s)\n" % len(OVERRIDES)) if OVERRIDES else "\n")
    return 1 if problems or (changed and not write) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
