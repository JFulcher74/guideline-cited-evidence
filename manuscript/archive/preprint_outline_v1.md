> **Superseded (2026-10-09).** This is the v1 outline, based on publication-type strata. The current design is `manuscript/protocol.md`, and the manuscript outline will be rewritten from it. The terms "formulaic" and "basket" used below have been retired; the protocol uses "selected secondary-analysis designs", framed as research waste.

# Preprint outline — Compositional dilution of the biomedical literature

**Target:** medRxiv, meta-research. **Length:** ~2,500 words (excluding abstract, references, legends).
**Working title:** Formulaic study designs are outgrowing trial-grade evidence in PubMed: a 1950–2025 bibliometric analysis with a data-estimated breakpoint

> Framing rules
> 1. The question is **composition**, not raw volume: total PubMed output did not rise above its trend after 2022 (pilot data); the share of formulaic designs relative to high-signal evidence did.
> 2. 2022 is a **hypothesised** breakpoint (ChatGPT public release, 30 Nov 2022), tested against a data-estimated one. Report whichever the data support.
> 3. Temporal coincidence ≠ causation. Formulaic growth predates generative AI.
> 4. The noise discount is a **scenario parameter**, not a measured quantity.
> 5. Individual basket designs are **examples** of exploited literature; they are never reported as separate results, only via leave-one-out sensitivity.

| Section | Words |
|---|---|
| Abstract (structured, separate) | 250 |
| Introduction | 400 |
| Methods | 650 |
| Results | 650 |
| Discussion | 650 |
| Conclusion | 100 |
| **Body total** | **2,450** |

## Abstract (structured; ≤250 words)
Background / Methods / Results / Conclusions. Fill last from `data/processed/*_dp.csv`.

## 1. Introduction (~400 words)
1. Biomedical output has grown exponentially for decades; volume is not knowledge.
2. Some study designs can be produced at scale from public data with little original input. Documented examples: single-factor NHANES analyses [1], two-sample Mendelian randomisation [2], Global Burden of Disease reanalyses [3], network pharmacology [4], pharmacovigilance disproportionality analyses [5], and bibliometric reviews [6].
3. Generative AI (public from Nov 2022) may lower the cost of such papers further, but the growth began earlier.
4. Gap: no long-run analysis has compared this formulaic literature against trial-grade evidence, or tested *when* the divergence began.
5. Aim: quantify the divergence between a pre-specified basket of exploited designs and high-signal clinical evidence from 1950 to 2025, and estimate whether and when its growth changed.

## 2. Methods (~650 words)
- **2.1 Data source & design:** PubMed via NCBI E-utilities (Biopython `Entrez.esearch`, counts only); retrieval date `{{retrieved_utc}}`; year = publication date `[dp]`; 1950–2025; **preprints excluded** (`NOT preprint[pt]`) so all strata are indexed journal literature. Code and raw counts archived at `{{repo/OSF DOI}}`.
- **2.2 Strata:**
  - (a) *Total*: all records.
  - (b) *High-signal*: Randomized Controlled Trial, Clinical Trial Phase III, Practice Guideline publication types.
  - (c) *High-volume*: one stratum built from a pre-specified basket of exploited designs (title/abstract text words), each justified by a published source:

    | Design | Justification |
    |---|---|
    | NHANES cross-sectional | [1] |
    | Two-sample MR | [2] |
    | Global Burden of Disease | [3] |
    | Network pharmacology | [4] |
    | FAERS disproportionality | [5] |
    | Bibliometric/scientometric | [6] |

    Exact query strings: **Supplementary Table S1** (from the `query` column of the raw CSV).
- **2.3 Growth metrics:** CAGR and doubling time = ln 2 / ln(1+CAGR) for epochs 1980–2000, 2000–2022, 2022–2025 and 2023–2025. If the starting year has zero records, the first non-zero year is used and reported. The primary estimate is a log-linear regression with a 95% CI.
- **2.4 Primary outcome:** the ratio of high-volume to high-signal records per year.
- **2.5 Breakpoint analysis:** a continuous segmented (hinge) log-linear regression over 2000–2025 with one break, chosen by grid search. A 95% CI for the break year comes from a moving-block bootstrap of residuals (block length 3, 999 replicates). This model is compared by AIC with a fixed 2022 break and with a no-break model. A break counts as supported when ΔAIC > 2 versus no break.
- **2.5b Two-break test:** checks for a second change in growth on top of the best single break. Two models are tested against the one-break model: (i) two estimated breaks at least 3 years apart; (ii) the estimated break plus a break fixed at 2022. Because break years are found by grid search, AIC is anti-conservative, so p-values come from a moving-block bootstrap under the one-break null, repeating the full grid search in each of 999 replicates. In simulation the type I error was about 0.05 for the two-break test and about 0.02 for the added-2022 test. CIs for the break years come from a bootstrap around the two-break fit.
- **2.6 Counterfactual:** the 2010–2022 log-linear trend is projected to 2023–2025 and compared with observed counts (observed/projected). The projection is repeated excluding 2020–21, the COVID-19 publication surge.
- **2.7 Noise-discount scenarios:** post-2022 volume is multiplied by (1 − d), with d from 0 to 0.5 in steps of 0.1, in step and linear-ramp variants. This is a sensitivity analysis only.
- **2.8 Robustness:** (i) repeat everything using PubMed entry date `[edat]`; (ii) leave each basket design out in turn and recompute; (iii) acknowledge publication-type indexing lag for recent years.
- **2.9 Ethics / reporting:** no human participants, so no ethics approval is required. Reporting checklist: `{{select}}`.

