# 검토 기록과 발행

`check`는 구역·소문항·수식 구분자·자원·파일 해시만 검사해요. 의미와 답이 맞다는 판단은 하지 않아요. `build`가 만든 `BUCKET/review.json`은 전부 `not_run`이에요. 실제 확인을 수행한 에이전트의 결과만 기록해요. md `## 풀이`(source.json의 `reference_steps`·`reference_answer`)를 독립 검산의 결과로 간주하지 않아요.

`input_hash`는 현재 원본과 설명 조각에 묶여 있어요. `artifact_hashes`는 build가 넣은 stage 파일 해시예요. 조각·원본·evidence를 바꿨다면 다시 build하고 네 검토를 모두 다시 해요. build는 review.json을 초기화하므로 예전 기록을 복사해 붙이지 않아요. `artifact_hashes`를 손으로 고치지 않아요.

경로: `BUCKET=RUN/review-<range>-<slug>`, stage HTML은 `BUCKET/stage.json`의 `stage`·`html`로 찾아요(`BUCKET/<stage>/<html>`).

## review.json 형태

```json
{
  "input_hash": "(build가 넣은 값 그대로)",
  "artifact_hashes": {"(build가 넣은 값 그대로)": "…"},
  "references": [{"path": "/abs/REPO/교과서/마이크로전자회로/10장.pdf", "sha256": "…"}],
  "source_visual": {"status": "pass", "reviewer": "…", "evidence": "…"},
  "content": {"status": "pass", "reviewer": "…", "evidence": "…",
              "items": {"pN:main": {"status": "pass", "reviewer": "…", "evidence": "…"}}},
  "independent": {"status": "pass", "reviewer": "…", "evidence": "…",
                  "items": {"pN:main": {"status": "pass", "reviewer": "…", "evidence": "evidence/pN-sympy.py, evidence/pN-result.txt: …",
                                        "method": "symbolic", "conclusion": "…"}}},
  "browser": {"status": "pass", "reviewer": "…", "evidence": "…"}
}
```

`items`의 키는 `source.json`의 모든 `pN:<subpart>`(`pN:a`, `pN:1`, `pN:main`)이고 build가 미리 만들어 둬요. 모든 단계와 items가 status=`pass`, 비어 있지 않은 reviewer·evidence여야 발행돼요. `not_run`, `fail`, `disputed`는 발행을 보류해요.

review.json은 python으로 읽고 고쳐 써요(키를 지우거나 해시를 바꾸지 않게 필요한 값만 넣어요).

## source_visual: 원본 쪽 대조

문제 md의 frontmatter `pdf_page`와 다음 쪽을 PNG로 렌더해 대조해요. 교과서는 `교과서/마이크로전자회로/<N>장.pdf`, 기출은 frontmatter `source`의 PDF예요.

```bash
python3 "$REPO/workbook/source_pages.py" render <문제 md 절대 경로…> --out "$RUN/pages"
```

`RUN/pages/<id>-p<쪽>.png`를 Read 도구로 열어 문항마다 다음을 확인해요: 조건의 수치·기호·가정(어느 트랜지스터가 $\lambda\neq0$인지 등), 그림의 회로 연결, 소문항 개수와 표지(`(a)`/`(1)`), 구할 것. 조립된 stage HTML의 원문·조건·구할 것·그림과도 맞는지 봐요. evidence에 "pN(workbook id): <PDF> p<쪽> 대조, 일치/차이 내용"을 문항마다 적어요. 차이가 있으면 md는 고치지 않고 그 팩을 disputed로 보고해요.

## content: 내용 리뷰 (작성자가 아닌 opus 리뷰어 1명)

