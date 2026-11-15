# Expanded study protocol

The benchmark now contains 1000 MT, 1000 QA, and 1000 templated probes. This is a new frozen study. The historical Gemini results are retained in the earlier project.

900 QA items are published Belebele. The additional 100 are constructed reading/arithmetic tasks with explicitly defined answers. They have a different difficulty and construct and are reported separately. The 1000 probes are combinations of ten grammatical templates, ten subjects, and ten locations. Independent human review is pending for these 1100 constructed items. They are not 1100 independently authored language phenomena.

This expanded study has no pilot set. Calibration failures and model replacements must be documented before interpreting final scores. Scores on partial model coverage remain exploratory. Generated answer keys are references, while model outputs are populated only from actual inference.

Qwen 2.5 1.5B failed to finish a calibration translation due to repeated text at the token limit. With user approval it is replaced by Qwen 2.5 7B. Failed calls were not saved as successful benchmark answers.
