#!/usr/bin/env python3
"""G4: score the citation-context pilot (protocol §5 G4).

Joins the first-pass codes (100 pairs) to the group key (selected design vs other), reports the
distribution of citation context by group with Wilson 95% CIs, and intra-rater agreement and Cohen's
kappa on the 25 recoded pairs. Recode pairs are matched to the first pass by guideline and cited PMID.

Usage: python scripts/18_g4_score.py
Reads data/gates/g4_context_sheet.csv (first-pass codes filled in), g4_recode_codes.csv and
g4_group_key.csv. Writes data/processed/gate_g4_context.csv and gate_g4_agreement.csv.
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pubinfl import gates  # noqa: E402

GATES = ROOT / "data" / "gates"
OUT = ROOT / "data" / "processed" / "gate_g4_context.csv"
OUT_AGREE = ROOT / "data" / "processed" / "gate_g4_agreement.csv"
CONTEXTS = ["background", "methods", "evidence", "other"]
KEY = ["guideline_pmid", "cited_pmid"]


def main() -> None:
    sheet = pd.read_csv(GATES / "g4_context_sheet.csv", dtype=str)
    if not sheet["context"].isin(CONTEXTS).all():
        raise ValueError("every first-pass pair needs a context code")
    groups = pd.read_csv(GATES / "g4_group_key.csv", dtype=str)
    d = sheet.merge(groups, on=KEY, how="left")
    if d["group"].isna().any():
        raise ValueError("pairs missing from the group key")

    rows = []
    for g, sub in [("all", d)] + list(d.groupby("group")):
        n = len(sub)
        for c in CONTEXTS:
            k = int((sub["context"] == c).sum())
            lo, hi = gates.wilson_ci(k, n)
            rows.append({"group": g, "context": c, "k": k, "n": n, "share": k / n, "ci_low": lo, "ci_high": hi})
    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)

    recode = pd.read_csv(GATES / "g4_recode_codes.csv", dtype=str).merge(
        sheet[["row_id"] + KEY], on="row_id", how="left")
    m = d.merge(recode[KEY + ["context"]], on=KEY, suffixes=("_1", "_2"))
    agree = int((m["context_1"] == m["context_2"]).sum())
    kappa = gates.cohens_kappa(m["context_1"], m["context_2"])
    pd.DataFrame([{"n_recoded": len(m), "agree": agree, "kappa": kappa}]).to_csv(OUT_AGREE, index=False)

    print(out.pivot(index="context", columns="group", values="k").loc[CONTEXTS].to_string())
    for g in ["selected", "other"]:
        s = out[(out["group"] == g) & (out["context"] == "evidence")].iloc[0]
        print(f"{g}: evidence {s['k']}/{s['n']} = {s['share']:.2f} (95% CI {s['ci_low']:.2f}-{s['ci_high']:.2f})")
    print(f"Intra-rater: {agree}/{len(m)} agree, kappa {kappa:.2f}")


if __name__ == "__main__":
    main()
