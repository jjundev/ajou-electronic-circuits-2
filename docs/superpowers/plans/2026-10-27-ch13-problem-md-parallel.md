# 13장 문제 md 병렬 추출 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `13장.pdf`(발진기)의 예제·연습문제·장말문제(P13.01–P13.59)를 ch09–11과 같은 FORMAT의 md로 옮긴다(`## 원문` 포함, `## 풀이`·`## 힌트` 제외). 작성 묶음을 병렬로 돌려 빨리 끝낸다.

**Architecture:** 기존 `textbook-to-md`는 작성 에이전트를 한 번에 하나만 돌린다. git 인덱스와 `figures.yaml` 끝에 덧붙이는 충돌 때문이다. 이 계획은 12장 병렬 계획(`7efd6ba0:docs/superpowers/plans/2026-10-26-ch12-problem-md-parallel.md`)과 같은 방식으로 두 원인을 없앤다. (1) 작성 전에 에이전트 하나가 그림 bbox를 **모두** 등록하고, 작성자는 이미 있는 항목에 `crops:`만 단다. (2) 묶음마다 **자기 worktree·브랜치**를 둬서 git 인덱스를 공유하지 않는다. 묶음은 작성 → 리뷰 → 반영까지 동시에 진행하고, 오케스트레이터가 통합 브랜치로 차례로 병합한 뒤 장 단위 검증을 한다.

**Tech Stack:** opus 서브에이전트(Agent, `model: opus`), git worktree, PyMuPDF(`fitz`), `교과서/마이크로전자회로/_tools/*.py`, `workbook/build_workbook.py`

**Spec:** `교과서/마이크로전자회로/FORMAT.md`(형식의 유일한 기준), `.claude/skills/textbook-to-md/SKILL.md`와 `references/{survey,common,writer,reviewer}.md`(절차·프롬프트 템플릿). 이 계획은 그 절차에서 아래 항목만 바꾼다. 설계 결정(2026-10-27 대화): 원문 절 넣음, 예제 `## 답 (검증용)` 유지, 예제+연습문제+장말문제 전부 다룸, SPICE 13.60–13.69 제외.

## Global Constraints
- 모든 서브에이전트는 opus로 띄운다. 렌더링 검증(md → PNG)은 하지 않는다. SPICE Problems(13.60–13.69)는 범위 밖이다. 13.59는 Design Problems라 포함한다.
- `## 풀이`, `## 힌트`는 쓰지 않는다. `## 원문`은 모든 파일에 쓴다(형식은 FORMAT `## 문제집용 절`).
- 경로는 다음과 같이 쓴다.
  - `MAIN` = `/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2`
  - 통합 worktree `INT` = `MAIN/.claude/worktrees/microelectronics-ch13-problems-954d84`(브랜치 `claude/microelectronics-ch13-problems-954d84`, 이미 있음)
  - 묶음 worktree `WT_<B>` = `MAIN-ch13-<B>`(브랜치 `feat/ch13-<B>`)
  - `SCRATCH` = 세션 scratchpad
  - 경로의 한글은 디스크에 NFD로 저장돼 있다. 에이전트 프롬프트에 붙일 절대 경로는 손으로 치지 말고 `pwd` 출력에서 복사한다.
