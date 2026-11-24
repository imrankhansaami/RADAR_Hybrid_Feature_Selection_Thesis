"""Scan the converted PDF and write pagemap.json (printed page numbers of every
ToC heading, figure caption and table caption)."""
import os
import sys
import re
import json

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, 'scripts')
sys.path.insert(0, SCRIPTS)

import pymupdf
import build as B

BUILDDIR = os.path.join(BASE, 'build')
PDF = os.path.join(BUILDDIR, 'thesis.pdf')


def norm(s):
    return re.sub(r'\s+', ' ', s).strip()


def main():
    doc = pymupdf.open(PDF)
    pages = [norm(p.get_text()) for p in doc]
    n_front = 9  # cover + title + 7 front-matter sheets
    print('pdf pages:', len(pages))

    def find(key, start=n_front):
        pattern = re.compile(re.escape(norm(key)), re.IGNORECASE)
        for i in range(start, len(pages)):
            if pattern.search(pages[i]):
                return i - (n_front - 1)
        return None

    pagemap = {}
    missing = []

    for (level, text, key, fixed) in B.TOC_ENTRIES:
        if fixed:
            continue
        page = find(key)
        if page is None:
            missing.append('TOC ' + key)
        else:
            pagemap[key] = page

    for (cap,) in B.FIGURES:
        page = find(cap)
        if page is None:
            missing.append('FIG ' + cap)
        else:
            pagemap[cap] = page

    for cap in B.TABLES:
        page = find(cap)
        if page is None:
            missing.append('TAB ' + cap)
        else:
            pagemap[cap] = page

    with open(os.path.join(BUILDDIR, 'pagemap.json'), 'w', encoding='utf-8') as fh:
        json.dump(pagemap, fh, indent=1, ensure_ascii=False)

    print('pagemap entries:', len(pagemap))
    if missing:
        print('MISSING (%d):' % len(missing))
        for m in missing:
            print('   ', m)
    for k, v in pagemap.items():
        print('%3d  %s' % (v, k))


if __name__ == '__main__':
    main()
