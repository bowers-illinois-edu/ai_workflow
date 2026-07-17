---
name: review-response
description: Draft a response memo to actual peer reviewers after a decision. Use for revise-and-resubmit (R&R) responses, response-to-reviewers memos, rebuttals, decision letters, or when real reviewer comments are pasted in to be answered. Not for simulating a referee before submission --- that is the reviewer2 skill. Bundles LaTeX and Quarto memo templates.
---

# Response to reviewers

Instructions for helping craft a response to peer reviewers. This document governs the tone, structure, and rhetorical strategy of the response memo. It supplements --- and does not override --- the writing style principles in the global `CLAUDE.md`. Two memo templates live in this skill directory: `response_to_reviewers_template.tex` (LaTeX) and `response_to_reviewers_template.qmd` (Quarto).

## Context

This paper is under review. The decision is "revise and resubmit". The goal is an accept. Before drafting, read the journal's aims and scope. Understand what methods and topics it publishes, what level of technical detail it expects, and how long its typical articles run. Do not question the journal choice --- the authors chose this venue deliberately.

## The audience is the editor, not the reviewer

Journal editors and published guides agree on something easy to miss: the primary audience for the response memo is the handling editor and associate editor, not the reviewers.

- AEs at top statistics journals are explicitly instructed to form their own independent judgment --- they do not simply tally reviewer votes (IMS AE Guidelines for Annals of Statistics).
- The JASA editors have stated that they value papers where the revision reflects the authors' own intellectual labor, not mechanical compliance with reviewer requests (ASA, "JASA Editors Offer Advice to Authors").
- A major-revision decision means the editor found the topic interesting but could not yet judge whether the work is good enough. The response letter must convince the editor that it is (Williams & Kerns, 2019, "Writing Author Response Letters That Get Editors to 'Yes'").

You do not need to win an argument with a reviewer. You need to show the editor that you engaged seriously, responded substantively, and made defensible choices --- including the choice to decline certain suggestions.

## A response, not a rebuttal

Frame the response document as "here is how the feedback improved the paper" --- even when you disagree with specific suggestions. A rebuttal says: "Here is why you are wrong." A strategic response says: "Here is how your feedback made the paper better, and here is where we chart a different course."

The response document is itself a persuasive document --- a sloppy or defensive one can sink a good paper (Noble, 2017). Invest as much care in it as in the revised manuscript.

## Overriding principles

### 1. Gratitude first, always genuine

Open every section of the response with sincere thanks. Not boilerplate --- specific thanks that show we read carefully and understood what the reviewer was driving at. If a reviewer pushed us to think harder, say so. If a comment improved the paper, say that concretely ("This comment led us to add Section X, which strengthens the paper"). Gratitude is not weakness; it signals that we are colleagues engaged in the same intellectual project. We review other papers ourselves --- we know the labor involved and want to honor it.

### 2. Every point gets a response

Do not skip or silently absorb any comment, no matter how minor. The reviewer took time to write it; we take time to answer it. For minor points (typos, notation fixes), a brief acknowledgment and confirmation of the fix is sufficient. For substantive points, demonstrate that we understood the concern and engaged with it seriously. Then do one of three things: (a) describe what we changed, (b) explain why we did not change anything, or (c) describe what we did instead and why.

### 3. Reproduce the reviewer's words

Quote the reviewer's language directly and at length before responding. Use block quotes in a different font, perhaps in subtly colored text (in LaTeX, `\textcolor{blue}{...}`). The reviewer should see their own words and verify that we are responding to what they actually said, not a straw version. When a comment is long, break it into logical sub-parts and respond to each. Never paraphrase a reviewer's point in a way that softens or distorts it.

### 4. Honesty over diplomacy --- but delivered with respect

If we disagree with a reviewer, say so directly. Do not hedge with empty qualifiers or bury the disagreement in a footnote. But frame the disagreement as a difference of judgment between colleagues, not as a correction. Useful phrasings:

- "Thank you for pushing on this. We think, however, that..."
- "We took this criticism seriously. Our view is that..."
- "We agree that X is true. We disagree, though, that X implies Y, because..."
- "This is a fair question, and we should have addressed it in the original manuscript. We now do so in Section X. Our position is..."

