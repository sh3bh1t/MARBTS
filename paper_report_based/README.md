# MARBTS Report-Based Paper Bundle

This bundle contains a fresh paper rewrite prepared from the CIP81 project report, with repository artifacts used only for implementation and metric verification.

## Contents

- `main.tex`: rewritten research-paper version of the MARBTS project.
- `figures/`: report-derived diagrams and result plots used by `main.tex`.
- `data/`: selected repository artifact JSON/Markdown files used to verify reported metrics.
- `source/CIP81-1.pdf`: source report provided by the user.
- `notes/source_crosscheck.md`: concise record of the report-to-repo consistency checks.

## Source-Of-Truth Policy

The CIP81 report is the narrative source of truth for project goals, scope, requirements, design intent, and reported experimental findings. The repository was used to verify exact module paths, console scripts, Python dependencies, enum/action names, transition behavior, and stored artifact metrics.

## Originality Note

The paper text in `main.tex` is rewritten in fresh prose rather than copied from the report. Shared project names, module names, action labels, numerical results, and bibliography facts are necessarily retained for accuracy. No proprietary plagiarism service is available in this environment, so this bundle cannot certify a commercial similarity score; it is prepared to minimize verbatim overlap while preserving technical correctness.

## Local Validation

The paper bundle was checked for referenced figure availability, citation consistency, local repository test status, and zip integrity. A full PDF compile was not run because `pdflatex` is not installed in the current environment.
