<!-- One page. Fill the bracketed fields, then paste into the journal's cover-letter box or a letterhead document. -->

[Date]

The Editor-in-Chief
*IEEE Access*

**Submission: "Kazakh–English Performance Gaps in Large Language Models: A Paired Benchmark with Morphology- and Tokenization-Aware Diagnostics"**

Dear Editor,

We submit the above manuscript for consideration as a regular article in *IEEE Access*.

Large language models are now routinely used to translate into and out of Kazakh, an agglutinative Turkic language spoken by over thirteen million people, but their reliability has rarely been measured on content held constant across Kazakh and English. Our study addresses this gap with a paired, within-item design. We release KAZLLM, a hash-frozen benchmark of 430 Kazakh–English items (830 prompts per model) and an auditable pipeline, and we show for a widely deployed model that translation into Kazakh is 8.93 chrF2 points worse than translation into English on the same 138 FLORES-200 sentences (paired 95% CI [−12.19, −5.64]). The gap is robust across four metrics and three sensitivity analyses. We then test explanations rather than only reporting scores: a prefix-based analysis with a mismatched-reference control shows that same-stem, different-ending divergence is four times as frequent in Kazakh outputs, a truncation ablation shows that word-level metrics overstate the deficit while chrF2 does not, and API-reported token counts show that Kazakh costs about twice as many tokens per character.

We believe the manuscript fits the scope of *IEEE Access* because it is an applied, reproducible evaluation of AI systems with direct relevance to engineering practice in multilingual language technology. It continues a line of work recently published in the journal on Kazakh and low-resource language processing, including Kazakh–English neural machine translation (Yazar and Kılıç, 2025, doi:10.1109/ACCESS.2025.3542491), fine-tuning of large language models for low-resource translation (Liang et al., 2025, doi:10.1109/ACCESS.2025.3549795), and Kazakh question answering (Mukanova et al., 2024, doi:10.1109/ACCESS.2024.3433426).

All data, code, model responses and the scripts that regenerate every table and figure are publicly available, and the limitations of the current evidence are stated explicitly in the manuscript. The manuscript is original, has not been published elsewhere and is not under consideration by another journal. All authors have approved the submission and declare no conflicts of interest. The use of generative AI tools is disclosed in the manuscript in line with IEEE policy.

Suggested reviewers (optional): [names, affiliations, e-mails; no conflicts of interest].

Sincerely,

[Corresponding author name]
School of Software Engineering, Astana IT University, Astana, Kazakhstan
[e-mail]
On behalf of all authors
