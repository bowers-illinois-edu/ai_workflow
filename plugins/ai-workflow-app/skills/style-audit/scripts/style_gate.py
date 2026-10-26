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
              the scan without the skill being invoked by name. Since
              2026-10-26 the first save of a document in a session also
              asks for the style-audit skill before the reply, clean scan
              or not, so that audit_guard.py rarely has to ask after it.

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

import glob
import json
import os
import re
import subprocess
import sys
import tempfile
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

# Folders whose files never reach the reader or a note. Since 2026-10-25
# sessions started in ~/repos/mail-extract run inside Claude Code's sandbox,
# which keeps them out of Thunderbird's copy of Jake's mail and out of the
# extractor's output. `check` cannot run inside the sandbox, because
# `claude -p` writes under ~/.claude, so it runs outside it, where it could
# open any file. It sends the file it is given to the reader and prints the
# scanner's matches, which quote the file, so without this list a session
# could pass it a mail file and read the mail through it.
PRIVATE_DIRS = (os.path.expanduser("~/Library/Thunderbird"),
                os.path.expanduser("~/mail-extract-output"))

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
    "Does each passage say what question it answers, before it answers it? "
    "Can you name what answering it does for the stated point of the project?",
    "Is every other term one Jake can resolve from what is on the page?",
    "Does every sentence give its action to a person?",
    "Does every pronoun have exactly one antecedent?",
    "Does any sentence end in a clause that adds nothing?",
    "Does every therefore have its premise in the sentence before it?",
    "Is any word one Jake did not give you, chosen by you or carried in "
    "from a file he has not read?",
)

# Rides on every single turn. Until 2026-09-14 it named only the three
# mechanical faults; from then until 2026-09-20 it also carried the eight
# reading questions. Jake objected to 55 chat replies in those six days, all
# written with the questions in front of the writer, and on 2026-09-20 he
# traced three faults in one reply to the rules themselves: "pass mark" from
# avoiding a listed word, "One decision is yours" from a rule about where
# decisions go, and a clipped sentence from the length rules. So the
# questions went to the second reader, and the note now says to run it.
PREFLIGHT = "\n".join(
    ["Before sending your reply, write the draft to a file in your scratchpad",
     "and run",
     "  python3 %s check <that file>" % os.path.abspath(__file__),
     "It runs the scanner and then a second reader, who has only what Jake",
     "has seen and asks what each sentence means. Fix what it reports, then",
     "send. Open by restating what Jake asked and what he wants it for, then",
     "answer it. Then say what you need",
     "from him and why. Say nothing about your own process. Write --- for",
     "an em dash and no other unicode, no bold sentence opening a paragraph,",
     "and no em dash and semicolon on one line. Fenced code is exempt. The",
     "check takes one to three minutes, so give the Bash call a timeout of",
     "300000."])


# Memory between hook calls, kept beside the log. It holds, per session and
# file, the findings last reported, so that a rescan reports only what is
# new; and the sentences of each draft that went through `check`, so that
# the Stop hook can say whether the reply Jake saw was the checked one.
# Measured 2026-09-20: of 2156 file notes sent since 2026-09-14, 1675 were
# byte-identical to the note just sent for the same file.
STATE_NAME = "style_gate_state.json"

# A checked draft is remembered this long. A reply is written within minutes
# of its check; anything older is a different reply.
CHECKED_TTL_SECONDS = 2 * 60 * 60

# The share of a reply's sentences that must appear in a checked draft for
# the reply to count as checked. An assistant fixes a word or two after the
# check, and that must still count; a reply rewritten from scratch must not.
CHECKED_OVERLAP = 0.6

# How much of the session the reader is shown: the last few things Jake
# typed and the assistant's replies to them, capped in characters so that a
# long session does not make every check slow.
CONTEXT_TURNS = 4
CONTEXT_CHARS = 24000

# Which model reads. Measured 2026-09-20 on the 31 replies Jake stopped on
# that week; see memo_reply_check_2026-09-20.md.
READER_MODEL = "sonnet"

# Set in the reader's environment so that the hooks inside its session know
# they are running under the reader and stay silent.
READER_MARK = "STYLE_GATE_READER"
READER_TIMEOUT = 240

