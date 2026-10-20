#!/usr/bin/env python3
"""Gate G1: iCite reference coverage of the F1 guideline frame, 2000-2025.

Usage: NCBI_EMAIL=you@example.com python scripts/03_gate_g1_coverage.py [--refresh]
Writes data/raw/f1_guidelines_icite.jsonl (cache) and data/processed/gate_g1_coverage.csv.
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pubinfl import cache, gates, icite, ncbi  # noqa: E402

CACHE = ROOT / "data" / "raw" / "f1_guidelines_icite.jsonl"
OUT = ROOT / "data" / "processed" / "gate_g1_coverage.csv"
YEARS = range(2000, 2026)


def build_cache(sleep_s: float) -> None:
    frame = []
    for y in YEARS:
        ids = ncbi.search_pmids(ncbi.F1_QUERY, y, sleep_s=sleep_s)
        frame += [(p, y) for p in ids]
        print(f"{y}: {len(ids)} F1 guidelines")
    recs = icite.fetch_icite([p for p, _ in frame], ["pmid", "year", "references"])
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    with CACHE.open("w") as fh:
        for p, y in frame:
            r = recs.get(p)
            fh.write(json.dumps({"pmid": p, "year": y, "in_icite": r is not None,
                                 "references": (r or {}).get("references") or []}) + "\n")
    cache.write_gz_copy(CACHE)  # the .gz copy is committed so the snapshot travels with the repo


def load_cache():
    rows = cache.read_jsonl(CACHE)
    frame = pd.DataFrame([{"pmid": r["pmid"], "year": r["year"]} for r in rows])
    recs = {r["pmid"]: {"references": r["references"]} for r in rows if r["in_icite"]}
    return frame, recs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="re-download even if the cache exists")
    args = ap.parse_args()
    sleep_s = ncbi.configure_entrez()
    if args.refresh or not cache.cache_exists(CACHE):
        build_cache(sleep_s)
    frame, recs = load_cache()
    cov = gates.coverage_by_year(frame, recs)
    cov["query"] = ncbi.F1_QUERY
    src = CACHE if CACHE.exists() else cache.gz_path(CACHE)
    cov["retrieved_utc"] = datetime.fromtimestamp(src.stat().st_mtime, timezone.utc).isoformat(timespec="seconds")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    cov.to_csv(OUT, index=False)
    passed, failing = gates.gate_g1(cov)
    print(cov[["year", "n_guidelines", "n_with_refs", "coverage", "median_refs"]].round(3).to_string(index=False))
    print(f"\nG1 {'PASS' if passed else 'FAIL'}" + ("" if passed else f" - years below 0.70: {failing}"))


if __name__ == "__main__":
    main()
