# Is guideline-cited evidence keeping pace with the biomedical literature?

A pre-registered cohort analysis, 2008–2025.

**Jordan Fulcher**, independent researcher, UK · ORCID [0009-0001-6294-1127](https://orcid.org/0009-0001-6294-1127) · jfulcherresearch@gmail.com

**Pre-registration:** OSF, 16 October 2026, [doi:10.17605/OSF.IO/VN9BQ](https://doi.org/10.17605/OSF.IO/VN9BQ). The final protocol is in the public OSF project [osf.io/hpg6f](https://osf.io/hpg6f) and in [`manuscript/protocol.md`](manuscript/protocol.md).

**Status (October 2026):**

| Step | State |
|---|---|
| Pre-registration | Done |
| Feasibility gates G1–G4 | G1 and G3 complete. G2 and G4 first passes are coded and sealed; blind recodes are due in November 2026 |
| Data extraction | Complete |
| Analysis | Not started. It begins after the gates are scored |

## The question

The biomedical literature keeps growing. Does the evidence that clinical practice guidelines actually cite grow with it?

The study follows cohorts of research papers (the denominator D) and asks how many are cited by a clinical practice guideline, and how quickly. It uses two pre-specified guideline frames:
- **F1:** PubMed "Practice Guideline" records.
- **F2:** 31 named guideline bodies.

NICE guidance (F3) serves as an external check.

There are two co-primary outcomes:
- **P1:** the absolute number of guideline-cited papers per cohort, compared with the growth of D.
- **P2:** a discrete-time hazard of first guideline citation by cohort.

Hypotheses H1–H3 and research questions RQ1–RQ5 are set out in the protocol.

## Repository layout

| Path | Contents |
|---|---|
| `manuscript/protocol.md` | Full protocol, with a dated record of every decision and gate result |
| `manuscript/eligibility_codebook.md` | Codebooks for the G2 eligibility gate and the G4 citation-context gate |
| `manuscript/f2_*.csv` | Frozen F2 named-body rules, and the 50-guideline recall reference set |
| `pubinfl/` | Shared code: PubMed E-utilities, the iCite API, gate statistics |
| `scripts/01–02` | Exploratory v1 analysis of publication-type strata (superseded; see protocol §7) |
| `scripts/03–13` | Feasibility gates G1–G4, the coverage audit and the F2 checks |
| `scripts/14_extract.py` | Main extraction: frames, reference lists, cited-paper years and denominator membership |
| `scripts/15–16` | The D-journals sensitivity denominator and the FDA approvals context series |
| `data/raw/extract/` | Extraction snapshot (gzipped), with queries and timestamps in `provenance.json` |
| `data/gates/` | Gate samples, coding sheets and results |
| `data/gates/sealed/` | Sealed first-pass codes, compressed until the blind recodes are done (see that folder's README) |
| `data/processed/` | Derived tables |
| `tests/` | Offline unit tests |

## Reproducing

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export NCBI_EMAIL=you@example.com     # required by NCBI
export NCBI_API_KEY=...               # optional: 10 requests/s instead of 3
python -m pytest                      # offline tests
python scripts/14_extract.py          # re-run the main extraction (several hours; resumable)
```

PubMed and iCite change over time, so a fresh extraction will differ slightly from the committed snapshot. The analysis uses the snapshot.

## Not included

- **Abstracts** used during eligibility coding. They are publishers' text; the PMIDs needed to retrieve them are in the coding sheets.
- **The private coding interface** used for the G2 and G4 gates.
- **Working documents and correspondence.**

## AI assistance

AI tools (Anthropic's Claude) were used for code, query design, literature checks and drafting, as stated in the protocol. The author made all study decisions, did all manual coding and is responsible for the content.

## Licence

- **Code:** MIT ([`LICENSE`](LICENSE)).
- **Data, protocol and other documents:** CC BY 4.0 ([`LICENSE-DATA`](LICENSE-DATA)).
- **Third-party data:**
  - PubMed and iCite records are from the US National Library of Medicine and NIH.
  - Drugs@FDA is from the US FDA.
  - NICE reference strings are bibliographic citations taken from NICE evidence reviews.

Please cite using [`CITATION.cff`](CITATION.cff).
