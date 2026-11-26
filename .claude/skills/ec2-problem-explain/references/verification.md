# 검토 기록과 발행

참고 풀이가 없는 문항도 동일한 게이트를 적용한다. 작성자는 원문·그림에서 직접 풀며 독립 검토자는 작성자의 결과를 보기 전에 원문에서 별도 풀이를 기록한다. 회로 연결·출력 극성/정의·근사 조건을 먼저 대조하고 식·수치·단위·극한 조건을 검산한다. 단순한 같은 식의 재대입이나 참고 풀이 유무는 승인 근거가 아니다. 없음 자체는 disputed가 아니며 원문 모호·독립 풀이 불일치·검증 미완료는 해결 전 withheld다. 부모가 문항을 교체하면 새 source/build/모든 검토를 거친다. selection.json의 핵심/추가·소문항 묶음 수·추정 시간이 입력 해시와 일치하는지 확인한다. 해설 HTML·동반 MD에 학습량 행이 없는지 검사하고 PDF 표시는 기존 PDF 정책과 선발 메타데이터에 맞는지 별도로 확인한다.

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
- 간략 해설은 회로 판단, 첫 식, 필수 중간량과 답을 순서대로 확인한다. 별도 상세 풀이와 일반 공식의 반복을 제거했는지, 소문항별 답과 가정이 정확히 한 번 보이는지 읽는다. 기존 일곱 구역 자료를 재조립할 때는 기존 순서와 답안 선택을 대조한다.
- 회로 그림의 ㉠ 등 표지가 해설에서 같은 소자·노드·회로 상태를 가리키는지 확인한다. 원문 회로·개루프·시험원 조건을 구분한다.
- 독립 계산은 한 행씩 두고, 결론에 영향을 주는 유한 항·가정·단위·부호를 해당 식 곁에서 확인한다. 본문 검산은 문항의 오답을 가려내는 경우에 두며 독립 검산은 모든 소문항에 적용한다.
- 요약 sum의 개념·공식·답이 본문과 일치하는지.

