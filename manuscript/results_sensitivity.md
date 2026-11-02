# Sensitivity analyses (protocol §6)

Generated 2026-11-02 by `scripts/22_sensitivity.py` (999 bootstrap replicates; otherwise the primary specification). Unweighted, `[edat]`, D-Humans and D-all are in `results_primary.md`. Outputs are in `data/processed/sensitivity/`.

| Specification | Frame | β (95% CI) | g₁ − g_D, %/yr (95% CI) | H1 | H2 | Decision cell |
|---|---|---|---|---|---|---|
| Headline age 3 years | F1 | -0.0189 (-0.0301 to 0.0216) | -4.28 (-5.78 to -3.01) | NS | S | Not diluted (unexpected; investigate the decomposition) |
| Excluding 2020–21 cohorts | F1 | -0.0210 (-0.0367 to 0.0138) | -4.91 (-5.87 to -4.04) | NS | S | Not diluted (unexpected; investigate the decomposition) |
| D-journals denominator | F1 | -0.0101 (-0.0191 to 0.0268) | -2.97 (-4.38 to -1.93) | NS | S | Not diluted (unexpected; investigate the decomposition) |
| Stable-coverage journals | F1 | -0.0184 (-0.0283 to 0.0189) | -3.83 (-5.16 to -2.87) | NS | S | Not diluted (unexpected; investigate the decomposition) |
| Follow-up censored at 2021 (exploratory) | F1 | -0.0538 (-0.0625 to -0.0469) | -5.48 (-7.47 to -3.99) | S | S | Diluted, with a stagnant or shrinking yield |
| Headline age 3 years | F2 | -0.0173 (-0.0216 to -0.0066) | -1.72 (-2.73 to -0.64) | S | S | Diluted, with a growing absolute yield |
| Excluding 2020–21 cohorts | F2 | -0.0183 (-0.0253 to -0.0078) | -2.26 (-3.15 to -1.54) | S | S | Diluted, with a growing absolute yield |
| D-journals denominator | F2 | -0.0046 (-0.0077 to 0.0019) | -0.58 (-1.40 to 0.05) | NS | NS | Not diluted (unexpected; investigate the decomposition) |
| Stable-coverage journals | F2 | -0.0186 (-0.0253 to 0.0018) | -2.52 (-4.68 to -1.39) | NS | S | Not diluted (unexpected; investigate the decomposition) |
| Follow-up censored at 2021 (exploratory) | F2 | -0.0244 (-0.0374 to -0.0166) | -2.40 (-4.01 to -1.19) | S | S | Diluted, with a growing absolute yield |
| Headline age 3 years | F2 cleaned | -0.0131 (-0.0170 to -0.0028) | -1.50 (-2.79 to 0.02) | S | NS | Diluted, with a growing absolute yield |
| Excluding 2020–21 cohorts | F2 cleaned | -0.0134 (-0.0198 to -0.0021) | -1.93 (-2.71 to -1.19) | S | S | Diluted, with a growing absolute yield |
| D-journals denominator | F2 cleaned | 0.0007 (-0.0026 to 0.0080) | -0.27 (-0.90 to 0.35) | NS | NS | Not diluted (unexpected; investigate the decomposition) |
| Stable-coverage journals | F2 cleaned | -0.0148 (-0.0205 to 0.0067) | -2.30 (-4.36 to -1.28) | NS | S | Not diluted (unexpected; investigate the decomposition) |
| Follow-up censored at 2021 (exploratory) | F2 cleaned | -0.0209 (-0.0325 to -0.0146) | -2.12 (-3.59 to -0.71) | S | S | Diluted, with a growing absolute yield |

S = supported; NS = not supported.

## Findings

**Excluding the COVID cohorts removes the 2018 breakpoint.** Breakpoints on cohorts 2008–2019 (excluding 2020) find no late upturn:
- F1: P1 break 2010 (-2.1 → -0.3%/yr; ΔAIC vs no break 3.3); 5-yr incidence break 2011 (-7.7 → -4.0%/yr).
- F2: P1 break 2013 (4.3 → 0.5%/yr; ΔAIC vs no break -11.3); 5-yr incidence break 2013 (-1.7 → -2.6%/yr).
- F2 cleaned: P1 break 2013 (4.5 → 0.9%/yr; ΔAIC vs no break -11.3); 5-yr incidence break 2012 (-1.3 → -2.2%/yr).

The 2018 "break" in secondary analysis 1 therefore reflects the 2020 COVID publication surge, not a lasting change.

**The F1 indexing dip explains F1's uncertain H1.** F1 guideline counts fall from 1,708 (2020) to 1,022–1,083 (2022–2023), then rise to 1,720–1,945 (2024–2025). F2 shows no such dip (477–585), so this is NLM publication-type tagging rather than guideline output. With follow-up censored at calendar year 2021, which excludes the dip and recovery, F1 β = −0.054 (−0.063 to −0.047), and all three frames support H1. This analysis was not pre-specified: it is reported as part of the pre-specified F1-versus-F2 2022–23 comparison and labelled exploratory.

**The D-journals denominator attenuates dilution.**
- Restricted to journals that already published guideline-cited research in 2008–2012, D grows only about 1.5%/yr, against 4.7%/yr for all of D.
- Dilution weakens: β crosses 0 in every frame. H2 holds for F1 (−3.0%/yr) but not for F2.
- Much of D's growth is therefore in journals launched after 2012 or rarely cited by guidelines. This is consistent with the decomposition (fixed guideline capacity against a literature growing mainly outside the established clinical journals) and is a key nuance for the paper.
- Caveat: the journal set covers only 48% of D in 2025, by design.

**F3 (NICE), descriptive only.**
- The pilot of 10 guidelines is too small to estimate a trend.
- Median citation age: NICE 9 years, against 7 years for F1 guidelines from 2015–2020. The share of references aged 5 years or less is 32% for NICE against 41% for F1.
- Only 23% of NICE-cited papers are also cited by any F1 guideline, and 9% by any F2 guideline. PubMed-indexed guidelines and NICE draw on largely different evidence, which is a limit on generalising beyond PubMed-indexed guidance.
