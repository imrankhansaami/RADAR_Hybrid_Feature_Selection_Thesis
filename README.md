# RADAR Hybrid Feature Selection — Thesis

Thesis notebook and results for **hybrid feature selection on behavioural ransomware data**
using the [MLRan](https://github.com/faithfulco/mlran) dataset.

## What is here

| File | Purpose |
|---|---|
| `Thesis_Final.ipynb` | Main pipeline: load → vote-based selection → temporal + family-disjoint evaluation |
| `Thesis_Final_original_backup.ipynb` | Original RADAR-based notebook, kept for reference |
| `thesis raw.pdf` | Thesis draft |
| `MLRan_supplementary/results_temporal.csv` | Balanced accuracy / F1 / FNR / AUC by feature set × model |
| `MLRan_supplementary/results_family_disjoint.csv` | Per-fold family-disjoint metrics |
| `MLRan_supplementary/selected_features.csv` | Full 24,162-feature ranking with names, votes and MI |

The raw datasets are **not** committed: `MLRan_full_dataset/` is ~5 GB and is published on
[Zenodo](https://zenodo.org/records/23403681). The notebook downloads the smaller MI set
(~236 MB) automatically on first run.

## Dataset

MLRan contains **4,880 samples** (2,550 goodware + 2,330 ransomware from 64 families) with
nine behavioural modalities: API, registry, file, directory, string, network, system,
drop/delete and signature. The notebook uses the **MI-selected 24,162-feature set** with the
official temporal split (3,905 train / 975 test).

## Pipeline

1. **Load** the MI train/test CSVs (`float32`, labels included).
2. **Vote-based selection** (`paper1_votes`): mutual information, ANOVA F, RFE and
   |correlation|. A feature is kept when at least two of the four rank it above their mean.
   MI uses `discrete_features=True`; RFE runs on the top 2,000 MI features with `step=20`.
3. **Temporal split evaluation** — vote≥2, top-483, the paper's RFE-483, and all MI features.
4. **Family-disjoint protocol** — `GroupKFold` over families (goodware grouped by submission
   year), with selection recomputed inside every fold.
5. **Feature-count sweep** (25 → 1,000) and **modality breakdown** of the selected sets.

## Results (validation run)

| Protocol | Best balanced accuracy |
|---|---|
| Temporal split | 0.977 (LR / XGB on vote≥2 and all-MI) |
| Family-disjoint (2 folds) | 0.959 (XGB), 0.955 (RF) |

The top-483 set is registry-heavy (428/483 registry features) and overlaps the paper's
RFE-483 set by 45 features; mean Jaccard across family folds is 0.514.

## How to run

```bash
pip install numpy pandas scikit-learn xgboost
jupyter notebook Thesis_Final.ipynb
```

On Google Colab the notebook mounts Drive at `/content/drive/MyDrive/Thesis`; locally it
uses the notebook folder. First run downloads the MI CSVs from Zenodo into
`MLRan_supplementary/`. Runtime is about 13 minutes on a laptop.