추가 교육적 연결 검토:
- 핵심 규칙에서 작은 상태 변화/기호 조작, 실제 첫 식, 유도까지 이어지는지. 수치 예시 유무 자체로 판정하지 않아요.
- KCL의 방향·노드·제어 전압 정의와 가지별 전류, 시험전류 귀환 경로가 보여서 첫 식을 재구성할 수 있는지.
- 반회로 전환·병렬 공통 인자·기호 치환·차수 판단·허용된 보충 정확식에 숨은 중간 단계가 없는지. $R_{out}$ 정확식은 위 예외가 아니면 내부 검산에만 두고 본문·요약·MD·PDF에는 나타나지 않아야 해요.
- 예시가 원문 조건과 구분되고, 근사·단위·부호가 본문·요약·MD·그림에 일치하는지. 증명은 예시 뒤에도 일반 논증을 유지하는지.
- 소신호 등가회로 그림: 문항마다 start·solve가 소신호 KCL/KVL을 세우는지 먼저 판정해요. 세우는데 [저작 규칙](authoring.md)의 "소신호 등가회로 그림"이 없으면 fail이에요. 그림이 있으면 원 문제 그림과 토폴로지(어느 노드 사이에 어느 소자가 있는지, 무엇을 AC 접지로 보냈는지)가 같은지, 노드 이름·전류 방향·제어 전압 극성이 첫 KCL 식과 같은지 대조해요. 그림이 2개면 각 그림의 경계 조건(단락·무부하·CM·DM)이 해당 식과 맞는지도 봐요. 판정과 대조 결과를 evidence에 문항마다 적어요. DC KCL만 있어 제외한 문항도 이유를 적어요.
- 풀이 회로의 개인화: `CIRCUIT-02`에 따라 해당 단계의 그림에서 $G_m$의 출력 단락 접지와 전류 방향, $R_{out}$의 입력 영점·시험원을 확인해요. 해당 축퇴 구조의 입력/중앙 노드/제어원/아래 저항 배치와 노드 관계를 첫 식에 대조해요. 생략 가지·모델 조건·정확/근사 기호를 확인하고 유한 β 결과에 $v_e=i_{out}r_{o1}$를 사용하면 fail이에요. 단락을 본문에만 적은 일반 모델 그림은 통과시키지 않아요. 측정·모델별 풀이에서 조건·결과가 서로 대응하는지도 기록해요. $R_{out}$은 예외가 아닌 한 양쪽 모두 근사 모델이며 상세 정확 모델을 요구하지 않아요. 해당하지 않는 문항은 구체적 비적용 이유를 남겨요.
- 출력 배치 필수: 입력은 왼쪽, 출력 단자·출력 라벨·출력 시험원/단락 접속은 오른쪽에 둔다. 회로로 유입하는 시험전류는 오른쪽에서 왼쪽으로 그리며, 내부 제어 전류원의 방향·전압 극성·실제 접속은 유지한다. 전기적으로 같은 노드라는 이유로 출력 접속을 왼쪽이나 중앙에 두지 않는다. 풀이 본문·HTML·PDF에서 각각 확인한다.
- 병렬 가지 순서 필수: 제어 전류원과 $r_o$가 병렬이면 반드시 **제어 전류원 왼쪽 → $r_o$ 또는 병렬 합성 저항 오른쪽 → 출력 접속 맨 오른쪽** 순서로 그린다. 입력은 그 왼쪽, 이미터/소스 축퇴 저항은 해당 노드 아래에 둔다. $r_o$를 생략한 축약 모델에는 없는 저항을 추가하지 않는다. 그 모델의 제어원 위치를 병렬쌍의 배치 규칙으로 일반화하지 않는다. 풀이 본문의 모든 SVG와 답안 PDF에서 소자·단자 전체 배치를 대조하고, 전기적 등가성만으로 위치 불일치를 승인하지 않는다.
- 노드 점과 시험 표기 필수: 접지 표기만 하는 비분기 단자와 접지 기호의 직접 접속점을 제외하고, 입력·출력·시험 노드와 이름을 붙인 전압 노드에는 연결 위치가 분명한 눈에 보이는 점을 찍는다. 출력 시험전압 노드의 점은 출력 도선의 실제 맨 끝이자 가장 오른쪽 단자에 둔다. 점 오른쪽으로 도선(ink)이 더 이어지거나 연장된 도선 중간에 점이 놓이면 안 된다. 시험 노드 전압 $V_t(+)$는 그 끝점 위에 둔다. 유입 시험전류는 오른쪽에서 왼쪽으로 흐르며, 왼쪽을 향하는 $i_t$ 화살표는 $V_t$ 점 왼쪽의 도선 구간에 둔다. $i_t$ 라벨도 점 왼쪽에서 그 화살표 아래나 곁에 둔다. 화살표 전체가 점 왼쪽에 머물고 점을 덮지 않도록 화살표 꼬리와 점 사이에 작은 간격을 남긴다. 화살표나 전류 라벨을 점 오른쪽에 놓지 않는다. 다른 시험 기호($v_x/i_x$ 등)를 쓰면 같은 배치와 정의를 적용한다. 선 교차만 있고 연결되지 않은 곳에는 점을 찍지 않는다. 라이트·다크 HTML과 실제 답안 PDF에서 점·라벨·화살표의 분리와 가시성을 각각 확인한다.
- 회로 안 글자와 점의 정돈: SVG 안에는 소자 이름·값·제어 전류원 라벨(예: $g_mv_\pi$), 노드 이름·극성·방향처럼 실제 회로를 읽는 표기를 남긴다. 분석용 $G_m$ 제목·측정 조건 문구·유도 설명은 그림 아래 figcaption이나 수식 문단에 둔다. 출력 단락·입력 영점의 실제 연결은 그림에 보존한다. 접지 입력 위의 독립 제목 `Rout`처럼 불필요한 제목은 옮겨 중복하지 않고 삭제한다. 가까운 노드 관계는 유도 설명이 아니고 겹치지 않을 때만 남길 수 있다. 접지 표기만 하는 비분기 단자·접지 기호의 직접 접속점은 제외하고 입력·출력·시험 단자, 이름 붙인 내부 전압 노드, 실제 분기 접속점의 점은 유지하되 이름도 분기도 없는 직선 도선 중간의 장식 점은 없앤다. 모든 도선에 점을 추가하라는 규칙이 아니다. $V_{out}(+)$·$V_t$ 등 라벨은 아래첨자까지 포함한 실제 글리프 경계상자가 도선에서 최소 0.6em(보통 화면에서 약 8px) 떨어지게 배치한다. 텍스트 기준선 간격만 확인하지 않는다. 필요하면 라벨을 옮기고 viewBox 위쪽 여백을 늘린다. 풀이 본문의 모든 SVG를 열거하여 라이트·다크 HTML과 실제 답안 PDF의 보통 보기 크기에서 이 간격·클리핑·겹침을 확인한다. 병렬 제어원 왼쪽/$r_o$ 오른쪽/출력 맨 오른쪽, 맨 끝 $V_t$ 점 오른쪽 도선 없음, 점 왼쪽의 왼쪽 방향 $i_t$와 라벨 배치도 유지한다.
- 접지·전압 라벨·노드 색 대응: 접지 기호에 직접 닿는 점과 접지만 표시하는 비분기 입력 단자의 점은 생략한다. 접지로 이어지는 회로라도 별도의 실제 분기 접속점·이름 있는 비접지 노드는 유지한다. $v_e$ 등 전압 이름은 다른 소자나 저항 옆으로 멀리 밀지 않고 해당 노드 바로 곁에 둔다. 아래첨자·극성을 포함한 실제 글리프 경계로 도선과 최소 0.6em 간격을 확보하면서 가능하면 0.6–1em 정도의 가까운 간격을 목표로 한다. 혼잡 때문에 더 벌리면 배치 이유를 검토에 기록한다. 노드 점과 해당 전압 이름·극성은 같은 파랑 또는 빨강으로 묶는다. 주요 신호 경로를 따라 파랑·빨강을 교대하고 가까운 전압 라벨끼리 최대한 다른 색을 쓴다. 같은 전기적 노드는 다른 위치의 점도 같은 색이며, 모든 인접 노드를 반대색으로 만드는 그래프 채색을 강제하지 않는다. 접지 표기·도선·소자/제어원 라벨·전류 화살표/라벨·본문 수식의 색은 이 노드 색 규칙으로 바꾸지 않는다. 색 없이도 노드 이름과 극성으로 구분되어야 한다. SVG에는 대응 노드 식별자와 색을 명시하고, HTML 테마와 PDF에서 실제 계산된 색이 파랑/빨강인지 확인한다. PDF의 문항 종류별 초록/주황 `--kind`를 노드 파랑의 대체값으로 사용하지 않는다. 풀이 본문의 모든 SVG와 MD에 참조된 같은 그림, 라이트·다크 HTML 및 실제 답안 PDF에서 접지 점 생략·가까운 라벨·점/전압 색 일치를 검토한다.
- 출력저항 표시/검산 경계: $R_{out}$은 처음부터 유효한 근사식으로 시작하고 조건과 $\approx$를 유지한다. 이 규칙은 생성하는 풀이 본문(start/solve/verify·formal/보충 포함) HTML·요약·동반 MD·답안 PDF 모두에 적용한다. 정확식 → 근사식 유도나 정확식과 수치 비교를 학습 본문에 추가하지 않는다. 정확한 $R_{out}$의 전체 모델·유도·수치/극한 대조는 내부 독립 검산 evidence에만 둔다. 원문이 정확식·유한 β 전체 결과 또는 수업 기본 큰 곱 근사와 반대인 조건·수치를 명시하면 예외 이유를 짧게 밝히고 필요한 모델과 결과를 제시한다. 유한 β 또는 $r_o$가 있다는 사실만으로 예외를 선언하지 않는다. 이 제한은 $R_{out}$에 한정하며 다른 개념의 필요한 상세 유도를 줄이지 않는다.
- 기존 원고에 retry가 있으면 예상 답 없이 먼저 풀어 답·이유·적용 조건을 기록한 뒤 작성자 evidence와 대조해요. 값이 부족하거나 조건 밖인 질문은 보강해요. 범용 재계산 지시만 있거나 본문 복사만으로 끝나면 fail이에요.

