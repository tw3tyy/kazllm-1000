"""Analysis helpers for the final manuscript.

Every function here works only on saved benchmark files and saved model responses.
Nothing queries a model and nothing is simulated.
"""
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from sacrebleu.metrics import BLEU, CHRF, TER
from scipy import stats

from kazllm import prompts as templates
from kazllm import query
from kazllm.baselines import heuristic_translate

SEED = 42
N_BOOT = 1000
DIRECTIONS = ("en2kk", "kk2en")

# sacreBLEU metric objects. chrF2 is the primary metric (char order 6, beta 2).
METRICS = {
    "chrf2": CHRF(),
    "chrfpp": CHRF(word_order=2),
    "bleu": BLEU(),
    "ter": TER(),
}
HIGHER_IS_BETTER = {"chrf2": True, "chrfpp": True, "bleu": True, "ter": False}


def signatures():
    """sacreBLEU builds a signature only after one evaluation, so score a dummy pair first."""
    out = {}
    for name, m in METRICS.items():
        m.corpus_score(["a"], [["a"]])
        out[name] = str(m.get_signature())
    return out

_WORD = re.compile(r"[^\W\d_]+", re.UNICODE)
_LATIN = re.compile(r"[A-Za-z\u00C0-\u024F]")
_CYRILLIC = re.compile(r"[\u0400-\u04FF]")


# --------------------------------------------------------------------------- inputs
def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_benchmark(repo):
    repo = Path(repo)
    bench = read_jsonl(repo / "data/benchmark.jsonl")
    ps = templates.build_prompts(bench)
    overlap = set(json.loads((repo / "data/overlap_audit.json").read_text())["excluded_item_ids"])
    return {r["item_id"]: r for r in bench}, ps, overlap


def load_outputs(path, prompts):
    """Saved responses keyed by prompt_id. Records whose prompt hash does not match the frozen prompt are rejected."""
    path = Path(path)
    if not path.exists():
        return {}
    meta = {p["prompt_id"]: p for p in prompts}
    out = {}
    for r in read_jsonl(path):
        pid = r["prompt_id"]
        if pid not in meta:
            raise ValueError(f"Unknown prompt id in {path.name}: {pid}")
        if "prompt_sha256" in r and r["prompt_sha256"] != query.digest(meta[pid]["prompt"]):
            raise ValueError(f"Prompt hash mismatch in {path.name}: {pid}")
        if pid in out:
            raise ValueError(f"Duplicate response in {path.name}: {pid}")
        out[pid] = r
    return out


def mt_pairs(bench, prompts, out_map):
    """Items with a saved response in BOTH directions, in benchmark order."""
    by_item = defaultdict(dict)
    for p in prompts:
        if p["task"] == "mt":
            by_item[p["item_id"]][p["condition"]] = p
    rows = []
    for iid, d in by_item.items():
        if all(d[c]["prompt_id"] in out_map for c in DIRECTIONS):
            b = bench[iid]
            rec = {c: out_map[d[c]["prompt_id"]] for c in DIRECTIONS}
            rows.append({
                "item_id": iid, "source": b.get("source"), "domain": b.get("domain"),
                "en": b["en"], "kk": b["kk"],
                "hyp_en2kk": templates.clean_translation(rec["en2kk"].get("output")),
                "hyp_kk2en": templates.clean_translation(rec["kk2en"].get("output")),
                "rec_en2kk": rec["en2kk"], "rec_kk2en": rec["kk2en"],
            })
    rows.sort(key=lambda r: r["item_id"])
    return rows


def dictionary_baseline(rows):
    """The frozen word-substitution baseline from kazllm/baselines.py, applied to the same items."""
    return [{**r, "hyp_en2kk": heuristic_translate(r["en"], "english", "kazakh"),
             "hyp_kk2en": heuristic_translate(r["kk"], "kazakh", "english"), "rec_en2kk": {}, "rec_kk2en": {}}
            for r in rows]


# --------------------------------------------------------------------------- corpus metrics + bootstrap
def refs_for(direction):
    return "kk" if direction == "en2kk" else "en"


def segment_stats(rows, direction, metric):
    m = METRICS[metric]
    hyps = [r[f"hyp_{direction}"] for r in rows]
    refs = [[r[refs_for(direction)] for r in rows]]
    return np.asarray(m._extract_corpus_statistics(hyps, refs), dtype=float)


