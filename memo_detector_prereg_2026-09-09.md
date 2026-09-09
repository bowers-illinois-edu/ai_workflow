<!-- Written before any check was scored. -->

# Extraction rule and decision rule, fixed 2026-09-09 before any detector was scored

Written before running any detector on the held-out window, so the target
cannot move while detectors are compared.

## What counts as a stop

A row of ~/Claude_Transcript_Archive/corpus.jsonl whose `human` field matches
the marker list in find_stops.py, minus the two shapes retriage.py removes:
turns that spawn an agent, and questions asking what to do next. On rows from
2026-08-15 onward this gives 164 stops in 1315 rows, 155 of them in the 1181
rows carrying assistant prose.

## What counts as a located span

Every substring of the `human` field enclosed in straight double quotes, curly
double quotes, or backticks, of four or more characters, that appears in the
preceding `assistant` field after collapsing whitespace and lowercasing both.
Every such substring counts, not only the first in a row.

That rule gives 141 spans overall and 35 in the held-out window.

## What is held out

Rows dated 2026-08-30 or later: 545 replies carrying prose, 62 of them stops,
35 located spans. Earlier rows are not held out, because the scanner patterns
for `worth` plus a gerund and for internal shorthand were added on 2026-08-29
in commit b5bcf88, whose comments quote the very phrases Jake had objected to
that day.

## What counts as a hit

A detector's flagged span overlaps a located span by at least one character.
Sentence-level credit is not given, because the median located span is short
and a detector that flagged the sentence for another reason would score.

## The decision rule

The 35 phrases are the ones Jake happened to quote back. They are not a sample
drawn from a larger set by any known process, so there is no repeated
experiment to attach an interval or a p-value to. Report a count and nothing
more.

Of the 35 phrases, how many does the check point at?

- 8 or more: keep the four questions.
- 3 or fewer: drop them.
- 4 to 7: neither, and the questions stay in section 0 marked unproven.

The thresholds are set here, before any check is run, so that the numbers
cannot be chosen to fit a result. They are round numbers, not estimates: 8 of
35 is roughly a fifth and 3 of 35 is roughly a tenth.

## What this cannot settle, known in advance

Two checks that differ by one or two phrases out of 35 are not distinguishable
by this comparison, and no care in running it makes them so. It separates a
check that points at almost none from one that points at most, and nothing
finer.
