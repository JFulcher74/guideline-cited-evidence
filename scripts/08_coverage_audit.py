#!/usr/bin/env python3
"""Coverage audit (protocol v2.3, §3.4): is iCite reference coverage of F1 guidelines lower
for guidelines without a PubMed Central full text (a proxy for paywalled guidelines)?

NCBI Bookshelf records (full guidelines published as books, e.g. WHO and NICE) have no journal in
esummary and are never in iCite, which covers journal articles. They are reported separately and
excluded from the full-text comparison (all 975 such records were confirmed as Bookshelf on 2026-10-15).

Usage: NCBI_EMAIL=you@example.com python scripts/08_coverage_audit.py [--refresh]
Reads the iCite cache from 03. Caches esummary metadata (journal, PMC id) to
data/raw/f1_guideline_summaries.jsonl (gzipped copy committed). Writes
data/processed/coverage_audit_by_year_pmc.csv and data/processed/coverage_audit_by_journal.csv.
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pubinfl import cache, gates, ncbi  # noqa: E402

ICITE = ROOT / "data" / "raw" / "f1_guidelines_icite.jsonl"
SUMMARIES = ROOT / "data" / "raw" / "f1_guideline_summaries.jsonl"
OUT_YEAR = ROOT / "data" / "processed" / "coverage_audit_by_year_pmc.csv"
OUT_JOURNAL = ROOT / "data" / "processed" / "coverage_audit_by_journal.csv"
YEARS = (2008, 2025)
ERAS = {"2008-2012": (2008, 2012), "2013-2019": (2013, 2019), "2020-2025": (2020, 2025)}
MIN_JOURNAL_N = 50


def build_summaries(pmids, sleep_s: float) -> None:
    meta = ncbi.fetch_summaries(pmids, sleep_s=sleep_s)
    SUMMARIES.parent.mkdir(parents=True, exist_ok=True)
    with SUMMARIES.open("w") as fh:
        for p in pmids:
            m = meta.get(p, {})
            fh.write(json.dumps({"pmid": p, "journal": m.get("journal", ""), "pmcid": m.get("pmcid", "")}) + "\n")
    cache.write_gz_copy(SUMMARIES)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="re-download summaries even if cached")
    args = ap.parse_args()
    first = {}
    for r in cache.read_jsonl(ICITE):
        if r["pmid"] not in first or r["year"] < first[r["pmid"]]["year"]:
            first[r["pmid"]] = r
    rows = [r for r in first.values() if YEARS[0] <= r["year"] <= YEARS[1]]
    pmids = sorted(r["pmid"] for r in rows)
    if args.refresh or not cache.cache_exists(SUMMARIES):
        build_summaries(pmids, ncbi.configure_entrez())
    meta = {m["pmid"]: m for m in cache.read_jsonl(SUMMARIES)}
    frame = pd.DataFrame([{"pmid": r["pmid"], "year": r["year"],
                           "journal": meta.get(r["pmid"], {}).get("journal", ""),
                           "has_pmc": bool(meta.get(r["pmid"], {}).get("pmcid"))} for r in rows])
    frame["bookshelf"] = frame["journal"] == ""
    books = frame[frame["bookshelf"]]
    frame = frame[~frame["bookshelf"]]
    recs = {r["pmid"]: {"references": r["references"]} for r in rows if r["in_icite"]}

    by_year = gates.coverage_by_group(frame, recs, ["year", "has_pmc"])
    OUT_YEAR.parent.mkdir(parents=True, exist_ok=True)
    by_year.to_csv(OUT_YEAR, index=False)

    frame["era"] = frame["year"].map(lambda y: next(k for k, (a, b) in ERAS.items() if a <= y <= b))
    by_era = gates.coverage_by_group(frame, recs, ["era", "has_pmc"])
    big = frame["journal"].value_counts()
    big = big[big >= MIN_JOURNAL_N].index
    jt = gates.coverage_by_group(frame[frame["journal"].isin(big)], recs, ["journal", "era"])
    wide = jt.pivot(index="journal", columns="era", values="coverage").add_prefix("coverage_")
    sizes = frame[frame["journal"].isin(big)].groupby("journal").agg(
        n_guidelines=("pmid", "size"), share_pmc=("has_pmc", "mean"))
    by_journal = sizes.join(wide).sort_values("n_guidelines", ascending=False).reset_index()
    by_journal.to_csv(OUT_JOURNAL, index=False)

    print(f"{len(books)} Bookshelf records (no journal; never in iCite) excluded from the comparison")
    print(f"{len(frame)} F1 journal-article guidelines {YEARS[0]}-{YEARS[1]}; "
          f"{frame['has_pmc'].mean():.1%} have a PMC full text\n")
    print("Coverage by era and PMC full text:")
    print(by_era[["era", "has_pmc", "n_guidelines", "coverage", "median_refs"]].round(3).to_string(index=False))
    print(f"\n{len(by_journal)} journals with >= {MIN_JOURNAL_N} guidelines -> {OUT_JOURNAL.name}")
    print(f"Wrote {OUT_YEAR.name} and {OUT_JOURNAL.name}")


if __name__ == "__main__":
    main()
