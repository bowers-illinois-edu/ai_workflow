#!/usr/bin/env python3
"""Prose gate on Claude's replies, driven by style_scan.py.

Two entry points, one per hook event:

  preflight   UserPromptSubmit. Injects a short reminder immediately before
              Claude generates. This is the only half that can PREVENT a
              violation, because a Stop hook fires after the text has already
              reached the terminal and no hook can retract displayed text.
              Since 2026-09-14 the reminder carries the whole reply audit:
              the three mechanical faults, the instruction to write the draft
              to a file and scan it, and the eight reading questions from
              SKILL.md section 0.

  stop        Stop. Scans the finished reply, appends a record to a log, and
              injects a note Claude is told not to surface. It never blocks.
              Blocking would show Jake the flawed message and then a rewrite,
              which is the one outcome he ruled out.

  posttool    PostToolUse. After Write or Edit touches a prose file (.md,
              .tex, .Rmd, .qmd), or after a Bash command names one that
              changed in the last minute, scans that file and injects the
              findings as context, so the next step is to fix the file
              rather than report it done. Added 2026-09-14 so documents get
              the scan without the skill being invoked by name.

The split into tiers comes from measurement, not taste. Over 329 assistant
prose messages in 12 recent transcripts, 40% carried a mechanical violation
(212 unicode em dashes, 95 bold run-in openers, 14 em-dash + semicolon
collisions) and 16% touched a judgment category. Only the mechanical tier
admits no argument, so only it is named as a fault in the injected reminder.
Naming "costs" or "appropriate" there would teach avoidance of words rather
than of the habit, which is the failure the global CLAUDE.md warns about
directly. The reading questions the reminder carries name no words at all;
they ask about the draft.

Every path returns 0. A gate that wedges a session is worse than no gate.
"""

import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style_scan  # noqa: E402

# The categories a scan can settle without judgment. style_scan
# over-includes on purpose everywhere else, so everything not named here is
# a candidate for the judgment pass and never more than that.
MECHANICAL = frozenset({"unicode", "bold-run-in-opener", "dash-semicolon"})

# Categories that tell a reader to look twice rather than that something is
# wrong. `trailing-clause` fires on about one line in fourteen, which is cheap
# inside a reading and ruinous in a note Jake sees after every reply. The scan
# still records them; only the note leaves them out.
ATTENTION = frozenset({"trailing-clause"})

DEFAULT_LOG = os.path.expanduser("~/.claude/logs/style_gate.jsonl")

# The files the posttool entry point scans, matched without regard to case.
# These are the formats Jake writes prose in; code files stay out because
# the scanner reads comments as prose and fires on ordinary identifiers.
PROSE_SUFFIXES = (".md", ".tex", ".rmd", ".qmd", ".txt", ".docx")

# Formats the scanner cannot read. Jake chose on 2026-09-14 to leave .rtf
# unscanned and asked for a warning instead, so a file with one of these
# suffixes gets a note saying the writing rules were not checked on it, and
# the assistant is told to say so in the reply.
UNCHECKED_SUFFIXES = (".rtf",)

# Where the text of a Word file lives. A .docx is a zip archive; the words
# are in w:t elements inside w:p paragraphs in this one member. Word splits
# a paragraph into runs (w:r) wherever formatting changes, so the runs are
# joined before scanning or a pattern spanning two of them is missed.
DOCX_DOCUMENT = "word/document.xml"
DOCX_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# A Bash command names files it reads as well as files it writes. Only a
# file whose modification time is this recent counts as one the command
# wrote, so `cat old_notes.md` does not trigger a scan of a file nobody
# touched.
FRESH_SECONDS = 60

# A path-shaped token ending in a prose suffix, as it appears inside a shell
# command: heredoc targets, sed -i arguments, python scripts that name the
# file. Quotes and shell operators end a token.
_PROSE_PATH = re.compile(
    r"[^\s'\"<>|;&()`]+\.(?:md|tex|rmd|qmd|txt|docx|rtf)\b", re.IGNORECASE)

# A `cd` at the start of a command or after a connective, with its target
# bare, double-quoted, single-quoted, or absent (which means home). A
# command that changes directory names its files relative to where it went,
# and the harness reports only where the session started (Jake, 2026-09-14).
_CD = re.compile(r"""(?:^|&&|\|\||;)\s*cd(?:\s+(?:"([^"]*)"|'([^']*)'|([^\s;&|]+)))?(?=\s|;|&|\||$)""")

