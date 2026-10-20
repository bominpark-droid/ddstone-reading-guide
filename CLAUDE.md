# 독서 지도안 자료실 (뜨인돌 독서 지도안 프로그램)

이 파일은 Claude Code가 가장 먼저 읽는 프로젝트 안내서입니다. 사람이 읽어도 됩니다.
이 저장소는 공개될 수 있으므로, 여기에는 개인정보, 비밀번호, API 키, 거래 조건 같은 내용을 적지 않습니다.

## 한 줄 설명

학회와 행사에서 사서 선생님들께 QR 코드로 보여 줄, 독서 지도안과 독후 활동지(교사용, 학생용 PDF) 모음 웹페이지입니다.
선생님이 폰으로 QR을 찍으면 학년, 주제, 키워드로 책을 찾고 PDF를 바로 열어 볼 수 있습니다.
목표 규모는 약 70권, PDF 약 140개(추정)입니다. 자료는 공개해도 된다고 확인받았습니다.

## 현재 상태 (2026-10-20 기준)

- 책 목록은 구글 드라이브 <1)독서지도안> 폴더(백업 폴더 제외)에서 만듭니다. 2026-10-20 기준 77권(라면소설 3권, 황룡의 속담 권법 4권을 나눠 센 수), PDF 105개(다자구할머니는 원본과 용량줄인버전 2개가 한 자료라서 화면 자료는 104개), 한글 파일 다수.
- 화면으로 보기 = 사이트 안 줄인 사본(docs/pdf/<드라이브ID>.pdf). 인쇄용 원본 받기, 한글 파일 받기 = 드라이브 원본 링크.
- 줄인 사본은 104개 모두 있습니다 (2026-10-20, 사이트 전체 약 186MiB). 환경 네트워크에 drive.google.com, drive.usercontent.google.com 이 허용돼 있어 컨테이너에서 원본을 바로 받을 수 있습니다: `curl -L -o source-pdfs/<ID>.pdf "https://drive.usercontent.google.com/download?id=<ID>&export=download&confirm=t"`
- 학년 탭은 드라이브 폴더 이름 그대로 5개(유아, 초등 저학년, 초등 중학년, 초등 고학년, 청소년). 주제 분류는 근거가 없어 비워 두었고, 비어 있으면 화면에서 주제 줄이 숨겨집니다.
- 소개 문장, 수업 흐름, 미리보기 같은 자세한 정보는 시안 3권(udang, jin, mind)에만 있습니다 (notes/rich_books.json).
- 임시값과 미확인 사항은 notes/open-questions.md를 먼저 읽으세요.

## 구조

```
docs/                 사이트 전체. GitHub Pages가 이 폴더를 그대로 게시합니다. 여기에 있는 것은 전부 공개됩니다.
  index.html          화면 뼈대
  css/style.css       화면 스타일 (색과 글꼴은 :root 변수)
  js/app.js           동작. 데이터를 직접 담지 않고 data/books.json을 읽어 옵니다
  data/books.json     책 목록과 학년, 주제 분류. 책을 추가할 때 고치는 곳은 사실상 여기뿐입니다
  assets/covers/      표지 (webp, 폭 480px)
  assets/previews/    PDF 안쪽 미리보기 (jpg, 폭 460px)
  assets/ui/          상단 일러스트, 아이콘, 책더미, 파비콘
  pdf/                웹용으로 줄인 PDF
notes/                결정 기록, 열린 질문, 목업 이미지. 게시되지 않습니다
scripts/              작업 도구 (PDF 압축, 압축 결과 비교, 표지/미리보기 추출, 데이터 점검, 화면 점검)
source-pdfs/          원본 PDF 임시 보관. git에는 올라가지 않습니다
```

notes/, scripts/, source-pdfs/는 docs/ 밖에 있으므로 사이트에 게시되지 않습니다. 비공개로 두고 싶은 메모는 docs/ 밖에만 두세요.

## 자주 쓰는 명령

```bash
python3 -m http.server 8000 -d docs     # 로컬 확인: http://localhost:8000  (끝에 /?proto 를 붙이면 폰/PC 크기 전환 막대가 보임)
python3 scripts/validate_books.py       # books.json 점검. 책을 고칠 때마다 실행
node scripts/smoke_test.js              # 화면 자동 점검 (서버를 켠 상태에서). playwright 필요
```

