# manifest.json 작성 규칙 (메인 에이전트)

manifest는 이번 팩의 계약이다. 작성자, 검사기, 조립기가 모두 이 파일을 기준으로 삼는다.
정본 예시: `tests/fixtures/mini-run/manifest.json`.
작성 후 반드시 `python3 <SKILL>/scripts/manifest.py <RUN>/manifest.json <REPO>` → `OK`(REPO를 주면 문제 md가 있는지도 본다).

## 최상위
| 키 | 값 |
|---|---|
| `course` | `"전자회로2"` |
| `range` | `"0923"` 또는 `"0916-0918"` (첫 STT–마지막 STT 날짜) |
| `slug` | 이번 범위 대표 주제의 영문 밑줄 형태, 예: `"Cascode_Stage"`, `"Differential_Amplifiers"`. 두 주제에 걸치면 뒤쪽 것 |
| `note_title` | `"<주제> — 5살도 이해하는 정리노트"` |
| `note_subtitle` | `"권익진 교수님 전자회로2 · 0916 · 0918 수업 (Lec3, Razavi 9장)"` 형식 |
| `footer_note` | HTML 허용. `출처: 권익진 교수님 강의자료(LecN) · 수업 녹음 전사(MMDD…) · B. Razavi, <i>Microelectronics</i>, 2nd ed. (Wiley) N장.` |
| `sessions` | 날짜별 `{date, stt, summary, slides}` |

## sections / topics
- **첫 섹션은 항상 "왜 이런 회로를 쓸까" 페이지다**(manifest.py가 섹션 id, 토픽 id, eli5·formal 레이어를 강제). 제목과 `short`도 아래와 글자 그대로 쓴다.
  ```json
  {"id": "why", "title": "들어가며: 왜 이런 회로를 쓸까", "short": "왜 쓸까", "topics": [
    {"id": "why-circuit", "title": "왜 이런 회로를 쓸까", "required_terms": ["캐스코드", "출력저항", "헤드룸"], "layers": ["eli5", "formal", "prof"], "supp": false}
  ]}
  ```
  - 토픽은 `why-circuit` 하나. `layers`에 `eli5`, `formal`은 필수, 요약 `## 동기 발언`에 교수님 발언이 있으면 `prof`를 더한다. 수업에서 말하지 않은 동기(교과서 장 도입부)를 쓰면 `supp: true`.
  - `required_terms` 3~6개: 대표 회로 이름, 그 회로가 푸는 문제, 그 대가를 각각 1개 이상. 범위에 회로가 여럿이면 모두 이 한 페이지에 담는다.
  - 예고 토픽(`preview_topic`)이 될 수 없다. 범위의 다른 섹션(`s0`…) 안에 "왜 필요한가" 토픽을 따로 만들지 않는다.
- 그다음 섹션 id는 `s0`, `s1`, … 순서. 마지막 섹션은 항상 "요약 · 예고"이며 토픽 `s<N>-cheatsheet`, `s<N>-next`, `s<N>-links`를 둔다.
- 섹션은 **개념 순서(슬라이드 로드맵)** 로 묶는다. 날짜는 토픽 태그로만 드러낸다.
- 토픽 id는 `s<n>-<kebab>`(영문 소문자). 토픽 하나 = 슬라이드 1~3장 또는 칠판 유도 하나.
- `short`는 상단 목차 글자(예: `"2 출력저항"`), `title`은 `"2. 캐스코드의 출력저항"`.
- `layers`: 개념 토픽은 `["eli5", "formal", "prof"]`. 교수님 발언이 없으면 `prof` 대신 빼되 이유를 보고서 "스킬이 정한 사항"에 적는다. 요약에 그 토픽의 강조 발언(인용+타임스탬프)이 있으면 `layers`에 `"warn"`을 넣는다(작성자는 강조 발언을 prof가 아니라 warn에 싣는다). 요약·예고 섹션 토픽은 `[]`.
- `supp`: 요약의 `🕳️ 미룬 유도`를 보충으로 싣는 토픽만 `true`.
- `required_terms`: 토픽당 3~9개. 요약의 **용어·식 목록과 강조 발언**에서 고른다.
  - 식은 작성자가 **공백까지 그대로** 쓸 TeX 문자열이다(예: `"R_{out} \\approx g_m r_O^2"`).
  - 교수님 비유의 핵심 단어를 최소 하나 넣어 교수님 말씀(prof) 레이어 누락을 잡는다.
- `preview_topic`: `s<N>-next`.
- `forbidden_outside_preview`: 슬라이드·절 대조표에서 **"예고만"이거나, 지금까지 수업에서 아직 다루지 않은** 슬라이드·절의 핵심 용어 3~8개. 이전 수업에서 이미 배운 내용이나 이번 range의 STT에서 실제로 쓴 용어는(다른 날짜·다른 팩이라도) 절대 넣지 않는다 — "안 다룸"은 예고 없이 그냥 건너뛴 슬라이드에만 쓰고, 이미 배운 것을 다시 금지어로 넣지 않는다. 본문에 나오면 검사 실패.

## problems
- 선별은 `references/problem-selection.md`. 0~12개, 목표 10개. workbook에 맞는 문제가 없으면 `[]`.
- 항목: `{"id": "P9.05", "kind": "장말문제", "anchor": "s2-rout", "date": "0916", "why": "캐스코드 출력저항 수치 계산"}`
  - `id`: workbook id. 교과서 `E`(예제)/`X`(연습문제)/`P`(장말문제) + `장.두자리`(예: `E10.03`), 기출 `<연도>-<학기>_<중간|기말>-Q<n>`(예: `2023-1_기말-Q1`).
  - `kind`: id에서 정해진다(`E`→예제, `X`→연습문제, `P`→장말문제, 기출). 틀리면 manifest.py가 실패.
  - `anchor`: 문제가 기대는 정리노트 토픽 id. `date`: 관련 수업 날짜(MMDD).
  - `why`: 이 문제를 고른 이유 한 줄. `.assets/problems.txt`와 보고서에 그대로 쓰인다.
- 배열 순서가 PDF 순서다. 수업 순서(=토픽 순서)대로 둔다.

## links
- `href`는 작성자가 `<a href="…">`에 **글자 그대로** 넣을 값이다(검사기가 해당 `topic` 안의 링크와 정확히 비교한다).
- 문제가 1개 이상이면 `{"topic": "s<N>-links", "href": "복습문제_<range>_<slug>-문제.pdf"}`와 `…-답안.pdf` 두 항목을 **반드시** 넣는다(없으면 manifest.py 실패). 문제가 0개면 두 항목을 넣지 않는다.
- 이전 복습팩과 이어지는 개념이면 `../<이전 range>/정리노트_<이전 range>_<slug>.html#<토픽>` 링크를 건다(팩마다 `복습노트/<range>/` 폴더라 한 단계 위로 올라간다).
- 문제집 전체를 보고 싶을 때를 위해 `../../workbook/pdf/chNN-문제.pdf` 링크를 걸어도 된다(그 장을 다뤘을 때만, 파일이 있을 때만).
