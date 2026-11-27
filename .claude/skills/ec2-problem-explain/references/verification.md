# 검토 기록과 발행

참고 풀이가 없는 문항도 동일한 게이트를 적용한다. 작성자는 원문·그림에서 직접 풀며 독립 검토자는 작성자의 결과를 보기 전에 원문에서 별도 풀이를 기록한다. 회로 연결·출력 극성/정의·근사 조건을 먼저 대조하고 식·수치·단위·극한 조건을 검산한다. 단순한 같은 식의 재대입이나 참고 풀이 유무는 승인 근거가 아니다. 없음 자체는 disputed가 아니며 원문 모호·독립 풀이 불일치·검증 미완료는 해결 전 withheld다. 부모가 문항을 교체하면 새 source/build/모든 검토를 거친다. selection.json의 핵심/추가·소문항 묶음 수·추정 시간이 입력 해시와 일치하는지 확인한다. 해설 HTML·동반 MD에 학습량 행이 없는지 검사하고 PDF 표시는 기존 PDF 정책과 선발 메타데이터에 맞는지 별도로 확인한다.

`check`는 구역·소문항·수식 구분자·자원·파일 해시만 검사해요. 의미와 답이 맞다는 판단은 하지 않아요. `build`가 만든 `BUCKET/review.json`은 전부 `not_run`이에요. 실제 확인을 수행한 에이전트의 결과만 기록해요. md `## 풀이`(source.json의 `reference_steps`·`reference_answer`)를 독립 검산의 결과로 간주하지 않아요.

`input_hash`는 현재 원본과 설명 조각에 묶여 있어요. `artifact_hashes`는 build가 넣은 stage 파일 해시예요. 조각·원본·evidence를 바꿨다면 다시 build하고 네 검토를 모두 다시 해요. build는 review.json을 초기화하므로 예전 기록을 복사해 붙이지 않아요. `artifact_hashes`를 손으로 고치지 않아요.

경로: `BUCKET=RUN/review-<range>-<slug>`, stage HTML은 `BUCKET/stage.json`의 `stage`·`html`로 찾아요(`BUCKET/<stage>/<html>`).

## review.json 형태