리뷰어에게 stage HTML 경로, `source.json`, 이 문서와 [저작 규칙](authoring.md)의 경로, 참고 자료 경로를 넘기고, 모든 `pN:<subpart>`에 대해 판정을 JSON으로 받아요. 확인할 것:
- recall: 문제의 단서 → 개념 → 기호의 뜻 → 근사 조건 → 선택 이유가 이어지는지. 제목만 있거나 공식만 나열하면 fail.
- start: 실제 첫 줄(등가회로·하프 서킷·KCL 첫 식)인지, recall의 긴 설명을 복제하지 않았는지.
- solve: 유도 이유·근사의 적용 범위·소문항별 누락 여부, 모든 답.
- verify: 극한·단위·대칭 특수값 검산이 실제로 계산되었는지.
- 요약 sum의 개념·공식·답이 본문과 일치하는지.

추가 교육적 연결 검토:
- 핵심 규칙에서 작은 상태 변화/기호 조작, 실제 첫 식, 유도까지 이어지는지. 수치 예시 유무 자체로 판정하지 않아요.
- KCL의 방향·노드·제어 전압 정의와 가지별 전류, 시험전류 귀환 경로가 보여서 첫 식을 재구성할 수 있는지.
- 반회로 전환·병렬 공통 인자·기호 치환·차수 판단·보충 정확식에 숨은 중간 단계가 없는지. 보충식도 본문과 같은 기준이에요.
- 예시가 원문 조건과 구분되고, 근사·단위·부호가 본문·요약·MD·그림에 일치하는지. 증명은 예시 뒤에도 일반 논증을 유지하는지.
- 소신호 등가회로 그림: 문항마다 start·solve가 소신호 KCL/KVL을 세우는지 먼저 판정해요. 세우는데 [저작 규칙](authoring.md)의 "소신호 등가회로 그림"이 없으면 fail이에요. 그림이 있으면 원 문제 그림과 토폴로지(어느 노드 사이에 어느 소자가 있는지, 무엇을 AC 접지로 보냈는지)가 같은지, 노드 이름·전류 방향·제어 전압 극성이 첫 KCL 식과 같은지 대조해요. 그림이 2개면 각 그림의 경계 조건(단락·무부하·CM·DM)이 해당 식과 맞는지도 봐요. 판정과 대조 결과를 evidence에 문항마다 적어요. DC KCL만 있어 제외한 문항도 이유를 적어요.
- retry를 예상 답 없이 먼저 풀어 답·이유·적용 조건을 기록한 뒤 작성자 evidence와 대조해요. 값이 부족하거나 조건 밖인 질문은 보강해요. 범용 재계산 지시만 있거나 본문 복사만으로 끝나면 fail이에요.

교육적 연결 검토와 독립 수학 검산, 원문 시각 대조, 브라우저 검토는 각각 수행 사실과 범위를 기록해요. 한 검토의 통과를 다른 검토의 통과로 대신하지 않아요.

결함이 있으면 그 항목을 `fail`로 두고 작성자에게 되돌려요. 고친 뒤 build부터 다시 해요.

## independent: 독립 검산 (작성자와 다른 에이전트)

검산 에이전트는 조건과 구할 것만으로 먼저 답을 구해요.
1. SymPy가 없으면 설치해요: `pip3 install --user --break-system-packages sympy`.
2. 기호 계산 스크립트를 `BUCKET/evidence/pN-sympy.py`로 저장해요. 소신호 등가회로의 KCL/KVL을 `sympy.solve`로 풀고, 결과를 `simplify`해 목표 식과의 차이가 0인지 확인해요. 근사가 있으면 `sympy.limit`(예: $r_o\to\infty$, $\lambda\to0$)으로 근사 전후를 모두 보여요. 수치 문항은 주어진 값을 대입해요.
3. 실행 출력을 `BUCKET/evidence/pN-result.txt`로 저장해요.
   ```bash
   python3 "$BUCKET/evidence/pN-sympy.py" > "$BUCKET/evidence/pN-result.txt" 2>&1
   ```
   `pN`은 실제 문항 id(`p1`, `p2`…)로 바꿔 써요. 문항마다 이 두 파일 이름만 써요.
