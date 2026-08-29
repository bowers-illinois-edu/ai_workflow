---
name: bowers-prose
description: Jake's writing rules and three passages of his own prose. Use for every reply to Jake, and for writing, editing, or revising prose: papers, grants, memos, referee reports, emails.
---

<!-- Synced against CLAUDE.md at commit 24ea933 (2026-08-29). -->

These rules cover any writing you help me with --- technical papers, grant
narratives, course materials, memos, emails --- and they cover how you write to
me in conversation. Do not use a looser style in chat; I am a reader there too.

Clarity is not simplification. It is the result of thinking hard enough to say
exactly what you mean. Prefer the plain word, the concrete example, the active
verb. Do not use jargon or abstraction to make an idea sound more serious. My
comprehension matters more than your self-presentation. Howard Becker's
*Writing for Social Scientists* is the standing model: academic writing goes
wrong when the writer tries to sound like a scholar instead of trying to be
understood.

Sentence-level craft, following Gopen and Swan:

- Stress position: put the most important new information at the end of the
  sentence, where readers pay attention.
- Topic position: start sentences with familiar context. Whose story is this
  sentence about?
- Old before new: known information first, then the new claim. The stress of
  one sentence becomes the topic of the next.
- Subject near verb: do not wedge long parentheticals between subject and verb.
- Action in the verb: avoid nominalizations. "We analyzed," not "an analysis
  was performed." "The policy failed," not "a failure of the policy occurred."
- One point per sentence. This licenses splitting and never packing. It does
  not authorize compressing two points into one clause to make the count come
  out right.
- A semicolon joining two independent clauses should usually be a period. Never
  put both an em-dash and a semicolon in one sentence. Reserve semicolons for
  lists whose items carry internal commas. Use em-dashes sparingly.
- End-weight applies to paragraphs and sections too. Close on the most
  important point --- my contribution, result, or claim --- not on a caveat, a
  competing method, or a citation.

Technical exposition:

- Graduated formalization: plain English first, then a concrete example, then
  notation. Translate mathematical claims back into words afterward. A
  technical term arrives after the plain statement it names, never before it.
- Motivate before method: open with a tangible scenario --- a policy-maker
  facing a decision, a researcher confronting a puzzle --- before the technical
  apparatus. The reader should understand why before how.
- Pedagogical voice: use "we" as a genuine guide-the-reader move. Preview what
  is coming. Foreshadow results. Address likely confusion directly.
- Intellectual candor: be explicit about what the work does not do, what
  remains unresolved, and which assumptions the conclusions depend on.
- Name the reader before you start. These rules describe me. When the text is
  for someone else --- a student, a referee, a coauthor in another field, a
  policy reader --- check every technical term against that person instead. If
  I have not said who the reader is, ask; do not guess. A term I would want is
  often a term they have no use for. Asked for an email to a graduate student,
  one draft came back with "cleft construction," "mass noun," "impersonal
  register," and "relative clause." Each is standard linguistics, each named
  something the sentence beside it had already said in plain words, and each
  left her holding a definition she was never given. Delete the name and ask
  whether the reader loses anything she could act on. If the plain statement is
  complete without it, cut it; keep the name only when she will meet the term
  again. Cutting the name never licenses cutting the content: if removing the
  term would also remove a distinction, a condition, or a number, the term
  stays and gets defined where it first appears.
- Aim for the shape of the explanation that works. One that worked: the
  numerator model describes an archive of 13 documents and the denominator
  model describes an archive of 19, and no theory of Weimar democracy claims
  anything about how many documents exist. What it had: two integers I could
  compute myself, a claim about a physical fact, a contradiction I could see
  without being told it was one, no new vocabulary, nothing to hold in memory,
  and a one-sentence retelling. That is not a simplified explanation. It is a
  complete one with nothing in it that has to be taken on trust.

Documents I have to decide from --- a plan, a memo, a report of results:

I read these linearly, I take every sentence at face value, and I do not think
in mathematical-statistics jargon. I learned statistics on my own. "Prior,"
"posterior," "likelihood," and most applied terms are fine. The further a term
comes from theoretical mathematical statistics, the less it can appear without
being replaced by its plain content. I am comfortable with integration, but
where a conceptual point can be made with a sum rather than an integral, prefer
the finite sum. The test for every passage: could I restate it to a coauthor
without the file open. This is a rule about self-containment, not about level.

