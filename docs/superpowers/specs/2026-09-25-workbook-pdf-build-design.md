# 문제 md → 문제지·답안지 PDF 빌드 설계

## Intent
교과서 문제 md(377개, ch09–ch11)와 기출 문제 md(22개)는 지금처럼 md를 원본으로 둔다. 여기에 문제집용 선택 절 `## 원문`, `## 힌트`, `## 풀이`를 추가하고, md를 문제집 템플릿 두 개(문제지·답안지)가 읽는 `#workbook-data` JSON으로 바꿔 PDF를 만드는 생성기를 새로 만든다. 사용자는 이 저장소 주인인 수강생 본인이다. `python3 workbook/build_workbook.py ch09` 한 줄로 9장 문제지·답안지 PDF가 쪽 넘침 없이 나오면 완료다. 새 절이 비어 있으면 템플릿이 알아서 숨기거나 빈 칸으로 둔다.

원래 요청은 독립 작업 넷이 묶여 있다: ① 형식 확장과 생성기, ② 원문 OCR, ③ 힌트 채우기, ④ 풀이 생성·검증. **이 설계는 ①만 다룬다** [confirmed]. ②–④는 ①이 정한 절을 채우는 콘텐츠 작업이다.

분류: architectural. 새 하위 시스템(생성기, 템플릿 주입, PDF 렌더링)과 새 md 절 계약이 생긴다.

## 조사 사실
| 대상 | 사실 |
|---|---|
| 템플릿 | `~/Downloads/template_problem.html`, `template_answer.html`(최종본). 둘 다 `<script type="application/json" id="workbook-data">`에 샘플 JSON(12문제)이 들어 있다. `loadData`는 내용이 `__WORKBOOK_DATA__`이면 `sample.json`을 읽고, `?data=<url>` 쿼리도 받는다. 끝나면 `html[data-ready]`('true' / 'error'), `body[data-overflow]`(넘친 쪽 id를 쉼표로 이음)를 둔다 |
| 이전 템플릿 | 워크트리 `전자회로2-workbook`(브랜치 `workbook-template`)의 `교과서/마이크로전자회로/_tools/workbook/template.html`은 옛 v3다. 이번 작업은 Downloads 최종본을 쓴다 |
| 샘플 JSON | 12문제의 기계적인 필드(id, kind, number, title, section, book_page, difficulty, sol, depends_on, figures의 src·w_mm·h_mm)가 md·PNG에서 만든 값과 모두 같다(PNG base64도 바이트 단위로 같다). 조건은 6문제(E9.01, E11.18, P9.07, P10.32, P9.09, E9.07), 구할 것은 10문제(P9.05, P10.32 제외)가 규칙 변환 결과와 같다. 나머지는 손으로 다듬은 것이다 |
| 템플릿 JS | `KIND_SLUG`에 `기출`이 없다. `head-info`가 `` `${p.section} · p.${p.book_page} · …` ``로 고정돼 있다. 원문 블록의 lang이 `'en'`으로 고정돼 있다. 답안 템플릿의 힌트 `formula`는 문자열만 받는다. `solution`이 없으면 빈 점 격자, `hints: []`이면 Hint 띠를 숨긴다 |
| 그림 크기 | `w_mm = PNG 픽셀 / dpi × 25.4`를 소수 첫째 자리로 반올림한다(fig9-43.png 200px @144dpi → 35.3). dpi는 각 `figures/figures.yaml`의 `dpi` |
| md 문법 | 조건·구할 것·답 절에 쓰인 것: `- ` 목록(0칸·2칸 들여쓰기), 목록 아래 2칸 들여쓴 `$$…$$`와 이어지는 글 줄, 들여쓰지 않은 `$$…$$` 줄. 답 절에는 `### 정답 회로`, spice 블록, `> 참고:`도 있다 |
| 작성자 표시 | `(원문에 없음)` 297회 외 변형이 여러 개 있다. `- 회로:` 줄이 186개 있다 |
| 도구 | `markdown`, `mistune`, `pytest`, `playwright`가 설치돼 있지 않다. Homebrew Python 3.14는 EXTERNALLY-MANAGED이고, PyYAML은 `--user`로 설치돼 있다. `pip3 install --user --break-system-packages playwright`는 dry-run에서 통과한다. Google Chrome 153이 설치돼 있다 |
| 테스트 | 교과서 도구 79개, 기출 도구 65개가 통과한다(unittest) |