4. 그다음 md `## 풀이`(source.json `reference_answer`)와 조각의 완성 답과 비교해요.
   - 셋이 같으면 `pass`.
   - 조각만 다르면 작성자에게 되돌려요(그 사이 상태는 `fail`).
   - md `## 풀이`와 독립 검산이 다르면 `disputed`이고 그 팩은 발행하지 않아요. conclusion에 두 값을 모두 적어요.
   - 근사 수준의 차이는 `disputed`가 아니에요. 조각이 표준 근사 조건(예: $r_{O3}\gg R_1\parallel r_{\pi3}$, $g_m r_o\gg1$)을 명시하고 정확한 식도 함께 보이며, 독립 검산이 그 조건에서 두 값의 비가 1로(또는 차이가 0으로) 간다는 것을 보이면 `pass`로 두고 conclusion에 그 조건을 적어요.
   - 실제 수치·구조 불일치(예: 한 식 안에서 서로 맞지 않는 모델을 섞음)는 근사 차이가 아니므로 `disputed`로 남겨요.

method는 `exact|symbolic|numerical|proof|qualitative` 중 하나예요. 기호 유도는 `symbolic`, 증명은 `proof`(숫자 예만 있는 evidence는 승인하지 않아요), 정성 비교(예: "CM 이득이 커진다/작아진다")는 `qualitative`로 두고 논증과 극한 확인을 evidence에 적어요. `numerical`이면 유한한 `tolerance`>0과 0≤`residual`≤`tolerance`도 넣어요.

```json
{
  "status": "pass",
  "reviewer": "독립 검산 에이전트(opus, pN 작성자와 다름)",
  "evidence": "evidence/pN-sympy.py, evidence/pN-result.txt: CM 하프 서킷 KCL을 풀어 simplify(A_CM - 목표식) = 0",
  "method": "symbolic",
  "conclusion": "A_CM = -(R_D/2)/(1/(2g_m)+r_O3), md 풀이·조각과 일치"
}
```

evidence 파일은 build 전에 써 둬야 stage의 `.assets/자료_…/evidence/`로 복사되어 함께 발행돼요. evidence에는 RUN 기준이 아닌 `evidence/…` 상대 이름을 적어요.

## browser: 화면 검토 (메인 에이전트)

file:// 미리보기에서는 스크립트가 돌지 않으므로 stage 폴더를 서버로 열어요. 셸 상태가 이어지지 않으니 포트를 먼저 출력해 두고 숫자를 직접 써요.
1. 빈 포트: `python3 -c "import socket; s=socket.socket(); s.bind(('',0)); print(s.getsockname()[1])"`
2. Bash 도구의 `run_in_background: true`로 `python3 -m http.server <port> --bind 127.0.0.1 --directory "<BUCKET>/<stage>"`. 서버를 띄우고 몇 초 지난 뒤에 측정해요.
3. URL: `http://127.0.0.1:<port>/문제설명_<range>_<slug>.html`(한글 그대로).

**전제: 측정하는 페이지의 `document.visibilityState`가 `'visible'`이어야 해요.** 탭이 숨겨져 있으면 `requestAnimationFrame`이 돌지 않아 템플릿의 수식 줄 배치와 등장 애니메이션이 실행되지 않고, `hScroll`이 실제로 없는 넘침을 보고해요. visibilityState가 `'visible'`이 아닌 페이지에서 잰 값은 검토 결과로 쓰지 않아요. 내장 브라우저 창은 숨겨진 상태일 수 있어서 측정은 헤드리스 Playwright로 해요.

### 측정: 헤드리스 Playwright (기본 경로)

[scripts/epe_browser_check.py](../scripts/epe_browser_check.py)가 1280×900·375×812 × light·dark 네 조합을 새 컨텍스트로 열고, 문항마다 700ms 기다리며 아래 스크립트로 재고, 콘솔 오류를 모아 JSON으로 출력해요. 한 조합이라도 통과 기준을 넘지 못하면 종료 코드 1이에요.

