# What stops Jake, measured

Written 2026-09-09. You asked whether the judgment half of `style-audit` can
be improved, and whether a text-analysis approach over your own transcripts
would beat it. This memo reports what the transcripts say. The scripts are in
the session scratchpad and every number below can be recomputed from
`~/Claude_Transcript_Archive/corpus.jsonl`.

## The data

`mine_transcripts.py` builds one row per exchange: the assistant prose that
was on your screen, and the next thing you typed. There are 1411 rows from
2026-06-05 to 2026-09-09. I used the 1315 rows from 2026-08-15 onward, which
is the period you asked about.

A row counts as a stop when what you typed shows you could not read what was
above it. I matched a list of your phrasings for that, such as "I don't
understand," "what does X mean," "I'm confused," "too long," and "doesn't
make sense." 175 rows matched. I read all 175 and dropped 11 that match a
phrasing without being a stop: six are your own instructions to spawn an
agent, and five ask what to do next rather than report that you could not
read something. That leaves 164 stops in 1315 replies, which is 12.5 percent,
or one reply in eight.

## The scanner separates the two groups only by length

`style_scan.py` fires on 56.1 percent of the 164 replies you stopped on and
on 47.2 percent of the 1151 you did not. Shuffling the stop labels 5000 times
puts that 8.9-point difference at a two-sided p-value of 0.041, so taken
alone it looks like signal.

It is not, and settling that took three tries.

134 of the 1315 rows have an empty assistant field. Those are turns where I
ran tools and wrote you no prose at all. A row with no prose cannot hold a
sentence you stop on, and only 6.7 percent of them drew a stop against 12.5
percent overall. They count as zero words, so all 134 land in the shortest
length group and pull its stop rate down.

Drop them and length stops mattering. Over the 1181 rows that carry prose,
the rank correlation between word count and stopping is 0.042 with a
randomization p-value of 0.154. Counting the empty rows it is 0.065 with p =
0.018, and that difference is the whole apparent effect. So among replies that
exist as prose, a longer reply is not detectably likelier to stop you, and the
five-group tables that suggested otherwise, mine and an agent's alike, were
reading a shape into noise.

The scanner comparison survives on the same rows and says the same thing. Over
the 1181 prose replies it fires on 59.4 percent of the ones that stopped you
and 52.9 percent of the rest, and shuffling the stop labels only within
deciles of word count leaves 4.4 points with a p-value of 0.271. Hits per
thousand words run the other way, 5.55 against 5.92.

So the scanner tells you what `wc -w` already tells you, and nothing beyond
it.

## Where exactly you stopped, and what the scanner saw there

In 118 of the 164 stops you quoted the words you stopped on. For 47 of them
the quoted string appears verbatim in the reply above, so those 47 are not
just "he stopped somewhere in this reply" but "he stopped on these words."
Nobody had to mark anything by hand to get them.

`style_scan.py` flags 2 of those 47. The two are
`which is the failure mode worth naming` and `load-bearing`.
The other 45 it reads as clean, and it reads them as clean when handed the
offending span alone, with nothing else in the file to distract it.

One of the two does not count. You stopped on
`the failure mode worth naming` on 2026-08-29, and commit b5bcf88, made at
16:49 that same day, added the pattern that catches it. The comment above the
pattern names your phrase, listing `a reason worth stating`,
`a point worth making`, and `the failure mode worth naming`.
The same commit added the `internal-shorthand` patterns, whose comment names
`guard passes`, `scanner clean`, and `numbers match`,
the three you had objected to that evening.
Scoring the scanner on a span from before 2026-08-30 scores it partly on
sentences its patterns were written to catch. On the spans it did not see
first, it flags 1 of 47.

## Three ways to use your corpus, all of which fail

You asked what someone who does text analysis for a living would do with a
corpus of your writing and a corpus of your complaints. I tried the three
ideas that need no model at all against the 47 spans.

A word you have never typed. Your turns contain 4140 distinct words. Of
the 47 spans, 0 contain a word absent from that vocabulary. Of 2000 random
Claude sentences, 67 percent do. The test fires four times as often on prose
you read past as on prose you stopped on, which is the opposite of what it
would need to do.

A two-word phrase you have never written. You have written 12846 distinct
content bigrams. Of the 29 spans long enough to have a content bigram, 0
consist entirely of bigrams new to you. Of comparable random Claude
sentences, 62 percent do.

A verb that belongs to a person. Your catalog says Claude gives things
people's verbs, and comparing the two vocabularies supports it: "sits,"
"carries," "stays," "keeps," "survives," and "renders" are words Claude uses
often and you almost never do. But a list of such verbs matches 17 percent of
the 47 spans and 15 percent of random Claude sentences of the same length. It
separates nothing, because the fault is which noun is doing the verb, and a
word list cannot see the noun.

Two of the three fail in the same direction: the words that stop you are
more ordinary than average, not less. That is the finding, and it rules out
the whole family of methods that work on words alone --- Naive Bayes,
FastText, a support vector machine on n-grams --- because those methods see
only words. What stops you is not in the string. It is in what the text
failed to do earlier: define the term, or fix the antecedent.

## Why no method that reads only words can work

The three failed tests above are evidence. A fourth result is closer to a
proof, and an agent working the same corpus separately produced it.

Take the strings you stopped on and look for them in the replies that drew no
stop. Seventeen of the forty-eight occur there verbatim, matching on whole
words. "The count" stopped you once and sits in 82 replies you read past.
"Working theory" sits in 101, "judgment pass" in 36, "collection" in 32.

