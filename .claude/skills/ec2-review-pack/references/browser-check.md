# 브라우저 검증 (메인 에이전트)

## 서버
file:// 미리보기에서는 스크립트가 돌지 않는다. 빈 포트로 서버를 띄운다. 셸 상태는 Bash 호출 사이에 이어지지 않으므로 포트 번호를 먼저 출력해 두고, 이후 명령과 URL에는 그 숫자를 직접 쓴다.
1. 빈 포트 찾기(출력된 숫자가 `<port>`):
   ```bash
   python3 -c "import socket; s=socket.socket(); s.bind(('',0)); print(s.getsockname()[1])"
   ```
2. 서버 띄우기: Bash 도구의 `run_in_background: true`로 실행한다(명령 끝에 `&`를 붙이지 않는다).
   ```bash
   python3 -m http.server <port> --directory "<RUN>/repo"
   ```
3. URL: `http://localhost:<port>/복습노트/<range>/<파일명>` (한글 그대로).
4. 끝나면 서버를 종료한다: 그 백그라운드 작업을 멈추거나(TaskStop 등), `pkill -f "http.server <port>"`.

## 측정 전 준비
브라우저 창이 숨겨져 있으면 `document.documentElement.clientWidth`가 0이 되어 `hScroll`이 거짓 양성으로 나온다. 측정 전에 `resize_window`로 크기를 명시하고(`width: 1280`, `height: 900`) `document.documentElement.clientWidth > 0`을 확인한다. `.katex-mathml` 안 요소는 화면에 보이지 않으므로 넘침 원인으로 치지 않는다. 스크롤 직후 스크린샷은 늦게 반영될 수 있으니 1초쯤 기다린 뒤 찍는다.

## 가로 넘침 측정
템플릿은 `body`를 고정하고 본문을 `.content` 안에서 스크롤하며, 한 번에 한 화면(토픽·카드)만 보여 준다. 그래서 `document.documentElement.scrollWidth`로는 넘침이 잡히지 않는다. 아래 `overflowScreens`로 화면을 하나씩 넘기며 `.content`를 잰다. 결과는 넘친 화면 id 목록이고, 비어 있어야 통과다. 목록이 나오면 그 화면에서 `.content`의 오른쪽 끝을 넘는 요소를 찾아 원인을 확인한다(`.katex-display`·`.table-wrap` 안의 자체 가로 스크롤은 넘침이 아니다).
```js
async function overflowScreens() {
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));
  const scroller = document.querySelector('.content') || document.documentElement;
  const screens = Array.from(document.querySelectorAll('main .screen'));
  const over = [];
  for (const s of screens.length ? screens : [document.querySelector('main')]) {
    if (screens.length) { location.hash = s.id ? '#' + s.id : ''; await wait(150); }
    // 넘어올 때의 translateX(24px) 애니메이션이 넘침으로 잡히지 않게 끝낸다(숨은 창에서는 애니메이션이 멈춰 있다)
    document.getAnimations().forEach((a) => a.finish());
    if (scroller.scrollWidth > scroller.clientWidth + 1 || document.documentElement.scrollWidth > window.innerWidth + 1) over.push(s.id || 'hero');
  }
  location.hash = '';
  await wait(150);
  return over;
}
```

## 정리노트 (`mcp__Claude_Browser__javascript_tool`)
위 `overflowScreens` 정의를 같은 실행에 붙여 넣는다.
```js
await new Promise((r) => setTimeout(r, 1500));
const textNodes = Array.from(document.querySelectorAll('main *, #panel-right *')).filter((e) => !['SCRIPT', 'STYLE'].includes(e.tagName) && !e.closest('[hidden]'));
({
  katex: document.querySelectorAll('.katex').length,
  katexErrors: document.querySelectorAll('.katex-error').length,
  rawDollar: textNodes.some((e) => Array.from(e.childNodes).some((n) => n.nodeType === 3 && n.textContent.includes('$'))),
  sumsInPanel: document.querySelectorAll('#panel-right .sum').length,
  sumsLeftInMain: document.querySelectorAll('main .sum').length,
  hScroll: await overflowScreens(),
  panelOverflow: await panelOverflow(),
  widgets: Array.from(document.querySelectorAll('.widget')).map((w) => ({ id: w.id, drawn: Array.from(w.querySelectorAll('svg')).some((s) => !s.closest('[hidden]') && s.childElementCount > 0) })),
})
```
`panelOverflow`는 토픽마다 넘겨 가며 "페이지 요약" 패널의 식이 패널 폭을 넘는지 잰다. 패널 식은 가로 스크롤이 되지만 스크롤바가 안 보여 잘린 것처럼 보이므로 넘침으로 친다. 1280px에서 재야 패널이 열려 있다. 같은 실행에 아래 정의도 붙여 넣는다.
```js
async function panelOverflow() {
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));
  const over = [];
  for (const t of document.querySelectorAll('main article.topic')) {
    location.hash = '#' + t.id; await wait(250);
    for (const d of document.querySelectorAll('#panel-right .sum .katex-display')) {
      if (d.offsetParent !== null && d.scrollWidth > d.clientWidth + 1) over.push({ topic: t.id, px: d.scrollWidth - d.clientWidth, tex: (d.querySelector('annotation') || {}).textContent });
    }
  }
  location.hash = '';
  await wait(150);
  return over;
}
```
통과: `katexErrors: 0`, `rawDollar: false`, `sumsInPanel`이 manifest에서 `layers`가 빈 목록이 아닌 토픽 수, `sumsLeftInMain: 0`, `hScroll: []`, `panelOverflow: []`, 모든 위젯 `drawn: true`. `read_console_messages`에 오류 없음. `panelOverflow`에 나온 식은 그 토픽 작성자에게 `.sum`의 식을 여러 줄로 나누라고 되돌린다(`references/content-rules.md` 페이지 요약).

