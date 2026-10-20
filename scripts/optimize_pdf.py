#!/usr/bin/env python3
"""화면용 PDF 압축본 만들기.

사용법:
  python3 scripts/optimize_pdf.py 원본.pdf docs/pdf/jin_teacher.pdf [--dpi 130] [--quality 75]

원본은 건드리지 않고, 이미지 해상도와 화질만 낮춘 복사본을 새로 만듭니다.
인쇄용 PDF에 재단선(트림 박스)이 정의돼 있으면 재단선 바깥 표시를 화면에서 가립니다.
(내용은 지워지지 않고 보이는 영역만 줄어듭니다. 끄려면 --keep-marks)
필요한 것: pip install pymupdf
"""
import argparse, os, sys
import pymupdf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--dpi", type=int, default=130, help="이미지를 이 해상도로 줄임. 이보다 30 넘게 높은 이미지만 대상 (기본 130)")
    ap.add_argument("--quality", type=int, default=75, help="JPEG 화질 1-100 (기본 75)")
    ap.add_argument("--keep-marks", action="store_true", help="재단선 표시를 가리지 않음")
    a = ap.parse_args()
    if os.path.abspath(a.src) == os.path.abspath(a.dst):
        sys.exit("원본과 같은 경로에는 저장할 수 없습니다.")
    doc = pymupdf.open(a.src)
    if not a.keep_marks:
        for page in doc:
            t, m = page.trimbox, page.mediabox
            if t.width < m.width - 1 or t.height < m.height - 1:
                page.set_cropbox(t)
    doc.rewrite_images(dpi_threshold=a.dpi + 30, dpi_target=a.dpi, quality=a.quality)
    os.makedirs(os.path.dirname(os.path.abspath(a.dst)), exist_ok=True)
    doc.save(a.dst, garbage=4, deflate=True)
    before, after = os.path.getsize(a.src), os.path.getsize(a.dst)
    print(f"{os.path.basename(a.src)}: {before/1e6:.1f}MB -> {after/1e6:.1f}MB ({after/before:.0%}), {doc.page_count}쪽")


if __name__ == "__main__":
    main()
