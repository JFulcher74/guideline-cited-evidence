"""Primary-outcome machinery (protocol §3.3–§3.4, §6): coverage weights, first-citation life tables,
the discrete-time hazard model (P2), log-linear growth of P1 against D, and moving-block bootstraps."""
import numpy as np
import pandas as pd

END_YEAR = 2025


def coverage_by_year(gyear: dict, journal: dict, has_refs: dict) -> pd.Series:
    """Share of a frame's journal-article guidelines with at least one iCite reference, by guideline year.
    Bookshelf books (no journal) are excluded from the denominator (protocol §3.4)."""
    g = pd.DataFrame({"pmid": list(gyear), "year": list(gyear.values())})
    g = g[g["pmid"].map(lambda p: bool(journal.get(p)))]
    return g.groupby("year")["pmid"].apply(lambda s: np.mean([bool(has_refs.get(p)) for p in s]))


def first_citations(gyear: dict, refs: dict, weight_by_year=None) -> pd.DataFrame:
    """Earliest frame-guideline year citing each paper, with weight 1/coverage of that year (or 1)."""
    first = {}
    for g, y in gyear.items():
        for c in refs.get(g, ()):
            c = int(c)
            if c not in first or y < first[c]:
                first[c] = y
    out = pd.DataFrame({"pmid": list(first), "first_year": list(first.values())})
    out["w"] = 1.0 if weight_by_year is None else 1.0 / out["first_year"].map(weight_by_year)
    return out


def life_table(first: pd.DataFrame, cohort_of: pd.Series, denom: pd.Series, cohorts, end_year: int = END_YEAR) -> pd.DataFrame:
    """Rows (cohort, age, n_at_risk, events) for papers in the denominator set.

    `cohort_of` maps PMID -> publication cohort for papers in the denominator set (others are ignored);
    `denom` maps cohort -> number of papers in the set. Age = first citation year - cohort, floored at 0.
    """
    f = first.merge(cohort_of.rename("cohort"), left_on="pmid", right_index=True)
    f["age"] = (f["first_year"] - f["cohort"]).clip(lower=0)
    ev = f.groupby(["cohort", "age"])["w"].sum()
    rows = []
    for y in cohorts:
        n = float(denom[y])
        for a in range(0, end_year - y + 1):
            d = float(ev.get((y, a), 0.0))
            rows.append({"cohort": y, "age": a, "n": n, "d": d})
            n -= d
    return pd.DataFrame(rows)


def cumulative_incidence(lt: pd.DataFrame, max_age: int) -> pd.Series:
    """1 - Kaplan-Meier survival at `max_age` (ages 0..max_age inclusive), for cohorts observed that long."""
    out = {}
    for y, g in lt.groupby("cohort"):
        if g["age"].max() < max_age:
            continue
        g = g[g["age"] <= max_age]
        out[y] = 1 - np.prod(1 - g["d"] / g["n"])
    return pd.Series(out, name=f"ci_{max_age}")


def fit_logistic(X: np.ndarray, d: np.ndarray, n: np.ndarray, iters: int = 50) -> np.ndarray:
    """Grouped-binomial logistic regression by IRLS: d successes out of n trials per row."""
    beta = np.zeros(X.shape[1])
    p0 = np.clip(d.sum() / n.sum(), 1e-12, 1 - 1e-12)
    beta[0] = np.log(p0 / (1 - p0))
    for _ in range(iters):
        eta = X @ beta
        p = 1 / (1 + np.exp(-eta))
        w = n * p * (1 - p)
        z = eta + (d - n * p) / np.maximum(w, 1e-300)
        new = np.linalg.solve(X.T @ (X * w[:, None]), X.T @ (w * z))
        if np.max(np.abs(new - beta)) < 1e-10:
            return new
        beta = new
    return beta


def hazard_design(lt: pd.DataFrame, base_year: int = 2008, hinges=(), age_cohort=False) -> tuple:
    """Design matrix for logit h(a, Y) = f(a) + beta*(Y - base) [+ hinge terms]: f(a) is one indicator per
    age (age 0 is the intercept). Returns (X, column names)."""
    ages = sorted(lt["age"].unique())
    cols, names = [np.ones(len(lt))], ["intercept"]
    for a in ages[1:]:
        cols.append((lt["age"] == a).to_numpy(float)); names.append(f"age_{a}")
    c = (lt["cohort"] - base_year).to_numpy(float)
    cols.append(c); names.append("beta")
    for name, tau in hinges:
        cols.append(np.maximum(0, lt["cohort"].to_numpy(float) - tau)); names.append(name)
    if age_cohort:
        for lo, hi, lab in [(2, 4, "beta_x_age2_4"), (5, 99, "beta_x_age5plus")]:
            cols.append(c * lt["age"].between(lo, hi).to_numpy(float)); names.append(lab)
    return np.column_stack(cols), names


