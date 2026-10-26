#!/usr/bin/env python3
"""Show one next action for work owed to other people.

Reviews, students' papers, letters, reimbursements, and required trainings
arrive by email and pile up there, and a pile is what Jake avoids. This
script keeps that work apart from research and shows it one step at a time.
Each request is a folder in the queue directory holding REQUEST.md:

    ---
    title: AJPS 2024-0412
    kind: journal
    due: 2024-04-01
    added: 2024-02-27
    step: 1
    ---
    10 | download the PDF into this folder
    45 | read once, marking the PDF
    ...

The steps are copied from review_templates.txt when the request is added, so
editing a template later does not change requests already under way, and any
request's steps can be edited by hand.

Commands:

    review                                    show the next action, one line
    review add TITLE --kind K --due YYYY-MM-DD
    review done                               close the step just shown

Decisions behind the rules below (2026-10-25):

- Earliest due date first, because the cost of this work is lateness to
  someone waiting, and that order never makes the worst lateness larger
  than any other order does.
- A current step under 15 minutes goes first whatever its due date, so a
  reviewing slot can open with something finished; it delays the due-date
  order only by those minutes.
- One line, fixed format, never mentioning the other requests: the count
  of waiting requests is what tells Jake he is behind.
- `done` closes the step `review` last showed, and refuses if the request
  at the front has changed since, so it cannot advance a request Jake has
  not seen. `review` records what it showed in a hidden file in the queue.
- Loose files and folders without REQUEST.md are ignored, because the real
  queue sits in Dropbox among years of PDFs. A REQUEST.md that cannot be read
  is an error naming the file, never the empty-queue message.

Added the same day: Jake reads Obsidian on his phone, tablet, and laptop,
and the Dropbox app is no good for reading anything but PDFs. He asked to
see the whole queue at a glance, next request on top and clearly marked, in
one note rather than one per request. So every command rewrites one note in
his vault, which Obsidian Sync copies to his devices: the request `review`
would print under "Next", the rest in order under "After that". The note is
the only place the whole list appears; `review` still prints one line.
"""

import argparse
import datetime
import os
import re
import shutil
import sys

DEFAULT_DIR = "~/Library/CloudStorage/Dropbox/ReviewsInbox/REVIEWS/QUEUE"
DEFAULT_TEMPLATES = os.path.join(os.path.dirname(os.path.realpath(__file__)), "review_templates.txt")
STATE = ".review_last_shown"
EMPTY = "nothing in the review queue"
# No spaces in the note's own name, at Jake's request; the vault folder is his.
DEFAULT_NOTE = "~/Documents/Obsidian Vault/review_queue.md"
SHORT_MINUTES = 15
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
STEP_RE = re.compile(r"^\s*(\d+)\s*\|\s*(\S.*?)\s*$")


class QueueError(Exception):
    pass


def read_text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def parse_date(text):
    """A date written exactly YYYY-MM-DD, or None. Python 3.11 accepts other
    ISO forms in fromisoformat and 3.9 does not, so check the form first."""
    if not DATE_RE.match(text or ""):
        return None
    try:
        return datetime.datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def read_templates(path):
    """{kind: [(minutes, text), ...]} from lines like 'journal:' followed by
    indented 'minutes | text' lines."""
    templates, kind = {}, None
    try:
        lines = read_text(path).splitlines()
    except OSError as err:
        raise QueueError(f"cannot read templates {path}: {err.strerror}")
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        if re.match(r"^\S.*:\s*$", line):
            kind = line.strip().rstrip(":").strip()
            templates[kind] = []
            continue
        m = STEP_RE.match(line)
        if m is None or kind is None:
            raise QueueError(f"{path}, line {number}: expected 'kind:' or 'minutes | step', got {line!r}")
        templates[kind].append((int(m.group(1)), m.group(2)))
    return templates