# What the project is for, in the project's own file. Jake confirms it, so
# the reader may see it although it is not part of the conversation. On
# 2026-10-15 he asked that every passage be traceable to the point of the
# project; before then the reader could ask only whether a passage states
# its own question, and a passage answering a question the project does not
# need passed. A statement of the point is a few sentences, so the cap only
# stops a wrong file from crowding out the conversation.
POINT_NAME = "POINT.md"
POINT_CHARS = 6000
NO_POINT = "(no statement of the point is on file for this project)"

# What the reader is told. Two prompts were measured on 2026-09-20 against
# the 31 replies Jake had stopped on that week (memo_reply_check_2026-09-20.md).
# This one, the eight questions of SKILL.md section 0 plus three about the
# reply as a whole, pointed at 13 of the 46 phrases he quoted, in 46 to 63
# seconds a call. Jake's own specification, restating every sentence and
# swapping its nouns, pointed at 11 in 94 seconds a call. The two counts are
# not distinguishable on 46 phrases, so the faster one is installed. It
# names no words, for the reason given at the top of SKILL.md section 6.
READER_PROMPT = """TASK: An assistant is about to send Jake Bowers the reply below, in a terminal. You have what Jake has seen: the statement of what this project is for, which Jake has confirmed, then the earlier messages in this conversation, and nothing else. You have not seen the assistant's files, scripts, or tool output, and neither has Jake.

Read the reply as Jake, sentence by sentence. For each sentence ask: what does this sentence mean? Could I restate it in other words? If I replaced the nouns with other nouns, would the verbs still make sense, which would mean the verbs are decorative? Then ask these questions of the reply:
%s
9. Does the reply open by restating the question Jake asked, with what he wants it for, and answering it?
10. Is any sentence a fragment with no main verb?
11. Does the reply say more than the answer needs?

Output a JSON array only, no prose before or after. Each element: {"phrase": "<exact words copied from the reply, 1 to 12 words>", "why": "<one short sentence>"}. Flag a place only when Jake would stop there: he cannot say what the sentence means, a word is used without the sentence fixing what it means, a pronoun has two possible antecedents, a sentence has no main verb, the passage never says what question it answers, or you cannot name what the passage does for the stated point. If nothing, output [].

THE POINT OF THE PROJECT:
%s

EARLIER MESSAGES:
%s

REPLY START
%s
REPLY END
""" % ("\n".join("%d. %s" % (k + 1, q) for k, q in enumerate(QUESTIONS)), "%s", "%s", "%s")

# Text in a user record that the harness injected rather than Jake typed.
# Copied from first-reader/scripts/mine_transcripts.py, which the gate cannot
# import: a hook must not depend on a second skill being installed.
MACHINERY_PREFIXES = (
    "<local-command", "<command-name", "<command-message", "<command-args",
    "<user-memory", "<system-reminder", "<bash-", "[Request interrupted",
    "Caveat:", "Another Claude session")


def state_path(log_path):
    return os.path.join(os.path.dirname(log_path or DEFAULT_LOG), STATE_NAME)


def load_state(path):
    """The memory, or an empty one when it cannot be read. A missing or
    corrupt file means the gate has forgotten, which only costs a repeated
    note."""
    try:
        with open(path, encoding="utf-8") as fh:
            state = json.load(fh)
    except (OSError, ValueError):
        return {}
    return state if isinstance(state, dict) else {}


def save_state(path, state):
    """Raises OSError; the caller decides that losing the memory is fine."""
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(state, fh)


def sentences_of(text):
    """The sentences of a reply, normalized so that a change of spacing or
    case between draft and reply does not make them different sentences.
    Fenced code is dropped, since the scanner never reads it either."""
    kept, in_fence = [], False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            kept.append(line)
    flat = re.sub(r"\s+", " ", " ".join(kept)).strip().lower()
    parts = re.split(r"(?<=[.!?])\s+", flat)
    return [p for p in parts if len(p) > 3]


def remember_checked(state, text, now=None):
    now = now if now is not None else time.time()
    drafts = [d for d in state.get("checked_drafts", [])
              if now - d.get("time", 0) <= CHECKED_TTL_SECONDS]
    drafts.append({"time": now, "sentences": sentences_of(text)})
    state["checked_drafts"] = drafts


