# Guideline citation and the growth of PubMed

A pre-registered cohort study, 2008–2024.

**Jordan Fulcher**, independent researcher, UK · ORCID [0009-0001-6294-1127](https://orcid.org/0009-0001-6294-1127) · jfulcherresearch@gmail.com

**Pre-registration:** OSF, 16 October 2026, [doi:10.17605/OSF.IO/VN9BQ](https://doi.org/10.17605/OSF.IO/VN9BQ). The final protocol is in [`manuscript/protocol.md`](manuscript/protocol.md) and in the OSF project [osf.io/hpg6f](https://osf.io/hpg6f).

**Archive:** Zenodo, [doi:10.5281/zenodo.23897510](https://doi.org/10.5281/zenodo.23897510) (all versions; v1.0.0 is [doi:10.5281/zenodo.23897511](https://doi.org/10.5281/zenodo.23897511)).

**Status (November 2026):** analysis complete; manuscript prepared for journal submission. The manuscript and supplement are in [`manuscript/submission/`](manuscript/submission/).

## The question

The biomedical literature keeps growing. Does the research that clinical practice guidelines cite grow with it?

The study follows publication-year cohorts of 18.0 million PubMed research articles (2008–2024). Through NIH iCite, it links them to the reference lists of two pre-specified guideline sets:
- **F1:** PubMed "Practice Guideline" records (23,920).
- **F2:** guidelines from 31 named national and international bodies (7,943).

It asks two things: how many papers per cohort are cited by a guideline within five years, and how the probability of first guideline citation changes across cohorts.

## Main findings (see the manuscript for intervals and caveats)

- **Growth gap.** Between 2008 and 2020, research articles in PubMed grew 4.7% a year. Papers cited by a guideline within five years grew 0.6% a year (F1) and 2.7% a year (F2).
- **Falling probability of citation.**
  - The five-year probability of citation fell from 1 in 25 to 1 in 43 (F1) and from 1 in 87 to 1 in 112 (F2), comparing the 2008 and 2019 cohorts.
  - The pre-registered cohort trend was supported for F2. For F1 it was inconclusive, because of a 2022–23 gap in PubMed publication-type indexing.
- **Guideline capacity.** The number of guidelines times references per guideline grew only 0.7–2.7% a year.
- **Where the growth is.** The dilution is concentrated outside MEDLINE and outside journals that guidelines cited in 2008–2012. Restricted to MEDLINE-indexed articles (a post hoc analysis), guideline-cited papers still lagged the literature, but the cohort trend was inconclusive.

## Repository layout

| Path | Contents |
|---|---|
| `manuscript/submission/` | Manuscript, supplement and RECORD-adapted checklist (as prepared for submission) |
| `manuscript/protocol.md` | Full protocol, with a dated record of every decision and gate result |
| `manuscript/results_*.md` | Generated summaries of the primary, secondary and sensitivity analyses |
| `manuscript/eligibility_codebook.md` | Codebooks for the G2 eligibility gate and the G4 citation-context gate |
| `manuscript/f2_*.csv` | Frozen F2 named-body rules and the 50-guideline recall reference set |
| `pubinfl/` | Shared code: PubMed E-utilities, the iCite API, gate statistics, life tables and hazard models |
| `scripts/01–02` | Exploratory v1 analysis of publication-type strata (superseded; see protocol) |
| `scripts/03–13`, `17–18` | Feasibility gates G1–G4, the coverage audit and the F2 checks |
| `scripts/14_extract.py` | Main extraction: frames, reference lists, cited-paper years and denominator membership |
| `scripts/15–16` | Established-journals denominator and the FDA approvals context series |
| `scripts/19–22` | Primary, design-arm, secondary and sensitivity analyses |
| `scripts/23_figures.py` | Publication figures (`figures/main/`) |
| `scripts/24–26` | Post hoc analyses: MEDLINE-only denominator, bootstrap block length, pooled design ratios |
| `scripts/27–28` | Builds the submission copy and renumbers references |
| `data/raw/extract/` | Extraction snapshot (gzipped), with queries and timestamps in `provenance.json` |
| `data/gates/` | Gate samples, coding sheets, recodes and results |
| `data/processed/` | Derived tables behind every reported number |
| `tests/` | Offline unit tests |

## Reproducing

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m pytest                                   # offline tests
python scripts/19_primary.py                       # primary analysis from the committed snapshot
python scripts/19_primary.py --denom D_medline     # post hoc MEDLINE-only denominator
python scripts/21_secondary.py && python scripts/22_sensitivity.py
python scripts/23_figures.py
```

Re-running the extraction (`scripts/14_extract.py`, `scripts/24_medline_extract.py`) needs `NCBI_EMAIL` set; `NCBI_API_KEY` is optional. PubMed and iCite change over time, so a fresh extraction will differ slightly from the committed snapshot. The reported analysis uses the snapshot.

## Not included

- **Abstracts** used during eligibility coding. They are publishers' text; the PMIDs needed to retrieve them are in the coding sheets.
- **The private coding interface** used for the G2 and G4 gates.
- **Working documents, drafts and correspondence.**

## AI use

Claude Opus 5.5 (Anthropic) was used to support coding and to provide editing support on the manuscript. The author reviewed all outputs and takes full responsibility for the content.

## Licence

- **Code:** MIT ([`LICENSE`](LICENSE)).
- **Data, protocol, manuscript and other documents:** CC BY 4.0 ([`LICENSE-DATA`](LICENSE-DATA)).
- **Third-party data:**
  - PubMed and iCite records are from the US National Library of Medicine and NIH.
  - Drugs@FDA is from the US FDA.
  - NICE reference strings are bibliographic citations taken from NICE evidence reviews.

Please cite using [`CITATION.cff`](CITATION.cff).