class Request:
    def __init__(self, folder):
        self.folder = folder
        self.name = os.path.basename(folder)
        self.path = os.path.join(folder, "REQUEST.md")
        self.read()

    def fail(self, why):
        raise QueueError(f"{self.path}: {why}")

    def read(self):
        try:
            text = read_text(self.path)
        except (OSError, UnicodeDecodeError) as err:
            self.fail(f"cannot read it ({err})")
        lines = text.splitlines()
        if not lines or lines[0].strip() != "---":
            self.fail("no header; the file should start with a line '---'")
        try:
            end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
        except StopIteration:
            self.fail("the header has no closing '---' line")
        self.fields = {}
        for line in lines[1:end]:
            if ":" in line:
                key, value = line.split(":", 1)
                self.fields[key.strip().lower()] = value.strip()
        for key in ("title", "kind", "due", "step"):
            if not self.fields.get(key):
                self.fail(f"the header has no '{key}:' line")
        self.title = self.fields["title"]
        self.due = parse_date(self.fields["due"])
        if self.due is None:
            self.fail(f"due date must be YYYY-MM-DD, got {self.fields['due']!r}")
        self.steps = []
        for line in lines[end + 1:]:
            if line.strip():
                m = STEP_RE.match(line)
                if m is None:
                    self.fail(f"step lines must read 'minutes | step', got {line!r}")
                self.steps.append((int(m.group(1)), m.group(2)))
        if not self.fields["step"].isdigit() or not 1 <= int(self.fields["step"]) <= len(self.steps):
            self.fail(f"step: {self.fields['step']} but the file lists {len(self.steps)} steps")
        self.step = int(self.fields["step"])
        self.lines = lines
        self.header_end = end

    @property
    def minutes(self):
        return self.steps[self.step - 1][0]

    @property
    def action(self):
        return self.steps[self.step - 1][1]

    def sort_key(self):
        # Short steps first; within each group, earliest due date; then the
        # date added and the folder name so the order never depends on how
        # the file system lists folders.
        return (self.minutes >= SHORT_MINUTES, self.due, self.fields.get("added", ""), self.name)

    def line(self):
        return f"{self.title} | due {self.due.isoformat()} | {self.minutes} min | {self.action}"

    def set_step(self, step):
        lines = list(self.lines)
        for i in range(1, self.header_end):
            if re.match(r"^step\s*:", lines[i]):
                lines[i] = f"step: {step}"
        write_atomically(self.path, "\n".join(lines) + "\n")


def write_atomically(path, text):
    # Write beside the target and rename, so an interrupted write never
    # leaves a half-written REQUEST.md for Dropbox to sync.
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, path)


def load_queue(queue):
    if not os.path.isdir(queue):
        raise QueueError(f"no queue folder at {queue} (the first 'review add' creates it)")
    requests = []
    for name in sorted(os.listdir(queue)):
        folder = os.path.join(queue, name)
        if name.startswith(".") or name.lower() == "archive" or not os.path.isdir(folder):
            continue
        if os.path.isfile(os.path.join(folder, "REQUEST.md")):
            requests.append(Request(folder))
    return sorted(requests, key=Request.sort_key)


def unused_path(parent, base):
    path, n = os.path.join(parent, base), 2
    while os.path.exists(path):
        path = os.path.join(parent, f"{base}-{n}")
        n += 1
    return path


def state_path(queue):
    return os.path.join(queue, STATE)


def clear_state(queue):
    if os.path.exists(state_path(queue)):
        os.remove(state_path(queue))


def note_text(requests, today):
    """The note: the request `review` would print under "Next", then the
    others in the order `review` would reach them."""
    lines = ["# Review queue", "",
             f"Written by review.py on {today.isoformat()}. "
             "Steps are marked done on the Mac with `review done`.", ""]
    if not requests:
        return "\n".join(lines + [EMPTY]) + "\n"
    lines += ["## Next", "", requests[0].line(), ""]
    if len(requests) > 1:
        lines += ["## After that", ""]
        lines += [f"{i}. {r.line()}" for i, r in enumerate(requests[1:], 1)]
    return "\n".join(lines).rstrip("\n") + "\n"


def write_note(args, requests):
    # The vault folder is Jake's; on a machine without it, review.py still
    # does its work and says once that the note was not written, rather
    # than create a vault nobody syncs.
    folder = os.path.dirname(os.path.abspath(args.note))
    if not os.path.isdir(folder):
        print(f"review: did not write the note: no folder at {folder}", file=sys.stderr)
        return
    write_atomically(args.note, note_text(requests, args.today))


def refresh_note(args):
    """After add or done, which have already done their work: a queue that
    cannot be read leaves the note as it was and says so, but does not turn
    a finished add or done into a failure."""
    try:
        write_note(args, load_queue(args.dir))
    except QueueError as err:
        print(f"review: did not update the note: {err}", file=sys.stderr)


