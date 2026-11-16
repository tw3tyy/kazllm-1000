# Appendix B. Submission Readiness Checklist — status on 16 November 2026

| Check | Yes / No | Note |
|---|---|---|
| The manuscript follows the target journal template and word limit | Partly | IEEEtran journal format, ~7,200 words up to the references; move the section files into the official IEEE Access template before submission |
| Abstract, results, discussion, and conclusion report identical numbers | Yes | All numbers come from `paper/generated/numbers.tex` |
| Every number is traceable to a log or output in the repository | Yes | See `paper/README.md`; QA baselines are now saved to `final_results.json` |
| All references are real, read by the authors, and formatted in the journal style | Partly | 40 real, verifiable sources with DOIs where available; each author must read them |
| At least 25 references; at least half from the last 5 years | Yes | 40 references, 25 from 2021 or later |
| Contributions are explicit and supported by the results | Yes | Four contributions in Section I |
| Limitations and threats to validity are discussed | Yes | Section V-E and V-F |
| Data and code availability statement is included | Yes | Add the Zenodo DOI after tagging `final` |
| CRediT author contributions, AI-use, conflict-of-interest, and ethics statements are included | Partly | CRediT roles and the AI tool name must be confirmed by the authors |
| Human-participant data (if any) has prior ethical approval and consent | N/A | No human participants |
| Similarity check completed and acceptable | No | Run the university check |
| Main results reproduced by another person from the README | No | Ask a classmate to run `make results` and compare `final_results.json` |
| All authors have read and approved the final version | No | Also resolve the two-author rule of the course |
