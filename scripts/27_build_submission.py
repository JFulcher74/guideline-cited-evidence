#!/usr/bin/env python3
"""Build the Scientometrics submission package from the working draft.

Follows the journal's author guidelines (Springer, checked November 2026): title page with author information,
author contributions and acknowledgments; unstructured abstract of 150-250 words and 4-6 keywords; at most three
heading levels; figures placed in the body after their first citation, captions beginning "Fig. n" with no
final punctuation; "Statements and Declarations" before an APA 7 reference list; supplementary material as
PDF "Online Resource" files that carry the article title, journal, author and corresponding e-mail; Word
manuscript in Times New Roman 10 pt with automatic page numbers; figure files named Fig<n> (TIFF, 600 dpi,
written by scripts/23_figures.py).

Working material is removed: draft banner, key message, title options, author notes in "> `[...]`" blockquotes
and "*(...)*" heading annotations. The working draft stays the source of truth; rerun after every edit.

Usage: python scripts/27_build_submission.py
Writes manuscript/submission/{manuscript.md, manuscript.docx, supplement.md, ESM_1.pdf, ESM_2.pdf}.
Needs pypandoc_binary, python-docx and weasyprint (submission-only dependencies, not in requirements.txt).
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "manuscript" / "draft_manuscript.md"
SUPP = ROOT / "manuscript" / "supplement.md"
OUT = ROOT / "manuscript" / "submission"
FIGS = {1: "fig1_study_flow", 2: "fig2_growth_index", 3: "fig3_cumulative_incidence", 4: "fig4_decomposition",
        5: "fig5_robustness"}
TITLE = "Guideline citation and the growth of PubMed: a pre-registered cohort study, 2008–2024"
CITY = "Norwich"  # Springer records only city and country for unaffiliated authors
AUTHOR_LINE = f"Jordan Fulcher, independent researcher, {CITY}, United Kingdom"
EMAIL = "jfulcherresearch@gmail.com"
ORCID = "https://orcid.org/0009-0001-6294-1127"


def section(text: str, start: str, end: str) -> str:
    i = text.index(start)
    j = text.index(end, i + len(start))
    return text[i:j]


def words(md: str) -> int:
    md = re.sub(r"^#.*$", "", md, flags=re.M)
    md = re.sub(r"^\|.*$", "", md, flags=re.M)  # tables are not counted
    md = re.sub(r"^!\[.*$", "", md, flags=re.M)
    md = re.sub(r"^\*\*Fig\. \d\*\*.*$", "", md, flags=re.M)  # captions are not counted
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
        if run:
            out.append(" ".join(run))
            run = []
        out.append(line)
    if run:
        out.append(" ".join(run))
    return "\n".join(out)


def clean(md: str) -> str:
    md = re.sub(r"^> `\[.*?\]`\n?", "", md, flags=re.M)                     # author notes
    md = re.sub(r"(^#+ [^\n*]*?) \*\([^)]*\)\*", r"\1", md, flags=re.M)      # heading annotations
    md = re.sub(r"^\*APA 7 style.*\*$\n?", "", md, flags=re.M)               # reference-list working note
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip() + "\n"


def place_figures(body: str, captions: dict, img_prefix: str) -> str:
    """Insert each figure after the paragraph that first cites it (Springer: figures within the body)."""
    paras = body.split("\n\n")
    for n in sorted(captions):
        for k, para in enumerate(paras):
            if para.startswith("![") or para.startswith("**Fig."):  # skip figures already placed and their captions
                continue
            if re.search(rf"\bFigs?\. (?:\d and )?{n}\b", para):
                paras.insert(k + 1, f"![]({img_prefix}{FIGS[n]}.png)\n\n{captions[n]}")
                break
        else:
            raise SystemExit(f"Fig. {n} is never cited in the text")
    return "\n\n".join(paras)


def to_docx(md: str, path: Path) -> None:
    import pypandoc
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Pt
    pypandoc.convert_text(md, "docx", format="markdown+pipe_tables", outputfile=str(path))
    doc = Document(str(path))
    for style in doc.styles:
        if style.type != 1:  # paragraph styles only
            continue
        rpr = style.element.get_or_add_rPr()
        fonts = rpr.find(qn("w:rFonts"))
        if fonts is None:
            fonts = OxmlElement("w:rFonts")
            rpr.append(fonts)
        for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
            fonts.set(qn(attr), "Times New Roman")
        for a in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
            fonts.attrib.pop(qn(a), None)
        if style.name in ("Normal", "Body Text", "First Paragraph", "Compact", "Image Caption", "Table", "Abstract"):
            style.font.size = Pt(10)
    footer = doc.sections[0].footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer.add_run()  # automatic page number, as the guidelines ask
    for tag, text in (("begin", None), (None, "PAGE"), ("end", None)):
        if tag:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), tag)
        else:
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = text
        run._r.append(el)
    doc.save(str(path))


PDF_CSS = """@page { size: A4; margin: 20mm; @bottom-center { content: counter(page); font-size: 9pt; } }
body { font-family: "Times New Roman", Times, serif; font-size: 10pt; line-height: 1.35; }
h1 { font-size: 14pt; } h2 { font-size: 12pt; margin-top: 1.2em; } h3 { font-size: 10.5pt; }
table { border-collapse: collapse; font-size: 8.5pt; margin: 0.6em 0; } th, td { border: 0.5pt solid #999; padding: 2pt 4pt; }
img { max-width: 100%; } code { font-size: 8pt; word-break: break-all; }
header#title-block-header { display: none; }"""


def to_pdf(md: str, path: Path, base: Path) -> None:
    import pypandoc
    import weasyprint
    html = pypandoc.convert_text(md, "html5", format="markdown+pipe_tables",
                                 extra_args=["--standalone", "--metadata", "pagetitle=Online Resource"])
    weasyprint.HTML(string=html, base_url=str(base) + "/").write_pdf(str(path), stylesheets=[weasyprint.CSS(string=PDF_CSS)])


def main() -> None:
    d = SRC.read_text()
    abstract = section(d, "## Abstract", "\n---\n")
    abstract = re.sub(r"^## Abstract.*$", "## Abstract", abstract, flags=re.M)
    body = section(d, "## 1. Introduction", "## Statements and Declarations")
    body = re.sub(r"\n---\n", "\n", body)
    decl = section(d, "## Statements and Declarations", "## References")
    contrib = re.search(r"\*\*Author contributions\.\*\* (.*)", decl).group(1).strip()
    refs = section(d, "## References", "## Figure legends")
    caps = {int(m.group(1)): m.group(0).strip()
            for m in re.finditer(r"^\*\*Fig\. (\d)\*\*.*$", d[d.index("## Figure legends"):], re.M)}
    body = clean(bullets_to_prose(body))
    abstract_words = words(re.sub(r"^\*\*Keywords:.*$", "", abstract, flags=re.M))
    main_words = words(body)
    body = place_figures(body, caps, "../../figures/main/")
    title_page = (f"# {TITLE}\n\n"
                  f"**Jordan Fulcher**\n\nIndependent researcher, {CITY}, United Kingdom\n\n"
                  f"ORCID: {ORCID}\n\n**Corresponding author:** Jordan Fulcher, {EMAIL}\n\n"
                  f"**Author contributions:** {contrib}\n\n**Acknowledgments:** none.\n\n"
                  f"**Word count:** abstract {abstract_words}; main text {main_words} (Introduction to Conclusions, "
                  "excluding tables and figure captions).\n\n"
                  "**Registration:** Open Science Framework, https://doi.org/10.17605/OSF.IO/VN9BQ (16 October 2026).\n")
    out = "\n".join(clean(x) for x in (title_page, abstract, body, decl, refs))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "manuscript.md").write_text(out)
    to_docx(out.replace("../../figures/main/", str(ROOT / "figures" / "main") + "/"), OUT / "manuscript.docx")

    supp = SUPP.read_text()
    (OUT / "supplement.md").write_text(supp.replace("](../figures/", "](../../figures/"))
    to_pdf(supp, OUT / "ESM_1.pdf", SUPP.parent)
    record = (OUT / "RECORD_checklist.md").read_text()
    header = (f"# Online Resource 2: Reporting checklist adapted from RECORD\n\n**Article:** {TITLE}\n\n"
              f"**Journal:** *Scientometrics*\n\n**Author:** {AUTHOR_LINE}. Corresponding author: {EMAIL}\n\n")
    to_pdf(header + record.split("\n", 1)[1], OUT / "ESM_2.pdf", OUT)

    open_items = re.findall(r"\[(?:AUTHOR TO CONFIRM|MISSING|FIX|TODO|REF NEEDED|CITY)[^\]]*\]", out + supp)
    print(f"abstract {abstract_words} words; main text {main_words} words")
    print("open items:", *sorted(set(open_items)), sep="\n  ")


if __name__ == "__main__":
    main()
