#!/usr/bin/env python3
"""G4: sample guideline-citation pairs for citation-context coding.

Candidates: F1 guidelines first published 2015-2019 with references and a PMC full text.
Protocol v2.3: 50 selected-design and 50 other pairs (GBD flagship papers excluded from the
selected designs), 25% recode (25 pairs).
Writes data/gates/g4_context_sheet.csv (code `context` from the citing sentence in the PMC
full text), a 25% blind recode sheet, and data/gates/g4_group_key.csv. Sheets omit the
selected/other group and are shuffled, so coding is blind to group; do not open the key. Codebook: manuscript/eligibility_codebook.md (G4 part).
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
BLANK = ["context", "notes"]


def main() -> None:
    sleep_s = ncbi.configure_entrez()
    first = {}
    for r in cache.read_jsonl(CACHE):
        if r["pmid"] not in first or r["year"] < first[r["pmid"]]["year"]:
            first[r["pmid"]] = r
    rows = [r for r in first.values() if 2015 <= r["year"] <= 2019 and r["references"]]
    meta = ncbi.fetch_summaries([r["pmid"] for r in rows], sleep_s=sleep_s)
    open_ids = {p for p, m in meta.items() if m.get("pmcid")}
    pairs = pd.DataFrame([{"guideline_pmid": r["pmid"], "cited_pmid": c, "guideline_year": r["year"]}
                          for r in rows if r["pmid"] in open_ids for c in r["references"]])
    print(f"{len(open_ids)} guidelines with PMC full text; {len(pairs)} citation pairs; "
          f"{pairs['cited_pmid'].nunique()} unique cited papers")
    selected = ncbi.search_subset(ncbi.SELECTED_DESIGNS_QUERY, pairs["cited_pmid"].unique(), sleep_s=sleep_s)
    print(f"{len(selected)} cited papers use a selected design")
    sample = gates.sample_citation_pairs(pairs, selected)
    sample["guideline_pmcid"] = sample["guideline_pmid"].map(lambda p: meta[p]["pmcid"])
    cited_meta = ncbi.fetch_summaries(sample["cited_pmid"].tolist(), sleep_s=sleep_s)
    sample["guideline_url"] = sample["guideline_pmcid"].map(lambda p: f"https://pmc.ncbi.nlm.nih.gov/articles/{p}/")
    sample["cited_first_author"] = sample["cited_pmid"].map(lambda p: cited_meta.get(p, {}).get("first_author", ""))
    sample["cited_title"] = sample["cited_pmid"].map(lambda p: cited_meta.get(p, {}).get("title", ""))
    sample["cited_url"] = sample["cited_pmid"].map(lambda p: f"https://pubmed.ncbi.nlm.nih.gov/{p}/")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out1, out2, key = (OUT_DIR / "g4_context_sheet.csv", OUT_DIR / "g4_context_recode.csv",
                       OUT_DIR / "g4_group_key.csv")
    for path in (out1, out2, key):
        if path.exists():
            sys.exit(f"{path} exists - refusing to overwrite coded work")
    # Blind the coder to group: group goes to a separate key file, rows are shuffled.
    sample[["guideline_pmid", "cited_pmid", "group"]].to_csv(key, index=False)
    sheet = sample.drop(columns="group").assign(**{c: "" for c in BLANK})
    recode = gates.recode_subset(sheet, sort_by=["guideline_pmid", "cited_pmid"])
    for df, path in ((sheet, out1), (recode, out2)):
        df = df.sample(frac=1, random_state=gates.SEED).reset_index(drop=True)
        df.insert(0, "row_id", range(1, len(df) + 1))
        df.to_csv(path, index=False)
    print(sample["group"].value_counts().to_string())
    print(f"Wrote {out1} and {out2} (code the recode sheet at least 14 days later, blind)")


if __name__ == "__main__":
    main()