Never: "The reviewer misunderstands..." or "The reviewer fails to appreciate..." Even when the reviewer *has* misunderstood something, the fault lies with our exposition. Say: "We did not make this point clearly enough. We have revised Section X to show that..."

### 5. The paper we wrote is the paper we are defending

This is the most important principle. Some reviewers will ask us, in effect, to write a different paper. They may suggest a different estimand, a different philosophical framework, a different application, or a fundamentally different analytical strategy. We must take these suggestions seriously --- engage with them on their merits, acknowledge what is valuable in them --- and then explain clearly why *this* paper contributes enough as it stands.

Useful strategies for "write a different paper" comments:

- **Acknowledge the larger program.** "The reviewer points to an important question. We agree that [X] matters. Our paper does something narrower: it [does Y]. We think [Y] is a necessary step toward [X] and stands on its own."
- **Distinguish between what a paper *should do* and what *every* paper must do.** "We agree that [X] is a deep question. We do not think, however, that every paper touching [topic] must resolve [X] first. Our paper takes [stated assumptions] as given and asks what follows. We have revised the text to state these assumptions more explicitly and to be honest about what they leave out."
- **Show that we heard the concern and responded --- even if we did not do exactly what was asked.** Add discussion, caveats, or new analysis that addresses the spirit of the comment without capitulating on the paper's core identity.

### 6. Make the response self-contained

Paste the actual revised text --- or a substantive summary of it --- into the response memo so the reviewer can evaluate the changes without flipping back and forth to the manuscript. When a reviewer can read the new language right there in the response, they are less likely to re-read the entire paper looking for new problems (Noble, 2017, Rule 3-4). For small changes, quote the new sentence. For larger revisions, summarize the key new content and give section/page references.

### 7. Changes must be traceable

For every change we describe in the response memo, cite the specific location in the revised manuscript (section number, page number, or --- for small changes --- the exact new language). The reviewer should be able to verify every claim we make about what we changed. Use phrases like: "We have revised Section 3.2 (pp. 14--15 of the revised manuscript) to..." or "The new paragraph beginning 'We acknowledge that...' on p. 23 addresses this point."

### 8. Distinguish "we changed the paper" from "we explain here why we did not"

Use clear signposting so the reviewer knows which type of response is coming:

- **When we made a change:** "Good suggestion. We [did X] --- specifically, [describe the change and its location]."
- **When we added discussion but did not change the core approach:** "We now address this in Section X, where we discuss [summary]. We did not change [aspect of the paper's design], because [reason]."
- **When we respectfully decline:** "We considered this carefully and decided not to [do X]. The reason: [reasons]. We did, however, [describe what we did instead, if anything]."

### 9. The burden of proof is on the authors

During pre-publication review, the burden lies with the author, not the reviewer. If a reviewer raises a concern --- even speculatively --- the author's job is to fix the problem or demonstrate its unimportance with evidence, not to argue it away (Gelman, "Learning from and Responding to Statistical Criticism"). Treat every reviewer comment as if it comes from a knowledgeable expert who has identified a real issue, even when the comment is imprecise. This posture produces better responses and a better paper.

## Tone and style

Follow all writing principles from `CLAUDE.md`. In addition:

- **Register.** Formal but not stiff. The reader is a fellow scientist. First person plural ("we"). No contractions in the body of responses, but natural sentence rhythms --- not bureaucratic prose.
- **Brevity where possible, length where necessary.** A one-sentence fix deserves a one-sentence response. A deep methodological challenge deserves a multi-paragraph engagement. Match the depth of the response to the depth of the comment.
- **No defensiveness.** The worst thing a response memo can do is sound defensive. "The reviewer response that kills papers is not the one with weak science. It is the one that sounds defensive, dismissive, or evasive" (ManuSights). The response as a whole should convey: "This scrutiny improved the paper. Here is how we engaged with it." Even when we disagree, the posture is confident openness, not embattlement.
- **Misunderstanding is a writing problem.** When a reviewer misunderstands something, the fault lies with the authors for not writing clearly enough (Noble, 2017). Reframing misunderstanding as a writing problem is strategically shrewd --- and often genuinely true. "We did not explain this point clearly enough" is always stronger than any version of "the reviewer did not read carefully enough."
- **No sycophancy.** Do not flatter reviewers ("This brilliant observation..."). Be warm, be grateful, be specific --- but do not grovel. The reviewers are peers.
- **Active voice.** "We revised Section 3" not "Section 3 was revised." "The reviewer asks whether..." not "A question has been raised about..."
- All sentence-level principles from `CLAUDE.md` apply here too: action in the verb, subject near verb, one point per sentence, no ornamental transitions. Do not restate them --- just follow them.

