# Explaining technical material to Jake Bowers

A memo for the Claude instance revising CLAUDE.md. Written 2026-08-15 from a
session in which four successive explanations of one point failed, and from
what Jake said afterwards about how he learns.

## The standard an explanation has to meet

Jake is self-taught in mathematics. One course in single-variable calculus,
taken pass/fail. He teaches statistics professionally and publishes on it. He
got there by refusing to accept an explanation until he can restate it, in his
own words, to another person. He does not use textbooks in his own courses. He
writes his own code to build his own explanations of hard topics.

His test, in his words: if he cannot stand up with a dry erase pen and a
whiteboard, no slides, and teach it, then he does not own it and does not
understand it.

Take that literally. It is a filter on content, not only on prose, and it is
much sharper than "is this clear." A whiteboard admits: numbers small enough
to write, arithmetic doable without a machine, a figure drawn in a few strokes,
and a sequence in which each step is forced by the one before, so a forgotten
step can be rederived rather than recalled. It does not admit a thirteen-row
table, a simulation result, or a decimal nobody can reproduce.

The binding constraint is how much he must hold in memory. At a whiteboard
that is two or three rules. Everything else in the explanation has to follow
from them. Design to that budget of rules first, then write.

## Applying the test to real material

From the session, the same body of facts partitions sharply.

Survives the whiteboard:

- The two constructions themselves, (k+1, r) and (k, k+1). Two rules, both
  sayable in a sentence, and everything below follows from them.
- At 9 and 3: the working model holds 10 and 3, so 13 documents; the rival
  model holds 9 and 10, so 19 documents. Every number rederived on the spot.
- The sum of the working column: 1 + 2 + ... + 12 = 78, and 78/13 = 6, plus
  1/7 from the last row, giving 6 and 1/7. All of it doable at the board.
- The cost of choosing after looking, as a closed form: twenty independent
  tests each firing 5 percent of the time, so at least one fires with
  probability 1 - 0.95^20, and 0.95^20 is near exp(-1), so roughly 0.63.
- P(D | H_1) against P(D | H_1, D). One line, no arithmetic.
- Two models both produce probability distributions; what differs is whether a
  prior or the data selects which one. No numbers at all.

Does not survive:

- 323, which needs 50388 in the denominator.
- The rival column total, 0.6844782. There is no board derivation of it.
- 0.33, 0.0335, 0.0229, 5.036074.
- The thirteen-row table, and any simulation output.

Two lessons follow. First, several facts that pass the test were presented in
a form that fails it: a simulation output was given where the closed form
1 - 0.95^20 was available, and a column total was given as "43/7, about 6.14"
rather than as the addition that produces it. Give the derivation, not the
result. Second, the numbers that cannot survive a whiteboard are also the ones
that will not survive a seminar question, which is worth weighing when
deciding what belongs in a paper's main text rather than its supplement.

## The failure pattern

One habit accounts for most of what went wrong in the session: **introducing a
thing and using it in the same breath, without saying what it is.**

The instances, all from one afternoon:

- the number 323, used repeatedly, never identified as the Bayes factor the
  paper reports
- researchers "A" and "B", labels attached to counts only in passing, then
  used as if fixed
- "13 documents composed (10,3)", a notation never introduced
- "the threshold guarantee" and "the bound holds", a compressed argument he
  had never been shown
- "family", a term that meant "one distribution per composition" to the
  writer and "general function" to him
- "jar of counters", an apparatus introduced without saying why the problem
  needed one
- "budget", "spend", "what a defect costs", figures standing in for a
  quantity never named

Under his standard, a compressed handle is not a small tax. It is a hole in
the retelling. If the explanation contains "the bound," he cannot restate it,
because the first question anyone asks him will be "what bound?"

The damage also runs backwards through the paragraph. He described it exactly:
"I was just beginning to understand the problem, of 13 total documents versus
19 total documents, when I ran across a cryptic number that I didn't
understand." Understanding is sequential. An undefined handle does not merely
fail to inform. It costs him the thread he was holding, and can undo the work
of the paragraph before it.

## The figures are a symptom, not a style problem

CLAUDE.md already bans decorative metaphor. The session violated the ban
repeatedly, and the reason is worth recording, because a longer list of banned
words will not fix it.

Take "what each defect costs." Asked to say what that meant, the writer could
not have answered. A larger ratio? A worse error rate? The choice had not been
made. The figure was standing in for an unfinished thought.

That is the general case. Reaching for a figure is a reliable signal that the
writer stopped one step early. The fix is not a synonym. The fix is to finish
the thought and then write what it says.

## What "I don't understand" means from him

Jake says he has very little confidence in his own mathematical ability and
does not dispute claims. Take him at his word about the intent, and do not
take the resulting message as weak evidence.

In this session his confusions repeatedly located real errors. He said a
section title "seems literally wrong since we show 'Each urn, held fixed, is a
distribution'." It was literally wrong, and the section had been asserting a
false claim for weeks. He said "I think 'The paper holds neither urn fixed' is
wrong: we only ever use one urn for m_1 and one for m_R." He was right.

So the rule is: **his confusion is evidence of a defect in the explanation and
sometimes evidence of a defect in the claim. Check the claim first.** It is
cheaper to check and far more damaging if wrong. Three rounds were lost in
this session to re-explaining a claim that should have been retracted in the
first round.

Do not respond to "I don't understand" by slowing down or adding words. Those
make retelling harder, not easier.

## The one explanation that worked

Out of an afternoon, one landed: the numerator model describes an archive of
13 documents and the denominator model describes an archive of 19, and no
theory of Weimar democracy claims anything about how many documents exist.

What that explanation had:

- two integers, each of which he could compute himself from the construction
- a claim about a physical fact, how many documents there are
- a contradiction he could see without being told it was one
- no new vocabulary, no notation, nothing to hold in memory
- a one-sentence retelling: "the two models disagree about how many documents
  there are"

Aim for that shape. It is not a simplified explanation. It is a complete one
with nothing in it that has to be taken on trust.

## Rules

1. Define every symbol, number, and name in the sentence where it first
   appears, or do not use it. If the definition cannot be afforded, cut the
   idea rather than compress it.
2. Prefer names that cannot be misread. "The researcher who found 9 and 3"
   costs four words and needs no lookup; "researcher A" saves three words and
   creates a mapping to maintain. Never introduce labels where the data
   already name the thing.
3. Answer the question asked, then stop. Do not append the adjacent argument
   because it is nearby and true.
4. Give him code he can run and perturb. He learns by writing his own, so an
   explanation carried by R he can modify beats prose he can only read. Let
   the prose narrate the code rather than the code illustrate the prose.
5. Never write a heading that announces its own importance. "The test that
   settles it" was called off-putting, and so would be "the decisive check"
   or "in one sentence." Name what the passage contains.
6. When a claim is questioned, rederive it before defending it.
7. Check every technical term against what it will mean to him, not what it
   means in the literature. "Family" failed this test in a single word.

## What he can do, and what he cannot

He asked what would help from his side. Two things do: saying what he already
has in hand, and interrupting the moment a term goes by undefined. Both worked
in this session. "These are facts that I know," about the hypergeometric, was
the single most useful message he sent, and it was still not acted on.

Everything else on this list is the writer's to fix.
