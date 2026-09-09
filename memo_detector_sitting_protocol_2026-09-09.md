<!-- Unedited agent output, kept as a record of the reasoning. -->

# How to run the reading experiment

Written 2026-09-09 by a subagent during the session that measured what makes
Jake stop reading. It is kept as a record and has not been rewritten.

A first-reader pass read it as Jake and found 26 places he would stop in 45 lines of prose, the first in the opening sentence. The findings were not
applied. Applying them would mean writing replacement sentences that nobody
has read as a reader, and on the class note of 2026-08-30 that is where 16 of
his 28 stops came from. Since he has said he will not read this memo, editing
it would add unread prose and remove nothing.

---

## What is being measured

The number that decides is the count of places you stop in the document you
finally read. It is not the share of your stops a detector points at. A
detector can point at many of them and still leave you with more stops than
you started with, because applying a finding means writing a sentence nobody
has read as a reader. On the class note, 16 of the 28 places you stopped were
sentences a first-reader round had written as its replacement.

## The sitting, step by step

1. You choose one document no pass has read. Script writes its
   `git hash-object` hash, the persona SHA, the date, and a random seed to
   `prereg.md`.
2. You type the extraction rule into `prereg.md`: the stop-phrase list, the
   six-character quote match, and whether the unit is a reply or a span.
3. Script greps the document's sentences against every file an agent loads
   (`~/.claude/CLAUDE.md`, `CLAUDE_WRITING_STANCE.md`, the persona) into
   `contamination.txt`. Any hit disqualifies the document; choose another.
4. Script runs three detectors, each report to disk: C (first-reader
   subagent), A (`style_scan.py`), and the checklist twice, D-self inside the
   writing session and D-fresh in a subagent given only the draft.
5. Script pools the reports into `findings.csv`, one row per finding: line
   span, quoted text, detectors, and the paragraph's word count as a
   covariate.
6. Script randomizes each finding to applied or held from the seed in step 1,
   without blocking, and appends the arm to `findings.csv`. You do not open
   it.
7. A session applies the applied findings as written, replacements included,
   and writes `reading_copy.md`.
8. You read `reading_copy.md` once, top to bottom, marking each place you stop
   and the line where you quit, into `stops.md`. This is the only step that
   takes your time.
9. Script joins `stops.md` to `findings.csv` and runs the permutation test,
   with word count entered as a covariate rather than a blocking factor.

## The decision rule, fixed before step 8

C's replacements: stop rate at applied locations below the rate at held
locations with permutation p < 0.05, keep C and keep applying replacements; at
or above the held rate, keep C's report and apply only deletions; below but p
at or above 0.05, mark a second document, whose assignment is fixed now.

The four-question checklist: one sitting cannot decide it, because the
checklist produces about five findings and its applied arm holds two or three.
Decide it on the corpus instead. Keep it if it reaches 20 percent of the
localized spans at 3 findings per 1000 words; drop it below 10 percent at that
density; between those it is inconclusive and stays off by default. The
sitting contributes one number to that decision, q, the share of its applied
findings you stop on.

Two assumptions to record: that an applied edit at one location does not
change whether you stop at a held location, which a definition can violate;
and that your quit line censors everything after it.

## What I would run first

Not the sitting. Score A, D-self and D-fresh on the 545 held-out replies under
the frozen extraction rule, as recall against findings per 1000 words. It
takes none of your time and says which detectors deserve a sitting. C cannot
go on that curve, since 545 runs at 7 to 12 minutes is 60 to 100 hours, so run
C on a random 30 and report the wider interval.
