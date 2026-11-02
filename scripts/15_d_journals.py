#!/usr/bin/env python3
"""Sensitivity denominator D-journals (protocol §3.2).

The journal set is every journal that published at least one paper cited by a frame guideline
(F1 or F2) first published 2008-2012 by [dp]. It is fixed from those early guidelines only. D-journals
is D restricted to these journals; its yearly size is counted under [dp] and [edat], 2008-2025.
Journals are matched by MEDLINE title abbreviation ([ta]), which equals iCite's `journal` field
(checked on 200 cited papers, 2026-10-20).

Usage: NCBI_EMAIL=you@example.com python scripts/15_d_journals.py [--overlaps]
Reads data/raw/extract/. Writes data/processed/d_journals_set.csv and d_journals_counts.csv.
--overlaps instead counts, from the saved journal set, records matching both year Y-1 and Y [dp], so
the yearly counts can be de-duplicated to the earliest year (writes d_journals_overlaps.csv).
"""
import random
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pubinfl import cache, ncbi  # noqa: E402
from Bio import Entrez  # noqa: E402

EXTRACT = ROOT / "data" / "raw" / "extract"
OUT_SET = ROOT / "data" / "processed" / "d_journals_set.csv"
OUT_COUNTS = ROOT / "data" / "processed" / "d_journals_counts.csv"
SET_YEARS = range(2008, 2013)
YEARS = range(2008, 2026)
CHUNK = 100


def esearch_count(term: str, sleep_s: float) -> int:
    def _s():
        with Entrez.esearch(db="pubmed", term=term, retmax=0) as h:
            return Entrez.read(h)
    n = int(ncbi.with_retries(_s)["Count"])
    time.sleep(sleep_s)
    return n


def ta(j: str) -> str:
    return '"' + j.replace('"', "") + '"[ta]'


def overlaps(sleep_s: float) -> None:
    js = pd.read_csv(OUT_SET)["journal"].tolist()
    chunks = [js[i:i + CHUNK] for i in range(0, len(js), CHUNK)]
    rows = []
    for y in YEARS:
        n = sum(esearch_count(f"({' OR '.join(map(ta, ch))}) AND ({ncbi.D_QUERY}) AND {y - 1}[dp] AND {y}[dp]", sleep_s)
                for ch in chunks)
        rows.append({"later_year": y, "overlap": n})
        print(f"overlap {y - 1}-{y}: {n}", flush=True)
    pd.DataFrame(rows).to_csv(OUT_COUNTS.with_name("d_journals_overlaps.csv"), index=False)


def main() -> None:
    sleep_s = ncbi.configure_entrez()
    if "--overlaps" in sys.argv:
        overlaps(sleep_s)
        return
    early = {r["pmid"] for f in ("f1", "f2") for r in cache.read_jsonl(EXTRACT / f"frame_{f}.jsonl")
             if r["dp_year"] in SET_YEARS}
    cited = {int(c) for g in cache.read_jsonl(EXTRACT / "guidelines.jsonl") if g["pmid"] in early
             for c in g["references"]}
    journal = {r["pmid"]: r["journal"] for r in cache.read_jsonl(EXTRACT / "cited.jsonl")}
    js = pd.Series([journal.get(p, "") for p in cited])
    js = js[js != ""].value_counts().rename_axis("journal").reset_index(name="n_cited_2008_2012")
    print(f"{len(early)} frame guidelines 2008-2012 cite {len(cited)} papers in {len(js)} journals")

    # Each journal string must retrieve D records on its own; check a random sample.
    sample = random.Random(20221130).sample(list(js["journal"]), min(100, len(js)))
    empty = [j for j in sample if esearch_count(f"{ta(j)} AND ({ncbi.D_QUERY})", sleep_s) == 0]
    print(f"[ta] check: {len(sample) - len(empty)}/{len(sample)} sampled journals retrieve D records; empty: {empty}")

    chunks = [list(js["journal"][i:i + CHUNK]) for i in range(0, len(js), CHUNK)]
    rows = []
    for field in ("dp", "edat"):
        for y in YEARS:
            n = sum(esearch_count(f"({' OR '.join(map(ta, ch))}) AND ({ncbi.D_QUERY}) AND {y}[{field}]", sleep_s)
                    for ch in chunks)
            rows.append({"date_field": field, "year": y, "count": n})
            print(f"{field} {y}: {n}", flush=True)
    OUT_SET.parent.mkdir(parents=True, exist_ok=True)
    js.to_csv(OUT_SET, index=False)
    pd.DataFrame(rows).to_csv(OUT_COUNTS, index=False)


if __name__ == "__main__":
    main()
