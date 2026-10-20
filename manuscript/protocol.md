# Study protocol (v2.3, draft for OSF pre-registration)

**Title:** Is guideline-cited evidence keeping pace with the biomedical literature? A cohort analysis, 2008–2025

**Registered:** OSF, 16 October 2026, Secondary Data Preregistration, public, doi:10.17605/OSF.IO/VN9BQ (https://osf.io/vn9bq).
- The registration form text (research questions RQ1–RQ5; hypotheses H1–H3; the statistical model for each) matches this version.
- The protocol file attached to the registration is the previous version (v2.3.3, git commit f541aec, sha256 fa806f9c…). In it, "H2" is the generative-AI hypothesis, which is H3 here.
- **This version is published in the registration's public OSF project** (https://osf.io/hpg6f, file "protocol V2.3.4", uploaded 16 October 2026, sha256 c015cd7798ff3ee16fedbd57d80c4e6c6a7694d6981d2b22f6795c34bb8f1b92, verified against the OSF API). That hash is of the file as uploaded; later repository edits to this status block change it. No data were accessed between the two versions.

**Status:** v2.3.4, 2026-10-16, approved by the author. v2.3.4 adds explicit research questions (RQ1–RQ5) to §2 and links each hypothesis to one. It adds H2, the directional form of the existing P1 estimand, and renumbers the generative-AI hypothesis from H2 to H3. RQ4 and RQ5 are stated as estimation questions without directional hypotheses. v2.3.3 freezes the F2 named-body list (31 bodies; WHO rule tightened), accepts F2 recall of 0.92 without tuning, and records the decision not to use a second coder. v2.3.2 records two author decisions made after the GBD and coverage checks (§3.4, §3.5, §5):
- the GBD arm counts only reanalyses by teams outside the GBD consortium (no collaborator-group byline and no IHME author);
- coverage and weights are computed over journal-article guidelines, with NCBI Bookshelf records reported as a structural gap.

v2.3.1 rewrites secondary analysis 3 (§6) so that cohorts after 2020 are analysed rather than dropped by right-censoring. It adds a group × cohort interaction with a pre-specified 2018 hinge, a 3-year equal-follow-up sensitivity, and a descriptive breakdown by design. v2.3 responds to a second external review (2026-10-15):
- the construct is renamed from "practice-changing" to "guideline-cited";
- the decision rule now separates dilution (P2) from absolute yield (P1);
- inverse-coverage weighting is primary, with the unweighted restricted analysis as a sensitivity;
- official GBD Collaborator papers are excluded from the selected designs;
- G4 is enlarged to 50 pairs per group;
- the 8-year window is shown alongside 5 years in the main results;
- F2 gets a recall test;
- a journal-restricted denominator sensitivity and a coverage audit are added.

Gate results are unchanged. v2.2 (2026-10-09) sets the window to 2008 onward and adds a coverage correction, after gate G1 (§5). v2.1 replaced v2 after an external review (Gemini) and checks against PubMed data. Changes from v2: two co-primary guideline frames; a MeSH-independent denominator; time-to-first-citation (Kaplan–Meier / discrete-time hazard) in place of a fixed window; a citation-context pilot (G4); the generative-AI question retained as a pre-registered hypothesis; no Overton access, handled as a limitation.
**Target:** medRxiv preprint only (free to post; no journal submission planned). Sole author. About 2,500 words. Reporting will follow BIBLIO (Montazeri et al., *Syst Rev* 2023, PMID 38102710).

---

## 1. Background and rationale

Biomedical publication volume has grown roughly exponentially for decades, and has long been described as exceeding what clinicians can use (Bastian, Glasziou & Chalmers, *PLoS Med* 2010, doi:10.1371/journal.pmed.1000326; Ioannidis, *PLoS Med* 2016, doi:10.1371/journal.pmed.1002049). Whether practice-changing knowledge has grown at the same rate is unknown. If it has not, a growing share of research never reaches practice: the literature is being *diluted*. Citation by clinical guidelines has been used before as an indicator of the clinical value of research (Grant et al., *BMJ* 2000, doi:10.1136/bmj.320.7242.1107; Thelwall & Maflahi, *J Assoc Inf Sci Technol* 2016, doi:10.1002/asi.23432), but not, as far as I know, to track the whole literature over time. Some secondary-analysis designs that can be produced at scale from public data (single-factor NHANES analyses, two-sample Mendelian randomisation, Global Burden of Disease reanalyses and others) are one suspected source of that dilution.

The measured construct is **guideline-cited evidence**: research cited by a clinical practice guideline issued by a national or international professional society or a government/guideline body. This captures research that clinicians, through a formal clinically authored process, judged relevant enough to cite. "Practice-changing" is used only to frame the wider debate, never as the name of an outcome. Guidelines also cite background, methods and negative evidence, so citation is a proxy for practice relevance, not proof of practice change (see G4 and §8).

## 2. Objectives and hypotheses

**Research questions** (each hypothesis below names the question it answers).
- **RQ1 (dilution):** has the probability that a newly published research article is eventually cited by a clinical practice guideline changed across publication cohorts 2008–2024?
- **RQ2 (absolute yield):** has the number of articles per cohort cited by a guideline within 5 years grown, stayed flat or fallen (2008–2020), and how does that compare with the growth of all research articles?
- **RQ3 (timing):** when did any change occur, and is there an additional change after 2022?
- **RQ4 (guideline capacity):** how much of any change reflects guideline capacity rather than the research literature?
- **RQ5 (high-volume designs):** are papers using the six selected designs cited at a different rate from other research, and did that change after 2018?

**Co-primary outcomes.** They answer different questions and are reported together under the decision rule in §6.
- **P1. Absolute yield.** The number of unique papers, by publication cohort, first cited by a frame guideline within 5 years.
  - It does not use the denominator, so it is not affected by denominator drift.
  - Estimand: annual growth of this count, reported alongside the annual growth of the research denominator.
- **P2. Dilution: time to first guideline citation.** Cumulative incidence of first guideline citation by cohort, from Kaplan–Meier life tables, handling right-censoring.
  - Estimand: the cohort trend β in the discrete-time hazard of first citation (§6).
  - This is the probability that a paper from cohort *Y* enters a guideline, so it is the measure of dilution.

**Secondary.**
1. Breakpoints in P1 and P2: when did any change occur?
2. Decomposition: how much of any change reflects guideline capacity (number of guidelines, references per guideline) rather than literature growth?
3. Yield of the selected secondary-analysis designs compared with all other research: do these designs reach guidelines at a different rate, and did that change after their post-2018 volume surge?
4. Early signal for 2021–2024 cohorts, descriptive only.

**Context (descriptive, not tested).** Annual FDA novel approvals (new molecular entities and original biologics), from Drugs@FDA.

**Pre-registered hypotheses.**
- **H1 → RQ1 (dilution).** The hazard of first guideline citation declines across cohorts (β < 0 in P2): a paper from a later cohort is less likely to be cited by a guideline than one from an earlier cohort.
- **H2 → RQ2 (absolute yield relative to volume).** For cohorts 2008–2020, the annual growth of guideline-cited papers (P1) is lower than the annual growth of the research denominator D: the P1 estimand (growth of P1 minus growth of D) is below 0. H2 can hold even if P1 itself is rising.
- **H3 → RQ3 (timing; generative AI).** After 2022, the selected-design share or the P2 cohort trend shows an additional change, tested as a break fixed at 2022 on top of the best-fitting single break. **Disclosed:** the exploratory v1 analyses (publication-type strata, §7) found no 2022 break, so H3 is expected to be unsupported. It is retained so the question is answered on the new outcome and the result is reported either way. When any earlier change occurred (the rest of RQ3) is estimated by the breakpoint analysis without a directional hypothesis.
- **RQ4 (guideline capacity): no directional hypothesis.** It is answered by estimation: the decomposition into number of guidelines, references per guideline and share citing recent work (§6, secondary analysis 2).
- **RQ5 (high-volume designs): no directional hypothesis.** The protocol assumes no direction (§3.5, §6 secondary analysis 3), because descriptive counts seen before registration cannot show whether these designs are cited more or less often than other research. It is answered by the estimates γ, δ₁ and δ₁ + δ₂ from the group × cohort hazard model.
- **Untested candidate drivers** of any earlier acceleration: open-access datasets (e.g. UK Biobank), automated analysis packages (e.g. TwoSampleMR), paper mills, and large language models. These dates and attributions are unverified and must be checked before they appear in the manuscript. No causal claim is made.

## 3. Definitions

### 3.1 Guideline frames (the "high-signal" source)

**Inclusion rule:** a document that gives recommendations for clinical practice, is clinically authored or edited, is issued by or on behalf of a reputable national or international body (government agency, statutory guideline body, or professional or scientific society), and can be cited.

Two numerator frames are **co-primary**, analysed in full and reported side by side. Neither is chosen after seeing the results.
- **F1 (publication-type frame):** PubMed records with `"Practice Guideline"[pt]`, published 2008–2025, excluding preprints. Guidelines before 2008 are excluded because their iCite reference coverage is below 0.70 (G1, §5). Pilot counts: 1,555 (2021), 1,239 (2022), 1,214 (2023), 1,917 (2024), 2,207 (2025). The 2022–23 dip is probably an indexing artefact (§8).
- **F2 (named-body frame):** records authored by a pre-specified list of named bodies (matched by collective author `[cn]`/byline) whose title or abstract contains guideline-type words (*guideline\**, *recommendation\**, *consensus statement*, *position statement*), whatever the publication type. This does not depend on NLM publication-type tagging. The list is fixed before extraction and published as Supplementary Table S1. Matching combines collective author, title acronyms and journal, because societies change their author strings (e.g. "on behalf of the ESC Scientific Document Group").
  - **Approved by the author 2026-10-15.**
    - Files: `manuscript/f2_named_bodies.csv` (31 bodies with matching rules), `manuscript/f2_reference_set_candidates.csv` (50 landmark guidelines pinned to their primary full-guideline PMIDs), and `scripts/10_f2_draft_check.py` → `data/processed/f2_body_counts.csv`, `f2_reference_set.csv`.
    - **Recall 46/50 = 0.92**, meeting the 0.80 threshold.
    - **Misses:**
      - the NICE hypertension summary (*BMJ* 2019), AASLD NAFLD guidance (2018) and ADA Standards of Care 2010, all of which have no guideline word in the title or abstract;
      - the AAP paediatric hypertension guideline (2017), which has no AAP byline or title mention.
    - Because recall met the threshold, the rules are not tuned to these misses (author decision, 2026-10-15). Tuning to the reference set would overstate recall.
    - **WHO rule tightened before freezing (2026-10-15).** The draft rule retrieved 2,340 records, including studies of adherence to WHO guidelines and titles where "who" is the ordinary word. The frozen rule requires a WHO byline, or a WHO-affiliated author with WHO and a guideline word in the title. It retrieves 314 records, and recall is unchanged at 46/50. This used record counts and titles only, not citation data.
    - The 31 body rules retrieve 8,053 records for 2008–2025 (summed across bodies, before de-duplication).
    - **Precision is assessed by the F2 eligibility sample (§3.1).**
  - **Recall test (before freezing):** before running the F2 query, the author lists a reference set of 50 major guidelines from the named bodies, 2008–2025, from the bodies' own websites. F2 recall against this set is reported. If recall is below 0.80, the matching rules are revised and retested before extraction, and every revision is recorded.
- **Eligibility validation (single author; no second coder, author decision 2026-10-15):** the author codes a random sample of 200 F1 records (stratified by decade) and 100 F2 records against the inclusion rule, using a written codebook fixed before coding. A random 25% is re-coded blind after at least 14 days. Reported: positive predictive value with a Wilson 95% CI and intra-rater Cohen's κ. If PPV is below 80% for a frame, that frame is reported with the shortfall stated.
- **External frame (F3, validation pilot):** NICE guidance (NG, CG, TA), largely not indexed in PubMed. References are extracted from published evidence reviews and matched to PMIDs. Reported: PMID match rate, and agreement with the F1/F2 trends for the overlapping years. This also estimates how much the PubMed-only reference route undercounts, because I do not have access to Overton (§8).

**Versions:** each paper counts once, dated by its *first* citation in any version of any frame guideline.

**Year assignment:** a `[dp]` search matches both print and electronic publication dates, so some records match two adjacent years (2,577 of 31,220 F1 guidelines, 8%). Every record, guideline or cited paper, is assigned to the *earlier* of its matching years.

### 3.2 Research denominator (D)

**D (primary, MeSH-independent):** research-type journal articles, by publication year `[dp]`:
`"Journal Article"[pt] NOT (Comment[pt] OR Editorial[pt] OR Letter[pt] OR News[pt] OR "Published Erratum"[pt] OR Guideline[pt] OR "Practice Guideline"[pt] OR preprint[pt])`
Pilot sizes: 637,868 (2005), 1,143,108 (2015), 1,646,329 (2022), 1,733,476 (2025).

**Why not MeSH:** the share of these records carrying `Humans[mh]` fell steadily from 63% (2005) to 49% (2025), and the MEDLINE-indexed share from 93% to 62% (partly indexing lag, partly non-MEDLINE journals). A MeSH-based denominator therefore drifts. I also rejected iCite's `is_clinical` flag as a denominator: in a 2015 sample of 265 journal articles only about 2% carry it (3% in 2022 from 279), because it is itself publication-type based.

**Sensitivity D-Humans:** the same query plus `Humans[mh]`, reported with the drift caveat. **Sensitivity D-all:** all PubMed records excluding preprints.

**Sensitivity D-journals (clinical journal set):** D restricted to journals that published at least one paper cited by a frame guideline from **2008–2012**.
- The journal set is fixed from those early guidelines only. Using all years would define the denominator by the outcome and would exclude recently launched journals, which have had no time to be cited, biasing the later cohorts.
- This removes journals that never publish clinically citable research (e.g. veterinary, plant or chemistry journals) without MeSH tags or indexing lag.
- It misses clinical journals launched after 2012. The share of D in such journals is reported by cohort.

Cited papers outside D (e.g. a cited record without the Journal Article type) are counted and reported separately.

### 3.3 Outcomes

- **P1.** Papers in cohort *Y* whose first frame-guideline citation occurs within 5 years (guideline year ≤ *Y* + 5), as an absolute count. Cohorts 2008–2020 are complete with data to 2025. The 8-year version (cohorts 2008–2017) is presented **alongside** the 5-year headline in the main results, not only in the supplement, because the median age of cited references is 7 years (§5). The 3-year version (cohorts 2008–2022) is a sensitivity analysis.
- **P2.** Life table by cohort and age *a* = guideline year − *Y*: papers at risk, first citations at age *a*, censored at the end of follow-up (2025). Cumulative incidence by age *a* = 1 − Kaplan–Meier survival. Cohorts 2008–2024 contribute, so the later cohorts are not dropped. Cohorts start in 2008 so that every cohort's follow-up begins in a year with adequate guideline reference coverage. Cumulative incidence at 5 years is reported as the headline summary.
- **Window rule (fixed before extraction):** if the lag pilot (§5) shows fewer than 40% of references are 5 years old or younger, the headline age becomes 8 years and 5 years becomes a sensitivity analysis.

### 3.4 Coverage correction

iCite reference coverage of F1 still rises after 2008, from 0.70 in 2008 to 0.88 in 2025. Without correction, rising coverage would look like growth in guideline-cited papers: about 26% (0.88 / 0.70) of apparent growth across the window. Restricting to guidelines with references does not remove this, because the number of such guidelines rises with coverage. The drift affects P1 and P2 alike.

**Primary: inverse-coverage weighting.**
- Analyses use guidelines with at least one iCite reference.
- Each citation from a guideline published in year *G* is weighted by 1 / coverage(*G*) when counting papers and first citations. This estimates what full coverage would show.
- Coverage is computed separately for each frame (F1, F2), by guideline year, over **journal-article guidelines only**. NCBI Bookshelf records (full guidelines published as books, mainly WHO and NICE; 4.1% of F1 records 2008–2025) are never in iCite. They are excluded from coverage denominators and weights, counted, and reported as a structural gap (§8). NICE is partly addressed by F3; WHO is not.
- It assumes guidelines missing references cite like those that have them. The coverage audit below tests this.

**Sensitivity: unweighted.** The same restricted set without weights. Guideline counts, references per guideline and the decomposition are reported both ways.

**Coverage audit (before extraction).** iCite builds references from MEDLINE, PubMed Central, Crossref and machine-extracted web full text (Hutchins et al., *PLoS Biol* 2019, doi:10.1371/journal.pbio.3000385). Guidelines missing references may therefore be disproportionately paywalled. The audit compares, by guideline year and journal:
- coverage for F1 guidelines with and without a PubMed Central full text;
- median references per covered guideline.

If coverage differs markedly by full-text availability, this is reported as a limit on the weighting assumption, and a further sensitivity restricts to journals with stable coverage across the window.

Both the weighted and unweighted analyses are reported, and neither is chosen after seeing the results.

### 3.5 Selected secondary-analysis designs

**Terminology.** There is no established collective term for these designs, so we use a descriptive one and define it operationally. *Selected secondary-analysis designs* are study designs that published sources describe as produced in high volume from public data with methodological concerns: two-sample Mendelian randomisation, bibliometric reviews, NHANES cross-sectional analyses, Global Burden of Disease reanalyses, network pharmacology and FAERS disproportionality analyses. We frame them within the established concept of *research waste* (Chalmers & Glasziou, *Lancet* 2009, doi:10.1016/S0140-6736(09)60329-9, PMID 19525005). We use "formulaic" only when quoting sources that use the word (e.g. Suchak et al. 2025), and we make no claim that any individual paper is low-value. Hub-gene bioinformatics was dropped for lack of a supporting citation.

The six designs are run as a single text-word query. Papers using them are used only as a subgroup of D (secondary objective 3), and results are not reported design by design, apart from the descriptive count below. Because guidelines may cite epidemiological designs (GBD, NHANES) as background rather than as evidence for a recommendation, objective 3 is interpreted with the G4 context results.

**The GBD arm counts only reanalyses by teams outside the GBD consortium.** Consortium output is excluded: records with a GBD collaborator-group byline (e.g. "GBD 2019 Diseases and Injuries Collaborators"), and records with any author affiliated with the Institute for Health Metrics and Evaluation (IHME), which coordinates GBD.
- The construct is an independent group reusing published GBD estimates. A paper with an IHME author is consortium-involved by definition, which is why the affiliation rule is used even though it also removes some papers that describe themselves as secondary analyses.
- The affiliation rule also catches flagship papers listed under individual authors (e.g. the GBD 2010 *Lancet* papers).
- The exclusion applies to the GBD arm only. The other five designs are not filtered by authorship.
- The exact exclusion string is tested before freezing. Its precision is checked on a sample of 50 retrieved GBD records, and the string is published with the protocol.
- Implemented GBD arm: `("Global Burden of Disease"[tiab] NOT (GBD[cn] OR "Global Burden of Disease"[cn] OR "Global Burden of Diseases"[cn] OR "Institute for Health Metrics and Evaluation"[ad]))`.
- PubMed indexed only the first author's affiliation before about 2014, so older consortium papers with a non-IHME first author may still pass. Earlier WHO burden-of-disease papers and incidental uses of the phrase also pass. Both are reported as limits of the text-word definition.
- **Spot check, 2026-10-15** (PubMed): about 350 records with "Global Burden of Disease" in the title or abstract carry one of these collective authors.
  - All 5 inspected were consortium outputs, so precision looks high.
  - Recall is incomplete: older flagship papers listed with individual authors only are not excluded, e.g. PMID 24880830 (Ng et al., GBD 2013 obesity, *Lancet* 2014).
  - An IHME affiliation filter was first rejected because it removes papers that self-describe as secondary analyses but have one IHME co-author. After the full check below, the author adopted it on construct grounds (2026-10-15): such papers are consortium-involved.
  - **Full check, 2026-10-15** (`scripts/09_gbd_exclusion_check.py`, `data/processed/gbd_exclusion_check.json`):
    - **Precision.** 352 records are excluded. In a random sample of 50, all are outputs of the GBD collaborator network: global, regional or national collaborator groups, the Vision Loss Expert Group, and the GBD–NHLBI–JACC writing group. Two (the "GBD Collaborator" and "GBD RA Collaborator Group" bylines) are borderline.
    - **Recall in the G4 pool.** Of 80,315 papers cited by 939 open-access 2015–2019 guidelines, 52 mention "Global Burden of Disease" in the title or abstract. The exclusion removes 11 and keeps 41. Of the 41, about 20 are consortium flagship papers listed under individual authors, such as the GBD 2010 *Lancet* capstones (Lozano, Vos, Murray, Lim 2012) and Ng 2014. Others are earlier WHO burden-of-disease papers, or papers that use the phrase without reanalysing GBD data (e.g. a GWAS and a qualitative review). Few, if any, are independent reanalyses of public GBD estimates.
    - The selected-design pool falls from 105 to 94 cited papers.
    - **Re-check under the final rule (2026-10-15).**
      - The rule excludes 794 records; in a random 50, 22 have a collaborator byline and 28 an IHME author.
      - In the G4 pool, 20 of the 52 GBD-text cited papers still pass the GBD arm. They are earlier WHO burden-of-disease papers (2003–2011), papers that use the phrase incidentally, two Brazilian GBD-network papers, and Vos et al. 2012, whose IHME affiliation was not indexed. None is clearly an independent reanalysis of public GBD estimates.
      - The selected-design pool is 73 cited papers.
    - **Decision (author, 2026-10-15):** exclude consortium output by collaborator byline or IHME affiliation, as above. The rule is justified on construct grounds. The citation results above were seen before the decision, and this is disclosed.
- Excluded consortium papers stay in D as ordinary research.
- **By design (2026-10-15, final rule; `scripts/11_selected_design_breakdown.py`).** Of the 73 guideline-cited selected-design papers in the G4 pool (cited by 939 open-access 2015–2019 guidelines):
  - NHANES cross-sectional analyses: 46;
  - GBD-text papers passing the exclusion: 20 (none clearly an independent reanalysis; see above);
  - FAERS disproportionality analyses: 4;
  - bibliometric reviews: 3;
  - two-sample Mendelian randomisation: 0;
  - network pharmacology: 0.

  The G4 "selected" group therefore mostly reflects NHANES analyses. These are counts only, with no denominator or rate. They are reported so that readers can see the pooled group's make-up.

Context for this subgroup comes from the Mendelian randomisation and NHANES literature: Munafò et al., *Addiction* 2024, doi:10.1111/add.16627; Byrne & Stender, *PLoS Biol* 2025, doi:10.1371/journal.pbio.3003167.

## 4. Data sources and extraction

| Item | Source | Method |
|---|---|---|
| Guideline frame F1 | PubMed E-utilities | `esearch`; PMID and `[dp]` year |
| Guideline frame F2 | PubMed E-utilities | `[cn]`/byline of the named bodies plus guideline-type words |
| Guideline reference lists | NIH iCite API (`references` field) | 1,000 PMIDs per call |
| Cited-paper year and membership of D | PubMed E-utilities | `epost` the cited PMIDs, then `esearch "#k AND (D query)"` per batch, so the numerator is exactly a subset of D |
| Selected-design membership | PubMed E-utilities | as above, with the selected-designs query |
| Denominators | PubMed E-utilities | yearly `esearch` counts (existing pipeline) |
| NICE references (F3) | NICE website evidence reviews | parsing, then PMID matching via the PubMed citation matcher |
| FDA approvals | Drugs@FDA data files (public download) | original approvals with type = NME, plus original BLAs |

All retrievals record the query, timestamp and software versions. NCBI rate limits are respected.

## 5. Feasibility gates (run before the main analysis; results reported regardless)

- **G1: reference coverage. Run 2026-10-09.** Share of F1 guidelines with at least one iCite reference, by year. Result: FAIL for 2000–2007 (0.54–0.67); 0.70–0.88 from 2008 to 2025 (`data/processed/gate_g1_coverage.csv`). Decision: the window starts in 2008 and the coverage correction in §3.4 applies, including the coverage audit. The same check will be run on F2 when it is built.
- **Lag pilot. Run 2026-10-10.** Ages of references cited by 2015 F1 guidelines. Applies the window rule in §3.3. Result: 960 guidelines, 94,246 references with known years; median age 7 years (IQR 3–12); 26.5% are 3 years old or younger, 42.1% 5 or younger, 59.9% 8 or younger; 110 references dated after the guideline were excluded (`data/processed/gate_lag_pilot_2015.csv`). Decision: 42.1% ≥ 40%, so the headline age stays at 5 years. It is close to the threshold, so the 8-year sensitivity carries weight. This is right-truncated by construction, so it is used only for the 5-versus-8-year headline choice, not as an estimate of lag.
- **Coverage audit (§3.4). Run 2026-10-15** (`scripts/08_coverage_audit.py`; `data/processed/coverage_audit_by_year_pmc.csv`, `coverage_audit_by_journal.csv`).
  - **Bookshelf records.** 975 of the 23,877 F1 records from 2008–2025 (4.1%) are NCBI Bookshelf books, not journal articles: WHO 463, NICE about 344, Royal College of Physicians 39, SAMHSA 23 and others. iCite covers only journal articles, so these can never have references, and they are counted as uncovered in G1. **Decision (author, 2026-10-15):** coverage and weights are computed over journal-article guidelines only, and the Bookshelf records are reported as a structural gap (§3.4, §8). The G1 figures above include them as uncovered and are kept as originally run.
  - **Journal articles (22,902; 17.8% with a PMC full text).** Coverage of guidelines with a PMC full text is 0.95–0.98 in every era. Without one, it is 0.76 (2008–2012), 0.84 (2013–2019) and 0.85 (2020–2025). The rise in coverage comes almost entirely from guidelines without a full text.
  - **By journal (96 journals with ≥ 50 guidelines).** 58 have coverage ≥ 0.90 in every era. Missingness clusters by journal, often non-English, e.g. *Ned Tijdschr Geneeskd*, *G Ital Cardiol*, *Rev Med Liege* and *Zhonghua Er Ke Za Zhi* at 0.00; *Obstet Gynecol* at 0.01 in 2008–2012.
  - **Implication.** Coverage differs markedly by full-text availability and by journal, so the weighting assumption (§3.4) is weakened. As pre-specified, the stable-coverage-journal sensitivity is triggered and will be reported.
- **G2: eligibility PPV** (§3.1). **Sheets generated 2026-10-10:** 200 F1 guidelines with references, stratified 2008–2013 / 2014–2019 / 2020–2025 (67/67/66) from a frame of 19,441, plus a 50-record recode sheet (`data/gates/`). Codebook: `manuscript/eligibility_codebook.md`.
  - **First pass complete, 2026-10-17** (06:24 UTC). All 200 records were coded by the author on a private coding page (`tools/g2-coder.html`). The codes are locked and hidden from the coder.
  - A sealed backup is in `data/gates/sealed/g2_first_pass_codes.csv.gz` (sha256 of the uncompressed CSV: 8d3990013a913e799c4ba71e9d17c0cb886643fbac9f2ca909d3a0079f342e23). It is not opened or summarised until the recode is done.
  - **Blind recode** of 50 records opens on 2026-10-31.
  - Scoring (PPV and intra-rater κ) runs after the recode.
  - **F2 sample drawn 2026-10-17** (`scripts/12_f2_eligibility_sample.py`).
    - The F2 frame has 7,943 records for 2008–2025, of which 7,007 have iCite references. Excluding the 27 already in the F1 sample leaves 6,980.
    - 100 records are stratified 34/33/33 across 2008–2013, 2014–2019 and 2020–2025 (seed 20221130), with a 25-record (25%) blind recode.
    - The sheets are `data/gates/f2_coding_sheet.csv` and `f2_recode_sheet.csv`. Coding uses the same codebook and the same page as F1.
    - The page does not show which named body each record matched.
    - **First pass complete, 2026-10-17** (11:05 UTC). All 100 records were coded by the author on the same page. The codes are locked and hidden from the coder.
    - A sealed backup is in `data/gates/sealed/f2_first_pass_codes.csv.gz` (sha256 of the uncompressed CSV: e3325317c069b42e7be5851605c43ab011868b1395a7c7a39398449d00b48d2f). It is not opened or summarised until the recode is done.
    - **Blind recode** of 25 records opens on 2026-10-31.
- **G3: NICE match rate.** Below 60% means F3 is reported descriptively only.
  - **Pilot design (fixed 2026-10-19, before any NICE reference was matched):**
    - **Sample:** 10 NICE guidelines (NG series) first published 2015–2020, taken in random order (seed 20221130) from NG1–NG199. A drawn guideline is skipped, with the reason recorded, if its page is missing, it was first published outside 2015–2020, or none of its evidence documents yields a parsable reference list.
    - **Sources:** the evidence-review PDFs on each guideline's "Evidence" page. Methods, consultation and comments, equality, scope and committee documents are excluded. A "full guideline" PDF is used only if the guideline has no separate evidence reviews. **Clarified 2026-10-19, before any reference was matched:** appendix documents (search strategies, evidence tables, flow diagrams) do not count as evidence reviews and are not used; the first run treated them as reviews and skipped guidelines whose references are only in the full guideline (e.g. NG66).
    - **Extraction:** the numbered "References" list of each document (excluded-studies appendices are not used), de-duplicated within each guideline.
    - **Matching:** the PubMed citation matcher (heuristic mode) on the raw reference text. A match counts only if it returns exactly one PMID whose first author and publication year (±1) agree with the reference.
    - **Gate statistic:** the match rate among references that look like journal articles (a year followed by a volume, e.g. "2018; 31(3)"), with a Wilson 95% CI. Reports, books and web pages cannot have PMIDs and are outside the gate denominator.
    - **Also reported:** the match rate over all references (the share of NICE's cited evidence reachable through PubMed), PDF parse success, and results per guideline.
  - **Result, 2026-10-19** (`scripts/13_g3_nice_pilot.py`; `data/gates/g3_nice_*.csv`). **G3 passed.**
    - **Sample:** 14 guidelines drawn to reach 10. Four were skipped because they have no evidence documents online: NG51 (2016) and the 2020 COVID-19 rapid guidelines NG163, NG172 and NG175. The 10 included are NG11, NG16, NG31, NG66, NG72, NG76, NG95, NG98, NG99 and NG155 (2015–2020), with 3,277 unique references.
    - **Gate statistic:** 1,748 of 2,044 journal-like references matched, **85.5% (95% CI 83.9–87.0%)**, well above the 60% threshold.
    - **All references:** 2,598 of 3,277 matched, **79.3% (77.9–80.6%)**. About a fifth of NICE's cited evidence (reports, books, grey literature and unmatched articles) is not reachable through PubMed.
    - **Precision:** every counted match agreed on first author and year. In a check of title-word overlap, 99.8% of matched records shared at least 60% of their title words with the reference; the 2 exceptions were Bookshelf reports with no PubMed title. A further 83 single candidates disagreed on author or year and were not counted.
    - **Limitations:**
      - The journal-like rule recognises "year; volume" styles only, so author-year lists (NG16, NG72, NG76, NG99) contribute almost nothing to the gate denominator. Their references count only in the all-references rate.
      - A random check of 20 parsed references found 19 clean and 1 that merged two references.
      - NICE's 2020 COVID-19 rapid guidelines have no evidence documents and cannot be part of F3.
- **G4: citation context (pilot).**
  - **Sample:** 100 guideline–citation pairs from F1 guidelines with open full text: 50 involving papers in the selected designs (with GBD flagship papers excluded, §3.5) and 50 others, or all available if fewer.
  - **Coding:** each citation is coded as *background/burden*, *methods*, *evidence for a recommendation* or *other*, from the citing sentence.
  - **Reported:** the distribution by group with Wilson 95% CIs, and a blind re-code of 25% (25 pairs) after at least 14 days (intra-rater κ). At 25 per group, a 50% proportion has a 95% CI of about 31–69%, which is too wide to compare the groups, hence the larger sample.
  - **Purpose:** the result limits how strongly "cited by a guideline" can be read as practice relevance.
  - **Status, 2026-10-15:** the v2.2 sheets (25 + 25 pairs, 12-pair recode, drawn 2026-10-10) had not been coded. They were deleted on 2026-10-15. **Redrawn 2026-10-15** under the final GBD rule: 50 selected-design and 50 other pairs from a pool of 73 selected-design cited papers, plus a 25-pair recode sheet (`data/gates/g4_context_sheet.csv`, `g4_context_recode.csv`). The group key (`g4_group_key.csv`) has not been opened. **Loaded onto the coding page 2026-10-17** (`tools/g2-coder.html`, G4 tab). The page shows the cited paper, its first author and the citing guideline with a link to its PMC full text, but not the group. The recode sheet numbers its rows separately, so recode pairs are matched to the first pass by guideline and cited PMID.
  - **First pass complete, 2026-10-19** (14:21 UTC). All 100 pairs were coded by the author; the codes are locked and hidden from the coder. A sealed backup is in `data/gates/sealed/g4_first_pass_codes.csv.gz` (sha256 of the uncompressed CSV: e695971119482b2bf6cd3485973796870b018ea76b6a897080bc8ad30f054ec4). It is not opened or summarised, and the group key is not opened, until the recode is done. **Blind recode** of 25 pairs opens on 2026-11-02. The candidate pool is 939 F1 guidelines first published 2015–2019 with PMC full text: 93,272 citation pairs and 80,315 unique cited papers.
  - **Descriptive note:** 105 of the 80,315 cited papers (0.13%) use a selected design (v2.2 query, GBD flagship papers included). This is **not** evidence that these designs are under-cited. Their share of all PubMed records was itself small when most of these papers were published (0.04% in 2010, 0.08% in 2015). The comparison that counts is the within-cohort analysis in secondary objective 3.

## 6. Statistical analysis

**P1 (absolute numerator).** Log-linear regression of the (coverage-weighted) number of unique guideline-cited papers per cohort, 2008–2020: log P1_Y = α + g₁·(Y − 2008). The same model is fitted to |D_Y|, giving growth g_D, and doubling times are reported.
- Estimand for H2: g₁ − g_D, the annual growth of P1 minus that of D, with a 95% CI from a moving-block bootstrap of cohort years (block length 3, 999 replicates, both series resampled together).
- **H2 is supported if g₁ − g_D < 0 with a 95% CI excluding 0.**
- Segmented versions of this model are used for the breakpoint analysis (secondary analysis 1).

**P2 (time to first citation).** Discrete-time hazard model fitted to the life-table counts: logit h(a, Y) = f(a) + β·(Y − 2008), with f a flexible function of age. Estimand: β, the annual change in the log-odds of first citation per year of age at risk. Check the proportional-hazards assumption with an age × cohort interaction. Uncertainty from a cohort-level block bootstrap. Interpret effect sizes, not p-values: denominators run to millions.

**Decision rule across the co-primary outcomes.** Dilution and absolute yield are separate questions, so they are labelled separately.
- **Dilution** is decided by P2 alone. The literature is described as diluted if β < 0 with a 95% CI excluding 0.
- **Absolute yield** is described by P1's growth: rising, flat or falling, with its CI. P1's growth is reported next to the growth of |D_Y|.
- The result is the cell of this table that applies:

| | P1 rising | P1 flat or falling |
|---|---|---|
| **β < 0** | Diluted, with a growing absolute yield | Diluted, with a stagnant or shrinking yield |
| **β ≈ 0 or > 0** | Not diluted; yield growing | Not diluted (unexpected; investigate the decomposition) |

A rising search burden for clinicians and guideline developers is a *consequence* of dilution, not an alternative to it, and it is discussed as such. Neither primary outcome is adjusted for the other. The decomposition (secondary analysis 2) is reported next to this table in the main text, so readers can judge whether dilution reflects a fixed guideline citation capacity rather than a change in the research itself.

**Secondary analyses.**
1. **Breakpoints.** Continuous segmented regression on log P1 and on the cohort-specific 5-year cumulative incidence: one break estimated from the data, then a two-break test, with p-values from a block bootstrap under the one-break null. This is the existing, simulation-calibrated method.
2. **Decomposition.** Cited papers = guidelines × references per guideline × share of references to cohort Y within 5 years. Report the trend in each factor in the main text. This tests whether any decline is simply guideline capacity: if capacity is fixed, P2 must fall as D grows, even if the research is unchanged.
3. **Selected designs compared with the rest.**
   - **Model.** The P2 discrete-time hazard model with an added design-group term and a group × cohort interaction:
     logit h(a, Y, g) = f(a) + β·(Y − 2008) + γ·g + δ₁·g·(Y − 2008) + δ₂·g·max(0, Y − 2018),
     where *g* = 1 for selected-design papers (GBD flagship papers excluded, §3.5) and 0 for all other papers in D.
     - The life-table framework handles censoring, so all cohorts 2008–2024 contribute. Cohorts after 2020 enter on their 1–4 years of follow-up instead of being dropped.
     - **Estimands:**
       - γ, the log odds ratio of first citation for selected-design papers in the 2008 cohort;
       - δ₁, the annual change in that ratio before 2018;
       - δ₁ + δ₂, the annual change from 2018.
   - **The 2018 hinge** is pre-specified from the exploratory v1 breakpoint in the ratio of selected-design papers to trial and guideline papers (§7). It is disclosed as data-informed, and no other hinge year is tested.
   - **Equal-follow-up sensitivity.** The 3-year cumulative incidence ratio (selected designs ÷ rest) for cohorts 2008–2022, so post-2018 cohorts are compared with earlier ones on the same follow-up. The 5-year ratio for cohorts 2008–2020 is a second sensitivity.
   - **Descriptive breakdown by design.** Counts of papers, guideline-cited papers and 3-year cumulative incidence for each of the six designs, by cohort era (2008–2017, 2018–2024), in the supplement. These are not tested; inference stays on the pooled group.
   - **No direction assumed.** The descriptive G4 count (§5) cannot tell whether these designs are cited more or less often than other research. This analysis is what answers that.
4. **Hypothesis H3.** A break fixed at 2022, tested on top of the best-fitting single break, in two series:
   - **(a) Selected-design share.** The annual share of D that uses a selected design, fitted by the continuous segmented log-linear regression of secondary analysis 1, with one estimated break plus a hinge fixed at 2022. The p-value comes from a block bootstrap under the one-break null.
   - **(b) The P2 cohort trend.** The P2 hazard model with two hinge terms: one at the break estimated for the 5-year cumulative incidence in secondary analysis 1, and one fixed at 2022, giving logit h(a, Y) = f(a) + β·(Y − 2008) + ψ·max(0, Y − τ̂) + θ·max(0, Y − 2022). The estimand is θ, with a cohort-level bootstrap 95% CI.
   - H3 is supported if either (a) or (b) shows a 2022 change: the bootstrap p < 0.05 in (a), or the 95% CI for θ excluding 0 in (b).
   - The post-2022 cohorts (2023–2024) have only 1–2 years of follow-up, so (b) has little power. This is stated in advance.
5. **Early signal.** One- and two-year cumulative incidence for 2015–2024 cohorts, descriptive only. Selected-design cohorts after 2020 are analysed formally in secondary analysis 3, not only here.

**Sensitivity analyses (pre-specified):**
- denominators D-Humans, D-all and D-journals (§3.2);
- headline age 3 years (8 years is shown in the main results, §3.3);
- unweighted coverage (§3.4), and, if the coverage audit calls for it, journals with stable coverage;
- excluding the 2020–21 COVID cohorts;
- publication date `[dp]` replaced by entry date `[edat]` throughout;
- F3 (NICE) trend agreement;
- an F1-versus-F2 comparison, particularly for 2022–2023.

**Multiplicity:** two co-primary outcomes with the decision rule above. Everything else is labelled secondary or sensitivity, and none is used to claim "significance".

## 7. Relationship to prior exploratory work

The v1 analyses (`data/processed/*_dp.csv`) compared publication-type strata (RCT, Phase III and guideline types) against the selected secondary-analysis designs. The guideline-citation data have not yet been extracted, so this protocol is fixed before the primary outcome data are seen. The v1 results will be disclosed as exploratory: the ratio of selected-design papers to trial and guideline papers broke in 2011 and 2018, and a break fixed at 2022 was not supported (p = 0.51; p = 0.36 using entry date).

## 8. Limitations anticipated

- Citation by a guideline is a proxy for practice relevance, not a measure of practice change. Guidelines also cite burden-of-disease, methods and background papers, and negative evidence. G4 quantifies this in a pilot of 100 pairs.
- F1 depends on NLM publication-type tagging. Practice Guideline records fell about 20% in 2022 (1,555 → 1,239) and recovered in 2024 (1,917), alongside dips in other publication types (RCT 28,455 → 25,620 in 2023). The cause is not established; changes in NLM indexing practice are a plausible explanation that I have not verified. F2 is the guard against this.
- MeSH-based filters drift (§3.2), which is why the primary denominator avoids MeSH.
- iCite covers citations between PubMed-indexed documents. It will miss citations from guidelines not indexed in PubMed. **I do not have access to Overton**, the usual database for policy and guideline citations, so F3 (NICE) is used to estimate the undercount. Free alternatives were not assessed.
- iCite reference coverage varies by journal and language, and the frame favours English-language guidance indexed in PubMed. The coverage audit (§5) found whole journals, often non-English, with no references.
- Guidelines published as NCBI Bookshelf books (WHO, NICE and others; 4.1% of F1 records) can never have iCite references, so they contribute no citations. NICE is partly recovered through F3. WHO guidance is not, which under-represents international public-health guidance.
- Guideline development takes years, but I have not found a general source for its duration. Published citation delays (UK Obstetric Surveillance System, about 221 weeks; a policy research unit, about 183 weeks) come from single programmes in the UK. The Kaplan–Meier design is meant to avoid relying on a fixed window.
- Single-author coding: validation measures intra-rater, not inter-rater, reliability.
- The study is ecological, so no causal attribution is possible, including to generative AI or to any of the candidate drivers in §2.
- Right-censoring limits conclusions about cohorts from about 2020 onward.
- The window is 2008 onward, so the study cannot describe change before 2008. With 13 complete P1 cohorts (2008–2020), breakpoint estimates will be imprecise.
- iCite reference coverage rises after 2008. The primary analysis weights by inverse coverage and the unweighted analysis is a sensitivity, but neither removes bias if guidelines missing references cite differently. The coverage audit (§3.4) tests the most likely reason they would, paywalled full text.

## 9. Outputs

- Figure 1: denominator compared with guideline-cited papers (log scale).
- Figure 2: Kaplan–Meier cumulative incidence curves by cohort.
- Figure 3: P1 (5-year and 8-year windows) and P2 trends with segmented fits.
- Figure 4: decomposition.
- Figure 5: selected designs compared with the rest: the cohort-specific odds ratio of first citation from the interaction model, with the 2018 hinge, and the 3-year cumulative incidence ratio by cohort.
- Table 1: growth rates and doubling times.
- Table 2: breakpoint models and the H3 test.
- Table 3: the decision-rule table (§6) with the decomposition.
- Supplementary material: named-body list for F2 with its recall test, the GBD exclusion string and its precision check, eligibility validation, coverage audit, citation-context pilot, NICE pilot, FDA context series.
- Code and data are archived with a DOI. The protocol is registered on OSF before any guideline-citation data are extracted.

## 10. Work plan

1. **Before freezing (all done 2026-10-15):**
   - fix the F2 named-body list and run its recall test;
   - fix and test the GBD exclusion string, and report the guideline-cited selected-design papers by design;
   - redraw the G4 sample;
   - run the coverage audit;
   - fix the codebooks.

   Then register on OSF, with this protocol, the codebooks, the F2 body list and reference set, and a statement of prior knowledge of the data.
2. **After registration, run the remaining gates:**
   - code G2 (F1, 200 + 50 records);
   - draw and code the F2 eligibility sample (100 records);
   - code G4 (100 + 25 pairs), with each recode at least 14 days after its first pass;
   - build and run G3 (NICE).
3. Extract the frames, references and cited-paper membership of D.
   - **Done 2026-10-19** (`scripts/14_extract.py`; snapshots in `data/raw/extract/`, with queries and timestamps in `provenance.json`). No analysis has been run; analysis waits for the G2 and G4 recodes.
     - **Frames:** F1 24,052 and F2 7,995 records matching 2008–2025 by `[dp]` or `[edat]`, 28,848 unique.
     - **References:** 27,774 guidelines are in iCite and 23,673 have references. They cite 1,010,117 unique PMIDs.
     - **Membership:** every cited PMID has its earliest `[dp]` and `[edat]` year (2008–2025) and its membership of D, D-Humans, D-all and the selected designs, from History-server intersections.
     - **Denominators:** yearly counts were checked against the pilot (D 2015 = 1,143,108, identical).
     - **NCBI outage:** NCBI returned intermittent 500/502 errors during the run. Every request succeeded on retry, and re-querying five flagged batches reproduced their saved results exactly.
     - **D-journals built 2026-10-20** (`scripts/15_d_journals.py` → `data/processed/d_journals_set.csv`, `d_journals_counts.csv`).
       - **Journal set:** 5,452 journals, defined by the 265,511 papers cited by the 6,968 frame guidelines first published 2008–2012.
       - **Matching:** journals are matched by MEDLINE title abbreviation, which equals iCite's journal field in a check of 200 cited papers. All 100 sampled journals retrieve D records.
       - **Share of D in these journals:** 80% in 2008 and 48% in 2025 (`[dp]`). This reflects journals launched after 2012 and is reported by cohort, as pre-specified.
     - **FDA approvals series extracted 2026-10-20** (`scripts/16_fda_approvals.py` → `data/processed/fda_approvals.csv`). Source: the Drugs@FDA data files, sha256 519f1166…f852 (recorded in the CSV). This is a descriptive context series only, under the pre-specified definition: original NME approvals plus original BLAs, 2008–2025.
       - **Limitation:** Drugs@FDA does not flag biosimilars on original BLAs, so this definition includes them and runs above CDER's published novel-approval lists, increasingly after about 2017.
       - **Before publication:** the series is to be checked against CDER's annual novel-approval reports. Any departure from the pre-specified definition will be reported as a deviation.
4. Run the primary and secondary analyses.
5. Run the sensitivity analyses.
6. Write the manuscript, reusing the v1 outline sections where they still apply.

## 11. Open decisions for the author

All decisions listed in earlier drafts were settled on 2026-10-15:
- **Named bodies for F2:** the 31-body list in `manuscript/f2_named_bodies.csv` is approved, with the tightened WHO rule (§3.1).
- **Second coder:** none. G2 and G4 report intra-rater reliability only (§8).
- **Thresholds:** F2 recall ≥ 0.80 is confirmed (achieved 0.92). The GBD exclusion is fixed as in §3.5.

## 12. Transparency and AI disclosure

This is a sole-author preprint. AI assistance (Claude, plus an external review by Gemini) was used for code, query design, literature verification and drafting. This will be disclosed in the Methods and the Acknowledgements, and the code will be archived with the data. All numbers, citations and claims are verified by the author against the primary sources and the pipeline outputs.
