---
name: style-audit
description: Audit a draft and report each finding with a rewrite. Use for a style pass, de-AI-ing prose, a last read before a paper or memo goes out, and to check your own long reply before sending it.
---

<!-- Synced against skills/style-audit/SKILL.md at commit 20285d2 (2026-08-23). -->

# Style audit

This skill turns Jake's writing rules into an audit procedure for existing
text. Those rules live in the Instructions for Claude field and in the
`bowers-prose` skill, and they govern how new prose gets written; this skill
checks prose that already exists --- written by Jake, a coauthor, an AI, or
Jake-two-years-ago. It adds no rules of its own. Where this file and those
rules disagree, those rules win.

Section 6 below holds the catalog of named offenders. It sits here rather than
with the drafting rules because a list of banned words helps an auditor and
hurts a drafter.

Scope: any prose leaving the desk --- papers, memos, grants, course
materials, referee reports, response memos, slide text, README prose, long
emails. Code style belongs to the `bowers-code` skill, but the ASCII rule and the
banned patterns apply to prose inside code comments and documentation too.

## 1. Two passes, in order

**Pass 1 is mechanical.** Run the scanner bundled with this skill over the
file Jake attached:

```
python3 scripts/style_scan.py <the attached file>
```

If that will not run --- code execution switched off, no attached file, any
other reason --- say so in one line and do Pass 1 by reading instead, working
through the document for the categories in section 6 and for characters
outside printable ASCII. Reading finds most of the named offenders and misses
some. It is worst at unicode, because a unicode minus sign and an ASCII hyphen
look identical on screen. Either way, the report says which way Pass 1 was
done.

It flags non-ASCII characters (with codepoint and name), the named offenders
catalogued in section 6 below (structural and industrial metaphors, vague
evaluatives, locative figures, colloquial idioms, throat-clearing,
ornamental transitions, empty hedges), and lines that carry both an em-dash
and a semicolon. The scanner carries its own copy of these patterns in
`RAW_PATTERNS`, so it does not read section 6 at runtime; if you add an
offender to the catalog, add the pattern to the script too. It skips fenced code blocks in markdown and comment lines
in LaTeX.

Every hit is a candidate, not a verdict. Literal uses pass ("an actual
load-bearing wall"); a quotation from someone else's text passes (but note
it); a technical term of art that the document defines and glosses passes.
The scanner exists to make the first pass cheap and complete, not to decide.

**Pass 2 is judgment, and it is the audit.** The catalog in section 6 is
illustrative, not a closed checklist --- read for the pattern, not for the
words. Reread the writing rules in Instructions for Claude and in the
`bowers-prose` skill, and then section 6 below, before this pass; then work
through the document paragraph by paragraph:

- **The substitution test, on everything evaluative, structural,
  impressive, or idiomatic** --- including words on no list. Try to replace
  the word with its concrete content. Easy substitution: the word was
  decorative; the substitute is the sentence. Hard substitution: the word
  was hiding a missing thought; the finding is the missing thought, not the
  word.
- **Sentence mechanics** (Gopen and Swan, as stated in the drafting rules):
  stress position holds the new claim; topic position holds familiar
  context; old before new; subject near verb; action in the verb; one point
  per sentence.
- **End-weight at paragraph and section scale**: no paragraph or section
  ends on a caveat, a competitor's method, or a bare citation when its point
  is Jake's own claim.
- **Epistemic verbs against the evidence**: "estimate," "identify,"
  "assume," "suggest," "consistent with," "show," "prove" each checked
  against what the design or proof actually supports. Strengthened claims
  are must-fix findings.
- **Defined-term consistency**: a term introduced once is used throughout;
  synonyms swapped in for defined technical terms are findings.
- **Attribution**: any term or position attributed to a cited author is one
  the cited work actually uses --- the `verify-citations` bar, applied to
  words instead of metadata.
- **Conclusions**: a concluding paragraph that restates the introduction is
  a finding; the fix names the implication, tension, or next question the
  conclusion should carry.

## 2. What a finding looks like

Report each finding with:

1. **Location** --- file and line (from the scanner) or section and
   paragraph (from the read).
2. **The text**, quoted exactly.
3. **The category** (structural-metaphor, vague-evaluative, locative,
   idiom, throat-clearing, hedge, transition, nominalization, stress
   position, end-weight, verb-drift, term-drift, attribution, unicode).
4. **Why it fails, concretely** --- one sentence naming what the word hides
   or misplaces. Not "this is on the banned list" but "appropriate hides
   the criterion: clustered at the school level because assignment was."
5. **A proposed rewrite**, or --- when the substitution is hard because the
   underlying thought is missing --- a question that names the missing
   thought. An ambiguous sentence gets a question, never a silent rewrite.

Order findings by severity: meaning-changing problems first (verb-drift,
attribution, term-drift), then clarity (stress position, end-weight,
throat-clearing), then surface (unicode, transitions, idioms). Close with a
count by category and a list of what was scanned and what was read.

