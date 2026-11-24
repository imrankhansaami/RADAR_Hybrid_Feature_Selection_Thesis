# Hybrid Voting and Percentage-Sweep Feature Selection for Ransomware Detection from Sysmon Events

Bachelor's thesis (Sylhet International University, Department of CSE). The study is about
**feature selection** for ransomware detection on **RADAR**, a published dataset of Sysmon
host events collected from goodware and ransomware executions.

The thesis re-implements two published selectors on RADAR with every threshold recomputed
from RADAR training scores — consensus **voting** (FS-A) and the **percentage sweep** with a
combined chi-square/F-test/mutual-information score (FS-B) — and proposes a **voting-ranked
sweep (FS-C)** that links the two. The kept subsets are evaluated with seven classical
classifiers and with the A2G-PTH deep model under a paper-faithful random split, a
leakage-aware group split and a chronological drift split, with repeated seeds, significance
tests and computational-cost measurements.

## Repository map

| Path | What it is |
|---|---|
| `thesis/Hybrid ... .docx` / `.pdf` | the finished thesis (every result table filled from `results/`) |
| `thesis/scripts/` | the python-docx build chain that produces the document; result numbers are pulled from `results/*.json` at build time |
| `thesis/scripts/build_cycle.ps1` | one-command rebuild: docx → PDF via LibreOffice → page map |
| `thesis/BUILD-GUIDE.md` | build and fill-in guide (what is left: the front-matter placeholders) |
| `thesis/figures/` | the six diagrams used in the thesis |
| `RADAR_Hybrid_Feature_Selection_Thesis_Plan.docx` | the working plan (dataset, protocols, experiment matrix fixed before the runs) |
| `experiments/` | all experiment code (classical pipeline, A2G-PTH, seed/significance, sensitivity, drift) |
| `results/*.json` | the raw output of every run — every number in the thesis traces back to these files |
| `requirements.txt` | the Python environment used for the runs and the document build |
| `MLRan_*` and `Thesis_Final.ipynb` | a **separate exploratory side study** on the AI-derived MLRan dataset — *not* part of the thesis (see below) |
| `thesis raw.pdf` | earlier compiled draft, kept for history |

## Headline results (archived run in `results/`)

| Configuration | Model | Test F1 (ransomware) | F2 | Notes |
|---|---|---|---|---|
| All 21 features | XGBoost | 0.6056 | 0.7711 | baseline (P1 random split) |
| FS-A — voting, 8 features | KNN | 0.5709 | 0.7412 | F2 just outside the pre-fixed 0.02 margin |
| FS-B — sweep, 6 features (p = 30 %) | Decision tree | 0.6173 | 0.7920 | best single F1 |
| FS-C — vote-ranked sweep, 10 features (p = 50 %) | XGBoost | 0.6033 | 0.7688 | within margin; not significantly different from baseline (McNemar p = 0.099) |

Other checks: kept subsets are identical across repeated seeds (Jaccard 1.00); the
leakage-aware group split (P2) moves test F1 by at most 0.013, so the random-split numbers
are not materially optimistic; the A2G-PTH deep model reproduces the subset ordering
(all 21: F1 0.5701, FS-C: 0.5668, FS-A: 0.5497); on the chronological drift split the
vote-based subsets stay above the full set (FS-A 0.2365, FS-C 0.2272 vs 0.1978).

## Reproducing the results

1. Download RADAR from Zenodo (<https://doi.org/10.5281/zenodo.14542547>) and place the
   engineered CSVs in `data/engineered/` (not committed — they are ~30 MB each):

   ```text
   data/engineered/dataset-imbalanced-10-engineered.csv   # primary file
   data/engineered/dataset-imbalanced-5-engineered.csv    # sensitivity file
   data/engineered/dataset-drift-engineered.csv           # drift file
   ```

2. `pip install -r requirements.txt`

3. Run the pipelines from the repository root (each writes into `results/`):

   ```bash
   python experiments/run_experiments.py   # P1 + P2 classical runs, voting/sweep tables, cost
   python experiments/run_a2g.py           # A2G-PTH deep evaluator (both graph variants)
   python experiments/run_statistics.py    # 5-seed repeats + McNemar/paired-bootstrap tests
   python experiments/run_sensitivity.py   # E8: Imbalanced-5, theta=0.75, RFE ablation, balancing arms
   python experiments/run_drift.py         # E7: chronological split of the Drift stream
   python experiments/run_a2g_drift.py     # E7 companion: compact A2G-PTH on the drift split
   ```

4. Rebuild the thesis document (needs LibreOffice for the PDF step):

   ```powershell
   python thesis\scripts\build.py
   powershell -File thesis\scripts\build_cycle.ps1   # docx -> PDF
   python thesis\scripts\extract_pagemap.py          # refresh ToC/LoF/LoT page numbers
   powershell -File thesis\scripts\build_cycle.ps1   # rebuild with refreshed numbers
   ```

## Dataset and reference papers

- **RADAR** — J. Ispahany, O. B. Deho, M. R. Islam, M. A. Khan and M. Z. Islam,
  *RADAR: a realistic dataset for advancing ransomware detection*, Cybersecurity, 2025;
  dataset DOI [10.5281/zenodo.14542547](https://doi.org/10.5281/zenodo.14542547).
- **[1]** A. Goni, R. J. Momtahina and R. R. Chowdhury, *A Hybrid Voting-Based Feature
  Selection Approach for Identifying Intrusions in IoT Networks*, WIECON-ECE 2025.
- **[2]** A. Goni, R. J. Momtahina and R. R. Chowdhury, *A2G-PTH: An Adversarial Autoencoder
  Graph Neural Network for Proactive Threat Hunting in IoT*, ICCIT 2025.

See `CITATION.cff` to cite this repository (fill in the author names before archiving).

## Statements

- **Data availability** — all analysis uses the public RADAR dataset above; no new telemetry
  was collected. The code and the run outputs that produce every number in the thesis are in
  this repository (`experiments/`, `results/`).
- **AI tools** — an AI-based assistant was used to help implement the pipeline and prepare
  the manuscript; the study design was fixed before the runs, all experiments were run and
  verified by the authors (see the "Statements" section of the thesis).
- **Ethics** — no human participants, personal data or live malware were involved; the study
  uses a previously collected, publicly released dataset.

## MLRan side study (separate from the thesis)

`Thesis_Final.ipynb` is an exploratory pipeline on the **MLRan** dataset
(<https://github.com/faithfulco/mlran>) — a *different*, AI-derived dataset — and is kept in
this repository for reference only; it is **not** part of the RADAR thesis and none of its
numbers appear in the thesis. It runs the vote-based selection on MLRan's MI-selected
24,162-feature set with the official temporal split (3,905 train / 975 test) plus a
family-disjoint `GroupKFold` protocol; results are in `MLRan_supplementary/`. The raw MLRan
dataset is ~5 GB and is not committed (the notebook downloads the smaller MI set on first
run).

## License

MIT for the code (see `LICENSE`). The thesis text and figures are the authors' work — reuse
with attribution (CC BY 4.0).
