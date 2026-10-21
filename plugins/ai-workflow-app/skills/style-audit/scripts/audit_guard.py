#!/usr/bin/env python3
"""Stop hook: keep a turn going until every document saved in it has been
through the style audit.

Jake, 2026-10-15: "I kind of hate having to constantly say 'did you do a full
style-audit' and being told 'Oh no! I need to do it. Please wait...'" The
rules told the assistant to audit every document before reporting it done,
and style_gate.py's PostToolUse note reminded it after every saved prose
file. The same day the assistant saved a memo, ran only the reply check on
it, and reported it done. A reminder in front of the writer did not make the
writer audit. A Stop hook can refuse to let the turn end, which this one does
until the style-audit skill has run on every document saved since Jake's
last message.

It asks for the style audit alone. Jake does not want both-passes run
routinely, because the first-reader agent it starts takes about ten minutes.

Usage, as a Claude Code Stop hook:

    python3 audit_guard.py        (reads the Stop event on stdin)

The decision rules are pinned by tests/test_audit_guard.py.
"""

import calendar
import json
import os
import re
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style_gate  # noqa: E402

READER_MARK = style_gate.READER_MARK

DEFAULT_LOG = os.path.expanduser("~/.claude/logs/audit_guard.jsonl")

# Skills whose run counts as an audit. both-passes runs style-audit, so a
# both-passes run that happened counts, though the guard never asks for one.
AUDIT_SKILLS = ("style-audit", "both-passes")

# Jake typing the skill as a command shows up as a user record carrying this
# tag, with or without a plugin prefix such as "ai-workflow-app:".
_AUDIT_COMMAND = re.compile(
    r"<command-name>/(?:[\w-]+:)?(?:style-audit|both-passes)</command-name>")

# Tools that save a file named in their input.
SAVE_TOOLS = ("Write", "Edit", "MultiEdit")

# Where the list of unaudited documents is written, one path per line, in
# a file named for the session. Claude Code draws Stop feedback in the
# terminal, in full, so the feedback names this file instead of listing the
# paths. It goes under the system's temporary directory and not under
# ~/.claude, which auto mode has refused to let the model read.
DEFAULT_LIST_DIR = tempfile.gettempdir()


def list_path(list_dir, session_id):
    safe = re.sub(r"[^\w.-]", "_", str(session_id or "unknown"))
    return os.path.join(list_dir, "audit_guard-%s.txt" % safe)


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
    if not path or not style_gate.is_prose_path(path):
        return False
    if any(_under(path, root) for root in scratch_roots):
        return False
    return not _under(path, os.path.join(home, ".claude"))