- `13장.pdf`는 이미 INT에서 추적된다(`3fd9722c`). 다시 add하거나 링크하지 않는다.
- PDF 한 페이지는 교재 두 쪽 펼침이다. 첫 페이지만 731쪽 한 쪽이고, PDF 2쪽 = 732·733쪽, … PDF 20쪽 = 768·769쪽이다. 장말문제는 PDF 18–20쪽에 있다.
- `git add`는 경로를 명시한다. `-A`, `.`는 쓰지 않는다. 커밋 메시지 끝에는 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`을 붙인다.
- 작성 에이전트는 **worktree당 하나**만 둔다. 동시에 도는 작성 에이전트는 최대 4개다. 리뷰 에이전트는 이 수에 넣지 않는다.
- main 병합, push, worktree 삭제는 사용자에게 묻고 나서 한다.

## Review Focus
1. **블록도 그림**(P13.01, P13.02의 그림 13.37·13.38: H(s)/G(s)/K(s) 상자와 ⊕): Task 1 Step 2에서 가져온 FORMAT 블록도 표기(`sum`, `gain`)로 적어야 하고, check_md 오류가 0이어야 한다. 리뷰어 프롬프트에 이 두 파일을 따로 짚는다(Task 4 Step 1).
2. **다른 묶음 문제에 대한 `depends_on`**("Repeat Problem 13.51", Colpitts 13.34–13.37의 "Repeat the analysis of the Colpitts oscillator" 연쇄 등): 묶음 안에서는 WARN이 정상이다. 병합 후에는 WARN이 0이어야 하고, `## 상속·참조` 내용이 상대 파일의 조건과 같아야 한다(Task 5 Step 3). Colpitts 연쇄 P13.32–P13.37과 P13.51–P13.52는 각각 한 묶음 안에 둔다(Task 1 Step 5).
3. **Design Problems 공통 가정 블록**(P13.53–P13.59, "unless otherwise stated, assume μnCox = 2μpCox = 100 μA/V², …"): 모든 설계 문제 파일에서 글자 하나까지 같아야 한다. 설계 문제는 한 묶음에 몰아 두고, Task 5 Step 3에서 `diff`로 대조한다.
4. **펼침 페이지의 `book_page`**: 오른쪽 쪽에서 시작하는 문제를 왼쪽 쪽 번호로 적기 쉽다. 리뷰어 체크리스트(Task 4 Step 1)로 잡고, 병합 후 `verify_chapter`가 절 순서 역전을 잡는다.
5. **예제와 짝 연습문제가 다른 묶음으로 갈라지는 경우**: `X…: 짝이 되는 예제가 없음` 오류가 난다. 묶음을 나눌 때 E/X 쌍은 붙여 둔다(Task 1 Step 5).

---

### Task 1: 준비 — FORMAT 반영, 조사, 묶음 계획

**Files:**
- Modify: `INT/교과서/마이크로전자회로/FORMAT.md`, `INT/교과서/마이크로전자회로/_tools/check_md.py`, `INT/교과서/마이크로전자회로/_tools/tests/test_check_md.py` (`7efd6ba0`에서 가져옴)
- Create: `INT/교과서/마이크로전자회로/ch13/figures/figures.yaml` (머리만)
- Create (scratch): `SCRATCH/survey-prompt-ch13.md`, `SCRATCH/survey-ch13.md`, `SCRATCH/batches-ch13.md`

**Interfaces:**
- Produces: 묶음 표 `SCRATCH/batches-ch13.md`. 행마다 `<B> | 대상 id 범위 | PDF 페이지 | 파일 수 | 묶음 밖 depends_on`을 적고, 이후 모든 Task가 이 표를 쓴다.

- [ ] **Step 1: 전제 확인**

```bash
git -C INT status --short | grep -v '^??'     # 비어 있어야 함
git -C INT log --oneline -1 -- 교과서/마이크로전자회로/13장.pdf   # 3fd9722c
```

- [ ] **Step 2: 12장의 블록도 표기 가져오기** — `7efd6ba0`에서 세 파일만 가져온다. ch12 PDF, plan, ch12 figures.yaml은 가져오지 않는다. 먼저 main이 그사이 이 세 파일을 바꿨는지 확인한다.

```bash
cd INT
git diff 3fd9722c main -- 교과서/마이크로전자회로/FORMAT.md 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/_tools/tests/test_check_md.py | head
```
- 비어 있으면 그대로 가져온다: `git checkout 7efd6ba0 -- <세 파일>`
- 비어 있지 않으면 덮어쓰지 않는다. `git show 7efd6ba0 -- <세 파일> | git apply --index`로 차이만 얹는다.

```bash
git diff --cached --stat     # 세 파일, FORMAT +8/-1, check_md +5, test +28
python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests
for c in 09 10 11; do python3 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/ch$c | tail -1; done
```
Expected: 테스트 OK. 9–11장은 모두 `오류 0개`다. 커밋 메시지는 `chore(ch13): adopt block-diagram notation from ch12 (7efd6ba0)`로 한다.

