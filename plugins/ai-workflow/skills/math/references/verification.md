# Math skill reference --- sections 12--13: verification passes and citations

Part of the `math` skill; read `SKILL.md` first. Section numbers continue the skill's single sequence.

## 12. Verification passes

Before presenting a nontrivial result, run the applicable checks and report which were run. Do not silently skip a check because it would be inconvenient.

### 12.1 Structural checks

- **Dimension and units**: both sides of every equation agree in dimension. Variance has units of (outcome)^2; SE has units of (outcome); test statistics are dimensionless; densities integrate to 1. For matrices, note dimensions over each factor.
- **Sign and monotonicity**: variances, information, KL divergences, squared quantities are nonneg. Power nondecreasing in effect size.
- **Invariance and equivariance**: if the problem has a natural symmetry (translation, scale, permutation, sign-flipping), does the formula respect it?
- **Arithmetic plug-in**: for closed forms, plug in simple values (`n = 1`, `n = 2`, `mu = 0`, `sigma = 1`) and check by hand or in R. Factors of 2, 1/2, square roots, logs, factorials are where errors hide.

### 12.2 Limiting and special-case checks

- **Limiting cases**: let parameters go to boundaries. Does the answer recover a known closed form? As `n -> inf`, does variance go to zero at the right rate?
- **Degenerate cases**: zero variance, sample size 1, single cluster or stratum, boundary of parameter space, identically-zero outcome, constant treatment. Do the formulas handle these, or produce 0/0, log(0), 1/0? If they break, say so.
- **Known special cases**: specialize the general formula to a case with a classical answer (Gaussian with known variance, one-sample t-test, two-arm complete randomization, independence model). Does the general formula recover it?

### 12.3 Mathematical consistency checks

- Hypothesis-by-hypothesis check for each theorem used.
- Alternative derivation if available.
- Reread once only for quantifiers.
- Reread once only for conditioning and measure.
- Verify every exchange of limit, expectation, integral, derivative, or supremum.
- Check that a result stated pointwise in one place is not quietly reported as uniform elsewhere.
- Check that abstract, introduction, theorem statement, and proof agree exactly --- watch for version drift.

### 12.4 Reporting rule

Do not say "checked." Say what was checked.

Good:

- "I verified the Lyapunov condition using the bounded fourth-moment assumption."
- "I checked the Gaussian special case and recovered the known variance."
- "I did not verify the empirical-process step; that part remains conditional."

Bad:

- "Standard checks pass."

---

## 13. Citations

Do not fabricate citations, theorem numbers, page numbers, or remembered results.

### 13.1 Cite specific results specifically

Prefer "Theorem 3.2 of van der Vaart (1998, p. 47)" over "van der Vaart (1998)" when invoking a particular theorem.

### 13.2 Do not paraphrase a citation into a stronger statement

If a cited theorem gives `X` and you need `X'`:

- prove `X'` from `X`, showing the steps,
- find a citation that actually states `X'`,
- or mark the gap honestly.

The failure mode is subtle: "Theorem 2 in [R] shows..." followed by a generalization rather than Theorem 2 itself. Referees catch this and trust is damaged.

### 13.3 Honest uncertainty from memory

If you do not have the reference in hand: "From memory --- please check: ..." That is better than fake precision.

Folklore results: "This appears to be folklore; the closest references we have are [X] and [Y], which prove weaker or different versions."

### 13.4 Prefer canonical sources

Trace results back to standard references (van der Vaart, Lehmann--Romano, Durrett, Billingsley, Dembo--Zeitouni) or original sources, especially for named theorems and delicate conditions.

---

