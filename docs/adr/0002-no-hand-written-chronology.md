# The wiki keeps no chronology, because git already is one

**Status:** accepted, 1 Sep 2026

`wiki/log.md` was a hand-written record of what was added to the bundle and when. Measured on the day this was decided, it held `Create` entries for 47 of 77 observations, mentioned 27 of them nowhere at all, carried sections for 5 dates where the observations span 10, and used root-absolute links of which **no single root resolves all** -- 55 need the bundle as root and 4 need the kit. Six of its link texts disagreed with the titles they pointed at.

**Decided: retire the file.** Chronology is the one organising axis version control provides for nothing, and a second hand-maintained copy of it is the "second copy of one measurement" hazard `WORKING.md` section 8 names -- which, that section notes, does not merely go quiet but manufactures findings.

## Consequences

The log's entries were far richer than `index.md`'s one-liners: they carried the argument, the false starts, the counts, and in several cases a correction that appears nowhere else. **That content is not discarded.** Retiring the file required first walking each of the 27 unmentioned observations and each rich entry, and moving anything the observation itself lacked into the observation -- where a reader meets it at the point of use, rather than in a file organised by a date nobody searches by.

That harvest is the expensive half and it is the reason this is an ADR rather than a deletion: the next person to want a changelog should know the content was moved rather than lost, and should not restore the file to recover it.

**What replaces it.** `index.md` answers what the bundle holds. `git log kit/wiki` answers when each piece arrived and what its commit argued. Neither can drift from the tree, because neither is written by hand.
