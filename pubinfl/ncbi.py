"""NCBI E-utilities helpers: configuration, retries, PMID search, summaries."""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

from Bio import Entrez

SLEEP_NO_KEY = 0.35
SLEEP_WITH_KEY = 0.11
MAX_RETRIES = 5
RETMAX = 9999
F1_QUERY = '"Practice Guideline"[pt] NOT preprint[pt]'
# Research denominator D (protocol §3.2): research-type journal articles, MeSH-independent.
D_QUERY = ('"Journal Article"[pt] NOT (Comment[pt] OR Editorial[pt] OR Letter[pt] OR News[pt] '
           'OR "Published Erratum"[pt] OR Guideline[pt] OR "Practice Guideline"[pt] OR preprint[pt])')
ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"


def configure_entrez() -> float:
    """Set Entrez email/tool/api_key from the environment; return the per-call sleep."""
    email = os.environ.get("NCBI_EMAIL", "").strip()
    if not email or "@" not in email:
        sys.exit("NCBI_EMAIL is not set. NCBI requires a contact address: "
                 "export NCBI_EMAIL=you@example.com")
    Entrez.email = email
    Entrez.tool = "pubmed-inflation-meta-research"
    key = os.environ.get("NCBI_API_KEY", "").strip()
    if key:
        Entrez.api_key = key
    return SLEEP_WITH_KEY if key else SLEEP_NO_KEY


