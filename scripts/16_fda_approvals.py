#!/usr/bin/env python3
"""FDA novel approvals context series (protocol §2 context, §4): descriptive only, not tested.

Pre-specified definition: original approvals (SubmissionType ORIG, status AP) of NDAs classed as a
new molecular entity (Type 1 or Type 1/4), plus original BLAs, from the Drugs@FDA data files,
counted by approval year. Drugs@FDA covers CDER-regulated BLAs only. Original BLAs include
biosimilars, which Drugs@FDA does not flag on original submissions (its BIOSIMILAR class is unused
there), so the series runs above CDER's published novel-approval counts.

Usage: python scripts/16_fda_approvals.py
Downloads the Drugs@FDA zip to data/raw/fda/ (not committed; its sha256 is recorded) and writes
data/processed/fda_approvals.csv.
"""
import hashlib
import io
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
URL = "https://www.fda.gov/media/89850/download"
ZIP = ROOT / "data" / "raw" / "fda" / "drugsatfda.zip"
OUT = ROOT / "data" / "processed" / "fda_approvals.csv"
YEARS = range(2008, 2026)
NME_CLASSES = {"TYPE 1", "TYPE 1/4"}


def read(z: zipfile.ZipFile, name: str) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(z.read(name)), sep="\t", dtype=str, encoding="latin-1")


def main() -> None:
    if not ZIP.exists():
        ZIP.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(URL, timeout=120) as r:
            ZIP.write_bytes(r.read())
    sha = hashlib.sha256(ZIP.read_bytes()).hexdigest()
    retrieved = datetime.fromtimestamp(ZIP.stat().st_mtime, timezone.utc).isoformat(timespec="seconds")
    with zipfile.ZipFile(ZIP) as z:
        apps, subs, cls = read(z, "Applications.txt"), read(z, "Submissions.txt"), read(z, "SubmissionClass_Lookup.txt")
    s = subs.merge(apps[["ApplNo", "ApplType"]], on="ApplNo").merge(cls, on="SubmissionClassCodeID", how="left")
    s = s[(s["SubmissionType"] == "ORIG") & (s["SubmissionStatus"] == "AP")].copy()
    s["year"] = pd.to_datetime(s["SubmissionStatusDate"], errors="coerce").dt.year
    nme = s[(s["ApplType"] == "NDA") & s["SubmissionClassCode"].isin(NME_CLASSES)]
    bla = s[s["ApplType"] == "BLA"]
    out = pd.DataFrame({"year": list(YEARS)})
    for name, d in [("nme", nme), ("bla_original", bla)]:
        out[name] = out["year"].map(d.drop_duplicates("ApplNo").groupby("year").size()).fillna(0).astype(int)
    out["novel_prespecified"] = out["nme"] + out["bla_original"]
    out["source_sha256"], out["retrieved_utc"] = sha, retrieved
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    print(out.drop(columns=["source_sha256", "retrieved_utc"]).to_string(index=False))
    print(f"sha256 {sha}")


if __name__ == "__main__":
    main()
