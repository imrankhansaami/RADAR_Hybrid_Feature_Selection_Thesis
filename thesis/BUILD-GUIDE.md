# Thesis build and results fill-in guide

**Deliverable:** `Hybrid Voting and Percentage-Sweep Feature Selection for Ransomware Detection from Sysmon Events.docx`
in this folder. Every result table is now produced by our own runs: the build pulls the numbers from
`results/*.json` through `experiments/results_data.py` — no cell is typed by hand.

**Preview of the exact pagination:** `thesis/build/thesis.pdf` (generated from the .docx with LibreOffice).

## What is inside the document

| Part | Pages |
|---|---|
| Cover (dark green, gold text) | unnumbered |
| Title page | unnumbered |
| Declaration | v |
| Abstract | vi |
| Acknowledgment | vii |
| Table of Content | viii–ix |
| List of Figures / List of Tables | x / xi |
| Chapter 1: Introduction | 1–3 |
| Chapter 2: Background | 4–10 |
| Chapter 3: Review of the Literature | 11–14 |
| Chapter 4: Implementation and Result | 15–25 |
| Chapter 5: Conclusion + 5.1 Future Work | 26–27 |
| Statements (data availability, AI tools, ethics) | 28 |
| References (48 entries) | 29–40 |

Format matches the old thesis: Times New Roman 12 pt, justified, page number top-right with a rule,
chapter titles centred between rules, `Fig x.y:` captions below figures, `Table N:` captions below tables,
dotted-leader ToC/LoF/LoT, roman numerals in the front matter.

## What you must fill in

1. **Placeholders** — search the document for `[` and replace:
   - Cover, title page, declaration, acknowledgment: `[Student Name 1..3]`, `[00000]` (roll),
     `[0000000000]` (reg), `[Supervisor Name]`, `[Title]`, `[Head of the Department]`, `[Rank]`, `[Month DD, YYYY]`.
2. **Abstract and Chapter 5** do not state numbers yet — add one or two sentences with your headline
   results after the runs, if your supervisor wants a results-bearing abstract.

Everything else is done. The result tables are generated from the runs at build time
(`results/*.json` → `experiments/results_data.py` → `thesis/scripts/ch4.py`). Section 4.2 also
reports, with numbers taken from the same files: the 5-seed repeats and significance tests
(McNemar + paired-bootstrap CIs), the E8 sensitivity checks (Imbalanced-5, θ = 0.75, RFE
ablation, balancing arms) and the E7 drift check (chronological split, classical models plus
the compact A2G-PTH). The Statements section (data availability, AI tools, ethics) sits
between Chapter 5 and References.

After editing the .docx in Word, only the ToC/LoF/LoT page numbers and the table-of-figures may need a manual
refresh if your edits change pagination. (Word can update the ToC field-style lists, but the numbers in this
document are plain text; type over them.)

## How the document was generated (rebuild option)

- `thesis/scripts/` — Python scripts (python-docx) that build the .docx, plus the figure generator
  (`figures.py`) and the page-map extractor (`extract_pagemap.py`).
- `thesis/figures/` — the six diagrams (PNG) used in the thesis.
- `experiments/` — the run scripts that produce `results/*.json` (classical pipeline, A2G-PTH,
  seed/significance, sensitivity, drift); see the repository README for the run order.
- `results/` — the raw run outputs; the build reads only these files for every table number.
- `data/radar_repo/` — the downloaded RADAR repository (Zenodo record 14542547).
- `data/engineered/` — the Imbalanced-10, Imbalanced-5 and Drift engineered CSVs used for the audit numbers.

To regenerate the document and its page numbers after editing the scripts:

```powershell
python thesis\scripts\build.py
powershell -File thesis\scripts\build_cycle.ps1   # builds + converts to PDF (needs LibreOffice)
python thesis\scripts\extract_pagemap.py          # refreshes ToC/LoF/LoT numbers from the PDF
powershell -File thesis\scripts\build_cycle.ps1   # rebuild + convert with refreshed numbers
```

## Notes

- The dataset audit numbers in Table 2 were recomputed from the delivered CSVs and differ from the plan's
  draft table under a documented deduplication rule (duplicates over the 21 features + label; the full-record
  rule is noted in the table footnote). Keep the rule you use in your runs consistent with the table.
- Verify the final bibliographic details of references [1] and [2] (conference proceedings, pages) before
  submission; the printed conference titles are used as given in your working plan.
- The RADAR README inconsistency (413,556 events, 19 features) versus the delivered files (350,604 rows,
  21 features in Imbalanced-10) is reported in Section 4.1, as recommended by the working plan.
