import gzip
import json

from pubinfl import cache


def test_read_jsonl_prefers_plain_then_falls_back_to_gz(tmp_path):
    p = tmp_path / "c.jsonl"
    with gzip.open(cache.gz_path(p), "wt") as fh:
        fh.write(json.dumps({"pmid": 1}) + "\n")
    assert cache.cache_exists(p)
    assert cache.read_jsonl(p) == [{"pmid": 1}]
    p.write_text(json.dumps({"pmid": 2}) + "\n")
    assert cache.read_jsonl(p) == [{"pmid": 2}]


def test_write_gz_copy_round_trips(tmp_path):
    p = tmp_path / "c.jsonl"
    p.write_text(json.dumps({"pmid": 3}) + "\n")
    cache.write_gz_copy(p)
    p.unlink()
    assert cache.read_jsonl(p) == [{"pmid": 3}]
