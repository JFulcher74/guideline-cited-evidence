# Primary results (P1, P2, H1, H2)

Generated 2026-11-02 by `scripts/19_primary.py` (999 moving-block bootstrap replicates, block length 3). The primary specification is publication date `[dp]`, coverage-weighted, denominator D. All cohorts are de-duplicated to the earliest `[dp]` year. Point estimates and 95% bootstrap CIs are shown.

## Primary specification

| Frame | Guidelines (with refs) | β, P2 cohort trend (log-odds/yr) | OR per year | P1 growth g₁ (%/yr) | D growth g_D (%/yr) | g₁ − g_D (%/yr) | H1 | H2 | Decision cell |
|---|---|---|---|---|---|---|---|---|---|
| F1 | 23,920 (19,483) | -0.0189 (-0.0301 to 0.0216) | 0.981 | 0.56 (-1.45 to 1.46) | 4.67 | -4.11 (-5.82 to -2.80) | not supported | supported | Not diluted (unexpected; investigate the decomposition) |
| F2 | 7,943 (7,007) | -0.0173 (-0.0216 to -0.0066) | 0.983 | 2.71 (0.44 to 4.02) | 4.67 | -1.96 (-2.92 to -1.56) | supported | supported | Diluted, with a growing absolute yield |
| F2 cleaned | 5,411 (4,811) | -0.0131 (-0.0170 to -0.0028) | 0.987 | 2.92 (1.00 to 4.17) | 4.67 | -1.75 (-2.60 to -1.29) | supported | supported | Diluted, with a growing absolute yield |

F2 cleaned is the added sensitivity analysis (a deviation; protocol §3.1). D doubles every 14.8 years.

Proportional-hazards check (age × cohort interaction on β): F1 +0.0047 (ages 2–4), +0.0487 (ages 5+); F2 -0.0087, -0.0090. F1 departs from proportionality at older ages.

## Sensitivity analyses run so far

| Specification | Frame | β (95% CI) | g₁ − g_D, %/yr (95% CI) | H1 | H2 |
|---|---|---|---|---|---|
| Unweighted | F1 | -0.0113 (-0.0224 to 0.0297) | -3.43 (-4.74 to -2.36) | NS | S |
| Unweighted | F2 | -0.0124 (-0.0182 to 0.0024) | -1.67 (-3.24 to -1.03) | NS | S |
| Unweighted | F2 cleaned | -0.0075 (-0.0122 to 0.0080) | -1.43 (-2.81 to -0.74) | NS | S |
| Entry date [edat] | F1 | -0.0144 (-0.0250 to 0.0230) | -3.62 (-5.17 to -2.80) | NS | S |
| Entry date [edat] | F2 | -0.0129 (-0.0187 to -0.0063) | -1.35 (-2.94 to -0.34) | S | S |
| Entry date [edat] | F2 cleaned | -0.0086 (-0.0148 to -0.0016) | -1.20 (-2.61 to -0.17) | S | S |
| D-Humans | F1 | -0.0168 (-0.0275 to 0.0221) | -3.73 (-5.40 to -2.43) | NS | S |
| D-Humans | F2 | -0.0120 (-0.0158 to -0.0033) | -1.40 (-2.22 to -0.96) | S | S |
| D-Humans | F2 cleaned | -0.0073 (-0.0111 to 0.0021) | -1.15 (-1.80 to -0.70) | NS | S |
| D-all | F1 | -0.0190 (-0.0305 to 0.0225) | -4.05 (-5.73 to -2.63) | NS | S |
| D-all | F2 | -0.0174 (-0.0217 to -0.0068) | -1.90 (-2.94 to -1.53) | S | S |
| D-all | F2 cleaned | -0.0133 (-0.0174 to -0.0033) | -1.70 (-2.60 to -1.23) | S | S |

S = supported (95% CI excludes 0 in the hypothesised direction); NS = not supported.

Still to run: secondary analyses 1–5 (breakpoints, decomposition, selected designs, H3, early signal) and the remaining sensitivity analyses (3-year headline age, excluding COVID cohorts, D-journals, F3 trend agreement, the F1-versus-F2 2022–23 comparison).
