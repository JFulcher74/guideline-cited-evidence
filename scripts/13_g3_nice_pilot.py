#!/usr/bin/env python3
"""G3: NICE reference match-rate pilot (protocol §3.1 F3 and the G3 gate).

Draws NICE guidelines (NG1-NG199, first published 2015-2020) in random order, seed 20221130, until
10 are eligible. For each, downloads the evidence-review PDFs listed on its Evidence page, extracts
the numbered "References" lists, de-duplicates them within the guideline, and matches each reference
to a PMID with the PubMed citation matcher. A match counts only if exactly one PMID is returned and
its first author and year (+/-1) agree with the reference.

Usage: NCBI_EMAIL=you@example.com python scripts/13_g3_nice_pilot.py
Needs pdftotext (poppler). PDFs are cached in data/raw/nice/ (not committed).
Writes data/gates/g3_nice_sample.csv, g3_nice_references.csv and g3_nice_summary.csv.
"""
import json
import random
import re
import subprocess
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pubinfl import gates, ncbi  # noqa: E402

RAW = ROOT / "data" / "raw" / "nice"
OUT_SAMPLE = ROOT / "data" / "gates" / "g3_nice_sample.csv"
OUT_REFS = ROOT / "data" / "gates" / "g3_nice_references.csv"
OUT_SUMMARY = ROOT / "data" / "gates" / "g3_nice_summary.csv"
NICE = "https://www.nice.org.uk"
CITMATCH = "https://pubmed.ncbi.nlm.nih.gov/api/citmatch/"
SEED, N_TARGET, NG_MAX, YEARS = 20221130, 10, 199, range(2015, 2021)
UA = {"User-Agent": "pubmed-inflation-meta-research (academic pilot)"}
EXCLUDE_DOC = re.compile(r"method|consultation|comment|stakeholder|equality|scope|committee|minutes|"
                         r"declaration|interest|surveillance|impact|tools|resource", re.I)
JOURNAL_LIKE = re.compile(r"\b(?:19|20)\d{2}\s*[;,]\s*\d+")
ENTRY = re.compile(r"^\s{0,6}(\d{1,4})\.?\s{1,}(\S.*)$")
STOP = re.compile(r"^(\d+(\.\d+)*\.?\s+)?(Appendices|Appendix\s+[A-Z]\b|Glossary|Abbreviations|Acronyms)", re.I)


def get(url: str, binary=False):
    def _get():
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
            return r.geturl(), r.read()
    final, body = ncbi.with_retries(_get)
    time.sleep(1.0)
    return final, (body if binary else body.decode("utf-8", "replace"))


def guideline_meta(n: int):
    """(title, first-published year) for NGn, or None if the page is missing or redirects elsewhere."""
    try:
        final, html = get(f"{NICE}/guidance/ng{n}")
    except RuntimeError:
        return None
    if f"/guidance/ng{n}" not in final.lower():
        return None
    year = re.search(r'<time[^>]*datetime="(\d{4})-', html)
    title = re.search(r"<title>Overview \| ([^|<]+)", html)
    return (title.group(1).strip() if title else ""), (int(year.group(1)) if year else None)


def evidence_pdfs(n: int) -> list:
    _, html = get(f"{NICE}/guidance/ng{n}/evidence")
    links = list(dict.fromkeys(re.findall(rf'href="(/guidance/ng{n}/evidence/[^"]*-pdf-\d+)"', html, re.I)))
    reviews = [l for l in links if not EXCLUDE_DOC.search(l.rsplit("/", 1)[1])
               and not re.search(r"full-guideline|appendi", l.rsplit("/", 1)[1])]
    return reviews or [l for l in links if "full-guideline" in l]


def pdf_text(n: int, link: str) -> str:
    path = RAW / f"ng{n}" / (link.rsplit("/", 1)[1] + ".pdf")
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        _, body = get(NICE + link, binary=True)
        path.write_bytes(body)
    res = subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True)
    return res.stdout if res.returncode == 0 else ""


