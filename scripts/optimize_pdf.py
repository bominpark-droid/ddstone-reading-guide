#!/usr/bin/env python3
"""화면용 PDF 압축본 만들기.

사용법:
  python3 scripts/optimize_pdf.py 원본.pdf docs/pdf/jin_teacher.pdf [--dpi 130] [--quality 75]

원본은 건드리지 않고, 이미지 해상도와 화질만 낮춘 복사본을 새로 만듭니다.
인쇄용 PDF에 재단선(트림 박스)이 정의돼 있으면 재단선 바깥 표시를 화면에서 가립니다.
(내용은 지워지지 않고 보이는 영역만 줄어듭니다. 끄려면 --keep-marks)
필요한 것: pip install pymupdf pillow
"""
import argparse, io, os, sys
import pymupdf
from PIL import Image

MODE = {1: "L", 3: "RGB", 4: "CMYK"}


def _key(doc, xref, k):
    return doc.xref_get_key(xref, k)[1]


def _samples(doc, xref):
    """이미지 xref 의 픽셀을 색 공간 그대로 (가로, 세로, 성분 수, 바이트) 로 꺼냅니다. 못 꺼내면 None."""
    if _key(doc, xref, "BitsPerComponent") != "8" or _key(doc, xref, "ImageMask") == "true":
        return None
    w, h = int(_key(doc, xref, "Width")), int(_key(doc, xref, "Height"))
    filt = _key(doc, xref, "Filter")
    if filt in ("/FlateDecode", "null", "/LZWDecode"):
        data = doc.xref_stream(xref)
    elif filt == "/DCTDecode":
        img = Image.open(io.BytesIO(doc.xref_stream_raw(xref)))
        img.draft(img.mode, img.size)
        data = img.tobytes()
        if img.mode == "CMYK":  # 저장된 값 그대로 읽힘. 다시 JPEG 로 쓰면 그대로 돌아가므로 표시
            return w, h, 4, data, True
    else:
        return None
    n = len(data) // (w * h) if w * h else 0
    if n < 1 or len(data) != n * w * h:
        return None
    return w, h, n, data, False


def _resize(w, h, n, data, nw, nh, nearest):
    filt = Image.NEAREST if nearest else Image.LANCZOS
    if n in MODE:
        return Image.frombytes(MODE[n], (w, h), data).resize((nw, nh), filt).tobytes()
    out = bytearray(nw * nh * n)
    for i in range(n):
        out[i::n] = Image.frombytes("L", (w, h), data[i::n]).resize((nw, nh), filt).tobytes()
    return bytes(out)


def _store(doc, xref, nw, nh, n, data, jpeg, quality, from_jpeg=False):
    for k in ("DecodeParms", "Filter"):
        doc.xref_set_key(xref, k, "null")
    if jpeg:
        if n == 4 and not from_jpeg:  # Adobe CMYK JPEG 는 반전된 값으로 읽히므로 미리 뒤집어 둠
            data = data.translate(bytes(range(255, -1, -1)))
        b = io.BytesIO()
        Image.frombytes(MODE[n], (nw, nh), data).save(b, "JPEG", quality=quality, optimize=True)
        doc.update_stream(xref, b.getvalue(), compress=False)
        doc.xref_set_key(xref, "Filter", "/DCTDecode")
    else:
        doc.update_stream(xref, data)  # deflate 로 다시 압축됨
    doc.xref_set_key(xref, "Width", str(nw))
    doc.xref_set_key(xref, "Height", str(nh))


def _shrink_bitonal(doc, xref, s):
    """1비트 흑백 이미지(글자, 선, 무늬 마스크)를 줄입니다. 결과도 1비트."""
    w, h = int(_key(doc, xref, "Width")), int(_key(doc, xref, "Height"))
    cs = _key(doc, xref, "ColorSpace")
    if _key(doc, xref, "ImageMask") != "true" and cs not in ("/DeviceGray", "null"):
        return False
    data = doc.xref_stream(xref)
    if not data or len(data) != (w + 7) // 8 * h:
        return False
    nw, nh = max(1, round(w * s)), max(1, round(h * s))
    small = Image.frombytes("1", (w, h), data).convert("L").resize((nw, nh), Image.BOX)
    small = small.point(lambda v: 255 if v >= 128 else 0).convert("1")
    for k in ("DecodeParms", "Filter"):
        doc.xref_set_key(xref, k, "null")
    doc.update_stream(xref, small.tobytes())
    doc.xref_set_key(xref, "Width", str(nw))
    doc.xref_set_key(xref, "Height", str(nh))
    return True


def shrink_images(doc, dpi=130, quality=75, min_bytes=50_000, bitonal_dpi=200):
    """화면에 그려지는 크기에 비해 해상도가 높은 이미지만 dpi 로 줄입니다.

    색 공간 정의(CMYK, ICC, 별색 등)는 건드리지 않고 픽셀 수만 줄입니다.
    pymupdf 의 rewrite_images 는 일부 CMYK JPEG 를 깨뜨려서 쓰지 않습니다 (notes/decisions.md).
    """
    todo = {}
    for page in doc:
        for im in page.get_images(full=True):
            xref = im[0]
            if len(doc.xref_stream_raw(xref) or b"") < min_bytes:
                continue
            rects = [r for r in page.get_image_rects(xref) if r.width > 0]
            if not rects:
                continue
            s = dpi * max(r.width for r in rects) / 72 / im[2]
            s = max(s, dpi * max(r.height for r in rects) / 72 / im[3])
            if xref in todo:
                s = max(s, todo[xref][0])
            todo[xref] = (s, im[5] == "Indexed", im[1], im[4])
    n_done = 0
    for xref, (s, indexed, smask, bpc) in todo.items():
        if bpc == 1:
            s = s * bitonal_dpi / dpi
            if s <= 0.75 and _shrink_bitonal(doc, xref, s):
                n_done += 1
            continue
        if s * (dpi + 30) / dpi > 1:  # 이미 충분히 작음
            continue
        got = _samples(doc, xref)
        if not got:
            continue
        w, h, n, data, from_jpeg = got
        nw, nh = max(1, round(w * s)), max(1, round(h * s))
        small = _resize(w, h, n, data, nw, nh, indexed)
        # JPEG 에서 온 것은 JPEG 로 되돌림. Decode 배열이 있는 Flate 이미지는 값이 바뀌지 않게 Flate 로 둠
        jpeg = not indexed and n in MODE and (from_jpeg or _key(doc, xref, "Decode") == "null")
        _store(doc, xref, nw, nh, n, small, jpeg, quality, from_jpeg)
        n_done += 1
        if smask:
            m = _samples(doc, smask)
            if m and m[2] == 1:  # 못 줄이면 그대로 둠 (SMask 는 크기가 달라도 됨)
                _store(doc, smask, nw, nh, 1, _resize(*m[:4], nw, nh, False), False, quality)
    return n_done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--dpi", type=int, default=130, help="이미지를 이 해상도로 줄임. 이보다 30 넘게 높은 이미지만 대상 (기본 130). 1비트 흑백 이미지는 200")
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
    shrink_images(doc, dpi=a.dpi, quality=a.quality)
    os.makedirs(os.path.dirname(os.path.abspath(a.dst)), exist_ok=True)
    doc.save(a.dst, garbage=4, deflate=True)
    before, after = os.path.getsize(a.src), os.path.getsize(a.dst)
    print(f"{os.path.basename(a.src)}: {before/1e6:.1f}MB -> {after/1e6:.1f}MB ({after/before:.0%}), {doc.page_count}쪽")


if __name__ == "__main__":
    main()