## Behavior when done
- `python3 workbook/build_workbook.py ch09`를 실행하면 `workbook/pdf/ch09-문제.pdf`와 `ch09-답안.pdf`가 나온다. 중간 산출물 `workbook/build/ch09-문제.json`, `.html` 등도 남는다.
- `2023-1_기말`처럼 기출 폴더 이름을 주면 그 회차가, `--ids P9.05,E9.01 --name 샘플`을 주면 고른 문제가, `--all`을 주면 모든 장과 기출이 PDF로 나온다. `--json-only`는 PDF 렌더링을 건너뛴다.
- 지금 데이터로 만들면 원문 블록과 Hint 띠가 없다. 답안지에서 예제는 `## 답 (검증용)`의 답만 나오고, 나머지 문제는 빈 격자다.
- md 오류가 있으면 `ERROR <파일>: <이유>`를 모두 출력하고 종료 코드 1을 낸다. 쪽이 넘치면 `OVERFLOW <이름>: <id>`를 출력하고 종료 코드 1을 내며, PDF는 확인용으로 남긴다. playwright나 Chrome이 없으면 설치 명령을 안내한다.

## Not in this round
- 원문 OCR(②), 힌트 내용(③; `상속·참조`의 식 줄로 초안 만들기 포함), 풀이 생성(④; 기출 md에 풀이를 허용하는 규칙 변경 포함).
- 샘플처럼 조건을 문제마다 손으로 다듬는 일. 이번에는 규칙으로 할 수 있는 정리만 한다.
- 기출 지원을 넘어서는 템플릿 디자인 변경.
- `role: answer` 그림(풀이 그림)을 답안지에 넣는 일(④).

## Approaches
| Option | Approach | Pro | Con | Chosen |
|---|---|---|---|---|
| A | md를 원본으로 두고 새 절을 추가, 생성기가 빌드할 때 JSON을 만든다 | 읽기·diff·리뷰 파이프라인, `check_md`/`make_index`를 그대로 쓴다. 넷리스트·배치 설명이 남아 풀이 검증에 쓸 수 있다 | md 하위 문법 파서를 직접 써야 한다 | ✔ |
| B | 문제마다 JSON 파일로 옮겨 원본으로 삼는다 | 템플릿에 바로 넣을 수 있다 | HTML과 `\\` 이스케이프가 섞여 사람이 편집·검토하기 어렵다. 기존 도구 4개와 FORMAT을 다시 만들어야 한다 | — |
| C | md 옆에 힌트·풀이용 YAML/JSON 파일을 둔다 | 기존 md를 건드리지 않는다 | 한 문제가 두 파일로 갈라진다. YAML 안의 LaTeX는 따옴표 문제가 생긴다 | — |

## 설계

### md 절 계약 (FORMAT.md '문제집용 절', 기출도 같음)
- `## 원문`(선택): H1 바로 다음 첫 절. 인쇄된 문장을 글자 그대로 옮긴다. 문단은 빈 줄로 나눈다.
- `## 힌트`(선택): 본문 끝, `## 풀이`보다 앞. 힌트 하나는 `### <이름표>` 소절이다. 소절 안의 `> 띠: $<LaTeX>$` 줄(선택)은 `formula`가 되고, 나머지 줄은 `html`이 된다.
- `## 풀이`(선택): 본문 맨 끝. 단계 하나는 `### <이름표>` 소절이고, 마지막 소절 하나만 `### 답`이다.
- `check_md.check_body()`(기출 검사기도 이 함수를 씀)가 위치, 중복, 빈 절·소절, 띠 줄 형식, `### 답`을 검사한다.

