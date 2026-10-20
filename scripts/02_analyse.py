#!/usr/bin/env python3
"""Growth analysis of PubMed strata: CAGR, doubling times, breakpoints, counterfactuals,
noise-discount scenarios and leave-one-out sensitivity.

Usage
  python scripts/02_analyse.py [--date-field dp|edat] [--discount 0.3] [--ramp]

Outputs (suffixed with the date field, e.g. _dp)
  data/processed/epoch_growth_<f>.csv      CAGR / doubling time / log-linear fit per stratum x epoch
  data/processed/breakpoints_<f>.csv       segmented regression: estimated break year + bootstrap CI,
                                           pre/post growth, comparison with a fixed 2022 break
  data/processed/counterfactual_<f>.csv    observed vs projected 2023-2025, two baselines
  data/processed/noise_sensitivity_<f>.csv raw vs effective volume across discount factors
  data/processed/loo_sensitivity_<f>.csv   selected secondary-analysis designs with each design left out
  figures/fig1_strata_<f>.png, fig2_ratio_<f>.png, fig3_noise_sensitivity_<f>.png, figS1_loo_<f>.png
"""
import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROC_DIR = ROOT / "data" / "processed"
FIG_DIR = ROOT / "figures"

MAIN_STRATA = ["total", "high_signal", "high_volume"]
RATIO = "ratio_hv_hs"  # high_volume / high_signal
EPOCHS = {
    "1980-2000": (1980, 2000),
    "2000-2022": (2000, 2022),
    "2022-2025": (2022, 2025),  # includes the 2022 baseline year, so 3 growth intervals
    "2023-2025": (2023, 2025),  # as specified; only 3 points / 2 intervals - interpret with care
}
BASELINE = (2010, 2022)
COVID_YEARS = (2020, 2021)
HYPOTHESISED_BREAK = 2022  # last pre-ChatGPT publication year; slope may change after it
BREAK_WINDOW = (2000, 2025)
BREAK_CANDIDATES = range(2005, 2024)  # leaves >= 2 years after any candidate
N_BOOT = 999
LOO_N_BOOT = 199  # leave-one-out sensitivity only, to keep run time reasonable
BLOCK_LEN = 3
SEED = 20221130  # ChatGPT public release date

# two-sided 95% t critical values, df = 1..30 (avoids a scipy dependency)
_T975 = [12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262, 2.228,
         2.201, 2.179, 2.160, 2.145, 2.131, 2.120, 2.110, 2.101, 2.093, 2.086,
         2.080, 2.074, 2.069, 2.064, 2.060, 2.056, 2.052, 2.048, 2.045, 2.042]


def t_crit(df: int) -> float:
    return _T975[df - 1] if 1 <= df <= 30 else 1.96


# ---------------------------------------------------------------- loading
def load_counts(date_field: str = "dp") -> pd.DataFrame:
    """Year-indexed wide table: main strata, the ratio, and loo_* columns."""
    long = pd.read_csv(RAW_DIR / f"pubmed_counts_{date_field}.csv")
    wide = long.pivot(index="year", columns="stratum", values="count").sort_index()
    loo = sorted(c for c in wide.columns if c.startswith("loo_"))
    wide = wide[MAIN_STRATA + loo].astype(float)
    wide[RATIO] = wide["high_volume"] / wide["high_signal"].replace(0, np.nan)
    return wide


# ---------------------------------------------------------------- growth metrics
def cagr(series: pd.Series, start: int, end: int):
    """CAGR between two years (endpoint method).

    If the series is zero at `start`, the first non-zero year in the epoch is used.
    Returns (rate, effective_start_year).
    """
    s = series.loc[start:end]
    nz = s[s > 0]
    if len(nz) < 2 or s.loc[end] <= 0:
        return float("nan"), None
    a = int(nz.index[0])
    return float((s.loc[end] / s.loc[a]) ** (1.0 / (end - a)) - 1.0), a


def doubling_time(rate: float) -> float:
    """Years to double at a constant annual growth rate; inf if not growing."""
    if np.isnan(rate):
        return float("nan")
    if rate <= 0:
        return float("inf")
    return float(np.log(2) / np.log1p(rate))


