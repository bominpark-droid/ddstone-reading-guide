#!/usr/bin/env python3
"""books.json 점검 도구.

books.json 은 scripts/build_books.py 가 만듭니다. 만든 뒤, 올리기 전에 꼭 돌려 보세요.

    python3 scripts/validate_books.py

확인하는 것
  - 필수 항목이 빠지지 않았는지, id 가 겹치지 않는지, 학년 id 가 목록에 있는 값인지
  - 자료(materials)마다 화면용 PDF, 원본 받기, 한글 파일 중 하나 이상이 있는지
  - 사이트 안 화면용 PDF, 표지, 미리보기 파일이 실제로 docs/ 안에 있는지 (PDF 형식, 쪽수)
  - 드라이브 링크가 drive.google.com 주소인지 (실제로 열리는지는 확인하지 않음)
  - 화면용 PDF 한 개가 너무 크지 않은지, 사이트 전체 용량
  - 어디에도 연결되지 않은 파일(고아 파일)이 없는지

오류(ERROR)가 있으면 종료 코드 1, 경고(WARN)만 있으면 0 으로 끝납니다.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
DATA = DOCS / "data" / "books.json"

GH_SITE_LIMIT = 1024 * 1024 * 1024        # GitHub Pages: 게시 사이트 1 GB (권장 한도)
GH_FILE_LIMIT = 100 * 1024 * 1024         # GitHub: 파일 1개 100 MB 넘으면 올라가지 않음
WARN_PDF = 8 * 1024 * 1024                # 화면용 PDF 가 이보다 크면 폰에서 느려서 경고
KINDS = {"teacher", "student", "sheet", "answer", "zip"}
DRIVE = re.compile(r"^https://drive\.google\.com/(file/d/[\w-]+/view|uc\?export=download&id=[\w-]+)$")

errors, warns = [], []
err, warn = errors.append, warns.append


def is_str(v):
    return isinstance(v, str) and v.strip() != ""


def local_file(rel, where):
    if not is_str(rel) or rel.startswith("/") or ".." in rel.split("/"):
        err(f"{where}: docs/ 안의 상대 경로여야 해요 → {rel}")
        return None
    p = DOCS / rel
    if not p.is_file():
        err(f"{where}: 파일이 없어요 → docs/{rel}")
        return None
    return p


def drive_link(url, where):
    if not (is_str(url) and DRIVE.match(url)):
        err(f"{where}: 드라이브 링크 형식이 아니에요 → {url}")


def main():
    try:
        data = json.loads(DATA.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"ERROR: books.json 을 읽을 수 없어요 → {e}")
        return 1
    grade_ids = {g["id"] for g in data.get("grades", [])}
    if not grade_ids:
        err("grades 가 비어 있어요")
    used = set()
    ids = set()
    try:
        import pymupdf  # type: ignore
    except ImportError:
        pymupdf = None
        warn("pymupdf 가 없어서 PDF 쪽수 확인을 건너뛰었어요 (pip install pymupdf)")

    for n, b in enumerate(data.get("books", []), 1):
        tag = f"책 {n} <{b.get('id', '?')}>"
        bid = b.get("id")
        if not (is_str(bid) and re.fullmatch(r"[a-z0-9][a-z0-9_-]*", bid)):
            err(f"{tag}: id 는 영문 소문자, 숫자, -, _ 만 쓸 수 있어요")
        elif bid in ids:
            err(f"{tag}: id 가 겹쳐요")
        ids.add(bid)
        for k in ("title", "info", "tint"):
            if not is_str(b.get(k)):
                err(f"{tag}: <{k}> 가 비어 있어요")
        if not b.get("grades") or any(g not in grade_ids for g in b["grades"]):
            err(f"{tag}: 학년이 비었거나 없는 학년 id 가 있어요 → {b.get('grades')}")
        mats = b.get("materials")
        if not mats:
            err(f"{tag}: 자료(materials)가 없어요")
            continue
        for i, m in enumerate(mats):
            w = f"{tag} {m.get('label', i)}"
            if m.get("k") not in KINDS or not is_str(m.get("label")):
                err(f"{w}: k 와 label 이 필요해요")
            if not any(x in m for x in ("pdf", "hwp", "zip")):
                err(f"{w}: 받을 파일이 하나도 없어요")
            if "pdf" in m:
                p = m["pdf"]
                drive_link(p.get("href"), w + " 원본")
                if p.get("view", "").startswith("http"):
                    drive_link(p["view"], w + " 화면")
                    warn(f"{w}: 줄인 사본이 없어 드라이브 미리보기로 연결돼요")
                else:
                    f = local_file(p.get("view"), w + " 화면")
                    if f:
                        used.add(f.resolve())
                        if f.read_bytes()[:5] != b"%PDF-":
                            err(f"{w}: PDF 형식이 아니에요 → {f.name}")
                        if f.stat().st_size > WARN_PDF:
                            warn(f"{w}: 화면용 PDF 가 {f.stat().st_size/1048576:.1f}MiB 로 커요")
                        if pymupdf and p.get("pages"):
                            with pymupdf.open(f) as d:
                                if d.page_count != p["pages"]:
                                    err(f"{w}: 쪽수 {p['pages']} 와 실제 {d.page_count} 가 달라요")
            for k in ("hwp", "zip"):
                if k in m:
                    drive_link(m[k].get("href"), f"{w} {k}")
        c = b.get("cover")
        if c:
            f = local_file(c.get("src"), tag + " 표지")
            if f:
                used.add(f.resolve())
        for i, pv in enumerate(b.get("previews") or []):
            f = local_file(pv.get("src"), f"{tag} 미리보기 {i}")
            if f:
                used.add(f.resolve())

    for folder in ("pdf", "assets/covers", "assets/previews"):
        for f in sorted((DOCS / folder).glob("*")):
            if f.is_file() and f.resolve() not in used:
                warn(f"어디에도 연결되지 않은 파일 → docs/{folder}/{f.name}")
    for f in DOCS.rglob("*"):
        if f.is_file() and f.stat().st_size > GH_FILE_LIMIT:
            err(f"GitHub 파일 한도(100MB)를 넘어요 → {f}")

    site = sum(f.stat().st_size for f in DOCS.rglob("*") if f.is_file())
    books = data.get("books", [])
    print(f"책 {len(books)}권 · 사이트 안 PDF {len([u for u in used if u.suffix == '.pdf'])}개 · 사이트 전체 {site/1048576:.1f}MiB "
          f"(GitHub Pages 권장 한도 1GB 의 {site*100/GH_SITE_LIMIT:.1f}%)")
    if site > GH_SITE_LIMIT * 0.8:
        warn("사이트 전체 용량이 GitHub Pages 한도(1GB)의 80% 를 넘었어요")
    for w in warns:
        print("WARN  ", w)
    for e in errors:
        print("ERROR ", e)
    print(f"\n오류 {len(errors)}건, 경고 {len(warns)}건")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