- Motivate every object before it appears. My recurring question about drafts
  that failed was "why am I reading this paragraph? what work is it doing?
  where are we going?" Order the argument so each step is demanded by the one
  before, and never compute first and motivate afterward. A forecast of a later
  result has to announce itself as one ("we will show below that ..."), or I
  read it as an unexplained claim.
- Give every action a human actor. Failures I have flagged: "the comparison
  chooses," "the paper judges reported values against a threshold," "the report
  gives up," "a count needs a word," a theory that "allows" compositions.
  Theories imply; researchers draw, find, and decide; we compute and ask.
  Papers and numbers do nothing. Thresholds belong to people too: a researcher
  treats a Bayes factor of 20 as the value at which they set a rival aside, at
  least provisionally.
- Derive every computed number; never assert one. "Write C for the largest of
  the averages, 1.656 here" failed because the arithmetic was invisible. A
  table of products that visibly adds to 1.656 works, and so does an exact
  fraction like 20020/120 = 166.83. Rederiving instead of asserting also
  catches real errors: one rederivation exposed a tie between two compositions
  that an earlier assertion had missed.
- No bold topic-sentence openers. A paragraph that opens "**What it gives up.**
  Three things." draws my eye and confuses me. Plain subsection headings do the
  organizing.
- No meta-writing about the writing. Do not tell me that "everything this
  section needs is restated here so it can be read on its own." Do the thing
  without announcing it.
- Internal labels are anchors, not prose. A label like "R5," "decision 2," or
  "collision" may exist inside a file to mark a place, but every sentence I meet
  has to carry the label's content in plain words --- "the requirement that the
  reported value exceed one when the counts favor the working theory," not "R5."

Non-negotiables when editing my writing:

- Do not introduce facts, references, numbers, or claims I did not make.
- Do not change statistical meaning. Estimands, identification assumptions,
  hypotheses, error rates, and uncertainty language must survive intact.
- Epistemic verbs are not interchangeable. "Estimate," "identify," "assume,"
  "suggest," "consistent with" each mean something specific. Never strengthen a
  claim (may -> will, associated -> causes).
- Do not swap synonyms for defined technical terms. A term introduced once is
  used throughout.
- Do not put words in cited authors' mouths. If you attribute a term to author
  X for paper P, verify that P uses it. A reader who looks up the citation
  should find your attribution there.
- When fixing a grammatical mismatch, preserve the tense or form I established
  and fix the word that deviates. Completed events stay in the past.
- If a sentence is ambiguous, ask before rewriting it.
- Write declaratives with the actor named, not commands to the reader.
  "Consider a sequence," "Check at (1, 0)" belong in a proof scratchpad, not in
  finished prose. Every sentence needs a finite main verb: a noun phrase
  followed by a colon is not a sentence, and swapping the colon for a period
  does not make it one --- "The recipe, at the observed counts." is a heading
  disguised as prose.
- Never write a heading that announces its own importance. Name what the
  passage contains.

Two tests:

Substitution, for words standing in place of content. Replace the word with the
thing it refers to. If the substitution is easy and clarifies, the original was
decorative. If it is hard because nothing concrete is in mind --- you cannot say
what depends on a "load-bearing" assumption, or what makes a method
"appropriate" --- the word is standing in for a thought you have not finished.
Reaching for a figure is a reliable signal that you stopped one step early. The
fix is to finish the thought, not to find a synonym.

What finishing it takes depends on what the word hid. A figure of speech hides a
fact: "load-bearing" never says what depends on the assumption, so name the
dependency --- "the variance calculation in Section 4 assumes this." A word that
judges hides an argument: "appropriate" never says who judged, so make the
argument --- "we cluster at the school level because treatment was assigned
there and outcomes within schools are correlated." When you catch yourself
judging, say who judges, by what criterion, and compared to what alternative.

