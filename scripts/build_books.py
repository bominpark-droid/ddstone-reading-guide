#!/usr/bin/env python3
"""드라이브 목록(notes/drive_inventory.json)으로 docs/data/books.json 을 만듭니다.

    python3 scripts/build_books.py

- 학년은 드라이브 폴더 이름을 그대로 씁니다 (유아, 초등 저/중/고학년, 청소년).
- 책 한 권 = 학년 폴더 바로 아래 폴더 하나. 예외(시리즈 나누기, 같은 책 합치기)는 아래 표에 있습니다.
- 화면으로 보기: docs/pdf/<드라이브ID>.pdf 가 있으면 그 줄인 사본, 없으면 드라이브 미리보기.
- 인쇄용 원본 받기, 한글 파일 받기: 드라이브 원본 다운로드 링크.
- 소개 문장, 주제, 미리보기처럼 사람이 확인한 내용은 notes/rich_books.json 에서 가져와 합칩니다.
"""
import json, re
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
inv = json.loads((ROOT / "notes/drive_inventory.json").read_text(encoding="utf-8"))
rich = {b["id"]: b for b in json.loads((ROOT / "notes/rich_books.json").read_text(encoding="utf-8"))["books"]}
pages = json.loads((ROOT / "notes/pdf_pages.json").read_text()) if (ROOT / "notes/pdf_pages.json").exists() else {}

GRADES = [
    ("kid", "유아", "유아", "#f7c9a3"),
    ("low", "초등 저학년", "저학년", "#9fdcb4"),
    ("mid", "초등 중학년", "중학년", "#a9d4ef"),
    ("high", "초등 고학년", "고학년", "#efe08f"),
    ("teen", "청소년", "청소년", "#dcbfe6"),
]
GID = {f"/{label}": gid for gid, label, _, _ in GRADES}
TINT = {gid: tint for gid, _, _, tint in GRADES}

# 표시 제목 고치기 (폴더 이름에 띄어쓰기가 빠진 것). 파일 이름에 띄어 쓴 표기가 있는 것만
TITLE_FIX = {"야호슈퍼의비밀": "야호슈퍼의 비밀", "펭귄의모험": "펭귄의 모험"}
# 기존 시안 3권과 이어 붙일 id
RICH_ID = {"우당탕 마을의 꿈 도둑": "udang", "14살부터 시작하는 나의 첫 진로 수업": "jin", "오늘 내 마음에 어울리는 말": "mind"}

KIND_LABEL = {"teacher": "교사용 지도안", "student": "학생용 활동지", "answer": "정답지", "sheet": "독후 활동지"}
KIND_ORDER = {"teacher": 0, "student": 1, "sheet": 2, "answer": 3, "zip": 4}


def kind_of(name):
    if re.search(r"정답|해답", name): return "answer"
    if "교사용" in name: return "teacher"
    if "학생용" in name: return "student"
    return "sheet"


def variant_of(name):
    m = re.search(r"(\d)단계", name)
    if m: return f"{m.group(1)}단계"
    m = re.search(r"활동(\d)\.", name)
    if m: return f"8차시 퀴즈 활동{m.group(1)}"  # 황룡의 속담 권법 3권
    return ""


def view_url(fid): return f"https://drive.google.com/file/d/{fid}/view"
def dl_url(fid): return f"https://drive.google.com/uc?export=download&id={fid}"
def mb(n): return round(n / 1048576, 1)


def norm(t): return re.sub(r"\s+", "", t)


# 1) 책 단위로 파일 모으기
books = OrderedDict()  # key -> dict


def add_book(key, title, grade, **extra):
    b = books.setdefault(key, {"title": title, "grades": [], "files": [], "series": None, "note": None, "src": []})
    if grade not in b["grades"]: b["grades"].append(grade)
    for k, v in extra.items():
        if v: b[k] = v
    return b


for r in inv:
    if r["kind"] == "folder" or r["path"].startswith("/백업") or not r["path"]:
        continue
    parts = r["path"].split("/")[1:]  # [grade, book, sub...]
    if f"/{parts[0]}" not in GID:
        continue
    gid = GID[f"/{parts[0]}"]
    if r["kind"] not in ("pdf", "x-hwp", "x-zip", "zip"):
        continue  # QR 그림, 메모, pptx 는 싣지 않음
    if len(parts) == 1:  # 학년 폴더 바로 아래 파일 (압축 파일 한 개)
        title = re.sub(r"_독서지도안\.zip$", "", r["name"])
        b = add_book(norm(title), title, gid, note="압축 파일로만 올라와 있어 내용은 아직 확인하지 못했습니다.")
        b["files"].append(dict(r, fmt="zip", grade=gid))
        continue
    folder = parts[1]
    title, note, series = folder, None, None
    if re.search(r"[(_]절판\)?$", folder):
        title = re.sub(r"[(_]절판\)?$", "", folder)
        note = "절판된 책입니다."
    title = TITLE_FIX.get(title, title)
    if folder == "독서지도안_라면소설":
        m = re.match(r"\d\.\s*(.+?)_독서지도안", r["name"])
        title, series = m.group(1), "라면소설"
    if folder == "황룡의 속담 권법 시리즈":
        if len(parts) < 3 or not re.match(r"\d권", parts[2]):
            continue
        title, series = f"황룡의 속담 권법 {parts[2]}", "황룡의 속담 권법 시리즈"
    b = add_book(norm(title), title, gid, note=note, series=series)
    fmt = "pdf" if r["kind"] == "pdf" else "hwp"
    b["files"].append(dict(r, fmt=fmt, grade=gid))

