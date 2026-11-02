import pytest

from pubinfl import ncbi


def fake_esearch(count, ids):
    calls = []

    def _esearch(term, retmax):
        calls.append((term, retmax))
        return {"Count": str(count), "IdList": [str(i) for i in ids]}

    return _esearch, calls


def test_search_pmids_builds_year_query_and_returns_ints():
    es, calls = fake_esearch(3, [11, 12, 13])
    out = ncbi.search_pmids(ncbi.F1_QUERY, 2015, esearch=es)
    assert out == [11, 12, 13]
    assert calls[0][0] == '("Practice Guideline"[pt] NOT preprint[pt]) AND 2015[dp]'
    assert calls[0][1] == 9999


def test_search_pmids_raises_when_count_exceeds_retmax():
    es, _ = fake_esearch(10_000, list(range(9999)))
    with pytest.raises(ValueError, match="exceeds"):
        ncbi.search_pmids(ncbi.F1_QUERY, 2015, esearch=es)


def test_with_retries_retries_then_succeeds():
    state = {"n": 0}

    def flaky():
        state["n"] += 1
        if state["n"] < 3:
            raise OSError("boom")
        return "ok"

    assert ncbi.with_retries(flaky, sleep=lambda s: None) == "ok"
    assert state["n"] == 3


def test_with_retries_gives_up():
    def always_fail():
        raise OSError("boom")

    with pytest.raises(RuntimeError, match="after 2 retries"):
        ncbi.with_retries(always_fail, retries=2, sleep=lambda s: None)


def test_fetch_summaries_parses_collective_authors():
    payload = {"result": {
        "uids": ["5"],
        "5": {"uid": "5", "title": "T", "source": "J", "pubdate": "2015 Jan",
              "authors": [{"name": "Smith J", "authtype": "Author"},
                          {"name": "ESC Task Force", "authtype": "CollectiveName"}]},
    }}
    out = ncbi.fetch_summaries([5], get_json=lambda url: payload)
    assert out[5]["title"] == "T"
    assert out[5]["journal"] == "J"
    assert out[5]["first_author"] == "Smith J"
    assert out[5]["collective_authors"] == "ESC Task Force"


def test_configure_entrez_requires_email(monkeypatch):
    monkeypatch.delenv("NCBI_EMAIL", raising=False)
    with pytest.raises(SystemExit):
        ncbi.configure_entrez()


def test_search_subset_chunks_ids_and_returns_matching_set():
    calls = []

    def es(term, retmax):
        calls.append(term)
        ids = [t for t in (1, 2, 3, 4, 5) if f"{t}[uid]" in term and t % 2 == 1]
        return {"Count": str(len(ids)), "IdList": [str(i) for i in ids]}

    out = ncbi.search_subset("DESIGN", [1, 2, 3, 4, 5], esearch=es, chunk=2)
    assert out == {1, 3, 5}
    assert len(calls) == 3                       # 5 ids in chunks of 2
    assert calls[0].startswith("(DESIGN) AND (")


def test_fetch_summaries_returns_pmcid():
    payload = {"result": {"uids": ["5"], "5": {"uid": "5", "title": "T", "source": "J",
               "articleids": [{"idtype": "pubmed", "value": "5"}, {"idtype": "pmc", "value": "PMC123"}]}}}
    assert ncbi.fetch_summaries([5], get_json=lambda url: payload)[5]["pmcid"] == "PMC123"


def test_selected_designs_query_excludes_gbd_consortium_from_gbd_arm_only():
    q = ncbi.SELECTED_DESIGNS_QUERY
    assert q.count("(") == q.count(")")
    assert f'("Global Burden of Disease"[tiab] NOT {ncbi.GBD_CONSORTIUM_QUERY})' in q
    assert q.count(" NOT ") == 1                 # other designs are not filtered by IHME authorship
    assert '"Institute for Health Metrics and Evaluation"[ad]' in ncbi.GBD_CONSORTIUM_QUERY


def test_f2_body_query_adds_guideline_words_and_exclusions():
    q = ncbi.f2_body_query('"ESC Scientific Document Group"[cn]')
    assert q.startswith('(("ESC Scientific Document Group"[cn]) AND (guideline*[tiab]')
    assert q.endswith('NOT (preprint[pt] OR Comment[pt] OR "Published Erratum"[pt] OR News[pt])')


def test_f2_clean_keep():
    assert ncbi.f2_clean_keep("2025 ESC Guidelines for the management of myocarditis", ["Journal Article"])
    assert ncbi.f2_clean_keep("ACR Appropriateness Criteria® Shoulder Pain", ["Journal Article"])
    assert ncbi.f2_clean_keep("Some title", ["Practice Guideline", "Journal Article"])
    assert not ncbi.f2_clean_keep("Adherence to the 2016 ESC guidelines in practice", ["Journal Article"])
    assert not ncbi.f2_clean_keep("WHO guidelines on hepatitis C", ["Editorial"])
    assert not ncbi.f2_clean_keep("Registry of cardiomyopathy", ["Journal Article"])


def test_selected_design_arms_rebuild_the_pooled_query():
    assert "(" + " OR ".join(ncbi.SELECTED_DESIGN_ARMS.values()) + ")" == ncbi.SELECTED_DESIGNS_QUERY