def loglinear_fit(series: pd.Series, start: int, end: int, exclude=()) -> dict:
    """OLS of ln(value) on year. Returns annual growth rate with 95% CI and the fit."""
    s = series.loc[start:end].drop(list(exclude), errors="ignore")
    s = s[s > 0]
    n = len(s)
    if n < 3:
        return dict(n=n, slope=np.nan, intercept=np.nan, growth=np.nan,
                    growth_lo=np.nan, growth_hi=np.nan)
    x, y = s.index.values.astype(float), np.log(s.values.astype(float))
    xm = x.mean()
    sxx = ((x - xm) ** 2).sum()
    slope = ((x - xm) * (y - y.mean())).sum() / sxx
    intercept = y.mean() - slope * xm
    resid = y - (intercept + slope * x)
    se = np.sqrt((resid ** 2).sum() / (n - 2) / sxx)
    t = t_crit(n - 2)
    g = lambda b: float(np.exp(b) - 1)
    return dict(n=n, slope=float(slope), intercept=float(intercept), growth=g(slope),
                growth_lo=g(slope - t * se), growth_hi=g(slope + t * se))


def epoch_table(df: pd.DataFrame, columns=MAIN_STRATA + [RATIO], epochs=EPOCHS) -> pd.DataFrame:
    rows = []
    for col in columns:
        for label, (a, b) in epochs.items():
            r, a_eff = cagr(df[col], a, b)
            fit = loglinear_fit(df[col], a, b)
            rows.append(dict(
                stratum=col, epoch=label, start=a, end=b, cagr_start_used=a_eff,
                cagr_pct=100 * r, doubling_years=doubling_time(r),
                loglin_growth_pct=100 * fit["growth"],
                loglin_ci_lo_pct=100 * fit["growth_lo"],
                loglin_ci_hi_pct=100 * fit["growth_hi"],
                loglin_doubling_years=doubling_time(fit["growth"]),
                n_points=fit["n"],
            ))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- segmented regression
def _hinge_design(x: np.ndarray, tau=None) -> np.ndarray:
    """Design matrix with one hinge column per break; `tau` is None, a year or a tuple."""
    taus = () if tau is None else np.atleast_1d(tau)
    cols = [np.ones_like(x), x - x.mean()] + [np.maximum(0.0, x - t) for t in taus]
    return np.column_stack(cols)


def _sse(X, y):
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    r = y - X @ beta
    return float(r @ r), beta


def _best_tau(x, y, candidates):
    best = (np.inf, None, None)
    for tau in candidates:
        sse, beta = _sse(_hinge_design(x, tau), y)
        if sse < best[0]:
            best = (sse, tau, beta)
    return best


def _aic(sse, n, k):
    return n * np.log(sse / n) + 2 * k