## 3. Non-negotiables

These repeat the drafting rules because an audit is where they are easiest to
violate:

- Propose rewrites; do not apply them unless Jake asks for an applied pass.
  When he does ask, apply only the findings he approves or the whole set if
  he says so, and never batch a meaning change in with surface fixes.
- Statistical meaning survives every rewrite: estimands, identification
  assumptions, hypotheses, error rates, uncertainty language.
- Preserve the tense and form Jake established; fix the word that deviates.
- Do not introduce facts, numbers, references, or claims the draft did not
  make.

## 4. Reporting rule

Do not say "style checked." Say what was scanned, what was read, what was
found, and what was not checked. Good: "Scanner covered paper.tex and both
memos: 3 unicode characters, 2 vague evaluatives, 1 dash-semicolon line.
Judgment pass covered sections 1-4; sections 5-6 (the proofs) I read only
for verb calibration. Two paragraph endings bury their point; details
below." Bad: "The draft largely follows the style rules."

## 5. Final checklist

1. Scanner run on every file in scope, hits triaged (candidate -> finding
   or pass, with reasons for the passes when nontrivial)?
2. Judgment pass done paragraph by paragraph, not by skimming for listed
   words?
3. Every finding located, quoted, categorized, explained concretely, and
   paired with a rewrite or a question?
4. Meaning-changing findings separated from surface findings?
5. Nothing rewritten silently?
6. The report says what was and was not covered?

## 6. The catalog of named offenders

This catalog sits apart from the drafting rules for a reason that matters to
how you use it: a long list of banned
words in context while *drafting* turns attention toward avoidance, and the
banned habit then reappears in words the list does not contain. The failures
that prompted the move --- a claim "wearing" a heading, an argument that
"lands," a comparison that "runs along" dimensions --- were all absent from
this list.

So: read this catalog during an audit, which is exactly the job a list is good
for. Do not load it while drafting. The generative rule is the one in the
drafting rules: use a metaphor only when it does work a plain verb cannot, and
gloss it once when you use it.

Every entry below is illustrative, not a closed checklist. A figure on no list
that fails the substitution test is still a finding.

