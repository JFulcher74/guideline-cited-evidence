# Figure review (2026-11-02, independent AI reviewer; findings to act on)

Numbers were checked: the plotted values match the results tables. The problems are in form, honesty and the composition of the set.

## Must-fix
1. **Remove the titles inside the images,** especially assertion titles; the Fig 3 title implies causation. Use panel letters and neutral labels, and put claims in captions.
2. **Redraw at final print size:** 85 mm single column or 175 mm double column, with text of at least 7 pt. Figs 2, 4 and 5 are currently too wide.
3. **Add uncertainty to Figs 1–4:** bootstrap bands for P1 and incidence, CIs on the decomposition bars and on the ratios.
4. **Flag 2020 (COVID)** in Figs 1 and 2: an open marker, a shaded band, or a dashed final segment.
5. **Fig 2 needs comparable axes:** one panel on a log scale, or each frame indexed to 2008.
6. **Fig 4a:** use a log ratio axis, add CIs, de-emphasise the noisy early cohorts, explain or remove the 2018 line, and use pooled or geometric rather than arithmetic mean ratios.
7. **Fig 5:** group the rows as primary, pre-specified sensitivity and exploratory.

## Should-fix
8. **Fig 1:** use a log y-axis and put D's doubling time in the caption.
9. **Fig 3:**
   - separate the P1 total from its components, or use a waterfall;
   - add a combined "capacity" marker;
   - use one term for "uniqueness";
   - add a COVID-excluded version in the supplement.
10. **Fig 4b (G4 pilot):** move it to the supplement. Show the two proportions as dot-and-CI and state which frame was used.
11. **Fig 5:**
    - drop the H1 "headline age 3 years" row, because β does not depend on the headline age;
    - consider showing an OR per decade;
    - relabel the H2 units.
12. **Colour:** make F2 cleaned a lighter or dashed variant of F2, since it is a subset, rather than a third hue.

## Nice-to-have
13. **Remove redundant legends:** Fig 1 has end labels, and Fig 2 has panel titles.
14. **Fig S1:**
    - explain why the x-axis runs to 2025;
    - annotate the 2020 F1 spike;
    - consider an indexed view.

## Recommended set
- **Main:**
  1. a study flow diagram (new);
  2. indexed growth on a log scale;
  3. cumulative incidence on a shared log axis, optionally with life-table curves by age;
  4. decomposition as a waterfall;
  5. robustness forest.
- **Supplement:**
  - guideline counts;
  - selected-design ratio;
  - G4 pilot;
  - COVID-excluded decomposition and breakpoints;
  - D against D-journals growth (possibly promoted to main).

## Numerical points raised
- **F1 β against its incidence curve.** β ≈ −0.019 looks weaker than the 5-year incidence decline (about −6%/yr, 2008–2018).
  - Checked: the bootstrap distribution is unimodal but right-skewed. Cohorts 2021–24 (indexing recovery) pull β toward 0.
  - Cohorts 2008–2020 only give β = −0.025, and 2008–2019 gives −0.028. This needs explaining in the text and caption.
- **D carries no uncertainty.** It is treated as a census; say so.
- **Follow-up windows differ.** Fig 4a uses cohorts 2008–2022 (3-year follow-up) while the others use 2008–2020; explain this in the caption.