def fit_breakpoint(series: pd.Series, window=BREAK_WINDOW, candidates=BREAK_CANDIDATES,
                   n_boot=N_BOOT, block_len=BLOCK_LEN, seed=SEED) -> dict:
    """Continuous piecewise log-linear (hinge) model with one data-estimated break.

    ln(y_t) = a + b*t + c*max(0, t - tau). Growth is exp(b)-1 up to tau and
    exp(b+c)-1 afterwards. tau is chosen by grid search (min SSE); its 95% CI comes
    from a moving-block bootstrap of residuals (block length 3, to respect
    serial correlation). The fixed-break model at HYPOTHESISED_BREAK and a
    no-break model are compared by AIC.
    """
    s = series.loc[window[0]:window[1]]
    s = s[s > 0]
    x, y = s.index.values.astype(float), np.log(s.values.astype(float))
    n = len(x)
    cands = [t for t in candidates if x.min() + 2 <= t <= x.max() - 2]

    sse_hat, tau_hat, beta = _best_tau(x, y, cands)
    fitted = _hinge_design(x, tau_hat) @ beta
    resid = y - fitted

    rng = np.random.default_rng(seed)
    taus = []
    for _ in range(n_boot):
        starts = rng.integers(0, n - block_len + 1, size=int(np.ceil(n / block_len)))
        r_star = np.concatenate([resid[i:i + block_len] for i in starts])[:n]
        taus.append(_best_tau(x, fitted + r_star, cands)[1])
    taus = np.array(taus)

    sse_fix, beta_fix = _sse(_hinge_design(x, HYPOTHESISED_BREAK), y)
    sse_none, _ = _sse(_hinge_design(x), y)
    g = lambda b: float(np.exp(b) - 1)
    return dict(
        window=f"{window[0]}-{window[1]}", n=n,
        break_year=int(tau_hat),
        break_ci_lo=int(np.percentile(taus, 2.5)), break_ci_hi=int(np.percentile(taus, 97.5)),
        boot_share_tau_ge_2021=float((taus >= 2021).mean()),
        growth_pre_pct=100 * g(beta[1]), growth_post_pct=100 * g(beta[1] + beta[2]),
        fixed2022_growth_pre_pct=100 * g(beta_fix[1]),
        fixed2022_growth_post_pct=100 * g(beta_fix[1] + beta_fix[2]),
        aic_estimated=_aic(sse_hat, n, 4),  # a, b, c, tau
        aic_fixed2022=_aic(sse_fix, n, 3),
        aic_no_break=_aic(sse_none, n, 2),
        break_supported=bool(_aic(sse_hat, n, 4) < _aic(sse_none, n, 2) - 2),
    )


def breakpoint_table(df: pd.DataFrame, columns=MAIN_STRATA + [RATIO]) -> pd.DataFrame:
    return pd.DataFrame([dict(stratum=c, **fit_breakpoint(df[c])) for c in columns])


def _best_pair(x, y, pairs):
    best = (np.inf, None, None)
    for p in pairs:
        sse, beta = _sse(_hinge_design(x, p), y)
        if sse < best[0]:
            best = (sse, p, beta)
    return best


def _block_resample(resid, rng, block_len):
    n = len(resid)
    starts = rng.integers(0, n - block_len + 1, size=int(np.ceil(n / block_len)))
    return np.concatenate([resid[i:i + block_len] for i in starts])[:n]