def with_retries(fn, *args, retries=MAX_RETRIES, sleep=time.sleep, **kwargs):
    for attempt in range(1, retries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:  # network, HTTP 429, parse errors
            print(f"  retry {attempt}/{retries} after error ({exc})", file=sys.stderr)
            sleep(2 ** attempt)
    raise RuntimeError(f"Failed after {retries} retries: {getattr(fn, '__name__', fn)}")


def _entrez_esearch(term, retmax):
    with Entrez.esearch(db="pubmed", term=term, retmax=retmax) as h:
        return Entrez.read(h)


def search_pmids(query: str, year: int, *, esearch=None, sleep_s: float = 0.0) -> list[int]:
    """All PMIDs matching `query` in publication year `year`. Raises if truncated."""
    esearch = esearch or _entrez_esearch
    term = f"({query}) AND {year}[dp]"
    res = with_retries(esearch, term, RETMAX)
    time.sleep(sleep_s)
    count = int(res["Count"])
    if count > RETMAX:
        raise ValueError(f"{count} records for {year} exceeds retmax {RETMAX}; split the query")
    return [int(i) for i in res["IdList"]]


def _get_json(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r)


def fetch_summaries(pmids, *, get_json=None, batch: int = 200, sleep_s: float = 0.0) -> dict:
    """PubMed esummary (JSON) for PMIDs -> {pmid: {title, journal, pubdate, first_author, collective_authors}}."""
    get_json = get_json or _get_json
    out = {}
    pmids = list(dict.fromkeys(int(p) for p in pmids))
    for i in range(0, len(pmids), batch):
        chunk = pmids[i:i + batch]
        params = {"db": "pubmed", "id": ",".join(map(str, chunk)), "retmode": "json",
                  "email": os.environ.get("NCBI_EMAIL", ""), "tool": "pubmed-inflation-meta-research"}
        if os.environ.get("NCBI_API_KEY"):
            params["api_key"] = os.environ["NCBI_API_KEY"]
        res = with_retries(get_json, f"{ESUMMARY_URL}?{urllib.parse.urlencode(params)}")["result"]
        for uid in res.get("uids", []):
            rec = res[uid]
            authors = rec.get("authors") or []
            people = [a["name"] for a in authors if a.get("authtype") == "Author"]
            groups = [a["name"] for a in authors if a.get("authtype") == "CollectiveName"]
            out[int(uid)] = {
                "title": rec.get("title", ""),
                "journal": rec.get("source", ""),
                "pubdate": rec.get("pubdate", ""),
                "first_author": people[0] if people else "",
                "collective_authors": "; ".join(groups),
                "pmcid": next((x["value"] for x in rec.get("articleids", []) if x.get("idtype") == "pmc"), ""),
            }
        time.sleep(sleep_s)
    return out


# GBD arm = reanalyses by teams outside the GBD consortium (protocol v2.3.1, §3.5). Excluded:
# collaborator-group bylines ("GBD 2019 ... Collaborators", "Global Burden of Disease Cancer
# Collaboration") and any paper with an author at IHME, which also catches flagship papers
# listed under individual authors (e.g. the GBD 2010 Lancet papers).
GBD_CONSORTIUM_QUERY = ('(GBD[cn] OR "Global Burden of Disease"[cn] OR "Global Burden of Diseases"[cn] '
                        'OR "Institute for Health Metrics and Evaluation"[ad])')

# The six arms of the selected-designs query (protocol §3.5), used only for the descriptive breakdown.
SELECTED_DESIGN_ARMS = {
    "two_sample_mr": '(("two-sample"[tiab] OR "two sample"[tiab]) AND Mendelian[tiab] AND (randomization[tiab] OR randomisation[tiab]))',
    "bibliometric": "(bibliometric*[tiab] OR scientometric*[tiab])",
    "nhanes_cross_sectional": '((NHANES[tiab] OR "National Health and Nutrition Examination Survey"[tiab]) AND ("cross-sectional"[tiab] OR "cross sectional"[tiab]))',
    "gbd_reanalysis": f'("Global Burden of Disease"[tiab] NOT {GBD_CONSORTIUM_QUERY})',
    "network_pharmacology": '"network pharmacology"[tiab]',
    "faers_disproportionality": '((FAERS[tiab] OR "Adverse Event Reporting System"[tiab]) AND disproportionality[tiab])',
}

# Differs from `high_volume` in 01_extract_pubmed.py (v1 exploratory strata) by the GBD exclusion.
SELECTED_DESIGNS_QUERY = (
    '((("two-sample"[tiab] OR "two sample"[tiab]) AND Mendelian[tiab] AND (randomization[tiab] OR randomisation[tiab])) '
    'OR (bibliometric*[tiab] OR scientometric*[tiab]) '
    'OR ((NHANES[tiab] OR "National Health and Nutrition Examination Survey"[tiab]) AND ("cross-sectional"[tiab] OR "cross sectional"[tiab])) '
    f'OR ("Global Burden of Disease"[tiab] NOT {GBD_CONSORTIUM_QUERY}) '
    'OR "network pharmacology"[tiab] '
    'OR ((FAERS[tiab] OR "Adverse Event Reporting System"[tiab]) AND disproportionality[tiab]))'
)


# Frame F2 (protocol §3.1): each named body's frozen rule (manuscript/f2_named_bodies.csv) combined
# with guideline-type words, excluding preprints, comments, errata and news.
F2_GUIDELINE_WORDS = ('(guideline*[tiab] OR recommendation*[tiab] OR "consensus statement"[tiab] '
                      'OR "position statement"[tiab])')
F2_EXCLUDE = '(preprint[pt] OR Comment[pt] OR "Published Erratum"[pt] OR News[pt])'


# F2 cleaning rule for the sensitivity analysis (protocol §3.1, added 2026-11-02 before any analysis).
# Keep a record if it has a guideline publication type or a guideline-type title, unless its
# publication type is a research, comment or correspondence type, or its title marks it as research
# about guidelines, commentary, a statement without recommendations, or a withdrawn record.
F2_CLEAN_KEEP_PT = {"Practice Guideline", "Guideline"}
F2_CLEAN_DROP_PT = {"Editorial", "Letter", "Comment", "Case Reports", "Comparative Study", "Observational Study",
                    "Multicenter Study", "Retracted Publication", "Evaluation Study", "Randomized Controlled Trial",
                    "Clinical Trial", "Published Erratum", "News"}
F2_CLEAN_TITLE_KEEP = re.compile(
    r"guideline|recommendation|appropriateness criteria|appropriate use criteria|position on |best practice advice"
    r"|consensus statement|practice parameter|standards of (medical )?care|task force report|clinical policy", re.I)
F2_CLEAN_TITLE_DROP = re.compile(
    r"systematic review for|review of |evolution of|evolution and|registr|validation of|implementing|\bcase\b|trends"
    r"|after the|since the|fragility|discordance|endorsement|commentary|webinar|summit|ethic|author response|reply"
    r"|adherence|compliance|withdrawn|q and a|\bq&a\b|era of|impact of|combining|misguided|reconsidering"
    r"|scientific statement|policy statement|position statement|leveraging|bridging the gap|disparit|mortality", re.I)


def f2_clean_keep(title: str, pubtypes) -> bool:
    pt = set(pubtypes)
    if pt & F2_CLEAN_DROP_PT or F2_CLEAN_TITLE_DROP.search(title):
        return False
    return bool(pt & F2_CLEAN_KEEP_PT) or bool(F2_CLEAN_TITLE_KEEP.search(title))


def f2_body_query(rule: str) -> str:
    return f"(({rule}) AND {F2_GUIDELINE_WORDS}) NOT {F2_EXCLUDE}"


def search_subset(query: str, pmids, *, esearch=None, chunk: int = 300, sleep_s: float = 0.0) -> set:
    """Which of `pmids` match `query`? Searches `(query) AND (id[uid] OR ...)` in chunks."""
    esearch = esearch or _entrez_esearch
    ids = list(dict.fromkeys(int(p) for p in pmids))
    hits = set()
    for i in range(0, len(ids), chunk):
        sub = ids[i:i + chunk]
        term = f"({query}) AND ({' OR '.join(f'{p}[uid]' for p in sub)})"
        res = with_retries(esearch, term, len(sub))
        hits |= {int(x) for x in res["IdList"]}
        time.sleep(sleep_s)
    return hits