- [ ] **Step 3: 0단계 조사** — `references/survey.md`를 채워(`<<REPO>>`=INT, `<<N>>`=13, `<<PDF>>`=`교과서/마이크로전자회로/13장.pdf`) opus 에이전트 하나에 포그라운드로 맡긴다. 결과는 `SCRATCH/survey-ch13.md`다. 예제 수(최소 13.10까지), 짝 연습문제 수, 장말 59개, 문제·예제가 쓰는 그림 목록을 확정한다.

- [ ] **Step 4: 새 그림 유형 확인 (멈추는 곳 1)** — 블록도와 종속 전원(그림 13.43의 `g_m V_x`)은 Step 2로 해결된다. 그 밖에 FORMAT이 다루지 않는 유형이 나오면 멈춘다. 예상 후보는 크리스털 기호(그림 13.30·13.34)와 파형 그림(13.14·13.17)이다.
  - 파형은 FORMAT의 "그래프·파형뿐인 그림" 규칙으로 처리되므로 새 유형이 아니다.
  - 크리스털은 `X<이름> n1 n2 box "crystal"`을 제안한다.
  - 사용자 확인을 받은 뒤 FORMAT.md 넷리스트 표에 추가해 커밋한다.

- [ ] **Step 5: 묶음 계획** — 묶음당 12–16파일, 이름은 A, B, C …로 한다.
  - 예제와 그 연습문제는 같은 묶음에 둔다.
  - 장말문제는 PDF 페이지 경계(18 / 19 / 20)를 기본으로 나눈다.
  - Colpitts 연쇄 P13.32–P13.37, 크리스털 P13.51–P13.52, Design Problems P13.53–P13.59는 각각 한 묶음 안에 둔다.
  - "Repeat Problem N"이나 "the analysis of …"가 가리키는 문제·예제가 다른 묶음에 있으면 표의 `묶음 밖 depends_on` 칸에 적는다.

- [ ] **Step 6: 준비 커밋** — `figures.yaml` 머리(SKILL.md 3절의 블록, `pdf: ../../13장.pdf`, `dpi: 144`)를 쓰고 커밋한다. Step 4에서 FORMAT을 고쳤으면 그 파일도 함께 add한다.

```bash
git -C INT add "교과서/마이크로전자회로/ch13/figures/figures.yaml"
git -C INT commit -m "chore(ch13): add figures.yaml header"
```

- [ ] **Step 7: 사용자에게 한 번 알린다** — 장 제목, 파일 수(E/X/P), 묶음 표를 보여 주고, 묻지 않고 진행한다.

---

### Task 2: 그림 bbox 일괄 등록

**Files:**
- Modify: `INT/교과서/마이크로전자회로/ch13/figures/figures.yaml`
- Create: `INT/교과서/마이크로전자회로/ch13/figures/fig13-<NN>.png` (전체 그림만)

**Interfaces:**
- Consumes: 조사 결과의 그림 번호 목록(예제의 문제·풀이 그림, 장말 그림 13.37–13.46, 장말이 문제 회로로 쓰는 본문 그림)
- Produces: 문제·예제가 쓰는 모든 그림의 `"13.NN": {page, bbox}` 항목이 **id 순서로** 들어간 figures.yaml. 작성자는 새 항목을 끝에 덧붙이지 않는다.

- [ ] **Step 1: opus 에이전트 하나(포그라운드)에 맡긴다** — 프롬프트는 `SCRATCH/figures-prompt-ch13.md`에 쓴다.
  - COMMON(Task 3 Step 1)을 먼저 읽게 한다.
  - 조사 목록의 그림마다 216 dpi로 확대해 bbox를 잡는다. 펼침 페이지에서는 bbox가 가운데 접힘을 넘지 않게 한다.
  - 본문 설명용 그림(문제·예제가 쓰지 않는 것)은 넣지 않는다.
  - `crop_figures.py`를 돌리고 PNG를 Read로 열어, 잘린 곳이 없는지와 옆 그림을 침범하지 않았는지 확인한다.
  - `crops:`는 달지 않는다.