HEADING = re.compile(r"^\s*(\d+(\.\d+)*\.?\s+)?(References|Reference list|Bibliography)\b[^.]{0,50}$", re.I)
YEAR = re.compile(r"\b(?:19|20)\d{2}\b")
AUTHOR_START = re.compile(r"^[A-Z][A-Za-z'’\-]+(?: [A-Z][A-Za-z'’\-]+)?,? (?:[A-Z]{1,3}|[A-Z]\.(?: ?[A-Z]\.)*)[,.]? ")


def _split_block(block: list) -> list:
    """Split an unnumbered block of lines into entries: by hanging indent when it has one,
    otherwise at author-like lines that follow a line ending an entry."""
    if not block:
        return []
    indents = {len(l) - len(l.lstrip()) for l in block}
    if len(indents) == 1 or not re.match(r"^\s{0,2}\S", block[0]):
        # No hanging indent: a new entry starts at an author-like line after a line that ends one.
        out, cur = [], []
        for ln in block:
            if cur and AUTHOR_START.match(ln.strip()) and re.search(r"[.\d)\]]\s*$", cur[-1]):
                out.append(" ".join(cur))
                cur = []
            cur.append(ln.strip())
        return out + ([" ".join(cur)] if cur else [])
    out, cur, prev_indented = [], [], False
    for ln in block:
        flush_left = re.match(r"^\s{0,2}\S", ln) is not None
        if flush_left and prev_indented and cur:
            out.append(" ".join(cur))
            cur = []
        cur.append(ln.strip())
        prev_indented = not flush_left
    if cur:
        out.append(" ".join(cur))
    return out


def parse_references(text: str) -> list:
    """Entries under each 'References' or 'Bibliography' heading, numbered or author-year.
    Running headers and footers (lines that open or close three or more pages) and page numbers are dropped, and
    entries without a year are discarded."""
    firsts = {}
    for pg in text.split("\f"):
        nonblank = [l.strip() for l in pg.splitlines() if l.strip()]
        for ln in set(nonblank[:3] + nonblank[-3:]):
            firsts[ln] = firsts.get(ln, 0) + 1
    running = {k for k, v in firsts.items() if v >= 3 and not HEADING.match(k)}
    lines = [l for l in text.replace("\f", "\n").splitlines()
             if l.strip() not in running and not re.fullmatch(r"(\s{15,})?\d+\s*", l)
             and not re.search(r"\b\d+ of \d+\s*$", l)]
    entries, block, cur, active, numbered, expect, restart_ok = [], [], None, False, False, 1, False

    def close():
        nonlocal block, cur
        if cur:
            entries.append(cur)
        entries.extend(_split_block(block))
        block, cur = [], None

    for line in lines:
        if HEADING.match(line):
            if active and numbered:  # a running "References" header, or a new list restarting at 1
                restart_ok = True
                continue
            close()
            active, numbered, expect = True, False, 1
            continue
        if not active:
            continue
        m = ENTRY.match(line)
        if m and restart_ok and int(m.group(1)) == 1:
            expect = 1
        if line.strip():
            restart_ok = False
        is_entry = bool(m) and int(m.group(1)) == expect and not block
        if STOP.match(line.strip()) or (not is_entry and not numbered and not block and
                                        re.match(r"^\d+(\.\d+)*\.?\s+[A-Z][a-z]", line.strip())):
            close()
            active = False
            continue
        if is_entry:
            if cur:
                entries.append(cur)
            numbered, expect, cur = True, expect + 1, m.group(2).strip()
        elif numbered:
            if line.strip() and re.match(r"^\s{3,}\S", line):
                cur += " " + line.strip()
        elif line.strip():
            block.append(line)
        else:
            close()
    close()
    refs = [e for e in entries if YEAR.search(e)]
    return [re.sub(r"(\d)- (\d)", r"\1-\2", re.sub(r"([a-z])- ([a-z])", r"\1\2", r)) for r in refs]


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", s)


def citmatch(ref: str) -> list:
    q = urllib.parse.urlencode({"method": "heuristic", "raw-text": ref[:500]})
    def _q():
        with urllib.request.urlopen(urllib.request.Request(f"{CITMATCH}?{q}", headers=UA), timeout=60) as r:
            return json.load(r)
    res = ncbi.with_retries(_q)
    time.sleep(0.4)
    return [int(u["pubmed"]) for u in (res.get("result") or {}).get("uids", []) if "pubmed" in u]


