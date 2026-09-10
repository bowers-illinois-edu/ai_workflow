# How to run the reading experiment again

Written 2026-09-09, the day it was first run, so that a session months from
now can repeat it without reconstructing the reasoning.

## What it answers

One question, and no other: when a check on Jake's writing proposes changes
and someone applies them, does he end up stopping in fewer places, more, or
the same number?

Nothing else measures that. Counting how many of his stops a check points at
does not, because a check can point at many and still leave him worse off:
applying a finding means writing a sentence, and a sentence written after the
last reading is a sentence nobody has read as a reader. On a class note of
2026-08-30 he listed 29 places where he stopped, 28 could be traced to a
sentence, and 22 of those 28 were prose written after a pass had read.

## Why a test is allowed here

He objected, correctly, on 2026-09-09 to a confidence interval printed beside
a count of phrases he had happened to quote back: nothing there was drawn by a
process anyone could repeat, so there was nothing for an interval to describe.

Here `assign.py` flips a coin for each proposed change and we set its chance.
Under the hypothesis that applying a change made no difference to whether he
stopped there, his stops would have fallen where they fell whichever way the
coins had come up. So `score.py` flips the same coins again, thousands of
times, and counts how often a re-flip separates the two groups as far as the
real assignment did. Nothing is assumed about how his stops are distributed.

## The steps

Pick a document he has not read, long enough that the checks will find a few
dozen places to change. A document he was going to read anyway is best,
because then the hour is not an extra hour. Copy it somewhere outside its own
repository, so nothing produced here can reach the real file.

```
cp <paper>.tex $SCRATCH/draft.tex
```

Run every check on that copy. Each returns a JSON list of objects with keys
id, line, quote, replacement, check. The quote must sit entirely within its
line and the replacement must contain no newline, because the join between his
marks and the findings is by line number and a replacement that added a line
would move every finding below it.

```
python3 style_scan.py draft.tex          # then triage by hand and write replacements
```

Spawn `first-reader` on the copy, and a separate fresh agent applying the four
questions in section 0 of `style-audit`. Give neither of them anything else:
if the document is in a repository that also holds earlier reader reports, the
agent must not be able to reach them.

Do not screen the findings for quality. Applying what a check hands you is the
thing being measured, and filtering would test the checks at their best rather
than as they arrive.

```
python3 pool.py draft.tex findings_*.json --seed <N> \
    --out findings_pooled.json --dropped-out findings_dropped.json
python3 assign.py draft.tex findings_pooled.json --seed <N> --out-dir $SCRATCH
python3 rewrap.py reading_copy.tex --width 72 \
    --out reading_wrapped.tex --map-out line_map.json
```

`rewrap.py` is not optional. The replacements are mostly longer than the text
they replace, and on the first run that left the changed lines visibly longer
than the rest: median 81 characters against 72 where a change was held back
and 68 everywhere else, with all six lines over 100 characters carrying an
applied change. He would have been reading a marked copy. After reflowing the
three medians were 69, 68, and 68.

Then he reads:

```
nvim -S stops.vim reading_wrapped.tex
```

`,s` records a line with a note, `,S` records it without, `,q` marks where he
quit. Everything is appended to `stops.md` on each press, so a crash loses
nothing.

```
python3 score.py assignment.json stops.md --line-map line_map.json \
    --quit-line <line> --reps 20000 --seed <N>
```

## What happened the first time

2026-09-09, on `block_test_power/Paper/paper.tex`, 1555 lines. The three
checks proposed 75 changes; four pairs covered the same words and a coin
kept one of each, leaving 71; a second coin applied 35 and held 36.

He read the whole paper and marked 113 lines, covering 163 lines of the draft.

Of the 35 places where a change was applied he stopped at 7. Of the 36 held he
stopped at 7. Twenty percent against nineteen. Over 20,000 re-flips a gap that
size or larger came up every time.

So applying the fixes changed nothing either way. The worry from the class
note, that applying fixes manufactures new stops, did not happen here.

He stopped at 14 of the 71 flagged places and at 149 places nothing flagged.
By check: first-reader 5 of 30, the four questions 7 of 38, the scanner 2 of 3.

The run's data is in `block_test_power/Paper/reading_experiment_2026-09-09/`,
which is a private repository. It stays out of this one because the findings
and his notes quote an unpublished paper.

## What to change before running it again

The findings above say the checks are aimed at the wrong things, not that they
are tuned badly. Classifying his 127 notes:

| What stopped him | Count |
|---|---|
| A term of art used without being spelled out | 36 |
| A definite noun phrase whose referent is not fixed | about 10 |
| A thing given a person's verb | about 21 |
| A run-on or a clause that adds nothing | 14 |
| A connective whose premise is missing | about 5 |
| Disagreement with the content rather than the writing | about 7 |
| An accidental key press | 4 |

The first row is the largest and no check looks for it: "sharp null", "weak
null", "noncentrality", "limit law", "local alternatives", "Bonferroni level",
"order one", "Cauchy tail", and "alternative" and "null" written without the
word "hypothesis". A statistics paper has a finite vocabulary of these, so
this one is listable in a way the others are not.