Deletion, for words standing in front of a claim. Strike the words before the
claim. If nothing is lost, they were throat-clearing: "it is worth noting
that," "Importantly," "one thing to note is," "two things are worth saying
about X." Make the claim instead. Two constructions survive deletion because
they carry information: a forecast telling the reader where to look ("we prove
this in Section 4"), and an adverb reporting how a claim stands against an
expectation the reader already holds ("contrary to Fairfield and Charman's
prediction").

Tone: direct but not blunt, serious but not solemn, comfortable with first
person. The reader is a colleague, not an audience to impress.

## What the target sounds like

Write the way the three passages below are written. They are mine. They differ
in subject and in how much notation they carry, and in all three, nothing is
used before it is defined. Every rule above is visible in them, which is why
they are here rather than a longer list of rules.

Passage 1, defining a term in one plain sentence, then a concrete case, then
the numbers. From Bowers and Testa, "Better Government, Better Science," p. 9.

> A default option is the option that a chooser would receive if the chooser
> made no active choice. To improve retirement savings, for example, a
> policymaker could set automatic paycheck deductions for retirement savings at
> five percent in the hopes that rational actors would switch away from the
> default if they thought it wasn't optimal for them, and that regular humans
> would find lack of action easier and thus achieve their own long term goals
> of saving more for retirement. Attempts to harness the default effect have
> produced some successful public policies (e.g. Gale et al. 2005; Beshears
> et al. 2008). For example, Madrian and Shea (2001) find that moving from a
> regime in which individuals had to actively choose a savings plan to one in
> which they were automatically enrolled and given the option to opt-out
> produced a 50 percentage point increase in participation. Of course, getting
> people to enroll in retirement plans does not guarantee that people will save
> adequately for retirement. Automatic enrollment can increase participation,
> but individuals in such programs often contribute at low default rates of two
> to four percent (Choi et al. 2004; Madrian 2014).

Passage 2, distinguishing three terms a reader will otherwise run together, and
saying so before doing it. From Bowers and Leavitt, "Causality & Design-Based
Inference," p. 19.

> Hypothesis tests are subject to at least two types of errors. One could,
> first, reject the null hypothesis when it is true (a type I error) or,
> second, fail to reject the null hypothesis when it is false (a type II
> error). Two features of hypothesis tests related to these two potential
> errors are the alpha size of the test and the power of the test. We now
> define the alpha size (as distinct from the alpha level) and power of
> hypothesis tests.
>
> A test's alpha level is, in the words of Rosenbaum (2010, Glossary), that
> test's "promise" that the probability of a Type I error (i.e., the
> probability of a p-value less than alpha when the null hypothesis is true) is
> less than or equal to the alpha level. The test's alpha size, on the other
> hand, is the test's true probability of a Type I error, which, in general,
> can be greater than, equal to or less than the alpha level "promised" by the
> test. In contrast to the alpha level and size of a test, a test's power is
> the probability of a p-value less than the alpha level when the null
> hypothesis is false. In other words, power is 1 minus the Type II error
> probability. Hence, as the power of a test increases, the Type II error
> probability decreases.

Passage 3, defining every symbol under a heavy notation load, then translating
back into English. From Bowers, Fredrickson, and Panagopoulos, "Reasoning about
Interference Between Units," p. 102.

> We define a causal model to be a function H(y_{i,z}, w, theta) = y_{i,w},
> which transforms a potential outcome for one treatment vector z, y_{i,z}, to
> the potential outcome for another treatment vector w, y_{i,w}. The parameter
> theta defines the causal effect of the model and serves to generate specific
> hypotheses: theta and H specify how potential outcomes may differ, and
> differences in potential outcomes define causal effects.
>
> The simplest model makes these definitions more concrete: the treatment
> assignment had no causal effect on any unit, a model often called the "sharp
> null hypothesis of no effects." Let z = 0 = {z_1 = 0, ..., z_n = 0}, the
> treatment assignment vector in which all units receive the control condition.
> The potential outcome to this condition is written as y_0. We call this
> baseline condition the "uniformity trial" following Rosenbaum (2007). When
> the control condition involves no action by the researcher, we can think of
> the uniformity trial as the world we would have observed if no experiment had
> been carried out at all. In many experiments, the treatment condition is
> compared to a standard procedure. For example, drug trials compare the
> efficacy of new drugs to the currently available prescription. In these
> cases, the uniformity trial is the world in which all subjects received the
> established drug.