교육적 연결 검토와 독립 수학 검산, 원문 시각 대조, 브라우저 검토는 각각 수행 사실과 범위를 기록해요. 한 검토의 통과를 다른 검토의 통과로 대신하지 않아요.

결함이 있으면 그 항목을 `fail`로 두고 작성자에게 되돌려요. 고친 뒤 build부터 다시 해요.

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
  external: performance.getEntriesByType('resource').map((e) => e.name).filter((u) => !u.startsWith(location.origin) && !['https://cdn.jsdelivr.net/npm/katex@0.16.11/','https://cdn.jsdelivr.net/npm/pretendard@1.3.9/'].some((p) => u.startsWith(p))),
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

현재 `review_policy_version`은 `problem-explain-2026-10-21-learning-style`다. 새 review.json·manifest의 버전이 일치해야 발행된다. 구버전/버전 없는 검토를 단순히 현재 버전으로 바꾸거나 pass를 복사하지 않는다. 기준 변경은 실제 content·independent 재검토를 요구한다.

content는 recall의 근거 있는 명칭 대응, pitfall의 오답 판별 기준, 부정형의 참·거짓과 선택 적합성, understand·solve·verify·pitfall·sum의 결함 공개·공식 답 확인 여부가 일관적인지 확인한다. 과목별 disputed 규칙은 유지한다. 독립 검산은 작성자와 다른 검산자가 정답·참고 풀이·설명 조각을 보지 않고 문제·그림·필요한 이론 자료만으로 먼저 수행한다. 컨트롤러가 그 결과를 참고 답과 대조한다.