- [ ] **Step 2: 검사**

```bash
cd INT && python3 교과서/마이크로전자회로/_tools/crop_figures.py 교과서/마이크로전자회로/ch13
python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests
```
Expected: 크롭 오류가 없고 테스트는 OK다. 등록 수는 조사 목록의 그림 수와 같아야 한다.

- [ ] **Step 3: 커밋** — `docs(ch13): register figure bboxes`로 커밋한다. 이 커밋이 모든 묶음 브랜치의 기준점(`BASE`)이다.

---

### Task 3: 묶음 worktree와 프롬프트, 작성자 병렬 실행

**Files:**
- Create (scratch): `SCRATCH/COMMON-ch13.md`, `SCRATCH/writer-ch13-<B>.md` (묶음마다)
- Create (묶음 worktree): `WT_<B>/교과서/마이크로전자회로/ch13/{예제,연습문제,장말문제}/*.md`, 크롭 PNG
- Modify (묶음 worktree): `figures.yaml`의 기존 항목에 `crops:`만

**Interfaces:**
- Consumes: Task 1 묶음 표, Task 2 `BASE` 커밋
- Produces: 묶음마다 add 커밋 해시와 작성자 보고(파일 목록, 판독이 애매했던 곳). 작성 에이전트 id는 Task 4에서 SendMessage로 다시 부르므로 기록해 둔다.

- [ ] **Step 1: COMMON 작성** — `references/common.md`를 채운다(`<<REPO>>`는 "자기 묶음 worktree"로, `<<PAGE_MAP>>`은 조사 결과 그대로). 그 위에 다음 차이를 덧붙인다.
  - `## 원문`을 H1 바로 다음에 쓴다. 인쇄된 문장을 글자 그대로 옮기고, FORMAT `## 문제집용 절`과 `check_md.py`의 원문 규칙을 따른다. 참고 파일은 `ch11/장말문제/P11.05.md`(영문)와 `ch11/예제/E11.04.md`(한국어 예제)다. 예제의 원문은 "풀이" 앞 문장이다.
  - `## 풀이`, `## 힌트`는 쓰지 않는다. 예제의 `## 답 (검증용)`은 FORMAT대로 쓴다.
  - 블록도(⊕, H(s) 상자)와 종속 전원은 FORMAT 넷리스트 표의 `sum`/`gain`/`G` 규칙으로 적는다. FORMAT이 예로 드는 ch12 파일은 이 checkout에 없으므로, 표기는 FORMAT 문장만 따른다.
  - figures.yaml은 기존 항목에 `crops:`만 단다. 그림 항목이 없으면 id 순서 자리에 넣고 보고에 적는다.
  - git 규칙의 브랜치 이름은 `feat/ch13-<B>`다. PDF는 이미 추적되므로 다시 add하지 않는다.
  - 형식 검사의 기대값은 `<자기 묶음 파일 수>개 파일, 오류 0개`다. WARN은 묶음 표의 `묶음 밖 depends_on`에서 나온 것만 허용한다. `verify_chapter.py`의 번호 빠짐과 README 오류는 정상이다.
  - 묶음 밖 depends_on의 조건은 다른 파일을 기다리지 않고 원본 PDF에서 직접 읽어 `## 상속·참조`와 `## 조건`에 적는다.

- [ ] **Step 2: 묶음 worktree 생성** (묶음마다)

```bash
git -C INT worktree add MAIN-ch13-<B> -b feat/ch13-<B> BASE
```

- [ ] **Step 3: 작성자 프롬프트** — `references/writer.md`를 다음 값으로 채운다.
  - `<<PREV_REVIEW>>`=없음, `<<BUSY_FILES>>`=없음
  - `<<EXPECTED_TOTAL>>`=그 묶음의 파일 수
  - `<<LOCATIONS>>`=조사의 해당 행

