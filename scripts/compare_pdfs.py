#!/usr/bin/env python3
"""줄인 화면용 사본이 원본과 똑같이 보이는지 쪽마다 비교합니다.

    python3 scripts/compare_pdfs.py            # source-pdfs/ 와 docs/pdf/ 에 둘 다 있는 파일 전부
    python3 scripts/compare_pdfs.py <드라이브ID> ...

두 파일을 낮은 해상도로 그려서 픽셀 차이(0~255 평균)를 봅니다. 압축으로 생기는 차이는 보통 3 아래입니다.
기준(--limit, 기본 6)을 넘는 쪽이 있으면 파일과 쪽 번호를 출력하고 종료 코드 1을 돌려줍니다.
그림이 깨졌는지 눈으로 보려면 --save 를 붙이면 notes/compare/ 에 나란히 놓은 그림이 저장됩니다 (git 에는 안 올림).
"""
import argparse, sys
from pathlib import Path
import pymupdf
from PIL import Image, ImageChops, ImageStat

ROOT = Path(__file__).resolve().parent.parent


def render(page, size=None):
    pix = page.get_pixmap(dpi=40)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    return img.resize(size) if size and img.size != size else img


def compare(src, dst):
    """쪽마다 (차이, 원본 그림, 사본 그림) 목록"""
    out = []
    with pymupdf.open(src) as a, pymupdf.open(dst) as b:
        if a.page_count != b.page_count:
            return None
        for pa, pb in zip(a, b):
            if pa.rect != pb.rect:  # 사본은 재단선 바깥을 가렸음
                pa.set_cropbox(pb.cropbox)
            ib = render(pb)
            ia = render(pa, ib.size)
            out.append((max(ImageStat.Stat(ImageChops.difference(ia, ib)).mean), ia, ib))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--limit", type=float, default=6)
    ap.add_argument("--save", action="store_true")
    a = ap.parse_args()
    ids = a.ids or sorted(p.stem for p in (ROOT / "docs/pdf").glob("*.pdf") if (ROOT / "source-pdfs" / p.name).exists())
    bad = 0
    for fid in ids:
        res = compare(ROOT / "source-pdfs" / f"{fid}.pdf", ROOT / "docs/pdf" / f"{fid}.pdf")
        if res is None:
            print(f"FAIL {fid}: 쪽수가 다름"); bad += 1; continue
        worst = [(i + 1, d) for i, (d, _, _) in enumerate(res) if d > a.limit]
        if worst:
            bad += 1
            print(f"FAIL {fid}: " + ", ".join(f"{p}쪽 {d:.0f}" for p, d in worst))
            if a.save:
                (ROOT / "notes/compare").mkdir(exist_ok=True)
                for p, _ in worst:
                    _, ia, ib = res[p - 1]
                    c = Image.new("RGB", (ia.width * 2 + 8, ia.height), "red")
                    c.paste(ia); c.paste(ib, (ia.width + 8, 0))
                    c.save(ROOT / f"notes/compare/{fid}_p{p}.png")
    print(f"비교 {len(ids)}개, 문제 {bad}개")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
