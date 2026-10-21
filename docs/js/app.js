/* 독서 지도안 자료실 - 동작
   데이터는 data/books.json 에서 읽어 옵니다. 책을 추가할 때는 이 파일이 아니라 books.json 을 고칩니다. */
let GRADES=[],TOPICS=[],BOOKS=[];

const $=s=>document.querySelector(s);
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const IC={
  teacher:'<svg class="i" viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4v2h6V4M9 13l2 2 4-4"/></svg>',
  student:'<svg class="i" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 20l1-4L16 5l3 3L8 19l-4 1zM14 7l3 3"/></svg>',
  sheet:'<svg class="i" viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 9h6M9 13h6M9 17h4"/></svg>',
  x:'<svg class="i" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>',
  eye:'<svg class="i" viewBox="0 0 24 24" aria-hidden="true"><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg>',
  print:'<svg class="i" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 9V3h10v6M7 17H4v-7h16v7h-3M7 14h10v7H7z"/></svg>',
  down:'<svg class="i" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4v11M7 10l5 5 5-5M5 20h14"/></svg>'
};
IC.answer=IC.teacher;IC.zip=IC.sheet;
const FK={teacher:['ft','교사용'],student:['fs','학생용'],sheet:['fa','활동지'],answer:['ft','정답지'],zip:['fa','압축 파일']};
const state={g:null,t:null,q:'',view:'find'};

/* 새 탭으로 여는 링크. 드라이브 원본 받기는 download 힌트를 붙임 */
function link(href,cls,inner){
  return '<a class="'+cls+'" href="'+esc(href)+'" target="_blank" rel="noopener">'+inner+'</a>';
}
/* 자료 한 줄에서 가장 먼저 열 링크: 화면용 PDF, 없으면 한글 파일 */
function quickHref(m){return m.pdf?m.pdf.view:m.hwp?m.hwp.href:m.zip.href}
function mbTxt(x){return x<1?'1MB 미만':x.toFixed(x<10?1:0)+'MB'}
function gradeOf(id){return GRADES.find(g=>g.id===id)}
function passes(b,s){
  if(s.g && !b.grades.includes(s.g)) return false;
  if(s.t && !b.topics.includes(s.t)) return false;
  if(s.q){
    const toks=s.q.toLowerCase().split(/\s+/).filter(Boolean);
    if(!toks.every(t=>b.hay.includes(t))) return false;
  }
  return true;
}
function gtag(b){
  if(!b.grades.length) return '<span class="tag g-none">학년 미정</span>';
  return b.grades.map(id=>'<span class="tag g-'+id+'">'+gradeOf(id).label+'</span>').join('');
}
function coverHtml(b,big){
  const c=b.cover;
  if(!c) return '<span class="fb"><b>'+esc(b.title)+'</b><span>'+esc(b.series||'뜨인돌 독서 지도안')+'</span></span>';
  return (c.flag&&!big?'<span class="flag">'+esc(c.flag)+'</span>':'')+'<img class="'+c.kind+'" src="'+esc(c.src)+'" alt="'+esc(c.alt)+'">';
}

