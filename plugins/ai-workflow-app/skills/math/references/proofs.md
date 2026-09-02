# Math skill reference --- sections 8--11: theorem use, proof construction, failure modes, counterexamples and simulation

Part of the `math` skill; read `SKILL.md` first. Section numbers continue the skill's single sequence.

## 8. Theorem-use protocol

The single most common LLM failure in mathematical statistics is invoking the right-sounding theorem under the wrong hypotheses. Do not cite a theorem by vibe.

### 8.1 Build a theorem ledger before invoking a result

For any named theorem, lemma, asymptotic device, or exchange-of-limits step, write down:

1. the exact theorem (or a precise paraphrase),
2. the hypotheses, one by one,
3. where each hypothesis is verified in the current setting,
4. the exact conclusion you are using,
5. any notation translation or adaptation.

If you cannot do this, you do not yet know enough to invoke the theorem safely.

### 8.2 Name the actual theorem

Do not write "by the CLT," "by the LLN," "by the delta method," "by standard empirical process theory," "by dominated convergence," "by symmetry," or "WLOG" unless you can say exactly which result or symmetry is being used and why it applies.

There are many CLTs (Lindeberg, Lyapunov, martingale, triangular-array, Lindeberg--Feller). Same for LLN, DCT, MCT, Fubini, Slutsky, continuous mapping, delta method, Cramer--Wold, Portmanteau, Glivenko--Cantelli, Donsker, uniform LLN, Bernstein/Hoeffding/Azuma, Lehmann--Scheffe, Rao--Blackwell, Cramer--Rao, Neyman--Pearson, Le Cam's lemmas, Hajek's projection, functional delta method, any inequality named after someone. Use the right one and check its hypotheses.

### 8.3 Common theorem mismatches

Check aggressively for:

- i.i.d. theorem applied to dependent data (needs mixing, martingale-difference, or m-dependence);
- fixed-dimension theorem applied in high dimension;
- interior-point theorem applied on the boundary;
- differentiability-based theorem used at a kink;
- finite-variance theorem used with heavy tails;
- unconditional result used after conditioning;
- weak-convergence result used as if it delivered moments;
- exact-optimizer theorem used when only an approximate optimizer exists;
- pointwise theorem reported as uniform;
- absolutely continuous argument applied in a discrete or mixed setting;
- delta method where the first derivative vanishes (need second-order delta or direct argument);
- Slutsky used without one sequence going to a constant in probability.

### 8.4 If the theorem is close but not exact

Do one of three things:

- prove the missing bridge as a lemma,
- weaken the claim to match the theorem,
- mark the result as conditional on the gap.

Do not smuggle the missing step past the reader.

### 8.5 Exchanges of limits and operators

Whenever you exchange limit and expectation, limit and integral, sum and expectation, derivative and integral, or supremum and limit, name the licensing theorem and verify its condition.

Check explicitly for:

- domination (DCT),
- monotonicity (MCT),
- absolute integrability (Fubini--Tonelli),
- uniform integrability,
- measurability of the supremum,
- domination of the derivative (Leibniz rule).

---

## 9. Proof construction

A good proof makes its skeleton visible.

### 9.1 Roadmap first

For any substantial proof, begin with a short overview: "We prove this in three steps: reduction, approximation, and remainder control." This forces you to know the structure before writing algebra.

### 9.2 Keep logical layers separate

Do not bury assumptions inside calculations or the key idea inside notation. Keep distinct: setup, assumptions, claim, proof overview, proof details, scope remarks, unresolved gaps.

### 9.3 Proof-obligation ledger

As you reason, keep a running list of unresolved obligations:

- show measurability,
- verify uniformity,
- justify a limit-expectation interchange,
- control a boundary term,
- show existence and uniqueness,
- establish a remainder bound.

Do not delete an obligation because the prose moved on.

### 9.4 Every nontrivial step gets a reason

For each important line, know whether it follows from:

- algebra,
- a definition,
- a stated assumption,
- a proved lemma,
- a cited theorem whose hypotheses were checked.

If the reason is "standard," the step probably still needs work.

### 9.5 Local lemmas for hard substeps

If a proof depends on a delicate bound, approximation, existence claim, or regularity verification, isolate that step as a lemma rather than hiding it in prose.

### 9.6 Quantifier order matters

Watch for:

- pointwise in `theta` vs uniform over `Theta`,
- "for each `epsilon` there exists `N`" vs "there exists `N` for all `epsilon`",
- fixed alternative vs local alternative,
- existence of an optimizer for each sample vs a measurable selection uniformly in the sample.

Write the quantifiers you mean.

### 9.7 Do not hide the hard step

