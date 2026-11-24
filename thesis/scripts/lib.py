"""Library for building the thesis .docx in the format of the old SIE thesis.

Key features replicated from 'Old thesis-compressed.pdf':
- A4 pages, Times New Roman body, justified text
- Page number in header, top-right, with a rule below it, spanning the text width
- Roman numerals for front matter (starting at v), arabic for body (starting at 1)
- Chapter headings centred bold with a rule above and below
- Figures centred with bold 'Fig x.y: Caption' below
- Tables with 'Table N: Caption' below, grid borders
- Dotted-leader table of content, list of figures and list of tables
"""
import json
import os

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Cm, RGBColor, Emu

FONT = 'Times New Roman'
BODY_SIZE = Pt(12)
TABLE_SIZE = Pt(10)
CAPTION_SIZE = Pt(11)

CONTENT_WIDTH_CM = 16.0  # A4 (21 cm) minus 2.5 cm margins each side


def set_run(run, size=None, bold=None, italic=None, color=None, font=FONT):
    run.font.name = font
    r = run._element
    rPr = r.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.append(rFonts)
    for attr in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'):
        rFonts.set(qn(attr), font)
    if size is not None:
        run.font.size = size
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    if color is not None:
        run.font.color.rgb = color
    return run


def add_field(paragraph, instr, size=None, bold=None):
    run = paragraph.add_run()
    set_run(run, size=size, bold=bold)
    fld1 = OxmlElement('w:fldChar')
    fld1.set(qn('w:fldCharType'), 'begin')
    instr_el = OxmlElement('w:instrText')
    instr_el.set(qn('xml:space'), 'preserve')
    instr_el.text = instr
    fld2 = OxmlElement('w:fldChar')
    fld2.set(qn('w:fldCharType'), 'end')
    run._r.append(fld1)
    run._r.append(instr_el)
    run._r.append(fld2)
    return run


def para_border(paragraph, top=False, bottom=False, sz='6', space='6'):
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = pPr.find(qn('w:pBdr'))
    if pBdr is None:
        pBdr = OxmlElement('w:pBdr')
        pPr.append(pBdr)
    if top:
        b = OxmlElement('w:top')
        b.set(qn('w:val'), 'single')
        b.set(qn('w:sz'), sz)
        b.set(qn('w:space'), space)
        b.set(qn('w:color'), '000000')
        pBdr.append(b)
    if bottom:
        b = OxmlElement('w:bottom')
        b.set(qn('w:val'), 'single')
        b.set(qn('w:sz'), sz)
        b.set(qn('w:space'), space)
        b.set(qn('w:color'), '000000')
        pBdr.append(b)


def add_page_number_header(section, link_previous=False):
    header = section.header
    header.is_linked_to_previous = link_previous
    if link_previous:
        return
    # clear existing paragraphs
    for p in list(header.paragraphs[1:]):
        p._element.getparent().remove(p._element)
    p = header.paragraphs[0]
    p.text = ''
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p.paragraph_format.space_after = Pt(2)
    add_field(p, ' PAGE ', size=Pt(12))
    para_border(p, bottom=True, sz='6', space='3')


def set_page_numbering(section, fmt, start):
    sectPr = section._sectPr
    pgNumType = sectPr.find(qn('w:pgNumType'))
    if pgNumType is None:
        pgNumType = OxmlElement('w:pgNumType')
        sectPr.append(pgNumType)
    pgNumType.set(qn('w:fmt'), fmt)
    pgNumType.set(qn('w:start'), str(start))


def clear_header(section):
    header = section.header
    header.is_linked_to_previous = False
    for p in header.paragraphs:
        p.text = ''


def chapter_heading(doc, text, size=16, space_before=4, space_after=8,
                    page_break_before=False):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.page_break_before = page_break_before
    r = p.add_run(text)
    set_run(r, size=Pt(size), bold=True)
    para_border(p, top=True, bottom=True, sz='6', space='6')
    return p


