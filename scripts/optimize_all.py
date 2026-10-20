#!/usr/bin/env python3
"""source-pdfs/<드라이브ID>.pdf 를 모두 화면용으로 줄여 docs/pdf/<드라이브ID>.pdf 로 저장합니다.

    python3 scripts/optimize_all.py

이미 만든 파일은 건너뜁니다. 줄여도 작아지지 않으면 원본을 그대로 복사합니다.
쪽수는 notes/pdf_pages.json 에 모아 둡니다 (books.json 만들 때 씀).
"""
import json, shutil, subprocess, sys
from pathlib import Path
import pymupdf

ROOT = Path(__file__).resolve().parent.parent
SRC, DST = ROOT / "source-pdfs", ROOT / "docs" / "pdf"
DST.mkdir(parents=True, exist_ok=True)
pages_f = ROOT / "notes" / "pdf_pages.json"
pages = json.loads(pages_f.read_text()) if pages_f.exists() else {}

for src in sorted(SRC.glob("*.pdf")):
    fid, dst = src.stem, DST / src.name
    if not dst.exists():
        r = subprocess.run([sys.executable, str(ROOT / "scripts/optimize_pdf.py"), str(src), str(dst)], capture_output=True, text=True)
        if r.returncode or not dst.exists():
            print("FAIL", fid, r.stderr[-300:]); continue
        if dst.stat().st_size >= src.stat().st_size:
            shutil.copyfile(src, dst)
        print(f"{fid} {src.stat().st_size/1e6:.1f} -> {dst.stat().st_size/1e6:.1f}MB")
    with pymupdf.open(dst) as d:
        pages[fid] = d.page_count
pages_f.write_text(json.dumps(pages, indent=1))
tot = sum(f.stat().st_size for f in DST.glob("*.pdf"))
print("total", len(list(DST.glob('*.pdf'))), f"{tot/1e6:.0f}MB")
