#!/usr/bin/env python3
"""G2: draw the stratified eligibility sample and write blank coding sheets.

Frame: F1 guidelines 2008-2025 with >=1 iCite reference (protocol 3.4), each assigned to its
earliest matching [dp] year (protocol 3.1). Reads data/raw/f1_guidelines_icite.jsonl.
Writes data/gates/g2_coding_sheet.csv and data/gates/g2_recode_sheet.csv (code the recode
sheet at least 14 days later, blind). Codebook: manuscript/eligibility_codebook.md.
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pubinfl import cache, gates, ncbi  # noqa: E402

CACHE = ROOT / "data" / "raw" / "f1_guidelines_icite.jsonl"
OUT_DIR = ROOT / "data" / "gates"
BLANK = ["eligible", "issuing_body_type", "notes"]


def earliest_year_rows():
    first = {}
    for r in cache.read_jsonl(CACHE):
        if r["pmid"] not in first or r["year"] < first[r["pmid"]]["year"]:
            first[r["pmid"]] = r
    return first


def main() -> None:
    sleep_s = ncbi.configure_entrez()
    rows = earliest_year_rows()
    frame = pd.DataFrame([{"pmid": p, "year": r["year"]} for p, r in rows.items()
                          if r["year"] >= 2008 and r["references"]])
    sample = gates.stratified_sample(frame)
    meta = ncbi.fetch_summaries(sample["pmid"].tolist(), sleep_s=sleep_s)
    get = lambda p, k: meta.get(p, {}).get(k, "")
    sheet = sample.assign(
        journal=sample["pmid"].map(lambda p: get(p, "journal")),
        title=sample["pmid"].map(lambda p: get(p, "title")),
        collective_authors=sample["pmid"].map(lambda p: get(p, "collective_authors")),
        first_author=sample["pmid"].map(lambda p: get(p, "first_author")),
        pubmed_url=sample["pmid"].map(lambda p: f"https://pubmed.ncbi.nlm.nih.gov/{p}/"),
        **{c: "" for c in BLANK},
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    first, recode = OUT_DIR / "g2_coding_sheet.csv", OUT_DIR / "g2_recode_sheet.csv"
    for path in (first, recode):
        if path.exists():
            sys.exit(f"{path} exists - refusing to overwrite coded work")
    sheet.to_csv(first, index=False)
    gates.recode_subset(sheet).assign(**{c: "" for c in BLANK}).to_csv(recode, index=False)
    print(f"Frame: {len(frame)} guidelines. Wrote {first} ({len(sheet)} rows) and {recode}")
    print(sheet["stratum"].value_counts().to_string())


if __name__ == "__main__":
    main()