# 2) 파일을 자료 단위(교사용/학생용/정답지/활동지)로 묶기: PDF 와 한글 파일을 한 줄로
gshort = {gid: short for gid, _, short, _ in GRADES}
out = []
for key, b in books.items():
    multi_grade = len(b["grades"]) > 1
    mats = OrderedDict()
    reduced = {}  # 같은 자료의 용량 줄인 PDF
    for f in b["files"]:
        if f["fmt"] == "zip":
            mats[("zip", "", "")] = {"k": "zip", "label": "자료 묶음 (압축 파일)", "zip": {"href": dl_url(f["id"]), "mb": mb(f["size"])}}
            continue
        k = kind_of(f["name"])
        var = variant_of(f["name"])
        g = f["grade"] if multi_grade else ""
        mk = (k, var, g)
        if f["fmt"] == "pdf" and "용량줄인" in f["name"]:
            reduced[mk] = f
            continue
        m = mats.setdefault(mk, {"k": k})
        label = var if var.startswith("8차시") else (var + " " if var else "") + KIND_LABEL[k]
        if g: label = f"{gshort[g]}용 {label}" if g != "kid" else f"유아용 {label}"
        m["label"] = label
        if f["fmt"] == "pdf":
            if "pdf" in m:
                print("WARN 같은 자료에 PDF 가 둘:", b["title"], f["name"])
            local = DOCS / "pdf" / f"{f['id']}.pdf"
            view = f"pdf/{f['id']}.pdf" if local.exists() else None
            m["pdf"] = {"view": view or view_url(f["id"]), "light": bool(view), "href": dl_url(f["id"]), "mb": mb(f["size"])}
            if f["id"] in pages: m["pdf"]["pages"] = pages[f["id"]]
        else:
            if "hwp" in m:
                print("WARN 같은 자료에 한글 파일이 둘:", b["title"], f["name"])
            m["hwp"] = {"href": dl_url(f["id"]), "mb": mb(f["size"]), "ext": f["name"].rsplit(".", 1)[-1]}
    for mk, f in reduced.items():
        if mk in mats and "pdf" in mats[mk]:
            p = mats[mk]["pdf"]
            if not p["light"]:
                local = DOCS / "pdf" / f"{f['id']}.pdf"
                p["view"], p["light"] = (f"pdf/{f['id']}.pdf" if local.exists() else view_url(f["id"])), True
    mats = sorted(mats.values(), key=lambda m: (KIND_ORDER[m["k"]], m["label"]))
    has_pdf = any("pdf" in m for m in mats)
    has_hwp = any("hwp" in m for m in mats)
    kinds = [m["k"] for m in mats]
    short = {"teacher": "교사용", "student": "학생용", "sheet": "활동지", "zip": "압축 파일"}
    info = " · ".join(OrderedDict.fromkeys(short[k] for k in kinds if k != "answer"))
    if has_hwp and not has_pdf:
        info += " · 한글 파일만"
    rid = RICH_ID.get(b["title"])
    book = {
        "id": rid or f"{b['grades'][0]}-{len([x for x in out if x['grades'][0] == b['grades'][0]]) + 1:02d}",
        "title": b["title"],
        "grades": b["grades"],
        "series": b["series"],
        "note": b["note"],
        "tint": TINT[b["grades"][0]],
        "info": info,
        "pdf": has_pdf,
        "hwp": has_hwp,
        "materials": mats,
    }
    if rid:
        r = rich[rid]
        for k in ("authors", "by", "publisher", "guide", "lede", "keywords", "flow", "curri", "previews", "prevLabel", "cover", "tint"):
            if r.get(k): book[k] = r[k]
        if r.get("series") and not book["series"]: book["series"] = r["series"]
        if r.get("note") and not book["note"]: book["note"] = r["note"]
    if "cover" not in book:  # 표지 파일이 없으면 화면용 PDF 첫 장 (make_covers.py 로 만든 그림)
        for m in [m for m in mats if m["k"] != "answer"]:
            v = m.get("pdf", {}).get("view", "")
            img = f"assets/covers/p_{Path(v).stem}.webp"
            if v.startswith("pdf/") and (DOCS / img).exists():
                book["cover"] = {"kind": "sheet", "alt": f"{b['title']} {m['label']} 첫 장", "src": img}
                break
    out.append(book)

# 쓰지 않는 첫 장 그림은 지움 (make_covers.py 가 다시 만들 수 있음)
in_use = {b["cover"]["src"] for b in out if b.get("cover")}
for f in (DOCS / "assets/covers").glob("p_*.webp"):
    if f"assets/covers/{f.name}" not in in_use:
        f.unlink()

data = {
    "version": 3,
    "source": "구글 드라이브 <1)독서지도안> 폴더 (백업 폴더 제외). scripts/build_books.py 로 생성",
    "grades": [{"id": gid, "label": label, "short": short} for gid, label, short, _ in GRADES],
    "topics": [],
    "books": out,
}
(DOCS / "data/books.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
n_pdf = sum(1 for b in out for m in b["materials"] if "pdf" in m)
n_light = sum(1 for b in out for m in b["materials"] if "pdf" in m and m["pdf"]["light"])
print(f"책 {len(out)}권, PDF 자료 {n_pdf}개 중 줄인 사본 {n_light}개, PDF 없는 책 {sum(1 for b in out if not b['pdf'])}권")
