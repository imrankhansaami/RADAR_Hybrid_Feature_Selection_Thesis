import pymupdf
import sys

pdf = sys.argv[1] if len(sys.argv) > 1 else r'thesis\build\thesis.pdf'
doc = pymupdf.open(pdf)
print('pages:', doc.page_count)
for i, page in enumerate(doc):
    t = page.get_text()
    lines = [l.strip() for l in t.split('\n') if l.strip()]
    head = ' | '.join(lines[:4])[:150]
    print(f'{i:3d}: {head}')
