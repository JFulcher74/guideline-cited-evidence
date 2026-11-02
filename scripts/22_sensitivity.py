#!/usr/bin/env python3
"""Remaining pre-specified sensitivity analyses (protocol §6), for F1, F2 and cleaned F2. Primary
specification otherwise ([dp], coverage-weighted, D). Already run by 19_primary.py: unweighted, [edat],
D-Humans, D-all.

- age3: P1 at a 3-year headline age (guideline year <= Y + 3), cohorts 2008-2022.
- no_covid: cohorts 2020 and 2021 excluded from the hazard model, the P1 growth fit and the breakpoints.
- d_journals: D restricted to the 2008-2012 clinical journal set (numerator and denominator).
- stable_journals: frame guidelines restricted to journals with coverage >= 0.90 in every era of the
  coverage audit (triggered by the audit, protocol §3.4).
- F1 vs F2, 2022-2023: guideline counts and coverage by year, and (exploratory, not pre-specified) the
  hazard model with follow-up censored at calendar year 2021, which removes the F1 indexing dip.
- F3 (NICE): the pilot has 10 guidelines, too few to estimate a trend, so agreement is described:
  overlap of NICE-cited papers with F1/F2-cited papers, and their citation ages.

Usage: python scripts/22_sensitivity.py [--reps 999]
Writes data/processed/sensitivity/.
"""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pubinfl import analysis, cache, icite  # noqa: E402

spec = importlib.util.spec_from_file_location("primary", ROOT / "scripts" / "19_primary.py")
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)

EXTRACT = ROOT / "data" / "raw" / "extract"
PROC = ROOT / "data" / "processed"
OUT = PROC / "sensitivity"


def run(gyear, journal, refs, cohort_of, denom, reps, cohorts=range(2008, 2025), p1_cohorts=range(2008, 2021),
        horizon=5, end_year=2025, exclude=()) -> dict:
    has_refs = {p: True for p in refs}
    cov = analysis.coverage_by_year(gyear, journal, has_refs)
    first = analysis.first_citations(gyear, refs, cov)
    cohorts = [c for c in cohorts if c not in exclude]
    lt = analysis.life_table(first, cohort_of, denom, cohorts, end_year=end_year)
    fit = analysis.fit_hazard(lt)
    bs = analysis.bootstrap_hazard(lt, ["beta"], reps=reps)["beta"].dropna()
    p1c = [c for c in p1_cohorts if c not in exclude]
    p1 = lt[lt["age"] <= horizon].groupby("cohort")["d"].sum().reindex(p1c)
    g = analysis.p1_growth(p1, denom, reps=reps)
    beta_ci = tuple(np.percentile(bs, [2.5, 97.5]))
    return {"beta": fit["beta"], "beta_ci": beta_ci, "g1": g["g1"], "g1_ci": g["g1_ci"], "gD": g["gD"],
            "diff": g["diff"], "diff_ci": g["diff_ci"], "H1": beta_ci[1] < 0, "H2": g["diff_ci"][1] < 0,
            "decision": analysis.decision_cell(beta_ci, g["g1_ci"]), "lt": lt}


def stable_journals() -> set:
    a = pd.read_csv(PROC / "coverage_audit_by_journal.csv")
    eras = [c for c in a.columns if c.startswith("coverage_")]
    return set(a.loc[(a[eras] >= 0.90).all(axis=1), "journal"])


def d_journals_denominator() -> pd.Series:
    c = pd.read_csv(PROC / "d_journals_counts.csv")
    c = c[c["date_field"] == "dp"].set_index("year")["count"].astype(float)
    o = pd.read_csv(PROC / "d_journals_overlaps.csv").set_index("later_year")["overlap"]
    return (c - o.reindex(c.index).fillna(0)).rename("D_journals")


