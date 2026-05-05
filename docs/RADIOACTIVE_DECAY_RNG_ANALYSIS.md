# Radioactive-Decay-Inspired RNG: NZ Lotto Powerball Dataset Analysis

## Abstract

This document presents a research-style analysis of 1,869 NZ Lotto Powerball draws (2001-02-17 → 2026-04-22) through the lens of radioactive-decay physics. We ask whether the statistical fingerprint of lottery draws — inter-arrival gap distributions, count-in-window distributions, and independence properties — is consistent with the Poisson emission model that governs radioactive decay. We then introduce a *decay-mimicking generator* that simulates 40 virtual radioactive sources (one per ball) in a closed chamber, selecting the 6 sources whose first emission arrives soonest. The generator is validated against uniform random, the existing Gaussian-weighted picker used in this project, and the historical empirical distribution using chi-square, KL divergence, and two NIST SP 800-22 statistical tests. **No predictive claim is made.** A fair lottery is mechanically i.i.d. by design; finding Poisson statistics confirms fairness, not predictability.

---

## 1. Introduction

Radioactive decay is the canonical example of a *memoryless* stochastic process. A nucleus has no memory of how long it has existed; the probability of decaying in the next instant is the same regardless of its age. This memorylessness — formally the *Markov property* — means that inter-decay waiting times follow an **Exponential distribution**, and the count of decays in a fixed time window follows a **Poisson distribution**.

These same properties are exactly what we expect from a fair discrete-draw lottery: each number has no memory of when it last appeared, the probability of appearing in the next draw is constant, and the count of appearances in any fixed window of draws should follow Poisson statistics. The physical and mathematical frameworks map cleanly onto each other, with draw index playing the role of continuous time.

This parallel motivates two questions:

1. **Empirical:** Does the NZ Lotto Powerball dataset exhibit the statistical signature of Poisson emission? (If yes, it confirms the draw mechanism is fair and i.i.d.)
2. **Generative:** Can we construct a lottery number generator whose architecture directly mirrors the physics of a closed radioactive decay chamber, deriving selection probabilities from historical emission rates?

The analysis is executed in full in the companion Jupyter notebook: `notebooks/analysis/radioactive_decay_rng.ipynb`.

---

## 2. Background & Literature

### 2.1 Foundational Poisson Observation

The canonical connection between radioactive decay and Poisson statistics was established by Rutherford and Geiger in 1910. Counting α-particle emissions from a polonium source over 8-minute intervals, they measured an empirical distribution with λ ≈ 3.87 and showed it matched the Poisson formula with striking precision [1]. This was among the first empirical validations of the Poisson distribution in physics and established the memoryless, rate-constant character of nuclear decay.

### 2.2 Radioactive Decay as a True Random Number Source

Because radioactive decay is governed by quantum mechanics — a process believed to be fundamentally indeterminate, not merely unpredictable — it is one of the few physical phenomena that can supply *true* (rather than pseudorandom) entropy. John Walker's **HotBits** service (1996, still operational) pipes counts from a ⁶⁰Co or ¹³⁷Cs source through a Geiger-Müller tube to an internet-accessible TRNG [2]. The inter-pulse timing provides the entropy: the interval between two successive counts, measured in microseconds, contributes bits that are then Von Neumann-debiased to remove rate drift.

The *closed environment* is critical in hardware implementations: shielding prevents external radiation from contaminating the source, keeping the measured rate λ stable and known. In our algorithm, the "closed chamber" is a mathematical abstraction — all 40 virtual sources share a fixed λ derived from historical data, isolated from external variation.

### 2.3 NIST Standards for Entropy Sources and Statistical Tests

NIST SP 800-90B [3] defines requirements for entropy sources used in cryptographic random bit generators. It specifies how to estimate entropy from a physical source and what statistical tests the source must pass. NIST SP 800-22 (the companion document) provides a suite of 15 statistical tests — including the Frequency (Monobit) and Runs tests we apply here — for evaluating the output bit stream of any RNG against the null hypothesis of uniform, independent binary output.