## Rhetorical strategy by reviewer type

### The philosophical/conceptual challenge (e.g., "What do you mean by race as a treatment?")

These comments question the entire framework, not just its execution. They deserve the most careful, most respectful, and most substantive engagement. The strategy:

1. **Acknowledge the depth of the question.** Show that we know this is a real intellectual problem, not a pedantic objection.
2. **Demonstrate familiarity with the literature.** Cite the relevant debates (Holland, VanderWeele, Sen & Wasow, Kohler-Hausmann, etc.) to show we have grappled with these questions.
3. **State our position clearly.** We adopt a specific operationalization. We know it is one of several possible ones. We state what it is and why we chose it. We do not pretend it is the only defensible choice.
4. **Draw the boundary of the paper.** Every paper must take some things as given. Ours takes [X] as given and asks what follows. We are explicit about what we assume and what we do not resolve.
5. **Show what we added to the paper.** New discussion, caveats, or framing that makes our assumptions more visible.

Do *not* dismiss these concerns as "out of scope." They are in scope. What is out of scope is *resolving* them --- not *acknowledging* them.

### The technical/methodological challenge (e.g., "How do the two parameters interact?")

These comments ask for clearer math, better exposition, or additional formal results. The strategy:

1. **Thank the reviewer for pushing the technical exposition.** These comments almost always make the paper clearer.
2. **Answer the technical question directly** --- in the response memo itself, not just by pointing to the revised paper. Give the reviewer the answer here, then say where it appears in the revision.
3. **Add the requested exposition to the paper** wherever feasible. A unified expression showing both parameters, a discussion of how the bounds interact, a worked example --- these are improvements, not concessions.
4. **If we cannot provide what is asked, explain why** and describe what we provide instead.

### The empirical/practical challenge (e.g., "Why not adjust for the observed confounders?")

These comments ask us to do additional analysis, use additional data, or change the empirical design. The strategy:

1. **Take the suggestion seriously.** If the requested analysis is feasible and would strengthen the paper, do it.
2. **If we do the analysis:** Present results clearly. If results change, discuss what we learn. If results do not change, explain why that is also informative.
3. **The "do it and show why it doesn't belong" move.** When a reviewer requests an analysis we consider uninformative or tangential, we are often in a stronger position if we *do the analysis, report the results in the response memo*, and then explain why the results do not belong in the manuscript. This shows confidence, not defensiveness, and lets the reviewer see that we took them seriously.
4. **Supplement as compromise.** When a reviewer wants analyses we consider unimportant but not wrong, include them in supplementary material rather than arguing about their value. This satisfies the reviewer without distorting the paper.
5. **If we do not do the analysis:** Explain why --- data limitations, scope, or the fact that the analysis addresses a different question than the one our paper asks. Be specific about the obstacle, not vague.
6. **Distinguish between "this would improve the paper" and "this is a different paper."** Adjusting for impact zones is an improvement to *this* paper's analysis. Switching to a completely different estimand or dataset is a different paper. We can do the former; we explain why the latter is beyond the scope of this revision.
7. **The ~20% guideline.** You can decline about a fifth of reviewer suggestions and still get accepted. If you are pushing back on more than half, either the reviewers are unusually off-base or the paper has problems you are not seeing (ManuSights). When in doubt, do a few things you consider borderline out of scope to demonstrate good faith.

## Structure of the response document

Use this structure for the LaTeX response memo:

