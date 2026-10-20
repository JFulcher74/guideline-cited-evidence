"""NIH iCite API client (https://icite.od.nih.gov/api)."""
import json
import time
import urllib.parse
import urllib.request

from pubinfl.ncbi import with_retries

ICITE_URL = "https://icite.od.nih.gov/api/pubs"


def _get_json(url):
    with urllib.request.urlopen(url, timeout=120) as r:
        return json.load(r)


def fetch_icite(pmids, fields, *, get_json=None, batch: int = 250, sleep_s: float = 0.2) -> dict:
    """Return {pmid: record} for PMIDs found in iCite. Missing PMIDs are absent.

    Batches of 250: the API returns HTTP 413 once the GET URL passes ~4 kB (400 PMIDs failed).
    """
    get_json = get_json or _get_json
    unique = list(dict.fromkeys(int(p) for p in pmids))
    out = {}
    for i in range(0, len(unique), batch):
        chunk = unique[i:i + batch]
        qs = urllib.parse.urlencode({"pmids": ",".join(map(str, chunk)), "fl": ",".join(fields)})
        data = with_retries(get_json, f"{ICITE_URL}?{qs}")
        for rec in data.get("data", []):
            out[int(rec["pmid"])] = rec
        time.sleep(sleep_s)
    return out