rerender의 검토 재사용은 동일한 입력·조각·입력 그림과 무결한 발행 자료, 검증된 모든 참조, 같은 검토 기준을 전제로 한다. 참조가 없거나 바뀌면 content·independent도 not_run으로 두고 다시 검토한다. 전자회로2는 problems.txt가 같더라도 문제 MD·그림이 바뀌면 재사용하지 않는다. source_visual·browser는 매번 새 stage에서 수행한다. 구조 검사는 내용 검증이 아니다.

browser는 1280×900·1024×900·375×812, light/dark에서 실제 확인한다. 1023→1024 경계에서 목차·문제 기본 열림, 저장한 닫힘 유지, 원문 탭(원문 없는 문항은 숨김), 문제 패널 왼쪽·오른쪽 붙이기·띄우기, 이동·크기 조절·화면 내 제한, 모바일 접힘, 그림 확대와 인쇄 문제/원문 보존을 확인한다. 유효한 객관식은 오답·정답·다시 풀기·판정 이동, 모델 없는 문항은 정적 표시를 확인한다. 코드 문자·들여쓰기·수식·소문항·원문을 보존하고 외부 요청·콘솔/KaTeX 오류·누락 자원·문서 가로 넘침은 0이어야 한다.

참조 HTML·MD·SVG가 로컬 그림을 사용하면 해당 그림도 references에 절대 경로와 SHA-256으로 별도 기록한다. 참조 그림 해시 누락·변경은 검토 재사용과 새 발행을 막는다. 옮긴 그림의 이전 바이트를 확인할 수 없으면 현재 파일을 자기 자신과 비교해 같은 그림이라고 간주하지 않는다.

## 본문과 페이지 요약의 계약

요약은 시험 직전 확인할 핵심만 남긴다. 기본 구성은 핵심 한 문장 → 필요한 식 1~3개 → 판단 기준 1~3개이며 권장 분량이지 할당량이나 강제 상한이 아니다. 반복 예시·유도·중복 용어 풀이·일반적인 경고는 본문에 둔다. 식의 적용 여부나 답의 부호를 바꾸는 조건은 해당 식 옆에 압축한다. 본문에 없는 사실을 추가하지 않는다. 모든 본문 주장을 요약에 복제하지 않고 핵심의 일치·오해 가능성·중복 여부를 검토하며 생략 이유는 감사 기록에 남긴다.

요약의 문장은 각각 별도 `<p>`로 작성하며 한 문장에는 하나의 판단을 담는다. 마침표로 문장을 실행 중 자동 분리하지 않는다(소수·약어·TeX 보존). 자연스러운 화면 줄바꿈은 허용한다. 의미가 나뉘면 짧은 소제목의 `summary-group`으로 묶되 단순 요약에 소제목을 늘리지 않는다. 제목 아래 12px, 그룹 사이 24px, 문장 문단 사이 8px을 공통 템플릿이 처리하며 빈 문단·연속 `<br>`로 간격을 만들지 않는다. 긴 식은 하나의 `aligned` 안에서 관계를 유지하며 나눈다. 중앙 제목·고정 패널 제목과 유일한 `.sums#sum-for`, 문제·원문 탭·앵커·저장 키를 보존한다.

