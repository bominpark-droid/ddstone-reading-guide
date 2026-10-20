#!/usr/bin/env python3
"""화면용 PDF(docs/pdf/<드라이브ID>.pdf)의 첫 장으로 카드용 그림을 만듭니다.

    python3 scripts/make_covers.py

결과: docs/assets/covers/p_<드라이브ID>.webp (폭 360px). 이미 있으면 건너뜁니다.
build_books.py 가 표지가 없는 책에 이 그림을 붙입니다 (활동지 첫 장으로 표시).
"""
from pathlib import Path
import io
import pymupdf
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs/assets/covers"
OUT.mkdir(parents=True, exist_ok=True)
n = 0
for pdf in sorted((ROOT / "docs/pdf").glob("*.pdf")):
    dst = OUT / f"p_{pdf.stem}.webp"
    if dst.exists():
        continue
    with pymupdf.open(pdf) as d:
        pg = d[0]
        zoom = 360 / pg.rect.width
        pix = pg.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
    Image.open(io.BytesIO(pix.tobytes("png"))).save(dst, "WEBP", quality=72, method=6)
    n += 1
print(f"새로 만든 그림 {n}개")