### md → JSON 매핑
| JSON | 출처 |
|---|---|
| `id, kind, number` | frontmatter |
| `title` | H1의 첫 ` — ` 뒤 |
| `section` | 교과서는 frontmatter. 기출은 `"<exam.yaml exam> · <points>점"` |
| `book_page` | 교과서는 frontmatter, 기출은 `null` |
| `difficulty, sol` | 장말문제는 frontmatter, 나머지는 `null` |
| `original_lang` | frontmatter `source_lang` |
| `html.original` | `## 원문`이 있을 때만(문제지). 답안지에서는 뺀다 |
| `html.conditions` | `## 조건`. 문제 그림이 하나라도 있으면 `- 회로:` 줄과 그 아래 들여쓴 줄을 뺀다. 작성자 표시를 지운다 |
| `html.ask` | `## 구할 것`. 작성자 표시를 지운다 |
| `figures[]` | `role: problem` 그림을 id 중복 없이 frontmatter 순서대로. `src`는 PNG base64 data URI, `w_mm`·`h_mm`는 위 공식 |
| `depends_on[]` | `{id, in_file: 같은 묶음에 있는지}` |
| `hints[]` | `## 힌트`, 없으면 `[]`. `label`은 inline HTML, `formula`는 있을 때만 넣는 문자열 |
| `solution` | 답안지만. `## 풀이`가 있으면 `{steps, answer}`. 없고 예제면 `{steps: [], answer: <## 답 (검증용)의 정답 회로·spice·> 참고 앞 글>}`. 둘 다 없으면 키를 넣지 않는다 |
| `meta` | `{mode, title, chapter, total}`. title은 장 README H1에서 ` — 문제 인덱스`를 뗀 것, 기출은 exam.yaml `exam`, `--ids`는 `--name`. 답안지는 뒤에 ` 답안`을 붙인다. chapter는 장 번호, 그 밖에는 0 |

작성자 표시: `(`…`)` 괄호 쌍(한 줄 안, 안쪽 괄호 없음) 가운데 `원문에 없음`, `원문의 `, `보조 출처`를 담은 것과 그 앞 공백. 수식을 먼저 가려 두고 지우므로, 수식 안은 바뀌지 않고 수식을 품은 표시도 지워진다.

answer HTML: 비어 있지 않은 줄이 하나면(`- `를 떼고) inline, 여러 줄이면 목록·문단 HTML.

### md 하위 문법 → HTML (`workbook/mdsub.py`, 의존성 없음)
- `- ` 목록은 2칸 들여쓰기마다 한 단계. 두 단계 이상 건너뛰면 한 단계로 본다.
- 목록 아래 들여쓴 목록 아닌 줄은 그 항목에 공백으로 이어 붙인다.
- 들여쓰지 않은 줄은 문단이고, 빈 줄이 블록을 나눈다. `**x**`는 `<b>`(수식 밖만).
- `& < >`는 수식 안팎 모두 이스케이프한다(KaTeX auto-render는 텍스트 노드를 읽는다). 수식은 그대로 둔다.

### 템플릿 (`workbook/templates/`)
- Downloads 최종본을 `problem.html`, `answer.html`로 복사한다. 샘플 JSON 자리를 `__WORKBOOK_DATA__`로 바꾸고, 샘플은 `sample-problem.json`, `sample-answer.json`으로 뺀다. 미리보기는 `problem.html?data=sample-problem.json`으로 한다(템플릿의 `?data=` 지원).
- 기출 지원을 위해 최소한만 고친다(두 파일 모두) [confirmed]:
  - `--kind-exam: #7A4FA0` 토큰과 `[data-kind="exam"]` 규칙을 추가한다.
  - `KIND_SLUG`에 `'기출': 'exam'`을 넣는다.
  - `head-info`는 있는 값만 ` · `로 잇는다.
  - problem.html의 원문 블록 lang은 `p.original_lang || 'en'`으로 바꾼다.

### 주입과 렌더링 (`workbook/render.py`)
- 템플릿에서 `__WORKBOOK_DATA__`는 정확히 한 번 나와야 한다. JSON(`ensure_ascii=False`)의 `<`를 모두 `<`로 바꿔 넣는다. 그러면 `</script>`나 `<!--`가 데이터에 있어도 스크립트가 끊기지 않는다.
- Playwright(python)를 `channel="chrome"`으로 써서 설치된 Chrome을 쓴다(브라우저를 따로 받지 않는다).
  - viewport 1400×1000을 쓴다(화면 배율 1).
  - `html[data-ready]`를 기다리고, `'true'`가 아니면 실패로 처리한다.
  - `body[data-overflow]`를 읽어 돌려준다.
  - `page.pdf(prefer_css_page_size=True, print_background=True)`로 출력한다(`@page` 297×210mm).
- 빌드할 때 CDN(Pretendard, KaTeX)을 받으므로 인터넷이 필요하다.

