---
name: today
description: Answer "what should I work on today, and why?" by running the bundled today.py over ~/repos and offering at most three projects, closest to completion first, from the header at the top of each project's HANDOFF.md. Use when Jake asks what to work on, which project to pick up, or where his projects stand at the start of a research morning.
---

# What to work on today

Jake's rule for a research morning is to work on whatever project is closest to
completion, given the kind of work he is in the mood for. Each project's
HANDOFF.md starts with a short header that the last session in that project
wrote: the next concrete step, the kind of work, the next milestone, an
estimate of sessions to that milestone, what the work is waiting on, and an
optional deadline. The global CLAUDE.md, under "The header at the top of
HANDOFF.md," says how sessions write it. `scripts/today.py` in this skill's
directory reads every header under `~/repos` and prints one tab-separated row
per active project, fewest sessions first.

Work Jake does for other people --- reviews, students' papers, letters,
reimbursements, trainings --- is not in this table and does not belong in the
answer. Jake keeps that work in a separate queue and opens it himself with
`review`. Keeping the two kinds of work apart is the reason there are two
tools.

## Steps

1. Run the script from this skill's directory and read all of its output:

       python3 <this skill's directory>/scripts/today.py

   If it exits nonzero, show Jake the error and stop. An error is never "you
   have no projects."

2. If Jake has not said what kind of work he is in the mood for, ask once,
   naming the kinds that appear in the `kind` column. Then go on.

3. Offer at most three projects of that kind, in the table's order. If no row
   has that kind, say so and offer the first three rows instead. Pass over
   rows with something in `blocked_on` unless nothing else is left. When you
   do offer one, say what it is waiting for. For each option give the repository
   name, the `next` step quoted as written, and the reason in the table's own
   numbers: sessions left to the milestone and days since the last commit.

4. A project with 14 or fewer days in `deadline_in_days` goes among the three
   options even when others are closer to completion. Its reason gives the
   days left. Never compute or mention how far past a deadline anything
   is. The script leaves passed deadlines blank on purpose, because an
   overdue count is what made Jake stop opening his old task lists.

5. Say that a row marked STALE has an estimate older than the latest work in
   that repository. Mention rows showing `?` only to say the project has no
   header yet. Offer to write one at the end of the next session there.

6. Begin with the options and stop after them. Do not explain the rule of
   working on what is closest to completion, the 14-day deadline rule, or
   what the HANDOFF.md header is: Jake wrote all three and does not need them
   read back to him. The restatement his CLAUDE.md asks a reply to open with
   is one short line here, such as "You asked what to work on today." Do not
   list or count the remaining projects, and do not add advice.

## The columns

- `repo` --- the directory name under `~/repos`.
- `sessions_left` --- the last session's estimate of sessions to the next
  milestone. It shows `?` when the header gives none.
- `days_since_commit` --- local calendar days since the last commit. It
  shows `?` for a folder that is not a git repository or has no commits.
- `deadline_in_days` --- days until the header's deadline. It is blank when
  there is no deadline or the deadline has passed.
- `kind` --- code, math, prose, teaching, or whatever the session wrote.
- `stale` --- STALE when the header was written on an earlier day than the
  last commit.
- `next` --- the next concrete step, as the last session wrote it.
- `blocked_on` --- what or whom the work is waiting for, if anything.

Only a header line `active: no` removes a project from the table. Jake adds
that line himself; do not add it for him.
