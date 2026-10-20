#!/usr/bin/env python3
"""Main extraction (protocol §4): guideline frames, reference lists, cited-paper years and
denominator membership, and yearly denominator counts.

Stages (each cached under data/raw/extract/, so a rerun resumes where it stopped):
  1. frames      F1 and F2 PMIDs by year, 2008-2025, under [dp] and [edat]; a record matching
                 several years takes the earliest (protocol §3.1).
  2. guidelines  esummary for every frame guideline (journal; no journal = NCBI Bookshelf book)
                 and its iCite reference list.
  3. cited       the union of cited PMIDs, with iCite year and journal.
  4. membership  for each cited PMID: earliest [dp] and [edat] year in 2008-2025, and membership of
                 D, D-Humans, D-all and the selected designs. PMIDs are posted to the History
                 server and intersected with each query, so the numerator is exactly a subset of D.
  5. counts      yearly sizes of each denominator and of the selected designs, [dp] and [edat].

No analysis is run here.

Usage: NCBI_EMAIL=you@example.com python scripts/14_extract.py [--stage NAME]
"""
import argparse
import csv
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from Bio import Entrez

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pubinfl import cache, icite, ncbi  # noqa: E402

OUT = ROOT / "data" / "raw" / "extract"
BODIES = ROOT / "manuscript" / "f2_named_bodies.csv"
YEARS = range(2008, 2026)
DATE_FIELDS = ("dp", "edat")
BATCH = 5000

QUERIES = {
    "D": ncbi.D_QUERY,
    "D_humans": f"({ncbi.D_QUERY}) AND Humans[mh]",
    "D_all": "all[sb] NOT preprint[pt]",
    "selected": ncbi.SELECTED_DESIGNS_QUERY,
}


def log(msg: str) -> None:
    print(f"[{datetime.now(timezone.utc):%H:%M:%S}] {msg}", flush=True)


def esearch(term: str, retmax: int = 0, **kw) -> dict:
    def _s():
        with Entrez.esearch(db="pubmed", term=term, retmax=retmax, **kw) as h:
            return Entrez.read(h)
    return ncbi.with_retries(_s)


def search_year(query: str, year: int, field: str, sleep_s: float) -> list:
    res = esearch(f"({query}) AND {year}[{field}]", ncbi.RETMAX)
    time.sleep(sleep_s)
    if int(res["Count"]) > ncbi.RETMAX:
        raise ValueError(f"{query[:60]}… {year}[{field}] exceeds {ncbi.RETMAX}")
    return [int(i) for i in res["IdList"]]