For those seventeen, a method that reads only the words is handed exactly the
same input in both cases. No function of that input can give two answers to
one question, so no such method can separate them, and no quantity of extra
training data changes that. The other thirty-one strings appear nowhere else
in 1266 replies, so a method could only memorize them, and the next stop will
use a different string.

Naive Bayes, FastText, and a support vector machine over n-grams all estimate
the chance of a stop from a bag of words, so all three inherit that. The
agent also ran the experiment: trained on August, tested on September, the
area under the ROC curve is 0.494 with the full vocabulary and 0.553 when
regularization strips most of it, against 0.5 for guessing.

A rule that reads the surrounding words does no better, and this was checked
rather than assumed. Reading three examples suggested that the passing uses
of "the count" put a number in the same clause and the stopping use did not.
Counting all of them kills it: 64 of the 140 passing clauses carry a digit,
LaTeX math, or a spelled number, and the rule would flag 76 passing clauses to
catch the single stop.

So the failure is not that we picked the wrong words to look at. Whether a
phrase points at something you can find is a fact about the phrase, its
sentence, and everything the document has already established. Deciding it is
reading, and no rule over strings reads.

## What the 47 spans actually are

Reading each one and assigning it to a family:

| Family | Count |
|---|---|
| A term used without definition | 23 |
| A thing given a person's verb | 9 |
| A pronoun with no unique antecedent | 6 |
| An offender already in the catalog | 4 |
| A sentence you judged wrong, or other | 5 |

The terms you stopped on are "collection," "boundary," "holder," "the count,"
"residuals," "report," "scanner," "registry," "robust," "guarded chunk,"
"retarget," "Course 3," "General Statistics." You know every one of those
words. Each was doing technical duty that the text had never assigned it.

The first and third families are one fault seen twice, a word whose meaning
the text has not fixed, and together they are 29 of the 47. That reproduces,
on a different slice of your transcripts, what the first-reader validation
already found: the two families it misses most often are a term you could not
resolve and a thing given a person's verb.

## Where a fast automatic check could run

You asked whether something could catch this before you ever see it. One hook
runs before your terminal prints my words, and I verified it in the program
itself rather than taking an agent's word. Two strings inside
`/opt/homebrew/Caskroom/claude-code@latest/2.1.266/claude`:

> Hook input for the MessageDisplay event. Fired with each batch of newly
> completed lines while an assistant message streams. Display-only: the
> stored message and what the model sees are untouched.

> Hook-specific output for the MessageDisplay event. Display-only: replaces
> the delta on screen without changing the stored message.

The documentation adds that the hook returns `displayContent` to replace that
batch of lines, that it cannot block the message, and that its timeout is ten
seconds. It was added in version 2.1.152 and you run 2.1.266.

So a script does get to alter what you read, one batch of finished lines at a
time, while the rest of the reply is still being written. That timing decides
what it can do. A hook holding four lines cannot know whether a term gets
defined in the paragraph after them, and it cannot know how long the reply
will turn out to be. Those are the two failures the measurement above found:
a term the text never defines, and a reply longer than the answer. The one
automatic check that runs before you read is unable, by construction, to see
either.

What it can repair is anything decidable inside one line: a unicode
character, a line carrying a dash and a semicolon, a paragraph opening in
bold. Those are the three faults the scanner settles without judgment, and
they are 9 of the 78 notes the gate has logged.

Two cautions. A hook that rewrites your screen leaves you and me reading
different text, since the stored message keeps my original words. Repairs
that change no meaning are safe; anything else is not. And a hook that hides
a reply would hide it on the evidence of a scanner that this memo shows does
not predict your stops.

## What these numbers do not settle

Everything above counts how often a detector points at a place you stopped.
That is not the quantity that decides which detector to use. What decides is
how many places you stop in the document that finally reaches you.

The two come apart, and your own class note shows how far. Of the 28 stops you
found there, 16 were sentences a review round had written as a replacement and
6 more were written after the last round had read. Every one of those rounds
had good sensitivity by the count above. The document you received still had 28
stops in it, because applying a finding means writing a sentence, and a
sentence written after the last reading is a sentence nobody has read.

So a detector that points at 40 of your 47 spans and hands back 40 rewrites can
leave you worse off than one that points at 10. Nothing measured tonight can
tell the two apart. That needs a document read twice, once with the findings
applied and once without.

## What I changed

Section 0 of `style-audit/SKILL.md`, which governs replies to you. It used to
say to run the scanner over a draft reply and read by hand for three further
things. It now says the scanner is not a check on a reply, gives the two
numbers above that say so, and replaces the three items with four questions
ordered by how often each family appears among the 47 spans.

## What I did not measure

Whether the four questions work. They were derived from the same 47 spans
they would be tested on, so their agreement with those spans is not evidence.
A test needs stops that came after the change.

I could not check whether the style gate's notes track your stops. The gate
logs a session id and a prompt id; the corpus logs a session id and a turn
number, so the two join at the session and not at the reply. Within a session
the gate fired 29 times and 13 of those sessions also contain a stop, which
says nothing, because a session holds many replies. Adding the turn number to
the gate log would make the join possible.

I also did not measure the 71 stops where you quoted words that are not in
the reply. Those come from a document you were reading, and finding them
would mean matching against files rather than transcripts.
