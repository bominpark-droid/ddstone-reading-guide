#!/usr/bin/env python3
"""드라이브 커넥터로 받은 결과(JSON, base64)를 source-pdfs/<파일ID>.pdf 로 풀어 놓습니다.

    python3 scripts/ingest_drive_downloads.py <tool-results 폴더>

풀어낸 결과 파일은 지워서 디스크를 아낍니다. 원본 드라이브 파일은 건드리지 않습니다.
"""
import base64, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "source-pdfs"
OUT.mkdir(exist_ok=True)
inv = {r["id"]: r for r in json.loads((ROOT / "notes/drive_inventory.json").read_text(encoding="utf-8"))}

for f in sorted(Path(sys.argv[1]).glob("mcp-Google_Drive-download_file_content-*.txt")):
    try:
        d = json.loads(f.read_text())
    except Exception as e:
        print("SKIP", f.name, e); continue
    fid = d.get("id")
    data = base64.b64decode(d["content"])
    want = inv.get(fid, {}).get("size")
    ok = data[:5] == b"%PDF-" and (want is None or len(data) == want)
    dest = OUT / f"{fid}.pdf"
    if ok:
        dest.write_bytes(data); f.unlink()
        print("OK  ", fid, len(data), d.get("title"))
    else:
        print("BAD ", fid, len(data), want, d.get("title"))
