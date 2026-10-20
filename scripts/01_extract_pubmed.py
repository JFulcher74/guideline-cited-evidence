#!/usr/bin/env python3
"""Extract annual PubMed publication counts (1950-2025) for three strata.

Strata (all exclude preprints: NOT preprint[pt])
  total        every PubMed record dated in the year
  high_signal  RCT / Phase III trial / Practice Guideline publication types
  high_volume  a pre-specified set of secondary-analysis designs that published
               sources describe as produced in high volume with methodological
               concerns (see SECONDARY_ANALYSIS_DESIGNS). Reported as ONE stratum.
  loo_<design> the set with one design left out - used only for the
               leave-one-out sensitivity analysis, never reported on its own.

Usage
  export NCBI_EMAIL=you@example.com        # required by NCBI
  export NCBI_API_KEY=...                  # optional, raises limit to 10 req/s
  python scripts/01_extract_pubmed.py [--date-field dp|edat] [--start 1950] [--end 2025]
"""
import argparse
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from Bio import Entrez

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"

SLEEP_NO_KEY = 0.35  # NCBI limit: 3 requests/s without an API key
SLEEP_WITH_KEY = 0.11  # 10 requests/s with a key
MAX_RETRIES = 5

EXCLUDE = "preprint[pt]"

HIGH_SIGNAL = (
    '("Randomized Controlled Trial"[pt] OR "Clinical Trial, Phase III"[pt] '
    'OR "Practice Guideline"[pt])'
)

# Exploited designs. Each needs a supporting citation in the manuscript
# (manuscript/preprint_outline.md, Methods 2.2). Text-word searches: none of these
# has a PubMed publication type.
SECONDARY_ANALYSIS_DESIGNS = {
    "mr_two_sample": (
        '(("two-sample"[tiab] OR "two sample"[tiab]) '
        'AND Mendelian[tiab] AND (randomization[tiab] OR randomisation[tiab]))'
    ),
    "bibliometric": "(bibliometric*[tiab] OR scientometric*[tiab])",
    "nhanes_cross_sectional": (
        '((NHANES[tiab] OR "National Health and Nutrition Examination Survey"[tiab]) '
        'AND ("cross-sectional"[tiab] OR "cross sectional"[tiab]))'
    ),
    "gbd_secondary": '"Global Burden of Disease"[tiab]',
    "network_pharmacology": '"network pharmacology"[tiab]',
    "faers_disproportionality": (
        '((FAERS[tiab] OR "Adverse Event Reporting System"[tiab]) '
        'AND disproportionality[tiab])'
    ),
}


def any_of(designs) -> str:
    return "(" + " OR ".join(SECONDARY_ANALYSIS_DESIGNS[d] for d in designs) + ")"


STRATA = {
    "total": None,  # year filter only
    "high_signal": HIGH_SIGNAL,
    "high_volume": any_of(SECONDARY_ANALYSIS_DESIGNS),
    **{f"loo_{d}": any_of([x for x in SECONDARY_ANALYSIS_DESIGNS if x != d]) for d in SECONDARY_ANALYSIS_DESIGNS},
}


def year_filter(year: int, field: str) -> str:
    if field == "dp":
        return f"{year}[dp]"
    return f"{year}/01/01:{year}/12/31[{field}]"


def build_query(stratum_query, year: int, field: str) -> str:
    yf = year_filter(year, field)
    core = yf if stratum_query is None else f"({stratum_query} AND {yf})"
    return f"{core} NOT {EXCLUDE}"


def get_count(query: str) -> int:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with Entrez.esearch(db="pubmed", term=query, retmax=0) as handle:
                return int(Entrez.read(handle)["Count"])
        except Exception as exc:  # network / HTTP 429 / parse errors
            wait = 2 ** attempt
            print(f"  retry {attempt}/{MAX_RETRIES} after error ({exc}); sleeping {wait}s",
                  file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"Failed after {MAX_RETRIES} retries: {query}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--date-field", choices=["dp", "edat"], default="dp")
    ap.add_argument("--start", type=int, default=1950)
    ap.add_argument("--end", type=int, default=2025)
    args = ap.parse_args()

    email = os.environ.get("NCBI_EMAIL", "").strip()
    if not email or "@" not in email:
        sys.exit("NCBI_EMAIL is not set. NCBI requires a contact address: "
                 "export NCBI_EMAIL=you@example.com")
    Entrez.email = email
    Entrez.tool = "pubmed-inflation-meta-research"
    api_key = os.environ.get("NCBI_API_KEY", "").strip()
    if api_key:
        Entrez.api_key = api_key
    sleep_s = SLEEP_WITH_KEY if api_key else SLEEP_NO_KEY

    out_path = RAW_DIR / f"pubmed_counts_{args.date_field}.csv"
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    if out_path.exists():  # resume, keeping only rows whose query is unchanged
        prev = pd.read_csv(out_path)
        current = prev.apply(lambda r: r["stratum"] in STRATA and r["query"] == build_query(
            STRATA[r["stratum"]], int(r["year"]), args.date_field), axis=1)
        rows = prev[current].to_dict("records")
        print(f"Resuming: kept {len(rows)} rows, dropped {(~current).sum()} with changed queries")
    done = {(int(r["year"]), r["stratum"]) for r in rows}

    years = range(args.start, args.end + 1)
    total_calls = len(years) * len(STRATA)
    n = 0
    for year in years:
        for name, sq in STRATA.items():
            n += 1
            if (year, name) in done:
                continue
            query = build_query(sq, year, args.date_field)
            count = get_count(query)
            rows.append({
                "year": year,
                "stratum": name,
                "count": count,
                "date_field": args.date_field,
                "query": query,
                "retrieved_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            })
            print(f"[{n}/{total_calls}] {year} {name:<32} {count:>9,}")
            time.sleep(sleep_s)  # strict rate limiting
        pd.DataFrame(rows).to_csv(out_path, index=False)  # checkpoint per year

    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
