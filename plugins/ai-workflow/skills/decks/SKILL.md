---
name: decks
description: Draft, revise, or critique slide decks for Jake --- research talks and teaching --- in LaTeX Beamer or Quarto revealjs, detected from the project. Use when slides, a deck, a talk, a presentation, lecture slides, or workshop materials are the deliverable, or when .tex beamer or revealjs .qmd files are in scope. Two modes (research, teaching) with length profiles from a 12-minute conference slot to a multi-hour workshop.
---

# Slide decks

This skill gives an AI assistant instructions for drafting, revising, and
critiquing slide decks for Jake Bowers, in two modes: research talks and
teaching. The global `CLAUDE.md` applies alongside this skill --- every writing
rule there (stress position, plain verbs, no vague evaluatives, epistemic
verbs kept at their stated strength) binds slide text too, and slides tempt
every vice that file bans, because compression invites jargon and bullets
invite fragments that say nothing.

ASCII only in source files. In LaTeX, use LaTeX commands; in Quarto markdown,
use the ASCII approximations (`---`, `->`, straight quotes).

---

## 1. What a deck is for

A deck is not the paper, and it is not the lecture notes. The audience can
read or listen, but not both at once; every word on the screen competes with
the words Jake is saying. So the deck's job is narrow:

- **Research mode.** The talk earns three beliefs: the question matters, the
  design answers it, and the result is what Jake says it is. The deck supports
  a spoken argument; the paper carries the details. Success is an audience
  member who wants to read the paper and knows what they will find there.
- **Teaching mode.** The session earns a capability: afterward, the audience
  can do something they could not do before. The deck structures attention
  and practice; it is not a complete record of the material. Success is
  measured by what the audience can do, not by what the slides covered.

A deck that tries to be the paper (research) or the textbook (teaching) fails
at being a deck.

## 2. Step 0 --- the brief

Before drafting any slide, settle these. Ask short menu questions for
whatever is unknown; do not guess silently.

- **Mode**: research or teaching.
- **Audience**: who is in the room and what they already know. A methods
  audience, a substantive political science audience, undergraduates, grad
  students, and a mixed workshop room need different notation loads and
  different examples. Lectures and workshops in particular serve different
  audiences --- ask which.
- **Length in minutes**, and whether interruptions are expected. A 30-minute
  slot with interruption culture holds about 20 minutes of content; the same
  slot uninterrupted holds nearly all 30.
- **Toolchain**: detect from the project. Existing `.tex` with
  `\documentclass{beamer}` means Beamer; a `.qmd` with `format: revealjs`
  means Quarto. If the project has neither, ask rather than choose.
- **For research talks**: which paper, and the one sentence that must survive
  if the audience forgets everything else. That sentence is the talk's
  target; every slide either advances it or gets cut.

## 3. Principles for every deck

1. **One point per slide, and the title states it.** Titles are
   full-sentence assertions: "Interference bias grows with cluster size,"
   not "Results." If a slide cannot be titled with its claim, it does not
   yet have one --- find the claim or cut the slide. Read in sequence, the
   titles alone should carry the argument.
2. **Evidence sits under the assertion.** The body of the slide shows why
   the title is true: a figure, a small table, a displayed equation, a
   quotation. Body text beyond roughly 30 words means the slide is doing the
   speaking instead of Jake.
3. **Figures over tables; remake both for the screen.** Never paste a
   paper's table or figure onto a slide. A slide table holds a handful of
   numbers, each of which will be said aloud; a slide figure has axis labels
   and annotations legible from the back row. If the paper's regression
   table matters, the slide shows the one or two estimates that matter, with
   uncertainty, as a plot.
4. **Progressive disclosure sparingly.** Reveal in steps only when the
   pause itself teaches --- a prediction the audience should make before
   seeing the answer, a derivation whose steps must land one at a time.
   Decorative builds slow the talk and break navigation.
5. **The deck ends on the contribution.** The stress position applies at
   deck scale: the last content slide states what the audience now knows or
   can do --- not "Thank you," not "Questions?", not a references dump. Keep
   a contact-and-references slide after it if needed, but the argument
   closes on the claim.
6. **Budget, then cut.** Plan about one substantive slide per minute in
   research mode and one per two to three minutes in teaching mode, then cut
   until the count is under budget. A deck that fits exactly has no room for
   a question, a stumble, or a slow start.
7. **Back-pocket slides.** Anticipated questions get appendix slides:
   robustness, the formal theorem statement, the extra example, the
   alternative specification. When a `reviewer2` revision plan exists for
   the paper, its must-fix and decline-with-reason items are the seed list
   for these slides.
8. **Citations on slides clear the `verify-citations` bar.** Any "X (year)"
   on a slide is real, correctly attributed, and relevant. A fabricated or
   misattributed citation on a screen is public in a way a draft never is.

## 4. Research mode

- **Open with the substantive question in words**, no notation, inside 90
  seconds: the scenario, the decision or puzzle, the stakes. This is the
  math skill's motivate-before-formalism rule compressed to a slide or two.
- **The target of inference gets its own slide.** The estimand (or the
  hypothesis and test, for randomization-inference work) appears in words
  first, then in the minimum notation, before any results. The audience
  should never see an estimate while unsure what is being estimated.
- **Design before results.** What was randomized or assumed, what the
  comparison is, why it licenses the inference. One slide of design earns
  more belief than three slides of robustness.
