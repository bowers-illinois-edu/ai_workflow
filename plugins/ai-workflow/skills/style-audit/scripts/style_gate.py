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
import sys
import time

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
        return 0
    except Exception:
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], sys.stdin.read(), DEFAULT_LOG))
