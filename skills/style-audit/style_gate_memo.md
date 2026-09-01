# A gate on Claude's prose: what it is, what it cannot do, how to turn it on

## The problem it addresses

Your CLAUDE.md tells me how to write to you. It does not check what I wrote,
and the gap between those two things is large enough to measure.

I scanned every message I have written to you in your last 12 transcripts,
using the scanner your style-audit skill already has. That is 341 messages of
prose, with fenced code excluded, since shell and R use words like "sandbox"
and "costs" in their ordinary senses.

Of those 341 messages:

    192 clean                                     56%
    135 carried a violation needing no judgment    40%
     14 carried only a judgment candidate           4%
    ---
    341

The middle line is the one worth acting on, and it breaks down like this. The
counts are messages containing at least one instance, followed by total
instances:

    unicode              109 messages, 213 instances
    bold run-in opener    42 messages, 103 instances
    em dash + semicolon   11 messages,  14 instances

Those three message counts add to 162 rather than 135 because a single message
often carries two of the faults.

All 213 unicode instances are one of two characters: 212 em dashes and 1 en
dash. Your rule against them is the most explicit instruction you have written
and the one that needs the least judgment to follow, and I break it in 109 of
341 messages, which is 32 percent.

I offer this as the argument for a mechanical check rather than more
instruction. While writing the test file for this gate, I twice typed a real em
dash into the file whose subject is not typing real em dashes. The scanner
caught both.

## Why the gate does not stop a bad message from reaching you

You asked to see only the corrected message, never the flawed one followed by
its repair. I cannot build that, and the reason is worth stating because it
constrains every version of this idea.

Claude Code runs a script at named moments. The moment after I finish a reply
is called Stop. A script running there can read what I wrote and can force me
to keep working, but my text has already been printed to your terminal by the
time it runs. No moment exists between my writing a sentence and your seeing
it. The one event that fires at display time cannot stop anything.

So a gate that catches a fault after the fact can only ever add a second
message. To give you one clean message, the check has to happen before I write,
and the only thing a script can do before I write is put words in front of me.

That is what this does. It splits into a reminder that arrives first and a
record that accumulates afterward.

## The two halves

The reminder runs when you send a message, before I begin composing.
It injects six lines naming the three faults above and pointing at the reread
your CLAUDE.md already requires. It sits immediately before I generate, rather
than 28KB away at the top of my context, and adjacency is the only mechanical
difference between it and the instruction that has been failing. Whether that
difference matters is an empirical question, which is what the second half is
for.

The record runs after I finish a reply. It scans what I wrote, appends one JSON
line per dirty message to a log, and passes me a private note listing what it
found. It never blocks, so nothing doubles in your terminal and nothing can
hang. The note tells me to apply the correction going forward and not to
mention it to you, because a note I discuss out loud becomes the second message
by another route.

I am trading a guarantee for a measurement. Some replies will still reach you
with an em dash in them. What you get in exchange is a count you can watch: if
40 percent does not fall, we will know from the log rather than from
impression, and you can decide then whether to make the gate block after all.
That decision is a one-line edit, described at the end.

## What is on disk now

    skills/style-audit/scripts/style_gate.py     the gate, 175 lines
    skills/style-audit/tests/test_style_gate.py  35 tests, all passing

The gate calls your existing style_scan.py rather than carrying its own list of
offenders, so the catalog stays in one file and adding a pattern there changes
both the audit and the gate at once.

Run the tests with:

    /usr/bin/python3 skills/style-audit/tests/test_style_gate.py

I have not edited CLAUDE.md, settings.json, or the Makefile, because another
agent is working in this directory. Everything below is text for you to paste
when you want it.

## Turning it on

Your ~/.claude/settings.json already has both UserPromptSubmit and Stop, and
each one runs your iTerm status script. So these are additions to two existing
arrays, not new keys. Pasting a fresh key would replace cc-status and your
status line would stop updating.

Add a second element to each array. UserPromptSubmit becomes:

    "UserPromptSubmit": [
      {
        "hooks": [
          { "type": "command",
            "command": "/Users/jwbowers/.config/iterm2/cc-status" }
        ]
      },
      {
        "hooks": [
          { "type": "command",
            "command": "/usr/bin/python3 /Users/jwbowers/repos/ai_workflow/skills/style-audit/scripts/style_gate.py preflight" }
        ]
      }
    ],

and Stop becomes the same shape with the second command ending in `stop`
instead of `preflight`.

The interpreter is written as /usr/bin/python3 rather than python3 on purpose.
A hook can inherit a minimal PATH that omits /opt/homebrew/bin, where your
Homebrew python3 and rg both live. The system python3 at /usr/bin is always
present, and the gate uses only the standard library, so version 3.9 is enough.

To wire the tests into `make test`, add test-style-gate to the .PHONY line and
to the test target's list, then add:

    test-style-gate:
    	$(PYTHON) skills/style-audit/tests/test_style_gate.py

## Checking that it works

Turn it on, then paste this into a session and watch what happens:

    Reply to me with a sentence containing a real unicode em dash.

Two things should follow. You should see no second message and no delay. Then:

    cat ~/.claude/logs/style_gate.jsonl

should show one line ending in `"tier": "mechanical", "categories":
["unicode"], "count": 1`. If the file does not exist, the Stop hook is not
running, and the fastest check is whether your iTerm status line still updates,
which tells you whether the array edit broke the first entry.

## Reading the log

To see the rate over the last hundred replies:

    tail -100 ~/.claude/logs/style_gate.jsonl | \
      /usr/bin/python3 -c "import sys,json,collections; \
      c=collections.Counter(json.loads(l)['tier'] for l in sys.stdin); print(c)"

The log records only dirty messages, so it gives you the numerator directly and
you would need the transcript count for the denominator. If you want the rate
computed for you rather than the count, say so and I will add a small reader,
with its own tests.

## What it does not catch

The Stop event hands the script the final text of a turn. Prose I write between
tool calls, which is most of what you read while I am working, is not in that
field. Roughly, the gate sees my answers and not my narration.

It also skips fenced code entirely, which means a unicode character inside a
code block reaches you unflagged. That is deliberate, since flagging ordinary
words in shell would fire constantly, but it is a real hole and the fix, if you
want it, is a separate unicode-only scan that ignores fences.

And it settles only the three faults that need no judgment. Whether "costs" is
a metaphor or a literal statement about three days of cluster time is a
question the scanner cannot answer, which is why those candidates go into the
log and never into the reminder. Putting them there would teach me to avoid
particular words rather than the habit behind them, which is the failure your
own note about ban lists describes.

## When to change it

Watch the log for a few weeks. Three outcomes, and what each one asks of you.

If the mechanical rate falls well below 40 percent, the reminder is doing the
work and nothing needs changing.

If it holds near 40 percent, the reminder is not enough, and the next step is
to make the gate block on the mechanical tier only. You would accept seeing the
flawed message followed by a correction, in exchange for never being left with
the flawed one. That is the trade you declined at the start, and you would be
making it with a number in hand rather than in advance.

If the judgment tier grows while the mechanical tier shrinks, I have started
avoiding flagged words and reaching for unflagged figures instead. That is the
outcome your ban-list note predicts, and the response is not another pattern.
It is to add a passage of your own prose to the exemplars in SKILL.md.

The tier membership is one line in style_gate.py:

    MECHANICAL = frozenset({"unicode", "bold-run-in-opener", "dash-semicolon"})

and one test in test_style_gate.py pins it, so a change there fails loudly
rather than quietly.
