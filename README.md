# 독서 지도안 자료실

QR 코드를 찍으면 폰에서 바로 열리는, 독서 지도안과 독후 활동지 PDF 모음 웹페이지입니다.
선생님은 학년, 주제, 키워드로 책을 찾고, 교사용 지도안과 학생용 활동지를 받아 볼 수 있습니다.

지금은 책 3권, PDF 5개로 만든 시안입니다. 작업 상황과 임시값은 CLAUDE.md와 notes/open-questions.md에 있습니다.

## 1. 내 컴퓨터에서 보기

```bash
python3 -m http.server 8000 -d docs
```

브라우저에서 http://localhost:8000 을 엽니다.
주소 끝에 `/?proto` 를 붙이면 폰 크기와 PC 크기를 바꿔 볼 수 있는 시안용 막대가 위에 나타납니다.

index.html 파일을 그냥 더블클릭하면 책 목록이 나오지 않습니다. 목록을 별도 파일(data/books.json)에서 읽어 오기 때문이며, 위 명령으로 열어야 합니다.

## 2. 책 추가하기

자세한 순서와 항목 설명은 CLAUDE.md의 <책 한 권 추가하는 순서>와 <books.json 항목 규칙>에 있습니다. 요약하면 다음과 같습니다.

1. 원본 PDF를 `source-pdfs/`에 둡니다 (git에는 올라가지 않음)
2. `scripts/optimize_pdf.py`로 줄여서 `docs/pdf/`에 저장
3. `scripts/make_assets.py`로 표지와 미리보기 이미지 생성
4. `docs/data/books.json`에 책 정보 추가
5. `python3 scripts/validate_books.py`로 점검

필요한 파이썬 패키지는 `pip install -r requirements.txt`로 설치합니다.

## 3. 올리기 (배포)

둘 중 하나를 고릅니다. 둘 다 무료 요금제가 있습니다.

GitHub Pages
1. 이 폴더를 GitHub 저장소로 올립니다. 무료 Pages는 공개 저장소에서 쓸 수 있고, 올린 모든 파일이 공개됩니다.
2. 저장소의 Settings, Pages에서 Source를 <Deploy from a branch>, Branch를 `main`, 폴더를 `/docs`로 저장합니다.
3. 잠시 뒤 `https://<계정>.github.io/<저장소>/` 로 열립니다.

Cloudflare Pages
1. Cloudflare 계정에서 Pages 프로젝트를 만들고 GitHub 저장소를 연결합니다. 비공개 저장소도 연결할 수 있습니다.
2. Build command는 비우고, Build output directory를 `docs`로 정합니다.
3. 파일 하나가 25MiB를 넘으면 올라가지 않습니다 (validate_books.py가 미리 알려 줍니다).

용량과 한도 수치는 올리기 전에 각 서비스의 공식 문서로 다시 확인하세요. 서비스 정책은 바뀔 수 있습니다.

## 4. QR 코드를 만들기 전에

- QR은 인쇄하면 바꾸기 어렵습니다. 최종 주소를 먼저 정하세요. 짧은 주소(자체 도메인 등)를 QR에 넣고 그 주소가 실제 호스팅으로 연결되게 하면, 나중에 호스팅을 옮겨도 QR은 그대로 쓸 수 있습니다.
- 인쇄 전에 실제 폰으로 꼭 열어 보세요. 아이폰 사파리, 갤럭시, 카카오톡 안에서 열리는 화면(인앱 브라우저)은 아직 확인하지 못했습니다.

## 5. 점검

```bash
python3 scripts/validate_books.py                       # 데이터와 파일 점검
python3 -m http.server 8000 -d docs &                   # 서버를 켠 상태에서
node scripts/smoke_test.js                              # 폰/PC 너비에서 화면과 PDF 링크 점검
```

smoke_test.js는 Playwright가 필요합니다. `npm i -D playwright` 후 `npx playwright install chromium`을 한 번 실행하세요.
