from pubinfl import icite


def test_fetch_icite_batches_dedupes_and_maps_by_pmid():
    urls = []

    def fake(url):
        urls.append(url)
        ids = url.split("pmids=")[1].split("&")[0].split("%2C")
        return {"data": [{"pmid": int(i), "references": [1, 2]} for i in ids if i != "3"]}

    out = icite.fetch_icite([1, 2, 2, 3, 4], ["pmid", "references"], get_json=fake, batch=2, sleep_s=0)
    assert len(urls) == 2                      # 4 unique PMIDs, batch size 2
    assert set(out) == {1, 2, 4}               # 3 missing from iCite -> absent
    assert out[1]["references"] == [1, 2]
    assert "fl=pmid%2Creferences" in urls[0]
