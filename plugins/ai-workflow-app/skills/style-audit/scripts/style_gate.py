#!/usr/bin/env python3
"""Prose gate on Claude's replies, driven by style_scan.py.

Two entry points, one per hook event:

  preflight   UserPromptSubmit. Injects a short reminder immediately before
              Claude generates. This is the only half that can PREVENT a
              violation, because a Stop hook fires after the text has already
              reached the terminal and no hook can retract displayed text.

  stop        Stop. Scans the finished reply, appends a record to a log, and
              injects a note Claude is told not to surface. It never blocks.
              Blocking would show Jake the flawed message and then a rewrite,
              which is the one outcome he ruled out.

The split into tiers comes from measurement, not taste. Over 329 assistant
prose messages in 12 recent transcripts, 40% carried a mechanical violation
(212 unicode em dashes, 95 bold run-in openers, 14 em-dash + semicolon
collisions) and 16% touched a judgment category. Only the mechanical tier
admits no argument, so only it goes into the injected reminder. Naming
"costs" or "appropriate" there would teach avoidance of words rather than of
the habit, which is the failure the global CLAUDE.md warns about directly.

Every path returns 0. A gate that wedges a session is worse than no gate.
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style_scan  # noqa: E402

# The categories a scan can settle without judgment. style_scan
# over-includes on purpose everywhere else, so everything not named here is
# a candidate for the judgment pass and never more than that.
MECHANICAL = frozenset({"unicode", "bold-run-in-opener", "dash-semicolon"})

DEFAULT_LOG = os.path.expanduser("~/.claude/logs/style_gate.jsonl")

# Kept short because it rides on every single turn. It points at the check
# CLAUDE.md already requires rather than restating it, so there is one
# statement of the rule instead of two that can drift apart.
PREFLIGHT = """Before sending your reply, run the reread CLAUDE.md requires.
Three faults a mechanical scan can settle, so settle them yourself:
1. No unicode. Write --- for an em dash, -- for an en dash, -> for an arrow,
   and straight quotes. This is the one you break most often.
2. No paragraph opening with a bold run-in sentence.
3. No line carrying an em dash and a semicolon together.
Fenced code is exempt. Reread after drafting, never during."""


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
        cats.setdefault(cat, []).append(matched)

    lines = ["Your last reply broke the writing rules in these places:"]
    for cat in sorted(cats):
        shown = ", ".join(sorted(set(cats[cat]))[:4])
        lines.append("  %s: %s" % (cat, ascii_only(shown)))
    lines.append("")
    lines.append("Apply this to what you write from here on. Do not mention "
                 "this note to the user and do not resend the last reply.")
    return "\n".join(lines)


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

    emit("Stop", build_note(findings))
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
        return 0
    except Exception:
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], sys.stdin.read(), DEFAULT_LOG))