def score_from_stats(metric, summed):
    m = METRICS[metric]
    if metric == "bleu":
        summed = [int(round(x)) for x in summed]
    return float(m._compute_score_from_stats(list(summed)).score)


def boot_indices(n, n_boot=N_BOOT, seed=SEED):
    """One seeded index matrix. Every interval in the paper uses the same resamples (paired bootstrap)."""
    rng = np.random.default_rng(seed)
    return np.stack([rng.integers(0, n, n) for _ in range(n_boot)])


def corpus_with_ci(seg, idx, metric):
    point = score_from_stats(metric, seg.sum(0))
    draws = np.array([score_from_stats(metric, seg[i].sum(0)) for i in idx])
    lo, hi = np.percentile(draws, [2.5, 97.5])
    return {"point": point, "lo": float(lo), "hi": float(hi)}, draws


def gap_with_ci(seg_kk, seg_en, idx, metric):
    """gap = score(EN->KK) - score(KK->EN); negative means lower quality into Kazakh."""
    point = score_from_stats(metric, seg_kk.sum(0)) - score_from_stats(metric, seg_en.sum(0))
    draws = np.array([score_from_stats(metric, seg_kk[i].sum(0)) - score_from_stats(metric, seg_en[i].sum(0))
                      for i in idx])
    lo, hi = np.percentile(draws, [2.5, 97.5])
    return {"point": float(point), "lo": float(lo), "hi": float(hi)}


def sentence_chrf(rows, direction):
    m = METRICS["chrf2"]
    return np.array([m.sentence_score(r[f"hyp_{direction}"], [r[refs_for(direction)]]).score for r in rows])


