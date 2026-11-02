import numpy as np
import pandas as pd

from pubinfl import analysis


def test_first_citations_takes_earliest_year_and_weight():
    gyear = {1: 2012, 2: 2010}
    refs = {1: [10, 11], 2: [10]}
    f = analysis.first_citations(gyear, refs, {2010: 0.5, 2012: 0.8}).set_index("pmid")
    assert f.loc[10, "first_year"] == 2010 and f.loc[10, "w"] == 2.0
    assert f.loc[11, "first_year"] == 2012 and f.loc[11, "w"] == 1.25


def test_life_table_risk_set_and_cumulative_incidence():
    first = pd.DataFrame({"pmid": [1, 2, 3], "first_year": [2023, 2024, 2020], "w": [1.0, 1.0, 1.0]})
    cohort_of = pd.Series({1: 2023, 2: 2023, 3: 2021})  # paper 3 cited before publication -> age 0
    lt = analysis.life_table(first, cohort_of, pd.Series({2023: 10, 2021: 5}), cohorts=[2021, 2023])
    c23 = lt[lt["cohort"] == 2023].set_index("age")
    assert list(c23["n"]) == [10, 9, 8] and list(c23["d"]) == [1, 1, 0]
    assert lt[(lt["cohort"] == 2021) & (lt["age"] == 0)]["d"].item() == 1
    ci = analysis.cumulative_incidence(lt, 1)
    assert np.isclose(ci[2023], 0.2)


def test_fit_logistic_recovers_known_slope():
    rng = np.random.default_rng(0)
    x = np.repeat(np.arange(10.0), 1)
    n = np.full(10, 1e6)
    p = 1 / (1 + np.exp(-(-3 - 0.1 * x)))
    d = n * p
    b = analysis.fit_logistic(np.column_stack([np.ones(10), x]), d, n)
    assert np.allclose(b, [-3, -0.1], atol=1e-6)


def test_p1_growth_difference_sign():
    years = range(2008, 2021)
    p1 = pd.Series({y: 100 * 1.02 ** (y - 2008) for y in years})
    d = pd.Series({y: 1000 * 1.05 ** (y - 2008) for y in years})
    r = analysis.p1_growth(p1, d, reps=50)
    assert r["diff"] < 0 and r["diff_ci"][1] < 0
    assert analysis.decision_cell((-0.1, -0.05), r["g1_ci"]) == "Diluted, with a growing absolute yield"


def test_segmented_finds_planted_break():
    years = np.arange(2008, 2026)
    y = np.where(years <= 2016, 0.05 * (years - 2008), 0.05 * 8 + 0.15 * (years - 2016))
    rng = np.random.default_rng(1)
    s = pd.Series(np.exp(y + rng.normal(0, 0.005, len(years))), index=years)
    r = analysis.segmented(s, n_boot=50, fixed=2022)
    assert r["break"] == 2016 and r["growth_post_pct"] > r["growth_pre_pct"]
    assert "p_fixed" in r and "p_two_break" in r


def test_group_hazard_recovers_group_terms():
    rows = []
    for y in range(2008, 2020):
        for a in range(3):
            for g in (0, 1):
                eta = -4 + 0.2 * a - 0.02 * (y - 2008) + g * (0.5 - 0.03 * (y - 2008) - 0.05 * max(0, y - 2014))
                n = 1e7
                rows.append({"cohort": y, "age": a, "group": g, "n": n, "d": n / (1 + np.exp(-eta))})
    r = analysis.fit_group_hazard(pd.DataFrame(rows), hinge=2014)
    assert np.allclose([r["beta"], r["gamma"], r["delta1"], r["delta2"]], [-0.02, 0.5, -0.03, -0.05], atol=1e-5)
