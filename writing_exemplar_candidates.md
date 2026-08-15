# Candidate passages for the "What the target sounds like" slot in CLAUDE.md

Pick one, paste it into `CLAUDE.md` under `### What the target sounds like` in
place of the TODO comment, then delete this file.

Five readers were sent to five of your papers. Four reported. The reader for
`bowers2020causality.pdf` went idle twice without producing anything, so the
main session read that paper directly instead --- it is 52 pages, which is
probably what defeated the readers. Every passage below is your own published
prose, transcribed verbatim.

**Verification.** The three recommended passages were checked character by
character against the source PDF pages by the main session, not only by the
readers who found them. The runners-up at the end were not. Do not paste an
unverified passage without checking it first --- pasting drifted text into a
file that forbids putting words in an author's mouth would be a poor start.

Unicode was converted to ASCII throughout: em dash to `---`, Greek letters
spelled out, `!=` for the not-equal sign. Subscripts use underscores and
braces. Italics in the original are marked with asterisks. Script and bold
symbols in the original (script H, bold z) are rendered as plain letters.

---

## Recommended: Bowers, Fredrickson, and Panagopoulos (2013), p. 102

"Reasoning about Interference Between Units: A General Framework," *Political
Analysis* 21:97-124, Section 3 "Method: Hypotheses and Models."

**Verified against page 102 of the source PDF.** 335 words.

> We define a *causal model* to be a function H(y_{i,z}, w, theta) = y_{i,w},
> which transforms a potential outcome for one treatment vector z, y_{i,z}, to
> the potential outcome for another treatment vector w, y_{i,w}. In vector
> notation, we might replace y_{i,z} with the vector y_z to indicate that H is
> applied to the entire sample with the same z and w arguments. The parameter
> theta defines the *causal effect* of the model and serves to generate
> specific hypotheses, which we demonstrate in more detail in Section 4: theta
> and H specify how potential outcomes may differ, and differences in potential
> outcomes define causal effects.
>
> To make these definitions more concrete, consider the simplest model: that
> the treatment assignment had no causal effect on any unit, often called the
> "sharp null hypothesis of no effects." This model states that any treatment
> assignment would not change the outcome of any subject in the experiment:
>
> H(y_z, w) = y_z.  (1)
>
> By definition H(y_z, w) = y_w, therefore, this model states that y_z = y_w.
> As the sharp null does not make use of parameters, we omit theta when
> discussing the sharp null of no effects.
>
> Let z = 0 = {z_1 = 0, ..., z_n = 0}, the treatment assignment vector in which
> all units receive the control condition (i.e., z is all zeros). The potential
> outcome to this condition is written as y_0. We call this baseline condition
> the "uniformity trial" following Rosenbaum (2007). When the control condition
> involves no action by the researcher, we can think of the uniformity trial as
> the world we would have observed if no experiment had been carried out at
> all. In many experiments, the treatment condition is compared to a standard
> procedure. For example, drug trials compare the efficacy of new drugs to the
> currently available prescription. In these cases, the uniformity trial is the
> world in which all subjects received the established drug. Using the
> uniformity trial, we see that we could write equation (1) as H(y_0, w) = y_0.
> In other words, for any treatment assignment w, the potential outcome is y_0.

**Why this one.** It is the only candidate that demonstrates the discipline
that is actually failing. The complaint is compressed notation and undefined
shorthand, and this passage carries heavy notation while defining every symbol
at the moment it appears --- H, z, w, theta, y_{i,z}, y_0, none used before it
is named. It also runs the full cycle in both directions: model stated in
words, then in notation, then glossed with a drug trial anyone can picture,
then translated back to English in the last sentence. A passage with no
notation cannot model the behavior that needs correcting.

---

## Co-leader: Bowers and Leavitt (2020), p. 19

"Causality & Design-Based Inference," Section 4, just before 4.1.

**Verified against page 19 of the source PDF.** 224 words. Alpha is spelled
out; italics in the original are marked with asterisks.