Treat these as warning lights: "clearly," "obviously," "routine," "standard," "it follows," "one can show," "easy to see."

Rule: if writing out the omitted step would be hard, it is not routine. Either write it or flag it as a gap.

### 9.8 End the proof cleanly

Close by saying exactly which earlier steps imply the claim. Do not stop with a cloud of algebra and assume the reader can infer the final implication.

---

## 10. General failure modes

### 10.1 Sign, index, off-by-one

- Check signs on a simple case. KL divergence is nonnegative. Fisher information is PSD. Variances are nonnegative.
- For sums and products, write out the first two terms and the last. `sum_{i=1}^n`, `sum_{i=0}^{n-1}`, `sum_{i=1}^{n-1}` are different sums.
- When changing summation variables, rewrite bounds carefully.
- For matrix derivations, check dimensions at every step.

### 10.2 Notation collisions

Before using hat, tilde, bar, star, subscript, or prime: is the symbol already in use? Pick a different decoration. Do not use the same letter for an index and a parameter in the same scope.

### 10.3 Convergence types

Almost sure implies in probability implies in distribution; reverses fail. `L^p` implies in probability, but almost sure and `L^p` neither implies the other. Pointwise convergence of random functions does not imply uniform. Slutsky requires one sequence in distribution and another in probability to a constant --- check this is what you have.

### 10.4 Random vs fixed, finite-sample vs asymptotic

`P(X = x)` treats `X` as random, `x` as fixed. Estimators are random; estimates are realizations. In design-based analysis, potential outcomes are fixed and assignment is random --- mixing these produces wrong variances.

A sentence that mixes a finite-sample property (unbiasedness) with an asymptotic one (asymptotic normality) is fine if both hold --- state them as two claims with their own justifications.

### 10.5 "WLOG" and "by symmetry"

"Without loss of generality" requires a symmetry or reduction. State it: "WLOG assume `mu = 0` by translation invariance." "By symmetry" requires naming the symmetry (exchangeability, sign-flipping, rotational). If it is not literally present, do not invoke it.

### 10.6 Unstated regularity

Convexity, continuity, differentiability, measurability, integrability, compactness, identifiability: never assume implicitly. For optimization arguments, state whether the objective is convex, strictly convex, continuous, coercive --- existence and uniqueness of optimizers depend on these.

### 10.7 Danger zones worth special care

- **Likelihood and score**: whether the support depends on the parameter; whether differentiation under the integral is justified; whether the score has mean zero under the correct measure; whether boundary points are handled separately.
- **Delta method and Taylor expansion**: differentiability at the relevant point; whether the first derivative vanishes; remainder control; uniformity.
- **M-estimation and argmax**: identification of the population criterion; uniform law of large numbers; stochastic equicontinuity; existence, uniqueness, and measurability of the optimizer.
- **Empirical processes**: never invoke as a black box. Name the function class, envelope, entropy or VC control, and which maximal inequality or symmetrization step.
- **CLT-type arguments**: independence vs dependence; triangular arrays; Lindeberg or Lyapunov conditions; martingale structure; cluster dependence; heteroskedasticity.
- **Randomization and causal inference**: keep distinct the estimand, identification, assignment mechanism, finite-population vs superpopulation target, exact randomization distribution, and asymptotic approximation.

Specialized subfields (saddlepoint approximations, Edgeworth expansions, large-deviation bounds, importance sampling, tilting, high-dimensional asymptotics, functional data, causal machine learning, etc.) often have their own load-bearing conditions that are easy to miss. If the project enters one of these, see section 16 on project-specific supplements.

---

## 11. Counterexamples and simulation

Counterexamples and simulations are diagnostic tools, not theater.

### 11.1 Counterexamples

If a claim looks false, try to break it quickly. Prefer the smallest decisive case: scalar before vector, finite before infinite-dimensional, two-point distribution before a large family, one stratum before many.

A claimed counterexample is not complete until you verify both:

- the assumptions it is meant to satisfy,
- the conclusion it is meant to violate.

Compute explicitly. Never claim a counterexample without checking it.

### 11.2 Simulation

Simulation is worth doing when it can test a claimed null distribution, reveal a wrong sign or wrong constant, distinguish a plausible rate from an implausible one, stress-test boundary cases, or produce evidence for or against a conjecture.

Simulation can falsify, calibrate, and prioritize. It does not prove a theorem.

Report simulation honestly: what was simulated, what was fixed, what varied, which theorem conditions the design represents, what the simulation supports, what it does not establish.

"This simulation checks plausibility and can reveal failure, but it does not prove the theorem."

When simulation is easy and the stakes are nontrivial, run it before presenting.

---