def fit_two_breaks(series: pd.Series, window=BREAK_WINDOW, candidates=BREAK_CANDIDATES,
                   min_gap: int = 3, n_boot=N_BOOT, block_len=BLOCK_LEN, seed=SEED) -> dict:
    """Test for a second break on top of the best single break.

    Models (all continuous hinge, log scale):
      M1   one estimated break
      M2   two estimated breaks, tau1 < tau2, at least `min_gap` years apart
      M1+  one estimated break plus a break fixed at HYPOTHESISED_BREAK (2022)

    Because break years are grid-searched, AIC and F tables are anti-conservative.
    P-values therefore come from a moving-block residual bootstrap under the null
    M1 (the full grid search is repeated in every replicate):
      p_second_break     M2 vs M1   - is there any second change in growth?
      p_added_2022_break M1+ vs M1  - does growth change again after 2022?
    Break-year CIs come from a separate bootstrap around the M2 fit.
    """
    s = series.loc[window[0]:window[1]]
    s = s[s > 0]
    x, y = s.index.values.astype(float), np.log(s.values.astype(float))
    n = len(x)
    cands = [t for t in candidates if x.min() + 2 <= t <= x.max() - 2]
    pairs = [(a, b) for a in cands for b in cands if b - a >= min_gap]
    plus_pairs = [(a, HYPOTHESISED_BREAK) for a in cands if HYPOTHESISED_BREAK - a >= min_gap]

    def stats(yv):
        s1, t1, b1 = _best_tau(x, yv, cands)
        s2, p2, b2 = _best_pair(x, yv, pairs)
        sp, pp, bp = _best_pair(x, yv, plus_pairs)
        return (s1, t1, b1), (s2, p2, b2), (sp, pp, bp)

    (sse1, tau1, beta1), (sse2, pair2, beta2), (ssep, pairp, betap) = stats(y)
    f_two = (sse1 - sse2) / sse2
    f_plus = (sse1 - ssep) / ssep

    rng = np.random.default_rng(seed)
    fit1 = _hinge_design(x, tau1) @ beta1
    res1 = y - fit1
    f_two_null, f_plus_null = [], []
    for _ in range(n_boot):
        (b1, _, _), (b2, _, _), (bp, _, _) = stats(fit1 + _block_resample(res1, rng, block_len))
        f_two_null.append((b1 - b2) / b2)
        f_plus_null.append((b1 - bp) / bp)
    p_two = (1 + np.sum(np.array(f_two_null) >= f_two)) / (n_boot + 1)
    p_plus = (1 + np.sum(np.array(f_plus_null) >= f_plus)) / (n_boot + 1)

    fit2 = _hinge_design(x, pair2) @ beta2
    res2 = y - fit2
    boot_pairs = np.array([_best_pair(x, fit2 + _block_resample(res2, rng, block_len), pairs)[1]
                           for _ in range(n_boot)])

    g = lambda b: float(np.exp(b) - 1)
    return dict(
        window=f"{window[0]}-{window[1]}", n=n,
        m1_break=int(tau1),
        m2_break1=int(pair2[0]), m2_break2=int(pair2[1]),
        m2_break1_ci=f"{int(np.percentile(boot_pairs[:, 0], 2.5))}-{int(np.percentile(boot_pairs[:, 0], 97.5))}",
        m2_break2_ci=f"{int(np.percentile(boot_pairs[:, 1], 2.5))}-{int(np.percentile(boot_pairs[:, 1], 97.5))}",
        m2_share_break2_2021_2023=float(((boot_pairs[:, 1] >= 2021) & (boot_pairs[:, 1] <= 2023)).mean()),
        m2_growth_seg1_pct=100 * g(beta2[1]),
        m2_growth_seg2_pct=100 * g(beta2[1] + beta2[2]),
        m2_growth_seg3_pct=100 * g(beta2[1] + beta2[2] + beta2[3]),
        m1plus_break1=int(pairp[0]),
        m1plus_growth_pre2022_pct=100 * g(betap[1] + betap[2]),
        m1plus_growth_post2022_pct=100 * g(betap[1] + betap[2] + betap[3]),
        aic_m1=_aic(sse1, n, 4), aic_m2=_aic(sse2, n, 6), aic_m1plus2022=_aic(ssep, n, 5),
        p_second_break=float(p_two), p_added_2022_break=float(p_plus),
    )


def two_break_table(df: pd.DataFrame, columns=MAIN_STRATA + [RATIO]) -> pd.DataFrame:
    return pd.DataFrame([dict(stratum=c, **fit_two_breaks(df[c])) for c in columns])


# ---------------------------------------------------------------- noise discount
def apply_noise_discount(df: pd.DataFrame, factor, start_year: int = HYPOTHESISED_BREAK + 1,
                         columns=("total", "high_volume"), ramp: bool = False) -> pd.DataFrame:
    """Model the gap between raw volume and effective clinical signal.

    Returns a copy of `df` where, for years >= start_year, each selected column is
    multiplied by (1 - discount). A discount of 0.3 means 30% of post-2022 volume
    is assumed to carry no effective clinical signal.

    factor : float in [0, 1], or a {year: float} mapping for a per-year schedule.
    ramp   : if True and `factor` is a scalar, phase the discount in linearly so
             it reaches `factor` in the last year, instead of a step change.

    This is a scenario parameter, NOT an empirical estimate: report results across
    a range of factors (see sensitivity_table).
    """
    out = df.copy().astype(float)
    years = out.index[out.index >= start_year]
    if isinstance(factor, dict):
        f = pd.Series({y: float(factor.get(y, 0.0)) for y in years})
    else:
        f = pd.Series(float(factor), index=years)
        if ramp and len(years) > 1:
            f = pd.Series(np.linspace(factor / len(years), factor, len(years)), index=years)
    if ((f < 0) | (f > 1)).any():
        raise ValueError("noise discount must lie in [0, 1]")
    for col in columns:
        if col in out.columns:
            out.loc[years, col] = out.loc[years, col] * (1.0 - f)
    return out