function renderTabs(){
  $('#tabs').innerHTML=GRADES.map(g=>{
    const n=BOOKS.filter(b=>b.grades.includes(g.id)).length;
    return '<button type="button" class="gtab g-'+g.id+'" data-g="'+g.id+'" data-n="'+n+'" aria-pressed="'+(state.g===g.id)+'" aria-label="'+g.label+' '+n+'권"><span class="gn"><span class="gl">'+g.label+'</span><span class="gs">'+(g.short||g.label)+'</span></span><span class="gc">'+n+'권</span></button>';
  }).join('');
}
function renderTopics(){
  document.querySelector('.topics').hidden=!TOPICS.length;
  $('#topics').innerHTML=TOPICS.map(t=>{
    const total=BOOKS.filter(b=>b.topics.includes(t.id)).length;
    const hit=BOOKS.filter(b=>passes(b,{...state,t:t.id})).length;
    return '<button type="button" class="chip'+(hit===0&&state.t!==t.id?' dim':'')+'" data-t="'+t.id+'" aria-pressed="'+(state.t===t.id)+'">'+t.label+' <span class="c">'+total+'</span></button>';
  }).join('');
}
function renderList(){
  const list=BOOKS.filter(b=>passes(b,state));
  const tags=[];
  if(state.g) tags.push(['g','학년 '+gradeOf(state.g).label]);
  if(state.t) tags.push(['t',TOPICS.find(t=>t.id===state.t).label]);
  if(state.q) tags.push(['q','검색 '+state.q]);
  const hidden=state.g?BOOKS.filter(b=>!b.grades.length&&passes(b,{...state,g:null})).length:0;
  $('#rbar').innerHTML='<span class="cnt">도서 '+list.length+'권</span>'
    +tags.map(t=>'<span class="tagx">'+esc(t[1])+'<button type="button" data-clear="'+t[0]+'" aria-label="'+esc(t[1])+' 해제">'+IC.x+'</button></span>').join('')
    +(tags.length?'<button type="button" class="reset" data-clear="all">전체 보기</button>':'')
    +(hidden?'<span class="note">학년이 정해지지 않은 자료 '+hidden+'권은 전체 보기에서 볼 수 있어요.</span>':'');
  const empty='<li class="empty"><h3>맞는 자료가 아직 없어요</h3><p>학년이나 주제를 바꾸거나 검색어를 줄여 보세요.</p><button type="button" class="pbtn" data-clear="all">전체 보기</button></li>';
  const gridOn=state.view==='find';
  $('#grid').hidden=!gridOn;$('#flist').hidden=gridOn;
  if(gridOn){
    $('#grid').innerHTML=list.length?list.map(b=>{
      const ks=[...new Set(b.materials.map(m=>m.k).filter(k=>k!=='answer'))];
      const ft=ks.map(k=>'<span class="tag '+FK[k][0]+'">'+IC[k]+FK[k][1]+'</span>').join('')+(b.pdf?'':'<span class="tag fh">한글 파일</span>');
      return '<li><button type="button" class="card" data-id="'+b.id+'">'
        +'<span class="cv" style="--tint:'+b.tint+'">'+coverHtml(b)+'</span>'
        +'<span class="cb"><span class="ct">'+esc(b.title)+'</span>'+(b.by?'<span class="ca">'+esc(b.by)+'</span>':'')
        +'<span class="tags">'+gtag(b)+ft+'</span></span></button></li>';
    }).join(''):empty;
  }else{
    $('#flist').innerHTML=list.length?list.map(b=>{
      const dl=b.materials.map(m=>link(quickHref(m),'dl '+FK[m.k][0],IC[m.k]+esc(m.label)+' <small>'+(m.pdf?'PDF'+(m.pdf.pages?' · '+m.pdf.pages+'쪽':''):m.hwp?'한글':'압축')+'</small>')).join('');
      return '<li class="frow"><span class="cv" style="--tint:'+b.tint+'">'+coverHtml(b,true)+'</span>'
        +'<div style="min-width:0"><button type="button" class="ftitle" data-id="'+b.id+'">'+esc(b.title)+'</button><div class="tags">'+gtag(b)+'</div></div>'
        +'<div class="fbtns">'+dl+'</div></li>';
    }).join(''):empty;
  }
}
function renderNav(){
  document.querySelectorAll('.nav').forEach(n=>{if(n.dataset.view===state.view)n.setAttribute('aria-current','page');else n.removeAttribute('aria-current')});
  const home=state.view==='home';
  $('#vHome').hidden=!home;$('#vList').hidden=home;
}
function render(){
  renderTabs();renderTopics();renderList();renderNav();
  $('#qx').hidden=!state.q;
}
function setView(v){state.view=v;render()}

