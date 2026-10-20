/*
 * 화면 점검 스크립트 (자동 클릭 테스트)
 *
 * 사용법
 *   1) 터미널 1:  python3 -m http.server 8000 -d docs
 *   2) 터미널 2:  node scripts/smoke_test.js [주소]        기본 주소는 http://localhost:8000
 *
 * 준비물: npm i -D playwright 후 npx playwright install chromium
 * 클라우드 작업 환경처럼 크로미움 경로가 정해져 있으면 환경변수 CHROMIUM_PATH 로 알려 주세요.
 *
 * 확인하는 것
 *   - 폰 360, 390 / 태블릿 768 / PC 1100 너비에서 가로로 넘치는 부분이 없는지
 *   - books.json 의 책 수만큼 카드가 나오는지
 *   - 검색, 학년 탭, 주제 칩, 상세 화면, 미리보기 확대, 되돌아가기
 *   - 사이트 안의 화면용 PDF 링크가 실제로 열리는지 (200 응답, PDF 형식). 드라이브 링크는 열어 보지 않음
 *   - 같은 사이트 안에서 404 가 나는 요청이 없는지, 자바스크립트 오류가 없는지
 * 실패가 하나라도 있으면 종료 코드 1 로 끝납니다.
 */
let playwright;
try { playwright = require('playwright'); }
catch (e) { playwright = require(process.env.PLAYWRIGHT_MODULE || '/opt/npm-tools/node_modules/playwright'); }
const { chromium } = playwright;

const BASE = (process.argv[2] || 'http://localhost:8000').replace(/\/$/, '');
const WIDTHS = [360, 390, 768, 1100];
let failed = 0;
const btnCount = b => b.materials.reduce((n, m) => n + (m.pdf ? 2 : 0) + (m.hwp ? 1 : 0) + (m.zip ? 1 : 0), 0);
const ok = (cond, msg) => { console.log((cond ? '  통과  ' : '  실패  ') + msg); if (!cond) failed++; };

