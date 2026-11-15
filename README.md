# KAZLLM expanded study

This is a new isolated evaluation with 1000 translation pairs, 1000 paired QA items, and 1000 grammar probes. It produces 5000 prompts per model. Saved results are actual service responses; counts show current coverage.

## Dataset

- Translation uses the first 1000 unique aligned FLORES-200 development pairs.
- QA contains all 900 published English/Kazakh Belebele questions and 100 constructed reading/arithmetic questions. The two sources are shown separately in website scores.
- Probes contain ten grammatical sentence patterns crossed with ten subjects and ten locations. These 1000 template variants are correlated. The 1100 constructed items require independent human review.
- The old 138-pair experiment remains in the earlier project and must be reported as a different study.
- Source URLs and SHA-256 checksums are stored in data/expanded_sources.json. FLORES and Belebele retain their upstream dataset licenses. The project MIT license applies to code.

## Setup and display

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
./demo.sh --status
open website/index.html
```

## Collect responses

Check the Google project free-tier/billing settings before using the confirmation flag. The key is entered through hidden terminal input. Keep an Ollama server running on 127.0.0.1:11434 for local inference.

```sh
./run_gemini.sh --free-tier-confirmed --max-new 25
./run_local.sh --max-new 25
./refresh_site.sh
```

Use `./run_batch.sh 25` to attempt a batch for Gemini and both local models and rebuild the site. Errors are printed and progress is preserved. Qwen and Gemma are attempted separately, so failure of one does not prevent attempting the other. The scripts skip saved successful prompts. Translation pairs, QA pairs, and probes are interleaved, so each five-prompt block visits all task types. A response is saved only after the service response passes validation. Probe chrF2 measures overlap with the reference.

Omit --max-new to continue through all remaining prompts. Full inference for three models requires 15000 requests and can take hours or days. Free API quotas can require multiple sessions. CLI flags do not establish billing status.

## Scores and final comparison

```sh
./demo.sh --preliminary
./reproduce.sh
```

The final comparison requires complete validated model runs. Until then the website displays available translations, per-source QA accuracy, probe scores, and explicit coverage. Smoke-test records are separate. Model switching never substitutes one model's output for another.

## Checks

```sh
python3 -m unittest discover -s tests -v
```

Use `build_expanded_dataset.py SOURCE_DIR` in a fresh study directory with the official `flores.tar.gz` and `belebele.zip` to rebuild the data. An existing frozen benchmark is protected from replacement.
