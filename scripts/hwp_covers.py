#!/usr/bin/env python3
"""한글 파일만 있는 책의 카드 표지를 한글 파일 안의 그림에서 꺼냅니다.

    python3 scripts/hwp_covers.py

notes/hwp_covers.json 에 적힌 대로 드라이브에서 한글 파일(또는 압축 파일)을 source-pdfs/ 에 받고,
그 안의 그림 하나를 docs/assets/covers/<책id>.webp (폭 480px) 로 저장합니다. 이미 있으면 건너뜁니다.
어떤 그림이 표지인지는 사람이 눈으로 골라 표에 적습니다. build_books.py 가 이 파일을 책 표지로 붙입니다.
필요한 것: pip install olefile pillow
"""
import io, json, subprocess, zipfile, zlib
from pathlib import Path
import olefile
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
CACHE, OUT = ROOT / "source-pdfs", ROOT / "docs/assets/covers"


def fetch(fid, ext):
    f = CACHE / f"{fid}.{ext}"
    if not f.exists():
        url = f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t"
        subprocess.run(["curl", "-sSLf", "--retry", "4", "--retry-all-errors", "-o", str(f), url], check=True)
    return f.read_bytes()


def bin_image(hwp_bytes, name):
    ole = olefile.OleFileIO(io.BytesIO(hwp_bytes))
    raw = ole.openstream(["BinData", name]).read()
    try:
        raw = zlib.decompress(raw, -15)  # 압축 저장된 문서
    except zlib.error:
        pass
    return Image.open(io.BytesIO(raw)).convert("RGB")


def main():
    table = json.loads((ROOT / "notes/hwp_covers.json").read_text(encoding="utf-8"))["books"]
    n = 0
    for bid, p in table.items():
        dst = OUT / f"{bid}.webp"
        if dst.exists():
            continue
        if "image" in p:  # 한글 파일에 표지가 없어 따로 받은 그림
            img = Image.open(ROOT / p["image"]).convert("RGB")
        elif "zip" in p:
            z = zipfile.ZipFile(io.BytesIO(fetch(p["zip"], "zip")))
            names = [i for i in z.infolist() if i.filename.endswith(".hwp")]
            dec = lambda i: i.filename if i.flag_bits & 0x800 else i.filename.encode("cp437").decode("cp949")
            data = z.read(next(i for i in names if p["member"] in dec(i)))
        else:
            data = fetch(p["hwp"], "hwp")
        if "image" not in p:
            img = bin_image(data, p["bin"])
        if "crop" in p:
            img = img.crop(tuple(p["crop"]))
        # 표지 둘레의 흰 여백은 잘라 냄
        box = img.convert("L").point(lambda v: 255 if v < 240 else 0).getbbox()
        if box:
            img = img.crop(box)
        if img.width > 480:
            img = img.resize((480, round(img.height * 480 / img.width)), Image.LANCZOS)
        img.save(dst, "WEBP", quality=80, method=6)
        n += 1
    print(f"새로 만든 표지 {n}개")


if __name__ == "__main__":
    main()