```bash
python3 -c "import playwright" || pip3 install --user --break-system-packages playwright
python3 -m playwright install chromium   # chromium이 없을 때만
python3 "$SKILL/scripts/epe_browser_check.py" --url "http://127.0.0.1:<port>/문제설명_<range>_<slug>.html" --topics <문항 수> --shots "$RUN/shots" > "$RUN/browser.json"
```

- `--shots`는 선택이에요. 주면 조합×문항마다 `shot-<조합>-<pN>.png`를 저장하니 Read 도구로 열어 회로 그림과 수식이 잘리거나 겹치지 않는지, 글자가 다크 모드에서 보이는지 확인해요. 소신호 등가회로 그림이 있는 팩은 `--shots`를 반드시 주고, 다크 모드에서 선·글자·노드 점이 모두 보이는지 봐요.
- 콘솔 오류에 `ERR_CONNECTION_RESET`·`ERR_SOCKET_NOT_CONNECTED`가 있으면(출력의 `flaky_rerun`) 로컬 서버가 요청을 끊은 것이라 페이지 결함이 아니에요. fail로 두지 말고 같은 명령을 다시 실행해요. 두 번 연속 깨끗하지 않으면 원인을 살펴요.

조합마다 재는 값(스크립트에 들어 있는 것과 같아요):
```js
await new Promise((r) => setTimeout(r, 1500));
const textNodes = Array.from(document.querySelectorAll('main *, #panel-right *')).filter((e) => !['SCRIPT', 'STYLE'].includes(e.tagName) && !e.closest('[hidden]'));
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const scroller = document.querySelector('.content') || document.documentElement;
const over = [], panelOver = [];
for (const t of document.querySelectorAll('main article.topic')) {
  location.hash = '#' + t.id; await wait(700);
  document.getAnimations().forEach((a) => a.finish());
  await wait(100);
  if (scroller.scrollWidth > scroller.clientWidth + 1 || document.documentElement.scrollWidth > window.innerWidth + 1) over.push(t.id + ':' + scroller.scrollWidth);
  for (const d of document.querySelectorAll('#panel-right .sum .katex-display')) {
    if (d.offsetParent !== null && d.scrollWidth > d.clientWidth + 1) panelOver.push(t.id);
  }
}
location.hash = '';
({
  visibility: document.visibilityState,
  topics: document.querySelectorAll('main article.topic').length,
  katex: document.querySelectorAll('.katex').length,
  katexErrors: document.querySelectorAll('.katex-error').length,
  rawDollar: textNodes.some((e) => Array.from(e.childNodes).some((n) => n.nodeType === 3 && n.textContent.includes('$'))),
  sumsInPanel: document.querySelectorAll('#panel-right .sum').length,
  sumsLeftInMain: document.querySelectorAll('main .sum').length,
  brokenImages: Array.from(document.images).filter((i) => !i.complete || i.naturalWidth === 0).map((i) => i.getAttribute('src')),
  external: performance.getEntriesByType('resource').map((e) => e.name).filter((u) => !u.startsWith(location.origin)),
  hScroll: over,
  panelOverflow: panelOver,
})
```
통과(네 조합 모두): `visibility: "visible"`, `topics`·`sumsInPanel`이 문항 수, `katexErrors: 0`, `rawDollar: false`, `sumsLeftInMain: 0`, `brokenImages: []`, `external: []`, `hScroll: []`, `panelOverflow: []`, 콘솔 오류 없음(`consoleErrors: []`).

### 손으로 누르는 확인: 내장 브라우저 창

