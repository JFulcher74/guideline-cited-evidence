"""Pure logic for the protocol v2.1 feasibility gates (no network access)."""
import numpy as np
import pandas as pd


def _n_refs(rec) -> int:
    if rec is None:
        return 0
    return len(rec.get("references") or [])


def coverage_by_group(frame: pd.DataFrame, icite_records: dict, by: list) -> pd.DataFrame:
    """Share of frame guidelines with >=1 iCite reference, by the columns in `by`.

    PMIDs absent from iCite count as having no references. Duplicate PMIDs count once.
    """
    f = frame.drop_duplicates("pmid")
    rows = []
    for key, grp in f.groupby(by):
        recs = [icite_records.get(int(p)) for p in grp["pmid"]]
        n_refs = [_n_refs(r) for r in recs]
        with_refs = [n for n in n_refs if n > 0]
        rows.append(dict(
            zip(by, key),
            n_guidelines=len(grp),
            n_in_icite=sum(r is not None for r in recs),
            n_with_refs=len(with_refs),
            coverage=len(with_refs) / len(grp),
            median_refs=float(np.median(with_refs)) if with_refs else float("nan"),
        ))
    return pd.DataFrame(rows)


def coverage_by_year(frame: pd.DataFrame, icite_records: dict) -> pd.DataFrame:
    """Share of frame guidelines with >=1 iCite reference, by year."""
    cov = coverage_by_group(frame, icite_records, ["year"])
    cov["year"] = cov["year"].astype(int)
    return cov


def gate_g1(cov: pd.DataFrame, threshold: float = 0.70):
    """PASS only if coverage >= threshold in every year. Returns (passed, failing_years)."""
    failing = sorted(int(y) for y in cov.loc[cov["coverage"] < threshold, "year"])
    return (len(failing) == 0), failing


def citation_ages(guideline_years: dict, refs: dict, cited_years: dict):
    """Ages (guideline year - cited paper year) for every guideline reference.

    Excludes references with no known year and references dated after the guideline.
    """
    ages, unknown, negative = [], 0, 0
    for g, gy in guideline_years.items():
        for r in refs.get(g, []):
            cy = cited_years.get(int(r))
            if cy is None:
                unknown += 1
            elif gy - cy < 0:
                negative += 1
            else:
                ages.append(gy - cy)
    return pd.Series(ages, dtype=int), {"unknown_year": unknown, "negative_age": negative}


def age_summary(ages: pd.Series) -> dict:
    a = ages.astype(float)
    return dict(
        n=int(len(a)), median=float(a.median()),
        p25=float(a.quantile(0.25)), p75=float(a.quantile(0.75)),
        share_le_3=float((a <= 3).mean()), share_le_5=float((a <= 5).mean()),
        share_le_8=float((a <= 8).mean()),
    )


STRATA = ((2008, 2013), (2014, 2019), (2020, 2025))
SEED = 20221130


def stratified_sample(frame: pd.DataFrame, n_total: int = 200, strata=STRATA, seed: int = SEED) -> pd.DataFrame:
    """Equal allocation across year strata (remainder to the earliest strata), capped at availability."""
    f = frame.drop_duplicates("pmid")
    base, extra = divmod(n_total, len(strata))
    parts = []
    for i, (a, b) in enumerate(strata):
        want = base + (1 if i < extra else 0)
        pool = f[(f["year"] >= a) & (f["year"] <= b)]
        take = pool.sample(n=min(want, len(pool)), random_state=seed + i)
        parts.append(take.assign(stratum=f"{a}-{b}"))
    return pd.concat(parts).sort_values(["stratum", "pmid"]).reset_index(drop=True)


def recode_subset(sample: pd.DataFrame, frac: float = 0.25, seed: int = SEED, sort_by="pmid") -> pd.DataFrame:
    return sample.sample(n=int(round(len(sample) * frac)), random_state=seed).sort_values(sort_by)


def wilson_ci(k: int, n: int, z: float = 1.96):
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    denom = 1 + z ** 2 / n
    centre = (p + z ** 2 / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2)) / denom
    return float(centre - half), float(centre + half)


def cohens_kappa(a, b) -> float:
    a, b = list(a), list(b)
    if len(a) != len(b) or not a:
        raise ValueError("kappa needs two equal-length, non-empty code lists")
    cats = sorted(set(a) | set(b))
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in cats)
    return 1.0 if pe == 1 else float((po - pe) / (1 - pe))


def score_g2(coded: pd.DataFrame, recoded: pd.DataFrame, ppv_threshold: float = 0.80) -> dict:
    c = coded.assign(eligible=coded["eligible"].str.strip().str.upper())
    if not c["eligible"].isin(["Y", "N"]).all():
        raise ValueError("every coded row needs eligible = Y or N")
    k, n = int((c["eligible"] == "Y").sum()), len(c)
    lo, hi = wilson_ci(k, n)
    r = recoded.assign(eligible=recoded["eligible"].str.strip().str.upper())
    m = c.merge(r, on="pmid", suffixes=("_1", "_2"))
    return dict(n=n, n_eligible=k, ppv=k / n, ppv_lo=lo, ppv_hi=hi,
                n_recoded=len(m), kappa=cohens_kappa(m["eligible_1"], m["eligible_2"]),
                below_threshold=bool(k / n < ppv_threshold))


def sample_citation_pairs(pairs: pd.DataFrame, selected: set, n_per_group: int = 50, seed: int = SEED) -> pd.DataFrame:
    """Equal-sized samples of guideline-citation pairs: cited paper in the selected designs vs not."""
    p = pairs.assign(group=pairs["cited_pmid"].map(lambda x: "selected" if int(x) in selected else "other"))
    parts = []
    for i, g in enumerate(("selected", "other")):
        pool = p[p["group"] == g]
        parts.append(pool.sample(n=min(n_per_group, len(pool)), random_state=seed + i))
    return pd.concat(parts).sort_values(["group", "guideline_pmid", "cited_pmid"]).reset_index(drop=True)