def was_checked(state, text, now=None):
    now = now if now is not None else time.time()
    mine = sentences_of(text)
    if not mine:
        return False
    for d in state.get("checked_drafts", []):
        if now - d.get("time", 0) > CHECKED_TTL_SECONDS:
            continue
        theirs = set(d.get("sentences", []))
        share = sum(1 for s in mine if s in theirs) / float(len(mine))
        if share >= CHECKED_OVERLAP:
            return True
    return False


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


def is_private_path(path):
    """True when `path` lies in or under one of PRIVATE_DIRS.

    The path is resolved first, so a symlink elsewhere that points into a
    private folder, or a name that climbs into one through "..", counts as
    inside it. Spelling alone is not enough after that: a Mac disk ignores
    letter case, so ~/library/THUNDERBIRD is the same folder as
    ~/Library/Thunderbird, and os.path.realpath keeps whatever case it was
    given. So each folder on the way up from the resolved path is also
    compared with each private folder by device and inode. Both comparisons
    go by whole folders, so mail-extract-output-old is not private.
    """
    real = os.path.realpath(path)
    identities = set()
    for d in PRIVATE_DIRS:
        root = os.path.realpath(d).rstrip(os.sep)
        if real.lower() == root.lower() or real.lower().startswith(root.lower() + os.sep):
            return True
        try:
            st = os.stat(root)
        except OSError:
            continue  # a private folder that is missing or unreadable holds nothing to compare
        identities.add((st.st_dev, st.st_ino))
    current = real
    while identities:
        try:
            st = os.stat(current)
            if (st.st_dev, st.st_ino) in identities:
                return True
        except OSError:
            pass  # a name that does not exist; the folders above it still count
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return False


def is_prose_path(path):
    return path.lower().endswith(PROSE_SUFFIXES)


def is_unchecked_path(path):
    return path.lower().endswith(UNCHECKED_SUFFIXES)


def default_scratch_roots():
    """Directories whose files are drafts, not documents. The assistant
    drafts every reply in its scratchpad under the system's temporary
    directory and checks it with `style_gate.py check`."""
    roots = {"/tmp", "/private/tmp", tempfile.gettempdir()}
    if os.environ.get("TMPDIR"):
        roots.add(os.environ["TMPDIR"])
    return tuple(sorted(roots))


def _under(path, root):
    """True when `path` is `root` or inside it, compared both as written and
    with links resolved, because /tmp on a Mac is a link to /private/tmp."""
    for p, r in ((os.path.abspath(path), os.path.abspath(root)),
                 (os.path.realpath(path), os.path.realpath(root))):
        r = r.rstrip(os.sep)
        if p == r or p.startswith(r + os.sep):
            return True
    return False


def is_document(path, home, scratch_roots):
    """A prose file that leaves the desk: not a reply draft in the scratch
    area, which `check` covers, and not memory or settings under ~/.claude.
    audit_guard.py uses this same test."""
    if not path or not is_prose_path(path):
        return False
    if any(_under(path, root) for root in scratch_roots):
        return False
    return not _under(path, os.path.join(home, ".claude"))


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
        if path and is_private_path(path):
            return []  # the note would quote the file; see PRIVATE_DIRS
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
            if path in found or is_private_path(path):
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


# Added to the note the first time in a session that a document is saved.
# Jake chose on 2026-10-26 (memo_audit_guard_in_focus_view_2026-10-26.md)
# that when audit_guard.py has to ask for the audit after a reply, the reply
# goes out a second time, because focus view shows only the last message of
# a turn. Asking here, before the reply, is what keeps that rare. Once per
# document and session, because the audit's own fixes are saves of the same
# file and a second request would start the audit over.
AUDIT_REQUEST = ("Before you write to Jake, run the style-audit skill on %s, "
                 "which asks the eight questions the scan cannot answer. "
                 "Not both-passes, not first-reader.")