def fit_hazard(lt: pd.DataFrame, **kw) -> dict:
    lt = lt[lt["n"] > 0]
    X, names = hazard_design(lt, **kw)
    b = fit_logistic(X, lt["d"].to_numpy(float), lt["n"].to_numpy(float))
    return dict(zip(names, b))


def moving_blocks(units, rng, block: int = 3) -> list:
    """Resample an ordered list of units by moving blocks of length `block`, to the original length."""
    units = list(units)
    starts = rng.integers(0, len(units) - block + 1, size=int(np.ceil(len(units) / block)))
    return [u for s in starts for u in units[s:s + block]][:len(units)]


def bootstrap_hazard(lt: pd.DataFrame, keys, reps: int = 999, seed: int = 20221130, **kw) -> pd.DataFrame:
    """Cohort-level moving-block bootstrap of hazard-model coefficients (protocol §6)."""
    rng = np.random.default_rng(seed)
    cohorts = sorted(lt["cohort"].unique())
    by = {y: g for y, g in lt.groupby("cohort")}
    out = []
    for _ in range(reps):
        sample = pd.concat([by[y] for y in moving_blocks(cohorts, rng)], ignore_index=True)
        try:
            fit = fit_hazard(sample, **kw)
        except np.linalg.LinAlgError:  # a resample with no cohorts after a hinge leaves its term undefined
            fit = {}
        out.append({k: fit.get(k, np.nan) for k in keys})
    return pd.DataFrame(out)


def loglinear_slope(years, values) -> float:
    x = np.asarray(years, float) - 2008
    return float(np.polyfit(x, np.log(np.asarray(values, float)), 1)[0])


def p1_growth(p1: pd.Series, d: pd.Series, reps: int = 999, seed: int = 20221130) -> dict:
    """Annual log-growth of P1 and of D over the same cohorts, and g1 - gD, with moving-block bootstrap
    CIs (block 3; both series resampled together)."""
    years = sorted(p1.index)
    g1, gd = loglinear_slope(years, p1[years]), loglinear_slope(years, d[years])
    rng = np.random.default_rng(seed)
    bs = []
    for _ in range(reps):
        ys = moving_blocks(years, rng)
        if len(set(ys)) < 3:
            continue
        a, b = loglinear_slope(ys, p1[ys]), loglinear_slope(ys, d[ys])
        bs.append((a, b, a - b))
    bs = np.array(bs)
    ci = lambda col: tuple(np.percentile(bs[:, col], [2.5, 97.5]))
    return {"g1": g1, "g1_ci": ci(0), "gD": gd, "gD_ci": ci(1), "diff": g1 - gd, "diff_ci": ci(2),
            "doubling_p1": np.log(2) / g1 if g1 > 0 else np.inf, "doubling_d": np.log(2) / gd if gd > 0 else np.inf}


def decision_cell(beta_ci, g1_ci) -> str:
    diluted = beta_ci[1] < 0
    rising = g1_ci[0] > 0
    if diluted:
        return "Diluted, with a growing absolute yield" if rising else "Diluted, with a stagnant or shrinking yield"
    return "Not diluted; yield growing" if rising else "Not diluted (unexpected; investigate the decomposition)"


# ---- segmented (continuous hinge) log-linear regression: secondary analysis 1 and H3(a) -------------
def _hinge_X(x: np.ndarray, taus=()) -> np.ndarray:
    return np.column_stack([np.ones_like(x), x - x.mean()] + [np.maximum(0.0, x - t) for t in taus])


def _sse(X, y):
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    r = y - X @ b
    return float(r @ r), b


def _best(x, y, tau_sets):
    best = (np.inf, None, None)
    for taus in tau_sets:
        sse, b = _sse(_hinge_X(x, taus), y)
        if sse < best[0]:
            best = (sse, taus, b)
    return best


def _resample(resid, rng, block):
    n = len(resid)
    starts = rng.integers(0, n - block + 1, size=int(np.ceil(n / block)))
    return np.concatenate([resid[i:i + block] for i in starts])[:n]