- Nominalizations and passive constructions that hide the actor.
- Jargon used for its own sake. Technical terms are fine when they do real work; they are not fine when a plain word would serve.
- **Architectural, anatomical, and industrial metaphors used decoratively.** Avoid metaphorical "load-bearing," "spine," "backbone," "scaffolding," "skeleton," "pillar," "cornerstone," "foundational," "the connective tissue," and similar structural-engineering or body-part figures. The same caution applies to industrial figures used for methodology: "the machinery of X," "the apparatus of Y," "the engine of Z," "the gears of W." These sound substantive while committing to nothing the reader can check, and they are a tell of AI prose --- not Bowers, not Didion, not Rosenbaum. Literal use is fine (an actual load-bearing wall, an actual vertebrate spine, an actual machine). Metaphorical use is almost never fine: if an assumption matters, name what depends on it; if a section organizes the rest, name which sections refer back to it; if a result anchors the paper, say which downstream claims fail without it; if "the machinery" is doing work, name the specific construction or formula. The same caution covers software, security, and infrastructure figures used metaphorically: "firewall," "sandbox," "guardrail," "pipeline," "plumbing," "the stack." These read as precise but name nothing the reader can check; say what the rule actually is --- for "firewall," what is kept out of what, and by what mechanism (e.g., "the model proposes a coding; the count method, which the model never alters, produces the number"). Replace the figure with the thing.
- **Vague evaluative judgments that hide the agent and the criterion.** Avoid "is appropriate," "are appropriate," "is suitable," "is reasonable," "is warranted," "is justified," "is well-suited," "makes sense," "is the right choice," "is comfortable," "comfortably above / below," "a comfortable margin." Each invites: who says? on what grounds? compared to what alternative? Name the decider, the criterion, and the alternative being rejected. "Clustered standard errors are appropriate" tells the reader nothing; "we cluster standard errors at the school level because treatment was assigned at that level and outcomes within schools are correlated --- ignoring the clustering would understate uncertainty" tells the reader the design and the reason. "The conclusion is comfortably above threshold" tells the reader nothing; "the conclusion is above threshold and the largest perturbation in the sensitivity table leaves it above 50" tells the reader the magnitude. The same caution applies to "valid," "robust," "principled," "natural" when used without saying valid/robust/principled/natural with respect to what.
- **Locative figures that hide a plain verb.** Avoid "the framework reads onto X," "the analysis maps onto Y," "the model reads cleanly off Z," "the theory lives in P," "the argument sits across Q." These figures replace a plain verb ("applies to," "fits," "handles," "covers," "extends to") with a spatial gesture that adds nothing. If the framework applies to a range of designs, say "applies to"; if a method handles a class of problems, say "handles." The spatial figure is the tell that the writer has not chosen the verb.
- **Colloquial idioms and figurative cliches.** Avoid stock idioms that a plain verb would replace: "earn their keep," "shore up," "hold at bay," "fold in," "wave away," "keep faith with," "put on a slide," "with eyes open," "hand-waving," "walk the list." These are not pretentious, and they pass the structural, evaluative, and locative checks above, which is exactly why they slip through --- yet each hides a plain verb (shore up = strengthen, wave away = dismiss, fold in = add, walk the list = go through one at a time), so they fail the substitution test. Replace the idiom with the plain verb; keep the figure only when it does real work the plain verb cannot, and gloss it once when you keep it. Some idioms are also structural-engineering metaphors --- "shore up," "load-bearing" --- and are already covered above; this rule adds the folksy idioms that are not.
- **Reader-directed imperatives in finished prose.** The proof register writes derivations as commands to the reader --- "Consider a sequence," "Run both researchers through the model," "Relabel K as 1 - K," "Check at (1, 0)," "Start with the second row," "Let K be a fair coin." In a paper, memo, or email these read as assigned work, and each hides its actor: who runs, who checks? Write the declarative with the actor named: "Each researcher feeds the model their own coded record"; "The relabeling K -> 1 - K permutes the nodal types"; "When C = 0, K is a fair coin." The same failure produces leftover outline items: a planning sentence addressed to the writer ("Spell his example out in our notation") that the paragraph below it then executes. Once the paragraph exists, the instruction must be deleted, not published.
- **Noun-phrase-plus-colon fragments posing as sentences.** "His example, written in our notation: the raw datum is a fact F" has no main verb; a topic label with a colon is not a sentence. Write the sentence: "In our notation, the raw datum of his example is a fact F." Headings and list labels may be fragments; prose may not.
- **A technical term arriving before its content.** Naming a phenomenon in a heading or topic sentence ("the example is an identification failure at the coding map") and defining the term paragraphs later reverses graduated formalization: the reader meets the label while the thought is still owed. State the plain content first --- "a flipped coding with share 1 - t produces the same distribution of coded records as the original coding with share t, so no data can tell the two apart" --- and then ask whether the term still earns a mention. Often the plain statement is complete and the term adds only a name; keep the name only for an audience that needs it, introduced after the statement it names.
- Hedging that adds no information ("it is perhaps the case that arguably..."). Qualify where the qualification matters; otherwise, commit.
- Ornamental transitions ("Moreover," "Furthermore," "It is important to note that"). If the logic is clear, the transition is unnecessary.
- **Throat-clearing that announces a claim instead of making it.** The governing test is deletion: strike the words standing in front of the claim, and if nothing is lost --- not information, not emphasis --- they were throat-clearing, and what remains is the sentence you wanted. This pattern changes grammatical form freely, so a search for any one form misses the rest. The families: expletive "it" ("it is important to," "it is worth (noting / saying / mentioning / emphasizing) that," "it should be noted that," "it is interesting / crucial / essential / useful that," "note that," "one should observe that"); modifiers hung on a noun ("a reason worth stating," "a point worth making," "a case worth noting," "which is worth emphasizing," "an observation worth flagging"); existential "there" ("there is an important point here," "there are several things worth noting"); first-person announcements ("I want to emphasize that," "let me note that," "we should observe that," "this bears mentioning," "this cannot be overstated"); sentence adverbs asserting importance ("Importantly," "Notably," "Crucially," "Significantly," "Tellingly"); nominal setups ("one thing to note is that," "a key point is that," "the important thing here is that," "what is worth emphasizing is that"); and forward-pointing counts ("two things are worth saying about X," "three points deserve emphasis"). Each defers the sentence's real subject and hides who cares and why. Make the claim directly --- "it is worth saying what the weights are" becomes "the weights are X"; "it is important to control the FWER" becomes "controlling the FWER matters because ..." with the reason supplied, or name what fails if you do not; "no for the hypergeometric, for a reason worth stating" becomes "no for the hypergeometric," with the reason in the sentence after. Emphasis comes from a short declarative sentence, never from an announcement that emphasis is coming. Two constructions resemble this one and survive the deletion test. A forecast that tells the reader where to look carries information the announcement lacks --- "we prove this in Section 4," "the derivation is in the supplement" --- and the pedagogical voice described above depends on it. An adverb that reports how a claim stands against an expectation the reader already holds also does real work: "unexpectedly," "contrary to Fairfield and Charman's prediction," and "against our own prior" state a relation rather than the writer's enthusiasm, provided the expectation was stated. Delete the word and ask whether a claim disappeared with it. (This generalizes the "It is important to note that" example under Ornamental transitions above.)
- Concluding paragraphs that merely restate the introduction. A conclusion should say something new --- an implication, a tension, a next question.
