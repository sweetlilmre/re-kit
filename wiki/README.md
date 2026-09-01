---
type: Orientation
title: The wiki
description: What this bundle is, how to check it, and what is deliberately missing from it.
tags: [orientation, verification]
timestamp: 2026-08-19T00:00:00Z
---

# The wiki

An [OKF v0.1](https://okf.md/spec/) bundle. It grows every time somebody reads a binary; `index.md` lists what it holds.

It began as a single page written end to end, as the pattern every later page would be cut against, and it was moved here by the decision that settled where the bundle sits -- which also put the tools in `kit/tools/wikitools/` rather than inside the bundle, because OKF governs the knowledge documents and says nothing about Python. The move kept the file history, which matters: two of the corrections below are lessons these files themselves demonstrate.

## What is in it

Observations, one directory each, all listed in `index.md`. Most are a single page: it opens with what somebody saw, and states its rule, because there is nowhere else for the rule to go.

A few are **hubs**, and those are the shape worth understanding before writing one. A hub is a DISCRIMINATOR and never states a rule, because its children hold rules that **invert** -- what you must forgive in one artefact is exactly what convicts in another, so a rule stated in the hub is a rule stated for the wrong half of the corpus.

    observations/zero-byte-difference/
        observation.md      the hub -- a DISCRIMINATOR, never a rule
        tpu.md              artefact answer, Pascal tier
        obj-tasm.md         artefact answer, substrate tier
        linked-image.md     artefact answer, substrate tier
        index.md            generated, and says so

That one was written first and deliberately, because it exercises every decision the template makes at once: three artefacts whose rules invert, two tiers inside one hub, a caveat and a withdrawn conclusion belonging to different children -- and a third child, `linked-image.md`, that **neither source entry states outright**. The shape found a missing case, which is the argument for the shape.

An earlier version of this section said the bundle held *one* observation. That was true on the day it was written and had not been touched since; the count is in `index.md`, which is checked, and is deliberately not repeated here.

## Two validators, deliberately separate

    python kit/tools/wikitools/okfcheck.py kit/wiki
    python kit/tools/wikitools/kbprofile.py kit/wiki

`okfcheck.py` asks only what OKF asks: does every non-reserved document have parseable frontmatter with a non-empty `type`? The spec says a linter for that is "about 10 lines of bash", and it is right. It must **not** reject a document for missing optional fields, unknown `type` values, unknown keys, or broken links.

`kbprofile.py` is ours and is stricter. It requires the fields our template settled on, and it refuses a hub that states an unqualified rule. It also **generates** the hub's discriminator table and the `index.md` files from the children's frontmatter, so those cannot drift from the answers they summarise.

    python kit/tools/wikitools/kbprofile.py kit/wiki --write

## Known gaps, recorded rather than hidden

- **It needs a virtual environment.** Both tools import `pyyaml` from PyPI, installed with `uv` into `.venv` at the repo root, because the template's fields are real frontmatter read by a real YAML parser rather than matched out of text -- this project has been burned by regex-over-text before. Run them with `.venv/Scripts/python.exe`, not the system Python. **This was the toolkit's first third-party dependency**, and the decision that drew the toolkit's package boundary has since allowed it, with `kit/tools/pyproject.toml` as the manifest.
- **The encoding auditor once did not scan this directory**, because its default directories were a constant naming one repository's folders. It reads the project's own answer now and covers the toolkit's own programs, which it had never audited. The general form is in [An exemption list is where a check goes to die](observations/exemption-that-cannot-fail/observation.md): a list at least admits what it skips, while a constant scope claims to have checked everything.
- **A README is a concept document.** OKF reserves only `index.md` and `log.md`, so `okfcheck.py` correctly refused this very file until it grew frontmatter and a `type`. The spec has no notion of a README, so anything else in a bundle must declare a type or be reserved.
- **The hub was still answering, via the generator.** The first version generated a `summary` column holding each artefact's *rule*, which put rules back into the hub -- the exact thing the design forbids. Worse, `check_hub_states_no_rule` deliberately strips the generated block before looking, so **the one place rules ended up was the one place exempt from the check.** Fixed twice over: the column is now `identify` ("how to tell you are holding this"), which serves discrimination and gives nothing away, and the check now also reads the `identify` and `description` keys that feed the table. Verified by injecting a rule and watching it fail.
- **The hub's no-rule check is a text heuristic and it produced a false positive on its first run** -- it flagged the sentence *A rule phrased as "forgive zeros" silently assumes the first case*, which is the hub doing its job. Stripping quoted spans fixed that case on a principled basis: a rule verb inside quotation marks is a rule being *discussed*, not stated. But the check remains a heuristic over prose, which is the exact disease `encaudit.py` was rewritten to cure. **The most important guardrail in the design is the one that resists automation.**

  The rule that settles what such a check may do: a heuristic may only REPORT, unless it offers an explicit, recorded override -- an overridable gate beats a warning, because a warning gets ignored -- and it must never fail silently or pass silently, so every override is printed. This check gated without an override for its whole life, which was a live inconsistency written on a ticket and nowhere in the code. It now takes `hub_rule_allow` in a hub's frontmatter, prints every override it grants, and counts them in the summary line.
- **`ladder_node` earned its keep as evidence, not as an index.** All three answers are R7, so the ladder cross-index would file them together and tell a reader nothing -- which is what the template's own design predicted when it ordered the three cross-indexes and put the ladder one last.
- **OKF v0.1 appears to contradict itself on `index.md` frontmatter**: section 6 says index files carry none, section 11 says the root `index.md` declares `okf_version` in frontmatter. This bundle follows section 11 for the root and section 6 everywhere else.
