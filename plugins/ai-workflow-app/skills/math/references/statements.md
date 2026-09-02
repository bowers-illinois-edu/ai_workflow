# Math skill reference --- sections 4--7: statements, assumptions, vocabulary, proof status

Part of the `math` skill; read `SKILL.md` first. Section numbers continue the skill's single sequence.

## 4. Motivate before formalism

Every substantial mathematical section should open with a motivating sentence or paragraph.

Preferred order:

1. problem,
2. scenario,
3. stakes,
4. main difficulty,
5. notation,
6. formal statement,
7. proof,
8. remark on scope.

Notation is expensive. The reader should know what they are buying before paying the notation tax.

A good opening does some combination of:

- states the substantive question,
- previews the answer in words,
- names the hard part,
- tells the reader how the section proceeds.

Rule: if you strip all notation from the section, the remaining prose should still tell a coherent story.

### 4.1 Concrete example before general theorem

Before stating a general theorem, give the simplest nontrivial case that shows the mechanism.

The toy case should:

- be small enough to work by hand,
- not be so trivial the mechanism disappears,
- match the general statement when specialized back,
- reveal what the assumptions are buying.

This is not ornament. It is both pedagogy and a correctness check. A common bug is a general theorem whose assumptions exclude the toy case it was meant to cover.

---

## 5. Assumption discipline

Assumptions are part of the mathematical content, not backstage machinery.

### 5.1 Every assumption gets stated

Do not write "under regularity conditions" or "by standard assumptions" unless you immediately enumerate them. The skipped conditions are almost always the ones that matter.

State explicitly:

- moment conditions,
- smoothness,
- compactness or coercivity,
- measurability,
- domination,
- overlap or positivity,
- identifiability,
- tail behavior,
- dependence structure,
- asymptotic regime.

### 5.2 Classify assumptions by role

Separate into categories:

- design (randomization, ignorability, SUTVA),
- model (parametric form, error distribution),
- identification,
- regularity (differentiability, finite variance, dominating function for DCT),
- technical measurability or integrability,
- asymptotic regime.

A reader should see at a glance what is substantive and what is technical.

### 5.3 Load-bearing vs cosmetic

For each important assumption, say whether it is:

- **load-bearing**: the claim fails without it. State whether the conclusion breaks or only the proof technique fails. Give a counterexample or failure mode when possible.
- **cosmetic**: convenience; a weaker variant would suffice. Point to where the weaker version lives or note you have not verified it.
- **unknown**: you do not know which; say so.

For each load-bearing assumption, answer near the theorem:

1. What does it mean substantively?
2. When is it plausible?
3. What breaks when it fails --- quantitatively (rate worsens) or qualitatively (inconsistency, blowup)?

### 5.4 Do not silently strengthen assumptions

A common LLM failure: the user asks about one theorem and the assistant quietly proves a different, easier theorem under stronger assumptions.

If you use stronger conditions than the user asked about, state:

- what stronger condition you imposed,
- where it enters,
- whether it seems essential or only convenient.

### 5.5 Necessary vs sufficient

A sufficient condition guarantees the conclusion; a necessary condition is implied by the conclusion. Not symmetric. Flag: "Sufficient. We do not know whether it is necessary." Or: "Necessary and sufficient (see [Reference, Theorem N])." When in doubt, claim sufficiency only.

---

## 6. Theorem statements and mathematical vocabulary

State theorems as conditional statements: if assumptions, then conclusion. Do not bury hypotheses in prose.

### 6.1 Convergence, rate, uniformity

"Converges" is not a complete statement. Specify:

- **mode**: almost sure, in probability, in distribution, in `L^p`, uniformly on compacta, uniformly over a function class,
- **rate**: `O_p(n^(-1/2))`, `o_p(1)`, exponential in `n`,
- **what is fixed, what moves**,
- **pointwise vs uniform**.

Pointwise is strictly weaker than uniform. Pointwise plus stochastic equicontinuity gives uniform --- say you are using this, not "by uniformity."

