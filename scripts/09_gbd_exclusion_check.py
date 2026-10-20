#!/usr/bin/env python3
"""GBD flagship exclusion checks (protocol v2.3, §3.5).

(1) Precision: 50 random records removed by the consortium exclusion (seed 20221130).
(2) Recall in the G4 pool: GBD-text papers cited by 2015-2019 open-access F1 guidelines that the
    exclusion keeps. Usage: NCBI_EMAIL=you@example.com python scripts/09_gbd_exclusion_check.py
Writes data/processed/gbd_exclusion_check.json.
"""
import json
import random
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from Bio import Entrez
from pubinfl import cache, ncbi

OUT = ROOT / "data" / "processed" / "gbd_exclusion_check.json"
sleep_s = ncbi.configure_entrez()
GBD_TXT = '"Global Burden of Disease"[tiab]'

# (1) precision: records the exclusion removes
with Entrez.esearch(db="pubmed", term=f"{GBD_TXT} AND {ncbi.GBD_CONSORTIUM_QUERY}", retmax=9999) as h:
    res = Entrez.read(h)
ids = [int(i) for i in res["IdList"]]
random.seed(20221130)
samp = sorted(random.sample(ids, 50))
meta = ncbi.fetch_summaries(samp, sleep_s=sleep_s)
prec = [{"pmid": p, **meta.get(p, {})} for p in samp]
print(f"excluded by consortium rule: {res['Count']} records; sampled 50")

# (2) G4 candidate pool, same rule as scripts/07
first = {}
for r in cache.read_jsonl(ROOT / "data" / "raw" / "f1_guidelines_icite.jsonl"):
    if r["pmid"] not in first or r["year"] < first[r["pmid"]]["year"]:
        first[r["pmid"]] = r
rows = [r for r in first.values() if 2015 <= r["year"] <= 2019 and r["references"]]
gmeta = ncbi.fetch_summaries([r["pmid"] for r in rows], sleep_s=sleep_s)
open_ids = {p for p, m in gmeta.items() if m.get("pmcid")}
cited = sorted({c for r in rows if r["pmid"] in open_ids for c in r["references"]})
print(f"{len(open_ids)} open guidelines; {len(cited)} unique cited papers")
gbd_all = ncbi.search_subset(GBD_TXT, cited, sleep_s=sleep_s)
gbd_kept = ncbi.search_subset(f"{GBD_TXT} NOT {ncbi.GBD_CONSORTIUM_QUERY}", cited, sleep_s=sleep_s)
sel_new = ncbi.search_subset(ncbi.SELECTED_DESIGNS_QUERY, cited, sleep_s=sleep_s)
kmeta = ncbi.fetch_summaries(sorted(gbd_kept), sleep_s=sleep_s)
print(f"GBD text: {len(gbd_all)}; kept after exclusion: {len(gbd_kept)}; selected designs {len(sel_new)}")
OUT.write_text(json.dumps({"n_excluded_total": int(res["Count"]), "precision_sample": prec,
    "pool": {"open_guidelines": len(open_ids), "cited": len(cited), "gbd_text": len(gbd_all),
             "gbd_kept": len(gbd_kept), "selected_new": len(sel_new)},
    "gbd_kept_records": [{"pmid": p, **kmeta.get(p, {})} for p in sorted(gbd_kept)]}, indent=1))