# After a Bash command the working directory is searched for prose files
# changed in the last minute, because a command like `f=memo.md; cat > $f`
# names no file in its text (Jake, 2026-09-14). The search skips hidden
# directories, which is where .git and caches live, and gives up after this
# many entries so a stray data tree cannot stall a turn.
WALK_LIMIT = 20000

# The most findings one note lists. A first draft of a long memo can carry
# hundreds, and a note that long buries the next instruction.
NOTE_LIMIT = 30

# The reading check on a reply, copied from SKILL.md section 0. The gate
# carries its own copy for the same reason style_scan carries RAW_PATTERNS:
# a hook cannot parse a skill file on every turn. test_style_gate pins the
# count here to the count in section 0, so the copies cannot drift silently.
# Each question asks about the draft and never names a word, because a named
# word teaches avoidance of that word rather than of the habit behind it.
QUESTIONS = (
    "Is every technical term spelled out where it first appears?",
    "Does each passage say what question it answers, before it answers it?",
    "Is every other term one Jake can resolve from what is on the page?",
    "Does every sentence give its action to a person?",
    "Does every pronoun have exactly one antecedent?",
    "Does any sentence end in a clause that adds nothing?",
    "Does every therefore have its premise in the sentence before it?",
    "Is any word one Jake did not give you, chosen by you or carried in "
    "from a file he has not read?",
)

# Rides on every single turn, so it stays under 1700 characters. Until
# 2026-09-14 it named only the three mechanical faults. The gate's log then
# showed 15 replies with a mechanical fault in two weeks against a pre-gate
# rate of 40 percent, so the adjacent reminder does what it names, and what
# Jake still stopped on was the part it left out: the reading.
PREFLIGHT = "\n".join(
    ["Before sending your reply, run the check CLAUDE.md requires. Reread",
     "after drafting, never during. First the three faults a scan settles:",
     "1. No unicode. Write --- for an em dash, -- for an en dash, -> for an",
     "   arrow, and straight quotes.",
     "2. No paragraph opening with a bold run-in sentence.",
     "3. No line carrying an em dash and a semicolon together.",
     "Then the reading, which no scan can do. Write the draft to a file in",
     "your scratchpad, run skills/style-audit/scripts/style_scan.py on it,",
     "and read the draft against these eight questions:"]
    + ["%d. %s" % (i, q) for i, q in enumerate(QUESTIONS, 1)]
    + ["Fix what you find, then send. Fenced code is exempt from the scan."])


def ascii_only(text):
    """Replace any non-ASCII character with a printable escape.

    The note this builds quotes text that Claude just wrote, which is
    precisely the text most likely to contain the character being reported.
    Injecting it raw would put the banned character back into context.
    """
    out = []
    for ch in text:
        out.append(ch if ord(ch) <= 126 else "<U+%04X>" % ord(ch))
    return "".join(out)