def _epoch(ts):
    """Seconds since 1970 for a transcript timestamp such as
    2026-10-15T20:00:00.000Z, which is in UTC; None when unreadable."""
    try:
        return calendar.timegm(time.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S"))
    except (TypeError, ValueError):
        return None


def _texts(content):
    """The text of a user record: the string itself, or its text blocks.
    None when the record carries a tool result, which Jake did not type."""
    if isinstance(content, str):
        return [content]
    if not isinstance(content, list):
        return []
    if any(isinstance(b, dict) and b.get("type") == "tool_result"
           for b in content):
        return None
    return [b.get("text", "") for b in content
            if isinstance(b, dict) and b.get("type") == "text"]


def _is_jake(rec):
    """Something Jake typed, as opposed to a tool result or text the
    harness injected. Follows style_gate.visible_turns."""
    if rec.get("type") != "user" or rec.get("isMeta"):
        return False
    origin = (rec.get("origin") or {}).get("kind")
    if origin is not None and origin != "human":
        return False
    texts = _texts((rec.get("message") or {}).get("content"))
    if not texts:
        return False
    text = "\n".join(texts).lstrip()
    return bool(text) and not text.startswith(style_gate.MACHINERY_PREFIXES)


def _read(transcript_path):
    records = []
    with open(transcript_path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if isinstance(rec, dict):
                records.append(rec)
    return records


def _tool_uses(rec):
    if rec.get("type") != "assistant":
        return []
    content = (rec.get("message") or {}).get("content")
    if not isinstance(content, list):
        return []
    return [b for b in content
            if isinstance(b, dict) and b.get("type") == "tool_use"]


def _bash_saves(command, cwd, start, end):
    """Prose files a shell command names and that were modified while it
    ran, between `start`, when it was issued, and `end`, when its result
    came back. A command names the files it reads as well as those it
    writes, and a file another command changed earlier can be named by a
    later one that only reads it, so the window decides which it wrote.
    Transcript times are whole seconds, hence the slack at both ends."""
    base = style_gate.effective_cwd(command, cwd)
    out = []
    for name in style_gate.paths_in_command(command):
        path = os.path.expanduser(name)
        if not os.path.isabs(path):
            if not base:
                continue
            path = os.path.join(base, path)
        try:
            mtime = os.stat(path).st_mtime
        except OSError:
            continue
        if start - 1 <= mtime <= end + 2:
            out.append(os.path.abspath(path))
    return out


def _result_times(records):
    """When each tool's result came back, by the id of the tool call."""
    out = {}
    for rec in records:
        if rec.get("type") != "user":
            continue
        content = (rec.get("message") or {}).get("content")
        if not isinstance(content, list):
            continue
        for b in content:
            if isinstance(b, dict) and b.get("type") == "tool_result":
                out[b.get("tool_use_id")] = _epoch(rec.get("timestamp"))
    return out


def unaudited_documents(transcript_path, home=None, scratch_roots=None):
    """Documents saved since Jake's last message that the style audit has
    not run on since their first save in this turn, in the order saved."""
    home = home or os.path.expanduser("~")
    if scratch_roots is None:
        scratch_roots = default_scratch_roots()
    records = _read(transcript_path)

    last_jake = -1
    for i, rec in enumerate(records):
        if _is_jake(rec):
            last_jake = i

    results = _result_times(records)
    first_save = {}    # real path -> (index of first save, path as named)
    audits = []
    named = []         # the argument text of each audit, which may name files
    for i in range(last_jake + 1, len(records)):
        rec = records[i]
        if rec.get("type") == "user":
            texts = _texts((rec.get("message") or {}).get("content")) or []
            if any(_AUDIT_COMMAND.search(t) for t in texts):
                audits.append(i)
            continue
        for use in _tool_uses(rec):
            name = use.get("name")
            data = use.get("input") or {}
            saved = []
            if name == "Skill":
                skill = str(data.get("skill", "")).split(":")[-1]
                if skill in AUDIT_SKILLS:
                    audits.append(i)
                    named.append(str(data.get("args", "")))
            elif name in SAVE_TOOLS:
                saved = [data.get("file_path")]
            elif name == "Bash":
                start = _epoch(rec.get("timestamp"))
                end = results.get(use.get("id")) or time.time()
                if start is not None:
                    saved = _bash_saves(str(data.get("command", "")),
                                        rec.get("cwd"), start, end)
            for path in saved:
                if not is_document(path, home, scratch_roots):
                    continue
                # One file can have two names when a directory is a link;
                # skills/ here is a link to plugins/ai-workflow/skills.
                key = os.path.realpath(path)
                if key not in first_save:
                    first_save[key] = (i, path)

    # An audit covers a document first saved before it. An audit that names
    # the document covers it whenever it was saved, because a save after
    # such an audit is the audit's fixes being written out.
    def covered(at, path):
        if any(a > at for a in audits):
            return True
        return any(path in text or os.path.basename(path) in text
                   for text in named)

    return [path for (at, path) in first_save.values()
            if not covered(at, path)]


def build_feedback(paths, listing):
    """The text handed to the model: two lines, however many documents the
    turn saved. Jake sees it in full at the end of the turn. On 2026-10-21
    the feedback listed five paths and he pasted all nine lines back, so
    the paths now go to the file `listing` and the feedback names it. The
    text carries no explanation of the ask, which the model has in
    SKILL.md. It once ended by asking for two or three sentences on what
    the audit changed. Jake, 2026-10-20: "I don't need to know how it
    improved its message to me or the writing it is working on." He has
    read the reply that came before this text."""
    n = len(paths)
    return "\n".join([
        "Not yet style-audited this turn: %d document%s, listed in %s"
        % (n, "" if n == 1 else "s", style_gate.ascii_only(listing)),
        "Load the style-audit skill, run its two passes on what you wrote "
        "or changed in each, apply the fixes, and end the turn without "
        "writing anything more to Jake. Not both-passes, not first-reader."])


def _write_list(listing, paths):
    with open(listing, "w", encoding="utf-8") as fh:
        fh.write("".join(p + "\n" for p in paths))


def _log(log_path, session_id, paths):
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"time": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                 "session_id": session_id,
                                 "files": paths}) + "\n")
    except OSError:
        pass  # the ask matters more than the record of it


def run(stdin_text, log_path=DEFAULT_LOG, home=None, scratch_roots=None,
        list_dir=DEFAULT_LIST_DIR):
    """Always returns 0. Prints feedback that continues the turn when a
    document is unaudited and nothing otherwise. Any failure lets the turn end, because
    a broken guard must not wedge a session."""
    try:
        if os.environ.get(READER_MARK):
            return 0
        event = json.loads(stdin_text)
        # Claude Code sets this when the assistant is already continuing
        # because a Stop hook spoke. Letting that turn end means the guard
        # speaks at most once in a row and cannot loop.
        if event.get("stop_hook_active"):
            return 0
        path = event.get("transcript_path")
        if not path or not os.path.isfile(path):
            return 0
        pending = unaudited_documents(path, home, scratch_roots)
        if not pending:
            return 0
        _log(log_path, event.get("session_id"), pending)
        os.makedirs(list_dir, exist_ok=True)
        listing = list_path(list_dir, event.get("session_id"))
        _write_list(listing, pending)
        # additionalContext continues the turn exactly as a block does,
        # through stop_hook_active and the eight-continuation cap, but the
        # harness draws it as hook feedback and not as a hook error. Jake,
        # 2026-10-21, of the error it drew in his terminal: "I'd prefer not
        # to have to scroll past such clutter."
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "Stop",
            "additionalContext": build_feedback(pending, listing)}}))
        return 0
    except Exception:  # noqa: BLE001 - fail open on anything at all
        return 0


if __name__ == "__main__":
    sys.exit(run(sys.stdin.read()))