```json
{
  "review_policy_version": "(build가 넣은 값 그대로)",
  "input_hash": "(build가 넣은 값 그대로)",
  "artifact_hashes": {"(build가 넣은 값 그대로)": "…"},
  "references": [{"path": "/abs/REPO/교과서/마이크로전자회로/10장.pdf", "sha256": "…"}],
  "source_visual": {"status": "pass", "reviewer": "…", "evidence": "…"},
  "content": {"status": "pass", "reviewer": "…", "evidence": "…",
              "items": {"pN:main": {"status": "pass", "reviewer": "…", "evidence": "…"}}},
  "independent": {"status": "pass", "reviewer": "…", "evidence": "…",
                  "items": {"pN:main": {"status": "pass", "reviewer": "…", "evidence": "evidence/pN-sympy.py, evidence/pN-result.txt: …",
                                        "method": "symbolic", "conclusion": "…"}}},
  "browser": {"status": "pass", "reviewer": "…", "evidence": "…"},
  "learning_style_audit": {"learning_style": {"path": ".claude/skills/ec2-review-pack/references/solution-style.md", "sha256": "…", "rule_ids": ["…"]},
    "items": {"pN:main": {"status": "not_run", "reviewer": "", "rules": {"<규칙 ID>": {"disposition": "applied", "evidence": ""}}}}}
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

## content: 내용 리뷰 (작성자와 별도 리뷰어 1명)

리뷰어 모델은 [스킬의 모델 선택 규칙](../SKILL.md)을 따른다.

리뷰어에게 stage HTML 경로, `source.json`, 이 문서와 [저작 규칙](authoring.md)의 경로, 참고 자료 경로를 넘기고, 모든 `pN:<subpart>`에 대해 판정을 JSON으로 받아요. 확인할 것:
- 단일 풀이 구역을 읽고 회로 판단에서 첫 식을 재구성한다. 필요한 중간량, 소문항별 답과 조건이 한 번씩 드러나는지 확인한다. 독립 계산은 한 행에 하나씩, 결론에 영향을 주는 가정·유한 항·단위·부호는 해당 식 곁에 둔다. 문항의 오답을 가려내는 검산이 본문에 있으면 그 역할을 확인한다.
- [말로 줄인 연산 금지](authoring.md#핵심-규칙에서-첫-식까지)를 적용한다. 곱·나눗셈·대입의 대상을 이름만으로 부르고 식이 없는 단계가 있으면 fail이다. 블록 이득을 익숙한 이상값(팔로워 1 등)으로 잘못 읽을 수 있는 곳과 전달비의 종류가 바뀌는 곳에 바꾸는 식이 있는지 특히 확인한다.
- 회로 그림의 ㉠ 등 위치 표지가 같은 소자·노드·회로 상태를 가리키는지 확인한다. 원문 회로, 개루프, 시험원의 조건을 구별한다. KCL/KVL을 쓴 곳은 [소신호 등가회로 기준](authoring.md#소신호-등가회로-그림)에 따라 토폴로지, 노드 이름, 전류 방향, 제어 전압의 극성 및 측정 상태를 첫 식과 대조한다. 필수 회로 누락은 fail이며, 그림이 필요 없는 DC KCL 등은 비적용 이유를 적는다.
- [회로 배치와 출력저항 기준](authoring.md#회로-배치와-출력저항-표시-기준)을 적용한다. 출력 단자·병렬 가지·시험전류 방향·접지·노드 점·라벨 여백과 색을 실제 산출에서 확인한다. 유한 β가 필요한 식과 큰 β 근사, 입력 영점과 출력 단락을 구별한다. 원문 예외가 없는 정확 $R_{out}$ 전체 모델과 유도는 내부 검산 evidence에서 확인한다.
- 연쇄 곱 문항은 목표 전달비의 곱이 단별 계산보다 먼저 나오는지, 바로 읽히고 재사용할 개루프 저항이 앞에서 정의되는지 확인한다. 귀환 문항은 감지·반송과 복제 종단의 대응, 테브난 전압의 기준과 첫 인자 $v_{\mathrm{Th}}/I_{in}$, 분압의 1회 반영, $R_{in,\mathrm{open}}$의 별도 정의, 단별 부하와 귀환율 시험의 방향·부호를 확인한다. 적용 위치 또는 비적용 근거를 CIRCUIT-02·GAIN-01·NOTATION-01에 적는다.
- 귀환 해설의 첫 전체 개루프 이득 정의에 $A_{\mathrm{open}}$과 전달비 단위가 보이는지, 폐루프 식에 부호 있는 $KA_{\mathrm{open}}$을 직접 썼는지 확인한다. 레이저 직렬 감지에서는 $A_{\mathrm{open}}$과 첫 저항 괄호에 모두 같은 $R_L$이 포함되고, 포트 자체의 답에서는 $R_L$을 한 번 빼는지 확인한다. 노턴 전류의 단락 조건과 노턴 저항의 시험원 조건을 대조한다.
- [페이지 요약 기준](authoring.md#페이지-요약)에 따라 요약의 핵심·공식·답과 성립 조건을 본문·MD와 대조한다. 결과를 바꾸는 원문 결함·가정은 해당 식 곁에서 확인하고, 보기의 참·거짓과 선택 적합성을 구별한다.
- 답안 선택 표지가 각 소문항의 회로·판단·계산·최종 답을 가리키는지 확인한다. 고정 회로는 `data-answer-step`과 `data-answer-subpart`가 함께 있어야 답안에 들어간다. 여러 소문항이 공유하면 첫 사용 단계에서 한 번 선택한다. `answer-overlay.json`과 실제 답안 PDF에서 회로·조건·수치·부호·답을 대조한다. HTML 위치 표시를 걷어낸 뒤에도 회로와 식을 읽을 수 있어야 한다.

내용, 독립 검산, 원문 대조, 브라우저 검토는 각각 실제 수행 범위를 기록한다. 결함이 있으면 해당 항목을 `fail`로 두고 작성자에게 되돌린다. 수정 뒤 build부터 다시 한다.

## learning_style_audit: 모든 소문항의 개인화 감사

content 리뷰어 브리프의 필수 입력은 `<REPO>/.claude/skills/ec2-review-pack/references/solution-style.md` 절대 경로, `source.json.learning_style`, stage HTML, 저작·검토 규칙이다. 마지막 build가 만든 `review.json.learning_style_audit`의 각 `pN:<subpart>`를 실제 의미 검토한 뒤 채운다. 모든 소문항·모든 rule_ids에 `reviewer`, `status=pass`, `rules[ID]={disposition: applied|not_applicable, evidence: 적용 위치/내용 또는 비적용 이유}`가 필요하다. 수치 계산이 없는 문항에는 이유 있는 `not_applicable`를 사용한다.

snapshot은 path·sha256·rule_ids를 그대로 보존하고 references에 실제 읽은 명세의 절대 경로·현재 SHA-256을 유지한다. 풀이 본문에서 관찰된 사고 순서를 확인하고 필요한 상세 유도가 사라지지 않았는지도 본다. $R_{out}$ 정확식은 위 예외가 아닌 한 내부 검산에만 보존한다. 명세 바이트 변경은 HTML 동등성으로 대체할 수 없고 실제 재검토가 필요하다. 형식 검증이 evidence의 의미를 승인하지 않는다. 현재 네 검토와 개인화 감사가 모두 pass인 발행 `validation.json`만 overlay를 승인한다.

## independent: 독립 검산 (작성자와 다른 에이전트)

검산 에이전트는 조건과 구할 것만으로 먼저 답을 구해요.
조정자는 전달할 입력과 브리프의 참조가 문제·그림·필요 이론만 포함하는지 확인해요. 정답·참고 풀이·설명 조각과 정답 필드가 포함된 전체 `source.json`은 검산자에게 전달하지 않아요. 검산자가 독립 풀이와 evidence를 먼저 저장한 뒤 조정자가 참고 답과 비교해요. 풀이 저장 전에 답이나 풀이가 노출되면 해당 검산 판정과 evidence는 무효예요. 기존 보고에 노출 사실을 기록하고 답을 보지 않은 새 검산자가 처음부터 다시 풀어요. 이전 무효 evidence·판정·보고는 새 검산자에게 전달하거나 읽게 하지 않고, 아래 정식 evidence 경로에는 재수행 결과만 제출해요. 새 검산자가 없으면 독립 검산은 미완료이며 발행을 보류해요.
1. SymPy가 없으면 설치해요: `pip3 install --user --break-system-packages sympy`.
2. 기호 계산 스크립트를 `BUCKET/evidence/pN-sympy.py`로 저장해요. 소신호 등가회로의 KCL/KVL을 `sympy.solve`로 풀고, 결과를 `simplify`해 독립 결과를 기록해요. 풀이를 저장한 뒤 참고 식과 비교할 때 차이가 0인지 확인해요. 근사가 있으면 `sympy.limit`(예: $r_o\to\infty$, $\lambda\to0$)으로 근사 전후를 내부 evidence에 모두 기록해요. $R_{out}$의 정확식·대조 수치는 위 예외가 아니면 학습 HTML·요약·MD·답안 PDF로 옮기지 않아요. 수치 문항은 주어진 값을 대입해요.
3. 실행 출력을 `BUCKET/evidence/pN-result.txt`로 저장해요.
   ```bash
   python3 "$BUCKET/evidence/pN-sympy.py" > "$BUCKET/evidence/pN-result.txt" 2>&1
   ```
   `pN`은 실제 문항 id(`p1`, `p2`…)로 바꿔 써요. 문항마다 이 두 파일 이름만 써요.
4. 그다음 md `## 풀이`(source.json `reference_answer`)와 조각의 완성 답과 비교해요.
   - 셋이 같으면 `pass`.
   - 조각만 다르면 작성자에게 되돌려요(그 사이 상태는 `fail`).
   - md `## 풀이`와 독립 검산이 다르면 `disputed`이고 그 팩은 발행하지 않아요. conclusion에 두 값을 모두 적어요.
   - 근사 수준의 차이는 `disputed`가 아니에요. 조각이 표준 근사 조건(예: $r_{O3}\gg R_1\parallel r_{\pi3}$, $g_m r_o\gg1$)을 명시하고, 독립 검산 evidence에서 정확식과 근사식을 대조해 그 조건에서 두 값의 비가 1로(또는 차이가 0으로) 간다는 것을 보이면 `pass`로 두고 conclusion에 그 조건을 적어요. 정확식을 조각에 함께 표시할 필요는 없으며 $R_{out}$은 위 예외가 아니면 근사식만 표시해요.
   - 실제 수치·구조 불일치(예: 한 식 안에서 서로 맞지 않는 모델을 섞음)는 근사 차이가 아니므로 `disputed`로 남겨요.