개념 토픽 하나로 넘겨(`location.hash = '#<토픽 id>'`) 오른쪽 "페이지 요약" 패널에 그 토픽의 요약이 보이는지 스크린샷으로 확인한다(1280px 이상에서는 패널이 기본으로 열린다).

위젯마다 그 토픽으로 넘긴 뒤 슬라이더 하나를 바꾸고(`input` 이벤트) readout 값이 `.widget-static` 표의 같은 설정 값과 같은지 확인한다.

## 모바일·다크
`resize_window`(`preset: "mobile"`, `colorScheme: "dark"`) → 새로고침 → `clientWidth > 0` 확인 → 위 스크립트 재실행(`hScroll: []`) → 스크린샷으로 그림·위젯 글자가 보이는지 확인 → 상단 바의 테마 버튼(`#theme-toggle`)을 눌러 `document.body` 배경색이 바뀌고 `aria-label`이 반대 모드로 바뀌는지 확인한 뒤 `localStorage.removeItem('od-theme')`로 지운다 → `preset: "desktop"`, `colorScheme: "light"`로 되돌린다.

## 복습문제 PDF (문제가 1개 이상일 때)
정리노트의 `s<N>-links` 토픽으로 넘긴 뒤 아래를 실행한다.
```js
await Promise.all(Array.from(document.querySelectorAll('a[href$=".pdf"]')).map(async (a) => {
  const r = await fetch(a.href, { method: 'HEAD' });
  return { href: a.getAttribute('href'), status: r.status, type: r.headers.get('content-type') };
}))
```
통과: 링크가 2개(문제·답안)이고 모두 `status: 200`, `type: "application/pdf"`. PDF 내용은 `Read` 도구(`pages: "1-2"`)로 첫 두 쪽을 열어 제목이 `복습문제_<range>_<slug>`이고 첫 문제가 manifest의 첫 id인지 확인한다.

## 마무리
모든 검사가 끝나면 `resize_window`(`preset: "desktop"`, `colorScheme: "light"`)로 되돌리고 서버를 종료한다(위 "서버" 4).

PDF 규격도 확인한다: 모든 쪽이 16:9이고, 아래쪽 1/6(1920×1080 기준 180px)에 텍스트·회로·격자가 없어야 한다. 이전 A4 영상 전체 화면과 비교해 텍스트 표시 크기를 유지한다. 본문 기본값은 약 11.34pt이며 기존 문항별 축소 배율을 보존한다. 문제/답안 문항 순서, Hint 부록, 넘침 여부를 함께 확인한다.

## 본문과 페이지 요약의 계약

요약은 본문의 핵심 개념·작동 원리·성립 조건·혼동 구분을 압축하며 항목 수의 고정 상한을 두지 않는다. 본문에 없는 사실을 요약에만 추가하지 않고 보충의 범위·출처·불확실성을 유지한다. 긴 회로식은 패널 폭 안에서 읽히도록 여러 수식 줄로 나눈다. 중앙 제목과 고정 패널 제목은 유지하며 우측 중복 주제·문항 제목은 출력하지 않는다. `sum-for`는 `.sums` 컨테이너의 유일한 ID로 보존하고 제목 대입 JS를 만들지 않는다. 문제·보기·정답·해설·원문 탭·앵커·저장 키는 보존한다.

모든 학습 토픽에 대해 자료·토픽별 일반·강조·주의·보충의 서로 다른 핵심을 별도 행으로 감사한다. 본문 주장·대응 요약 문장·판정/생략 이유와 `pass | unresolved`를 기록하고 보완 뒤 실제 요약을 다시 읽는다. 기존 동반 MD와 재생성 원고를 동기화하되 없는 MD 형식을 만들지 않는다. 검증 JSON은 `{schema_version:1, html, html_sha256, audit_path, audit_sha256, semantic_status, browser_status, evidence, unresolved}`이며 실제 검사 뒤에만 상태를 갱신한다. 파일 해시 변경 후 기존 증거는 갱신 전까지 오래된 근거다.

1280×900·375×812와 light·dark 네 조합에서 실제 패널을 열고 서로 다른 두 토픽의 요약 전환, 이전 요약 숨김, 표지 안내, 중앙 제목 유지·우측 중복 제목 없음, 유일한 `#sum-for.sums`, 패널 내부 가로 넘침 없음과 수식·콘솔 오류 0을 확인한다. 문제설명은 문제·원문 탭과 이전/다음 이동도 확인한다. 읽음·푼 문제 저장 키와 payload가 이동·새로고침 뒤 유지되는지 검사하며 missing-sum 검사는 계속 실패를 탐지해야 한다.
