#!/usr/bin/env python3
"""목업 이미지(notes/mockup.png)에서 임시 일러스트와 아이콘을 잘라 docs/assets/ui 에 저장한다.

이 파일들은 시안용 임시 자리입니다. 원본 일러스트 파일을 받으면 같은 이름으로 덮어쓰면 됩니다.
  hero_strip.webp  상단 배너 아래쪽의 아이들과 책등 그림 (초록 배경 포함)
  stack.webp       하단 왼쪽 책더미 (배경 투명)
  ic_pink / ic_blue / ic_yellow / ic_green.webp  기능 타일 아이콘 4개 (원형, 배경 투명)
좌표는 941x1670 목업 기준입니다. 필요한 것: pip install pillow
"""
import os
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "assets", "ui")
GREEN = (0x15, 0x53, 0x3d)

im = Image.open(os.path.join(ROOT, "notes", "mockup.png")).convert("RGB")
os.makedirs(OUT, exist_ok=True)

# 1) 배너 아래 띠: 제목 강조 표시와 분홍 밑줄이 섞이지 않게 세 조각으로 나눠 초록 바탕에 다시 붙임
X0, X1, Y0, Y1 = 19, 923, 296, 455
w, h = X1 - X0, Y1 - Y0
canvas = Image.new("RGB", (w, h), GREEN)
for x0, x1, y0 in [(19, 292, 300), (283, 652, 331), (646, 923, 298)]:  # 왼쪽 아이, 책등, 오른쪽 아이
    canvas.paste(im.crop((x0, y0, x1, Y1)), (x0 - X0, y0 - Y0))
px = canvas.load()
for y in range(h):
    for x in range(w):
        r, g, b = px[x, y]
        if (x < 34 or x > w - 34) and y > h - 36 and r > 200 and g > 200 and b > 180:
            px[x, y] = GREEN  # 목업 모서리의 크림색 제거
        if x >= 90 and y < (16 if x < 640 else 12) and r > 90:
            px[x, y] = GREEN  # 위쪽 가장자리에 남은 노랑·분홍 잔상 제거
canvas.save(os.path.join(OUT, "hero_strip.webp"), quality=90, method=6)

# 2) 하단 책더미: 크림 배경을 투명으로
s = im.crop((0, 1420, 198, 1670)).convert("RGBA")
for seed in [(2, 2), (190, 2), (100, 2), (2, 60), (190, 60)]:
    ImageDraw.floodfill(s, seed, (0, 0, 0, 0), thresh=14)
s.save(os.path.join(OUT, "stack.webp"), quality=90, method=6)

# 3) 아이콘 4개: 원형으로 오려 냄
for name, cx in [("pink", 139), ("blue", 361), ("yellow", 579), ("green", 802)]:
    c = im.crop((cx - 76, 1220 - 76, cx + 76, 1220 + 76)).convert("RGBA")
    S = 4
    m = Image.new("L", (152 * S, 152 * S), 0)
    ImageDraw.Draw(m).ellipse((2 * S, 2 * S, 150 * S, 150 * S), fill=255)
    c.putalpha(m.resize((152, 152), Image.LANCZOS))
    c.save(os.path.join(OUT, f"ic_{name}.webp"), quality=90, method=6)

print("저장 완료:", ", ".join(sorted(os.listdir(OUT))))