def nice_agreement(frames, refs) -> dict:
    """Descriptive F3 agreement: citation age (iCite year) of NICE-cited papers against F1/F2 guidelines
    of the same years (2015-2020), and the share of NICE-cited papers that F1/F2 guidelines also cite."""
    n = pd.read_csv(ROOT / "data" / "gates" / "g3_nice_references.csv")
    s = pd.read_csv(ROOT / "data" / "gates" / "g3_nice_sample.csv")
    n = n[n["matched"]].merge(s[["ng", "year"]], on="ng")
    pm = n["pmid"].astype(int).unique().tolist()
    years = {r["pmid"]: r["icite_year"] for r in cache.read_jsonl(EXTRACT / "cited.jsonl")}
    years.update({p: (r or {}).get("year") for p, r in icite.fetch_icite([p for p in pm if p not in years], ["pmid", "year"]).items()})
    age = (n["year"] - n["pmid"].astype(int).map(years)).dropna()
    out = {"nice_guidelines": int(n["ng"].nunique()), "nice_matched_pmids": len(pm),
           "NICE_median_citation_age": float(age.median()), "NICE_share_age_le5": float((age <= 5).mean())}
    for f in ("F1", "F2"):
        cited = {int(c) for g in frames[f] for c in refs.get(g, ())}
        out[f"share_of_NICE_cited_also_cited_by_{f}"] = float(np.mean([p in cited for p in pm]))
        a = pd.Series([y - years[int(c)] for g, y in frames[f].items() if 2015 <= y <= 2020
                       for c in refs.get(g, ()) if years.get(int(c)) is not None])
        out[f"{f}_2015_2020_median_citation_age"] = float(a.median())
        out[f"{f}_2015_2020_share_age_le5"] = float((a <= 5).mean())
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=999)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    frames, journal, refs, mem = P.load("dp")
    d_all = P.denominator("D", "dp")
    cohort_of = mem[(mem["D"] == 1) & mem["dp_year"].notna()].set_index("pmid")["dp_year"].astype(int)
    cited_journal = {r["pmid"]: r["journal"] for r in cache.read_jsonl(EXTRACT / "cited.jsonl")}
    jset = set(pd.read_csv(PROC / "d_journals_set.csv")["journal"])
    cohort_dj = cohort_of[cohort_of.index.map(lambda p: cited_journal.get(p) in jset)]
    d_j = d_journals_denominator()
    stable = stable_journals()

    rows, extra = [], {}
    for name, gyear in frames.items():
        specs = {
            "age3": dict(p1_cohorts=range(2008, 2023), horizon=3),
            "no_covid": dict(exclude=(2020, 2021)),
            "d_journals": dict(denom=d_j, cohort_of=cohort_dj),
            "stable_journals": dict(gyear={p: y for p, y in gyear.items() if journal.get(p) in stable}),
            "censor_2021": dict(cohorts=range(2008, 2021), p1_cohorts=range(2008, 2017), end_year=2021),
        }
        for label, kw in specs.items():
            args_ = dict(gyear=gyear, journal=journal, refs=refs, cohort_of=cohort_of, denom=d_all, reps=args.reps)
            args_.update(kw)
            r = run(**args_)
            rows.append({"frame": name, "spec": label, **{k: v for k, v in r.items() if k != "lt"},
                         "n_guidelines": len(args_["gyear"])})
            if label == "no_covid":
                p1 = r["lt"][r["lt"]["age"] <= 5].groupby("cohort")["d"].sum().reindex([c for c in range(2008, 2021) if c not in (2020, 2021)])
                ci5 = analysis.cumulative_incidence(r["lt"], 5).reindex(p1.index)
                extra[f"{name}_no_covid_breaks"] = {"P1": analysis.segmented(p1, n_boot=args.reps),
                                                    "ci5": analysis.segmented(ci5, n_boot=args.reps)}
            print(name, label, round(r["beta"], 4), [round(x, 4) for x in r["beta_ci"]], round(r["diff"], 4), flush=True)

    gl = pd.DataFrame([{"frame": f, "year": y, "has_refs": p in refs, "journal_article": bool(journal.get(p))}
                       for f in ("F1", "F2") for p, y in frames[f].items()])
    yearly = gl.groupby(["frame", "year"]).agg(guidelines=("has_refs", "size"), with_refs=("has_refs", "sum")).reset_index()
    yearly.to_csv(OUT / "f1_f2_guidelines_by_year.csv", index=False)
    extra["nice"] = nice_agreement(frames, refs)

    res = pd.DataFrame(rows)
    for col in ["beta_ci", "g1_ci", "diff_ci"]:
        res[[f"{col}_low", f"{col}_high"]] = pd.DataFrame(res.pop(col).tolist(), index=res.index)
    res.to_csv(OUT / "sensitivity_summary.csv", index=False)
    (OUT / "extra.json").write_text(json.dumps(extra, indent=2, default=lambda o: o.item() if isinstance(o, np.generic) else str(o)))
    print(json.dumps(extra["nice"], indent=1))


if __name__ == "__main__":
    main()