fetch로 books.json을 읽기 때문에 index.html을 더블클릭(file://)으로 열면 목록이 나오지 않습니다. 반드시 위 서버로 여세요.

## 책 한 권 추가하는 순서

books.json은 손으로 고치지 않고 스크립트로 다시 만듭니다.

1. 드라이브 목록을 새로 읽어 notes/drive_inventory.json 을 갱신합니다 (2026-10-20에는 사용자 크롬으로 읽음. 형식은 notes/drive_inventory_raw.txt 참고).
2. 새 PDF를 source-pdfs/<드라이브ID>.pdf 로 받습니다 (위의 curl 명령. 드라이브 커넥터로 받았다면 `python3 scripts/ingest_drive_downloads.py <tool-results 폴더>`).
3. `python3 scripts/optimize_all.py` 로 화면용 사본을 만들고 쪽수를 notes/pdf_pages.json 에 모읍니다. 이어서 `python3 scripts/compare_pdfs.py --save` 로 원본과 똑같이 보이는지 쪽마다 확인합니다.
4. `python3 scripts/make_covers.py` 로 카드용 첫 장 그림을 만듭니다. 한글 파일만 있는 책은 한글 파일 안 표지 그림을 notes/hwp_covers.json 에 적고 `python3 scripts/hwp_covers.py` 로 만듭니다.
5. `python3 scripts/build_books.py` 로 docs/data/books.json 을 다시 만듭니다. 제목 고치기, 시리즈 나누기 같은 예외는 이 스크립트 위쪽 표에 있습니다.
6. `python3 scripts/validate_books.py`, 서버를 켜고 `node scripts/smoke_test.js` 로 점검합니다.

## books.json 항목 규칙

최상위는 version, grades({id, label, short}), topics(지금은 빈 목록), books입니다. 책 한 권의 필드:

| 필드 | 설명 |
|---|---|
| id | 영문 소문자, 숫자, -, _. 시안 3권은 udang, jin, mind, 나머지는 <학년id>-<번호> |
| title, grades, series, note, tint, info | 제목, 학년 id 목록, 시리즈, 덧붙임(절판 등), 카드 배경색, 카드 한 줄 |
| pdf, hwp | 이 책에 PDF / 한글 파일이 하나라도 있는지 |
| materials | 자료 목록. {k: teacher·student·sheet·answer·zip, label, pdf:{view, light, href, mb, pages}, hwp:{href, mb, ext}, zip:{href, mb}} |
| cover | 없으면 글자 표지. 있으면 {kind, alt, src} |
| authors, by, publisher, guide, lede, keywords, flow, curri, previews, prevLabel | 시안 3권에만 있는 자세한 정보. 없으면 화면에서 그 칸이 숨겨짐 |

pdf.view 가 pdf/ 로 시작하면 사이트 안 줄인 사본, https 로 시작하면 드라이브 미리보기입니다. href 는 드라이브 원본 다운로드 링크입니다.

## 디자인 규칙

- 기준은 notes/mockup.png입니다. 문구는 목업의 문구를 그대로 씁니다. 임의로 바꾸지 마세요.
- 색: 칠판 #15533d, 제목 바 #1c5e46, 노랑 #feec77, 분홍 #e5256b, 크림 배경 #fbf7ed. 학년 탭은 파스텔 4색(저학년 민트, 고학년 버터, 중학생 하늘, 고등학생 연보라).
- 글꼴: 제목 Jua, 본문 Noto Sans KR, 손글씨 문구 Gaegu 700. 모두 Google Fonts에서 불러옵니다.
- 폰 우선입니다. 360px 너비에서 가로 넘침이 없어야 합니다. 한글이 단어 중간에서 끊기지 않도록 word-break: keep-all을 씁니다.
- 프레임워크, 빌드 과정 없이 일반 HTML, CSS, JS만 씁니다. 누가 열어도 고칠 수 있게 하려는 의도입니다. 이 방침을 바꾸려면 이유를 notes/decisions.md에 남기세요.

## 호스팅 메모

- 후보는 GitHub Pages(공개 저장소 무료, 게시 사이트 1GB 권장)와 Cloudflare Pages(무료, 파일 1개 25MiB 한도). 최종 선택은 PDF 총 용량과 공개 여부로 정합니다. 한도 수치는 작업 시점 확인 값이므로 올리기 전에 공식 문서로 다시 확인하세요.
- GitHub Pages 설정은 Settings, Pages에서 Deploy from a branch, main 브랜치, /docs 폴더를 고르면 됩니다. 모든 경로가 상대 경로라서 <계정>.github.io/<저장소>/ 같은 하위 주소에서도 동작합니다 (점검 완료).
- 상세 화면에는 책별 주소가 없습니다. QR은 첫 화면으로만 연결됩니다.

## 작업 원칙 (사용자 요청)

- 데이터에 근거해 정확하고 냉정하게 판단합니다.
- 모르는 것, 확인 안 된 것은 추측해서 채우지 말고 모른다고 말합니다. 틀린 정보보다 모른다고 하는 쪽이 낫습니다.
- PDF에서 확인되지 않는 사실(학년, 출판사, 저자, 판매 부수 등)을 books.json에 넣지 않습니다. 임시로 넣은 값은 notes/open-questions.md에 반드시 적습니다.
- 한국어로 답하고, 설명의 마지막에는 끝만 읽어도 알 수 있도록 요약을 붙입니다.
- 괄호는 낫표 대신 < > 를 씁니다.
- 변경 후에는 validate_books.py와 smoke_test.js를 돌려 통과 여부를 확인한 뒤 끝났다고 말합니다.