```
\title{Response to Editors and Reviewers}

[Opening paragraph: 3-4 sentences. Thank the editor, AE, and reviewers.
Summarize the major changes at a high level. Say concretely how the
revisions strengthened the paper.]

\section{Summary of Major Revisions}

[Bulleted list of the most important changes, with section/page references.
This gives the reviewers a roadmap before they dive into the point-by-point.]

\section{Response to Editor}

[Address any editor-specific requests.]

\section{Response to Reviewer 1}

[Point-by-point. Quote in red, respond in black (or use the \response
environment from response_to_reviewers_template.tex in this skill
directory). Number the points for easy reference.]

\section{Response to Reviewer 2}

[Same format.]

\section{Response to Reviewer 3}

[Same format.]
```

## Handling specific situations

### When a reviewer is wrong about a factual claim

Do not say "The reviewer is wrong." Say: "Thank you for flagging this. We read it differently: [correct statement], because [evidence/citation]. We have clarified the point at [location]."

### When two reviewers contradict each other

Acknowledge both perspectives. Explain the choice we made and why. "Reviewer 1 suggests X, while Reviewer 3 suggests Y. We have chosen [approach], because [reasons]. We discuss the alternative in [section]."

### When a reviewer asks for something we already did

Point to the relevant passage. "We agree this is important. We addressed it in the original manuscript at [location], but clearly we did not make the point visible enough. We have revised the passage so that [point] stands out."

### When a reviewer asks for something impossible or unreasonable

Do not call it impossible or unreasonable. Describe the specific obstacle. "We looked into this. [Specific obstacle: data not available for years X-Y, the estimand under this design answers a different question, etc.]. As an alternative, we [describe what we did instead]."

### When we need to push back firmly

Sometimes a reviewer's comment, taken to its logical conclusion, would require abandoning the paper's contribution. In these cases:

1. Restate the comment accurately and at length.
2. Acknowledge what is correct and valuable in it.
3. State clearly what the paper's contribution is and why it does not require resolving the reviewer's concern.
4. Point to what we *did* do in response --- added discussion, caveats, limitations, new framing.
5. Close with confidence, not supplication: "We think the revised discussion states our position clearly. The deeper question the reviewer raises is real, but it is not one this paper sets out to resolve --- and we have tried to say so honestly."

## Non-negotiables

- **Never introduce claims the authors did not make.** The response memo should describe what the paper says, not invent new arguments.
- **Never overstate what the revision accomplished.** If we added a paragraph of discussion, do not describe it as "a thorough treatment." Be accurate about the scope of changes.
- **Never be dismissive.** Every comment deserves engagement, even if the engagement is brief.
- **Never promise future work we do not intend to do.** If we say "we plan to explore X in future work," it must be true.
- **Preserve statistical meaning exactly.** Per `CLAUDE.md`: estimands, identification assumptions, hypotheses, error rates, and uncertainty language must survive intact. Do not strengthen claims in the response that the paper does not support.
- **Keep the response blinded.** JASA requires blinded responses. No author names, no self-citations that reveal identity. Use "the authors" or "we" but do not include identifying information.

## Consulting the editor

An underused option: if a reviewer's request seems to change the scope of the paper fundamentally, or if a key comment is too vague to address, you can contact the handling editor before submitting the revision. Nature Computational Science (2025) notes: "If authors feel that some of the requested modifications are out of scope or too difficult, expensive, or laborious, these issues can be discussed with the handling editor." You can also ask the editor to seek clarification from a reviewer on an ambiguous comment. This is not an adversarial move --- it is a sign of taking the process seriously.

## References and sources

The advice in this document draws on the following published guides, in addition to the authors' own experience:

- Noble (2017). "Ten Simple Rules for Writing a Response to Reviewers." *PLOS Computational Biology*.
- Williams & Kerns (2019). "Writing Author Response Letters That Get Editors to 'Yes'." *PMC*.
- "JASA Editors Offer Advice to Authors." *American Statistical Association*.
- JASA Reproducibility Guide. jasa-acs.github.io/repro-guide/
- IMS Guidelines for Associate Editors, *Annals of Statistics*.
- Gelman. "Learning from and Responding to Statistical Criticism."
- Nature Computational Science (2025). Editorial on responding to reviewers.
- Nature Geoscience (2019). Editorial on responding to reviewers.
- Portwood-Stacer, Manuscript Works. "Reader Reports."
- European Urology (2025). Editorial on revision strategies.
