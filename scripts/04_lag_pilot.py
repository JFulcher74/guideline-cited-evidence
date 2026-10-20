#!/usr/bin/env python3
"""Citation-lag pilot: age of papers cited by 2015 F1 guidelines -> sets the headline age (protocol 3.3).

Reads data/raw/f1_guidelines_icite.jsonl (run 03 first). Guidelines matching two [dp] years
are assigned to the earlier year (protocol 3.1), so 2015 means first matched in 2015.
Writes data/processed/gate_lag_pilot_2015.csv.
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pubinfl import cache, gates, icite  # noqa: E402

CACHE = ROOT / "data" / "raw" / "f1_guidelines_icite.jsonl"
OUT = ROOT / "data" / "processed" / "gate_lag_pilot_2015.csv"
PILOT_YEAR = 2015


def main() -> None:
    first = {}
    for r in cache.read_jsonl(CACHE):
        if r["pmid"] not in first or r["year"] < first[r["pmid"]]["year"]:
            first[r["pmid"]] = r
    pilot = [r for r in first.values() if r["year"] == PILOT_YEAR and r["references"]]
    g_years = {r["pmid"]: r["year"] for r in pilot}
    refs = {r["pmid"]: r["references"] for r in pilot}
    cited = {p for rs in refs.values() for p in rs}
    print(f"{len(pilot)} guidelines from {PILOT_YEAR} with references; {len(cited)} unique cited PMIDs")
    recs = icite.fetch_icite(sorted(cited), ["pmid", "year"])
    cited_years = {p: int(r["year"]) for p, r in recs.items() if r.get("year")}
    ages, excl = gates.citation_ages(g_years, refs, cited_years)
    summ = gates.age_summary(ages) | excl | {"pilot_year": PILOT_YEAR, "n_guidelines": len(pilot)}
    summ["window_rule_headline_age"] = 5 if summ["share_le_5"] >= 0.40 else 8
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([summ]).to_csv(OUT, index=False)
    for k, v in summ.items():
        print(f"{k:>24}: {v}")


if __name__ == "__main__":
    main()
