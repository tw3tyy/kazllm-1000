"""Vector figures sized for an IEEE two-column page (column width 3.5 in).

Fonts: STIX (bundled with matplotlib), so the figures render identically on any machine
and match the Times-style body text of the IEEE templates.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from paper.analysis import lib

COL = 3.5          # IEEE column width in inches
KK, EN, ACC, GREY = "#0072B2", "#E69F00", "#D55E00", "#8C8C8C"   # Okabe-Ito, colour-blind safe
META = {"Creator": "kazllm paper/analysis", "Producer": None, "CreationDate": None}

plt.rcParams.update({
    "font.family": "STIXGeneral", "mathtext.fontset": "stix", "font.size": 8, "axes.titlesize": 8,
    "axes.labelsize": 8, "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
    "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6, "lines.linewidth": 1.0,
    "savefig.bbox": "tight", "savefig.pad_inches": 0.02, "pdf.fonttype": 42,
})
NAMES = {"gemini-3.5-flash-lite": "Gemini 3.5 Flash-Lite", "qwen2.5-1.5b": "Qwen 2.5 1.5B", "gemma3": "Gemma 3",
         "nllb": "NLLB-200 600M", "dictionary": "Dictionary"}


def _save(fig, path):
    fig.savefig(path, metadata=META)
    plt.close(fig)


def _label(ax, letter):
    ax.text(-0.02, 1.04, f"({letter})", transform=ax.transAxes, fontsize=8, fontweight="bold", va="bottom", ha="right")


def fig_direction(main_tab, out):
    """Corpus chrF2 and BLEU per direction with 95% bootstrap intervals."""
    systems = list(main_tab)
    fig, axes = plt.subplots(1, 2, figsize=(COL, 1.75))
    for ax, metric, letter, ylab in ((axes[0], "chrf2", "a", "Corpus chrF2"), (axes[1], "bleu", "b", "Corpus BLEU")):
        x = np.arange(len(systems))
        w = 0.36
        for j, (d, col, lab) in enumerate((("en2kk", KK, "EN→KK"), ("kk2en", EN, "KK→EN"))):
            vals = np.array([main_tab[s][metric][d]["point"] for s in systems])
            lo = vals - np.array([main_tab[s][metric][d]["lo"] for s in systems])
            hi = np.array([main_tab[s][metric][d]["hi"] for s in systems]) - vals
            bars = ax.bar(x + (j - 0.5) * w, vals, w * 0.95, color=col, yerr=[lo, hi], capsize=1.8,
                          error_kw={"elinewidth": 0.6, "capthick": 0.6}, label=lab)
            for bx, v in zip(bars, vals):
                ax.text(bx.get_x() + bx.get_width() / 2, v + (hi.max() + 1.5), f"{v:.1f}", ha="center", fontsize=6)
        ax.set_xticks(x, [NAMES.get(s, s).replace(" ", "\n", 1) if len(NAMES.get(s, s)) > 10 else NAMES.get(s, s)
                          for s in systems])
        ax.set_ylabel(ylab)
        ax.set_ylim(0, 80 if metric == "chrf2" else 50)
        _label(ax, letter)
    axes[0].legend(frameon=False, loc="upper right", handlelength=1, borderaxespad=0)
    fig.tight_layout(w_pad=1.0)
    _save(fig, out / "fig_direction.pdf")


def fig_paired(rows, s, mostly_latin, out):
    """(a) Sentence chrF2 in both directions; (b) distribution of per-item differences."""
    a, b = s["en2kk"], s["kk2en"]
    lat = np.array([r["item_id"] in mostly_latin for r in rows])
    fig, axes = plt.subplots(1, 2, figsize=(COL, 1.75), gridspec_kw={"width_ratios": [1, 1.05]})
    ax = axes[0]
    ax.plot([0, 100], [0, 100], color=GREY, lw=0.6, ls="--", zorder=1)
    ax.scatter(b[~lat], a[~lat], s=5, color=KK, alpha=0.75, edgecolor="none", zorder=2, label="Cyrillic output")
    ax.scatter(b[lat], a[lat], s=14, marker="x", color=ACC, lw=0.8, zorder=3, label="Mostly Latin output")
    ax.set_xlim(0, 100), ax.set_ylim(0, 100)
    ax.set_xlabel("Sentence chrF2, KK→EN")
    ax.set_ylabel("Sentence chrF2, EN→KK")
    ax.set_aspect("equal")
    ax.legend(frameon=False, loc="upper left", handletextpad=0.2, borderaxespad=0, fontsize=6)
    _label(ax, "a")
    ax = axes[1]
    d = a - b
    ax.hist(d, bins=np.arange(-90, 51, 7.5), color=KK, alpha=0.85, edgecolor="white", lw=0.4)
    med = np.median(d)
    ax.axvline(0, color=GREY, lw=0.6, ls="--")
    ax.axvline(med, color=ACC, lw=1.0)
    ax.set_ylim(0, ax.get_ylim()[1] * 1.18)
    ax.text(med - 3, ax.get_ylim()[1] * 0.93, f"median {med:+.1f}", color=ACC, fontsize=6.5, ha="right")
    ax.set_xlabel("Per-item difference (EN→KK − KK→EN)")
    ax.set_ylabel("Items")
    _label(ax, "b")
    fig.tight_layout(w_pad=0.8)
    _save(fig, out / "fig_paired.pdf")


def fig_forest(R, out):
    """chrF2 gap with 95% CI for all pairs, sensitivity subsets and exploratory subgroups."""
    entries = [("All pairs", R["main"]["gemini-3.5-flash-lite"]["chrf2"]["gap"] | {"n": R["n_pairs"]}, "main"),
               ("Pilot items removed", R["subsets"]["no_pilot"], "sens"),
               ("Latin outputs removed", R["subsets"]["no_latin"], "sens")]
    for k, e in R["subsets"].items():
        if e and k.startswith("domain_"):
            entries.append((k.replace("domain_", "").capitalize(), e, "sub"))
    for k, lab in (("len_short", "Short sources"), ("len_medium", "Medium sources"), ("len_long", "Long sources")):
        if R["subsets"].get(k):
            entries.append((lab, R["subsets"][k], "sub"))
    fig, ax = plt.subplots(figsize=(COL, 2.15))
    y = np.arange(len(entries))[::-1]
    colours = {"main": KK, "sens": "#009E73", "sub": GREY}
    for yi, (lab, e, kind) in zip(y, entries):
        ax.plot([e["lo"], e["hi"]], [yi, yi], color=colours[kind], lw=1.2)
        ax.plot(e["point"], yi, "D" if kind == "main" else "o", color=colours[kind], ms=4 if kind == "main" else 3.2)
        ax.text(1.02, yi, f"{e['point']:+.2f}  (n={e['n']})", transform=ax.get_yaxis_transform(), va="center", fontsize=6.5)
    ax.axvline(0, color="black", lw=0.6)
    ax.axvline(entries[0][1]["point"], color=KK, lw=0.5, ls=":")
    ax.set_yticks(y, [e[0] for e in entries])
    ax.set_xlabel("chrF2 gap, EN→KK minus KK→EN (95% bootstrap CI)")
    ax.set_xlim(min(e[1]["lo"] for e in entries) - 1.5, 2)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    fig.tight_layout()
    _save(fig, out / "fig_forest.pdf")


def fig_inflection(R, out):
    """Near-miss rate (same k-letter prefix, different ending) by prefix length, with mismatched-reference control."""
    ks = sorted(int(k) for k in R["inflection"])
    fig, ax = plt.subplots(figsize=(COL, 1.85))
    for d, col, lab in (("en2kk", KK, "EN→KK (Kazakh output)"), ("kk2en", EN, "KK→EN (English output)")):
        rate = np.array([R["inflection"][str(k)][d]["rate"] for k in ks]) * 100
        lo = np.array([R["inflection"][str(k)][d]["lo"] for k in ks]) * 100
        hi = np.array([R["inflection"][str(k)][d]["hi"] for k in ks]) * 100
        ctrl = np.array([R["inflection"][str(k)][d]["control_rate"] for k in ks]) * 100
        ax.fill_between(ks, lo, hi, color=col, alpha=0.2, lw=0)
        ax.plot(ks, rate, "-o", color=col, ms=3, label=lab)
        ax.plot(ks, ctrl, ":", color=col, lw=0.9)
    ax.plot([], [], ":", color=GREY, label="Mismatched-reference control")
    ax.axvline(5, color=GREY, lw=0.5, ls="--")
    ax.set_xlabel("Prefix length $k$ (letters)")
    ax.set_ylabel("Reference words matched\nonly by prefix (%)")
    ax.set_xticks(ks)
    ax.set_ylim(bottom=0)
    ax.legend(frameon=False, loc="upper right", borderaxespad=0)
    fig.tight_layout()
    _save(fig, out / "fig_inflection.pdf")


def fig_tokens(R, rows, s, out):
    """(a) Output tokens per 100 characters; (b) item-level token ratio vs. sentence chrF2 gap."""
    T = R.get("tokens")
    if not T:
        return
    fig, axes = plt.subplots(1, 2, figsize=(COL, 1.7), gridspec_kw={"width_ratios": [0.8, 1.2]})
    ax = axes[0]
    v = [T["tokens_per_100_chars"]["en2kk"], T["tokens_per_100_chars"]["kk2en"]]
    bars = ax.bar([0, 1], v, 0.6, color=[KK, EN])
    for bx, val in zip(bars, v):
        ax.text(bx.get_x() + bx.get_width() / 2, val + 0.8, f"{val:.1f}", ha="center", fontsize=6.5)
    ax.set_xticks([0, 1], ["Kazakh\noutput", "English\noutput"])
    ax.set_ylabel("Output tokens per 100 chars")
    ax.set_ylim(0, max(v) * 1.25)
    _label(ax, "a")
    ax = axes[1]
    ratio = np.array(T["item_ratio"])
    gap = s["en2kk"] - s["kk2en"]
    ax.scatter(ratio, gap, s=5, color=KK, alpha=0.7, edgecolor="none")
    ax.axhline(0, color=GREY, lw=0.6, ls="--")
    ax.set_xlabel("Token ratio, KK/EN output (per item)")
    ax.set_ylabel("Sentence chrF2 gap")
    rho = T["spearman_item_ratio_vs_gap"]
    ax.set_ylim(top=55)
    ax.text(0.98, 0.97, f"Spearman ρ = {rho['rho']:.2f}, p = {rho['p']:.2f}", transform=ax.transAxes,
            ha="right", va="top", fontsize=6.5)
    _label(ax, "b")
    fig.tight_layout(w_pad=0.8)
    _save(fig, out / "fig_tokens.pdf")


def make_all(R, rows, s, systems, main_tab, out, main_model):
    out.mkdir(parents=True, exist_ok=True)
    fig_direction(main_tab, out)
    fig_paired(rows, s, set(R["script"]["mostly_latin_outputs"]), out)
    fig_forest(R, out)
    fig_inflection(R, out)
    fig_tokens(R, rows, s, out)