측정은 위 스크립트로 끝내고, 내장 브라우저 창은 실제로 눌러 보는 확인에만 써요. 누르기 전에 `javascript_tool`로 `document.visibilityState`가 `'visible'`인지 확인해요. 아니면 창을 앞으로 보이게 한 뒤 다시 확인하고, 그래도 안 되면 이 확인은 `--shots` 스크린샷으로 대신하고 그 사실을 evidence에 적어요.
- `resize_window`로 1280×900을 명시하고 `document.documentElement.clientWidth > 0`을 확인해요.
- 왼쪽 목차에서 문항 이동, `#pager-prev`/`#pager-next`, 오른쪽 요약 패널에 그 문항 요약이 보이는지(스크린샷), 짧은 인라인 수식에 스크롤바가 없는지, 구역 24px·제목 아래 12px·소문항 16px 간격.
- `resize_window`(`preset: "mobile"`, `colorScheme: "dark"`) → 새로고침 → `#theme-toggle`을 눌러 배경색과 `aria-label`이 바뀌는지 확인 → `localStorage.removeItem('od-theme')`.
- 끝나면 `preset: "desktop"`, `colorScheme: "light"`로 되돌리고 서버를 종료해요.

stage에서는 `복습문제_…-문제.pdf`나 정리노트로 가는 링크가 발행 위치(`복습노트/<range>/`) 기준이라 열리지 않아요. 이 링크는 check가 발행 위치 기준으로 파일·anchor를 검사하고, 메인 에이전트가 `href`의 대상 파일과 `id`가 실제로 있는지 한 번 더 확인해요.

evidence에는 쓴 경로(`playwright-headless` 측정 / 내장 브라우저 창 클릭 확인), 크기·테마 조합, 스크립트 결과 요약(재실행했다면 그 이유), 누른 항목을 적어요. 숨겨진 창에서 잰 값이나 경로가 적히지 않은 기록은 pass로 두지 않아요.

## references

실제로 읽은 저장소 자료(문제 md는 입력 해시에 이미 묶이므로 그 밖의 Razavi 장 PDF, 강의노트 PDF, 정리노트 HTML, STT 등)의 절대 경로와 SHA-256을 기록해요. 경로는 저장소 안의 실제 경로여야 하고 심볼릭 링크를 거치지 않아요. 발행 직전 다시 해시를 비교하므로 그 사이 바뀐 자료가 있으면 발행이 막혀요.

```bash
python3 - "$BUCKET/review.json" <읽은 자료 절대 경로…> <<'EOF'
import hashlib, json, sys
from pathlib import Path
review = Path(sys.argv[1])
data = json.loads(review.read_text(encoding="utf-8"))
refs = {r["path"]: r for r in data["references"]}
for arg in sys.argv[2:]:
    p = Path(arg).absolute()
    refs[str(p)] = {"path": str(p), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
data["references"] = list(refs.values())
review.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(len(data["references"]), "references")
EOF
```

## 발행과 보류

답 충돌·조건 모호함·원문 미확인은 그 팩을 `disputed`로 두고 이유를 보고해요. 다른 팩은 통과하면 발행해요. publish는 원본을 바꾸지 않고 설명 소유 파일(`문제설명_<range>_<slug>.html`, `.assets/`의 `문제설명_<range>_<slug>.md`·`figures_문제설명_…/`·`자료_문제설명_…/`)만 `BUCKET/backups/`에 백업한 뒤 교체하고, 실패하면 복구해요. 발행된 `.assets/자료_문제설명_…/validation.json`이 그때의 review.json이에요.


## 현재 기준과 재렌더링 검토 계약

현재 `review_policy_version`은 `problem-explain-2026-10-18-smallsignal`다. 새 review.json·manifest의 버전이 일치해야 발행된다. 구버전/버전 없는 검토를 단순히 현재 버전으로 바꾸거나 pass를 복사하지 않는다. 기준 변경은 실제 content·independent 재검토를 요구한다.

content는 recall의 근거 있는 명칭 대응, pitfall의 오답 판별 기준, 부정형의 참·거짓과 선택 적합성, understand·solve·verify·pitfall·sum의 결함 공개·공식 답 확인 여부가 일관적인지 확인한다. 과목별 disputed 규칙은 유지한다. 독립 검산은 작성자와 다른 검산자가 정답·참고 풀이·설명 조각을 보지 않고 문제·그림·필요한 이론 자료만으로 먼저 수행한다. 컨트롤러가 그 결과를 참고 답과 대조한다.

