# Secondary analyses (protocol §6) and H3

Generated 2026-11-02 by `scripts/21_secondary.py`. Primary specification: `[dp]`, coverage-weighted, D. 999 bootstrap replicates. Outputs are in `data/processed/secondary/`.

## 1. Breakpoints (cohorts 2008–2020)

| Frame | Series | Break (95% CI) | Growth before | Growth after | Two-break test p |
|---|---|---|---|---|---|
| F1 | P1 | 2018 (2017–2018) | -1.0%/yr | 17.0%/yr | 0.173 |
| F1 | 5-yr cumulative incidence | 2018 (2018–2018) | -5.2%/yr | 8.4%/yr | 0.066 |
| F2 | P1 | 2018 (2010–2018) | 2.1%/yr | 9.8%/yr | 0.056 |
| F2 | 5-yr cumulative incidence | 2018 (2010–2018) | -2.3%/yr | 1.7%/yr | 0.237 |
| F2 cleaned | P1 | 2018 (2010–2018) | 2.4%/yr | 8.2%/yr | 0.039 |
| F2 cleaned | 5-yr cumulative incidence | 2018 (2010–2018) | -1.9%/yr | 0.2%/yr | 0.086 |

**Caution.** With cohorts 2008–2020, the latest break the grid allows is 2018, and every estimate sits there. The upturn is driven by the 2019–2020 cohorts, especially the 2020 COVID surge. The pre-specified COVID-excluded sensitivity analysis is needed before reading this as a real change.

## 2. Decomposition of P1 (annual log-growth, %/yr, cohorts 2008–2020)

P1 = guidelines (coverage-adjusted, years Y..Y+5) × references per guideline × share of references to cohort Y × first citations per reference. The four factors sum to P1's growth.

| Frame | Guidelines | Refs/guideline | Share to cohort | Uniqueness | **P1** | D |
|---|---|---|---|---|---|---|
| F1 | +0.91 | -0.20 | -1.14 | +1.00 | **+0.56** | +4.67 |
| F2 | +3.78 | -1.08 | -0.30 | +0.31 | **+2.71** | +4.67 |
| F2 cleaned | +3.27 | -0.54 | -0.30 | +0.50 | **+2.92** | +4.67 |

Guideline capacity (number of guidelines × references per guideline) grows far more slowly than D: +0.7%/yr in F1 and +2.7%/yr in F2, against +4.7%/yr for D. The share of references going to any one recent cohort is flat or falling. The gap between P1 and D is therefore accounted for by limited guideline capacity rather than by guidelines turning away from recent research (RQ4).

## 3. Selected designs compared with the rest

Model: logit h = f(a) + β·c + γ·g + δ₁·g·c + δ₂·g·max(0, Y − 2018). Bootstrap replicates with no post-2018 cohorts leave the δ₂ term undefined and are excluded (shown in the last column).

| Frame | γ (log OR, 2008) | δ₁ (per yr, before 2018) | δ₁+δ₂ (per yr, from 2018) | Undefined replicates |
|---|---|---|---|---|
| F1 | 1.020 (0.068 to 1.160) | -0.129 (-0.168 to -0.018) | -0.054 (-0.109 to 0.144) | 46 |
| F2 | 1.528 (1.346 to 1.676) | -0.108 (-0.135 to -0.077) | -0.134 (-0.178 to 0.100) | 46 |
| F2 cleaned | 1.232 (0.778 to 1.412) | -0.101 (-0.142 to -0.052) | -0.116 (-0.163 to 0.043) | 45 |

Equal-follow-up ratios (cumulative incidence, selected ÷ rest; mean over cohorts):

| Frame | 3-yr ratio, 2008–2017 | 3-yr ratio, 2018–2022 | 5-yr ratio, 2008–2017 | 5-yr ratio, 2018–2020 |
|---|---|---|---|---|
| F1 | 1.79 | 0.95 | 1.76 | 1.05 |
| F2 | 3.68 | 1.55 | 3.27 | 1.80 |
| F2 cleaned | 1.97 | 1.39 | 2.15 | 1.48 |

**Reading (RQ5).** Selected-design papers were cited more often than other research in early cohorts. That advantage shrank by about 10% a year and was roughly gone by the post-2018 surge. Because G4 shows that these citations are mostly background (22% evidence, against 52% for other papers), this is not evidence that the designs inform recommendations.

Descriptive breakdown by design and era (F1, not tested): `design_breakdown.csv`.

## 4. H3: an additional change after 2022

- **(a) Selected-design share of D, 2008–2025:** estimated break 2019 (CI 2018–2019). Growth is 15%/yr before and 43%/yr after. Added 2022 hinge: **p = 0.067**, so no supported change.
- **(b) P2 hinge at 2022 (θ), with τ̂ = 2018:**

  - F1: θ = 0.080 (0.055 to 0.181); 424 of 999 replicates undefined
  - F2: θ = 0.068 (0.047 to 0.148); 424 of 999 replicates undefined
  - F2 cleaned: θ = 0.082 (0.071 to 0.156); 424 of 999 replicates undefined

**The formal criterion is met through (b), but the result is not credible.**
- 42% of bootstrap replicates had no 2023–2024 cohorts, so the interval is conditional and fragile.
- These cohorts have only 1–2 years of follow-up, all of it in 2023–2025. That period is when F1 guideline indexing recovered from its 2022–23 dip, which raises early-age hazards regardless of cohort. A calendar-year artefact is the likely explanation.
- (a) shows no 2022 change.
- **H3 should be reported as formally met on (b) but not robust, and as not supported on (a)**, with this explanation. The protocol had stated in advance that (b) would have little power.

## 5. Early signal (descriptive)

One- and two-year cumulative incidence for cohorts 2015–2024 is in `*_early_signal.csv`. In F1, 2-year incidence falls from 0.52% (2015) to 0.31% (2022), then rises to 0.57% (2024). The rise matches the F1 indexing recovery noted above.