def segmented(series: pd.Series, n_boot: int = 999, block: int = 3, min_gap: int = 3, fixed=None,
              seed: int = 20221130) -> dict:
    """Continuous segmented log-linear regression with one estimated break (grid over years leaving
    >= 2 points each side), its bootstrap CI, a two-break test and, if `fixed` is given, a test of an
    added hinge fixed at that year. P-values come from a moving-block residual bootstrap under the
    one-break null, repeating the grid search each time."""
    s = series[series > 0].sort_index()
    x, y = s.index.to_numpy(float), np.log(s.to_numpy(float))
    cands = [t for t in x if x.min() + 2 <= t <= x.max() - 2]
    one = [(t,) for t in cands]
    two = [(a, b) for a in cands for b in cands if b - a >= min_gap]
    plus = [(a, fixed) for a in cands if fixed is not None and fixed - a >= min_gap]
    sse1, t1, b1 = _best(x, y, one)
    sse0, b0 = _sse(_hinge_X(x), y)
    fit1 = _hinge_X(x, t1) @ b1
    res1 = y - fit1
    rng = np.random.default_rng(seed)
    taus = [_best(x, fit1 + _resample(res1, rng, block), one)[1][0] for _ in range(n_boot)]
    out = {"n": len(x), "break": int(t1[0]), "break_ci": (int(np.percentile(taus, 2.5)), int(np.percentile(taus, 97.5))),
           "growth_pre_pct": 100 * (np.exp(b1[1]) - 1), "growth_post_pct": 100 * (np.exp(b1[1] + b1[2]) - 1),
           "growth_nobreak_pct": 100 * (np.exp(b0[1]) - 1),
           "aic_break_minus_none": len(x) * np.log(sse1 / sse0) + 2 * 2}
    stat = lambda yv, sets: (_best(x, yv, one)[0] - _best(x, yv, sets)[0]) / max(_best(x, yv, sets)[0], 1e-300)
    for label, sets in [("two_break", two), ("fixed", plus)]:
        if not sets:
            continue
        obs = stat(y, sets)
        null = [stat(fit1 + _resample(res1, rng, block), sets) for _ in range(n_boot)]
        out[f"p_{label}"] = float((1 + np.sum(np.array(null) >= obs)) / (n_boot + 1))
        if label == "fixed":
            _, tp, bp = _best(x, y, plus)
            out["fixed_other_break"] = int(tp[0])
            out["growth_before_fixed_pct"] = 100 * (np.exp(bp[1] + bp[2]) - 1)
            out["growth_after_fixed_pct"] = 100 * (np.exp(bp[1] + bp[2] + bp[3]) - 1)
    return out


# ---- design-group hazard model: secondary analysis 3 ------------------------------------------------
def fit_group_hazard(lt: pd.DataFrame, base_year: int = 2008, hinge: int = 2018) -> dict:
    """logit h(a, Y, g) = f(a) + beta*(Y-base) + gamma*g + delta1*g*(Y-base) + delta2*g*max(0, Y-hinge).
    `lt` has columns cohort, age, group (0/1), n, d."""
    lt = lt[lt["n"] > 0]
    ages = sorted(lt["age"].unique())
    c = (lt["cohort"] - base_year).to_numpy(float)
    g = lt["group"].to_numpy(float)
    cols = [np.ones(len(lt))] + [(lt["age"] == a).to_numpy(float) for a in ages[1:]]
    cols += [c, g, g * c, g * np.maximum(0, lt["cohort"].to_numpy(float) - hinge)]
    b = fit_logistic(np.column_stack(cols), lt["d"].to_numpy(float), lt["n"].to_numpy(float))
    beta, gamma, d1, d2 = b[-4:]
    return {"beta": beta, "gamma": gamma, "delta1": d1, "delta2": d2, "delta1_plus_delta2": d1 + d2}


def bootstrap_group_hazard(lt: pd.DataFrame, reps: int = 999, seed: int = 20221130, **kw) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    cohorts = sorted(lt["cohort"].unique())
    by = {y: grp for y, grp in lt.groupby("cohort")}
    out = []
    for _ in range(reps):
        try:
            out.append(fit_group_hazard(pd.concat([by[y] for y in moving_blocks(cohorts, rng)]), **kw))
        except np.linalg.LinAlgError:  # no post-hinge cohorts in this resample
            out.append({})
    return pd.DataFrame(out, columns=["beta", "gamma", "delta1", "delta2", "delta1_plus_delta2"])