> Hypothesis tests are subject to at least two types of errors. One could,
> first, reject the null hypothesis when it is true (a type I error) or,
> second, fail to reject the null hypothesis when it is false (a type II
> error). Two features of hypothesis tests related to these two potential
> errors are the alpha size of the test and the *power* of the test. We now
> define the alpha size (as distinct from the alpha level) and power of
> hypothesis tests.
>
> A test's alpha *level* is, in the words of Rosenbaum (2010, Glossary), that
> test's "promise" that the probability of a Type I error (i.e., the
> probability of a p-value less than alpha when the null hypothesis is true) is
> less than or equal to the alpha level. The test's alpha *size*, on the other
> hand, is the test's true probability of a Type I error, which, in general,
> can be greater than, equal to or less than the alpha level "promised" by the
> test. In contrast to the alpha level and size of a test, a test's power is
> the probability of a p-value less than the alpha level when the null
> hypothesis is false. In other words, power is 1 minus the Type II error
> probability; hence, as the power of a test increases, the Type II error
> probability decreases.

**Why this one.** It takes three terms readers habitually run together --- alpha
level, alpha size, power --- and defines each one against the others, saying
explicitly that it is about to do so. This is your memo's rule 7 in action:
check the term against what it will mean to the reader, not what it means in
the literature. The word "family" failed that test in a single word and cost an
afternoon; this passage is what passing it looks like.

**One drawback.** The last sentence joins two independent clauses with a
semicolon, which your own punctuation rule says should usually be a period.

---

## Co-leader: Bowers and Testa (2019), p. 9

"Better Government, Better Science," Section 4.1 "The default example." The
excerpt starts mid-paragraph, after the sentence about where the idea came
from.

**Verified against page 9 of the source PDF.** 279 words.

> A default option is the option that a chooser would receive if the chooser
> made no active choice. To improve retirement savings, for example, a
> policymaker could set automatic paycheck deductions for retirement savings at
> five percent in the hopes that rational actors would switch away from the
> default if they thought it wasn't optimal for them, and that regular humans
> would find lack of action easier and thus achieve their own long term goals
> of saving more for retirement. Attempts to harness the default effect have
> produced some successful public policies (e.g Gale et al. 2005; Beshears
> et al. 2008). For example, Madrian and Shea (2001) find that moving from a
> regime in which individuals had to actively choose a savings plan to one in
> which they were automatically enrolled and given the option to opt-out
> produced a 50 percentage point increase in participation. Of course, getting
> people to enroll in retirement plans does not guarantee that people will save
> adequately for retirement. Automatic enrollment can increase participation,
> but individuals in such programs often contribute at low default rates of two
> to four percent (Choi et al. 2004; Madrian 2014). Thaler and Benartzi (2004)
> describe one behaviorally informed solution to this problem in which
> employees at one firm were offered the opportunity to meet with a financial
> consultant. Almost all were told they need to be saving more for retirement,
> and about 25 percent chose to increase their contributions to the recommended
> five percentage points after meeting with the consultant. Individuals who
> said they couldn't afford to increase their contribution were offered the
> chance to enroll in a plan that tied increased savings rates to future pay
> raises.

**Why this one.** Its first sentence is define-at-first-use in the purest form
in the whole set: "A default option is the option that a chooser would receive
if the chooser made no active choice." Then the definition becomes a
policymaker, a paycheck, and five percent, and only after that do the study
numbers arrive, each attached to the paper that produced it and placed at the
end of its sentence. This is the best model for ordinary prose, where most of
your writing lives.

**One drawback.** The excerpt carries a typo from the original: "(e.g Gale" is
missing the period after "e.g". Pasting it into `CLAUDE.md` puts a typo in the
one passage held up as the model. Fixing it silently would mean the file no
longer quotes you verbatim. Your call --- the honest options are to paste it as
printed, or to paste it with `[sic]`, or to prefer the 2013 passage, which has
no typo.

---

## Runner-up: Bowers, Fredrickson, and Aronow (2016), pp. 395-396

"Research Note: A More Powerful Test Statistic for Reasoning about Interference
between Units," *Political Analysis* 24(1):395-403, Section 1.

**Verified against page 395 of the source PDF.** 281 words.