- [ ] **Step 4: 실행** — 작성자를 백그라운드로, 동시에 최대 4개까지 띄운다. 하나가 끝나면 다음 묶음을 띄운다. 묶음마다 add 커밋과 파일 수를 한 줄씩 알린다.

- [ ] **Step 5: 묶음 완료 확인** (작성자 보고마다)

```bash
cd WT_<B> && python3 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/ch13 | tail -1
git -C WT_<B> status --short | grep -v '^??'                          # 비어 있어야 함
grep -rl '^## 풀이\|^## 힌트' 교과서/마이크로전자회로/ch13              # 비어 있어야 함
grep -rL '^## 원문' 교과서/마이크로전자회로/ch13/{예제,연습문제,장말문제}  # 비어 있어야 함
```
Expected: `<파일 수>개 파일, 오류 0개`, 허용된 WARN만 있다. 풀이·힌트 절은 없고, 모든 파일에 원문 절이 있다.

---

### Task 4: 묶음 리뷰와 반영

**Files:**
- Create: `WT_<B>/docs/superpowers/reports/ch13/review-<B>.md`
- Modify: 리뷰가 사실 오류를 찾은 md·figures.yaml·PNG

**Interfaces:**
- Consumes: Task 3 add 커밋, 작성자 보고의 "판독이 애매했던 곳", 작성 에이전트 id
- Produces: 묶음 브랜치의 끝 커밋이 `docs: apply review fixes to ch13 batch <B> (…)` 또는 `docs: record review of ch13 batch <B> (no fixes)`

- [ ] **Step 1: 리뷰어 실행** — 작성 k가 끝나는 즉시 `references/reviewer.md`로 리뷰어를 백그라운드로 띄운다.
  - 작업 루트는 `WT_<B>`, `<<PREV_FIX_COMMIT>>`=없음, `<<REPORT>>`=위 경로다. `.part` → `mv` 규칙은 그대로 둔다.
  - `<<FLAGS>>`에 다음 확인 항목을 덧붙인다.
    - `book_page`가 펼침의 왼쪽인지 오른쪽인지
    - `## 원문`이 인쇄와 글자 그대로 같은지
    - 블록도 넷리스트의 덧셈기 부호(P13.01, P13.02가 있는 묶음)

- [ ] **Step 2: 반영** — 리뷰가 끝나면 **같은 작성 에이전트**에 SendMessage로 writer.md 1단계(리뷰 반영)를 맡긴다. 원본을 이미 읽은 맥락을 다시 쓰기 위해서다. 에이전트가 끝나 재개가 안 되면 writer.md를 `<<TARGETS>>`=없음으로 채워 새로 띄운다.

- [ ] **Step 3: 확인**

```bash
git -C WT_<B> log --oneline BASE.. | head -3
git -C WT_<B> ls-files docs/superpowers/reports/ch13/review-<B>.md
```
Expected: add 커밋 뒤에 반영 또는 기록 커밋이 있고, 보고서가 추적된다. 묶음마다 사실 오류 수와 반영 커밋을 한 줄씩 알린다.

---

### Task 5: 통합 브랜치로 병합

**Files:**
- Modify: `INT/교과서/마이크로전자회로/ch13/figures/figures.yaml` (충돌을 해결할 때)

**Interfaces:**
- Consumes: Task 4가 끝난 모든 `feat/ch13-<B>`
- Produces: 모든 md·PNG·리뷰 보고서가 들어간 `claude/microelectronics-ch13-problems-954d84`

- [ ] **Step 1: 묶음 순서(A, B, …)대로 병합**

```bash
git -C INT merge --no-ff feat/ch13-<B> -m "merge: ch13 batch <B>"
```

- [ ] **Step 2: figures.yaml 충돌 해결 (있을 때만)** — 같은 그림의 `crops:`는 양쪽을 다 남긴다. 크롭 이름이 겹치는데 사각형이 다르면 뒤 묶음의 이름을 바꾸고, 그 md의 이미지 링크와 frontmatter `crop:`을 함께 고친다. 그 뒤 `crop_figures.py`를 돌리고, 충돌을 해결한 채로 병합 커밋을 마친다.

