#!/usr/bin/env python3
"""PDF에서 표지와 활동지 미리보기 이미지를 만든다.

표지 (PDF 1쪽에 들어 있는 가장 큰 그림을 꺼냄. 투명 배경이 있으면 유지):
  python3 scripts/make_assets.py cover --id jin --pdf 학생용.pdf [--page 1]

활동지 미리보기 (지정한 쪽을 그림으로 저장. 재단선이 있으면 가림):
  python3 scripts/make_assets.py previews --id jin --pdf 학생용.pdf --pages 4,16,19

결과는 docs/assets/covers/<id>.webp, docs/assets/previews/<id>_pNN.jpg 에 저장됩니다.
필요한 것: pip install pymupdf pillow
"""
import argparse, io, os, sys
import pymupdf
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COVERS = os.path.join(ROOT, "docs", "assets", "covers")
PREVIEWS = os.path.join(ROOT, "docs", "assets", "previews")


def to_pil(pix):
    if pix.colorspace is not None and pix.colorspace.n == 4 and not pix.alpha:
        pix = pymupdf.Pixmap(pymupdf.csRGB, pix)  # CMYK -> RGB
    return Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGBA")


def cover(args):
    doc = pymupdf.open(args.pdf)
    page = doc[args.page - 1]
    best = None
    for info in page.get_images(full=True):
        xref, smask = info[0], info[1]
        w, h = info[2], info[3]
        if smask == 0 and w * h < 200_000:  # 작은 장식이나 마스크용 그림은 제외
            continue
        if best is None or w * h > best[1] * best[2]:
            best = (xref, w, h, smask)
    if best is None:
        sys.exit("1쪽에서 표지로 쓸 그림을 찾지 못했습니다. 이 책은 수동으로 표지를 넣어야 합니다.")
    xref, _, _, smask = best
    base = pymupdf.Pixmap(doc, xref)
    if smask:
        base = pymupdf.Pixmap(base, pymupdf.Pixmap(doc, smask))
    im = to_pil(base)
    bbox = im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    if bbox:
        im = im.crop(bbox)
    im = im.resize((args.width, round(im.height * args.width / im.width)), Image.LANCZOS)
    os.makedirs(COVERS, exist_ok=True)
    out = os.path.join(COVERS, f"{args.id}.webp")
    im.save(out, quality=82, method=6)
    print(f"저장: {os.path.relpath(out, ROOT)} ({im.width}x{im.height}, {os.path.getsize(out)//1024}KB)")


def previews(args):
    doc = pymupdf.open(args.pdf)
    os.makedirs(PREVIEWS, exist_ok=True)
    for n in [int(x) for x in args.pages.split(",")]:
        page = doc[n - 1]
        t, m = page.trimbox, page.mediabox
        if t.width < m.width - 1 or t.height < m.height - 1:
            page.set_cropbox(t)
        zoom = args.width / page.rect.width
        pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
        im = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
        out = os.path.join(PREVIEWS, f"{args.id}_p{n:02d}.jpg")
        im.save(out, quality=72, optimize=True)
        print(f"저장: {os.path.relpath(out, ROOT)} ({im.width}x{im.height}, {os.path.getsize(out)//1024}KB)")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("cover")
    c.add_argument("--id", required=True)
    c.add_argument("--pdf", required=True)
    c.add_argument("--page", type=int, default=1)
    c.add_argument("--width", type=int, default=480)
    c.set_defaults(fn=cover)
    p = sub.add_parser("previews")
    p.add_argument("--id", required=True)
    p.add_argument("--pdf", required=True)
    p.add_argument("--pages", required=True, help="예: 4,16,19")
    p.add_argument("--width", type=int, default=460)
    p.set_defaults(fn=previews)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
