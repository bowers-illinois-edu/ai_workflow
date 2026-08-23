# Custom style (kept in case the feature comes back)

The app appears to have dropped custom styles. Anthropic's personalization
documentation now lists account-wide instructions, projects, skills, and memory
and says nothing about styles, and the control is not in the desktop app. These
passages moved into `claude_app/skills/bowers-prose/`, which loads when a
writing task appears rather than when a style is selected.

This file stays because the evidence is an absence rather than an announcement.
If a style picker turns up, create a style (name it something like "Bowers
prose") and paste the text below the line as its instructions and sample
writing. Styles are built from example writing, which is what these passages
are. Styles sync with the account, so one paste would cover phone and desktop.

**If the field is too short for all three passages**, drop them in this order:
2013 first (longest, and its virtue is notation discipline, which matters least
in app conversations), then 2020. Keep 2019 --- it is plain prose, which is what
most app conversations are.

The passages are ordered here for app use: plain prose first. In CLAUDE.md they
run in a different order.

Synced against CLAUDE.md at commit 4389b89 (2026-08-23).

-------------------------------------------------------------------------------

Write the way the three passages below are written. They differ in subject and
in how much notation they carry. In all three, nothing is used before it is
defined.

Specifically: define every term, symbol, and number in the sentence where it
first appears. Give the plain-English statement before the technical one, and a
concrete case before the general rule. Keep sentences short enough to
understand on one reading. Do not compress an idea into a figure of speech when
two clauses and a plain verb would carry it.

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
