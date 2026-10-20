#!/usr/bin/env python3
"""F2 draft check (protocol §3.1): resolve the candidate reference set, count F2 records per
named body, and measure F2 recall against the reference set.

Usage: NCBI_EMAIL=you@example.com python scripts/10_f2_draft_check.py
Reads manuscript/f2_named_bodies.csv and manuscript/f2_reference_set_candidates.csv (pinned PMIDs).
Writes data/processed/f2_reference_set.csv and data/processed/f2_body_counts.csv.
"""
import sys
import time
from pathlib import Path

import pandas as pd
from Bio import Entrez

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pubinfl import ncbi  # noqa: E402

BODIES = ROOT / "manuscript" / "f2_named_bodies.csv"
CANDIDATES = ROOT / "manuscript" / "f2_reference_set_candidates.csv"
OUT_REF = ROOT / "data" / "processed" / "f2_reference_set.csv"
OUT_COUNTS = ROOT / "data" / "processed" / "f2_body_counts.csv"

WINDOW = "2008:2025[dp]"
f2_body_query = ncbi.f2_body_query


def count(term: str, sleep_s: float) -> tuple:
    def _search(t):
        with Entrez.esearch(db="pubmed", term=t, retmax=20) as h:
            return Entrez.read(h)
    res = ncbi.with_retries(_search, term)
    time.sleep(sleep_s)
    return int(res["Count"]), [int(i) for i in res["IdList"]]


def main() -> None:
    sleep_s = ncbi.configure_entrez()
    bodies = pd.read_csv(BODIES)
    cands = pd.read_csv(CANDIDATES)

    # 1. Reference set: PMIDs pinned by hand to the primary full-guideline record (not an executive
    #    summary, translation or co-publication); titles were chosen independently of the F2 rules.
    ref = cands.rename(columns={"search": "chosen_title"})
    meta = ncbi.fetch_summaries([int(p) for p in ref["pmid"].dropna()], sleep_s=sleep_s)
    ref["title"] = ref["pmid"].map(lambda p: meta.get(int(p), {}).get("title", "") if pd.notna(p) else "")
    ref["journal"] = ref["pmid"].map(lambda p: meta.get(int(p), {}).get("journal", "") if pd.notna(p) else "")
    resolved = [int(p) for p in ref["pmid"].dropna()]

    # 2. Per-body counts and 3. recall: which reference PMIDs does each body's F2 rule retrieve?
    rows, hit = [], set()
    for b in bodies.itertuples():
        q = f2_body_query(b.match_rule)
        n, _ = count(f"{q} AND {WINDOW}", sleep_s)
        n_pg, _ = count(f'{q} AND {WINDOW} AND "Practice Guideline"[pt]', sleep_s)
        got = ncbi.search_subset(q, resolved, sleep_s=sleep_s)
        hit |= got
        own = set(int(p) for p in ref.loc[(ref["body_id"] == b.body_id), "pmid"].dropna())
        rows.append({"body_id": b.body_id, "body": b.body, "n_2008_2025": n,
                     "n_also_practice_guideline_pt": n_pg,
                     "ref_set_n": len(own), "ref_set_retrieved": len(own & got)})
    counts = pd.DataFrame(rows)
    ref["retrieved_by_f2"] = ref["pmid"].map(lambda p: pd.notna(p) and int(p) in hit)

    OUT_REF.parent.mkdir(parents=True, exist_ok=True)
    ref.to_csv(OUT_REF, index=False)
    counts.to_csv(OUT_COUNTS, index=False)
    print(counts.to_string(index=False))
    print(f"\nReference set: {len(resolved)} guidelines")
    print(f"F2 recall: {ref['retrieved_by_f2'].sum()} / {len(resolved)} = "
          f"{ref['retrieved_by_f2'].sum() / max(len(resolved), 1):.2f}")
    print(ref.loc[ref["pmid"].notna() & ~ref["retrieved_by_f2"], ["body_id", "pmid", "journal", "title"]].to_string(index=False))


if __name__ == "__main__":
    main()