For our application (lottery ticket generation rather than cryptography), NIST standards serve as a quality benchmark, not a certification requirement.

### 2.4 Review of Quantum and Decay-Based TRNGs

Stipčević and Koç (2014) survey the landscape of true random number generators, classifying physical entropy sources into thermal noise, shot noise, quantum-optical effects, and radioactive decay [4]. They note that decay-based TRNGs achieve high entropy rates (up to ~10 Mbit/s with modern scintillators), are robust against environmental attack, and have a clean theoretical model — making them easier to certify than thermal-noise sources whose entropy estimation is model-dependent.

### 2.5 RANDy: A Discrete Hardware Implementation

Rohe (2003) describes *RANDy*, a PC-card TRNG using an Am-241 source (the same isotope used in smoke detectors) with a silicon PIN photodiode detector [5]. RANDy demonstrates that decay-based TRNGs can be miniaturised, low-cost, and embedded. The architecture — a shielded source, a sensitive detector, a discriminator circuit, and a timestamp register — translates directly into our simulation: source → virtual atom, detector → arrival-time comparator, timestamp → τₙ sample.

---

## 3. Dataset

| Property | Value |
|---|---|
| Source | `frontend/public/results.json` |
| Game | NZ Lotto Powerball |
| Total draws | 1,869 |
| Date range | 2001-02-17 → 2026-04-22 |
| Main numbers | 6 unique values drawn from {1, …, 40} |
| Powerball | 1 value drawn from {1, …, 10} |
| Bonus Ball | Present in source Excel, excluded from JSON |

Under a fair draw mechanism, each main number appears with probability p = 6/40 = 0.15 per draw (expected ~280.4 appearances over 1,869 draws), and each powerball appears with probability 1/10 = 0.1 (expected ~186.9 appearances).

---

## 4. Statistical Characterisation

The full analysis is in `notebooks/analysis/radioactive_decay_rng.ipynb`. Key results are summarised here with cross-references to notebook sections.

### 4.1 Frequency Distribution (Notebook §2)

A chi-square goodness-of-fit test of the 40 observed main-number frequencies against the uniform expected value is computed in notebook §2. The null hypothesis is uniform distribution across all 40 numbers.

- **Main numbers:** χ² and p-value from notebook §2, cell 2. A p-value above 0.05 confirms no statistically significant deviation from uniformity — consistent with a fair draw.
- **Powerball:** Same test for the 10 powerball values, notebook §2, cell 2.
- **Bonferroni correction:** 40 individual per-number tests are reported at α/40 = 0.00125. The notebook reports how many (if any) numbers individually exceed this threshold (notebook §2, cell 2 output).

![Frequency distribution](../notebooks/analysis/freq_distribution.png)
*Figure 1. Observed vs expected (uniform) frequency for main numbers (left) and powerball (right). Dashed red line = expected count under uniformity.*

### 4.2 Inter-Arrival Gaps — The Decay Analogue (Notebook §2.1)

For each number n, we compute the sequence of gaps between its successive appearances. Under a fair i.i.d. lottery, these gaps are **Geometrically distributed** with parameter p = 6/40. For large gaps (gap >> 1) the Geometric is well approximated by the Exponential.

- **Empirical vs theoretical mean:** Geometric mean = 1/p = 40/6 ≈ 6.67 draws. The empirical mean is reported in notebook §2.1.
- **KS test:** A Kolmogorov-Smirnov test against the best-fit Exponential is reported (notebook §2.1, cell 2). A high p-value supports the Exponential gap model.
- **QQ plot** (Figure 2) shows the empirical quantiles vs the theoretical Exponential, indicating how closely the tails conform.

![Gap distribution](../notebooks/analysis/gap_distribution.png)
*Figure 2. Left: histogram of pooled inter-arrival gaps overlaid with fitted and theoretical Exponential. Right: QQ plot against Exponential quantiles.*