### 파일 배치
```
workbook/
  README.md  paths.py  mdsub.py  problem.py  assemble.py  render.py  build_workbook.py
  templates/{problem,answer}.html, sample-{problem,answer}.json
  tests/test_{mdsub,problem,assemble,render,build}.py
  pdf/        # 커밋한다 [confirmed #N5]
  build/      # .gitignore
```
`paths.py`가 `교과서/마이크로전자회로/_tools`와 `from_the_past/md/_tools`를 sys.path에 넣고, `check_md`(split_frontmatter, split_sections, split_subsections, check_workbook_sections, HINT_FORMULA_RE), `crop_figures.figure_filename`, `crop_exam.figure_filename`을 가져다 쓴다(`check_exam.py:17`과 같은 방식).

### CLI 선택
- `chNN`: 책 순서. 예제와 연습문제를 번호순으로 섞고(E9.01, X9.01, E9.02 …) 장말문제를 뒤에 둔다.
- 기출 폴더: `Q<n>.md`를 번호순으로. 다른 md는 무시한다(`verify_exam.py`가 따로 잡는다).
- `--ids`: 적은 순서대로.
- `--all`: 모든 `chNN`, 그다음 모든 기출 폴더.
- 경로 이름은 NFC로 맞춘다(macOS NFD 경로).

## Decisions
### Confident
| # | Decision | Answer | Rationale |
|---|---|---|---|
| 0 | 접근 | A | 위 표 |
| 1 | 원본 저장 형식 | md를 유지하고 JSON은 산출물로 | `in_file`, base64, mm는 묶음에 따라 정해진다. 템플릿 `loadData`도 주입을 전제로 한다 |
| 2 | 새 절 위치 | 원문은 맨 앞, 힌트·풀이는 맨 뒤 | 템플릿 표시 순서와 같고, FORMAT.md의 기존 절 순서와 충돌하지 않는다 |
| 3 | 빈 힌트·풀이 | `[]` 또는 키 생략 | 템플릿이 이미 처리한다(샘플 X11.01, `solutionArea`) |
| 4 | `formula` 타입 | 문자열 하나 | 답안 템플릿은 문자열만 받는다 |
| 5 | md → HTML | 직접 만든 최소 변환기 | 설치된 파서가 없고, 일반 md 파서는 LaTeX의 `_`와 `\`를 망가뜨린다 |
| 6 | 그림 크기 | `px / dpi × 25.4` | 샘플 12문제의 값과 모두 같다 |
| 7 | 넣을 그림 | `role: problem`만, id 중복 제거 | 샘플 E9.07에는 문제 그림 하나만 있다 |
| 8 | 템플릿 보관 | `workbook/templates/`, 샘플은 따로 뺀다 | 자리표시자 계약과 `?data=` 미리보기 |
| 9 | PDF 렌더링 | Playwright + 설치된 Chrome | `data-ready`를 기다리고 넘침을 읽으려면 필요하다. CLI의 `--print-to-pdf`로는 할 수 없다 |
| 10 | 새 절 검사 위치 | `check_body()` 한 곳 | 교과서와 기출이 함께 쓴다 |
| 11 | 넘침 | 목록을 출력하고 종료 코드 1, 파일은 남긴다 | 잘린 쪽을 조용히 내보내지 않는다 |
| 12 | JSON 주입 이스케이프 | `<` → `<` | `</script>`, `<!--` 모두 안전하고 JSON으로도 유효하다 |

### Needs you (답변 반영)
| # | Decision | 값 | 상태 |
|---|---|---|---|
| N1 | 이번 범위 | ① 형식 확장과 생성기만 | [confirmed by default] |
| N2 | PDF 한 권의 기본 단위 | 장 하나(책 순서) 또는 기출 한 회차 + `--ids` | [confirmed by default] |
| N3 | 조건 자동 정리 | `- 회로:` 줄(문제 그림이 있을 때)과 작성자 표시를 지운다 | [confirmed by default] |
| N4 | 기출 템플릿 수정 | 이번에 포함, 색 `#7A4FA0` | [confirmed by default] |
| N5 | 생성된 PDF | **커밋한다**: `workbook/pdf/`. 중간 산출물 `workbook/build/`는 gitignore | [confirmed] (제안은 gitignore였다) |
