# 문제집 PDF 생성기

문제 md(교과서 `교과서/마이크로전자회로/chNN`, 기출 `from_the_past/md/<회차>`)를 문제지·답안지 PDF로 만든다.
설계는 `docs/superpowers/specs/2026-09-25-workbook-pdf-build-design.md`에 있다.

## 준비
```bash
pip3 install --user --break-system-packages playwright
```
브라우저는 설치된 Google Chrome을 쓴다(`playwright install`은 하지 않는다). 빌드 중에 CDN에서 Pretendard와 KaTeX를 받으므로 인터넷이 필요하다.

## 사용법
```bash
python3 workbook/build_workbook.py ch09                                  # 교과서 장 (책 순서)
python3 workbook/build_workbook.py 2023-1_기말                           # 기출 회차
python3 workbook/build_workbook.py --ids P9.05,E9.01,2023-1_기말-Q1 --name 샘플
python3 workbook/build_workbook.py --all                                 # 모든 장과 기출
```
- `--json-only`: PDF 없이 JSON·HTML만 만든다.
- 결과:
  - `workbook/pdf/<이름>-문제.pdf`, `<이름>-답안.pdf` — 커밋한다. md를 고치면 다시 만들어 함께 커밋한다.
  - `workbook/build/` — JSON·HTML 중간 산출물. git이 무시한다.
- 종료 코드:
  - 0: 성공
  - 1: md 오류(`ERROR` 줄), 렌더링 실패, 쪽 넘침(`OVERFLOW <파일>: <id>` 줄. PDF는 남는다)
  - 2: 사용법·대상 오류

## md에서 PDF로 가는 것
| PDF | md |
|---|---|
| 문제 원문 | `## 원문` (없으면 블록을 숨김) |
| 조건 / 구할 것 | `## 조건` / `## 구할 것`. 문제 그림이 있으면 `- 회로:` 줄은 뺀다(값 `=`·`%`·`≈`·수식 속 숫자가 적힌 줄은 남김). 이미지 줄은 뺀다. `(원문에 없음)`·`(원문의 …)`·`(보조 출처: …)`도 뺀다 |
| 그림 | frontmatter `figures`의 `role: problem` 그림 (크기 = 픽셀 / dpi × 25.4 mm) |
| Hint 띠 / Hint 쪽 | `## 힌트`의 `### ` 소절 (`> 띠: $…$` 줄이 띠에 보인다) |
| 풀이 / 답 | `## 풀이`의 `### ` 소절, 마지막 `### 답`. 없고 예제면 `## 답 (검증용)` |

절 문법은 `교과서/마이크로전자회로/FORMAT.md`의 '문제집용 절'에 있다.

## 템플릿
- `templates/problem.html`, `templates/answer.html`. 데이터는 `<script id="workbook-data">` 안의 `__WORKBOOK_DATA__` 한 곳에 들어간다.
- 미리보기: `python3 -m http.server -d workbook/templates 8765`를 띄우고 http://localhost:8765/problem.html?data=sample-problem.json 을 연다. 답안지는 `answer.html?data=sample-answer.json`이다.
- 템플릿을 고친 뒤에는 아래 테스트(실제 Chrome 스모크 렌더링 포함)를 돌린다.

## 테스트
```bash
python3 -m unittest discover -s workbook/tests
```

## 원문 옮기기 도구
`source_pages.py`는 md frontmatter의 `pdf_page`로 원본 PDF 쪽을 찾는다. 규칙은 `교과서/마이크로전자회로/FORMAT.md` '문제집용 절'.
```bash
python3 workbook/source_pages.py next 교과서/마이크로전자회로/ch10 --size 10   # 다음 배치 (원문 없는 md)
python3 workbook/source_pages.py missing from_the_past/md/2023-1_기말           # 남은 것 (있으면 종료 코드 1)
python3 workbook/source_pages.py render <md…> --out /tmp/pages                  # pdf_page·다음 쪽 PNG (+ 글자 층 .txt)
python3 workbook/source_pages.py next 교과서/마이크로전자회로/ch10 --ledger docs/superpowers/reports/ch10/hints-ledger.md --size 15   # 힌트 판정 안 된 md
python3 workbook/source_pages.py missing 교과서/마이크로전자회로/ch10 --ledger docs/superpowers/reports/ch10/hints-ledger.md          # 남은 것 + MISMATCH
```
힌트 판정 원장의 줄 형식은 `- <id> | 힌트 <1|2> | <이유>` 또는 `- <id> | 없음 | <이유>`다. 목록 기호나 `|`가 든 줄은 모두 이 형식이어야 한다(틀리면 `ERROR`). 힌트는 없어도 되는 절이라, 검토가 끝났는지는 md가 아니라 원장으로 판단한다.
