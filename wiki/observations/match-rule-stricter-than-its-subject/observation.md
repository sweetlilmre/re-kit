---
type: Observation
title: A match rule stricter than the thing it matches reports absence, not failure
description: A cross-binary search masked relocations and demanded an exact match on the rest. It had never once succeeded, and it said NOT FOUND -- which reads as a claim about the binary rather than about the rule. Measured, the two images diverge at +0x07 on a DGROUP offset the relocation mask does not touch, because an offset is not a relocation. The tell was that a tool whose whole purpose is cross-binary comparison had no cross-binary result anybody had ever quoted.
tags: [verification, tooling, measurement, comparison, rtl]
measured_on: a Borland Pascal corpus of seven linked images
timestamp: 2026-09-01T00:00:00Z
---

# A match rule stricter than the thing it matches reports absence, not failure

A tool searches one binary for something it found in another: a runtime head, a shared routine, a known table. It reports `NOT FOUND`.

**Read that as a statement about the rule before reading it as a statement about the binary.** The two are indistinguishable in the output and they are opposite in meaning:

- the thing genuinely is not there;
- the thing is there and the rule cannot express how it differs.

A search only ever reports the first, because the second is not a case it knows about.

## Why it works

Cross-binary matching needs a tolerance, and the tolerance is always built out of a model of *what legitimately differs*. That model is where the strictness hides, because it is written once, early, from the differences somebody had already noticed.

Measured on one corpus: the search took 256 bytes of the first image's runtime head, zeroed the **relocations**, and required the rest to match exactly. The two images diverge at **+0x07**, on a DGROUP **offset** -- which the relocation mask does not touch, because an offset is not a relocation. They diverge again at **+0x0c**, on a near-call displacement the smart linker places differently in every binary.

**Masking far pointers was the right idea. It did not go far enough, and "not far enough" produced the same output as "nothing there".** Replaced with the general comparison engine -- the one built for exactly this tolerance -- the search finds its subject in all seven images.

## Blind spot

**The failure is invisible while the tool is only ever run one way.** Nothing about a `NOT FOUND` is anomalous on its own. It became visible only when somebody asked what the tool had ever *found*.

**So the tell is not in the output, it is in the history: a tool whose whole purpose is cross-binary comparison had no cross-binary result anybody had ever quoted.** That is a question worth asking of any instrument -- *what has this ever told us that we used?* -- and it needs no code to answer. An instrument with no citations behind it either measures something nobody needed or is quietly answering nothing.

**Loosening a rule moves the answer somewhere else, and that has its own failure.** A search under a loosened rule can find a better-scoring coincidence at the wrong position, which is confident and wrong in the opposite direction -- see [A believable percentage about a position nowhere near the thing](../search-loosened-drifts/observation.md). The two must be read together: locate under the rule that is strict enough to be unique, then measure under the one that is tolerant enough to be true.

## Cost

Asking one question of each comparison tool: what has it ever matched? Free, and it needs no run.

Then, where the answer is *nothing*: one pair of images, diffed at the byte level from the anchor, to see what the rule was refusing to forgive.

## Example

Seven linked images from one Borland Pascal corpus. The search for the runtime head had returned `RTL prologue NOT FOUND` for its whole existence and the message had been read, reasonably, as a fact about the images. Two divergences at +0x07 and +0x0c explained all of it, and both are differences a linker is entitled to produce. Using the tolerant engine, the runtime is located in **all seven**.

**A second instance, 3 Sep 2026, and the rule was a length rather than a tolerance.** `locate` suggests an alignment from a fixed 10-byte anchor run. For a pattern shorter than that the probe is short, the loop breaks before scoring anything, and it returns not-found -- so **no routine under ten bytes could ever be located**, and three of them were reported as `NOT FOUND in any built image` while sitting in the rebuild byte for byte at exactly the expected offset. Two were six-byte far-JMP vector stubs and one a seven-byte DMA reset.

The tell was four lines above the gate, in the constant that floors what may be believed: `MINIMUM = 4`, commented *"A believed alignment has to be at least this long. Six-byte routines exist."* The case was anticipated and the anchor made it unreachable, which is why nobody looked: the tool's own source said short routines were handled. Anchoring a short pattern on all of itself locates all three, and the one consumer with 85 locked routines reports the same 85 lengths afterwards -- so nothing that was already right moved.

**Ask what the tool has ever found, and ask it of the SIZES too.** A corpus whose routines are all comfortably longer than the anchor cannot show this defect, and the consumer that found it was the one declaring six-byte stubs for the first time.

## Citations

- `kit/tools/pascal/rtl.py`, the `match` subcommand, and `kit/tools/substrate/align.py`'s `locate`, which is the engine it now uses.
- [A believable percentage about a position nowhere near the thing](../search-loosened-drifts/observation.md) -- the opposite error, and why locating and measuring want different rules.
- [A compare tool's number is plausible, and it is wrong](../plausible-and-wrong/observation.md) -- where the allowed-difference rule and the location strategy are established as properties of the artefact rather than of the tool.
- [A total quietly drops a component and stays plausible](../absence-reads-as-zero/observation.md) -- the same shape one level out: a result that cannot distinguish *nothing was there* from *nothing was measured*.
