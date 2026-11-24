"""Front matter: cover, title page, declaration, abstract, acknowledgment,
table of content, list of figures, list of tables."""
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.shared import Pt, Cm, RGBColor

from lib import (FONT, set_run, add_para, chapter_heading, add_section,
                 page_break, toc_line, remove_table_borders, shade_cell,
                 set_row_height, para_border, clear_header, add_page_number_header,
                 set_page_numbering, CONTENT_WIDTH_CM)

GOLD = RGBColor(0xE8, 0xD8, 0xA8)
GOLD_DIM = RGBColor(0xD8, 0xC8, 0x98)

TITLE = ('Hybrid Voting and Percentage-Sweep Feature Selection '
         'for Ransomware Detection from Sysmon Events')

STUDENTS = [
    ('[Student Name 1]', '[00000]', '[0000000000]'),
    ('[Student Name 2]', '[00000]', '[0000000000]'),
    ('[Student Name 3]', '[00000]', '[0000000000]'),
]
SUPERVISOR = '[Supervisor Name]'
SUPERVISOR_TITLE = '[Title]'
HEAD = '[Head of the Department]'
DATE = '[Month DD, YYYY]'


def _center_run(p, text, size, bold=False, color=None, italic=False, underline=False):
    r = p.add_run(text)
    set_run(r, size=Pt(size), bold=bold, italic=italic, color=color)
    if underline:
        r.underline = True
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return r


def build_cover(doc, st):
    # full-page dark green cover like the bound cover of the old thesis
    table = doc.add_table(rows=1, cols=1)
    table.autofit = False
    remove_table_borders(table)
    cell = table.rows[0].cells[0]
    cell.width = Cm(CONTENT_WIDTH_CM)
    shade_cell(cell, '14352B')
    set_row_height(table.rows[0], 25.0, rule='atLeast')

    def cp(text, size, bold=False, italic=False, space=0, underline=False,
           color=GOLD, align=WD_ALIGN_PARAGRAPH.CENTER):
        p = cell.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_after = Pt(space)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.line_spacing = 1.1
        r = p.add_run(text)
        set_run(r, size=Pt(size), bold=bold, italic=italic, color=color)
        if underline:
            r.underline = True
        return p

    cell.paragraphs[0].text = ''
    cp('', 6, space=0)
    cp('SYLHET INTERNATIONAL UNIVERSITY', 19, bold=True, space=18, color=GOLD)
    cp('A Thesis Report Of', 12, space=6, color=GOLD_DIM)
    cp('\u201c' + TITLE + '\u201d', 15, bold=True, space=20, color=GOLD)
    cp('Supervised By', 12, bold=True, underline=True, space=4, color=GOLD)
    cp(SUPERVISOR, 13, bold=True, space=1, color=GOLD)
    cp(SUPERVISOR_TITLE + ', Department Of CSE,', 11.5, space=0, color=GOLD_DIM)
    cp('Sylhet International University', 11.5, space=18, color=GOLD_DIM)
    cp('Submitted By', 12, bold=True, underline=True, space=8, color=GOLD)

    inner = cell.add_table(rows=1, cols=3)
    inner.autofit = False
    remove_table_borders(inner)
    for j, (name, roll, reg) in enumerate(STUDENTS):
        icell = inner.rows[0].cells[j]
        for text, sz, bd in ((name, 12, True), ('Roll: ' + roll, 11, False),
                             ('Reg: ' + reg, 11, False)):
            p = icell.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(text)
            set_run(r, size=Pt(sz), bold=bd, color=GOLD)
        icell.paragraphs[0].text = ''


def build_title(doc, st):
    first = [True]

    def cp(text, size, bold=False, space=0, underline=False, italic=False):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(space)
        p.paragraph_format.line_spacing = 1.2
        if first[0]:
            p.paragraph_format.page_break_before = True
            first[0] = False
        r = p.add_run(text)
        set_run(r, size=Pt(size), bold=bold, italic=italic)
        if underline:
            r.underline = True

    cp('', 10, space=10)
    cp(TITLE, 17, bold=True, space=26)
    cp('By', 12, space=20)
    for name, roll, reg in STUDENTS:
        cp(name, 13, bold=True, space=2)
        cp('Id: ' + roll, 12, space=16)
    cp('Submitted in partial fulfillment of the requirements', 12, space=2)
    cp('of the degree of Bachelor of Science in Computer Science and Engineering',
       12, space=36)
    cp(DATE, 12, space=40)
    cp('Department of Computer Science and Engineering', 12.5, bold=True, space=2)
    cp('Sylhet International University', 12.5, bold=True, space=0)


def signature_line(cell, width_cm=None):
    p = cell.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(6)
    para_border(p, top=True, sz='6', space='1')
    return p