공개 학습 HTML·요약·동반 MD·툴팁·접근성 문구에는 STT 줄 번호·Part·타임스탬프·시각 정보 유무를 출력하지 않는다. 근거 위치는 별도 검토 기록에만 보관한다. 해설 HTML·동반 MD의 학습량 행(핵심/추가 연습·소문항 묶음·예상 시간)은 생성하지 않고 선발 JSON에는 유지한다. PDF 규칙은 이 HTML 가독성 변경으로 바꾸지 않는다.

모든 학습 토픽에 대해 자료·토픽별 일반·강조·주의·보충의 서로 다른 핵심을 별도 행으로 감사한다. 본문 주장·대응 요약 문장·판정/생략 이유와 `pass | unresolved`를 기록하고 보완 뒤 실제 요약을 다시 읽는다. 기존 동반 MD와 재생성 원고를 동기화하되 없는 MD 형식을 만들지 않는다. 검증 JSON은 `{schema_version:1, html, html_sha256, audit_path, audit_sha256, semantic_status, browser_status, evidence, unresolved}`이며 실제 검사 뒤에만 상태를 갱신한다. 파일 해시 변경 후 기존 증거는 갱신 전까지 오래된 근거다.

1280×900·375×812와 light·dark 네 조합에서 실제 패널을 열고 서로 다른 두 토픽의 요약 전환, 이전 요약 숨김, 표지 안내, 중앙 제목 유지·우측 중복 제목 없음, 유일한 `#sum-for.sums`, 패널 내부 가로 넘침 없음과 수식·콘솔 오류 0을 확인한다. 문제설명은 문제·원문 탭과 이전/다음 이동도 확인한다. 읽음·푼 문제 저장 키와 payload가 이동·새로고침 뒤 유지되는지 검사하며 missing-sum 검사는 계속 실패를 탐지해야 한다.

## 통합 구조 지원 확인

간략 해설과 기존 원고를 각각 해당 구조로 검토한다. 공통 도구는 본문의 선택 표지에서 overlay를 추출한다. 선택 요소가 해당 소문항의 회로·조건·계산·최종 답을 보존하는지 대조하며 누락·중첩·불명확한 범위이면 정상 publish는 withheld다. 구형 표지를 숨겨 중복 풀이를 끼워 넣거나 예전 validation을 승인으로 재사용하지 않는다. 변경된 명세 snapshot은 새 저작/내용 감사 대상이며 과거 발행물의 열람은 유지한다.

## 생성 회로 수식과 표시 제목 검토

- PROFILE CIRCUIT-02에 따라 $g_mr_o\gg1$, $g_mR_e\gg1$의 주항을 쓰고 캐스코드 곱 인자의 소자 번호를 확인한다. 외부 축퇴 저항과 내부 $r_e=1/g_m$를 구분하고, 유한 $r_\pi$를 임의로 제거하지 않는다. 원문이 반대 조건·수치 또는 정확 결과를 명시한 경우만 예외를 기록한다.
- 생성한 모든 SVG의 `<text>`를 열거한다. `vCM`, `gm`, `ro3`, 밑줄 기호·유니코드 가짜 첨자 `ₘ/₃/꜀`가 남지 않고 native `text/tspan`의 실제 sub/super 구조인지 확인한다. `$...$`를 텍스트로 남기거나 `foreignObject`의 수식 실행에 의존하지 않는다. 원문 인용·원본 이미지의 표기는 보존한다.
- 회로 라벨 전체의 실제 Pretendard SemiBold face·computed weight 600·정체(변수 포함)·기본 78% 실제 첨자를 확인한다. CSS 선언만 확인하지 않고 독립 SVG의 포함 글꼴 및 PDF 임베딩을 확인한다. HTML 라이트·다크, 모바일·데스크톱, 추출 SVG와 MD의 해당 그림, 실제 답안 PDF에서 첨자 높이·노드 색·라벨/도선 겹침·잘림을 각각 검사한다.
- `.assets/display-titles.json`의 ID 집합·순서별 번호를 대조한다. 제목은 목차·본문·MD·문제지·답안지에서 같은 `P<n>. 짧은 제목`이며 Fig 번호를 포함하지 않는다. 출처/원문 영역의 원래 교과서·기출 식별자는 보존한다. 제목 맵은 입력 해시에 포함되어야 하며 변경 전 승인으로 발행하지 않는다.

