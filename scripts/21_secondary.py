#!/usr/bin/env python3
"""Secondary analyses 1-5 and H3 (protocol §6), primary specification ([dp], coverage-weighted, D),
for frames F1, F2 and cleaned F2.

1. Breakpoints: continuous segmented regression on log P1 and on log 5-year cumulative incidence,
   cohorts 2008-2020; one estimated break (bootstrap CI) and a two-break test.
2. Decomposition of P1 per cohort Y: coverage-adjusted guidelines in years Y..Y+5 x references per
   guideline x share of those references to cohort-Y papers in D x uniqueness (first citations per
   reference); the log-growth of the four factors sums to the growth of P1.
3. Selected designs vs the rest: group x cohort hazard model (gamma, delta1, delta1 + delta2; 2018
   hinge), cohort-level bootstrap; 3- and 5-year cumulative incidence ratios; descriptive breakdown by
   design and era.
4. H3: (a) selected-design share of D, 2008-2025, one estimated break plus a hinge fixed at 2022;
   (b) P2 hazard model with hinges at the 5-year-incidence break and at 2022 (theta).
5. Early signal: 1- and 2-year cumulative incidence, cohorts 2015-2024.

Usage: python scripts/21_secondary.py [--reps 999]
Writes data/processed/secondary/.
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
from pubinfl import analysis  # noqa: E402

spec = importlib.util.spec_from_file_location("primary", ROOT / "scripts" / "19_primary.py")
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)

EXTRACT = ROOT / "data" / "raw" / "extract"
OUT = ROOT / "data" / "processed" / "secondary"
COHORTS = range(2008, 2025)
P1_COHORTS = range(2008, 2021)
ERAS = {"2008-2017": range(2008, 2018), "2018-2022": range(2018, 2023)}


def ci(lo_hi):
    return f"{lo_hi[0]:.4f} to {lo_hi[1]:.4f}"


def decomposition(gyear, refs, cov, cohort_of) -> pd.DataFrame:
    rows = [(y, int(c)) for g, y in gyear.items() for c in refs.get(g, ())]
    r = pd.DataFrame(rows, columns=["G", "pmid"])
    r["w"] = 1.0 / r["G"].map(cov)
    r["cohort"] = r["pmid"].map(cohort_of)
    g = pd.DataFrame({"G": list(gyear.values()), "pmid": list(gyear)})
    g = g[g["pmid"].isin(refs.keys())]
    g["w"] = 1.0 / g["G"].map(cov)
    out = []
    for y in P1_COHORTS:
        win = r[r["G"].between(y, y + 5)]
        n_g = g.loc[g["G"].between(y, y + 5), "w"].sum()
        refs_total = win["w"].sum()
        refs_y = win.loc[win["cohort"] == y, "w"].sum()
        out.append({"cohort": y, "guidelines": n_g, "refs_per_guideline": refs_total / n_g,
                    "share_to_cohort": refs_y / refs_total, "refs_to_cohort": refs_y})
    return pd.DataFrame(out).set_index("cohort")


def group_life_table(first, mem, d_all, d_sel):
    sel = mem[(mem["D"] == 1) & (mem["selected"] == 1) & mem["dp_year"].notna()].set_index("pmid")["dp_year"].astype(int)
    rest = mem[(mem["D"] == 1) & (mem["selected"] == 0) & mem["dp_year"].notna()].set_index("pmid")["dp_year"].astype(int)
    a = analysis.life_table(first, sel, d_sel, COHORTS).assign(group=1)
    b = analysis.life_table(first, rest, d_all - d_sel, COHORTS).assign(group=0)
    return pd.concat([a, b], ignore_index=True)


def design_breakdown(first, mem, frame_name) -> pd.DataFrame:
    counts = pd.read_csv(EXTRACT / "design_arm_counts.csv")
    counts["n"] = counts["count"] - counts["overlap_with_previous"]
    arms = pd.read_csv(EXTRACT / "design_arm_cited.csv")
    d = mem[(mem["D"] == 1) & mem["dp_year"].notna()].set_index("pmid")["dp_year"].astype(int)
    f = first.set_index("pmid")
    rows = []
    for arm in arms.columns.drop("pmid"):
        pm = arms.loc[arms[arm] == 1, "pmid"]
        cited = pd.DataFrame({"cohort": d.reindex(pm), "first": f["first_year"].reindex(pm), "w": f["w"].reindex(pm)}).dropna()
        cited["age"] = (cited["first"] - cited["cohort"]).clip(lower=0)
        n_by = counts[counts["arm"] == arm].set_index("year")["n"]
        for era, ys in ERAS.items():
            c = cited[cited["cohort"].isin(ys)]
            rows.append({"frame": frame_name, "design": arm, "era": era, "papers_in_D": int(n_by.reindex(ys).sum()),
                         "guideline_cited": len(c), "cum_inc_3y_pct": 100 * c.loc[c["age"] <= 2, "w"].sum() / n_by.reindex(ys).sum()})
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=999)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    frames, journal, refs, mem = P.load("dp")
    d_all = P.denominator("D", "dp")
    d_sel = P.denominator("D_selected", "dp")
    cohort_of = mem[(mem["D"] == 1) & mem["dp_year"].notna()].set_index("pmid")["dp_year"].astype(int)
    has_refs = {p: True for p in refs}
    summary, breakdowns = {}, []

    share = (d_sel / d_all).loc[2008:2025]
    h3a = analysis.segmented(share, n_boot=args.reps, fixed=2022)
    summary["H3a_selected_share"] = h3a
    pd.DataFrame({"D": d_all, "D_selected": d_sel, "share": share}).to_csv(OUT / "selected_share.csv")

    for name, gyear in frames.items():
        s = {}
        cov = analysis.coverage_by_year(gyear, journal, has_refs)
        first = analysis.first_citations(gyear, refs, cov)
        lt = analysis.life_table(first, cohort_of, d_all, COHORTS)
        p1 = lt[lt["age"] <= 5].groupby("cohort")["d"].sum().reindex(P1_COHORTS)
        ci5 = analysis.cumulative_incidence(lt, 5).reindex(P1_COHORTS)

        # 1. breakpoints
        s["SA1_P1"] = analysis.segmented(p1, n_boot=args.reps)
        s["SA1_ci5"] = analysis.segmented(ci5, n_boot=args.reps)

        # 2. decomposition
        dec = decomposition(gyear, refs, cov, cohort_of)
        dec["uniqueness"] = p1 / dec["refs_to_cohort"]
        dec["P1"] = p1
        dec.to_csv(OUT / f"{name}_decomposition.csv")
        s["SA2_growth_pct_per_year"] = {k: 100 * analysis.loglinear_slope(dec.index, dec[k])
                                        for k in ["guidelines", "refs_per_guideline", "share_to_cohort", "uniqueness", "P1"]}
        s["SA2_growth_pct_per_year"]["D"] = 100 * analysis.loglinear_slope(P1_COHORTS, d_all.reindex(P1_COHORTS))

        # 3. selected designs vs the rest
        glt = group_life_table(first, mem, d_all, d_sel)
        glt.to_csv(OUT / f"{name}_group_lifetable.csv", index=False)
        fit = analysis.fit_group_hazard(glt)
        bs = analysis.bootstrap_group_hazard(glt, reps=args.reps)
        s["SA3_group_model"] = {k: {"est": fit[k], "ci": tuple(np.percentile(bs[k].dropna(), [2.5, 97.5])),
                                    "undefined_reps": int(bs[k].isna().sum())}
                                for k in ["gamma", "delta1", "delta1_plus_delta2", "beta"]}
        ratios = {}
        for horizon, cohorts in [(3, range(2008, 2023)), (5, range(2008, 2021))]:
            a = analysis.cumulative_incidence(glt[glt["group"] == 1].drop(columns="group"), horizon - 1)
            b = analysis.cumulative_incidence(glt[glt["group"] == 0].drop(columns="group"), horizon - 1)
            r = (a / b).reindex(cohorts)
            ratios[f"ratio_{horizon}y"] = r
            s[f"SA3_ratio_{horizon}y_mean"] = {"2008-2017": float(r.loc[2008:2017].mean()), "2018+": float(r.loc[2018:].mean())}
        pd.DataFrame(ratios).to_csv(OUT / f"{name}_selected_ratios.csv")
        breakdowns.append(design_breakdown(first, mem, name))

        # 4. H3(b)
        tau = s["SA1_ci5"]["break"]
        hinges = [("psi", tau), ("theta", 2022)]
        th = analysis.fit_hazard(lt, hinges=hinges)
        tb = analysis.bootstrap_hazard(lt, ["theta"], reps=args.reps, hinges=hinges)
        s["H3b_theta"] = {"tau_hat": tau, "est": th["theta"], "ci": tuple(np.percentile(tb["theta"].dropna(), [2.5, 97.5])),
                          "undefined_reps": int(tb["theta"].isna().sum())}

        # 5. early signal
        early = pd.DataFrame({"cum_inc_1y": analysis.cumulative_incidence(lt, 0), "cum_inc_2y": analysis.cumulative_incidence(lt, 1)}).loc[2015:2024]
        early.to_csv(OUT / f"{name}_early_signal.csv")
        summary[name] = s
        print(name, "done", flush=True)

    s_h3 = {n: summary[n]["H3b_theta"] for n in frames}
    summary["H3_supported"] = {n: bool(h3a.get("p_fixed", 1) < 0.05 or (s_h3[n]["ci"][0] > 0 or s_h3[n]["ci"][1] < 0)) for n in frames}
    pd.concat(breakdowns).to_csv(OUT / "design_breakdown.csv", index=False)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=lambda o: o if not isinstance(o, np.generic) else o.item()))
    print(json.dumps(summary, indent=1, default=str)[:6000])


if __name__ == "__main__":
    main()