(async () => {
  const launchOpts = process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH }
    : require('fs').existsSync('/opt/pw-browsers/chromium') ? { executablePath: '/opt/pw-browsers/chromium' } : {};
  const browser = await chromium.launch(launchOpts);
  const data = await (await fetch(BASE + '/data/books.json')).json();
  const books = data.books;
  console.log('책 ' + books.length + '권, 주소 ' + BASE);

  for (const w of WIDTHS) {
    console.log('\n[너비 ' + w + 'px]');
    const ctx = await browser.newContext({ viewport: { width: w, height: 820 } });
    const page = await ctx.newPage();
    const errors = [], bad = [];
    page.on('pageerror', e => errors.push(e.message));
    page.on('console', m => { if (m.type() === 'error' && !/fonts\.g|ERR_(NAME|INTERNET|CONNECTION|TUNNEL)|net::/.test(m.text())) errors.push(m.text()); });
    page.on('response', r => { if (r.url().startsWith(BASE) && r.status() >= 400) bad.push(r.status() + ' ' + r.url()); });

    await page.goto(BASE + '/');
    await page.waitForSelector('.card', { timeout: 5000 });
    const overflow = () => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);

    ok((await page.locator('#grid .card').count()) === books.length, '첫 화면에 카드 ' + books.length + '장');
    ok((await overflow()) <= 0, '첫 화면 가로 넘침 없음');
    ok(await page.locator('#tools').isHidden(), '시안용 도구 막대는 숨김');

    // 검색
    await page.fill('#q', books[1].title.slice(0, 4));
    await page.waitForTimeout(100);
    ok((await page.locator('#grid .card').count()) >= 1, '검색: <' + books[1].title.slice(0, 4) + '> 결과 있음');
    await page.fill('#q', '없는말없는말없는말');
    await page.waitForTimeout(100);
    ok((await page.locator('#grid .card').count()) === 0 && (await page.locator('#grid .empty').count()) === 1, '검색: 결과 없을 때 안내 문구');
    await page.click('#qx');
    ok((await page.locator('#grid .card').count()) === books.length, '검색 지우면 전체로 복귀');

    // 학년 탭
    const grade = data.grades.find(g => books.some(b => b.grades.includes(g.id)));
    await page.click('.gtab[data-g="' + grade.id + '"]');
    const expect = books.filter(b => b.grades.includes(grade.id)).length;
    ok((await page.locator('#grid .card').count()) === expect, '학년 탭 <' + grade.id + '> 선택 시 ' + expect + '권');
    await page.click('.gtab[data-g="' + grade.id + '"]');

    // 상세
    await page.click('#grid .card[data-id="' + books[0].id + '"]');
    await page.waitForTimeout(250);
    ok(await page.locator('#detail').isVisible(), '상세 화면 열림');
    ok((await overflow()) <= 0, '상세 화면 가로 넘침 없음');
    const links = await page.locator('#dAct a[href]').evaluateAll(a => a.map(x => x.getAttribute('href')));
    ok(links.length === btnCount(books[0]), '상세 화면의 자료 버튼 ' + btnCount(books[0]) + '개');
    const pv = page.locator('[data-pv]');
    if (await pv.count()) {
      await pv.first().click();
      await page.waitForTimeout(150);
      ok(await page.locator('#lb').isVisible(), '미리보기 확대 열림');
      await page.click('#lbX');
      await page.waitForTimeout(100);
      ok(await page.locator('#lb').isHidden(), '미리보기 확대 닫힘');
    }
    await page.click('#back');
    await page.waitForTimeout(250);
    ok(await page.locator('#detail').isHidden(), '뒤로 가기로 목록 복귀');

    // 독서 지도안 목록 (파일 바로 받기)
    await page.click('.nav[data-view="guides"]');
    await page.waitForTimeout(150);
    const fl = await page.locator('#flist a[href]').count();
    const fileTotal = books.reduce((n, b) => n + b.materials.length, 0);
    ok(fl === fileTotal, '지도안 목록의 자료 링크 ' + fileTotal + '개');
    ok((await overflow()) <= 0, '지도안 목록 가로 넘침 없음');

    if (w === WIDTHS[0]) {
      // PDF 는 너비마다 반복할 필요가 없어서 한 번만 확인
      let local = 0;
      for (const b of books) for (const m of b.materials) {
        if (!m.pdf || /^https?:/.test(m.pdf.view)) continue;
        const r = await ctx.request.get(BASE + '/' + m.pdf.view);
        const head = (await r.body()).subarray(0, 5).toString();
        if (!(r.status() === 200 && head === '%PDF-')) ok(false, 'PDF 열림 ' + m.pdf.view); else local++;
      }
      ok(local > 0, '사이트 안 화면용 PDF ' + local + '개 모두 열림');
      for (const b of books) {
        const srcs = [...(b.cover ? [b.cover.src] : []), ...(b.previews || []).map(p => p.src)];
        for (const s of srcs) { const r = await ctx.request.get(BASE + '/' + s); if (r.status() !== 200) ok(false, '이미지 없음 ' + s); }
      }
    }
    ok(bad.length === 0, '같은 사이트 안 404 등 오류 요청 없음' + (bad.length ? ' → ' + bad.join(', ') : ''));
    ok(errors.length === 0, '자바스크립트 오류 없음' + (errors.length ? ' → ' + errors.join(' | ') : ''));
    await ctx.close();
  }

  // 시안 도구 막대
  const ctx = await browser.newContext({ viewport: { width: 1100, height: 800 } });
  const p = await ctx.newPage();
  await p.goto(BASE + '/?proto');
  await p.waitForSelector('.card');
  ok(await p.locator('#tools').isVisible(), '?proto 를 붙이면 시안 도구 막대 보임');
  await ctx.close();

  await browser.close();
  console.log('\n' + (failed ? '실패 ' + failed + '건' : '전부 통과'));
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
