#!/usr/bin/env python3
"""Publication figures from the processed results (no analysis is run here).

Numbering follows the submitted manuscript (manuscript/submission/manuscript.md, "Figure legends"):

Fig 1  Study flow diagram (single column, 85 mm).
Fig 2  Growth of guideline-cited papers (P1, 5-year) against the research literature (D), indexed to 2008, log scale.
Fig 3  Five-year probability of first guideline citation by cohort (P2), all frames on one log axis, labelled "1 in N".
Fig 4  (a) Waterfall/decomposition of P1 growth with combined capacity marker; (b) Literature D vs established journals.
Fig 5  Robustness: beta (H1) and g1 - gD (H2) across specifications, grouped primary / sensitivity / exploratory.
Fig S1 Guideline records per year in F1 and F2 (the 2022-23 F1 indexing dip).
Fig S2 Selected designs: 3-year cumulative-incidence ratio to other research by cohort.
Fig S3 G4: share of citations that are evidence for a recommendation.

All text is >= 7 pt; figure widths strictly match 85 mm (single column) or 175 mm (double column).
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402
import matplotlib.ticker as mticker  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
OUT = ROOT / "figures" / "main"

INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#ffffff"
COL = {"F1": "#2a78d6", "F2": "#eb6834", "F2_clean": "#eb6834", "D": "#8a8984", "D_j": "#3b3a37"}
LS = {"F1": "-", "F2": "-", "F2_clean": "--", "D": "-", "D_j": "-."}
MARK = {"F1": "o", "F2": "s", "F2_clean": "^", "D": "D", "D_j": "v"}
LAB = {
    "F1": "PubMed-indexed guidelines (F1)",
    "F2": "Named-body guidelines (F2)",
    "F2_clean": "Named-body, cleaned",
    "D": "Research literature (D)",
    "D_j": "Established journals (D-journals)",
}
SHORT = {
    "F1": "PubMed-indexed",
    "F2": "Named bodies",
    "F2_clean": "Named bodies,\ncleaned",
    "D": "Literature (D)",
    "D_j": "Established\njournals",
}
FRAMES = ["F1", "F2", "F2_clean"]
COVID = 2020

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 8,
    "axes.edgecolor": GRID,
    "axes.labelcolor": INK2,
    "xtick.color": INK2,
    "ytick.color": INK2,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "axes.labelsize": 8,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.6,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "legend.frameon": False,
    "figure.facecolor": SURF,
    "axes.facecolor": SURF,
    "axes.titlesize": 9,
    "axes.titleweight": "bold",
    "axes.titlecolor": INK,
    "axes.titlelocation": "left",
    "axes.axisbelow": True,
    "lines.linewidth": 1.3,
    "lines.markersize": 3.6,
    "savefig.dpi": 300,
})
MM = 1 / 25.4
DOUBLE = 175 * MM  # 6.89 in (double-column width)
SINGLE = 85 * MM   # 3.35 in (single-column width)


SUBMISSION_NAMES = {"fig1_study_flow": "Fig1", "fig2_growth_index": "Fig2", "fig3_cumulative_incidence": "Fig3",
                    "fig4_decomposition": "Fig4", "fig5_robustness": "Fig5"}
SUBMISSION_DIR = ROOT / "manuscript" / "submission" / "figures"


def _fit_width(fig, target_mm):
    """Shrink the figure until its tight bounding box is no wider than target_mm (Springer: 84 or 174 mm)."""
    for _ in range(4):
        bb = fig.get_tightbbox(fig.canvas.get_renderer())
        width_mm = (bb.width + 2 * 0.02) * 25.4
        if width_mm <= target_mm:
            return
        w, h = fig.get_size_inches()
        fig.set_size_inches(w * (target_mm - 0.5) / width_mm, h)


def save(fig, name):
    from io import BytesIO
    from PIL import Image
    OUT.mkdir(parents=True, exist_ok=True)
    fig.canvas.draw()
    natural_mm = fig.get_tightbbox(fig.canvas.get_renderer()).width * 25.4
    _fit_width(fig, 84 if natural_mm < 120 else 174)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"{name}.{ext}", bbox_inches="tight", pad_inches=0.02, facecolor=SURF)
    if name in SUBMISSION_NAMES:  # Springer: RGB TIFF, 600 dpi for combination art, files named Fig<n>
        SUBMISSION_DIR.mkdir(parents=True, exist_ok=True)
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=600, bbox_inches="tight", pad_inches=0.02, facecolor=SURF)
        Image.open(buf).convert("RGB").save(SUBMISSION_DIR / f"{SUBMISSION_NAMES[name]}.tif", dpi=(600, 600), compression="tiff_lzw")
    plt.close(fig)


def end_label(ax, x, y, text, dy=0):
    ax.annotate(text, (x, y), xytext=(4, dy), textcoords="offset points",
                va="center", fontsize=8, color=INK2, clip_on=False)


def cohorts(frame):
    return pd.read_csv(PROC / "primary" / f"dp_weighted_D_{frame}_cohorts.csv", index_col="cohort")


def plot_series(ax, s, key, lw=None, lo=None, hi=None):
    """Line with optional 95% CI ribbon and an open marker for the 2020 COVID cohort."""
    if lo is not None and hi is not None:
        ax.fill_between(s.index, lo.values, hi.values, color=COL[key],
                        alpha=0.12 if key != "F2_clean" else 0.07, lw=0)
    ax.plot(s.index, s.values, color=COL[key], ls=LS[key], lw=lw or plt.rcParams["lines.linewidth"],
            marker=MARK[key], markevery=[i for i, y in enumerate(s.index) if y != COVID], label=LAB[key])
    if COVID in s.index:
        ax.plot([COVID], [s.loc[COVID]], marker=MARK[key], mfc=SURF, mec=COL[key], ls="none")


def covid_band(ax, top_frac=0.03):
    ax.axvspan(COVID - 0.5, COVID + 0.5, color=GRID, alpha=0.5, lw=0)
    ax.text(COVID, top_frac, "COVID", transform=ax.get_xaxis_transform(),
            ha="center", va="bottom" if top_frac < 0.5 else "top", fontsize=8, color=INK2)



def log_axis(ax, ticks):
    ax.set_yscale("log")
    ax.yaxis.set_major_locator(mticker.FixedLocator(ticks))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:g}"))
    ax.yaxis.set_minor_locator(mticker.NullLocator())


def fig1_flow():
    """Single-column (85 mm) study flow diagram."""
    fig, ax = plt.subplots(figsize=(SINGLE, 3.1))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    def draw_box(x, y, w, h, title, body, edge=INK2):
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=1.2,rounding_size=2",
                             fc=SURF, ec=edge, lw=0.9)
        ax.add_patch(box)
        ax.text(x + w / 2, y + h - 4.5, title, ha="center", va="top",
                fontsize=8, fontweight="bold", color=INK)
        ax.text(x + w / 2, y + (h - 7) / 2, body, ha="center", va="center",
                fontsize=8, color=INK2, linespacing=1.25)

    draw_box(2, 70, 45, 27, "PubMed-indexed (F1)",
             "23,920 records\n2008–2025\n19,483 with references", edge=COL["F1"])
    draw_box(53, 70, 45, 27, "Named bodies (F2)",
             "7,943 records\n31 bodies\n7,007 with references", edge=COL["F2"])
    draw_box(8, 39, 84, 20, "Linkage through NIH iCite",
             "1,010,117 unique cited papers,\neach assigned its earliest publication year")
    draw_box(8, 3, 84, 25, "Research literature (D)",
             "18.0 million articles, 2008–2024\nP1: papers cited within 5 years (2008–2020)\nP2: cumulative incidence (2008–2024)")

    arrow_kw = dict(arrowstyle="-|>", color=INK2, lw=0.9, mutation_scale=8)
    ax.annotate("", xy=(35, 59), xytext=(24.5, 70), arrowprops=arrow_kw)
    ax.annotate("", xy=(65, 59), xytext=(75.5, 70), arrowprops=arrow_kw)
    ax.annotate("", xy=(50, 28), xytext=(50, 39), arrowprops=arrow_kw)

    fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
    save(fig, "fig1_study_flow")


def fig2_growth():
    fig, ax = plt.subplots(figsize=(SINGLE, 2.5))
    yrs = range(2008, 2021)
    d = cohorts("F1")["D"].loc[yrs]
    covid_band(ax)

    s_d = d / d.iloc[0]
    plot_series(ax, s_d, "D", lw=1.8)
    end_label(ax, s_d.index[-1], s_d.values[-1], SHORT["D"], dy=0)

    for f in FRAMES:
        df_c = cohorts(f).loc[yrs]
        p = df_c["P1_5y"]
        s = p / p.iloc[0]
        lo = df_c["P1_5y_index_ci_low"] if "P1_5y_index_ci_low" in df_c else None
        hi = df_c["P1_5y_index_ci_high"] if "P1_5y_index_ci_high" in df_c else None
        plot_series(ax, s, f, lo=lo, hi=hi)
        end_label(ax, s.index[-1], s.values[-1], SHORT[f],
                  dy={"F1": 0, "F2": -7, "F2_clean": 7}.get(f, 0))

    log_axis(ax, [0.8, 0.9, 1, 1.25, 1.5, 2])
    ax.set_xlim(2007.5, 2020.8)
    ax.set_xticks(range(2008, 2021, 3))
    ax.set_ylabel("Indexed to 2008 cohort (log scale)")
    ax.set_xlabel("Publication cohort")
    fig.subplots_adjust(left=0.16, right=0.73, top=0.96, bottom=0.17)
    save(fig, "fig2_growth_index")


def fig3_incidence():
    fig, ax = plt.subplots(figsize=(SINGLE, 2.6))
    covid_band(ax, top_frac=0.98)
    label_years = (2008, 2019)
    for f in FRAMES:
        df_c = cohorts(f).dropna(subset=["cum_inc_5y"])
        c = 100 * df_c["cum_inc_5y"]
        lo = 100 * df_c["cum_inc_5y_ci_low"] if "cum_inc_5y_ci_low" in df_c else None
        hi = 100 * df_c["cum_inc_5y_ci_high"] if "cum_inc_5y_ci_high" in df_c else None
        plot_series(ax, c, f, lo=lo, hi=hi)
        end_label(ax, c.index[-1], c.values[-1], SHORT[f],
                  dy={"F1": 0, "F2": 7, "F2_clean": -7}.get(f, 0))
        if f == "F2_clean":
            continue
        for y in label_years:
            v = c.loc[y]
            ax.annotate(f"1 in {round(100 / v)}", (y, v), xytext=(0, 6) if y == 2008 else (-14, 16),
                        textcoords="offset points", ha="center" if y == 2008 else "right", va="bottom" if y == 2008 else "center",
                        fontsize=8, fontweight="bold", color=COL[f],
                        arrowprops=None if y == 2008 else dict(arrowstyle="-", lw=0.6, color=COL[f], shrinkA=1, shrinkB=3))
    log_axis(ax, [0.5, 1, 2, 4])
    ax.set_ylim(0.5, 5.5)
    ax.set_xlim(2007.5, 2020.8)
    ax.set_xticks(range(2008, 2021, 3))
    ax.set_ylabel("Cited by a guideline\nwithin 5 years (%, log scale)")
    ax.set_xlabel("Publication cohort")
    fig.subplots_adjust(left=0.16, right=0.73, top=0.96, bottom=0.17)
    save(fig, "fig3_cumulative_incidence")


def fig4_decomposition():
    """Double-column (175 mm) 2-panel figure: (a) waterfall/capacity decomposition; (b) D vs D-journals."""
    s = json.loads((PROC / "secondary" / "summary.json").read_text())
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(DOUBLE, 2.8), gridspec_kw={"width_ratios": [1.35, 1.0]})

    # Panel (a): Decomposition with combined Capacity subtotal marker
    factors = [
        ("guidelines", "Guidelines"),
        ("refs_per_guideline", "Refs per guideline"),
        ("capacity", "Guideline capacity\n(guidelines x refs)"),
        ("share_to_cohort", "Share to cohort"),
        ("uniqueness", "First citations / ref"),
        ("P1", "P1 total"),
    ]
    y = np.arange(len(factors))
    h = 0.25
    for i, f in enumerate(FRAMES):
        g = dict(s[f]["SA2_growth_pct_per_year"])
        g["capacity"] = g["guidelines"] + g["refs_per_guideline"]
        vals = [g[k] for k, _ in factors]
        ypos = y + (i - 1) * h
        ax1.barh(ypos, vals, height=h - 0.03, color=COL[f],
                 alpha=0.5 if f == "F2_clean" else 0.9,
                 hatch="///" if f == "F2_clean" else None, edgecolor=SURF, label=LAB[f])
        if "SA2_ci_low" in s[f] and "SA2_ci_high" in s[f]:
            lo = [s[f]["SA2_ci_low"].get(k, np.nan) for k, _ in factors]
            hi = [s[f]["SA2_ci_high"].get(k, np.nan) for k, _ in factors]
            ax1.errorbar(vals, ypos, xerr=[np.subtract(vals, lo), np.subtract(hi, vals)],
                         fmt="none", ecolor=INK, elinewidth=0.8, capsize=1.5)

    for sep_y in (1.5, 2.5, 4.5):
        ax1.axhline(sep_y, color=GRID, lw=0.8, ls=":")
    dg = s["F1"]["SA2_growth_pct_per_year"]["D"]
    ax1.axvline(dg, color=COL["D"], lw=1.3, ls="--")
    ax1.text(dg - 0.1, 3.6, f"Literature (D)\n+{dg:.1f}%/yr", color=INK2, fontsize=8, va="center", ha="right")
    ax1.axvline(0, color=INK2, lw=0.8)
    ax1.set_xlim(-2.2, dg + 1.0)
    ax1.set_yticks(y, [lab for _, lab in factors])
    ax1.invert_yaxis()
    ax1.set_title("a", fontsize=9, fontweight="bold")
    ax1.set_xlabel("Annual growth, 2008-2020 (%/yr)")
    ax1.grid(axis="y", visible=False)

    # Panel (b): Full literature (D) vs established journals (D-journals)
    yrs = range(2008, 2021)
    d_all = cohorts("F1")["D"].loc[yrs]
    s_all = d_all / d_all.iloc[0]
    plot_series(ax2, s_all, "D", lw=1.6)
    end_label(ax2, s_all.index[-1], s_all.values[-1], "All research\narticles (D)")

    # Established journals: journals that published guideline-cited research in 2008-2012 (scripts/15_d_journals.py).
    # No fallback: the panel is drawn only from the real counts file.
    # De-duplicated exactly as in scripts/22_sensitivity.py::d_journals_denominator (counts minus adjacent-year overlaps).
    c = pd.read_csv(PROC / "d_journals_counts.csv").query("date_field == 'dp'").set_index("year")["count"].astype(float)
    o = pd.read_csv(PROC / "d_journals_overlaps.csv").set_index("later_year")["overlap"]
    dj = (c - o.reindex(c.index).fillna(0)).loc[yrs]
    s_dj = dj / dj.iloc[0]
    plot_series(ax2, s_dj, "D_j", lw=1.5)
    end_label(ax2, s_dj.index[-1], s_dj.values[-1], "Established\njournals")

    log_axis(ax2, [1, 1.2, 1.4, 1.6, 1.8, 2.0])
    ax2.set_xlim(2007.5, 2024.0)
    ax2.set_xticks(range(2008, 2021, 4))
    ax2.set_title("b", fontsize=9, fontweight="bold")
    ax2.set_ylabel("Indexed to 2008 (log scale)")
    ax2.set_xlabel("Publication cohort")

    h_leg, l_leg = ax1.get_legend_handles_labels()
    fig.subplots_adjust(left=0.22, right=0.98, top=0.88, bottom=0.24, wspace=0.34)
    fig.legend(h_leg, l_leg, loc="lower center", ncol=3, fontsize=8)
    save(fig, "fig4_decomposition")


def fig5_robustness():
    prim = {}
    for tag, lab in [
        ("dp_weighted_D", "Primary"),
        ("dp_unweighted_D", "Unweighted"),
        ("edat_weighted_D", "Entry date [edat]"),
        ("dp_weighted_D_humans", "Humans-only denominator"),
        ("dp_weighted_D_all", "All-records denominator"),
        ("dp_weighted_D_medline", "MEDLINE-only denominator"),
    ]:
        f = PROC / "primary" / f"{tag}_summary.csv"
        if f.exists():  # the MEDLINE-only run is post hoc and optional
            prim[lab] = pd.read_csv(f).set_index("frame")
    sens = pd.read_csv(PROC / "sensitivity" / "sensitivity_summary.csv")
    names = {
        "age3": "Headline age 3 years",
        "no_covid": "Excluding 2020-21 cohorts",
        "d_journals": "Established journals",
        "stable_journals": "Stable-coverage journals",
        "censor_2021": "Censored at 2021",
    }
    rows = []
    for lab, t in prim.items():
        for f in FRAMES:
            r = t.loc[f]
            rows.append((lab, f, r.beta, r.beta_ci_low, r.beta_ci_high,
                         100 * r.diff_g1_gD, 100 * r.diff_ci_low, 100 * r.diff_ci_high))
    for _, r in sens.iterrows():
        b = (np.nan,) * 3 if r.spec == "age3" else (r.beta, r.beta_ci_low, r.beta_ci_high)
        rows.append((names[r.spec], r.frame, *b, 100 * r["diff"], 100 * r.diff_ci_low, 100 * r.diff_ci_high))
    df = pd.DataFrame(rows, columns=["spec", "frame", "b", "bl", "bh", "d", "dl", "dh"])
    groups = [
        ("Primary", ["Primary"]),
        ("Pre-specified sensitivity", [
            "Unweighted", "Entry date [edat]", "Humans-only denominator",
            "All-records denominator", "Headline age 3 years", "Excluding 2020-21 cohorts",
            "Established journals", "Stable-coverage journals",
        ]),
        ("Exploratory and post hoc", ["Censored at 2021"] + (["MEDLINE-only denominator"] if "MEDLINE-only denominator" in prim else [])),
    ]
    ypos, labels, heads, yy = {}, [], [], 0
    for head, specs in groups:
        heads.append((yy, head))
        yy += 1
        for sp in specs:
            ypos[sp] = yy
            labels.append((yy, sp))
            yy += 1
        yy += 0.4
    fig, axes = plt.subplots(1, 2, figsize=(DOUBLE, 4.3), sharey=True)
    off = {"F1": -0.22, "F2": 0, "F2_clean": 0.22}
    panels = [
        ("b", "bl", "bh", "a", "β, log-odds per cohort year"),
        ("d", "dl", "dh", "b", "Growth gap, percentage points per year"),
    ]
    for ax, (v, lo, hi, title, xl) in zip(axes, panels):
        for f in FRAMES:
            sub = df[df["frame"] == f].dropna(subset=[v])
            y = sub["spec"].map(ypos) + off[f]
            ax.errorbar(sub[v], y, xerr=[sub[v] - sub[lo], sub[hi] - sub[v]],
                        fmt=MARK[f], color=COL[f], mfc=SURF if f == "F2_clean" else COL[f],
                        ms=3.8, lw=1.0, capsize=0, label=LAB[f])
        ax.axvline(0, color=INK2, lw=0.8)
        ax.set_title(title, fontsize=9, fontweight="bold")
        ax.set_xlabel(xl)
        ax.grid(axis="y", visible=False)
    axes[0].set_yticks([p for p, _ in labels], [s for _, s in labels])
    for p, head in heads:
        axes[0].text(-0.02, p, head, transform=axes[0].get_yaxis_transform(),
                     ha="right", va="center", fontsize=8, fontweight="bold", color=INK)
    axes[0].set_ylim(yy, -0.8)
    h, l = axes[0].get_legend_handles_labels()
    fig.subplots_adjust(left=0.28, right=0.98, top=0.92, bottom=0.17, wspace=0.15)
    fig.legend(h, l, loc="lower center", ncol=3, fontsize=8, bbox_to_anchor=(0.5, -0.01))
    save(fig, "fig5_robustness")


def figS1_counts():
    y = pd.read_csv(PROC / "sensitivity" / "f1_f2_guidelines_by_year.csv").pivot(
        index="year", columns="frame", values="guidelines"
    )
    fig, ax = plt.subplots(figsize=(SINGLE, 2.4))
    for f in ["F1", "F2"]:
        ax.plot(y.index, y[f], color=COL[f], marker=MARK[f], label=LAB[f])
        end_label(ax, y.index[-1], y[f].iloc[-1], SHORT[f])
    ax.axvspan(2021.5, 2023.5, color=GRID, alpha=0.6, lw=0)
    ax.text(2022.5, 0.04, "Tagging\ngap", transform=ax.get_xaxis_transform(),
            ha="center", va="bottom", fontsize=8, color=INK2)
    ax.set_ylim(0, None)
    ax.set_xlim(2007.5, 2025.8)
    ax.set_xticks(range(2008, 2026, 4))
    ax.set_ylabel("Guideline records per year")
    ax.set_xlabel("Publication year [dp]")
    fig.subplots_adjust(left=0.18, right=0.74, top=0.95, bottom=0.18)
    save(fig, "figS1_guideline_counts")


def figS2_selected_ratio():
    fig, ax = plt.subplots(figsize=(SINGLE, 2.5))
    for f in FRAMES:
        df_r = pd.read_csv(PROC / "secondary" / f"{f}_selected_ratios.csv", index_col=0).dropna(subset=["ratio_3y"])
        r = df_r["ratio_3y"]
        if "ratio_3y_ci_low" in df_r and "ratio_3y_ci_high" in df_r:
            ax.fill_between(r.index, df_r["ratio_3y_ci_low"], df_r["ratio_3y_ci_high"],
                            color=COL[f], alpha=0.12 if f != "F2_clean" else 0.06, lw=0)
        # De-emphasise noisy early cohorts (2008-2011) with open/smaller markers
        early = r.index < 2012
        ax.plot(r.index, r.values, color=COL[f], ls=LS[f], lw=1.2, label=LAB[f])
        ax.plot(r.index[early], r.values[early], marker=MARK[f], color=COL[f],
                mfc=SURF, ms=2.8, ls="none", alpha=0.7)
        ax.plot(r.index[~early], r.values[~early], marker=MARK[f], color=COL[f],
                mfc=SURF if f == "F2_clean" else COL[f], ms=3.6, ls="none")
        end_label(ax, r.index[-1], r.values[-1], SHORT[f],
                  dy={"F1": -10, "F2": 14, "F2_clean": -1}.get(f, 0))
    ax.axhline(1, color=INK2, lw=0.8)
    log_axis(ax, [0.5, 1, 2, 4, 8])
    ax.set_xlim(2007.5, 2022.8)
    ax.set_xticks(range(2008, 2023, 3))
    ax.set_ylabel("3-year incidence ratio, selected\ndesigns / other research (log scale)")
    ax.set_xlabel("Publication cohort")
    fig.subplots_adjust(left=0.18, right=0.73, top=0.95, bottom=0.18)
    save(fig, "figS2_selected_ratio")


def figS3_g4():
    fig, ax = plt.subplots(figsize=(SINGLE, 2.2))
    g = pd.read_csv(PROC / "gate_g4_context.csv")
    ev = g[(g["context"] == "evidence") & g["group"].isin(["selected", "other"])].set_index("group").loc[["selected", "other"]]
    ys = [0, 1]
    ax.errorbar(100 * ev["share"], ys,
                xerr=[100 * (ev["share"] - ev["ci_low"]), 100 * (ev["ci_high"] - ev["share"])],
                fmt="o", color=INK, ms=4.5, lw=1.2, capsize=2)
    for yv, v in zip(ys, ev["share"]):
        ax.annotate(f"{100 * v:.0f}%", (100 * v, yv), xytext=(0, 6),
                    textcoords="offset points", ha="center", fontsize=8)
    ax.set_yticks(ys, ["Selected designs\n(n = 50)", "Other research\n(n = 50)"])
    ax.set_ylim(1.6, -0.6)
    ax.set_xlim(0, 80)
    ax.set_xlabel("Evidence for a recommendation (%, 95% CI)")
    ax.grid(axis="y", visible=False)
    fig.subplots_adjust(left=0.28, right=0.96, top=0.86, bottom=0.22)
    save(fig, "figS3_g4_context")


if __name__ == "__main__":
    for fn in (fig1_flow, fig2_growth, fig3_incidence, fig4_decomposition, fig5_robustness, figS1_counts, figS2_selected_ratio, figS3_g4):
        fn()
    print("written:", sorted(p.name for p in OUT.glob("*.png")))