- [ ] **Step 3: 병합 후 교차 검사**

```bash
cd INT && python3 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/ch13 | grep -c WARN
D=교과서/마이크로전자회로/ch13/장말문제
blk() { awk '/^## 상속·참조/{f=1;next} /^## /{f=0} f' "$1" | grep -i 'unless\|otherwise\|공통 가정'; }
for f in $D/P13.5[4-9].md; do diff <(blk $D/P13.53.md) <(blk "$f") >/dev/null || echo "DIFF $f"; done
```
Expected: WARN 0, `DIFF` 출력 없음. 묶음 밖 depends_on마다 `## 상속·참조`의 조건이 상대 파일의 `## 조건`과 같은지 눈으로 대조한다. 다르면 고쳐서 `fix(ch13): align cross-batch inherited conditions`로 커밋한다.

---

### Task 6: 마무리 검증과 보고

**Files:**
- Create: `INT/교과서/마이크로전자회로/ch13/README.md` (make_index로 생성)
- Create: `INT/workbook/pdf/ch13-문제.pdf`, `INT/workbook/pdf/ch13-답안.pdf`

- [ ] **Step 1: 인덱스** — `python3 교과서/마이크로전자회로/_tools/make_index.py 교과서/마이크로전자회로/ch13 "13장 발진기"`를 돌리고 `docs: add ch13 problem index README`로 커밋한다.

- [ ] **Step 2: 전체 검증** (INT에서)

```bash
python3 교과서/마이크로전자회로/_tools/verify_chapter.py 교과서/마이크로전자회로/ch13 --recrop
for c in 교과서/마이크로전자회로/ch*/; do python3 교과서/마이크로전자회로/_tools/check_md.py "$c" | grep -c WARN; python3 교과서/마이크로전자회로/_tools/check_md.py "$c" | tail -1; done
python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests
python3 -m unittest discover -s workbook/tests
python3 -c "import sys; sys.path.insert(0,'.claude/skills/ec2-review-pack/scripts'); import problem_index as p; print(sum('/ch13/' in str(x) for x in p.md_paths('.', {13})))"
grep -rl '^## 풀이\|^## 힌트' 교과서/마이크로전자회로/ch13   # 비어 있어야 함
```
Expected:
- verify 오류는 0이다. INFO(연습문제가 없는 예제)는 원본에서 확인해 보고에 적는다.
- 모든 장의 check_md가 오류 0·WARN 0이고, 두 테스트 묶음이 OK다.
- problem_index 출력은 ch13 md 총수와 같다.
- 풀이·힌트 절은 없다.
- workbook 테스트가 golden sample 때문에 깨지면 원인을 보고하고 멈춘다(멈추는 곳 2).

- [ ] **Step 3: 문제집 PDF** — `python3 workbook/build_workbook.py ch13`을 돌린다. 종료 코드가 0이어야 한다(쪽 넘침 없음). 풀이가 없으므로 장말문제의 답안지 칸은 비어 있는 것이 정상이다. 두 PDF를 add하고 `docs(ch13): build workbook PDFs`로 커밋한다.

- [ ] **Step 4: 보고 (멈추는 곳 3)** — SKILL.md `## 마무리 보고 형식` 표에 "묶음 수·병렬도"와 "교차 병합 충돌" 행을 더해 보고한다. 그다음 다음 셋을 따로 묻는다.
  - main 병합: MAIN이 `main`인지 확인한 뒤 `git -C MAIN merge --ff-only claude/microelectronics-ch13-problems-954d84`를 한다. main이 앞서 있으면 INT에서 `git rebase --rebase-merges main` 후 ff한다. main에 ch12의 같은 FORMAT 변경이 먼저 들어갔으면 rebase 중 Task 1 Step 2 커밋이 빈 커밋이 되거나 충돌하는데, 이때는 main 쪽을 택한다.
  - push
  - worktree·브랜치 정리: `MAIN-ch13-<B>…`, `feat/ch13-<B>…`. INT는 앱이 만든 worktree라 따로 묻는다.
