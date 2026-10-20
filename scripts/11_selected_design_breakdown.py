#!/usr/bin/env python3
"""Per-design breakdown of guideline-cited selected-design papers in the G4 pool (protocol §3.5).

Pool: papers cited by F1 guidelines first published 2015-2019 with a PMC full text (as in 07).
Usage: NCBI_EMAIL=you@example.com python scripts/11_selected_design_breakdown.py
Writes data/processed/selected_design_breakdown.csv (counts only; no citation-context data).
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pubinfl import cache, ncbi  # noqa: E402

OUT = ROOT / "data" / "processed" / "selected_design_breakdown.csv"
DESIGNS = {
    "two_sample_mr": '("two-sample"[tiab] OR "two sample"[tiab]) AND Mendelian[tiab] AND (randomization[tiab] OR randomisation[tiab])',
    "bibliometric": "bibliometric*[tiab] OR scientometric*[tiab]",
    "nhanes_cross_sectional": '(NHANES[tiab] OR "National Health and Nutrition Examination Survey"[tiab]) AND ("cross-sectional"[tiab] OR "cross sectional"[tiab])',
    "gbd_reanalysis": f'"Global Burden of Disease"[tiab] NOT {ncbi.GBD_CONSORTIUM_QUERY}',
    "network_pharmacology": '"network pharmacology"[tiab]',
    "faers_disproportionality": '(FAERS[tiab] OR "Adverse Event Reporting System"[tiab]) AND disproportionality[tiab]',
}


def main() -> None:
    sleep_s = ncbi.configure_entrez()
    first = {}
    for r in cache.read_jsonl(ROOT / "data" / "raw" / "f1_guidelines_icite.jsonl"):
        if r["pmid"] not in first or r["year"] < first[r["pmid"]]["year"]:
            first[r["pmid"]] = r
    rows = [r for r in first.values() if 2015 <= r["year"] <= 2019 and r["references"]]
    meta = {m["pmid"]: m for m in cache.read_jsonl(ROOT / "data" / "raw" / "f1_guideline_summaries.jsonl")}
    open_ids = {r["pmid"] for r in rows if meta.get(r["pmid"], {}).get("pmcid")}
    cited = sorted({c for r in rows if r["pmid"] in open_ids for c in r["references"]})
    print(f"{len(open_ids)} open guidelines; {len(cited)} cited papers")
    hits = {k: ncbi.search_subset(q, cited, sleep_s=sleep_s) for k, q in DESIGNS.items()}
    union = set().union(*hits.values())
    out = pd.DataFrame([{"design": k, "n_cited_papers": len(v)} for k, v in hits.items()]
                       + [{"design": "any (pooled, de-duplicated)", "n_cited_papers": len(union)}])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