/* events */
$('#tabs').addEventListener('click',e=>{const b=e.target.closest('.gtab');if(!b)return;state.g=state.g===b.dataset.g?null:b.dataset.g;if(state.view==='home')state.view='find';render()});
$('#topics').addEventListener('click',e=>{const b=e.target.closest('.chip');if(!b)return;state.t=state.t===b.dataset.t?null:b.dataset.t;render()});
document.querySelector('.side').addEventListener('click',e=>{const b=e.target.closest('.nav');if(b)setView(b.dataset.view)});
$('#vHome').addEventListener('click',e=>{const b=e.target.closest('[data-view]');if(b)setView(b.dataset.view)});
$('#rbar').addEventListener('click',clearHandler);
function listClick(e){
  if(e.target.closest('[data-clear]')){clearHandler(e);return}
  const f=e.target.closest('[data-file]');
  if(f){toast(f.dataset.file+' PDF가 아직 연결되지 않았어요.');return}
  const c=e.target.closest('[data-id]');if(c)openDetail(c.dataset.id);
}
$('#grid').addEventListener('click',listClick);
$('#flist').addEventListener('click',listClick);
function clearHandler(e){
  const b=e.target.closest('[data-clear]');if(!b)return;
  const k=b.dataset.clear;
  if(k==='all'||k==='g')state.g=null;
  if(k==='all'||k==='t')state.t=null;
  if(k==='all'||k==='q'){state.q='';$('#q').value=''}
  render();
}
$('#q').addEventListener('input',e=>{state.q=e.target.value.trim();render()});
$('#qx').addEventListener('click',()=>{state.q='';$('#q').value='';render();$('#q').focus()});

/* sticky grade tabs: compact once pinned */
const bar=$('#tabsBar');
try{
  const sent=document.createElement('div');sent.style.cssText='height:1px;margin-bottom:-1px;pointer-events:none';
  bar.parentNode.insertBefore(sent,bar);
  new IntersectionObserver(([en])=>{bar.classList.toggle('stuck',!en.isIntersecting&&en.boundingClientRect.top<0)},{threshold:0}).observe(sent);
}catch(err){}