def write_jsonl(path: Path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    cache.write_gz_copy(path)


# ---- 1. frames ---------------------------------------------------------------------------------
def stage_frames(sleep_s: float) -> None:
    bodies = pd.read_csv(BODIES)
    frames = {"F1": [("F1", ncbi.F1_QUERY)],
              "F2": [(b.body_id, ncbi.f2_body_query(b.match_rule)) for b in bodies.itertuples()]}
    for name, rules in frames.items():
        recs = {}
        for rule_id, q in rules:
            for field in DATE_FIELDS:
                for y in YEARS:
                    for p in search_year(q, y, field, sleep_s):
                        r = recs.setdefault(p, {"pmid": p, "dp_year": None, "edat_year": None, "bodies": set()})
                        k = f"{field}_year"
                        r[k] = y if r[k] is None else min(r[k], y)
                        if name == "F2":
                            r["bodies"].add(rule_id)
            log(f"{name} {rule_id}: {len(recs)} records so far")
        rows = [{**r, "bodies": sorted(r["bodies"])} for r in recs.values()]
        write_jsonl(OUT / f"frame_{name.lower()}.jsonl", sorted(rows, key=lambda r: r["pmid"]))
        log(f"{name}: {len(rows)} records")


# ---- 2. guidelines ----------------------------------------------------------------------------
def stage_guidelines(sleep_s: float) -> None:
    pmids = sorted({r["pmid"] for f in ("f1", "f2") for r in cache.read_jsonl(OUT / f"frame_{f}.jsonl")})
    log(f"guidelines: {len(pmids)} unique frame PMIDs")
    meta = ncbi.fetch_summaries(pmids, sleep_s=sleep_s)
    refs = icite.fetch_icite(pmids, ["pmid", "year", "references"])
    rows = [{"pmid": p, "journal": meta.get(p, {}).get("journal", ""), "pmcid": meta.get(p, {}).get("pmcid", ""),
             "in_icite": p in refs, "references": (refs.get(p) or {}).get("references") or []} for p in pmids]
    write_jsonl(OUT / "guidelines.jsonl", rows)
    log(f"guidelines: {sum(r['in_icite'] for r in rows)} in iCite, {sum(bool(r['references']) for r in rows)} with references")


# ---- 3. cited ----------------------------------------------------------------------------------
def stage_cited(sleep_s: float) -> None:
    cited = sorted({int(c) for r in cache.read_jsonl(OUT / "guidelines.jsonl") for c in r["references"]})
    log(f"cited: {len(cited)} unique cited PMIDs")
    recs = icite.fetch_icite(cited, ["pmid", "year", "journal"])
    write_jsonl(OUT / "cited.jsonl", [{"pmid": p, "icite_year": (recs.get(p) or {}).get("year"),
                                        "journal": (recs.get(p) or {}).get("journal", "")} for p in cited])


# ---- 4. membership -----------------------------------------------------------------------------
MEMBER_COLS = ["pmid", "dp_year", "edat_year"] + list(QUERIES)


def stage_membership(sleep_s: float) -> None:
    cited = [r["pmid"] for r in cache.read_jsonl(OUT / "cited.jsonl")]
    path = OUT / "cited_membership.csv"
    done = set()
    if path.exists():  # keep only complete batches, so a run stopped mid-write resumes cleanly
        rows = pd.read_csv(path)
        size = rows.groupby("batch").size()
        full = [b for b, n in size.items() if n == min(BATCH, len(cited) - b * BATCH)]
        rows[rows["batch"].isin(full)].to_csv(path, index=False)
        done = set(full)
    new = not path.exists()
    with path.open("a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["batch"] + MEMBER_COLS)
        if new:
            w.writeheader()
        nb = (len(cited) + BATCH - 1) // BATCH
        for b in range(nb):
            if b in done:
                continue
            ids = cited[b * BATCH:(b + 1) * BATCH]

            def _post():
                with Entrez.epost(db="pubmed", id=",".join(map(str, ids))) as h:
                    return Entrez.read(h)
            post = ncbi.with_retries(_post)
            env, key = post["WebEnv"], post["QueryKey"]
            time.sleep(sleep_s)

            def hits(term):
                res = esearch(f"#{key} AND {term}", BATCH, webenv=env, usehistory="y")
                time.sleep(sleep_s)
                return {int(i) for i in res["IdList"]}

            year = {f: {} for f in DATE_FIELDS}
            for f in DATE_FIELDS:
                for y in YEARS:
                    for p in hits(f"{y}[{f}]"):
                        year[f].setdefault(p, y)  # years ascend, so the first hit is the earliest
            member = {name: hits(f"({q})") for name, q in QUERIES.items()}
            for p in ids:
                w.writerow({"batch": b, "pmid": p, "dp_year": year["dp"].get(p), "edat_year": year["edat"].get(p),
                            **{name: int(p in s) for name, s in member.items()}})
            fh.flush()
            log(f"membership batch {b + 1}/{nb}")


# ---- 5. counts ---------------------------------------------------------------------------------
def stage_counts(sleep_s: float) -> None:
    rows = []
    for name, q in {**QUERIES, "D_selected": f"({ncbi.D_QUERY}) AND {ncbi.SELECTED_DESIGNS_QUERY}"}.items():
        for f in DATE_FIELDS:
            for y in YEARS:
                n = int(esearch(f"({q}) AND {y}[{f}]")["Count"])
                time.sleep(sleep_s)
                rows.append({"set": name, "date_field": f, "year": y, "count": n})
        log(f"counts: {name}")
    pd.DataFrame(rows).to_csv(OUT / "denominator_counts.csv", index=False)


STAGES = {"frames": stage_frames, "guidelines": stage_guidelines, "cited": stage_cited,
          "membership": stage_membership, "counts": stage_counts}
DONE_MARK = {"frames": "frame_f2.jsonl", "guidelines": "guidelines.jsonl", "cited": "cited.jsonl",
             "counts": "denominator_counts.csv"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=list(STAGES), help="run only this stage")
    args = ap.parse_args()
    sleep_s = ncbi.configure_entrez()
    OUT.mkdir(parents=True, exist_ok=True)
    prov_path = OUT / "provenance.json"
    prov = json.loads(prov_path.read_text()) if prov_path.exists() else {
        "queries": {"F1": ncbi.F1_QUERY, "F2_words": ncbi.F2_GUIDELINE_WORDS, "F2_exclude": ncbi.F2_EXCLUDE, **QUERIES},
        "years": [YEARS.start, YEARS.stop - 1], "python": platform.python_version(),
        "biopython": __import__("Bio").__version__, "stages": {}}
    for name, fn in STAGES.items():
        if args.stage and name != args.stage:
            continue
        mark = DONE_MARK.get(name)
        if not args.stage and mark and cache.cache_exists(OUT / mark):
            log(f"{name}: cached, skipping")
            continue
        started = datetime.now(timezone.utc).isoformat(timespec="seconds")
        fn(sleep_s)
        prov["stages"][name] = {"started_utc": started,
                                "finished_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        prov_path.write_text(json.dumps(prov, indent=2))
    log("extraction complete")


if __name__ == "__main__":
    main()
