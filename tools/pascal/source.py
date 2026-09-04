"""Source text, reduced to the code -- the one thing three tools need in common.

It lived in `magic.py`, whose subject is pairing a target's literals against a
reference's named constants. `clean.py` imported that module for this function
alone, and `braces.py` reached it as `clean.magic.strip` -- importing one tool to
get at a second tool's helper. Three users, one of them at two removes.

NOT IN `substrate/`, which the tool inventory scopes to "reading DOS and 16-bit
binaries: MZ headers, LZEXE, segments, relocation tables". This reads Pascal and
assembler SOURCE, so it belongs beside the tools that do.
"""
import re


def strip(text, asm=False):
    """Blank comments, strings and char codes, keeping every column in place.

    `asm` adds the assembler's `;` to end-of-line form. It is NOT the default:
    in Pascal `;` separates statements, so stripping from it would blank most of
    every file. Scanning a .ASM without it reported two numbers that were both
    inside comments -- the only two matches the file produced.
    """
    out = list(text)
    if asm:
        for m in re.finditer(';[^' + chr(10) + ']*', text):
            for k in range(m.start(), m.end()):
                out[k] = ' '
        text = ''.join(out)
    i, n = 0, len(text)
    while i < n:
        if text[i] == '{':
            j = text.find('}', i)
            j = n if j < 0 else j + 1
        elif text.startswith('(*', i):
            j = text.find('*)', i)
            j = n if j < 0 else j + 2
        elif text[i] == "'":
            j = i + 1
            while j < n and text[j] != "'":
                j += 1
            j = min(j + 1, n)
        elif text[i] == '#':                      # #13, #10 -- a character code
            j = i + 1
            while j < n and text[j].isdigit():
                j += 1
        else:
            i += 1
            continue
        for k in range(i, j):
            if out[k] != '\n':
                out[k] = ' '
        i = j
    return ''.join(out)