The per-number empirical appearance rates λₙ = appearances / N_draws serve as the **decay rates** in the generator (notebook §2.1, cell 3, with Laplace smoothing).

### 4.3 Count-in-Window — Poisson Check (Notebook §2.2)

For non-overlapping windows of W = 50 draws, we count how many times each number appears. Under Poisson emission, this count should follow **Poisson(λ × 50) ≈ Poisson(7.5)**.

- The mean-to-variance ratio of the empirical window counts (notebook §2.2) diagnoses whether the Poisson variance=mean identity holds.
- A chi-square test of the count histogram against Poisson(7.5) is reported (notebook §2.2, cell 2).

![Poisson window](../notebooks/analysis/poisson_window.png)
*Figure 3. Empirical count-in-window histogram vs Poisson(7.5) PMF.*

### 4.4 Independence (Notebook §2.3)

- **Autocorrelation** of the binary indicator series (1 if number n appeared in draw t, else 0) for representative numbers 7, 13, 23, 38 over lags 1–20. Under independence, all autocorrelations should lie within ±1.96/√N (the 95% CI band shown in notebook §2.3, Figure 4).
- **Wald-Wolfowitz runs test** on the same streams. A p-value > 0.05 supports independence (notebook §2.3, cell 2).

![Autocorrelation](../notebooks/analysis/autocorrelation.png)
*Figure 4. Lag-1 to lag-20 autocorrelation for four representative indicator streams. Dashed lines = 95% confidence interval under independence.*

---

## 5. Decay-Mimicking Generator

### 5.1 Physical Model

We model a shielded closed chamber containing 40 virtual radioactive sources, one for each ball numbered 1–40. Source n has empirical decay rate:

$$\lambda_n = \frac{\text{appearances}_n + 1}{N_\text{draws} \times 6 + 40}$$

(Laplace smoothing ensures λₙ > 0 for all n, keeping every number reachable.)

The waiting time until source n's first emission is drawn from:

$$\tau_n \sim \text{Exponential}(\lambda_n)$$

### 5.2 Selection Rule

For each ticket, independently sample τₙ for all 40 sources. The 6 sources with the smallest τ — those whose particles arrive at the detector first — are the chosen numbers:

$$\text{ticket} = \text{argsort}(\tau)[{:}6] + 1$$

A separate 10-source chamber (powerball values 1–10) supplies the powerball via the same rule, choosing the single source with minimum τ.

### 5.3 Pseudocode

```
function decay_draw(λ_main[40], λ_pb[10]):
    for n in 1..40:
        τ_main[n] ← sample Exponential(rate=λ_main[n])
    numbers ← indices of 6 smallest τ_main, 1-indexed, sorted

    for n in 1..10:
        τ_pb[n] ← sample Exponential(rate=λ_pb[n])
    powerball ← index of smallest τ_pb, 1-indexed

    return numbers, powerball
```

Python implementation: `notebooks/analysis/radioactive_decay_rng.ipynb`, §3.

### 5.4 Mathematical Equivalence Note

Selecting the 6 sources with the smallest independent Exponential waiting times is **mathematically equivalent to weighted sampling without replacement** with weights proportional to λₙ. This can be proven via the competing-exponentials identity: given n independent Exp(λᵢ) random variables, the probability that source i fires first is λᵢ / Σλⱼ. The decay framing is a physical metaphor — apt and accurate — but it does not add algorithmic novelty beyond the frequency weighting it encodes. We disclose this explicitly so the simulation framing is transparent.

---

## 6. Validation Results

Ten thousand tickets were generated from each of three generators and compared to the historical empirical distribution. Full numeric outputs are in notebook §4.

| Generator | χ² (vs uniform) | p-value | KL vs Historical | KL vs Uniform | Monobit p | Runs p |
|---|---|---|---|---|---|---|
| Decay | *see notebook §4* | | | | | |
| Uniform | *see notebook §4* | | | | | |
| Gaussian-weighted | *see notebook §4* | | | | | |

