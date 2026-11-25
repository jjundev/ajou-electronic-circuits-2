# 브라우저 검증 (브라우저 QA 에이전트)

[delegation.md](delegation.md)의 파일 인계 계약을 따른다. QA 한 명이 자기 격리 브라우저 컨텍스트와 이번 실행의 서버를 단독 소유하며, 다른 에이전트와 같은 탭·뷰포트·테마·저장 상태를 동시에 조작하지 않는다. 저장소와 발행 파일은 읽기 전용이다. 상세 결과·실제 스크린샷·측정값은 `<RUN>/work/browser/`에만 저장하고, 부모에게 상태·증거 파일 경로·영향받는 topic ID 목록·미해결을 8줄 이내로 반환한다. 실제 브라우저 조작과 스크린샷 확인은 아래 모든 검사에서 그대로 수행하며, 정적 검사나 이전 실행 증거로 대체하지 않는다. 결함은 담당 작성자에게 돌리고 저장소 파일을 직접 고치지 않는다.

## 서버
file:// 미리보기에서는 스크립트가 돌지 않는다. 빈 포트로 서버를 띄운다. 셸 상태는 Bash 호출 사이에 이어지지 않으므로 포트 번호를 먼저 출력해 두고, 이후 명령과 URL에는 그 숫자를 직접 쓴다.
1. 빈 포트 찾기(출력된 숫자가 `<port>`):
   ```bash
   python3 -c "import socket; s=socket.socket(); s.bind(('',0)); print(s.getsockname()[1])"
   ```
2. 서버 띄우기: Bash 도구의 `run_in_background: true`로 실행한다(명령 끝에 `&`를 붙이지 않는다). 반환된 작업 ID나 실제 서버 PID를 `<RUN>/work/browser/`에 기록해 소유 프로세스를 식별한다.
   ```bash
   python3 -m http.server <port> --directory "<RUN>/repo"
   ```
3. URL: `http://localhost:<port>/복습노트/<range>/<파일명>` (한글 그대로).
4. 끝나면 이번 QA가 시작한 서버만 종료한다. 기록한 백그라운드 작업 ID(TaskStop 등)나 PID를 확인하고 해당 작업/프로세스만 멈춘다. 이름·명령 패턴으로 서버를 일괄 종료하지 않는다.

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
`panelOverflow`는 토픽마다 넘겨 가며 "요약" 패널의 식이 패널 폭을 넘는지 잰다. 패널 식은 가로 스크롤이 되지만 스크롤바가 안 보여 잘린 것처럼 보이므로 넘침으로 친다. 1280px에서 재야 패널이 열려 있다. 같은 실행에 아래 정의도 붙여 넣는다.
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

개념 토픽 하나로 넘겨(`location.hash = '#<토픽 id>'`) 오른쪽 "요약" 패널에 그 토픽의 요약이 보이는지 스크린샷으로 확인한다(1280px 이상에서는 패널이 기본으로 열린다).

## 토픽 회로 (`body[data-circuits]` 노트)
먼저 `layout_probe.py`의 결과가 현재 노트 해시로 결함 0인지 본다(`circuits`·`label_gaps`·`overflow`, 각 check의 `topic_svgs`가 1 이상). 그다음 회로가 있는 토픽을 모두 화면으로 본다.
- 1280px(패널 열림·닫힘)과 375px: formal을 끝까지 내리는 동안 회로가 상단 바 아래에 고정되고 식을 가리지 않으며, 글자를 읽을 수 있다.
- 회로가 둘이면 해당 구간에서 다음 회로로 넘어가고, 앞 회로가 그 아래로 비집고 나오지 않는다.
- 패널을 여닫아도 회로는 본문에 남고, 패널에는 그 토픽의 요약만 있다. 높이 500px 미만에서는 고정하지 않는다. 인쇄 미리보기에는 모든 회로가 본문 자리에 있다.
- 글의 ㉠㉡㉢이 회로의 그 자리를 가리키고, 라이트·다크에서 모두 보인다.

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
통과 기준은 manifest의 문제 수와 검사 단계에 따라 정한다. 선택 PDF 링크 이외의 다른 자료 링크도 실제 확인한다.
- 문제 0개: 이번 팩의 문제·답안 PDF 링크가 없어야 한다. 두 링크의 개수/200 응답이나 없는 PDF 화면을 요구하지 않는다.
- 문제 1개 이상, 답안 발행 전: 문제·답안 링크의 경로가 manifest와 일치해야 한다. 문제지는 `status: 200`, `type: "application/pdf"`여야 한다. 답안은 manifest의 정확한 pending 경로만 미발행을 허용하고 예비 검사로 기록한다. 다른 경로의 404나 이전 답안 PDF를 이번 승인 답안으로 통과시키지 않는다.
- 답안 발행 후: 두 링크 모두 `status: 200`, `type: "application/pdf"`여야 한다. 최종 검사에는 pending 유예가 없다.

현재 존재하는 PDF는 사용 가능한 PDF 읽기/이미지 도구로 첫 두 쪽을 열어 제목이 `복습문제_<range>_<slug>`이고 첫 문제가 manifest의 첫 id인지 확인한다. 전체 답안 렌더 검토는 통합 계약의 9단계에서 별도로 수행한다.

