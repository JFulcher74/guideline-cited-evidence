#!/usr/bin/env python3
"""Post hoc check of bootstrap calibration: block length 2 and 4 against the registered 3.

Added after the v0.3 pre-submission review (not pre-specified). Re-uses the saved primary life tables
(data/processed/primary/dp_weighted_D_<frame>_lifetable.csv and _cohorts.csv); point estimates are
unchanged, only the moving-block bootstrap intervals for beta (H1) and g1 - gD (H2) are recomputed.

Usage: python scripts/25_block_sensitivity.py
Writes data/processed/sensitivity/block_length.csv
"""
import sys
from functools import partial
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pubinfl import analysis  # noqa: E402

PRIM = ROOT / "data" / "processed" / "primary"
OUT = ROOT / "data" / "processed" / "sensitivity" / "block_length.csv"
P1_COHORTS = range(2008, 2021)
ORIGINAL = analysis.moving_blocks


def main() -> None:
    rows = []
    for frame in ("F1", "F2", "F2_clean"):
        lt = pd.read_csv(PRIM / f"dp_weighted_D_{frame}_lifetable.csv")
        d = pd.read_csv(PRIM / f"dp_weighted_D_{frame}_cohorts.csv", index_col="cohort")["D"]
        p1 = lt[lt["age"] <= 5].groupby("cohort")["d"].sum().reindex(P1_COHORTS)
        beta = analysis.fit_hazard(lt)["beta"]
        for block in (2, 3, 4):
            analysis.moving_blocks = partial(ORIGINAL, block=block)
            try:
                bs = analysis.bootstrap_hazard(lt, ["beta"])
                g = analysis.p1_growth(p1, d)
            finally:
                analysis.moving_blocks = ORIGINAL
            lo, hi = np.percentile(bs["beta"].dropna(), [2.5, 97.5])
            rows.append({"frame": frame, "block": block, "beta": beta, "beta_ci_low": lo, "beta_ci_high": hi,
                         "diff": g["diff"], "diff_ci_low": g["diff_ci"][0], "diff_ci_high": g["diff_ci"][1],
                         "H1": hi < 0, "H2": g["diff_ci"][1] < 0})
            print(rows[-1], flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT, index=False)


if __name__ == "__main__":
    main()