def build_declaration(doc, st):
    chapter_heading(doc, 'Declaration', page_break_before=False)
    add_para(doc,
             'We the undersigned solemnly declare that the thesis report '
             '\u201c' + TITLE + '\u201d is based on our own work carried out '
             'during the course of our study under the supervision of '
             '\u201c' + SUPERVISOR + '\u201d. We assert the statements made and '
             'conclusions drawn are an outcome of our research work. We further '
             'certify that:')
    items = [
        'I. The work contained in the report is original and has been done by us '
        'under the general supervision of our supervisor.',
        'II. The work has not been submitted to any other institution for any '
        'other degree/diploma/certificate in this university or any other '
        'university of Bangladesh or abroad.',
        'III. We have followed the guidelines provided by the university in '
        'writing the report.',
        'IV. Whenever we have used materials (data, theoretical analysis, and '
        'text) from other sources, we have given due credit to them in the text '
        'of the report and given their details in the references.',
    ]
    for it in items:
        p = add_para(doc, it, space_after=4)
        p.paragraph_format.left_indent = Cm(1.0)
        p.paragraph_format.first_line_indent = Cm(-0.7)

    add_para(doc, '', space_after=10)
    tbl = doc.add_table(rows=2, cols=3)
    tbl.autofit = False
    remove_table_borders(tbl)
    for row in tbl.rows:
        for cell in row.cells:
            cell.width = Cm(CONTENT_WIDTH_CM / 3)
    for j, (name, roll, reg) in enumerate(STUDENTS):
        cell = tbl.rows[0].cells[j]
        cell.paragraphs[0].text = ''
        for _ in range(2):
            p = cell.add_paragraph()
            p.paragraph_format.space_after = Pt(0)
        signature_line(cell)
        for text, sz, bd in ((name, 12, True), ('Roll: ' + roll, 11.5, False),
                             ('Reg: ' + reg, 11.5, False)):
            p = cell.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(0)
            if 'Roll' in text or 'Reg' in text:
                p.paragraph_format.space_after = Pt(0)
            r = p.add_run(text)
            set_run(r, size=Pt(sz), bold=bd)

    for j, (label, lines) in enumerate([
        ('Supervisor',
         [SUPERVISOR, SUPERVISOR_TITLE, 'Department of CSE',
          'Sylhet International University']),
        ('Head of the dept.',
         [HEAD, '[Rank], Head', 'Department of CSE',
          'Sylhet International University']),
    ]):
        cell = tbl.rows[1].cells[j]
        cell.paragraphs[0].text = ''
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(18)
        r = p.add_run(label)
        set_run(r, size=Pt(12), bold=True)
        for _ in range(2):
            q = cell.add_paragraph()
            q.paragraph_format.space_after = Pt(0)
        signature_line(cell)
        for text in lines:
            q = cell.add_paragraph()
            q.alignment = WD_ALIGN_PARAGRAPH.CENTER
            q.paragraph_format.space_after = Pt(0)
            r = q.add_run(text)
            set_run(r, size=Pt(11.5), bold=(text in (SUPERVISOR, HEAD)))


def build_abstract(doc, st):
    chapter_heading(doc, 'Abstract', page_break_before=True)
    add_para(doc,
             'Ransomware produces a large volume of low-level system events, and only '
             'some of the engineered event features separate malicious from benign '
             'activity. A detector therefore needs a compact and justified feature '
             'subset that keeps the recall on the rare ransomware class high while '
             'limiting computation. This thesis studies feature selection for ransomware '
             'detection on RADAR, a recent dataset of Sysmon host events collected from '
             'goodware and ransomware executions. Building on a hybrid voting-based '
             'selector that combines mutual information, the ANOVA F-test, recursive '
             'feature elimination and Pearson correlation, and on a percentage-sweep '
             'selector that ranks features by a combined chi-square, F-test and mutual '
             'information score, the thesis implements three selectors: FS-A (consensus '
             'voting), FS-B (percentage sweep) and FS-C, a proposed voting-ranked sweep '
             'that links the two ideas. The selectors are compared on subset size, '
             'agreement and stability, and the resulting subsets are evaluated with '
             'seven classical classifiers and with an adversarial autoencoder graph '
             'neural network model (A2G-PTH) under a paper-faithful random split and a '
             'leakage-aware group split, with repeated seeds and a computational cost '
             'comparison. The thesis also documents the inconsistencies found in the two '
             'source papers and how each one is resolved.')
    p = add_para(doc, '', space_after=6)


def build_acknowledgment(doc, st):
    chapter_heading(doc, 'Acknowledgment', page_break_before=True)
    add_para(doc,
             'This work would not have been possible without the input and support of '
             'many people over the last year. We would like to express our gratitude to '
             'everyone who contributed to it in some way or other.')
    add_para(doc,
             'First, we would like to thank our academic supervisor, **' + SUPERVISOR +
             '**, for the continuous guidance, the many detailed comments on the '
             'methodology, and the patience during the experimental phase of this '
             'study. We are also thankful to our department head, **' + HEAD + '**, and '
             'to the faculty members of the Department of Computer Science and '
             'Engineering for their advice and encouragement.')
    add_para(doc,
             'We thank the authors of the RADAR dataset for making a realistic '
             'ransomware telemetry dataset publicly available, and the authors of the '
             'two reference papers whose methods this thesis re-implements and '
             'extends. Finally, we owe our families their unconditional love and '
             'immense emotional support throughout our studies.')


def build_toc(doc, st, toc_structure, n_mid=None):
    chapter_heading(doc, 'Table Of Content', page_break_before=True)
    for i, (level, text, key, fixed_page) in enumerate(toc_structure):
        page = fixed_page if fixed_page else st.page_of(key)
        indent = 0.0 if level == 0 else (1.0 if level == 1 else 1.7)
        toc_line(doc, text, page, indent_cm=indent,
                 break_before=(n_mid is not None and i == n_mid))


def build_lof(doc, st, figures):
    chapter_heading(doc, 'List Of Figures', page_break_before=True)
    for item in figures:
        caption = item[0]
        key = item[1] if len(item) > 1 else caption
        toc_line(doc, caption, st.page_of(key))


def build_lot(doc, st, tables):
    chapter_heading(doc, 'List Of Tables', page_break_before=True)
    for item in tables:
        caption = item[0] if isinstance(item, (tuple, list)) else item
        key = item[1] if isinstance(item, (tuple, list)) and len(item) > 1 else caption
        toc_line(doc, caption, st.page_of(key))


def build_front(doc, st, toc_structure, figures, tables):
    build_cover(doc, st)
    page_break(doc)
    build_title(doc, st)