def show(args):
    requests = load_queue(args.dir)
    write_note(args, requests)
    if not requests:
        clear_state(args.dir)
        print(EMPTY)
        return 0
    front = requests[0]
    # Record the folder and step, not the title: two requests can share a title.
    with open(state_path(args.dir), "w", encoding="utf-8") as fh:
        fh.write(f"{front.name}\t{front.step}\n")
    print(front.line())
    return 0


def add(args):
    templates = read_templates(args.templates)
    if args.kind not in templates:
        raise QueueError(f"unknown kind {args.kind!r}; the templates list: {', '.join(sorted(templates))}")
    due = parse_date(args.due)
    if due is None:
        raise QueueError(f"due date must be YYYY-MM-DD, got {args.due!r}")
    title = " ".join(args.title.split())
    if not title:
        raise QueueError("the title is empty")
    parent = os.path.dirname(os.path.abspath(args.dir))
    if not os.path.isdir(args.dir) and not os.path.isdir(parent):
        # A mistyped path should fail, not grow a new tree in the wrong place.
        raise QueueError(f"no folder at {parent} to hold the queue")
    os.makedirs(args.dir, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "request"
    folder = unused_path(args.dir, slug)
    os.makedirs(folder)
    header = ["---", f"title: {title}", f"kind: {args.kind}", f"due: {due.isoformat()}",
              f"added: {args.today.isoformat()}", "step: 1", "---"]
    steps = [f"{minutes} | {text}" for minutes, text in templates[args.kind]]
    write_atomically(os.path.join(folder, "REQUEST.md"), "\n".join(header + steps) + "\n")
    refresh_note(args)
    print(f"added: {title} | due {due.isoformat()}")
    return 0


def done(args):
    requests = load_queue(args.dir) if os.path.isdir(args.dir) else []
    if not requests:
        if os.path.isdir(args.dir):
            clear_state(args.dir)
        raise QueueError(f"{EMPTY}, so there is no step to close")
    try:
        shown_name, shown_step = read_text(state_path(args.dir)).strip().split("\t")
    except (OSError, ValueError):
        raise QueueError("run 'review' first, so that 'done' closes a step you have seen")
    front = requests[0]
    if (front.name, str(front.step)) != (shown_name, shown_step):
        clear_state(args.dir)
        raise QueueError("the request at the front changed since 'review' showed it; run 'review' again")
    closed = front.action
    if front.step < len(front.steps):
        front.set_step(front.step + 1)
        note = ""
    else:
        archive = os.path.join(args.dir, "Archive")
        os.makedirs(archive, exist_ok=True)
        shutil.move(front.folder, unused_path(archive, front.name))
        note = " (last step; moved to Archive)"
    clear_state(args.dir)
    refresh_note(args)
    print(f"closed: {front.title} | {closed}{note}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="review", description="One next action for work owed to others.")
    parser.add_argument("--dir", default=DEFAULT_DIR, help="queue folder (default: %(default)s)")
    parser.add_argument("--templates", default=DEFAULT_TEMPLATES, help="step templates file")
    parser.add_argument("--today", default=None, help="date to use as today, YYYY-MM-DD")
    parser.add_argument("--note", default=DEFAULT_NOTE,
                        help="Obsidian note listing the queue (default: %(default)s)")
    sub = parser.add_subparsers(dest="command")
    p_add = sub.add_parser("add", help="add a request")
    p_add.add_argument("title")
    p_add.add_argument("--kind", required=True)
    p_add.add_argument("--due", required=True, help="YYYY-MM-DD")
    sub.add_parser("done", help="close the step 'review' last showed")
    args = parser.parse_args(argv)

    args.dir = os.path.expanduser(args.dir)
    args.templates = os.path.expanduser(args.templates)
    args.note = os.path.expanduser(args.note)
    if args.today is None:
        args.today = datetime.date.today()
    else:
        today = parse_date(args.today)
        if today is None:
            print(f"review: --today must be YYYY-MM-DD, got {args.today!r}", file=sys.stderr)
            return 2
        args.today = today

    try:
        return {"add": add, "done": done, None: show}[args.command](args)
    except QueueError as err:
        print(f"review: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
