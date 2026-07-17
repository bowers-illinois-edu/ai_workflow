---
name: style-audit
description: Audit an existing draft against Jake's writing rules and report per-instance findings with proposed rewrites. Use when asked to check the writing, run a style pass, edit for style, de-AI the prose, or apply the writing rules to a draft; and as a final pass before a paper, memo, grant, or long email leaves the desk. Bundles a scanner script (scripts/style_scan.py) for the mechanical first pass over the named offenders and unicode; the judgment pass applies the substitution test to what no list catches.
---

# Style audit

This skill turns the writing rules in the global `CLAUDE.md` into an audit
procedure for existing text. The global file governs how new prose gets
written; this skill checks prose that already exists --- written by Jake, a
coauthor, an AI, or Jake-two-years-ago. It adds no rules of its own. Where
this file and the global `CLAUDE.md` disagree, the global file wins.

Scope: any prose leaving the desk --- papers, memos, grants, course
materials, referee reports, response memos, slide text, README prose, long
emails. Code style belongs to `CLAUDE_CODING.md`, but the ASCII rule and the
banned patterns apply to prose inside code comments and documentation too.

## 1. Two passes, in order

**Pass 1 is mechanical.** Run the bundled scanner:

```
python3 scripts/style_scan.py Paper/paper.tex Memos/*.md
```

It flags non-ASCII characters (with codepoint and name), the named offenders
from the global `CLAUDE.md` (structural and industrial metaphors, vague
evaluatives, locative figures, colloquial idioms, throat-clearing,
ornamental transitions, empty hedges), and lines that carry both an em-dash
and a semicolon. It skips fenced code blocks in markdown and comment lines
in LaTeX.

Every hit is a candidate, not a verdict. Literal uses pass ("an actual
load-bearing wall"); a quotation from someone else's text passes (but note
it); a technical term of art that the document defines and glosses passes.
The scanner exists to make the first pass cheap and complete, not to decide.

**Pass 2 is judgment, and it is the audit.** The global `CLAUDE.md` says it
directly: the lists are illustrative, not a closed checklist --- read for
the pattern, not for the words. Reread the "Writing Style" section of the
global file before this pass, then work through the document
paragraph by paragraph:

- **The substitution test, on everything evaluative, structural,
  impressive, or idiomatic** --- including words on no list. Try to replace
  the word with its concrete content. Easy substitution: the word was
  decorative; the substitute is the sentence. Hard substitution: the word
  was hiding a missing thought; the finding is the missing thought, not the
  word.
- **Sentence mechanics** (Gopen and Swan, as stated in the global file):
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

These repeat the global file because an audit is where they are easiest to
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
