---
type: Observation
title: A round trip proves your encoder inverts your decoder, and nothing about whether either one is right
description: Decode then re-encode is the most tempting check available on an obfuscated artefact, and it is nearly worthless. It tests the PAIR. Where a transform is its own inverse over a range you handled wrongly, the round trip puts the shipped bytes back and the artefact comes out byte-identical while the recovered content is nonsense. Measured on a word-ciphered overlay whose first 80 bytes were plain and were decoded anyway -- the rebuilt file matched to the byte and the source held garbage where a copyright banner belonged.
tags: [verification, measurement, blind-spot, encoding, container, reverse-engineering]
measured_on: a 35,715-byte obfuscated overlay and the object module built from the same source
timestamp: 2026-09-04T00:00:00Z
---

# A round trip proves your encoder inverts your decoder, and nothing about whether either one is right

An obfuscated artefact offers one check that costs almost nothing: decode it, encode the result, and compare against the file you started with. It feels like a strong check. It is a weak one, and it is weak in a way that hides real errors rather than merely failing to catch them.

The round trip tests **the pair**. It says your encoder inverts your decoder. It cannot say either one matches what the original tool did.

## Where it goes wrong

The failure needs one condition: a range where your handling is wrong and the transform is its own inverse anyway. Then the round trip restores the shipped bytes there, and every byte-level check on the rebuilt artefact passes.

Measured. An overlay of 35,715 bytes carries a plain header, then a word cipher — each word rotated, then exclusive-ored with a counter and a constant. The algorithm came from the loader's own source, so it was not in doubt. The decode was applied from the end of the header.

It was applied 80 bytes too early. Those 80 bytes were **not ciphered**: they hold the product's copyright banner, terminated by a DOS end-of-file byte so that `TYPE` on the file prints the notice and stops. The tool that built the overlay began ciphering after them.

Decoding them produced 80 bytes of noise. Re-encoding them put the original 80 bytes back, because over an unciphered range the encode simply undid the decode. So:

- the rebuilt overlay was **byte-identical** to the shipped file,
- the round trip reported **exact**,
- and the reconstructed source carried 80 bytes of hexadecimal noise where a human-readable banner belonged.

Two of the three results were correct. The one that mattered — what the artefact actually contains — was wrong, and nothing in the artefact could say so.

## What does catch it

An **independent witness**: something that already knows what the decoded content should be, and is not derived from the decode.

Here the witness was a second artefact built from the same source — an object module whose segment holds the same code. Solving for the cipher key word by word against that segment answered it immediately: for the first forty words the ciphertext *equalled* the plaintext. No key fits, because no key was applied. From word forty on the counter fitted perfectly and the agreement ran to 97.2%.

Failing that, **read the output**. Decoded content is usually meant to be meaningful — text is text, a jump table looks like a jump table, a period table counts down. Noise at a boundary is a boundary error. This one announced itself as soon as anybody looked at the first line, and the round trip had been believed instead.

## The rule

Treat a round trip as a smoke test on your own code and never as evidence about the artefact. Before trusting a decode, name what would tell you it is right, and make sure that thing is not downstream of the decode itself. A second artefact, a known format, a string a person can read — any of them outranks a round trip.

And be careful how the result is stated. "The rebuilt file is byte-identical" was true and was taken to mean the content was recovered. Those are different claims, and the gap between them held eighty bytes.

## Blind spot

The witness bounds the decode; it does not confirm the whole of it. The object module here shares only 97.2% of its bytes with the overlay, so it can speak for the shared part and is silent about the rest. A range that appears in the obfuscated artefact and nowhere else has no witness at all, and for that range reading the output is the only check there is.

## Related

- [[byte-identity-is-not-correctness]] — the same ceiling seen from the other side: matching bytes hid a wrong array base there, and hide a wrong decode here.
- [[record-kind-outlives-the-bytes]] — another correct artefact concealing a wrong source, in the container rather than the cipher.
- [[absence-reads-as-zero]] — the neighbouring case where a missing thing and a real one share their bytes.