def run_posttool(stdin_text, log_path, home=None, scratch_roots=None):
    event = json.loads(stdin_text)
    session = event.get("session_id") or ""
    home = home or os.path.expanduser("~")
    if scratch_roots is None:
        scratch_roots = default_scratch_roots()
    spath = state_path(log_path)
    state = load_state(spath)
    seen = state.setdefault("file_notes", {})
    asked = state.setdefault("audit_asked", {})
    notes = []
    for path in files_to_scan(event):
        key = session + "|" + path
        request = None
        # Keyed by the resolved path, because a file reached through a
        # linked directory has two names; audit_guard.py does the same.
        asked_key = session + "|" + os.path.realpath(path)
        if is_document(path, home, scratch_roots) and not asked.get(asked_key):
            asked[asked_key] = True
            request = AUDIT_REQUEST % os.path.basename(path)
        if is_unchecked_path(path):
            findings, tier = [], "unchecked"
            current = [["unchecked", ""]]
            note = None if seen.get(key) == current else unchecked_note(path)
        else:
            findings = scan_path(path)
            tier = tier_of(findings)
            current = sorted({(cat, matched) for (_p, _n, cat, matched)
                              in findings if cat not in ATTENTION})
            current = [list(c) for c in current]
            before = {tuple(c) for c in seen.get(key, [])}
            # Only what this session has not been told about this file.
            fresh = [f for f in findings if (f[2], f[3]) not in before]
            note = build_file_note(path, fresh)
        seen[key] = current
        if note is not None:
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
        # After the findings, so the model reads what to fix first.
        if request is not None:
            notes.append(request)
    try:
        save_state(spath, state)
    except OSError:
        pass  # the gate forgets, and repeats a note, which is the old behaviour
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
    cats = sorted({cat for (_p, _n, cat, _t) in findings})
    state = load_state(state_path(log_path))
    record = {"time": time.strftime("%Y-%m-%dT%H:%M:%S"),
              "session_id": event.get("session_id"),
              "prompt_id": event.get("prompt_id"),
              "tier": tier_of(findings) if findings else "clean",
              "categories": cats,
              "count": len(findings),
              "checked": was_checked(state, message)}
    try:
        append_log(log_path or DEFAULT_LOG, record)
    except OSError:
        pass  # the note below is worth sending even with no log

    if not findings:
        return 0
    note = build_note(findings)
    if note is not None:
        emit("Stop", note)
    return 0


