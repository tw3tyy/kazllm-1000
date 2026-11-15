# Data sources and construction

FLORES-200 is provided by Meta through https://github.com/facebookresearch/flores/tree/main/flores200 and https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz . Its published dataset license applies to the parallel text. The paired English and Kazakh development files were used in line order.

Belebele is provided by Meta through https://github.com/facebookresearch/belebele and https://dl.fbaipublicfiles.com/belebele/Belebele.zip . Its upstream dataset licenses apply. This package uses the 900 published English and Kazakh records, joined by link and question number, with uniqueness and alignment checks.

The additional 100 QA items were constructed with AI assistance as elementary reading/arithmetic examples, using ten names and ten book counts. Correct answers follow the text's subtraction rule. They differ from the published Belebele task and are reported separately.

The 1000 probes were constructed with AI assistance from ten templates, ten subject nouns, and ten location phrases. Source labels and pending human-review flags are stored in each item. Template combinations do not establish 1000 independent linguistic phenomena. Reference translations need independent Kazakh review before making confirmatory language-quality claims.

Hashes of downloaded official archives are in data/expanded_sources.json. The input manifest records the benchmark, empty pilot, and generated prompts. The original project code is covered by LICENSE; upstream text retains its respective data licenses.