def agrees(ref: str, meta: dict) -> bool:
    surname = norm((meta.get("first_author") or "").split(" ")[0])
    years = {int(y) for y in re.findall(r"\b(?:19|20)\d{2}\b", ref)}
    y = re.match(r"\d{4}", meta.get("pubdate") or "")
    return bool(surname) and surname in norm(ref[:80]) and bool(y) and any(abs(int(y.group()) - v) <= 1 for v in years)


def main() -> None:
    sleep_s = ncbi.configure_entrez()
    order = list(range(1, NG_MAX + 1))
    random.Random(SEED).shuffle(order)
    sample, rows = [], []
    for n in order:
        if sum(s["status"] == "included" for s in sample) == N_TARGET:
            break
        meta = guideline_meta(n)
        if meta is None:
            sample.append({"ng": n, "status": "skipped: page missing or redirected"}); continue
        title, year = meta
        if year not in YEARS:
            sample.append({"ng": n, "title": title, "year": year, "status": "skipped: first published outside 2015-2020"}); continue
        links = evidence_pdfs(n)
        seen, n_docs_parsed = set(), 0
        for link in links:
            refs = parse_references(pdf_text(n, link))
            n_docs_parsed += bool(refs)
            for r in refs:
                k = norm(r)[:120]
                if k and k not in seen:
                    seen.add(k)
                    rows.append({"ng": n, "document": link.rsplit("/", 1)[1], "reference": r,
                                 "journal_like": bool(JOURNAL_LIKE.search(r))})
        status = ("included" if seen else "skipped: no parsable reference list" if links
                  else "skipped: no evidence documents online")
        sample.append({"ng": n, "title": title, "year": year, "n_documents": len(links),
                       "n_documents_parsed": n_docs_parsed, "n_references": len(seen), "status": status})
        print(f"NG{n} ({year}): {len(links)} documents, {n_docs_parsed} parsed, {len(seen)} references -> {status}")
    included = {s["ng"] for s in sample if s["status"] == "included"}
    refs = pd.DataFrame([r for r in rows if r["ng"] in included])

    print(f"Matching {len(refs)} references…")
    cands = []
    for i, r in enumerate(refs["reference"]):
        cands.append(citmatch(r))
        if i % 250 == 0:
            print(f"  {i}/{len(refs)}")
    refs["candidates"] = [len(c) for c in cands]
    single = [c[0] if len(c) == 1 else None for c in cands]
    meta = ncbi.fetch_summaries([p for p in single if p], sleep_s=sleep_s)
    refs["pmid"] = [p if p and agrees(r, meta.get(p, {})) else None for p, r in zip(single, refs["reference"])]
    refs["pmid_unverified"] = [p if p and not agrees(r, meta.get(p, {})) else None for p, r in zip(single, refs["reference"])]
    refs["matched"] = refs["pmid"].notna()

    summ = []
    for label, d in [("all references", refs), ("journal-like references (gate)", refs[refs["journal_like"]])]:
        k, n = int(d["matched"].sum()), len(d)
        lo, hi = gates.wilson_ci(k, n)
        summ.append({"set": label, "n": n, "matched": k, "rate": k / n if n else float("nan"), "ci_low": lo, "ci_high": hi})
    by_g = refs.groupby("ng").agg(n=("matched", "size"), matched=("matched", "sum"),
                                  journal_like=("journal_like", "sum")).reset_index()
    by_g["matched_journal_like"] = refs[refs["journal_like"]].groupby("ng")["matched"].sum().reindex(by_g["ng"]).fillna(0).astype(int).values

    pd.DataFrame(sample).to_csv(OUT_SAMPLE, index=False)
    refs.to_csv(OUT_REFS, index=False)
    pd.DataFrame(summ).to_csv(OUT_SUMMARY, index=False)
    print(pd.DataFrame(sample).to_string(index=False))
    print(by_g.to_string(index=False))
    print(pd.DataFrame(summ).to_string(index=False))
    print(f"Single candidate but author/year disagree (not counted): {refs['pmid_unverified'].notna().sum()}; "
          f"multiple candidates: {(refs['candidates'] > 1).sum()}; none: {(refs['candidates'] == 0).sum()}")


if __name__ == "__main__":
    main()
