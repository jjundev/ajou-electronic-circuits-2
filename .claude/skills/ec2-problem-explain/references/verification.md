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
              "items": {"p1:main": {"status": "pass", "reviewer": "…", "evidence": "…"}}},
  "independent": {"status": "pass", "reviewer": "…", "evidence": "…",
                  "items": {"p1:main": {"status": "pass", "reviewer": "…", "evidence": "evidence/p1-sympy.py, evidence/p1-result.txt: …",
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

결함이 있으면 그 항목을 `fail`로 두고 작성자에게 되돌려요. 고친 뒤 build부터 다시 해요.

## independent: 독립 검산 (작성자와 다른 에이전트)

검산 에이전트는 조건과 구할 것만으로 먼저 답을 구해요.
1. SymPy가 없으면 설치해요: `pip3 install --user --break-system-packages sympy`.
2. 기호 계산 스크립트를 `BUCKET/evidence/pN-sympy.py`로 저장해요. 소신호 등가회로의 KCL/KVL을 `sympy.solve`로 풀고, 결과를 `simplify`해 목표 식과의 차이가 0인지 확인해요. 근사가 있으면 `sympy.limit`(예: $r_o\to\infty$, $\lambda\to0$)으로 근사 전후를 모두 보여요. 수치 문항은 주어진 값을 대입해요.
3. 실행 출력을 `BUCKET/evidence/pN-result.txt`로 저장해요.
   ```bash
   python3 "$BUCKET/evidence/p1-sympy.py" > "$BUCKET/evidence/p1-result.txt" 2>&1
   ```
4. 그다음 md `## 풀이`(source.json `reference_answer`)와 조각의 완성 답과 비교해요.
   - 셋이 같으면 `pass`.
   - 조각만 다르면 작성자에게 되돌려요(그 사이 상태는 `fail`).
   - md `## 풀이`와 독립 검산이 다르면 `disputed`이고 그 팩은 발행하지 않아요. conclusion에 두 값을 모두 적어요.

method는 `exact|symbolic|numerical|proof|qualitative` 중 하나예요. 기호 유도는 `symbolic`, 증명은 `proof`(숫자 예만 있는 evidence는 승인하지 않아요), 정성 비교(예: "CM 이득이 커진다/작아진다")는 `qualitative`로 두고 논증과 극한 확인을 evidence에 적어요. `numerical`이면 유한한 `tolerance`>0과 0≤`residual`≤`tolerance`도 넣어요.

```json
{
  "status": "pass",
  "reviewer": "독립 검산 에이전트(opus, p1 작성자와 다름)",
  "evidence": "evidence/p1-sympy.py, evidence/p1-result.txt: CM 하프 서킷 KCL을 풀어 simplify(A_CM - 목표식) = 0",
  "method": "symbolic",
  "conclusion": "A_CM = -(R_D/2)/(1/(2g_m)+r_O3), md 풀이·조각과 일치"
}
```

evidence 파일은 build 전에 써 둬야 stage의 `자료_…/evidence/`로 복사되어 함께 발행돼요. evidence에는 RUN 기준이 아닌 `evidence/…` 상대 이름을 적어요.

## browser: 화면 검토 (메인 에이전트)

file:// 미리보기에서는 스크립트가 돌지 않으므로 stage 폴더를 서버로 열어요. 셸 상태가 이어지지 않으니 포트를 먼저 출력해 두고 숫자를 직접 써요.
1. 빈 포트: `python3 -c "import socket; s=socket.socket(); s.bind(('',0)); print(s.getsockname()[1])"`
2. Bash 도구의 `run_in_background: true`로 `python3 -m http.server <port> --bind 127.0.0.1 --directory "<BUCKET>/<stage>"`.
3. URL: `http://127.0.0.1:<port>/문제설명_<range>_<slug>.html`(한글 그대로).
4. `resize_window`로 1280×900을 명시하고 `document.documentElement.clientWidth > 0`을 확인한 뒤 측정해요.

`javascript_tool`로 실행해요.
```js
await new Promise((r) => setTimeout(r, 1500));
const textNodes = Array.from(document.querySelectorAll('main *, #panel-right *')).filter((e) => !['SCRIPT', 'STYLE'].includes(e.tagName) && !e.closest('[hidden]'));
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const scroller = document.querySelector('.content') || document.documentElement;
const over = [], panelOver = [];
for (const t of document.querySelectorAll('main article.topic')) {
  location.hash = '#' + t.id; await wait(250);
  document.getAnimations().forEach((a) => a.finish());
  if (scroller.scrollWidth > scroller.clientWidth + 1 || document.documentElement.scrollWidth > window.innerWidth + 1) over.push(t.id);
  for (const d of document.querySelectorAll('#panel-right .sum .katex-display')) {
    if (d.offsetParent !== null && d.scrollWidth > d.clientWidth + 1) panelOver.push(t.id);
  }
}
location.hash = '';
({
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
통과: `topics`·`sumsInPanel`이 문항 수, `katexErrors: 0`, `rawDollar: false`, `sumsLeftInMain: 0`, `brokenImages: []`, `external: []`, `hScroll: []`, `panelOverflow: []`, `read_console_messages`에 오류 없음.

그다음 실제로 눌러 봐요: 왼쪽 목차에서 문항 이동, `#pager-prev`/`#pager-next`, 오른쪽 요약 패널에 그 문항 요약이 보이는지(스크린샷), 회로 그림과 수식이 잘리거나 겹치지 않는지, 짧은 인라인 수식에 스크롤바가 없는지, 구역 24px·제목 아래 12px·소문항 16px 간격.

`resize_window`(`preset: "mobile"`, `colorScheme: "dark"`) → 새로고침 → 위 스크립트 재실행 → 스크린샷으로 그림·글자가 보이는지 확인 → `#theme-toggle`을 눌러 배경색과 `aria-label`이 바뀌는지 확인 → `localStorage.removeItem('od-theme')`. 1280×900 light/dark와 375×812 light/dark 네 조합을 모두 봐요. 끝나면 `preset: "desktop"`, `colorScheme: "light"`로 되돌리고 서버를 종료해요.

stage에서는 `복습문제_…-문제.pdf`나 정리노트로 가는 링크가 발행 위치(`복습노트/<range>/`) 기준이라 열리지 않아요. 이 링크는 check가 발행 위치 기준으로 파일·anchor를 검사하고, 메인 에이전트가 `href`의 대상 파일과 `id`가 실제로 있는지 한 번 더 확인해요.

evidence에는 크기·테마 조합, 스크립트 결과 요약, 누른 항목을 적어요.

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

답 충돌·조건 모호함·원문 미확인은 그 팩을 `disputed`로 두고 이유를 보고해요. 다른 팩은 통과하면 발행해요. publish는 원본을 바꾸지 않고 설명 소유 파일(`문제설명_<range>_<slug>.html/.md`, `figures_문제설명_…/`, `자료_문제설명_…/`)만 `BUCKET/backups/`에 백업한 뒤 교체하고, 실패하면 복구해요. 발행된 `자료_문제설명_…/validation.json`이 그때의 review.json이에요.
