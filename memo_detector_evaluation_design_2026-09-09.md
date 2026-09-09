<!-- Unedited agent output, kept as a record of the reasoning. -->

# How to compare the checks on my writing

Written 2026-09-09 by a subagent during the session that measured what makes
Jake stop reading. It is kept as a record and has not been rewritten.

A first-reader pass read it as Jake and found 45 places he would stop, and predicted that he would quit reading around line 14. The findings were not
applied. Applying them would mean writing replacement sentences that nobody
has read as a reader, and on the class note of 2026-08-30 that is where 16 of
his 28 stops came from. Since he has said he will not read this memo, editing
it would add unread prose and remove nothing.

---

# Deciding among the detectors

## The estimand

Write S(1) for the places you stop in the document that reaches you when a
detector has run and its findings are applied, S(0) for the same document
without. The estimand that decides is E[S(1) - S(0)], counted per document:
length is itself a stop mode, so dividing by it rewards padding.

Accuracy is the other quantity, the share of your stops a detector points at
and the share of its findings that are stops. Every measurement so far is of
accuracy, and the two come apart: 16 of the 28 stops you located on the class
note are sentences a first-reader round wrote as a replacement. A detector can
have any sensitivity you like and still raise S.

## Ground truth

The localized spans are the primary labeled set: your reply quotes the words
you stopped on, the quote is found in the prose above it, and it takes none of
your time.

Their number moves with the rule that makes them. Quoted and backticked runs
of six or more characters, matched against the normalized reply over turns
carrying a stop phrase named in advance, give 66 replies and 147 spans; a
narrower phrase list, one span per reply, gives 47. Fix the phrase list, the
match rule and the unit in writing first, or the set moves under the detectors
being compared.

Two selection problems. You quote when the fault is in a phrase, the median
quoted span being three words, so the set holds the referent you cannot
resolve and the false claim and almost nothing of "why am I reading this" or
"too long," which have no phrase to quote. The scanner was also fitted to part
of the set. Three of the nine spans it flags are "guard passes," "numbers
match" and "scanner clean," quoted in a turn timed 2026-08-29T21:44Z, and
commit b5bcf88 added the patterns that catch them five minutes later. Scoring
A before 2026-08-30 scores it on its training set, so only the 545 replies
after that date are held out.

The unmatched quotes recover less than they look worth: of the 69 that fail
under my rule, 5 name a file, so matching against documents adds about 5 and
not the 71 the brief expected, the rest failing because you paraphrased or the
text was reformatted. Your hand-marked read stays the only unbiased channel:
it alone records a stop you did not name.

## Metrics

Score a hit when the detector's span overlaps your quoted span; the three-word
median forces this, since sentence-level credit would reward a detector that
flagged the sentence for another reason.

Report each detector as one point, the share of the 147 spans it reaches
against its findings per 1000 words. At 20 seconds to read and reject one
finding, 10 findings per 1000 words takes 3.3 minutes, so a 500-word reply
carries 100 seconds of dismissing against 60 seconds of reading. Replies
tolerate about 3 findings per 1000 words, an hour-long document 20. Rank
detectors at those two densities, not at thresholds they chose.

The scanner reaches 9 of 147, three of them contaminated, at a density nobody
has measured. The question is how much recall C or D reaches at 3 and at 20.

Let m be your minutes when a stop reaches you, f the 20 seconds above, q the
chance that applying a wrong finding creates a new stop.

L = m x (misses) + f x (findings you reject) + m x q x (wrong findings
applied).

C hands you a report, so C pays f and q. D edits silently, so f is zero for D
and its errors reach you through q alone; six scored runs put C's precision at
14 to 29 percent.

## Sample size (0.05 level, 0.80 power)

Detectors on the localized spans: 147 separates recall 0.30 from 0.10, which
needs 59 spans, and does not separate 0.30 from 0.22, which needs 471.

Locations in one document, applied against not applied: 0.27 falling to 0.05
needs 43 per arm, 86 findings, which one first-reader run supplies; a fall
only to 0.12 needs 108 per arm, three sittings.

Block on length. The stop rate across length fifths is 14.6, 16.6, 12.6, 17.0
and 20.1 percent, rising at the long end but not monotone, so randomize within
blocks; unblocked, the comparison rediscovers length.

## The sitting

One document, frozen and hashed, that no pass has read. First record the
persona SHA, freeze the extraction rule, grep its sentences against every file
an agent loads, fix the seed, write the assignment to disk. C, A, D-self and
D-fresh read it, the last two differing only in whether the session wrote the
draft, which measures the contamination. Randomize each finding to applied or
not within length blocks, applied as written with replacements, because q is
what you want. You never see the list, and you read once, marking each stop
and where you quit.

No interference is the weak assumption: an applied definition can remove a
stop at an untouched location, shrinking the difference between arms, and a
replacement can create one. So the location contrast is primary, total stops
secondary, and the quit line recorded: your list of 2026-08-30 ends at line
277 of 807.

By permutation test: applied rate below unapplied at p < 0.05, keep C and keep
applying replacements; at or above, keep the report and stop applying; below
but p at or above 0.05, mark a second document.

## What I would run first

Not the sitting. Freeze the extraction rule and score A, D-self, D-fresh and E
on the held-out 545 replies as recall against findings per 1000 words. C
cannot go on that curve, since 545 runs at 7 to 12 minutes is 60 to 100 hours,
so run C on a random 30 and report the wider interval. This takes none of your
time and says which detectors deserve a sitting, which then measures q on the
survivors.
