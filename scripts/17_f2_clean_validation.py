#!/usr/bin/env python3
"""F2 cleaning rule for the sensitivity analysis (protocol §3.1, added 2026-11-02 before any analysis).

1. Fetches the title and publication types of every F2 record (extraction snapshot) and applies the
   frozen rule `ncbi.f2_clean_keep`; writes the kept/dropped flag.
2. Reports the rule against the 100 coded G2-on-F2 records. The rule was designed on these records,
   so this is an in-sample check only.
3. Draws a blind validation sample: 50 kept and 20 dropped records with iCite references, outside both
   G2 samples, stratified by year and shuffled together, so the coder cannot tell which is which.
   Precision of the cleaned frame is estimated from the 50 kept records.

Usage: NCBI_EMAIL=you@example.com python scripts/17_f2_clean_validation.py
Writes data/raw/extract/f2_pubtypes.jsonl(.gz), data/processed/f2_clean.csv,
data/gates/f2v_coding_sheet.csv (refuses to overwrite) and data/gates/f2v_abstracts.json.
"""
import json
import sys
import time
import urllib.parse
from pathlib import Path

import pandas as pd
from Bio import Entrez

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pubinfl import cache, gates, ncbi  # noqa: E402

EXTRACT = ROOT / "data" / "raw" / "extract"
GATES = ROOT / "data" / "gates"
META = EXTRACT / "f2_pubtypes.jsonl"
OUT_CLEAN = ROOT / "data" / "processed" / "f2_clean.csv"
OUT_SHEET = GATES / "f2v_coding_sheet.csv"
N_KEPT, N_DROPPED = 50, 20


def fetch_meta(pmids, sleep_s: float) -> None:
    rows = []
    for i in range(0, len(pmids), 200):
        params = {"db": "pubmed", "id": ",".join(map(str, pmids[i:i + 200])), "retmode": "json",
                  "tool": "pubmed-inflation-meta-research"}
        res = ncbi.with_retries(ncbi._get_json, f"{ncbi.ESUMMARY_URL}?{urllib.parse.urlencode(params)}")["result"]
        for u in res.get("uids", []):
            r = res[u]
            authors = r.get("authors") or []
            rows.append({"pmid": int(u), "title": r.get("title", ""), "pubtypes": r.get("pubtype", []),
                         "journal": r.get("source", ""),
                         "first_author": next((a["name"] for a in authors if a.get("authtype") == "Author"), ""),
                         "collective_authors": "; ".join(a["name"] for a in authors if a.get("authtype") == "CollectiveName")})
        time.sleep(sleep_s)
    with META.open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    cache.write_gz_copy(META)


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
    if OUT_SHEET.exists():
        sys.exit(f"{OUT_SHEET} exists - refusing to overwrite coded work")
    frame = pd.DataFrame(cache.read_jsonl(EXTRACT / "frame_f2.jsonl"))
    if not cache.cache_exists(META):
        fetch_meta(frame["pmid"].tolist(), sleep_s)
    meta = pd.DataFrame(cache.read_jsonl(META))
    meta["keep"] = [ncbi.f2_clean_keep(t, pt) for t, pt in zip(meta["title"], meta["pubtypes"])]
    frame = frame.merge(meta, on="pmid", how="left")
    frame[["pmid", "dp_year", "edat_year", "keep"]].to_csv(OUT_CLEAN, index=False)
    print(f"F2 frame {len(frame)}: kept {int(frame['keep'].sum())}, dropped {int((~frame['keep']).sum())}")

    coded = pd.read_csv(GATES / "f2_coding_sheet.csv", dtype={"pmid": int, "eligible": str}).merge(meta[["pmid", "keep"]], on="pmid")
    tab = pd.crosstab(coded["eligible"], coded["keep"])
    print("In-sample (rule designed on these 100 records):\n" + tab.to_string())

    refs = {g["pmid"]: bool(g["references"]) for g in cache.read_jsonl(EXTRACT / "guidelines.jsonl")}
    used = set(pd.read_csv(GATES / "g2_coding_sheet.csv")["pmid"]) | set(coded["pmid"])
    pool = frame[frame["pmid"].map(refs).fillna(False).astype(bool) & ~frame["pmid"].isin(used)
                 & frame["dp_year"].between(2008, 2025)].rename(columns={"dp_year": "year"})
    kept = gates.stratified_sample(pool[pool["keep"]][["pmid", "year"]], n_total=N_KEPT)
    dropped = gates.stratified_sample(pool[~pool["keep"]][["pmid", "year"]], n_total=N_DROPPED, seed=gates.SEED + 100)
    sample = pd.concat([kept.assign(rule_keep=True), dropped.assign(rule_keep=False)])
    sample = sample.sample(frac=1, random_state=gates.SEED).reset_index(drop=True).merge(meta, on="pmid", how="left")
    abs_ = abstracts(sample["pmid"].tolist(), sleep_s)
    sheet = sample.assign(pubmed_url=sample["pmid"].map(lambda p: f"https://pubmed.ncbi.nlm.nih.gov/{p}/"),
                          eligible="", issuing_body_type="", notes="")
    sheet[["pmid", "year", "stratum", "rule_keep", "journal", "title", "collective_authors", "first_author",
           "pubmed_url", "eligible", "issuing_body_type", "notes"]].to_csv(OUT_SHEET, index=False)
    (GATES / "f2v_abstracts.json").write_text(json.dumps({str(k): v for k, v in abs_.items()}))
    print(f"Validation sheet: {len(sheet)} records ({N_KEPT} kept, {N_DROPPED} dropped, shuffled)")


if __name__ == "__main__":
    main()