# --------------------------------------------------------------------------- tests
def wilcoxon(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    res = stats.wilcoxon(a, b)
    d = a - b
    d = d[d != 0]
    ranks = stats.rankdata(np.abs(d))
    r_rb = (ranks[d > 0].sum() - ranks[d < 0].sum()) / ranks.sum()
    return {"W": float(res.statistic), "p": float(res.pvalue), "n": int(len(a)),
            "median_diff": float(np.median(a - b)), "rank_biserial_r": float(r_rb)}


def holm(pvals):
    order = sorted(range(len(pvals)), key=lambda i: pvals[i])
    adj, running = [0.0] * len(pvals), 0.0
    for k, i in enumerate(order):
        running = max(running, min(1.0, (len(pvals) - k) * pvals[i]))
        adj[i] = running
    return adj


def exact_ci(k, n):
    if n == 0:
        return (0.0, 0.0)
    ci = stats.binomtest(k, n).proportion_ci(confidence_level=0.95, method="exact")
    return (float(ci.low), float(ci.high))


def mcnemar_exact(kk, en):
    kk_only = sum(1 for x, y in zip(kk, en) if x and not y)
    en_only = sum(1 for x, y in zip(kk, en) if y and not x)
    n = kk_only + en_only
    p = 1.0 if n == 0 else float(stats.binomtest(min(kk_only, en_only), n, 0.5).pvalue)
    return {"kk_only": kk_only, "en_only": en_only, "p": p}


# --------------------------------------------------------------------------- script audit
def latin_share(text):
    lat, cyr = len(_LATIN.findall(text or "")), len(_CYRILLIC.findall(text or ""))
    return lat / (lat + cyr) if lat + cyr else 0.0


# --------------------------------------------------------------------------- inflection-tolerant matching
def words(text):
    return [w.lower() for w in _WORD.findall(text or "")]


def unigram_matches(hyp, ref, k=None):
    """Clipped unigram matches between hypothesis and reference words; with k, words are cut to k-letter prefixes."""
    h, r = words(hyp), words(ref)
    if k:
        h, r = [w[:k] for w in h], [w[:k] for w in r]
    ch, cr = Counter(h), Counter(r)
    return sum(min(c, cr[w]) for w, c in ch.items()), len(h), len(r)


def inflection_table(rows, direction, k, ref_shift=0):
    """Per item: exact matches, prefix-k matches, hypothesis and reference lengths.
    ref_shift > 0 pairs each output with the reference of another item (chance-level control)."""
    n = len(rows)
    ref_key = refs_for(direction)
    out = []
    for i, r in enumerate(rows):
        ref = rows[(i + ref_shift) % n][ref_key]
        m_full, hl, rl = unigram_matches(r[f"hyp_{direction}"], ref)
        m_k, _, _ = unigram_matches(r[f"hyp_{direction}"], ref, k)
        out.append((m_full, m_k, hl, rl))
    return np.asarray(out, dtype=float)


def near_miss_rate(table):
    """Share of reference words matched only after prefix truncation (same stem, different ending)."""
    m_full, m_k, _, rl = table.sum(0)
    return float((m_k - m_full) / rl)


def exact_recall(table):
    m_full, _, _, rl = table.sum(0)
    return float(m_full / rl)


def near_miss_with_ci(rows, k, idx, shift):
    """Observed near-miss rate per direction, a mismatched-reference control, and the paired KK-EN contrast."""
    res = {}
    tabs = {d: inflection_table(rows, d, k) for d in DIRECTIONS}
    ctrl = {d: inflection_table(rows, d, k, ref_shift=shift) for d in DIRECTIONS}
    for d in DIRECTIONS:
        draws = [near_miss_rate(tabs[d][i]) for i in idx]
        res[d] = {"rate": near_miss_rate(tabs[d]), "lo": float(np.percentile(draws, 2.5)),
                  "hi": float(np.percentile(draws, 97.5)), "exact_recall": exact_recall(tabs[d]),
                  "control_rate": near_miss_rate(ctrl[d])}
        res[d]["net_rate"] = res[d]["rate"] - res[d]["control_rate"]
    diff = [near_miss_rate(tabs["en2kk"][i]) - near_miss_rate(tabs["kk2en"][i]) for i in idx]
    res["kk_minus_en"] = {"point": res["en2kk"]["rate"] - res["kk2en"]["rate"],
                          "lo": float(np.percentile(diff, 2.5)), "hi": float(np.percentile(diff, 97.5))}
    return res


# --------------------------------------------------------------------------- token usage
def token_usage(rows):
    """Visible output tokens reported by the API for the same items in both directions."""
    t = {d: [] for d in DIRECTIONS}
    c = {d: [] for d in DIRECTIONS}
    p = {d: [] for d in DIRECTIONS}
    for r in rows:
        for d in DIRECTIONS:
            um = (r[f"rec_{d}"].get("response") or {}).get("usageMetadata") or {}
            t[d].append(um.get("candidatesTokenCount"))
            p[d].append(um.get("promptTokenCount"))
            c[d].append(len(r[f"hyp_{d}"]))
    if any(v is None for d in DIRECTIONS for v in t[d] + p[d]):
        return None
    return {d: {"out_tokens": np.array(t[d], float), "out_chars": np.array(c[d], float),
                "prompt_tokens": np.array(p[d], float)} for d in DIRECTIONS}


# --------------------------------------------------------------------------- QA
def qa_baseline_answers(prompts, seed=SEED):
    """Always-A and the seeded uniform-random rule used by kazllm/baselines.py (same RNG call order)."""
    rng = random.Random(seed)
    fixed, rand = {}, {}
    for r in prompts:
        if r["task"] == "qa":
            fixed[r["prompt_id"]] = "A"
            rand[r["prompt_id"]] = rng.choice(["A", "B", "C", "D"])
    return fixed, rand


def score_qa(prompts, answers):
    """answers: prompt_id -> raw text. Items need both language versions; unparsable answers count as wrong."""
    by_item = defaultdict(dict)
    for r in prompts:
        if r["task"] == "qa":
            by_item[r["item_id"]][r["condition"]] = r
    kk, en, unparsed = [], [], 0
    for _, d in sorted(by_item.items()):
        if not all(d[c]["prompt_id"] in answers for c in ("qa_kk", "qa_en")):
            continue
        ok = {}
        for c in ("qa_kk", "qa_en"):
            pred = templates.parse_choice(answers[d[c]["prompt_id"]])
            unparsed += pred is None
            ok[c] = pred == d[c]["gold"]
        kk.append(ok["qa_kk"])
        en.append(ok["qa_en"])
    n = len(kk)
    if n == 0:
        return {"n": 0}
    t = mcnemar_exact(kk, en)
    return {"n": n, "acc_kk": sum(kk) / n, "acc_en": sum(en) / n, "ci_kk": exact_ci(sum(kk), n),
            "ci_en": exact_ci(sum(en), n), "diff_pp": 100 * (sum(kk) - sum(en)) / n, "unparsed": unparsed,
            "kk_only": t["kk_only"], "en_only": t["en_only"], "p_mcnemar": t["p"]}