### 6.2 Exact, approximate, asymptotic

- Use `=` only for exact equality.
- Use `approximately` or `\approx` for finite-sample numerical approximation.
- Use `~` only for asymptotic equivalence.
- Use `O`, `o`, `O_p`, `o_p` with care. `O` and `o` are not interchangeable.

Never slide from exact to approximate to asymptotic inside a chain of equations without flagging the transition.

### 6.3 Verbs calibrated to evidence

- **Prove**: full, rigorous proof. Use sparingly.
- **Show / establish**: derivation with no substantive gap but possibly lighter than a full formal proof.
- **Derive**: calculation under stated assumptions.
- **Argue heuristically**: informal reasoning, not a proof.
- **Suggest / is consistent with**: simulation or empirical evidence.
- **Support**: makes a claim more plausible; weaker than establish.
- **Conjecture**: believed true but not proved; mark explicitly.
- **Demonstrate**: vague. Avoid.

Probability vocabulary: "with probability tending to one" vs "with high probability" (usually exponentially close) vs "almost surely" --- these differ.

### 6.4 Estimand, estimator, estimate

Keep these separate:

- **Estimand**: target quantity. A functional of the distribution of observables (under identification) or of potential outcomes and the assignment mechanism. No data in it.
- **Estimator**: random variable built from data.
- **Estimate**: realized value of the estimator. A number.

Never write "the estimand is unbiased" (estimands are not unbiased; estimators are). Never write "the estimator is 0.27" (that is the estimate).

### 6.5 Identification before estimation

Identification asks whether the estimand is a functional of observables under the stated assumptions. Estimation asks whether a data-based procedure recovers it. If identification fails, no amount of data helps; asymptotics do not rescue the problem.

Identification assumptions (ignorability, positivity, SUTVA, exclusion restrictions, overlap) belong with the estimand, not the estimator.

### 6.6 Finite-sample vs asymptotic claims

Finite-sample properties (unbiasedness, exact level, exact coverage) are distinct from asymptotic properties (consistency, asymptotic normality, efficiency). Randomization inference often provides finite-sample guarantees that asymptotic theory cannot. Do not accidentally replace a finite-sample claim with an asymptotic one.

Do not compute finite-sample quantities (exact p-values) from asymptotic expressions without flagging the approximation.

---

## 7. Proof status and uncertainty

Never let the reader finish a section unsure whether they saw a proof, a sketch, a heuristic, or a simulation.

### 7.1 Explicit status labels

Allowed labels:

- `Proof`
- `Proof sketch`
- `Formal derivation`
- `Heuristic`
- `Simulation evidence`
- `Counterexample`
- `Conjecture`

Use the label that matches what you actually have. Commit to the level you provide.

### 7.2 Internal confidence, visible flags

Internally, track each step as checked and supported, plausible but subtle, or guessing/pattern-matching. Do not name those tiers in the user-visible output --- flag uncertainty in plain English:

- "This appears to follow from ..., but the domination condition still needs checking."
- "I think the claim holds under finite fourth moments; I have not verified whether finite variance alone suffices."
- "I do not currently have a proof of this step."

Unacceptable behavior:

- smoothing over a subtle step with polished prose,
- writing a guess as if it were standard,
- mentioning a gap only in an offhand parenthetical.

If a step is load-bearing and your confidence is not high, say so in the visible text. A referee will not discover your hedging; they will read the sentence as a claim.

### 7.3 Heuristic vs rigorous

Heuristic reasoning is legitimate --- saddlepoint derivations, large-deviation arguments, and related intuitions often start heuristically and are made rigorous later. Illegitimate: presenting a heuristic as a proof.

When a heuristic produces a formula later verified: "The heuristic of Section 3.1 yields formula (4); Theorem 2 in Section 3.3 confirms this under (A1)--(A3)."

When a derivation stays heuristic, say so and why: "A rigorous justification would require verifying [specific regularity] beyond this paper's scope."

---

