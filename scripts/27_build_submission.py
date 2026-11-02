#!/usr/bin/env python3
"""Build a clean submission copy of the manuscript from the working draft.

Removes working material (draft banner, key-message section, title options, author notes in "> `[...]`"
blockquotes, section-heading annotations in "*(...)*") and adds a title page with word counts. Remaining
`[AUTHOR TO CONFIRM ...]` markers are kept on purpose: they need the author's decision and are listed at the
end of the run. The working draft stays the source of truth; rerun after every edit.

Usage: python scripts/27_build_submission.py
Writes manuscript/submission/manuscript.md and copies manuscript/supplement.md to manuscript/submission/.
"""
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "manuscript" / "draft_manuscript.md"
OUT = ROOT / "manuscript" / "submission"
TITLE = "Guideline citation and the growth of PubMed: a pre-registered cohort study, 2008–2024"
RUNNING = "Guideline citation and the growth of PubMed"


def section(text: str, start: str, end: str) -> str:
    i = text.index(start)
    j = text.index(end, i + len(start))
    return text[i:j]


def words(md: str) -> int:
    md = re.sub(r"^#.*$", "", md, flags=re.M)
    md = re.sub(r"^\|.*$", "", md, flags=re.M)  # tables are not counted
    md = re.sub(r"[*`>#]", " ", md)
    return len([w for w in md.split() if w not in {"-", "–", "—"}])


def bullets_to_prose(md: str) -> str:
    """Journals expect prose: join each run of list items (any depth) into one paragraph."""
    out, run = [], []
    for line in md.splitlines():
        m = re.match(r"^\s*[-*]\s+(.*)$", line)
        if m and not line.lstrip().startswith("|"):
            run.append(m.group(1).strip())
            continue
        if run and line.strip() == "" and out is not None:
            out.append(" ".join(run)); run = []
            out.append(line); continue
        if run:
            out.append(" ".join(run)); run = []
        out.append(line)
    if run:
        out.append(" ".join(run))
    return "\n".join(out)


def clean(md: str) -> str:
    md = re.sub(r"^> `\[.*?\]`\n?", "", md, flags=re.M)          # author notes
    md = re.sub(r"(^#+ [^\n*]*?) \*\([^)]*\)\*", r"\1", md, flags=re.M)  # heading annotations
    md = re.sub(r" \*\((?:add volume|No journal version)[^)]*\)\*", "", md)  # notes in reference entries
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip() + "\n"


def main() -> None:
    d = SRC.read_text()
    abstract = section(d, "## Abstract", "\n---\n")
    abstract = re.sub(r"^## Abstract.*$", "## Abstract", abstract, flags=re.M)
    body = section(d, "## 1. Introduction", "## Statements and declarations")
    body = re.sub(r"\n---\n", "\n", body)
    decl = section(d, "## Statements and declarations", "## References")
    contrib = section(d, "### Author contributions", "### Data availability").split("\n", 1)[1].strip()
    refs = section(d, "## References", "## Figure legends")
    legends = d[d.index("## Figure legends"):]
    abstract_words = words(re.sub(r"\*\*[A-Za-z]+\.\*\*|^\*\*Keywords:.*$", "", abstract, flags=re.M))
    body = bullets_to_prose(body)
    main_words = words(clean(body))
    title_page = (f"# {TITLE}\n\n**Running title:** {RUNNING}\n\n"
                  "**Author:** Jordan Fulcher, Independent researcher, United Kingdom. ORCID 0009-0001-6294-1127.\n\n"
                  "**Correspondence:** Jordan Fulcher, jfulcherresearch@gmail.com\n\n"
                  f"**Word count:** abstract {abstract_words}; main text {main_words} (Introduction to Conclusions, excluding tables).\n\n"
                  "**Registration:** OSF, doi:10.17605/OSF.IO/VN9BQ (16 October 2026).\n\n"
                  "**Reporting guideline:** checklist adapted from RECORD (supplementary file).\n\n"
                  f"**Author contributions:** {contrib}\n")
    out = "\n".join(clean(x) for x in (title_page, abstract, body, decl, refs, legends))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "manuscript.md").write_text(out)
    shutil.copy(ROOT / "manuscript" / "supplement.md", OUT / "supplement.md")
    open_items = re.findall(r"\[(?:AUTHOR TO CONFIRM|MISSING|FIX|TODO|REF NEEDED)[^\]]*\]", out)
    print(f"abstract {abstract_words} words; main text {main_words} words")
    print("open items:", *open_items, sep="\n  ")


if __name__ == "__main__":
    main()
