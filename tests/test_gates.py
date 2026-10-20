import pandas as pd

from pubinfl import gates


def test_coverage_counts_missing_and_null_refs_as_no_refs_and_dedupes():
    frame = pd.DataFrame({"pmid": [1, 2, 3, 4, 4], "year": [2000, 2000, 2000, 2001, 2001]})
    icite = {1: {"references": [10, 11]}, 2: {"references": None}, 4: {"references": []}}
    cov = gates.coverage_by_year(frame, icite).set_index("year")
    assert cov.loc[2000, "n_guidelines"] == 3
    assert cov.loc[2000, "n_in_icite"] == 2      # 3 missing from iCite
    assert cov.loc[2000, "n_with_refs"] == 1
    assert abs(cov.loc[2000, "coverage"] - 1 / 3) < 1e-9
    assert cov.loc[2001, "n_guidelines"] == 1    # duplicate PMID 4 counted once
    assert cov.loc[2001, "coverage"] == 0.0
    assert cov.loc[2000, "median_refs"] == 2.0   # median among guidelines with refs


def test_coverage_by_group_splits_by_full_text_availability():
    frame = pd.DataFrame({"pmid": [1, 2, 3, 4], "year": [2010] * 4, "has_pmc": [True, True, False, False]})
    icite = {1: {"references": [10]}, 2: {"references": [11, 12]}, 3: {"references": []}}
    cov = gates.coverage_by_group(frame, icite, ["year", "has_pmc"]).set_index("has_pmc")
    assert cov.loc[True, "coverage"] == 1.0
    assert cov.loc[False, "coverage"] == 0.0
    assert cov.loc[False, "n_in_icite"] == 1     # 4 missing from iCite
    assert cov.loc[True, "median_refs"] == 1.5


def test_gate_g1_lists_failing_years():
    cov = pd.DataFrame({"year": [2000, 2001, 2002], "coverage": [0.9, 0.69, 0.70]})
    passed, failing = gates.gate_g1(cov, threshold=0.70)
    assert passed is False
    assert failing == [2001]
    assert gates.gate_g1(cov[cov.year != 2001])[0] is True


def test_citation_ages_excludes_unknown_and_negative():
    ages, excl = gates.citation_ages(
        guideline_years={1: 2015},
        refs={1: [10, 11, 12, 13]},
        cited_years={10: 2010, 11: 2015, 12: 2016},   # 13 unknown; 12 is after the guideline
    )
    assert sorted(ages.tolist()) == [0, 5]
    assert excl == {"unknown_year": 1, "negative_age": 1}


def test_age_summary_shares():
    s = gates.age_summary(pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]))
    assert s["n"] == 10
    assert s["median"] == 5.5
    assert s["share_le_3"] == 0.3
    assert s["share_le_5"] == 0.5
    assert s["share_le_8"] == 0.8


def test_stratified_sample_is_deterministic_balanced_and_capped():
    frame = pd.DataFrame({"pmid": range(1, 1001), "year": [2008 + (i % 18) for i in range(1000)]})
    a = gates.stratified_sample(frame, n_total=200)
    b = gates.stratified_sample(frame, n_total=200)
    assert a["pmid"].tolist() == b["pmid"].tolist()
    assert len(a) == 200 and a["pmid"].is_unique
    assert a["stratum"].value_counts().to_dict() == {"2008-2013": 67, "2014-2019": 67, "2020-2025": 66}
    small = pd.concat([frame[frame.year >= 2020].head(10), frame[frame.year < 2020]])
    s = gates.stratified_sample(small, n_total=200)
    assert (s["stratum"] == "2020-2025").sum() == 10   # capped at what exists


def test_recode_subset_size():
    sample = pd.DataFrame({"pmid": range(200), "stratum": ["x"] * 200})
    assert len(gates.recode_subset(sample, frac=0.25)) == 50


def test_wilson_ci_known_value():
    lo, hi = gates.wilson_ci(160, 200)
    assert abs(lo - 0.7393) < 1e-3 and abs(hi - 0.8495) < 1e-3


def test_cohens_kappa_perfect_and_chance():
    assert gates.cohens_kappa(["Y", "N", "Y", "N"], ["Y", "N", "Y", "N"]) == 1.0
    assert abs(gates.cohens_kappa(["Y", "Y", "N", "N"], ["Y", "N", "Y", "N"])) < 1e-9


def test_score_g2_decision():
    coded = pd.DataFrame({"pmid": range(10), "eligible": ["Y"] * 7 + ["N"] * 3})
    recoded = pd.DataFrame({"pmid": [0, 1, 7, 8], "eligible": ["Y", "Y", "N", "N"]})
    s = gates.score_g2(coded, recoded)
    assert s["n"] == 10 and s["n_eligible"] == 7
    assert abs(s["ppv"] - 0.7) < 1e-9
    assert s["below_threshold"] is True     # PPV < 0.80
    assert s["kappa"] == 1.0 and s["n_recoded"] == 4


def test_sample_citation_pairs_balanced_and_deterministic():
    pairs = pd.DataFrame({"guideline_pmid": [i // 3 for i in range(60)],
                          "cited_pmid": range(1000, 1060),
                          "guideline_year": [2015] * 60})
    selected = set(range(1000, 1030))            # 30 selected, 30 other
    a = gates.sample_citation_pairs(pairs, selected, n_per_group=10)
    b = gates.sample_citation_pairs(pairs, selected, n_per_group=10)
    assert a["cited_pmid"].tolist() == b["cited_pmid"].tolist()
    assert a["group"].value_counts().to_dict() == {"selected": 10, "other": 10}


def test_sample_citation_pairs_caps_at_available():
    pairs = pd.DataFrame({"guideline_pmid": [1, 2, 3], "cited_pmid": [10, 11, 12],
                          "guideline_year": [2015] * 3})
    out = gates.sample_citation_pairs(pairs, {10}, n_per_group=5)
    assert (out["group"] == "selected").sum() == 1
    assert (out["group"] == "other").sum() == 2


def test_recode_subset_sorts_by_given_columns():
    pairs = pd.DataFrame({"guideline_pmid": [3, 1, 2, 4], "cited_pmid": [9, 8, 7, 6]})
    out = gates.recode_subset(pairs, frac=0.5, sort_by=["guideline_pmid", "cited_pmid"])
    assert len(out) == 2 and out["guideline_pmid"].is_monotonic_increasing
