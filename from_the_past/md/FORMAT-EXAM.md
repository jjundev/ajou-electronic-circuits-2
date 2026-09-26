# 기출문제 MD 형식

본문 형식(조건, 구할 것, 상속·참조, 회로 절, 넷리스트, bullet 3개, 수식, 원문에 없는 보충, 원문 오식)은
[교과서 FORMAT.md](../../교과서/마이크로전자회로/FORMAT.md)를 **그대로** 따른다. 이 문서는 기출만 다른 점을 적는다.

## 폴더와 파일 이름
```
from_the_past/md/
  FORMAT-EXAM.md, README.md
  _tools/crop_exam.py         # figures.yaml → 그림 PNG (그림마다 pdf 경로)
  _tools/check_exam.py        # 파일 단위 형식 검사
  _tools/make_exam_index.py   # frontmatter + exam.yaml → <시험>/README.md
  _tools/verify_exam.py       # 시험 단위 검사 (번호, 그림, 절 순서, exam.yaml, README, --recrop)
  <YYYY>-<학기>_<중간|기말>/
    exam.yaml                 # 시험지 머리 문구, 원본 PDF, 메모
    README.md                 # make_exam_index.py로 생성, 손으로 고치지 않음
    Q<n>.md                   # 문제 번호 그대로 (Q1, Q2, … Q10), 앞에 0을 채우지 않음
    figures/figures.yaml, figures/fig-Q<n>.png
```

## frontmatter
```yaml
id: 2021-1_중간-Q2        # <시험 폴더>-Q<n>
kind: 기출
exam: "2021-1 중간고사"   # 폴더에서 정해짐: <YYYY>-<학기> <중간|기말>고사
number: "2"               # 반드시 따옴표
points: 20                # 원문 배점 (정수)
source: ../../2021중간_기말/중간/Midterm0422_1p_rev.pdf   # md 기준 상대 경로. 문제 문장이 시작하는 PDF
pdf_page: 1               # 그 PDF의 페이지(1부터)
source_lang: ko
figures:                  # 크롭 그림. id 는 반드시 따옴표. role 은 problem 만
  - {id: "Q2", role: problem, panels: [a, b]}
textbook_chapters: [9, 10]   # 관련 교과서 장 (작성자 판단). 없으면 []
depends_on: []            # 같은 시험 안의 id만 (예: [2021-1_중간-Q2])
refs: []                  # 다른 시험·교과서 문제·식 (자유 문자열, 예: "교과서 P9.04", "2021-1_기말-Q3과 같은 회로")
```
- `textbook_chapters`는 문제가 다루는 내용이 교과서 몇 장인지를 적는다. 교과서 문제 md가 아직 없는 장(12장 이후)도 번호로 적는다.

## 본문 절 — 교과서와 다른 점
- 제목: `# 기출 2021-1 중간 2 — <짧은 제목>`
- `## 조건`: 모든 소문항에 공통인 값을 먼저 적고, 소문항 하나에만 붙은 값은 `- (1) 전용: …` bullet으로 적는다. 원문 줄바꿈 위치가 아니라 **어느 소문항에 인쇄돼 있는지**로 나눈다.
- `## 구할 것`: 원문 소문항 번호 (1)(2)…를 그대로 쓴다. 회로 패널 (a)(b)와 헷갈리지 않게 한다. 배점은 적지 않는다(frontmatter `points`).
- 서술형 문제(회로 없음): `## 회로 — 없음 (서술형)`. 소문항 중 일부만 회로를 쓰면 회로 절을 두고, 서술형 소문항은 구할 것에만 적는다.
- `## 답` 절은 두지 않는다. 풀이와 답은 `## 풀이`(마지막 소절 `### 답`)에 쓴다.
- 문제집용 절 `## 원문`, `## 힌트`, `## 풀이`는 교과서 FORMAT.md의 '문제집용 절'을 그대로 따른다. 풀이 내용 규칙은 `.claude/skills/workbook-solution/references/rules.md`에 있다. 원문은 인쇄된 글자만 옮기고(손글씨 제외), 가려서 읽을 수 없는 글자는 `[판독 불가]`로 적는다. 2023-1 기말도 스캔(`기말고사.pdf`)에서 인쇄된 글자를 옮긴다. `2023 전회2 기말.hwp`는 본문 글이 거의 없고 그림만 들어 있으며, `23-1.pdf`는 2021-1 기말 문제지라 글자 원본으로 쓰지 않는다.
- 시험지 머리 문구("Closed book, 풀이과정 필수 …")는 문제 md가 아니라 `exam.yaml`의 header에 적는다.

## 그림 (figures.yaml)
```yaml
dpi: 144
figures:
  "Q2": {pdf: ../../../2021중간_기말/중간/Midterm0422_1p_rev.pdf, pdf_page: 1, bbox: [x0, y0, x1, y1]}
```
- `pdf`는 **figures 폴더 기준** 상대 경로다(md의 `source`보다 `../`가 하나 많다). 공백이 있는 경로는 따옴표로 감싼다.
- 문제 하나에 그림 한 장이 원칙이다. 패널 (a)(b)가 한 영역에 있으면 bbox 하나로 자르고 `panels: [a, b]`를 둔다. 두 영역이 멀리 떨어져 한 bbox에 다른 문제의 글이 섞이면 `"Q2"`, `"Q2-2"`로 나눈다.
- 이미지 링크는 md와 같은 폴더 기준 `![Q2](figures/fig-Q2.png)`이다.

## 스캔 답안지 (2023)
- 인쇄된 문제 위에 손글씨가 겹친다. 문제는 **인쇄된 글자만** 옮긴다. 손글씨(풀이, 채점 표시, 동그라미)는 옮기지 않는다.
- 손글씨에 가려 읽을 수 없는 글자는 `[판독 불가]`로 적고, 짐작한 값은 별도 줄에 `… 로 보임 (원문에 없음)`으로 적는다.
- 크롭 그림에 손글씨가 들어가면 이미지 링크 아래에 `> 참고: 답안지 손글씨가 겹침 (…위치…)`를 적는다. 넷리스트와 bullet에는 손글씨로 그린 선·라벨을 넣지 않는다.
- 2023 기말은 가려진 곳에 한해 `23-1 기말고사 문제 및 답.pdf`(손정리 노트)를 보조로 쓴다. 그 줄 끝에 `(보조 출처: 손정리 노트)`를 붙인다.
- 같은 폴더의 `2023 전회2 기말.hwp`에는 일부 회로의 깨끗한 원본 그림이 들어 있다(Q1(b) 확인됨). 손글씨에 가린 회로를 대조할 때 쓸 수 있다. 크롭 원본으로는 쓰지 않는다(`crop_exam.py`는 PDF만 읽는다).

## 텍스트 레이어 (2021)
2021 PDF는 텍스트를 추출할 수 있지만 그리스 문자(μ, λ, Ω, β)와 일부 기호가 빠진다. 판독은 렌더링한 이미지를 기준으로 하고, pdftotext는 보조로만 쓴다.

## 검사
```bash
python3 from_the_past/md/_tools/crop_exam.py from_the_past/md/2021-1_중간
python3 from_the_past/md/_tools/check_exam.py from_the_past/md/2021-1_중간
python3 from_the_past/md/_tools/make_exam_index.py from_the_past/md/2021-1_중간
python3 from_the_past/md/_tools/verify_exam.py from_the_past/md/2021-1_중간 --recrop
python3 -m unittest discover -s from_the_past/md/_tools/tests
```