def scan_message(text):
    """Scan prose, skipping fenced and inline code as style_scan does for .md.

    Claude shows shell and R in most replies, where 'sandbox', 'pipeline'
    and 'costs' are ordinary words. Scanning fences would fire on nearly
    every message carrying a command.

    Inline code is skipped for a second reason. build_note names the word it
    matched, so any reply passing that word on to Jake was logged as a fresh
    violation of its own: two lines from one offence, and the extra line
    arrived exactly in the sessions spent working on the gate. Code marks
    give a reply a way to name an offender without using it.
    """
    findings = []
    in_fence = False
    for lineno, line in enumerate(text.split("\n"), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        style_scan.scan_line("reply", lineno, line, findings,
                             strip_inline_code=True)
    return findings


def tier_of(findings):
    """Mechanical wins the label, since it is the half that admits no
    argument and so the half worth watching over time."""
    cats = {cat for (_p, _n, cat, _t) in findings}
    return "mechanical" if cats & MECHANICAL else "judgment"


def build_note(findings):
    """The context injected after a dirty reply.

    It lands at the start of Claude's next turn. The instruction not to
    mention it matters: a note Claude comments on becomes the doubled
    message by another route, which is what Jake asked to avoid.
    """
    cats = {}
    for (_p, _n, cat, matched) in findings:
        if cat in ATTENTION:
            continue
        cats.setdefault(cat, []).append(matched)
    if not cats:
        return None

    lines = ["Your last reply broke the writing rules in these places:"]
    for cat in sorted(cats):
        shown = ", ".join(sorted(set(cats[cat]))[:4])
        lines.append("  %s: %s" % (cat, ascii_only(shown)))
    lines.append("")
    lines.append("Apply this to what you write from here on. Do not mention "
                 "this note to the user and do not resend the last reply.")
    return "\n".join(lines)


def is_prose_path(path):
    return path.lower().endswith(PROSE_SUFFIXES)


def is_unchecked_path(path):
    return path.lower().endswith(UNCHECKED_SUFFIXES)


def effective_cwd(command, cwd):
    """The directory a command's relative names refer to after its `cd`s.

    Each `cd` is followed in order from the reported working directory. A
    `cd` to a directory that does not exist leaves the answer unknown, and
    None tells the caller to resolve nothing relative and search nowhere.
    """
    current = cwd or ""
    for match in _CD.finditer(command):
        target = match.group(1) or match.group(2) or match.group(3) or "~"
        target = os.path.expanduser(target)
        if not os.path.isabs(target):
            if not current:
                return None
            target = os.path.join(current, target)
        if not os.path.isdir(target):
            return None
        current = os.path.abspath(target)
    return current or None


def paths_in_command(command):
    """Every distinct prose path a shell command mentions, in order."""
    seen = []
    for match in _PROSE_PATH.finditer(command):
        path = match.group(0)
        if path not in seen:
            seen.append(path)
    return seen


def changed_recently(path, now=None):
    try:
        mtime = os.stat(path).st_mtime
    except OSError:
        return False
    return (now if now is not None else time.time()) - mtime <= FRESH_SECONDS


def files_to_scan(event):
    """The prose files a finished tool call may have written.

    Write and Edit name their file. Bash names nothing, so the command text
    is read for prose paths and each one that exists and changed in the last
    minute is taken as written by the command. This is a heuristic: a path
    built from a shell variable is invisible to it, and it scans a file the
    command merely read if something else changed that file a moment ago.
    Both errors are cheap, since the worst case is a scan of a prose file.
    """
    tool = event.get("tool_name") or ""
    tool_input = event.get("tool_input") or {}
    cwd = event.get("cwd") or ""
    if tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        path = tool_input.get("file_path") or ""
        if path and os.path.isfile(path) and (is_prose_path(path)
                                              or is_unchecked_path(path)):
            return [path]
        return []
    if tool == "Bash":
        command = tool_input.get("command") or ""
        base = effective_cwd(command, cwd)
        found = []
        for path in paths_in_command(command) + fresh_prose_files(base):
            if not os.path.isabs(path):
                if not base:
                    continue
                path = os.path.join(base, path)
            path = os.path.abspath(path)
            if path in found:
                continue
            if os.path.isfile(path) and changed_recently(path):
                found.append(path)
        return found
    return []


def fresh_prose_files(root, now=None):
    """Prose files under root changed in the last minute, hidden dirs skipped."""
    if not root or not os.path.isdir(root):
        return []
    found, seen = [], 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            seen += 1
            if seen > WALK_LIMIT:
                return found
            if is_prose_path(name) or is_unchecked_path(name):
                path = os.path.join(dirpath, name)
                if changed_recently(path, now):
                    found.append(path)
    return found


def docx_findings(path):
    """Scan a Word file one paragraph per line; the line number in each
    finding is the paragraph number. Anything that is not a readable Word
    file yields nothing, since the gate must never wedge a turn."""
    findings = []
    try:
        with zipfile.ZipFile(path) as zf:
            root = ET.fromstring(zf.read(DOCX_DOCUMENT))
    except (zipfile.BadZipFile, KeyError, ET.ParseError, OSError):
        return findings
    for number, para in enumerate(root.iter(DOCX_NS + "p"), 1):
        text = "".join(t.text or "" for t in para.iter(DOCX_NS + "t"))
        style_scan.scan_line(path, number, text, findings)
    return findings


def unchecked_note(path):
    """For a format the scanner cannot read: no findings, one warning, and
    the instruction to pass the warning on, since the note itself reaches
    only the assistant."""
    return ("The file you just wrote, %s, is in a format the writing rules "
            "are not checked on: the scanner does not read %s files, so "
            "nothing in it has been checked. Tell Jake that in your reply, "
            "in those words, when you report the file."
            % (os.path.basename(path), os.path.splitext(path)[1].lower()))


def scan_path(path):
    if path.lower().endswith(".docx"):
        return docx_findings(path)
    return style_scan.scan_file(path, True)


def build_file_note(path, findings):
    """The context injected after a tool writes a dirty prose file.

    Unlike build_note this lists judgment candidates as well as mechanical
    faults, because the reader of this note is about to reread the file
    anyway and a candidate costs one glance there. The attention categories
    stay out for the reason given at ATTENTION. The closing instruction
    names the eight questions so that a clean scan is not read as a clean
    file: the scan is the mechanical half of the audit and no more.
    """
    shown = [(n, cat, matched) for (_p, n, cat, matched) in findings
             if cat not in ATTENTION]
    if not shown:
        return None
    unit = "paragraph" if path.lower().endswith(".docx") else "line"
    lines = ["The file you just wrote, %s, breaks the writing rules here:"
             % os.path.basename(path)]
    for (n, cat, matched) in shown[:NOTE_LIMIT]:
        lines.append("  %s %d, %s: %s" % (unit, n, cat, ascii_only(matched)))
    if len(shown) > NOTE_LIMIT:
        lines.append("  ... and %d more." % (len(shown) - NOTE_LIMIT))
    lines.append("")
    lines.append("Fix these in the file before reporting it done. Then read "
                 "the file against the eight questions in section 0 of the "
                 "style-audit skill, which the scan cannot answer.")
    return "\n".join(lines)


def run_posttool(stdin_text, log_path):
    event = json.loads(stdin_text)
    notes = []
    for path in files_to_scan(event):
        if is_unchecked_path(path):
            findings, note, tier = [], unchecked_note(path), "unchecked"
        else:
            findings = scan_path(path)
            note = build_file_note(path, findings)
            tier = tier_of(findings)
        if note is None:
            continue
        cats = sorted({cat for (_p, _n, cat, _t) in findings})
        record = {"time": time.strftime("%Y-%m-%dT%H:%M:%S"),
                  "session_id": event.get("session_id"),
                  "file": path,
                  "tier": tier,
                  "categories": cats,
                  "count": len(findings)}
        try:
            append_log(log_path or DEFAULT_LOG, record)
        except OSError:
            pass
        notes.append(note)
    if notes:
        emit("PostToolUse", "\n\n".join(notes))
    return 0


def emit(event_name, context):
    """Write a hook envelope to stdout."""
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": event_name,
        "additionalContext": context}}))