- 새/수정 CM 전압이득 본풀이가 성립 조건 → $2R_{SS}$ 반회로 → 출력 단락 $G_m$ → 입력 영점·부하 포함 $R_{out}$ → 부호 있는 곱 순서인지 확인한다. CM을 가상 접지로 두지 않았는지, 불일치에서 같은 가지 전류 모델이 유효한지, 전류 거울 결합을 보존했는지 확인한다. 테일 저항 상세 유도는 뒤의 보충이며 원문 지정 증명·방법은 유지한다.

## 가독성 화면 확인

모든 토픽을 데스크톱·모바일과 라이트·다크에서 순회한다. 요약 문장은 별도 문단에서 시작하고(8px 간격), 제목 아래 12px·의미 그룹 사이 24px인지 실제 경계상자로 측정한다. solve의 첫 직계 소문항은 제목 뒤 24px, 동급 사이는 화면 너비 1024px 이상에서 32px·그 미만에서 24px이며 마지막 문단 여백과 중복되지 않아야 한다. 긴 식의 잘림, 목록·정의 목록, 소제목 이전 줄바꿈, 숨긴 요약이 본문에 남지 않는지 확인한다. 학습량 행과 공개 STT 위치 정보는 HTML·MD·툴팁·접근성 문구에 없어야 한다. Pretendard 및 회로 Pretendard 600을 유지하고 문항 순서·답·원문 탭·저장 상태를 보존한다.


**전압이득의 계산 순서:** 새로 작성하거나 내용을 고치는 적용 가능한 증폭기 전압이득 풀이는 PROFILE GAIN-01에 따라 성립 조건·입출력 정의 → 출력 단락의 $G_m$ → 입력 영점·시험원의 부하 포함 $R_{out}$ → 부호 있는 $A_v=-G_mR_{out}$ 순서로 쓴다. 짧게 푸는 것은 대수 전개를 줄이는 것이며 세 중간 계산을 생략하지 않는다. 같은 출력 정의에서 증폭기 쪽 근사 저항과 외부 부하의 병렬을 보인다. 필요한 유한 $r_\pi$·$r_o$와 원문 조건을 유지하고 $R_{out}$ 정확 전체식·긴 노드방정식은 예외가 아니면 내부 검산에 둔다. 순수 DC·전류 전달/트랜스임피던스·원문 지정 증명은 해당 목표와 방법을 유지한다. 기존 미수정 문항 전체에 소급 재작성을 강제하지 않는다.


### 새/수정 Gm–Rout 경로의 구조 검사

적용되는 새/수정 전압이득 경로에는 `data-gain-route="gm-rout"`와 그 안의 `data-gain-stage="gm"`, `"rout"`, `"gain"`을 사용한다. 수정하지 않는 기존 문항의 표지 없는 본문은 보존하고 사람 검토 범위로 남긴다. 세 단계는 같은 경로에 각각 한 번, 그 DOM 순서로 두고 각 단계의 제목 밖에 보이는 비어 있지 않은 `$...$` 또는 `$$...$$` 중간 수식을 쓴다. 경로를 중첩하거나 수식을 숨기지 않는다. 기존 보이는 `data-answer-step` 요소 안에도 넣을 수 있으며 새 본문이나 두 번째 풀이를 만들지 않는다. 이 속성들은 표시/MD 내용이나 답안 선택 의미를 바꾸지 않는다.

공통 HTML 검사와 EPE 조각 계약은 선언된 경로의 누락·순서·빈 식·명시적 숨김을 검사한다. 식의 정당성·입출력과 측정 조건·외부 부하 병렬·부호·필요한 유한 β/ro는 사람이 검토한다. 표지가 없는 과거 문장을 정규식으로 전압이득 풀이로 추측하지 않는다. 표지가 없는 새/수정 적용 문항은 내용 검토자가 표지를 보완한 뒤 같은 순서를 직접 확인하고, 비적용이면 GAIN-01 감사에 목표/원문 지정 방법을 구체적으로 기록한다. 숨김 CSS의 실제 가시성은 브라우저에서도 확인한다.