method는 `exact|symbolic|numerical|proof|qualitative` 중 하나예요. 기호 유도는 `symbolic`, 증명은 `proof`(숫자 예만 있는 evidence는 승인하지 않아요), 정성 비교(예: "CM 이득이 커진다/작아진다")는 `qualitative`로 두고 논증과 극한 확인을 evidence에 적어요. `numerical`이면 유한한 `tolerance`>0과 0≤`residual`≤`tolerance`도 넣어요.

```json
{
  "status": "pass",
  "reviewer": "독립 검산 에이전트의 실제 식별자",
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

[scripts/epe_browser_check.py](../scripts/epe_browser_check.py)가 1280×900·375×812 × light·dark 네 조합을 새 컨텍스트로 열고, 문항을 순회하며 측정값과 콘솔 오류를 모아 JSON으로 출력해요. 한 조합이라도 통과 기준을 넘지 못하면 종료 코드 1이에요.

```bash
python3 -c "import playwright" || pip3 install --user --break-system-packages playwright
python3 -m playwright install chromium   # chromium이 없을 때만
python3 "$SKILL/scripts/epe_browser_check.py" --url "http://127.0.0.1:<port>/문제설명_<range>_<slug>.html" --topics <문항 수> --shots "$RUN/shots" > "$RUN/browser.json"
```

- `--shots`는 선택이에요. 주면 조합×문항마다 `shot-<조합>-<pN>.png`를 저장하니 Read 도구로 열어 회로 그림과 수식이 잘리거나 겹치지 않는지, 글자가 다크 모드에서 보이는지 확인해요. 소신호 등가회로 그림이 있는 팩은 `--shots`를 반드시 주고, 다크 모드에서 선·글자·노드 점이 모두 보이는지 봐요.
- 콘솔 오류에 `ERR_CONNECTION_RESET`·`ERR_SOCKET_NOT_CONNECTED`가 있으면(출력의 `flaky_rerun`) 로컬 서버가 요청을 끊은 것이라 페이지 결함이 아니에요. fail로 두지 말고 같은 명령을 다시 실행해요. 두 번 연속 깨끗하지 않으면 원인을 살펴요.

통과 기준은 네 조합 모두 `visibility: "visible"`, 문항 수와 `topics`·`sumsInPanel` 일치, `katexErrors: 0`, `rawDollar: false`, `sumsLeftInMain: 0`이다. `brokenImages`·`external`·`hScroll`·`panelOverflow`·`consoleErrors`·`spacingErrors`는 빈 배열이어야 한다.

### 손으로 누르는 확인: 내장 브라우저 창

측정은 위 스크립트로 끝내고, 내장 브라우저 창은 실제로 눌러 보는 확인에만 써요. 누르기 전에 `javascript_tool`로 `document.visibilityState`가 `'visible'`인지 확인해요. 아니면 창을 앞으로 보이게 한 뒤 다시 확인하고, 그래도 안 되면 이 확인은 `--shots` 스크린샷으로 대신하고 그 사실을 evidence에 적어요.
- `resize_window`로 1280×900을 명시하고 `document.documentElement.clientWidth > 0`을 확인해요.
- 왼쪽 목차에서 문항 이동, `#pager-prev`/`#pager-next`, 오른쪽 요약 패널에 그 문항 요약이 보이는지(스크린샷), 짧은 인라인 수식에 스크롤바가 없는지 확인해요. 간격은 [가독성 화면 확인](#가독성-화면-확인) 기준을 써요.
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