/* detail */
let lastY=0,pushed=false,cur=null,pvList=[],pvI=0;
function openDetail(id){
  const b=BOOKS.find(x=>x.id===id);if(!b)return;
  cur=b;lastY=window.scrollY;
  $('#backLbl').textContent=state.view==='guides'?'독서 지도안':'도서 찾기';
  $('#dCover').innerHTML='<div class="cv'+(b.cover?'':' nocv')+'" style="--tint:'+b.tint+'">'+coverHtml(b,true)+'</div>';
  const kw=(b.keywords||[]).map(k=>'<button type="button" data-kw="'+esc(k)+'">'+esc(k)+'</button>').join('');
  let flow='';
  if(!b.flow);
  else if(b.flow.type==='phase') flow='<div class="phase">'+b.flow.items.map(p=>'<div class="ph"><b>'+p.n+'</b><ul>'+p.l.map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul></div>').join('')+'</div>';
  else if(b.flow.type==='session') flow='<ol class="sess">'+b.flow.items.map((x,i)=>'<li><span class="no">'+(i+1)+'차시</span>'+esc(x)+'</li>').join('')+'</ol>';
  else if(b.flow.type==='sheets') flow='<ul class="sheets">'+b.flow.items.map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul>';
  const flowTitle=b.flow&&b.flow.type==='sheets'?'활동지 구성':'수업 흐름';
  const flowSmall=!b.flow?'':b.flow.type==='session'?'총 '+b.flow.items.length+'차시':b.flow.type==='sheets'?b.flow.items.length+'가지':'';
  const facts=[['지은이',b.by],['출판사',b.publisher],['시리즈',b.series],['지도안 작성',b.guide],['참고',b.note]].filter(r=>r[1]);
  pvList=b.previews||[];
  $('#dInfo').innerHTML=
    '<div class="tags">'+gtag(b)+'</div>'
    +'<h1 id="dTitle" tabindex="-1">'+esc(b.title)+'</h1>'
    +(b.by?'<p class="d-by">'+esc(b.by)+'</p>':'')
    +(b.lede?'<p class="lede">'+esc(b.lede)+'</p>':'<p class="lede">'+esc(b.info)+' 자료가 있어요. 아래 버튼으로 화면에서 보거나 인쇄용 원본을 받으세요.</p>')
    +(kw?'<div class="kw" aria-label="주제어">'+kw+'</div>':'')
    +(flow?'<section class="d-sec"><h2><span>'+flowTitle+'</span>'+(flowSmall?'<small>'+flowSmall+'</small>':'')+'</h2>'+flow+'</section>':'')
    +(b.curri&&b.curri.length?'<section class="d-sec"><h2><span>교과 연계</span><small>국어</small></h2><div class="cc">'+b.curri.map(c=>'<span>'+esc(c)+'</span>').join('')+'</div></section>':'')
    +(pvList.length?'<section class="d-sec"><h2><span>'+esc(b.prevLabel)+'</span><small>눌러서 크게 보기</small></h2><div class="pv">'
      +pvList.map((p,i)=>'<button type="button" data-pv="'+i+'"><img src="'+esc(p.src)+'" alt="'+esc(p.cap)+'" loading="lazy"><span>'+esc(p.cap)+'</span></button>').join('')+'</div></section>':'')
    +(facts.length?'<section class="d-sec"><h2><span>자료 정보</span></h2><dl class="facts">'+facts.map(r=>'<div><dt>'+r[0]+'</dt><dd>'+esc(r[1])+'</dd></div>').join('')+'</dl></section>':'');
  const act=$('#dAct');
  act.className='mats';
  act.innerHTML=b.materials.map(m=>{
    const btns=[];
    if(m.pdf){
      btns.push(link(m.pdf.view,'btn btn-t',IC.eye+'<span>화면으로 보기<small>PDF'+(m.pdf.pages?' · '+m.pdf.pages+'쪽':'')+'</small></span>'));
      btns.push(link(m.pdf.href,'btn btn-s',IC.print+'<span>인쇄용 원본 받기<small>PDF · '+mbTxt(m.pdf.mb)+'</small></span>'));
    }
    if(m.hwp) btns.push(link(m.hwp.href,'btn btn-h',IC.down+'<span>한글 파일 받기<small>'+esc(m.hwp.ext.toUpperCase())+' · '+mbTxt(m.hwp.mb)+'</small></span>'));
    if(m.zip) btns.push(link(m.zip.href,'btn btn-h',IC.down+'<span>압축 파일 받기<small>ZIP · '+mbTxt(m.zip.mb)+'</small></span>'));
    return '<div class="mat"><h3 class="mat-t"><span class="tag '+FK[m.k][0]+'">'+IC[m.k]+FK[m.k][1]+'</span>'+esc(m.label)+'</h3><div class="act'+(btns.length===1?' one':'')+'">'+btns.join('')+'</div></div>';
  }).join('')+(b.hwp?'<p class="mat-note">한글 파일은 폰에서 열리지 않을 수 있어요. PC에서 여는 것을 권해요.</p>':'');
  $('#winBody').hidden=true;$('#detail').hidden=false;
  document.body.classList.add('detail-open');
  window.scrollTo(0,Math.max(0,$('#detail').getBoundingClientRect().top+window.scrollY-120));
  $('#dTitle').focus({preventScroll:true});
  try{history.pushState({d:id},'');pushed=true}catch(err){pushed=false}
}
function closeDetail(){
  if($('#detail').hidden)return;
  $('#detail').hidden=true;$('#winBody').hidden=false;
  document.body.classList.remove('detail-open');
  window.scrollTo(0,lastY);
  if(cur){const el=document.querySelector('[data-id="'+cur.id+'"]');if(el)el.focus({preventScroll:true})}
}
function backBtn(){
  if(pushed){
    pushed=false;
    try{history.back();setTimeout(()=>{if(!$('#detail').hidden)closeDetail()},300);return}catch(err){}
  }
  closeDetail();
}
$('#back').addEventListener('click',backBtn);
window.addEventListener('popstate',()=>{pushed=false;closeDetail()});
$('#dInfo').addEventListener('click',e=>{
  const k=e.target.closest('[data-kw]');
  if(k){state.q=k.dataset.kw;state.g=null;state.t=null;state.view='find';$('#q').value=state.q;pushed=false;closeDetail();render();return}
  const p=e.target.closest('[data-pv]');if(p)openLb(+p.dataset.pv);
});
$('#dAct').addEventListener('click',e=>{
  const b=e.target.closest('[data-file]');if(!b)return;
  toast(b.dataset.file+' PDF가 아직 연결되지 않았어요.');
});

/* lightbox */
function openLb(i){pvI=i;showLb();$('#lb').hidden=false;$('#lbX').focus()}
function showLb(){
  const p=pvList[pvI];
  $('#lbImg').src=p.src;$('#lbImg').alt=p.cap;
  $('#lbCap').textContent=p.cap+'  ('+(pvI+1)+' / '+pvList.length+')';
}
function stepLb(d){pvI=(pvI+d+pvList.length)%pvList.length;showLb()}
$('#lbPrev').addEventListener('click',e=>{e.stopPropagation();stepLb(-1)});
$('#lbNext').addEventListener('click',e=>{e.stopPropagation();stepLb(1)});
$('#lbX').addEventListener('click',()=>{$('#lb').hidden=true});
$('#lb').addEventListener('click',e=>{if(e.target===$('#lb'))$('#lb').hidden=true});
document.addEventListener('keydown',e=>{
  if(!$('#lb').hidden){
    if(e.key==='Escape')$('#lb').hidden=true;
    if(e.key==='ArrowLeft')stepLb(-1);
    if(e.key==='ArrowRight')stepLb(1);
    return;
  }
  if(e.key==='Escape')backBtn();
});

let tt;
function toast(msg){const t=$('#toast');t.textContent=msg;t.classList.add('on');clearTimeout(tt);tt=setTimeout(()=>t.classList.remove('on'),3800)}

function setDev(d){
  $('#stage').dataset.device=d;
  $('#devPhone').setAttribute('aria-pressed',d==='phone');
  $('#devPc').setAttribute('aria-pressed',d==='pc');
}
$('#devPhone').addEventListener('click',()=>setDev('phone'));
$('#devPc').addEventListener('click',()=>setDev('pc'));

/* 시작: 도서 데이터 읽기. 주소 끝에 ?proto 를 붙이면 시안용 도구 막대(폰/PC 크기 보기)가 나타납니다. */
if(/[?&]proto\b/.test(location.search))$('#tools').hidden=false;
fetch('data/books.json')
  .then(r=>{if(!r.ok)throw new Error(r.status);return r.json()})
  .then(d=>{
    GRADES=d.grades;TOPICS=d.topics;BOOKS=d.books;
    BOOKS.forEach(b=>{
      const fl=!b.flow?[]:b.flow.type==='phase'?b.flow.items.flatMap(p=>[p.n,...p.l]):b.flow.items;
      b.topics=b.topics||[];
      b.hay=[b.title,b.authors||'',b.by||'',b.publisher||'',b.series||'',(b.keywords||[]).join(' '),fl.join(' '),(b.curri||[]).join(' '),b.grades.map(g=>gradeOf(g).label).join(' '),b.materials.map(m=>m.label).join(' ')].join(' ').toLowerCase().replace(/\s+/g,'');
    });
    render();
  })
  .catch(()=>{
    $('#grid').innerHTML='<li class="empty"><h3>목록을 불러오지 못했어요</h3><p>잠시 후 다시 열어 주세요. 계속되면 관리자에게 알려 주세요.</p></li>';
  });