def append_log(log_path, record):
    """Best effort. Losing a measurement is cheaper than losing the session,
    so every failure here is swallowed by the caller."""
    directory = os.path.dirname(log_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


def run_stop(stdin_text, log_path):
    event = json.loads(stdin_text)
    message = event.get("last_assistant_message") or ""
    if not message.strip():
        return 0

    findings = scan_message(message)
    if not findings:
        return 0

    cats = sorted({cat for (_p, _n, cat, _t) in findings})
    record = {"time": time.strftime("%Y-%m-%dT%H:%M:%S"),
              "session_id": event.get("session_id"),
              "prompt_id": event.get("prompt_id"),
              "tier": tier_of(findings),
              "categories": cats,
              "count": len(findings)}
    try:
        append_log(log_path or DEFAULT_LOG, record)
    except OSError:
        pass  # the note below is worth sending even with no log

    note = build_note(findings)
    if note is not None:
        emit("Stop", note)
    return 0


def main(argv, stdin_text, log_path):
    """Always returns 0. The bare except is deliberate: any failure at all,
    including one this code does not anticipate, must leave the session
    untouched rather than block a turn or print a broken envelope."""
    try:
        if not argv:
            return 0
        if argv[0] == "preflight":
            emit("UserPromptSubmit", PREFLIGHT)
            return 0
        if argv[0] == "stop":
            return run_stop(stdin_text, log_path)
        if argv[0] == "posttool":
            return run_posttool(stdin_text, log_path)
        return 0
    except Exception:
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], sys.stdin.read(), DEFAULT_LOG))