## 마무리
모든 검사가 끝나면 `resize_window`(`preset: "desktop"`, `colorScheme: "light"`)로 되돌리고 서버를 종료한다(위 "서버" 4).

PDF 규격도 확인한다: 모든 쪽이 16:9이고, 아래쪽 1/6(1920×1080 기준 180px)에 텍스트·회로·격자가 없어야 한다. 이전 A4 영상 전체 화면과 비교해 텍스트 표시 크기를 유지한다. 본문 기본값은 약 11.34pt이며 기존 문항별 축소 배율을 보존한다. 문제/답안 문항 순서, Hint 부록, 넘침 여부를 함께 확인한다.

## 본문과 페이지 요약의 계약

요약은 시험 직전 확인할 핵심만 남긴다. 기본 구성은 핵심 한 문장 → 필요한 식 1~3개 → 판단 기준 1~3개이며 권장 분량이지 할당량이나 강제 상한이 아니다. 반복 예시·유도·중복 용어 풀이·일반적인 경고는 본문에 둔다. 식의 적용 여부나 답의 부호를 바꾸는 조건은 해당 식 옆에 압축한다. 본문에 없는 사실을 추가하지 않는다. 모든 본문 주장을 요약에 복제하지 않고 핵심의 일치·오해 가능성·중복 여부를 검토하며 생략 이유는 감사 기록에 남긴다.

요약의 문장은 각각 별도 `<p>`로 작성하며 한 문장에는 하나의 판단을 담는다. 마침표로 문장을 실행 중 자동 분리하지 않는다(소수·약어·TeX 보존). 자연스러운 화면 줄바꿈은 허용한다. 의미가 나뉘면 짧은 소제목의 `summary-group`으로 묶되 단순 요약에 소제목을 늘리지 않는다. 제목 아래 12px, 그룹 사이 24px, 문장 문단 사이 8px을 공통 템플릿이 처리하며 빈 문단·연속 `<br>`로 간격을 만들지 않는다. 긴 식은 하나의 `aligned` 안에서 관계를 유지하며 나눈다. 중앙 제목·고정 패널 제목과 유일한 `.sums#sum-for`, 문제·원문 탭·앵커·저장 키를 보존한다.

공개 학습 HTML·요약·동반 MD·툴팁·접근성 문구에는 STT 줄 번호·Part·타임스탬프·시각 정보 유무를 출력하지 않는다. 근거 위치는 별도 검토 기록에만 보관한다. 해설 HTML·동반 MD의 학습량 행(핵심/추가 연습·소문항 묶음·예상 시간)은 생성하지 않고 선발 JSON에는 유지한다. PDF 규칙은 이 HTML 가독성 변경으로 바꾸지 않는다.

모든 학습 토픽에 대해 자료·토픽별 일반·강조·주의·보충의 서로 다른 핵심을 별도 행으로 감사한다. 본문 주장·대응 요약 문장·판정/생략 이유와 `pass | unresolved`를 기록하고 보완 뒤 실제 요약을 다시 읽는다. 기존 동반 MD와 재생성 원고를 동기화하되 없는 MD 형식을 만들지 않는다. 검증 JSON은 `{schema_version:1, html, html_sha256, audit_path, audit_sha256, semantic_status, browser_status, evidence, unresolved}`이며 실제 검사 뒤에만 상태를 갱신한다. 파일 해시 변경 후 기존 증거는 갱신 전까지 오래된 근거다.

1280×900·375×812와 light·dark 네 조합에서 실제 패널을 열고 서로 다른 두 토픽의 요약 전환, 이전 요약 숨김, 표지 안내, 중앙 제목 유지·우측 중복 제목 없음, 유일한 `#sum-for.sums`, 패널 내부 가로 넘침 없음과 수식·콘솔 오류 0을 확인한다. 문제설명은 문제·원문 탭과 이전/다음 이동도 확인한다. 읽음·푼 문제 저장 키와 payload가 이동·새로고침 뒤 유지되는지 검사하며 missing-sum 검사는 계속 실패를 탐지해야 한다.

## 가독성 화면 확인

모든 토픽을 데스크톱·모바일과 라이트·다크에서 순회한다. 요약 문장은 별도 문단에서 시작하고(8px 간격), 제목 아래 12px·의미 그룹 사이 24px인지 실제 경계상자로 측정한다. solve의 첫 직계 소문항은 제목 뒤 24px, 동급 사이는 화면 너비 1024px 이상에서 32px·그 미만에서 24px이며 마지막 문단 여백과 중복되지 않아야 한다. 긴 식의 잘림, 목록·정의 목록, 소제목 이전 줄바꿈, 숨긴 요약이 본문에 남지 않는지 확인한다. 학습량 행과 공개 STT 위치 정보는 HTML·MD·툴팁·접근성 문구에 없어야 한다. Pretendard 및 회로 Pretendard 600을 유지하고 문항 순서·답·원문 탭·저장 상태를 보존한다.