def sensitivity_table(df: pd.DataFrame, factors=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5),
                      column: str = "total", ramp: bool = False) -> pd.DataFrame:
    """Raw vs effective volume and growth for a sweep of discount factors."""
    rows = []
    last = df.index.max()
    for d in factors:
        eff = apply_noise_discount(df, d, columns=(column,), ramp=ramp)[column]
        r, _ = cagr(eff, HYPOTHESISED_BREAK, last)
        rows.append(dict(
            discount=d, column=column,
            raw_last=float(df.loc[last, column]), effective_last=float(eff.loc[last]),
            gap_last=float(df.loc[last, column] - eff.loc[last]),
            cagr_2022_last_pct=100 * r, doubling_years=doubling_time(r),
        ))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- counterfactual
def counterfactual(df: pd.DataFrame, columns=MAIN_STRATA + [RATIO], baseline=BASELINE,
                   start_year=HYPOTHESISED_BREAK + 1) -> pd.DataFrame:
    """Project the baseline log-linear trend forward and compare with observed.

    Two baselines: all years, and excluding the COVID-affected years.
    """
    rows = []
    for variant, excl in [("all_years", ()), ("excl_covid", COVID_YEARS)]:
        for col in columns:
            fit = loglinear_fit(df[col], *baseline, exclude=excl)
            if np.isnan(fit["slope"]):
                continue
            for yr in df.index[df.index >= start_year]:
                proj = float(np.exp(fit["intercept"] + fit["slope"] * yr))
                obs = float(df.loc[yr, col])
                rows.append(dict(baseline=f"{baseline[0]}-{baseline[1]}", variant=variant,
                                 stratum=col, year=yr, observed=obs, projected=proj,
                                 excess=obs - proj, obs_over_proj=obs / proj))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- leave-one-out
def loo_table(df: pd.DataFrame) -> pd.DataFrame:
    """Headline metrics recomputed with each secondary-analysis design left out."""
    rows = []
    variants = {"all_designs": df["high_volume"]}
    variants.update({c[4:]: df[c] for c in df.columns if c.startswith("loo_")})
    last = df.index.max()
    for name, hv in variants.items():
        ratio = hv / df["high_signal"].replace(0, np.nan)
        r, _ = cagr(hv, HYPOTHESISED_BREAK, last)
        bp = fit_breakpoint(ratio)
        tb = fit_two_breaks(ratio, n_boot=LOO_N_BOOT)
        rows.append(dict(
            design_left_out=name if name != "all_designs" else "(none)",
            hv_cagr_2022_last_pct=100 * r,
            ratio_2022=float(ratio.loc[HYPOTHESISED_BREAK]), ratio_last=float(ratio.loc[last]),
            ratio_break_year=bp["break_year"],
            ratio_break_ci=f"{bp['break_ci_lo']}-{bp['break_ci_hi']}",
            ratio_m2_breaks=f"{tb['m2_break1']}, {tb['m2_break2']}",
            ratio_p_second_break=tb["p_second_break"],
            ratio_p_added_2022_break=tb["p_added_2022_break"],
        ))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- figures
def _break_line(ax):
    ax.axvline(HYPOTHESISED_BREAK + 0.5, ls="--", color="grey", lw=0.8)


