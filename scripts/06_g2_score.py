#!/usr/bin/env python3
"""G2: score the coded eligibility sheets for each frame -> PPV (Wilson 95% CI), intra-rater kappa,
threshold flag. Frames: F1 (g2_* sheets, 200 + 50 recode) and F2 (f2_* sheets, 100 + 25 recode)."""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pubinfl import gates  # noqa: E402

GATES = ROOT / "data" / "gates"
OUT = ROOT / "data" / "processed" / "gate_g2_eligibility.csv"
FRAMES = {"F1": "g2", "F2": "f2"}


def main() -> None:
    rows = []
    for frame, pre in FRAMES.items():
        coded = pd.read_csv(GATES / f"{pre}_coding_sheet.csv", dtype={"eligible": str, "pmid": str})
        recoded = pd.read_csv(GATES / f"{pre}_recode_sheet.csv", dtype={"eligible": str, "pmid": str})
        s = {"frame": frame, **gates.score_g2(coded, recoded)}
        rows.append(s)
        print(f"{frame}: PPV {s['ppv']:.3f} (95% CI {s['ppv_lo']:.3f}-{s['ppv_hi']:.3f}), {s['n_eligible']}/{s['n']} eligible; "
              f"kappa {s['kappa']:.2f} on {s['n_recoded']} recoded; "
              + ("PPV below 0.80 - report the shortfall for this frame" if s["below_threshold"] else "meets the 0.80 threshold"))
    pd.DataFrame(rows).to_csv(OUT, index=False)


if __name__ == "__main__":
    main()
