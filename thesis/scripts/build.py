"""Orchestrates the complete thesis .docx build."""
import os
import sys
import json

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # .../thesis
SCRIPTS = os.path.join(BASE, 'scripts')
sys.path.insert(0, SCRIPTS)

from lib import setup_document, add_section, add_page_number_header, \
    set_page_numbering, clear_header, BuildState, page_break
import front
import ch1
import ch2
import ch3
import ch4
import ch5
import statements
import refs

FIGDIR = os.path.join(BASE, 'figures')
BUILDDIR = os.path.join(BASE, 'build')
os.makedirs(BUILDDIR, exist_ok=True)
PAGEMAP_PATH = os.path.join(BUILDDIR, 'pagemap.json')
OUT_DOCX = os.path.join(BUILDDIR, 'thesis.docx')

# (level, display text, search key, fixed page)
# level 0 = chapter style line, 1 = subsection indent
TOC_ENTRIES = [
    (0, 'Table of Content', None, 'viii'),
    (0, 'List of Figures', None, 'x'),
    (0, 'List of Tables', None, 'xi'),
    (0, '1.  Introduction', 'Chapter 1: Introduction', None),
    (1, '1.1  Project Overview', '1.1  Project Overview', None),
    (1, '1.2  Motivation', '1.2  Motivation', None),
    (1, '1.3  Objectives', '1.3  Objectives', None),
    (1, '1.4  Methodology', '1.4  Methodology', None),
    (1, '1.5  Project Outcome', '1.5  Project Outcome', None),
    (0, '2.  Background', 'Chapter 2: Background', None),
    (1, '2.1  Ransomware and Sysmon Event Telemetry',
     '2.1  Ransomware and Sysmon Event Telemetry', None),
    (1, '2.2  Feature Selection: Concepts and Categories',
     '2.2  Feature Selection: Concepts and Categories', None),
    (1, '2.3  Statistical Measures for Feature Ranking',
     '2.3  Statistical Measures for Feature Ranking', None),
    (1, '2.4  Hybrid Consensus Voting (FS-A)',
     '2.4  Hybrid Consensus Voting (FS-A)', None),
    (1, '2.5  Percentage-Sweep Selection: FS-B and FS-C',
     '2.5  Percentage-Sweep Selection: FS-B and FS-C', None),
    (1, '2.6  Classical Machine Learning Classifiers',
     '2.6  Classical Machine Learning Classifiers', None),
    (1, '2.7  The A2G-PTH Adversarial Graph Model',
     '2.7  The A2G-PTH Adversarial Graph Model', None),
    (1, '2.8  Evaluation Metrics', '2.8  Evaluation Metrics', None),
    (0, '3.  Review of the Literature', 'Chapter 3: Review of the Literature', None),
    (1, '3.1  Preliminaries', '3.1  Preliminaries', None),
    (1, '3.2  Literature Review', '3.2  Literature Review', None),
    (1, '3.3  Summary', '3.3  Summary', None),
    (0, '4.  Implementation and Result', 'Chapter 4: Implementation and Result', None),
    (1, '4.1  Evaluation', '4.1  Evaluation', None),
    (1, '4.2  Result and Discussion', '4.2  Result and Discussion', None),
    (1, '4.3  Summary', '4.3  Summary', None),
    (0, '5.  Conclusion', 'Chapter 5: Conclusion', None),
    (1, '5.1  Future Work', '5.1  Future Work', None),
    (0, 'Statements', 'Statements', None),
    (0, 'References', 'References', None),
]

FIGURES = [
    ('Fig 1.1: Framework of the proposed study',),
    ('Fig 2.1: Categories of feature selection methods',),
    ('Fig 2.2: Workflow of the hybrid consensus voting selector (FS-A)',),
    ('Fig 2.3: Workflow of the percentage sweep (FS-B) and the voting-ranked sweep (FS-C)',),
    ('Fig 2.4: Architecture of the A2G-PTH model (adapted from [2])',),
    ('Fig 4.1: End-to-end pipeline with the leakage controls',),
]

TABLES = [
    'Table 1: The two reference papers and the scope of this thesis',
    'Table 2: Audited composition of the RADAR engineered files (Class 0 = goodware, Class 1 = ransomware)',
    'Table 3: The 21 engineered features of RADAR, by group',
    'Table 4: Evaluation protocols',
    'Table 5: Settings of the seven classical classifiers',
    'Table 6: Experiment matrix (fixed before running)',
    'Table 7: Training-set voting table (FS-A), computed on the primary file',
    'Table 8: Subset sizes across the percentage sweep',
    'Table 9: Percentage-sweep validation results for FS-B and FS-C',
    'Table 10: Agreement between selectors and stability of the kept subsets',
    'Table 11: Test-set F1 (ransomware class) of the classical models per subset',
    'Table 12: Detailed metrics of the best configuration per selector (primary split)',
    'Table 13: Leakage gap between the random and group splits',
    'Table 14: A2G-PTH results for the key inputs and both graph variants',
    'Table 15: Computational cost per configuration',
]


def build(pagemap):
    doc = setup_document()
    st = BuildState(pagemap=pagemap)

    # Section 1: cover + title page (no page numbers)
    sec1 = doc.sections[0]
    clear_header(sec1)
    front.build_cover(doc, st)
    front.build_title(doc, st)

    # Section 2: front matter, roman numerals starting at v
    sec2 = add_section(doc)
    add_page_number_header(sec2)
    set_page_numbering(sec2, 'lowerRoman', 5)
    front.build_declaration(doc, st)
    front.build_abstract(doc, st)
    front.build_acknowledgment(doc, st)
    toc_display = [(lv, tx, ky, fx) for (lv, tx, ky, fx) in TOC_ENTRIES]
    front.build_toc(doc, st, toc_display, n_mid=20)
    front.build_lof(doc, st, FIGURES)
    front.build_lot(doc, st, TABLES)

    # Section 3: body, arabic numerals starting at 1
    sec3 = add_section(doc)
    add_page_number_header(sec3)
    set_page_numbering(sec3, 'decimal', 1)
    ch1.build(doc, st)
    ch2.build(doc, st)
    ch3.build(doc, st)
    ch4.build(doc, st)
    ch5.build(doc, st)
    statements.build(doc, st)
    refs.build(doc, st)

    assert len(refs.REFS) == 48, 'reference count changed: %d' % len(refs.REFS)
    doc.save(OUT_DOCX)
    print('saved', OUT_DOCX)
    return OUT_DOCX


if __name__ == '__main__':
    pagemap = {}
    if os.path.exists(PAGEMAP_PATH):
        with open(PAGEMAP_PATH, 'r', encoding='utf-8') as fh:
            pagemap = json.load(fh)
        print('loaded pagemap with %d entries' % len(pagemap))
    build(pagemap)
