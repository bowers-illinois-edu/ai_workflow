# review

`review` keeps the work you owe other people --- journal reviews, students'
papers, letters, reimbursements, and required trainings --- apart from your
research, and shows it to you one step at a time.

## Where things are

- The queue is in Dropbox, at
  `~/Library/CloudStorage/Dropbox/ReviewsInbox/REVIEWS/QUEUE`. Each request
  is a folder there holding a file named `REQUEST.md`, and the folder is also
  where that request's PDFs and other files go.
- The steps for each kind of request are in `review_templates.txt`, in this
  folder.
- The list of everything in the queue is the Obsidian note `review_queue.md`,
  at the top of `~/Documents/Obsidian Vault`. Obsidian Sync copies it to your
  iPhone and iPad.
- The alias `review` in `~/.zshrc` runs `review.py` from this folder.

## The three commands

Run these in Ghostty.

```
review
review add "AJPS 2024-0412" --kind journal --due 2024-04-01
review done
```

`review` prints the one step to do next, for example
`AJPS 2024-0412 | due 2024-04-01 | 45 min | write the summary paragraph and the major concerns`.

`review add` puts a new request in the queue. Its kind must be one of
journal, student-paper, letter, reimbursement, or training, and it needs a due
date written YYYY-MM-DD. Its steps are copied from `review_templates.txt`.

`review done` marks the step that `review` last printed as finished. It
refuses when a different request, or a different step, is at the front than
when `review` last printed it, so it never finishes a step you have not seen. After the last step of a request, the
request's folder moves to `Archive` inside the queue.

## The order

The request whose next step takes under 15 minutes comes first, so a work
session can open with something finished. After those, the earliest due date comes
first. `review` prints only one line and never says how many requests are
waiting.

## The Obsidian note

Every command rewrites `review_queue.md`. Under "Next" it shows the step that
`review` would print. Under "After that" it lists every other request, in the
order `review` would reach them. You can read the note on any device, but you
mark steps done only on the Mac, with `review done`.

## Changing a request

`REQUEST.md` is plain text: a header with the title, kind, due date, date
added, and the number of the current step, followed by one line per step,
written as `minutes | what to do`. You can edit the due date, the steps, or
the step number by hand. Editing `review_templates.txt` changes requests added
afterward, not the ones already in the queue.

## Requests from your mail

The separate project in `~/repos/mail-extract` will write a file with one line
per mail message. You read that file first and then hand it to Claude, who
proposes `review add` lines for you to run. That project's tests exist, but the
extractor itself has not been written yet.

## Tests

`make test-review`, run in `~/repos/ai_workflow`, runs the tests in
`review/tests/`. The tests use temporary folders, so they never touch the real
queue or your vault.
