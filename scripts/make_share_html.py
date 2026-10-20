"""docs/ 사이트를 더블클릭으로 열리는 HTML 한 파일로 묶는다.
usage: bundle.py <docs_dir> <out.html> [--with-pdf]"""
import base64, json, mimetypes, re, sys
from pathlib import Path

docs = Path(sys.argv[1]); out = Path(sys.argv[2]); with_pdf = "--with-pdf" in sys.argv
mimetypes.add_type("image/webp", ".webp")

def data_uri(rel):
    p = docs / rel
    mt = mimetypes.guess_type(p.name)[0]
    return f"data:{mt};base64,{base64.b64encode(p.read_bytes()).decode()}"

html = (docs / "index.html").read_text(encoding="utf-8")
css = (docs / "css/style.css").read_text(encoding="utf-8")
js = (docs / "js/app.js").read_text(encoding="utf-8")
data = json.loads((docs / "data/books.json").read_text(encoding="utf-8"))

# 이미지 경로를 data URI로
for b in data["books"]:
    b["cover"]["src"] = data_uri(b["cover"]["src"])
    for pv in b["previews"]:
        pv["src"] = data_uri(pv["src"])
html = re.sub(r'(src|href)="(assets/[^"]+)"', lambda m: f'{m.group(1)}="{data_uri(m.group(2))}"', html)
html = html.replace('<link rel="stylesheet" href="css/style.css">', "<style>\n" + css + "\n</style>")

# books.json fetch 대신 내장 데이터
fetch_old = "fetch('data/books.json')\n  .then(r=>{if(!r.ok)throw new Error(r.status);return r.json()})"
assert fetch_old in js
js = js.replace(fetch_old, "Promise.resolve(window.__BOOKS__)")

pdfs = {}
if with_pdf:
    for b in data["books"]:
        for f in b["files"]:
            pdfs[f["href"]] = base64.b64encode((docs / f["href"]).read_bytes()).decode()

shim = """
(function(){
  var PDF=window.__PDF__||{}, made={};
  document.addEventListener('click',function(e){
    var a=e.target.closest&&e.target.closest('a[href]');
    if(!a)return;
    var key=a.dataset.pdf||a.getAttribute('href');
    if(!/^pdf\\//.test(key))return;
    a.dataset.pdf=key;
    if(!PDF[key]){e.preventDefault();toast('공유용 데모에는 PDF 파일이 빠져 있어요. 미리보기 이미지로 확인해 주세요.');return}
    if(!made[key]){
      var s=atob(PDF[key]),u=new Uint8Array(s.length);
      for(var i=0;i<s.length;i++)u[i]=s.charCodeAt(i);
      made[key]=URL.createObjectURL(new Blob([u],{type:'application/pdf'}));
    }
    a.href=made[key];
  },true);
})();
"""
inline = ("<script>window.__BOOKS__=" + json.dumps(data, ensure_ascii=False) + ";</script>\n"
          + "<script>window.__PDF__=" + json.dumps(pdfs) + ";</script>\n"
          + "<script>\n" + js + "\n" + shim + "</script>")
assert '<script src="js/app.js"></script>' in html
html = html.replace('<script src="js/app.js"></script>', inline)
html = html.replace("<title>독서 지도안 자료실</title>", "<title>독서 지도안 자료실 (공유용 데모)</title>")
out.write_text(html, encoding="utf-8")
print(out, f"{out.stat().st_size/1e6:.1f}MB")