def make_figures(df: pd.DataFrame, bps: pd.DataFrame, tbs: pd.DataFrame, ramp: bool, tag: str) -> None:
    FIG_DIR.mkdir(exist_ok=True)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    for col in MAIN_STRATA:
        ax.plot(df.index, df[col].replace(0, np.nan), label=col.replace("_", " "))
    _break_line(ax)
    ax.set_yscale("log")
    ax.set_xlabel("Publication year")
    ax.set_ylabel("PubMed records (log scale)")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIG_DIR / f"fig1_strata_{tag}.png", dpi=300)
    plt.close(fig)

    bp = bps.set_index("stratum").loc[RATIO]
    s = df[RATIO].loc[BREAK_WINDOW[0]:BREAK_WINDOW[1]].dropna()
    s = s[s > 0]
    x = s.index.values.astype(float)
    _, beta = _sse(_hinge_design(x, bp["break_year"]), np.log(s.values))
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(df.index[df.index >= 1990], df[RATIO][df.index >= 1990], "o", ms=3, label="observed")
    ax.plot(x, np.exp(_hinge_design(x, bp["break_year"]) @ beta), lw=1.5,
            label=f"segmented fit (break {bp['break_year']}, 95% CI {bp['break_ci_lo']}-{bp['break_ci_hi']})")
    ax.axvspan(bp["break_ci_lo"], bp["break_ci_hi"], color="grey", alpha=0.15)
    tb = tbs.set_index("stratum").loc[RATIO]
    pair = (tb["m2_break1"], tb["m2_break2"])
    _, beta2 = _sse(_hinge_design(x, pair), np.log(s.values))
    ax.plot(x, np.exp(_hinge_design(x, pair) @ beta2), lw=1.2, ls=":",
            label=f"two-break fit ({pair[0]}, {pair[1]}; p second break = {tb['p_second_break']:.3f})")
    _break_line(ax)
    ax.set_yscale("log")
    ax.set_xlabel("Publication year")
    ax.set_ylabel("High-volume / high-signal records (log)")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG_DIR / f"fig2_ratio_{tag}.png", dpi=300)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    recent = df.index >= 2015
    ax.plot(df.index[recent], df.loc[recent, "total"], color="black", label="raw")
    for d in (0.1, 0.3, 0.5):
        eff = apply_noise_discount(df, d, columns=("total",), ramp=ramp)["total"]
        ax.plot(df.index[recent], eff[recent], ls="--", label=f"effective (discount {d:.0%})")
    _break_line(ax)
    ax.set_xlabel("Publication year")
    ax.set_ylabel("PubMed records")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIG_DIR / f"fig3_noise_sensitivity_{tag}.png", dpi=300)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    recent = df.index >= 2010
    hs = df["high_signal"].replace(0, np.nan)
    ax.plot(df.index[recent], (df["high_volume"] / hs)[recent], color="black", lw=2, label="all selected designs")
    for c in [c for c in df.columns if c.startswith("loo_")]:
        ax.plot(df.index[recent], (df[c] / hs)[recent], lw=0.9, label=f"without {c[4:].replace('_', ' ')}")
    _break_line(ax)
    ax.set_xlabel("Publication year")
    ax.set_ylabel("High-volume / high-signal records")
    ax.legend(frameon=False, fontsize=7)
    fig.tight_layout()
    fig.savefig(FIG_DIR / f"figS1_loo_{tag}.png", dpi=300)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--date-field", default="dp")
    ap.add_argument("--discount", type=float, default=0.3, help="headline noise discount (scenario)")
    ap.add_argument("--ramp", action="store_true", help="phase discount in linearly from 2023")
    args = ap.parse_args()
    tag = args.date_field

    df = load_counts(tag)
    PROC_DIR.mkdir(parents=True, exist_ok=True)

    epochs = epoch_table(df)
    bps = breakpoint_table(df)
    cf = counterfactual(df)
    tbs = two_break_table(df)
    epochs.to_csv(PROC_DIR / f"epoch_growth_{tag}.csv", index=False)
    bps.to_csv(PROC_DIR / f"breakpoints_{tag}.csv", index=False)
    tbs.to_csv(PROC_DIR / f"two_breaks_{tag}.csv", index=False)
    cf.to_csv(PROC_DIR / f"counterfactual_{tag}.csv", index=False)
    sensitivity_table(df, ramp=args.ramp).to_csv(PROC_DIR / f"noise_sensitivity_{tag}.csv", index=False)
    loo = loo_table(df)
    loo.to_csv(PROC_DIR / f"loo_sensitivity_{tag}.csv", index=False)
    make_figures(df, bps, tbs, args.ramp, tag)

    pd.set_option("display.width", 200)
    print(epochs[["stratum", "epoch", "cagr_start_used", "cagr_pct", "doubling_years",
                  "loglin_ci_lo_pct", "loglin_ci_hi_pct"]].round(2).to_string(index=False))
    print()
    print(bps.round(2).to_string(index=False))
    print()
    print(tbs.round(3).to_string(index=False))
    print()
    print(cf.round(2).to_string(index=False))
    print()
    print(loo.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