def h2(doc, text, space_before=10, space_after=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    set_run(r, size=Pt(12.5), bold=True)
    return p


def add_para(doc, text='', justify=True, space_after=7, space_before=0, size=BODY_SIZE,
             first_line_indent=None, keep_with_next=False, italic=False):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_after = Pt(space_after)
    pf.space_before = Pt(space_before)
    pf.line_spacing = 1.15
    pf.keep_with_next = keep_with_next
    if justify:
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if first_line_indent is not None:
        pf.first_line_indent = first_line_indent
    if text:
        add_rich_runs(p, text, size=size, italic=italic)
    return p


def add_rich_runs(p, text, size=BODY_SIZE, italic=False):
    """Supports **bold** inline markup."""
    parts = text.split('**')
    for i, part in enumerate(parts):
        if not part:
            continue
        r = p.add_run(part)
        set_run(r, size=size, bold=(i % 2 == 1), italic=italic)
    return p


def add_bullets(doc, items, space_after=4, size=BODY_SIZE):
    for it in items:
        p = doc.add_paragraph(style='List Bullet')
        pf = p.paragraph_format
        pf.space_after = Pt(space_after)
        pf.line_spacing = 1.15
        pf.left_indent = Cm(0.9)
        pf.first_line_indent = Cm(-0.45)
        add_rich_runs(p, it, size=size)


def add_equation(doc, eq_text, number, size=BODY_SIZE):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(6)
    pf.space_after = Pt(6)
    pf.line_spacing = 1.0
    tabs = pf.tab_stops
    tabs.add_tab_stop(Cm(CONTENT_WIDTH_CM / 2), WD_TAB_ALIGNMENT.CENTER)
    tabs.add_tab_stop(Cm(CONTENT_WIDTH_CM), WD_TAB_ALIGNMENT.RIGHT)
    r = p.add_run('\t' + eq_text + '\t(' + str(number) + ')')
    set_run(r, size=size)
    return p


def add_figure(doc, image_path, caption, width_cm=15.0):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run()
    run.add_picture(image_path, width=Cm(width_cm))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after = Pt(8)
    r = cap.add_run(caption)
    set_run(r, size=CAPTION_SIZE, bold=True)
    return cap


def add_table_caption(doc, caption):
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_before = Pt(2)
    cap.paragraph_format.space_after = Pt(8)
    r = cap.add_run(caption)
    set_run(r, size=CAPTION_SIZE)
    return cap


def _set_cell_text(cell, text, bold=False, size=TABLE_SIZE, align=WD_ALIGN_PARAGRAPH.CENTER):
    cell.text = ''
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.space_before = Pt(0)
    p.alignment = align
    add_rich_runs(p, str(text), size=size)
    for r in p.runs:
        r.bold = bold or r.bold
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER


def _dxa(cm):
    return str(int(cm * 567))


def set_table_grid(table, widths_cm):
    """Force fixed column widths: tblLayout fixed, tblGrid columns and cell tcW."""
    tbl = table._tbl
    tblPr = tbl.tblPr
    layout = tblPr.find(qn('w:tblLayout'))
    if layout is None:
        layout = OxmlElement('w:tblLayout')
        tblPr.append(layout)
    layout.set(qn('w:type'), 'fixed')
    tblW = tblPr.find(qn('w:tblW'))
    if tblW is None:
        tblW = OxmlElement('w:tblW')
        tblPr.append(tblW)
    tblW.set(qn('w:w'), _dxa(sum(widths_cm)))
    tblW.set(qn('w:type'), 'dxa')
    grid = tbl.find(qn('w:tblGrid'))
    if grid is not None:
        tbl.remove(grid)
    grid = OxmlElement('w:tblGrid')
    for w in widths_cm:
        gc = OxmlElement('w:gridCol')
        gc.set(qn('w:w'), _dxa(w))
        grid.append(gc)
    tblPr.addnext(grid)
    for row in table.rows:
        for j, cell in enumerate(row.cells):
            tcPr = cell._tc.get_or_add_tcPr()
            tcW = tcPr.find(qn('w:tcW'))
            if tcW is None:
                tcW = OxmlElement('w:tcW')
                tcPr.append(tcW)
            tcW.set(qn('w:w'), _dxa(widths_cm[j]))
            tcW.set(qn('w:type'), 'dxa')


def repeat_header_rows(table, n_header_rows=1):
    for row in table.rows[:n_header_rows]:
        trPr = row._tr.get_or_add_trPr()
        tblHeader = OxmlElement('w:tblHeader')
        tblHeader.set(qn('w:val'), 'true')
        trPr.append(tblHeader)


def no_row_split(table):
    for row in table.rows:
        trPr = row._tr.get_or_add_trPr()
        cantSplit = OxmlElement('w:cantSplit')
        trPr.append(cantSplit)


def add_table(doc, header_rows, body_rows, col_widths_cm=None, caption=None,
              size=TABLE_SIZE, align_body=WD_ALIGN_PARAGRAPH.CENTER):
    if isinstance(align_body, str):
        align_body = {'left': WD_ALIGN_PARAGRAPH.LEFT,
                      'center': WD_ALIGN_PARAGRAPH.CENTER,
                      'right': WD_ALIGN_PARAGRAPH.RIGHT}[align_body.lower()]
    n_cols = len(header_rows[0]) if header_rows else len(body_rows[0])
    table = doc.add_table(rows=0, cols=n_cols)
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    for hr in header_rows:
        row = table.add_row()
        for j, val in enumerate(hr):
            _set_cell_text(row.cells[j], val, bold=True, size=size)
    for br in body_rows:
        row = table.add_row()
        for j, val in enumerate(br):
            _set_cell_text(row.cells[j], val, bold=False, size=size, align=align_body)
    if col_widths_cm:
        set_table_grid(table, col_widths_cm)
    repeat_header_rows(table, len(header_rows))
    no_row_split(table)
    if caption:
        add_table_caption(doc, caption)
    return table


def page_break(doc):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run()
    run.add_break(WD_BREAK.PAGE)
    return p


def shade_cell(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hexcolor)
    tcPr.append(shd)


def set_row_height(row, cm, rule='atLeast'):
    trPr = row._tr.get_or_add_trPr()
    trHeight = OxmlElement('w:trHeight')
    trHeight.set(qn('w:val'), str(int(cm * 567)))
    trHeight.set(qn('w:hRule'), rule)
    trPr.append(trHeight)


def remove_table_borders(table):
    tbl = table._tbl
    tblPr = tbl.tblPr
    borders = OxmlElement('w:tblBorders')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        el = OxmlElement('w:' + edge)
        el.set(qn('w:val'), 'none')
        el.set(qn('w:sz'), '0')
        borders.append(el)
    tblPr.append(borders)


def toc_line(doc, text, page, indent_cm=0.0, bold=False, size=BODY_SIZE,
             break_before=False):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_after = Pt(2)
    pf.space_before = Pt(0)
    pf.line_spacing = 1.0
    pf.left_indent = Cm(indent_cm)
    if break_before:
        pf.page_break_before = True
    tabs = pf.tab_stops
    tabs.add_tab_stop(Cm(CONTENT_WIDTH_CM), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
    r = p.add_run(text)
    set_run(r, size=size, bold=bold)
    r2 = p.add_run('\t' + str(page))
    set_run(r2, size=size, bold=bold)
    return p


def setup_document():
    doc = Document()
    # base style
    style = doc.styles['Normal']
    style.font.name = FONT
    style.font.size = BODY_SIZE
    rpr = style.element.get_or_add_rPr()
    rFonts = rpr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rpr.append(rFonts)
    for attr in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'):
        rFonts.set(qn(attr), FONT)
    pf = style.paragraph_format
    pf.space_after = Pt(6)
    pf.line_spacing = 1.12

    sec = doc.sections[0]
    sec.page_width = Cm(21.0)
    sec.page_height = Cm(29.7)
    sec.left_margin = Cm(2.5)
    sec.right_margin = Cm(2.5)
    sec.top_margin = Cm(2.2)
    sec.bottom_margin = Cm(2.2)
    sec.header_distance = Cm(1.0)
    sec.footer_distance = Cm(1.0)
    return doc


def add_section(doc):
    sec = doc.add_section(WD_SECTION.NEW_PAGE)
    sec.page_width = Cm(21.0)
    sec.page_height = Cm(29.7)
    sec.left_margin = Cm(2.5)
    sec.right_margin = Cm(2.5)
    sec.top_margin = Cm(2.2)
    sec.bottom_margin = Cm(2.2)
    sec.header_distance = Cm(1.0)
    sec.footer_distance = Cm(1.0)
    return sec


class BuildState:
    """Collects ToC entries, figure and table captions while building."""

    def __init__(self, pagemap=None, out_dir='.'):
        self.pagemap = pagemap or {}
        self.out_dir = out_dir
        self.toc_entries = []   # (level, text, key)
        self.figures = []       # (caption, key)
        self.tables = []        # (caption, key)
        self.eq_count = 0

    def page_of(self, key):
        return self.pagemap.get(key, '')

    def add_toc(self, level, text, key=None):
        self.toc_entries.append((level, text, key or text))

    def add_fig(self, caption, key):
        self.figures.append((caption, key))

    def add_tbl(self, caption, key):
        self.tables.append((caption, key))

    def next_eq(self):
        self.eq_count += 1
        return self.eq_count