## 기존 발행분의 재렌더링 검토

[기존 발행분 재렌더링](../SKILL.md#기존-발행분-재렌더링)에서 조립한 자료는 기존 구역·소문항·답안 선택 순서를 발행본과 대조한다. 현재 `review_policy_version`은 `problem-explain-2026-10-21-learning-style`이다. 동일한 입력·조각·입력 그림, 검토 기록과 일치하는 발행 산출 해시와 검증된 참조, 현재 명세 snapshot과 전체 소문항 감사, 같은 검토 기준이 모두 충족될 때만 content·independent와 개인화 감사를 재사용한다. `problems.txt`와 문제 MD·그림을 합친 입력 해시가 비교 기준이다. 원본·참조 자료가 같음을 입증할 수 없거나 기준이 달라지면 해당 검토를 다시 하고, source_visual·browser는 새 stage에서 매번 다시 한다.

참고로 읽은 HTML·MD의 바이트가 달라졌으면 해당 파일의 이전 바이트를 확보하고 내용 및 링크가 동등한지 검증한다. 참조 HTML·MD·SVG의 로컬 그림은 각각 실제 경로와 SHA-256을 기록한다. 그림이나 개인 명세 바이트가 바뀌었거나 필수 해시가 빠졌으면 해당 검토를 새로 수행한다. `check`와 `publish`는 재렌더링 때 확인한 발행 manifest와 조각을 다시 검증한다.

## 생성 회로 수식과 표시 제목 검토

- PROFILE CIRCUIT-02에 따라 $g_mr_o\gg1$, $g_mR_e\gg1$의 주항을 쓰고 캐스코드 곱 인자의 소자 번호를 확인한다. 외부 축퇴 저항과 내부 $r_e=1/g_m$를 구분하고, 유한 $r_\pi$를 임의로 제거하지 않는다. 원문이 반대 조건·수치 또는 정확 결과를 명시한 경우만 예외를 기록한다.
- 생성한 모든 SVG의 `<text>`를 열거한다. `vCM`, `gm`, `ro3`, 밑줄 기호·유니코드 가짜 첨자 `ₘ/₃/꜀`가 남지 않고 native `text/tspan`의 실제 sub/super 구조인지 확인한다. `$...$`를 텍스트로 남기거나 `foreignObject`의 수식 실행에 의존하지 않는다. 원문 인용·원본 이미지의 표기는 보존한다.
- 회로 라벨 전체의 실제 Pretendard SemiBold face·computed weight 600·정체(변수 포함)·기본 78% 실제 첨자를 확인한다. CSS 선언만 확인하지 않고 독립 SVG의 포함 글꼴 및 PDF 임베딩을 확인한다. HTML 라이트·다크, 모바일·데스크톱, 추출 SVG와 MD의 해당 그림, 실제 답안 PDF에서 첨자 높이·노드 색·라벨/도선 겹침·잘림을 각각 검사한다.
- `.assets/display-titles.json`의 ID 집합·순서별 번호를 대조한다. 제목은 목차·본문·MD·문제지·답안지에서 같은 `P<n>. 짧은 제목`이며 Fig 번호를 포함하지 않는다. 출처/원문 영역의 원래 교과서·기출 식별자는 보존한다. 제목 맵은 입력 해시에 포함되어야 하며 변경 전 승인으로 발행하지 않는다.

- 새/수정 CM 전압이득 본풀이가 성립 조건 → $2R_{SS}$ 반회로 → 출력 단락 $G_m$ → 입력 영점·부하 포함 $R_{out}$ → 부호 있는 곱 순서인지 확인한다. CM을 가상 접지로 두지 않았는지, 불일치에서 같은 가지 전류 모델이 유효한지, 전류 거울 결합을 보존했는지 확인한다. 테일 저항 상세 유도는 뒤의 보충이며 원문 지정 증명·방법은 유지한다.

## 가독성 화면 확인

모든 토픽을 데스크톱·모바일과 라이트·다크에서 순회한다. 요약 문장은 별도 문단에서 시작하고(8px 간격), 제목 아래 12px·의미 그룹 사이 24px인지 실제 경계상자로 측정한다. 직계 소문항은 앞 요소가 구역 제목일 때 24px, 그 외에는 화면 너비 1024px 이상에서 32px·그 미만에서 24px 간격을 확인한다. 각 소문항 제목과 첫 내용은 12px을 확인한다. 문단과 소문항 간격을 중복 가산하지 않는다. 긴 식의 잘림, 목록·정의 목록, 소제목 이전 줄바꿈, 숨긴 요약이 본문에 남지 않는지 확인한다. 학습량 행과 공개 STT 위치 정보는 HTML·MD·툴팁·접근성 문구에 없어야 한다. Pretendard 및 회로 Pretendard 600을 유지하고 문항 순서·답·원문 탭·저장 상태를 보존한다.

1280×900·1024×900·375×812와 라이트·다크에서 확인한다. 요약 패널을 열어 두 문항 사이를 이동하고 이전 요약의 숨김, 중앙 제목, 유일한 `#sum-for.sums`, 읽음·푼 문제 키와 새로고침 뒤 값 유지를 확인한다. 1023→1024 경계의 목차·문제 기본 열림과 사용자가 저장한 닫힘, 문제·원문 탭, 왼쪽·오른쪽 붙이기와 띄우기, 이동·크기 조절과 화면 내 제한, 모바일 접힘, 그림 확대와 인쇄의 원문 보존을 확인한다. 정답 모델이 유효하면 오답·정답·다시 풀기를, 모델이 없으면 정적 표시를 확인한다.


**전압이득 경로 검토:** PROFILE GAIN-01 감사에 중간 노드, 단별 로딩, 우회·역결합을 근거로 선택한 경로를 기록한다. 단별 곱이 성립하는 경우 각 단 이득의 입출력·로딩·부호와 최종 곱이 보이는지 확인한다. 단별 곱으로 충분한데 전체 $G_m$의 출력 단락 계산을 우선했으면 수정한다. 원문 지정 방법과 별도로 묻는 $G_m$·$R_{out}$은 해당 목표의 측정 조건을 확인한다.


### 새/수정 Gm–Rout 경로의 구조 검사

$G_m$·$R_{out}$ 방식으로 쓰는 새/수정 전압이득 경로에는 `data-gain-route="gm-rout"`와 그 안의 `data-gain-stage="gm"`, `"rout"`, `"gain"`을 사용한다. 수정하지 않는 기존 문항의 표지 없는 본문은 보존하고 사람 검토 범위로 남긴다. 세 단계는 같은 경로에 각각 한 번, 그 DOM 순서로 두고 각 단계의 제목 밖에 보이는 비어 있지 않은 `$...$` 또는 `$$...$$` 중간 수식을 쓴다. 경로를 중첩하거나 수식을 숨기지 않는다. 기존 보이는 `data-answer-step` 요소 안에도 넣을 수 있으며 새 본문이나 두 번째 풀이를 만들지 않는다. 이 속성들은 표시/MD 내용이나 답안 선택 의미를 바꾸지 않는다.

공통 HTML 검사와 EPE 조각 계약은 선언된 경로의 누락·순서·빈 식·명시적 숨김을 검사한다. 식의 정당성·입출력과 측정 조건·외부 부하 병렬·부호·필요한 유한 β/ro는 사람이 검토한다. 표지가 없는 과거 문장을 정규식으로 전압이득 풀이로 추측하지 않는다. 이 방식에 해당하는 새/수정 문항에 표지가 빠졌으면 보완하고 세 단계의 순서를 확인한다. 연쇄 곱은 GAIN-01을 적용한 경로로 기록하고 일반 답안 단계에서 식을 확인한다. 다른 목표나 원문 지정 방법은 GAIN-01 감사에 근거를 적는다. 숨김 CSS의 실제 가시성은 브라우저에서도 확인한다.
