#!/usr/bin/env python3
"""Pooled and geometric-mean selected-design incidence ratios (Supplement S4), replacing arithmetic means.

Pooled ratio: size-weighted cumulative incidence of the selected designs across the cohorts in a period,
divided by the same for other research (each group's cohort incidences weighted by its cohort size at
age 0), so small early cohorts no longer count as much as large later ones. The geometric mean of the
cohort ratios is shown alongside. Reads data/processed/secondary/<frame>_group_lifetable.csv; uses the same
cumulative-incidence convention as scripts/21_secondary.py (horizon - 1).

Usage: python scripts/26_pooled_selected_ratios.py   Writes data/processed/secondary/selected_ratios_pooled.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pubinfl import analysis  # noqa: E402

SEC = ROOT / "data" / "processed" / "secondary"
PERIODS = {3: [("2008-2017", range(2008, 2018)), ("2018-2022", range(2018, 2023))],
           5: [("2008-2017", range(2008, 2018)), ("2018-2020", range(2018, 2021))]}

rows = []
for frame in ("F1", "F2", "F2_clean"):
    glt = pd.read_csv(SEC / f"{frame}_group_lifetable.csv")
    size = glt[glt["age"] == 0].set_index(["group", "cohort"])["n"]
    for horizon, periods in PERIODS.items():
        ci = {g: analysis.cumulative_incidence(glt[glt["group"] == g].drop(columns="group"), horizon - 1) for g in (0, 1)}
        for label, cohorts in periods:
            cs = list(cohorts)
            pooled = {g: float((ci[g].reindex(cs) * size.loc[g].reindex(cs)).sum() / size.loc[g].reindex(cs).sum()) for g in (0, 1)}
            r = (ci[1] / ci[0]).reindex(cs)
            rows.append({"frame": frame, "horizon": horizon, "period": label, "pooled_ratio": pooled[1] / pooled[0],
                         "geometric_mean_ratio": float(np.exp(np.log(r).mean())), "arithmetic_mean_ratio": float(r.mean()),
                         "selected_papers": int(size.loc[1].reindex(cs).sum())})
out = pd.DataFrame(rows)
out.to_csv(SEC / "selected_ratios_pooled.csv", index=False)
print(out.round(2).to_string(index=False))
