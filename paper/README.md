# Final manuscript: reproduction guide

Every number, table and figure in `main.tex` is produced from the saved logs by one command.
No number is typed by hand: the text reads LaTeX macros from `generated/numbers.tex`.

```sh
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install -r requirements.txt -r requirements-paper.txt
make results      # or: python3 -m paper.analysis.run
make paper        # optional: compiles paper/main.pdf with latexmk
make test         # checks, including exact reproduction of the Assignment 4 gap
```

Seed 42 and 1,000 paired bootstrap resamples are fixed, so reruns give identical numbers.
Tested with Python 3.12 and the versions pinned in `requirements-paper.txt`.

## Where each result comes from

All keys refer to `paper/results/final_results.json`.

| In the manuscript | Generated file | JSON key |
|---|---|---|
| Table III (main translation results) | `generated/tab_main.tex` | `main.<system>.<metric>` |
| Table IV (Wilcoxon tests, Holm) | `generated/tab_tests.tex` | `tests` |
| Table V (robustness, sensitivity, subgroups) | `generated/tab_robustness.tex` | `main.gemini-3.5-flash-lite.*.gap`, `subsets` |
| Table VI (truncation ablation) | `generated/tab_ablation.tex` | `ablation_truncation` |
| Table VII (QA calibration) | `generated/tab_qa.tex` | `qa` |
| Table VIII (provisional labels) | `generated/tab_labels.tex` | `provisional_labels` |
| Fig. 2 (chrF2/BLEU by direction) | `figures/fig_direction.pdf` | `main` |
| Fig. 3 (paired items) | `figures/fig_paired.pdf` | `item_level.csv`, `script` |
| Fig. 4 (forest plot) | `figures/fig_forest.pdf` | `subsets` |
| Fig. 5 (prefix near-miss) | `figures/fig_inflection.pdf` | `inflection.<k>` |
| Fig. 6 (token usage) | `figures/fig_tokens.pdf` | `tokens` |
| Numbers in the text | `generated/numbers.tex` | macro names mirror the keys |

To check a single sentence score, find the item in `results/item_level.csv` and the raw
response with the same `prompt_id` in `outputs/gemini-3.5-flash-lite.jsonl`.

## Adding the pending runs

The analysis picks up new outputs automatically. After running

```sh
./run_gemini.sh --free-tier-confirmed     # remaining Gemini prompts (resumes)
./start_ollama_local.sh                   # terminal 1
./prepare_local.sh && ./run_local.sh      # terminal 2: Qwen 2.5 1.5B and Gemma 3
python3 run_nllb.py                       # NLLB-200 600M (pip install -r requirements-nllb.txt)
```

run `make results`. Systems with complete outputs on the analysed items appear in Table III
and their QA results in Table VII; the prose of the Results and Discussion sections must then
be updated to describe them.

## Overleaf

Upload the whole `paper/` folder (or the release zip), set `main.tex` as the main document
and compile with pdfLaTeX. Overleaf prints the Kazakh examples in Cyrillic; a local TeX
installation without T2A fonts prints a transliteration instead. For the IEEE Access
template, keep `sections/`, `generated/`, `figures/` and `references.bib` and `\input` the
section files into the official template.