def visible_turns(transcript_path, turns=CONTEXT_TURNS, chars=CONTEXT_CHARS):
    """What Jake has seen of the session: the turns he typed and the prose
    the assistant wrote back, in order. Tool calls, tool results, thinking
    and injected text are left out, because they never reached his screen.
    Returns the last `turns` of them, trimmed to `chars` characters."""
    if not transcript_path or not os.path.isfile(transcript_path):
        return []
    out = []
    with open(transcript_path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            kind = rec.get("type")
            msg = rec.get("message") or {}
            content = msg.get("content")
            if kind == "user" and not rec.get("isMeta"):
                origin = (rec.get("origin") or {}).get("kind")
                if origin is not None and origin != "human":
                    continue
                text = content if isinstance(content, str) else ""
                if text and not text.lstrip().startswith(MACHINERY_PREFIXES):
                    out.append(("JAKE", text))
            elif kind == "assistant" and isinstance(content, list):
                text = "\n".join(b.get("text", "") for b in content
                                 if isinstance(b, dict)
                                 and b.get("type") == "text").strip()
                if text:
                    out.append(("ASSISTANT", text))
    # Keep the last `turns` things Jake typed and everything the assistant
    # said after the first of them. Counting assistant turns would let a run
    # of short status lines push Jake's own words out of the window.
    jake_at = [i for i, (role, _t) in enumerate(out) if role == "JAKE"]
    if len(jake_at) > turns:
        out = out[jake_at[-turns]:]
    total = sum(len(t) for (_r, t) in out)
    while len(out) > 1 and total > chars:
        total -= len(out[0][1])
        out.pop(0)
    return out


def newest_transcript(cwd=None, home=None, session_id=None):
    """The transcript of the live session. Claude Code puts its session id
    in the shell's environment as CLAUDE_CODE_SESSION_ID, and keeps one
    JSONL per session under ~/.claude/projects/<flattened cwd>/. The id is
    decisive when it is set, because two sessions can run in one directory
    and the newer file is then the other session's (2026-09-20). Without
    it, the newest file in the directory's folder is taken."""
    cwd = cwd or os.getcwd()
    home = home or os.path.expanduser("~")
    session_id = session_id or os.environ.get("CLAUDE_CODE_SESSION_ID")
    if session_id:
        named = glob.glob(os.path.join(home, ".claude", "projects", "*",
                                       session_id + ".jsonl"))
        if named:
            return max(named, key=os.path.getmtime)
    # Claude Code flattens the path by turning every character that is not
    # a letter or digit into a hyphen, so /repos/ai_workflow becomes
    # -repos-ai-workflow.
    flat = re.sub(r"[^A-Za-z0-9]", "-", cwd)
    paths = glob.glob(os.path.join(home, ".claude", "projects", flat, "*.jsonl"))
    if not paths:
        return None
    return max(paths, key=os.path.getmtime)


def call_reader(prompt):
    """The real second reader: one `claude -p` call with no tools and no
    saved session. Raises on any failure; run_check reports it."""
    # A new session so that a timeout can kill the whole process group:
    # `claude` starts helpers that hold its pipes open, and killing only the
    # parent leaves communicate() waiting for those pipes forever, which is
    # what stalled the first live run on 2026-09-20.
    # The reader is itself a Claude session with Jake's hooks, so without
    # this mark its own Stop hook would log its output as one more unchecked
    # reply. Measured 2026-09-20: 40 such lines in one evening.
    env = dict(os.environ, **{READER_MARK: "1"})
    proc = subprocess.Popen(
        ["claude", "-p", "--model", READER_MODEL, "--no-session-persistence",
         "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, start_new_session=True, env=env)
    try:
        out, err = proc.communicate(prompt, timeout=READER_TIMEOUT)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, 9)
        except OSError:
            pass
        raise OSError("the reader took longer than %d seconds" % READER_TIMEOUT)
    if proc.returncode != 0:
        raise OSError(err.strip()[-200:] or "claude -p failed")
    return out


def parse_reader(raw):
    """The JSON array in the reader's output, or None. The reader sometimes
    wraps it in a code fence or a sentence of its own."""
    match = re.search(r"\[.*\]", raw or "", re.S)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
    except ValueError:
        return None
    return parsed if isinstance(parsed, list) else None



def find_point_file(start=None, stop=None):
    """The project's POINT.md, found by walking up from the working directory.

    `check` is run from the assistant's shell, whose working directory is the
    project the reply is about. The walk stops at the first directory holding
    .git, the project root, so that a POINT.md belonging to something above
    the project is never read as this project's, and it stops at the home
    directory when there is no repository at all.
    """
    d = os.path.abspath(start or os.getcwd())
    stop = os.path.abspath(stop or os.path.expanduser("~"))
    while True:
        candidate = os.path.join(d, POINT_NAME)
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(d)
        if os.path.exists(os.path.join(d, ".git")) or d == stop or parent == d:
            return None
        d = parent


def read_point(path):
    """The text of a statement of the point, cut at POINT_CHARS; None when
    the file cannot be read, so the reader is told none is on file."""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read(POINT_CHARS).strip() or None
    except OSError:
        return None


def parse_check_args(argv):
    """`check <draft> [--transcript <path>] [--point <path>]`. A flag with no
    value after it is ignored, and the caller fills in what is missing."""
    def flag(name):
        return argv[argv.index(name) + 1] if name in argv[:-1] else None
    return argv[1], flag("--transcript"), flag("--point")


def run_check(draft_path, log_path, transcript_path=None, reader=call_reader,
              point_path=None):
    """The check the assistant runs on a draft reply before sending it.

    Prints the scanner's findings, then the second reader's, and remembers
    the draft so the Stop hook can tell whether the reply that went out was
    this one. Every failure is printed rather than swallowed, because the
    assistant is reading this output and a silent failure would look like a
    clean draft.
    """
    # Before anything opens a file: a refusal must send nothing to the
    # reader and print nothing from the file. See PRIVATE_DIRS.
    for label, path in (("the draft", draft_path),
                        ("the --transcript file", transcript_path),
                        ("the --point file", point_path)):
        if path and is_private_path(path):
            print("Refused: %s is in a private folder (%s). Nothing was "
                  "scanned or sent to the reader."
                  % (label, ", ".join(PRIVATE_DIRS)))
            return 0

    try:
        with open(draft_path, encoding="utf-8", errors="replace") as fh:
            draft = fh.read()
    except OSError as e:
        print("cannot read the draft: %s" % e)
        return 0

    findings = style_scan.scan_file(draft_path, True)
    faults = [f for f in findings if f[2] not in ATTENTION]
    looks = [f for f in findings if f[2] in ATTENTION]
    printed = False
    if faults:
        print("Scanner: fix these.")
        for (_p, n, cat, matched) in faults:
            print("  line %d, %s: %s" % (n, cat, ascii_only(matched)))
        printed = True
    if looks:
        print("Scanner: read each of these twice; split the sentence if the "
              "clause carries a second point, cut it if it carries none.")
        for (_p, n, cat, matched) in looks:
            print("  line %d: %s" % (n, ascii_only(matched)))
        printed = True

    context = visible_turns(transcript_path)
    shown = "\n\n".join("%s: %s" % (role, text) for (role, text) in context)
    point = read_point(point_path) if point_path else None
    prompt = READER_PROMPT % (point or NO_POINT,
                              shown or "(this reply opens the session)", draft)
    stops = None
    reader_error = None
    try:
        stops = parse_reader(reader(prompt))
    except Exception as e:  # noqa: BLE001 - any failure is reported, none hides
        reader_error = ascii_only(str(e))[:200]
    if stops is None:
        print("Reader did not run: %s" % (reader_error or "no findings came back."))
        printed = True
    else:
        # Two output shapes are accepted: a phrase per finding, which the
        # installed prompt asks for, and a verdict per sentence, which the
        # per-sentence prompt asked for.
        flagged = [s for s in stops if isinstance(s, dict)
                   and (s.get("phrase")
                        or str(s.get("verdict", "")).lower() == "stop")]
        if flagged:
            print("Reader: Jake would stop here.")
            for s in flagged:
                words = ascii_only(str(s.get("phrase") or s.get("words")
                                       or s.get("sentence") or ""))
                print("  %s -- %s" % (words, ascii_only(str(s.get("why") or ""))))
            printed = True
    if not printed:
        print("Nothing found by the scanner or the reader.")
    # Said every time, because a reader that found nothing and a reader never
    # shown the point print the same findings, and the search for POINT.md
    # starts from the shell's working directory, which a `cd` can move.
    if point:
        print("Point: %s" % point_path)
    else:
        print("Point: none on file (searched upward from %s)" % os.getcwd())

    spath = state_path(log_path)
    state = load_state(spath)
    remember_checked(state, draft)
    try:
        save_state(spath, state)
    except OSError as e:
        print("Could not record the check: %s" % e)
    return 0


def main(argv, stdin_text, log_path):
    """Always returns 0. The bare except is deliberate: any failure at all,
    including one this code does not anticipate, must leave the session
    untouched rather than block a turn or print a broken envelope."""
    try:
        if not argv:
            return 0
        if os.environ.get(READER_MARK) and argv[0] != "check":
            return 0  # inside the reader's own session: no log, no notes
        if argv[0] == "preflight":
            emit("UserPromptSubmit", PREFLIGHT)
            return 0
        if argv[0] == "stop":
            return run_stop(stdin_text, log_path)
        if argv[0] == "posttool":
            return run_posttool(stdin_text, log_path)
        if argv[0] == "check" and len(argv) > 1:
            draft, transcript, point = parse_check_args(argv)
            return run_check(draft, log_path,
                             transcript or newest_transcript(),
                             point_path=point or find_point_file())
        return 0
    except Exception as e:  # noqa: BLE001
        if argv and argv[0] == "check":
            print("check failed: %s" % e)
        return 0


def reads_stdin(argv):
    """Only the hook entry points get an event on stdin. `check` is run by
    the assistant from a shell whose stdin may never close, and reading it
    there blocked every live run on 2026-09-20 until the process was killed."""
    return bool(argv) and argv[0] in ("stop", "posttool")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:],
                  sys.stdin.read() if reads_stdin(sys.argv[1:]) else "",
                  DEFAULT_LOG))