- **Claims at the paper's strength.** The epistemic verbs on slides match
  the paper: "suggests" does not become "shows" because the room is
  friendly. A slide is a public claim.
- **Interruption culture.** Protect the first three and last two slides ---
  they happen no matter what. Build the middle in modules so that a
  15-minute detour costs a module, not the conclusion. Decide in advance,
  and mark in the source, which slides to skip when time runs short.

Length profiles (adjust by the brief, not mechanically):

- **12-minute conference slot** (the common case): 10--13 slides. One
  question, one design, one main-result figure, one sentence of robustness,
  one contribution slide. No outline slide; no literature-review slide ---
  at most one slide placing the paper in its conversation. The talk is an
  advertisement for the paper, not a summary of it.
- **15--20 minutes**: room for a mechanism or a second result, or a worked
  toy example of the method. Still no outline slide.
- **30 minutes**: with interruption culture, plan 20 minutes of content and
  modular depth; without, up to about 25 substantive slides and a real toy
  example before the general result.
- **45--60 minute seminar**: the full arc --- motivation, toy example,
  design, main results, robustness or sensitivity analysis, scope and
  limits --- plus deep back-pocket slides, because a seminar audience asks
  about the design's edges. An outline slide is permitted here if the talk
  has genuinely distinct parts; it should be one slide and never return.

## 5. Teaching mode

- **Start from what the audience should be able to do afterward.** Write
  those capabilities down before drafting (for Jake, not necessarily as a
  slide). Every segment serves one of them. An opening puzzle --- data with
  a surprise, a claim to evaluate, a design to critique --- beats a bulleted
  agenda.
- **Calibrate to the room.** Undergraduate course, graduate methods course,
  and mixed-background workshop want different notation loads, different
  examples, and different amounts of R on screen. The brief (section 2)
  names the room; do not reuse a grad-course deck for a workshop by
  changing the title slide.
- **Attention resets every 10--15 minutes.** Plan a change of activity at
  least that often: a question to the room, a prediction before a reveal, a
  two-minute pair exercise, a live computation. The deck marks these
  explicitly rather than hoping they happen.
- **Worked example before general statement** --- graduated formalization,
  as in the math skill. The concrete case that the audience computes or
  inspects comes before the theorem or the estimator in general form.
- **Slides do not carry everything.** Derivations, algebra, and live coding
  often belong on a board, a document camera, or a live R session, with the
  slide holding only the setup and the conclusion. A slide of completed
  algebra teaches less than the same algebra unfolding.
- **Close segments with retrieval.** End each segment with a prompt that
  makes the audience produce what was just established ("what would happen
  to the p-value if..."), not with a summary that re-presents it.

Length profiles:

- **75--90 minute lecture**: two or three segments, each opening with a
  puzzle and closing with retrieval; roughly 25--35 slides total, with
  activity slides counted in the budget.
- **2--4 hour workshop**: alternate blocks of about 20 minutes of
  presentation with 20--40 minutes of guided practice. Exercise slides stay
  on screen while people work, so each carries the task, where the data
  live, and the time box. The deck for a workshop is two interleaved decks:
  instruction and exercises.

## 6. Math on slides

- Less notation than the paper, always. Every symbol on a slide is defined
  on that slide or the one before it; a symbol the audience must remember
  from ten slides ago is a symbol to cut or redefine.
- Show the structure of a derivation, not the algebra: the starting object,
  the one or two steps where something substantive happens, the result.
  The full derivation is a back-pocket slide or the paper's appendix.
- Theorem slides state assumptions and conclusion in words, with the formal
  statement in the back pocket. The math skill's honesty rules apply
  unchanged: what is proved is "proved," what is simulated is "simulation
  evidence," on a screen as in print.

## 7. Toolchain notes

- **Beamer**: one sentence per `\frametitle`; `\pause` and overlays only
  under principle 4; no `allowframebreaks` --- a frame that needs breaking
  has two points in it; back-pocket slides after `\appendix` so the slide
  count shown to the audience ends at the conclusion; speaker notes in
  `\note{}` rather than cramped onto the slide.
- **Quarto revealjs**: `incremental: false` as the default, enabling
  per-list builds only deliberately; speaker notes in `::: notes`; for code,
  `echo: true` only when the code itself teaches, and `output-location:
  fragment` for prediction-then-reveal moments; exercise slides get their
  own visual style (a background tint) so the room can tell instruction
  from task at a glance.

## 8. Critiquing an existing deck

When asked to review a deck rather than draft one, apply sections 3--7 as a
checklist and report findings per slide, by slide number, each with the
specific fix --- the `reviewer2` grounding rule retargeted at slides. "Slide
14's title is a topic, not a claim; retitle to the finding it shows" is a
finding. "The deck could be tightened" is not.

## 9. Self-audit before delivering

Run these and report what was found, not that checks ran:

- **Title test.** Read only the titles, in order. Do they carry the
  argument (research) or the session's arc (teaching)?
- **Budget test.** Slide count against the minutes, with the arithmetic
  shown. Name the slides to cut if time runs short.
- **Back-row test.** Any figure with unreadable labels, any body text over
  the word budget, any pasted paper table --- listed by slide number.
- **Verb test.** Every claim-bearing slide checked against the paper's (or
  the field's) strength of evidence.
- **Citation test.** Every "X (year)" on a slide verified or flagged, per
  the `verify-citations` skill.
- **Ending test.** The last content slide states the contribution or the
  capability --- not thanks, not questions.

If any test fails, fix or flag before handing the deck to Jake.
