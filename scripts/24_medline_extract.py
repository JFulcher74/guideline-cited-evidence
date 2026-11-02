#!/usr/bin/env python3
"""Post hoc sensitivity extraction: MEDLINE-indexed research denominator (D-MEDLINE).

Added after the v0.3 pre-submission review (not in the registered protocol; reported as post hoc).
PubMed's share of journal articles not indexed for MEDLINE (mostly PubMed Central-only journals) rose
from about 9% (2008) to 27% (2020), so part of D's growth could reflect PubMed's scope rather than
publication volume. D-MEDLINE = D AND medline[sb].

Stages (cached under data/raw/extract/, resumable):
  counts      yearly [dp] counts of D-MEDLINE, 2008-2025, and records matching both year Y-1 and Y
              (so counts can be de-duplicated to the earliest year, as for D).
  membership  for each cited PMID already in D: whether it is in medline[sb] (History-server intersection).

Caveat: medline[sb] is the status on the run date. Recent records still "in process" are not yet MEDLINE,
so the newest cohorts are undercounted in both numerator and denominator.

Usage: NCBI_EMAIL=you@example.com python scripts/24_medline_extract.py [--stage counts|membership]
"""
import argparse
import csv
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from Bio import Entrez

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pubinfl import ncbi  # noqa: E402

OUT = ROOT / "data" / "raw" / "extract"
YEARS = range(2008, 2026)
BATCH = 5000
Q = f"({ncbi.D_QUERY}) AND medline[sb]"


def log(msg: str) -> None:
    print(f"[{datetime.now(timezone.utc):%H:%M:%S}] {msg}", flush=True)


def esearch(term: str, retmax: int = 0, **kw) -> dict:
    def _s():
        with Entrez.esearch(db="pubmed", term=term, retmax=retmax, **kw) as h:
            return Entrez.read(h)
    return ncbi.with_retries(_s)


def stage_counts(sleep_s: float) -> None:
    rows = []
    for y in YEARS:
        n = int(esearch(f"{Q} AND {y}[dp]")["Count"]); time.sleep(sleep_s)
        o = int(esearch(f"{Q} AND {y - 1}[dp] AND {y}[dp]")["Count"]); time.sleep(sleep_s)
        rows.append({"set": "D_medline", "date_field": "dp", "year": y, "count": n, "overlap_with_previous": o})
        log(f"counts {y}: {n} (overlap {o})")
    pd.DataFrame(rows).assign(run_date=datetime.now(timezone.utc).date().isoformat()).to_csv(
        OUT / "medline_counts.csv", index=False)


def stage_membership(sleep_s: float) -> None:
    mem = pd.read_csv(OUT / "cited_membership.csv.gz")
    cited = sorted(mem.loc[mem["D"] == 1, "pmid"].astype(int).tolist())
    path = OUT / "medline_membership.csv"
    done = set(pd.read_csv(path)["batch"].unique()) if path.exists() else set()
    new = not path.exists()
    nb = (len(cited) + BATCH - 1) // BATCH
    log(f"membership: {len(cited)} cited PMIDs in D, {nb} batches, {len(done)} done")
    with path.open("a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["batch", "pmid", "medline"])
        if new:
            w.writeheader()
        for b in range(nb):
            if b in done:
                continue
            ids = cited[b * BATCH:(b + 1) * BATCH]

            def _post():
                with Entrez.epost(db="pubmed", id=",".join(map(str, ids))) as h:
                    return Entrez.read(h)
            post = ncbi.with_retries(_post); time.sleep(sleep_s)
            res = esearch(f"#{post['QueryKey']} AND medline[sb]", BATCH, webenv=post["WebEnv"], usehistory="y")
            time.sleep(sleep_s)
            hit = {int(i) for i in res["IdList"]}
            w.writerows({"batch": b, "pmid": p, "medline": int(p in hit)} for p in ids)
            fh.flush()
            if b % 20 == 0:
                log(f"membership batch {b + 1}/{nb}")
    log("membership done")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["counts", "membership"])
    args = ap.parse_args()
    sleep_s = ncbi.configure_entrez()
    for name, fn in (("counts", stage_counts), ("membership", stage_membership)):
        if args.stage in (None, name):
            fn(sleep_s)


if __name__ == "__main__":
    main()