## 3. Results (~650 words)
- **3.1 Corpus growth** — *Figure 1* (three strata, log scale). Total output in 2022 vs 2025, with its observed/projected ratio from the counterfactual.
- **3.2 Epoch growth rates** — *Table 1*: CAGR, doubling time and log-linear 95% CI per stratum and epoch. Doubling times to insert here:
  - Total: 1980–2000 `{{ }}` y; 2000–2022 `{{ }}` y; 2022–2025 `{{ }}` y
  - High-signal: `{{ }}` / `{{ }}` / `{{ }}` y
  - High-volume: `{{ }}` / `{{ }}` / `{{ }}` y
  - Ratio: `{{ }}` / `{{ }}` / `{{ }}` y
- **3.3 Divergence and breakpoint** — *Figure 2* (ratio with segmented fit and the break-year CI band). *Table 2*: estimated break year (95% CI), growth before and after the break, and AIC compared with the fixed-2022 and no-break models. State plainly whether the data put the break at about 2022 or earlier.
- **3.3b Two-break test** — *Table 2b* (`two_breaks_dp.csv`): break years with CIs, growth in each of the three segments, and p-values for a second break and for an added 2022 break. Leave-one-out versions go in *Supplementary Table S3*.
- **3.4 Counterfactual** — *Table 3*: observed vs projected counts for 2023–2025, with and without the COVID years.
- **3.5 Noise-discount scenarios** — *Figure 3*; effective CAGR and doubling time for each value of d (Supplementary Table S2).
- **3.6 Robustness** — `[edat]` results, and leave-one-out (*Supplementary Figure S1* and *Table S3*): does any single design drive the divergence?

## 4. Discussion (~650 words)
1. **Principal findings** (3–4 sentences, citing Tables 1–2).
2. **Composition rather than inflation:** total output did not rise above trend, but its make-up shifted.
3. **Timing and generative AI:** set the estimated break year against Nov 2022. Formulaic growth predates ChatGPT. Possible drivers include open GWAS summary statistics, point-and-click analysis tools, paper mills, open-access/mega-journal capacity and incentive structures. Generative AI may amplify an existing trend rather than start one.
4. **Recent plateau:** some designs flattened in 2025, plausibly because of editorial policy changes (verify specific journal policies before stating).
5. **Noise discount:** a what-if tool, because the true low-value fraction is unknown. Suggest validation by manually classifying a random sample of records.
6. **Implications:** workload for evidence synthesis, guideline development, editorial screening and reviewer capacity.
7. **Limitations:**
   - Text-word searches misclassify: they capture legitimate uses (e.g. GBD collaborator papers, rigorous MR) and miss unlabelled formulaic work.
   - The basket is illustrative, not exhaustive.
   - PubMed is not the whole literature.
   - RCT volume is not a measure of quality.
   - The post-2022 window is short.
   - The design is ecological.
   - The bootstrap assumes approximate stationarity of the residuals.
8. **Future arms:** a measure of LLM exposure from excess vocabulary in abstracts; preprint growth on medRxiv/bioRxiv; an abstract-level classifier.

## 5. Conclusion (~100 words)
One paragraph: the size and timing of the divergence and the scenario range, with the correlation-not-causation statement.

## References (verified in PubMed, 2026-10-09)
1. Suchak T, et al. Explosion of formulaic research articles, including inappropriate study designs and false discoveries, based on the NHANES US national health database. *PLoS Biol.* 2025. doi:10.1371/journal.pbio.3003152 (PMID 40338847)
2. Stender S, Gellert-Kristensen H, Smith GD. Reclaiming mendelian randomization from the deluge of papers and misleading findings. *Lipids Health Dis.* 2024. doi:10.1186/s12944-024-02284-w (PMID 39244551)
3. Degen, Riebler, Held. Paper mill or paper mine? A tentative answer to the sharp increase in research papers based on the Global Burden of Disease database. *J Clin Epidemiol.* 2026. doi:10.1016/j.jclinepi.2026.112464 (PMID 42624337)
4. Panossian. Trends and pitfalls in the progress of network pharmacology research on natural products. *Pharmaceuticals (Basel).* 2025. doi:10.3390/ph18040538 (PMID 40283973)
5. Fusaroli M, et al. The REporting of A Disproportionality Analysis for DrUg Safety Signal Detection Using Individual Case Safety Reports in PharmacoVigilance (READUS-PV): development and statement. *Drug Saf.* 2024. doi:10.1007/s40264-024-01421-9 (PMID 38713346) — *supports poor reporting quality, not exploitation per se; find a stronger source.*
6. Montazeri, et al. Preliminary guideline for reporting bibliometric reviews of the biomedical literature (BIBLIO). *Syst Rev.* 2023. doi:10.1186/s13643-023-02410-2 (PMID 38102710) — *reporting guideline; find a source documenting volume/quality concerns.*

Hub-gene bioinformatics was dropped from the basket (2026-10-09) because no supporting source was found.

## Back matter checklist
- Data/code availability (repo + archived DOI) · Funding · Competing interests · Author contributions · AI-use disclosure · References (target ≤40) · Supplementary Tables S1–S3, Figure S1.
