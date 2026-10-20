# G2 eligibility codebook (fixed before coding, 2026-10-10)

**Inclusion rule:** a document that gives recommendations for clinical practice, is clinically authored or edited, is issued by or on behalf of a reputable national or international body (a government agency, a statutory guideline body, or a professional or scientific society), and can be cited.

Code `eligible` = **Y** only if all four hold:
1. **Recommendations:** it states recommendations for clinical care (diagnosis, treatment, prevention, management). Background reviews, position statements without recommendations, and research agendas are **N**.
2. **Clinical authorship:** the authors or editors include clinicians, or a named clinical committee or panel. Purely administrative or legal documents are **N**.
3. **Issuing body:** it names a national or international society, government agency or guideline body, by byline, collective author, or an "on behalf of" statement. Guidance from a single hospital or local department is **N**. Expert-consensus papers with no issuing body are **N**.
4. **Citable:** it is published with a stable identifier (it qualifies if it is in PubMed).

`issuing_body_type`: `government` | `statutory_guideline_body` | `national_society` | `international_society` | `other` | `none`.

Code from the title, abstract, byline and journal. Open the full text only if those don't settle it, and say so in `notes`.

**Recode sheet:** code it at least 14 days after finishing the first pass, without looking at the first-pass codes.

**Sample:** 200 F1 guidelines with at least one iCite reference (the analysis set, protocol §3.4), stratified 2008–2013 / 2014–2019 / 2020–2025, seed 20221130.

**F2 sample:** 100 F2 records (named-body frame) with at least one iCite reference, excluding records in the F1 sample, stratified the same way (34/33/33), seed 20221130. The recode sheet has 25 records. The same rules apply.

---

# G4 citation-context codebook (fixed before coding; rules 2026-10-10, sample updated 2026-10-15)

**Sample (protocol v2.3.2):** 100 guideline–citation pairs from F1 guidelines first published 2015–2019 with a PMC full text: 50 whose cited paper uses a selected design (GBD consortium papers excluded) and 50 others, seed 20221130. The recode sheet has 25 pairs.

For each guideline–citation pair, open the guideline full text (the `guideline_url` column), find where the cited paper is cited, and code `context` from the citing sentence:
- **background**: disease burden, epidemiology, prevalence, cost, or general context.
- **methods**: guideline methods, grading systems, search methods, definitions or tools.
- **evidence**: evidence offered for or against a specific recommendation, including tables of evidence behind a recommendation.
- **other**: anything else, including citations that can't be located (say so in `notes`).

If a paper is cited more than once, code the most decision-relevant use (evidence > methods > background > other), and note the others.

**Blinding:** the sheets don't show whether a cited paper is a selected-design paper, and rows are shuffled. The group is in `data/gates/g4_group_key.csv`; don't open it until all G4 coding (including the recode) is finished. Some cited titles will still reveal the design (e.g. "Mendelian randomization"); code from the citing sentence regardless.

**Recode sheet (25 pairs):** at least 14 days later, blind to the first pass.
