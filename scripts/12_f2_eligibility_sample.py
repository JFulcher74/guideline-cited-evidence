#!/usr/bin/env python3
"""G2 on frame F2: build the F2 frame and draw the 100-record eligibility sample (protocol §3.1).

Frame: union of the 31 frozen named-body rules (manuscript/f2_named_bodies.csv), searched year by
year 2008-2025; a PMID matching several years takes the earliest. Analysis set: F2 records with at
least one iCite reference, as for the F1 sample. PMIDs already in the F1 (G2) sample are excluded so
the two samples are independent. Stratified 2008-2013 / 2014-2019 / 2020-2025, seed 20221130; a 25%
recode subset (25 records).

Usage: NCBI_EMAIL=you@example.com python scripts/12_f2_eligibility_sample.py
Writes data/raw/f2_frame.jsonl (+ .gz copy, committed), data/gates/f2_coding_sheet.csv and
data/gates/f2_recode_sheet.csv (refuses to overwrite either sheet).
"""
import csv
import json
import sys
import time
from pathlib import Path

import pandas as pd
from Bio import Entrez

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pubinfl import cache, gates, icite, ncbi  # noqa: E402

BODIES = ROOT / "manuscript" / "f2_named_bodies.csv"
FRAME = ROOT / "data" / "raw" / "f2_frame.jsonl"
F1_SHEET = ROOT / "data" / "gates" / "g2_coding_sheet.csv"
OUT = ROOT / "data" / "gates" / "f2_coding_sheet.csv"
OUT_RECODE = ROOT / "data" / "gates" / "f2_recode_sheet.csv"
YEARS = range(2008, 2026)
N_SAMPLE = 100


def build_frame(sleep_s: float) -> None:
    bodies = pd.read_csv(BODIES)
    found = {}
    for b in bodies.itertuples():
        q = ncbi.f2_body_query(b.match_rule)
        n_body = 0
        for y in YEARS:
            for p in ncbi.search_pmids(q, y, sleep_s=sleep_s):
                rec = found.setdefault(p, {"year": y, "bodies": set()})
                rec["year"] = min(rec["year"], y)
                rec["bodies"].add(b.body_id)
                n_body += 1
        print(f"{b.body_id}: {n_body} matches")
    refs = icite.fetch_icite(sorted(found), ["pmid", "references"])
    with FRAME.open("w") as fh:
        for p in sorted(found):
            r = refs.get(p)
            fh.write(json.dumps({"pmid": p, "year": found[p]["year"], "bodies": sorted(found[p]["bodies"]),
                                 "in_icite": r is not None,
                                 "n_references": len((r or {}).get("references") or [])}) + "\n")
    cache.write_gz_copy(FRAME)


def abstracts(pmids, sleep_s: float) -> dict:
    out = {}
    for i in range(0, len(pmids), 100):
        def _fetch(ids):
            with Entrez.efetch(db="pubmed", id=",".join(map(str, ids)), retmode="xml") as h:
                return Entrez.read(h)
        recs = ncbi.with_retries(_fetch, pmids[i:i + 100])
        for art in recs["PubmedArticle"]:
            mc = art["MedlineCitation"]
            parts = []
            for a in mc["Article"].get("Abstract", {}).get("AbstractText", []):
                lab = getattr(a, "attributes", {}).get("Label")
                parts.append((lab + ": " if lab else "") + str(a))
            out[int(mc["PMID"])] = "\n".join(parts)
        time.sleep(sleep_s)
    return out


def main() -> None:
    sleep_s = ncbi.configure_entrez()
    for path in (OUT, OUT_RECODE):
        if path.exists():
            sys.exit(f"{path} exists - refusing to overwrite coded work")
    if not cache.cache_exists(FRAME):
        build_frame(sleep_s)
    rows = cache.read_jsonl(FRAME)
    frame = pd.DataFrame(rows)
    f1 = {int(r["pmid"]) for r in csv.DictReader(F1_SHEET.open())}
    analysis = frame[(frame["n_references"] > 0) & ~frame["pmid"].isin(f1)]
    print(f"F2 frame {len(frame)} records; {int((frame['n_references'] > 0).sum())} with iCite references; "
          f"{len(analysis)} after excluding the F1 sample")
    sample = gates.stratified_sample(analysis[["pmid", "year"]], n_total=N_SAMPLE)
    meta = ncbi.fetch_summaries(sample["pmid"].tolist(), sleep_s=sleep_s)
    abs_ = abstracts(sample["pmid"].tolist(), sleep_s)
    body_of = dict(zip(frame["pmid"], frame["bodies"]))
    sheet = sample.assign(
        f2_bodies=sample["pmid"].map(lambda p: ";".join(body_of[p])),
        journal=sample["pmid"].map(lambda p: meta.get(p, {}).get("journal", "")),
        title=sample["pmid"].map(lambda p: meta.get(p, {}).get("title", "")),
        collective_authors=sample["pmid"].map(lambda p: meta.get(p, {}).get("collective_authors", "")),
        first_author=sample["pmid"].map(lambda p: meta.get(p, {}).get("first_author", "")),
        pubmed_url=sample["pmid"].map(lambda p: f"https://pubmed.ncbi.nlm.nih.gov/{p}/"),
        eligible="", issuing_body_type="", notes="",
    )
    sheet.to_csv(OUT, index=False)
    gates.recode_subset(sheet).assign(eligible="", issuing_body_type="", notes="").to_csv(OUT_RECODE, index=False)
    (ROOT / "data" / "gates" / "f2_abstracts.json").write_text(json.dumps({str(k): v for k, v in abs_.items()}))
    print(sheet["stratum"].value_counts().sort_index().to_string())
    print(f"Wrote {OUT.name} ({len(sheet)}) and {OUT_RECODE.name} "
          f"({len(gates.recode_subset(sheet))}); {sum(1 for v in abs_.values() if v)} with abstracts")


if __name__ == "__main__":
    main()
