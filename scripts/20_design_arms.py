#!/usr/bin/env python3
"""Per-design data for the descriptive breakdown in secondary analysis 3 (protocol §6).

For each of the six selected-design arms: yearly counts of D records using the design, 2008-2025 by
[dp] (with the two-year overlap, so counts can be de-duplicated to the earliest year), and which cited
selected-design papers match the arm.

Usage: NCBI_EMAIL=you@example.com python scripts/20_design_arms.py
Writes data/raw/extract/design_arm_counts.csv and data/raw/extract/design_arm_cited.csv.
"""
import sys
import time
from pathlib import Path

import pandas as pd
from Bio import Entrez

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pubinfl import ncbi  # noqa: E402

EXTRACT = ROOT / "data" / "raw" / "extract"
YEARS = range(2008, 2026)


def count(term: str, sleep_s: float) -> int:
    def _s():
        with Entrez.esearch(db="pubmed", term=term, retmax=0) as h:
            return Entrez.read(h)
    n = int(ncbi.with_retries(_s)["Count"])
    time.sleep(sleep_s)
    return n


def main() -> None:
    sleep_s = ncbi.configure_entrez()
    rows = []
    for arm, q in ncbi.SELECTED_DESIGN_ARMS.items():
        base = f"({ncbi.D_QUERY}) AND {q}"
        for y in YEARS:
            rows.append({"arm": arm, "year": y, "count": count(f"{base} AND {y}[dp]", sleep_s),
                         "overlap_with_previous": count(f"{base} AND {y - 1}[dp] AND {y}[dp]", sleep_s)})
        print(arm, sum(r["count"] for r in rows if r["arm"] == arm), flush=True)
    pd.DataFrame(rows).to_csv(EXTRACT / "design_arm_counts.csv", index=False)

    mem = pd.read_csv(EXTRACT / "cited_membership.csv.gz")
    sel = mem.loc[mem["selected"] == 1, "pmid"].tolist()
    out = pd.DataFrame({"pmid": sel})
    for arm, q in ncbi.SELECTED_DESIGN_ARMS.items():
        hits = ncbi.search_subset(q, sel, sleep_s=sleep_s)
        out[arm] = out["pmid"].isin(hits).astype(int)
    out.to_csv(EXTRACT / "design_arm_cited.csv", index=False)
    print(out.drop(columns="pmid").sum().to_string())


if __name__ == "__main__":
    main()