> In a randomized experiment with n = 4 subjects connected via a fixed network,
> the response of subject i = 1 might depend on the different ways that
> treatment is assigned to the *whole* network. When the treatment assignment
> vector, z, provides treatment to persons 2 and 3, z = {0, 1, 1, 0}, person
> i = 1 might respond one way, y_{i=1,z={0,1,1,0}}, and when treatment is
> assigned to persons 3 and 4, z = {0, 0, 1, 1} person i = 1 might act another
> way, y_{i=1,z={0,0,1,1}}. More generally, we might say that if the experiment
> had a causal effect on person i, then her outcome would differ under
> different realizations of the experimental treatment as a whole
> y_{i,z} != y_{i,z'}. The fundamental problem of causal inference reminds us
> that we can never see both states of the world: we only observe the outcome
> from person i under one treatment assignment vector, either z or some z' not
> both (Holland 1986; Brady 2008).
>
> Fisher's (1935, chap. 2) approach to design-based statistical inference as
> developed by Paul Rosenbaum (2010) begins with the premise of the fundamental
> problem of causal inference. Since we cannot observe all of the ways that a
> given person would respond to different treatments, the Fisher and Rosenbaum
> approach suggests that we focus on learning about how *models* of
> unobservable counterfactual outcomes relate to what we can observe. Although
> we do not know how person i would have acted under all possible experimental
> scenarios, we can learn how much information we have to dispel certain claims
> or hypotheses. This conceptual move---sidestepping the fundamental problem of
> causal inference by learning about claims made by scientists---drives
> hypothesis testing in general.

**Why this one.** The best instance of the concrete case arriving before the
general symbol. Four named people and two written-out assignment vectors come
first, so `y_{i,z} != y_{i,z'}` reads as shorthand for something the reader
already understands rather than as a new thing to decode. It also contains no
acronym and no term carried over from earlier pages, so it stands alone
better than any other candidate.

---

## Runner-up: Bowers (2014), p. 1

"Comment: Method Games---A Proposal for Assessing and Learning about Methods,"
*Sociological Methodology*, opening two paragraphs.

**Verified against page 1 of the source PDF.** 213 words.

> Imagine assessing a promising method for pattern discovery using a game. One
> scholar would invent a true pattern of features, generate an outcome, and
> perhaps hide this pattern amid irrelevant information. For example, the game
> designer might provide 15 binary features of 40 cases to the players. Players
> would compete to discover the hidden truth. One version of the method game
> would require that participants use a particular algorithm. A second version
> would allow participants to choose their own algorithms. For example, some
> might choose a variant of qualitative comparative analysis (QCA; Rihoux and
> Ragin 2008), others would implement an adaptive lasso (Zou 2006), and still
> others might prefer one of the many competitors to the lasso, such as the
> smoothly clipped absolute deviation (SCAD) penalty (Fan and Li 2001), random
> forests (Breiman 2001), or kernel-regularized least squares (Hainmueller and
> Hazlett 2012).
>
> In the first version of the competition, we would learn about craft: In
> different hands, the same method may perform differently. The results of this
> competition would teach us about the many kinds of substantive and
> methodological judgments required to use the method successfully. In the
> version of the game in which players choose different approaches, we could
> learn how different methods compare in their ability to address a given
> problem.

**Why this one.** Every acronym is spelled out before it is abbreviated, and
every number counts a named thing --- 15 binary features of 40 cases. It builds
a whole proposal in plain English with no notation at all. That last fact is
also its limitation for this purpose: it cannot model notation discipline,
because it has no notation.

---

## Pairing option

Nothing forces a single passage. The strongest pair is 2013 plus 2019, because
they cover the two registers you actually write in: 2013 shows the discipline
holding up under heavy notation, and 2019 shows it in ordinary policy prose
with no notation at all. Together they cost about 614 words. The whole Writing
Style section is now 1,588 words, so that is a real cost, and one well-chosen
passage probably beats two.

## Choosing among the three leaders

Each models a different virtue, and all three are verified.

- **2013, p. 102 (335 words)** --- every symbol defined at first appearance
  under heavy notation, then translated back into English. No typos, no
  borrowed acronyms, no rule violations. Take this one if you want the hardest
  case modeled.
- **2019, p. 9 (279 words)** --- a term defined in one plain sentence, then a
  concrete case, then numbers. Take this one if you want ordinary prose
  modeled, and decide what to do about the "(e.g Gale" typo.
- **2020, p. 19 (224 words)** --- three confusable terms defined against each
  other. Take this one if the failure you most want prevented is the one your
  memo describes, where a single word ("family") meant different things to
  writer and reader.

My pick is still 2013, on the reasoning that a model which holds under notation
will hold in plain prose too, and it is the only one of the three with nothing
to explain away. But 2020 is the closest match to the specific failure your memo
documents, and that is a fair basis for preferring it.

---

## Not verified, and not recommended

These were returned by the readers but not checked against the source PDFs by
the main session. Verify before using.

- **2013 Candidate A** (pp. 97-98, Introduction, ~230 words): the election
  monitoring scene --- observers, thugs moving to a control village, the
  question of what the causal effect even is. The best motivate-before-method
  passage of the whole set, but it contains no notation.
- **2013 Candidate C** (pp. 107-108, ~260 words): states what a well-operating
  test should do in plain words before naming "unbiasedness" and "power." About
  90 of its 260 words are quoted from Rosenbaum's glossary rather than written
  by you, so it models your sequencing more than your sentences.
- **2016 Candidate B** (p. 397, ~265 words): argues for the sum-of-squared-
  residual statistic by naming what the Kolmogorov-Smirnov statistic discards.
  "BFP" and "KS" are glossed earlier in the paper, not inside the excerpt.
- **2016 Candidate C** (p. 399, ~214 words): states a prior expectation, says
  how it was checked, and reports the case where your own proposal loses. Ends
  on a limitation rather than a boast.
- **2014 Candidate B** (pp. 2-3, 303 words): the six success rates, each with
  "found the truth and only the truth" defined before any percentage. Opens
  with "Notice that," which your own rules flag.
- **2014 Candidate C** (pp. 3-4, 239 words): names the paper's own limits in
  checkable specifics. Opens with "Obviously," which your rules also flag.
- **2019 Candidate B** (p. 7, 297 words): explains what randomization buys by
  naming the objection it defeats --- that those exposed to policy X were
  wealthier or healthier --- with Fisher's eight cups of tea as the concrete
  case. "RCT" arrives unexpanded; the paper defines it on p. 6.
- **2019 Candidate C** (pp. 13-14, 295 words): government forms as the concrete
  answer to whether academics have anything to say to government. Three defects
  in the original, per the reader: it opens with "Consider for example," which
  your own rules ban, a missing period after a citation, and "ought do" missing
  its "to."

## Also from the 2020 chapter, verified but not recommended

Both were read from the PDF text layer and checked against the page images.

- **2020, p. 1 (Section 1 opening), 253 words.** Verified against page 2 of the
  PDF. Opens "No one knows the true causal effect of an intervention," then
  explains why in plain English, then previews the chapter. The best
  motivate-before-method opening in the whole set and the only candidate that
  starts on a flat declarative sentence. It contains no notation, so like the
  2014 passage it cannot model notation discipline. It also joins two
  independent clauses with a semicolon in its second sentence.
- **2020, pp. 19-20 (Section 4.1), 279 words.** Verified against pages 19-20.
  Defines an unbiased test while saying in the same breath that it is not to be
  confused with an unbiased estimator, then does the same for a consistent test
  against a consistent estimator. Strong on distinguishing confusable terms, but
  the p. 19 passage above does that job in fewer words.

There is a further passage at the start of Section 7 (p. 40) that announces
"Before explaining this framework, we need to define a few additional terms"
and then defines treatment odds and the treatment odds ratio, each formula
paired with its plain-English gloss. I read it from the text layer but did not
check it against the page image, so verify it before using it.

## Coverage

All five papers are now covered. `bowers2020causality.pdf` was read by the main
session after two readers failed on it; at 52 pages it is by far the longest of
the five, which is the likeliest explanation.
