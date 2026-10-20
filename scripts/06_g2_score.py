#!/usr/bin/env python3
"""G2: score the coded eligibility sheets -> PPV (Wilson 95% CI), intra-rater kappa, threshold flag."""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pubinfl import gates  # noqa: E402

GATES = ROOT / "data" / "gates"
OUT = ROOT / "data" / "processed" / "gate_g2_eligibility.csv"


def main() -> None:
    coded = pd.read_csv(GATES / "g2_coding_sheet.csv", dtype={"eligible": str})
    recoded = pd.read_csv(GATES / "g2_recode_sheet.csv", dtype={"eligible": str})
    s = gates.score_g2(coded, recoded)
    pd.DataFrame([s]).to_csv(OUT, index=False)
    print(f"PPV {s['ppv']:.3f} (95% CI {s['ppv_lo']:.3f}-{s['ppv_hi']:.3f}), "
          f"kappa {s['kappa']:.2f} on {s['n_recoded']} recoded")
    print("PPV below 0.80 - report the shortfall for this frame" if s["below_threshold"] else "PPV meets the 0.80 threshold")


if __name__ == "__main__":
    main()