**Interpretation guide:**
- χ² p-value > 0.05 → generator output is not distinguishably non-uniform at this sample size.
- KL vs Historical < 0.01 → generator closely mirrors the historical frequency distribution.
- KL vs Uniform measures how much each generator deviates from a flat distribution.
- NIST monobit and runs p-values > 0.01 → pass at α = 0.01.

![Validation frequency](../notebooks/analysis/validation_frequency.png)
*Figure 5. Per-number frequency for each generator vs historical empirical. Dashed red line = uniform expected.*

---

## 7. Discussion

**On the fairness of NZ Lotto.** The chi-square, KS, and Poisson tests (§4) collectively assess whether the empirical draw data is consistent with a fair, i.i.d. mechanism. If all tests pass, this is strong evidence — though not proof — that the physical draw machine operates as advertised. It also means that no frequency-weighted generator can outperform uniform on expected return.

**On the decay generator's value.** The generator's output distribution mirrors historical frequencies: numbers that have appeared more often will continue to be emitted slightly more often. This is useful for users who want to play "historically hot" numbers, and it is implemented in a principled, physically motivated way. However, because the underlying lottery is fair, the historical skew is almost certainly a finite-sample fluctuation around uniform rather than a systematic bias.

**On the Gaussian-weighted generator.** The existing `frontend/src/utils.ts` generator adds a spatial leaning bias (left/middle/right zones of 1–40) via Gaussian proximity weighting. This is purely aesthetic — it modifies which region of the number space is favoured, not the overall frequency-weighted selection logic. The KL comparison in §6 shows how much each generator deviates from historical empirical vs from uniform.

---

## 8. Limitations & Non-Claims

1. **This analysis does not predict winning lottery numbers.** Lottery draws are mechanically random and statistically independent. Past frequencies have zero causal influence on future draws.

2. **Historical frequency weights reflect noise, not signal.** Over 1,869 draws, the binomial variance around the expected count of 280 appearances is ≈ sqrt(1869 × 0.15 × 0.85) ≈ 15.4 draws. Observed frequency differences between numbers are largely within this noise band.

3. **Only 2 of 15 NIST SP 800-22 tests are run.** Results are phrased as "passes monobit and runs at α = 0.01," not "NIST-certified."

4. **The decay simulation uses a pseudorandom number generator** (NumPy's PCG64, seeded at 42) for τ sampling. In a hardware TRNG, this sampling would be replaced by physical decay timing. The algorithm's structure is faithful to the physics; its entropy source in software is not.

5. **Laplace smoothing** slightly biases λₙ toward uniform for all numbers. This is conservative by design — it prevents any number from being permanently excluded.

---

## 9. References

[1] E. Rutherford and H. Geiger (1910). *The Probability Variations in the Distribution of α Particles*. Philosophical Magazine, Series 6, Vol. 20, No. 118, pp. 698–707. https://doi.org/10.1080/14786441008636955

[2] J. Walker (1996). *HotBits: Genuine Random Numbers, Generated by Radioactive Decay*. Fourmilab Switzerland. https://www.fourmilab.ch/hotbits/

[3] M. S. Turan, E. Barker, J. Kelsey, K. McKay, M. Baish, and M. Boyle (2018). *NIST SP 800-90B: Recommendation for the Entropy Sources Used for Random Bit Generation*. National Institute of Standards and Technology. https://doi.org/10.6028/NIST.SP.800-90B

[4] M. Stipčević and Ç. K. Koç (2014). *True Random Number Generators*. In: Ç. K. Koç (Ed.), Open Problems in Mathematics and Computational Science, Springer, pp. 275–315. https://cetinkayakoc.net/docs/b08.pdf

[5] M. Rohe (2003). *RANDy — A True-Random Generator Based On Radioactive Decay*. Semantic Scholar. https://www.semanticscholar.org/paper/RANDy-A-True-Random-Generator-Based-On-Radioactive-Rohe/95d5042fc5963d387563247166b7f904fb1153c8