rerender의 검토 재사용은 동일한 입력·조각·입력 그림과 무결한 발행 자료, 검증된 모든 참조, 같은 검토 기준을 전제로 한다. 참조가 없거나 바뀌면 content·independent도 not_run으로 두고 다시 검토한다. 전자회로2는 problems.txt가 같더라도 문제 MD·그림이 바뀌면 재사용하지 않는다. source_visual·browser는 매번 새 stage에서 수행한다. 구조 검사는 내용 검증이 아니다.

browser는 1280×900·1024×900·375×812, light/dark에서 실제 확인한다. 1023→1024 경계에서 목차·문제 기본 열림, 저장한 닫힘 유지, 원문 탭(원문 없는 문항은 숨김), 문제 패널 왼쪽·오른쪽 붙이기·띄우기, 이동·크기 조절·화면 내 제한, 모바일 접힘, 그림 확대와 인쇄 문제/원문 보존을 확인한다. 유효한 객관식은 오답·정답·다시 풀기·판정 이동, 모델 없는 문항은 정적 표시를 확인한다. 코드 문자·들여쓰기·수식·소문항·원문을 보존하고 외부 요청·콘솔/KaTeX 오류·누락 자원·문서 가로 넘침은 0이어야 한다.

참조 HTML·MD·SVG가 로컬 그림을 사용하면 해당 그림도 references에 절대 경로와 SHA-256으로 별도 기록한다. 참조 그림 해시 누락·변경은 검토 재사용과 새 발행을 막는다. 옮긴 그림의 이전 바이트를 확인할 수 없으면 현재 파일을 자기 자신과 비교해 같은 그림이라고 간주하지 않는다.

## 본문과 페이지 요약의 계약

요약은 본문의 핵심 개념·작동 원리·성립 조건·혼동 구분을 압축하며 항목 수의 고정 상한을 두지 않는다. 본문에 없는 사실을 요약에만 추가하지 않고 보충의 범위·출처·불확실성을 유지한다. 긴 회로식은 패널 폭 안에서 읽히도록 여러 수식 줄로 나눈다. 중앙 제목과 고정 패널 제목은 유지하며 우측 중복 주제·문항 제목은 출력하지 않는다. `sum-for`는 `.sums` 컨테이너의 유일한 ID로 보존하고 제목 대입 JS를 만들지 않는다. 문제·보기·정답·해설·원문 탭·앵커·저장 키는 보존한다.

모든 학습 토픽에 대해 자료·토픽별 일반·강조·주의·보충의 서로 다른 핵심을 별도 행으로 감사한다. 본문 주장·대응 요약 문장·판정/생략 이유와 `pass | unresolved`를 기록하고 보완 뒤 실제 요약을 다시 읽는다. 기존 동반 MD와 재생성 원고를 동기화하되 없는 MD 형식을 만들지 않는다. 검증 JSON은 `{schema_version:1, html, html_sha256, audit_path, audit_sha256, semantic_status, browser_status, evidence, unresolved}`이며 실제 검사 뒤에만 상태를 갱신한다. 파일 해시 변경 후 기존 증거는 갱신 전까지 오래된 근거다.

1280×900·375×812와 light·dark 네 조합에서 실제 패널을 열고 서로 다른 두 토픽의 요약 전환, 이전 요약 숨김, 표지 안내, 중앙 제목 유지·우측 중복 제목 없음, 유일한 `#sum-for.sums`, 패널 내부 가로 넘침 없음과 수식·콘솔 오류 0을 확인한다. 문제설명은 문제·원문 탭과 이전/다음 이동도 확인한다. 읽음·푼 문제 저장 키와 payload가 이동·새로고침 뒤 유지되는지 검사하며 missing-sum 검사는 계속 실패를 탐지해야 한다.
