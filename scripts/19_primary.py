#!/usr/bin/env python3
"""Co-primary outcomes P1 and P2 and the decision rule (protocol §6), for frames F1, F2 and cleaned F2.

For each frame: coverage weights by guideline year (journal-article guidelines only), first frame-
guideline citation of each paper in D, life tables for cohorts 2008-2024, the discrete-time hazard
model (beta, H1) with a cohort-level moving-block bootstrap, P1 growth against D for cohorts
2008-2020 (H2), and the decision-table cell. Denominators are de-duplicated for records that match two
[dp] years, matching the numerator's earliest-year rule.

Usage: python scripts/19_primary.py [--date-field dp|edat] [--unweighted] [--denom D|D_humans|D_all|D_medline]
D_medline (dp only) is a post hoc sensitivity denominator from scripts/24_medline_extract.py.
Reads data/raw/extract/. Writes data/processed/primary/<tag>_*.csv and a summary row per frame.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pubinfl import analysis, cache  # noqa: E402

EXTRACT = ROOT / "data" / "raw" / "extract"
OUT = ROOT / "data" / "processed" / "primary"
COHORTS = range(2008, 2025)
P1_COHORTS = range(2008, 2021)
P1_8Y_COHORTS = range(2008, 2018)


def load(date_field: str):
    key = f"{date_field}_year"
    frames = {f: {r["pmid"]: r[key] for r in cache.read_jsonl(EXTRACT / f"frame_{f.lower()}.jsonl")
                  if r[key] is not None and 2008 <= r[key] <= 2025} for f in ("F1", "F2")}
    clean = pd.read_csv(ROOT / "data" / "processed" / "f2_clean.csv")
    keep = set(clean.loc[clean["keep"], "pmid"])
    frames["F2_clean"] = {p: y for p, y in frames["F2"].items() if p in keep}
    gl = cache.read_jsonl(EXTRACT / "guidelines.jsonl")
    journal = {g["pmid"]: g["journal"] for g in gl}
    refs = {g["pmid"]: g["references"] for g in gl if g["references"]}
    mem = pd.read_csv(EXTRACT / "cited_membership.csv.gz" if not (EXTRACT / "cited_membership.csv").exists()
                      else EXTRACT / "cited_membership.csv")
    mpath = EXTRACT / "medline_membership.csv"
    if not mpath.exists():
        mpath = mpath.with_suffix(".csv.gz")
    if mpath.exists():  # post hoc D-MEDLINE flag (scripts/24_medline_extract.py); only D members were queried
        ml = pd.read_csv(mpath)[["pmid", "medline"]].drop_duplicates("pmid")
        mem = mem.merge(ml, on="pmid", how="left")
        mem["D_medline"] = ((mem["D"] == 1) & (mem["medline"].fillna(0) == 1)).astype(int)
    return frames, journal, refs, mem


def denominator(name: str, date_field: str) -> pd.Series:
    if name == "D_medline":
        if date_field != "dp":
            raise SystemExit("D_medline is extracted for [dp] only")
        m = pd.read_csv(EXTRACT / "medline_counts.csv").set_index("year")
        return (m["count"] - m["overlap_with_previous"]).astype(float)
    c = pd.read_csv(EXTRACT / "denominator_counts.csv")
    c = c[(c["set"] == name) & (c["date_field"] == date_field)].set_index("year")["count"].astype(float)
    if date_field == "dp":  # remove records also matching the previous year (assigned to the earlier year)
        o = pd.read_csv(EXTRACT / "denominator_year_overlaps.csv")
        o = o[o["set"] == name].set_index("later_year")["overlap"]
        c = c - o.reindex(c.index).fillna(0)
    return c


def run_frame(name, gyear, journal, refs, mem, denom, date_field, weighted, reps):
    has_refs = {p: True for p in refs}
    cov = analysis.coverage_by_year(gyear, journal, has_refs)
    first = analysis.first_citations(gyear, refs, cov if weighted else None)
    member_col = {"D": "D", "D_humans": "D_humans", "D_all": "D_all", "D_medline": "D_medline"}[denom.name]
    m = mem[(mem[member_col] == 1) & mem[f"{date_field}_year"].notna()]
    cohort_of = m.set_index("pmid")[f"{date_field}_year"].astype(int)
    lt = analysis.life_table(first, cohort_of, denom, COHORTS)

    fit = analysis.fit_hazard(lt)
    bs = analysis.bootstrap_hazard(lt, ["beta"], reps=reps)
    beta_ci = tuple(np.percentile(bs["beta"], [2.5, 97.5]))
    ph = analysis.fit_hazard(lt, age_cohort=True)

    ev = lt[lt["age"] <= 5].groupby("cohort")["d"].sum()
    p1 = ev.reindex(P1_COHORTS)
    g = analysis.p1_growth(p1, denom, reps=reps)
    ev8 = lt[lt["age"] <= 8].groupby("cohort")["d"].sum().reindex(P1_8Y_COHORTS)
    g8 = analysis.p1_growth(ev8, denom, reps=reps)
    ci5, ci8 = analysis.cumulative_incidence(lt, 5), analysis.cumulative_incidence(lt, 8)

    cohort_table = pd.DataFrame({"D": denom.reindex(COHORTS), "P1_5y": ev.reindex(COHORTS),
                                 "cum_inc_5y": ci5.reindex(COHORTS), "cum_inc_8y": ci8.reindex(COHORTS)})
    cohort_table.index.name = "cohort"
    summary = {
        "frame": name, "date_field": date_field, "weighted": weighted, "denominator": denom.name,
        "n_guidelines": len(gyear), "n_guidelines_with_refs": sum(p in refs for p in gyear),
        "beta": fit["beta"], "beta_ci_low": beta_ci[0], "beta_ci_high": beta_ci[1],
        "OR_per_year": float(np.exp(fit["beta"])),
        "ph_beta_x_age2_4": ph["beta_x_age2_4"], "ph_beta_x_age5plus": ph["beta_x_age5plus"],
        "g1": g["g1"], "g1_ci_low": g["g1_ci"][0], "g1_ci_high": g["g1_ci"][1],
        "gD": g["gD"], "diff_g1_gD": g["diff"], "diff_ci_low": g["diff_ci"][0], "diff_ci_high": g["diff_ci"][1],
        "doubling_P1_years": g["doubling_p1"], "doubling_D_years": g["doubling_d"],
        "g1_8y": g8["g1"], "diff_8y": g8["diff"], "diff_8y_ci_low": g8["diff_ci"][0], "diff_8y_ci_high": g8["diff_ci"][1],
        "H1_supported": beta_ci[1] < 0, "H2_supported": g["diff_ci"][1] < 0,
        "decision": analysis.decision_cell(beta_ci, g["g1_ci"]),
    }
    return summary, lt, cohort_table, cov


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date-field", default="dp", choices=["dp", "edat"])
    ap.add_argument("--unweighted", action="store_true")
    ap.add_argument("--denom", default="D", choices=["D", "D_humans", "D_all", "D_medline"])
    ap.add_argument("--reps", type=int, default=999)
    args = ap.parse_args()
    frames, journal, refs, mem = load(args.date_field)
    denom = denominator(args.denom, args.date_field).rename(args.denom)
    tag = f"{args.date_field}_{'unweighted' if args.unweighted else 'weighted'}_{args.denom}"
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, gyear in frames.items():
        s, lt, ct, cov = run_frame(name, gyear, journal, refs, mem, denom, args.date_field, not args.unweighted, args.reps)
        rows.append(s)
        lt.to_csv(OUT / f"{tag}_{name}_lifetable.csv", index=False)
        ct.to_csv(OUT / f"{tag}_{name}_cohorts.csv")
        cov.rename("coverage").to_csv(OUT / f"{tag}_{name}_coverage.csv")
        print(json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in s.items()}, default=str))
    pd.DataFrame(rows).to_csv(OUT / f"{tag}_summary.csv", index=False)


if __name__ == "__main__":
    main()
