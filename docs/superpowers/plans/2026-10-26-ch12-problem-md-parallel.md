# 12장 문제 md 병렬 추출 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `12장.pdf`(궤환)의 예제·연습문제·장말문제를 ch09–11과 같은 FORMAT의 md로 옮긴다(`## 원문` 포함, `## 풀이`·`## 힌트` 제외). 작성 묶음을 병렬로 돌려 빨리 끝낸다.

**Architecture:** 기존 `textbook-to-md`는 작성 에이전트를 한 번에 하나만 돌린다. git 인덱스와 `figures.yaml` 끝에 덧붙이는 충돌 때문이다. 여기서는 두 원인을 없앤다. (1) 그림 bbox를 작성 전에 한 에이전트가 **모두** 등록해, 작성자는 이미 있는 항목에 `crops:`만 단다. (2) 묶음마다 **자기 worktree·브랜치**를 둬서 인덱스를 공유하지 않는다. 묶음은 동시에 작성 → 리뷰 → 반영까지 끝내고, 오케스트레이터가 통합 브랜치로 차례로 병합한 뒤 장 단위 검증을 한다.

**Tech Stack:** opus 서브에이전트(Agent, `model: opus`), git worktree, PyMuPDF(`fitz`), `교과서/마이크로전자회로/_tools/*.py`, `workbook/build_workbook.py`

**Spec:** `교과서/마이크로전자회로/FORMAT.md`(형식의 유일한 기준), `.claude/skills/textbook-to-md/SKILL.md`와 `references/{survey,common,writer,reviewer}.md`(절차·프롬프트 템플릿). 이 계획은 그 절차에서 아래 항목만 바꾼다.

## Global Constraints
- 모든 서브에이전트는 opus. 렌더링 검증(md → PNG)은 하지 않는다. SPICE Problems는 범위 밖이다.
- `## 풀이`, `## 힌트`는 쓰지 않는다. `## 원문`은 모든 파일에 쓴다(ch09–11 전 파일에 있음, 형식은 FORMAT `## 문제집용 절`).
- 경로 `MAIN` = `/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2`, 통합 worktree `INT` = `MAIN-ch12`(브랜치 `feat/ch12-problem-md`), 묶음 worktree `WT_<B>` = `MAIN-ch12-<B>`(브랜치 `feat/ch12-<B>`), `SCRATCH` = 세션 scratchpad.
- `12장.pdf`는 9–11장 PDF처럼 **추적한다**. 심볼릭 링크를 쓰지 않고 준비 커밋에 넣는다. (SKILL.md의 링크 지시는 9–11장 PDF가 추적된 지금과 맞지 않음)
- `git add`는 경로를 명시한다. `-A`, `.` 금지. 커밋 끝 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- 작성 에이전트는 **worktree당 하나**다. 동시에 도는 작성 에이전트는 최대 4개로 한다. 리뷰 에이전트는 이 수에 넣지 않는다.
- main 병합, push, worktree 삭제는 사용자에게 묻는다.

## Review Focus
1. 다른 묶음의 문제를 잇는 `depends_on`(장말 "Repeat Problem N") → 묶음 안에서는 WARN이 정상이다. 병합 후 WARN 0, `## 상속·참조` 내용이 상대 파일의 조건과 같아야 한다 (Task 5 Step 3).
2. 두 묶음이 같은 그림에 `crops:`를 단 경우 → 병합 충돌이 나거나 크롭 이름이 겹친다. 둘 다 남기고, 이름이 겹치면 한쪽 이름과 md 링크를 바꾼다 (Task 5 Step 2).
3. 예제와 짝 연습문제가 다른 묶음으로 갈라짐 → `X…: 짝이 되는 예제가 없음`. 묶음을 나눌 때 E/X 쌍은 붙여 둔다 (Task 1 Step 4).
4. Design Problems(P12.71–) 공통 가정 블록 → 원문에 머리말이 인쇄돼 있으면 모든 설계 문제 파일에서 글자까지 같아야 한다. 설계 문제는 한 묶음에 몰아 둔다 (Task 1 Step 4, Task 5 Step 3).
5. 펼침 페이지의 `book_page` 왼쪽·오른쪽 혼동 → 리뷰어 체크리스트 8번으로 잡는다. 병합 후 `verify_chapter`가 절 순서 역전을 잡는다.

---

### Task 1: 준비 — 통합 worktree, 조사, 묶음 계획

**Files:**
- Create: `INT/교과서/마이크로전자회로/12장.pdf` (MAIN에서 복사), `INT/교과서/마이크로전자회로/ch12/figures/figures.yaml` (머리만)
- Create (scratch): `SCRATCH/survey-prompt-ch12.md`, `SCRATCH/survey-ch12.md`, `SCRATCH/batches-ch12.md`
- Modify (조건부): `INT/교과서/마이크로전자회로/FORMAT.md` `## 본문 절` 5

**Interfaces:**
- Produces: 묶음 표 `SCRATCH/batches-ch12.md` — 행마다 `<B> | 대상 id 범위 | PDF 페이지 | 파일 수 | 묶음 밖 depends_on`. 이후 모든 Task가 이 표를 쓴다.

- [ ] **Step 1: 전제 확인과 통합 worktree**

```bash
git -C MAIN status --short | grep -v '^??'          # 비어 있어야 함
git -C MAIN worktree add MAIN-ch12 -b feat/ch12-problem-md main
cp "MAIN/교과서/마이크로전자회로/12장.pdf" "INT/교과서/마이크로전자회로/12장.pdf"
```

- [ ] **Step 2: 0단계 조사** — `references/survey.md`를 채워(`<<REPO>>`=INT, `<<N>>`=12) opus 에이전트 하나에 포그라운드로 맡긴다. 결과 `SCRATCH/survey-ch12.md`.

- [ ] **Step 3: 새 그림 유형 확인 (멈추는 곳 1)** — 조사에 FORMAT이 다루지 않는 유형이 있으면 표기 방법을 제안하고 사용자 확인을 받는다. 12.1의 궤환 블록도(K, A₁, 합산점)가 예상 후보다. 확인되면 FORMAT.md `## 본문 절` 5에 추가한다.

- [ ] **Step 4: 묶음 계획** — 12–16파일씩, 이름 A, B, C …. 다음을 지킨다.
  - 예제와 그 연습문제는 같은 묶음에 둔다.
  - 장말문제는 PDF 페이지 경계로 나누고, Design Problems는 한 묶음에 몰아 둔다.
  - "Repeat Problem N"의 N이 다른 묶음이면 표의 `묶음 밖 depends_on` 칸에 적는다.

- [ ] **Step 5: 준비 커밋** — `figures.yaml` 머리(SKILL.md 3절의 블록, `pdf: ../../12장.pdf`)를 쓰고 커밋한다.

```bash
git -C INT add "교과서/마이크로전자회로/12장.pdf" "교과서/마이크로전자회로/ch12/figures/figures.yaml" [교과서/마이크로전자회로/FORMAT.md]
git -C INT commit -m "chore(ch12): add chapter 12 PDF and figures.yaml header"
```

- [ ] **Step 6: 사용자에게 한 번 알림** — 장 제목, 파일 수(E/X/P), 묶음 표. 묻지 않고 진행한다.

---

### Task 2: 그림 bbox 일괄 등록

**Files:**
- Modify: `INT/교과서/마이크로전자회로/ch12/figures/figures.yaml`
- Create: `INT/교과서/마이크로전자회로/ch12/figures/fig12-<NN>.png` (전체 그림만)

**Interfaces:**
- Consumes: 조사 결과의 그림 번호 목록(예제의 문제·풀이 그림, 장말 그림)
- Produces: 문제·예제가 쓰는 모든 그림의 `"12.NN": {page, bbox}` 항목이 **id 순서로** 들어간 figures.yaml. 작성자는 새 항목을 끝에 덧붙이지 않는다.

- [ ] **Step 1: opus 에이전트 하나(포그라운드)에 맡긴다** — 프롬프트는 `SCRATCH/figures-prompt-ch12.md`에 쓴다. 내용은 다음과 같다. COMMON(Task 3 Step 1)을 먼저 읽게 하고, 조사 목록의 그림마다 216 dpi로 확대해 bbox를 잡는다. 본문 설명용 그림(문제·예제가 쓰지 않는 것)은 넣지 않는다. 그다음 `crop_figures.py`를 돌리고 PNG를 Read로 열어 잘림·옆 그림 침범을 확인한다. `crops:`는 달지 않는다.

- [ ] **Step 2: 검사**

```bash
cd INT && python3 교과서/마이크로전자회로/_tools/crop_figures.py 교과서/마이크로전자회로/ch12
python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests
```
Expected: 크롭 오류 없음, 테스트 OK. 등록 수 = 조사 목록의 그림 수.

- [ ] **Step 3: 커밋** — `docs(ch12): register figure bboxes`. 이 커밋이 모든 묶음 브랜치의 기준점(`BASE`)이다.

---

### Task 3: 묶음 worktree와 프롬프트, 작성자 병렬 실행

**Files:**
- Create (scratch): `SCRATCH/COMMON-ch12.md`, `SCRATCH/writer-ch12-<B>.md` (묶음마다)
- Create (묶음 worktree): `WT_<B>/교과서/마이크로전자회로/ch12/{예제,연습문제,장말문제}/*.md`, 크롭 PNG
- Modify (묶음 worktree): `figures.yaml`의 기존 항목에 `crops:`만

**Interfaces:**
- Consumes: Task 1 묶음 표, Task 2 `BASE` 커밋
- Produces: 묶음마다 add 커밋 해시와 작성자 보고(파일 목록, 애매했던 곳). 작성 에이전트 id는 Task 4에서 SendMessage로 다시 부르므로 기록해 둔다.

- [ ] **Step 1: COMMON 작성** — `references/common.md`를 채운다(`<<REPO>>`는 "자기 묶음 worktree"로, `<<PAGE_MAP>>`은 조사 결과 그대로). 그 위에 다음 차이를 덧붙인다.
  - `## 원문`을 H1 바로 다음에 쓴다. 인쇄된 문장을 글자 그대로 옮기고 FORMAT `## 문제집용 절`과 `check_md.py`의 원문 규칙을 따른다. 참고 파일은 `ch11/장말문제/P11.05.md`.
  - `## 풀이`, `## 힌트`는 쓰지 않는다.
  - figures.yaml은 기존 항목에 `crops:`만 단다. 그림 항목이 없으면 id 순서 자리에 넣고 보고에 적는다.
  - git 규칙의 브랜치 이름은 `feat/ch12-<B>`다. PDF는 이미 추적되므로 다시 add하지 않는다.
  - 형식 검사 기대값은 `<자기 묶음 파일 수>개 파일, 오류 0개`다. WARN은 묶음 표의 `묶음 밖 depends_on`에서 나온 것만 허용한다. `verify_chapter.py`의 번호 빠짐과 README 오류는 정상이다.
  - 묶음 밖 depends_on의 조건은 다른 파일을 기다리지 않고 원본 PDF에서 직접 읽어 `## 상속·참조`와 `## 조건`에 적는다.

- [ ] **Step 2: 묶음 worktree 생성** (묶음마다)

```bash
git -C INT worktree add MAIN-ch12-<B> -b feat/ch12-<B> BASE
```

- [ ] **Step 3: 작성자 프롬프트** — `references/writer.md`를 채운다. `<<PREV_REVIEW>>`=없음, `<<BUSY_FILES>>`=없음, `<<EXPECTED_TOTAL>>`=그 묶음의 파일 수, `<<LOCATIONS>>`=조사의 해당 행.

- [ ] **Step 4: 실행** — 작성자를 백그라운드로, 동시에 최대 4개까지 띄운다. 하나가 끝나면 다음 묶음을 띄운다. 묶음마다 한 줄씩 알린다(add 커밋, 파일 수).

- [ ] **Step 5: 묶음 완료 확인** (작성자 보고마다)

```bash
cd WT_<B> && python3 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/ch12 | tail -1
git -C WT_<B> status --short | grep -v '^??'   # 비어 있어야 함
```
Expected: `<파일 수>개 파일, 오류 0개`, 허용된 WARN만.

---

### Task 4: 묶음 리뷰와 반영

**Files:**
- Create: `WT_<B>/docs/superpowers/reports/ch12/review-<B>.md`
- Modify: 리뷰가 사실 오류를 찾은 md·figures.yaml·PNG

**Interfaces:**
- Consumes: Task 3 add 커밋, 작성자 보고의 "판독이 애매했던 곳", 작성 에이전트 id
- Produces: 묶음 브랜치 끝 커밋이 `docs: apply review fixes to ch12 batch <B> (…)` 또는 `docs: record review of ch12 batch <B> (no fixes)`

- [ ] **Step 1: 리뷰어 실행** — 작성 k가 끝나는 즉시 `references/reviewer.md`로 리뷰어를 백그라운드로 띄운다. 작업 루트는 `WT_<B>`, `<<PREV_FIX_COMMIT>>`=없음, `<<REPORT>>`=위 경로다. `.part` → `mv` 규칙은 그대로 둔다.

- [ ] **Step 2: 반영** — 리뷰가 끝나면 **같은 작성 에이전트**에 SendMessage로 writer.md 1단계(리뷰 반영)를 맡긴다. 원본을 이미 읽은 맥락을 다시 쓰기 위해서다. 에이전트가 끝나 재개가 안 되면 writer.md를 `<<TARGETS>>`=없음으로 채워 새로 띄운다.

- [ ] **Step 3: 확인**

```bash
git -C WT_<B> log --oneline BASE.. | head -3
ls WT_<B>/docs/superpowers/reports/ch12/review-<B>.md
```
Expected: add 커밋 뒤에 반영 또는 기록 커밋이 있고, 보고서가 추적된다. 묶음마다 한 줄 알림(사실 오류 수, 반영 커밋).

---

### Task 5: 통합 브랜치로 병합

**Files:**
- Modify: `INT/교과서/마이크로전자회로/ch12/figures/figures.yaml` (충돌 해결 시)

**Interfaces:**
- Consumes: Task 4가 끝난 모든 `feat/ch12-<B>`
- Produces: 모든 md·PNG·리뷰 보고서가 들어간 `feat/ch12-problem-md`

- [ ] **Step 1: 묶음 순서(A, B, …)대로 병합**

```bash
git -C INT merge --no-ff feat/ch12-<B> -m "merge: ch12 batch <B>"
```

- [ ] **Step 2: figures.yaml 충돌 해결 (있을 때만)** — 같은 그림의 `crops:`는 양쪽을 다 남긴다. 크롭 이름이 겹치는데 사각형이 다르면 뒤 묶음의 이름을 바꾸고 그 md의 이미지 링크와 frontmatter `crop:`을 함께 고친다. 그 뒤 `crop_figures.py`를 돌리고, 충돌을 해결한 채로 병합 커밋을 마친다.

- [ ] **Step 3: 병합 후 교차 검사**

```bash
cd INT && python3 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/ch12 | grep -c WARN
```
Expected: 0. 묶음 밖 depends_on마다 `## 상속·참조`의 조건이 상대 파일의 `## 조건`과 같은지 눈으로 대조한다. 설계 문제 공통 가정 블록이 모든 설계 파일에서 같은지는 `diff`로 확인한다. 다르면 고쳐 `fix(ch12): align cross-batch inherited conditions`로 커밋한다.

---

### Task 6: 마무리 검증과 보고

**Files:**
- Create: `INT/교과서/마이크로전자회로/ch12/README.md` (make_index 생성)
- Create: `INT/workbook/pdf/ch12-문제.pdf`, `INT/workbook/pdf/ch12-답안.pdf`

- [ ] **Step 1: 인덱스** — `python3 교과서/마이크로전자회로/_tools/make_index.py 교과서/마이크로전자회로/ch12 "12장 <조사의 장 제목>"` → `docs: add ch12 problem index README`

- [ ] **Step 2: 전체 검증** (INT에서)

```bash
python3 교과서/마이크로전자회로/_tools/verify_chapter.py 교과서/마이크로전자회로/ch12 --recrop
for c in 교과서/마이크로전자회로/ch*/; do python3 교과서/마이크로전자회로/_tools/check_md.py "$c" | grep -c WARN; python3 교과서/마이크로전자회로/_tools/check_md.py "$c" | tail -1; done
python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests
python3 -m unittest discover -s workbook/tests
python3 -c "import sys; sys.path.insert(0,'.claude/skills/ec2-review-pack/scripts'); import problem_index as p; print(sum('/ch12/' in str(x) for x in p.md_paths('.', {12})))"
```
Expected: verify 오류 0. INFO(연습문제 없는 예제)는 원본에서 확인해 보고에 적는다. 모든 장의 check_md는 오류 0·WARN 0이고 두 테스트 묶음은 OK다. 마지막 줄은 ch12 md 총수와 같아야 한다. workbook 테스트가 golden sample 때문에 깨지면 원인을 보고하고 멈춘다(멈추는 곳 2).

- [ ] **Step 3: 문제집 PDF** — `python3 workbook/build_workbook.py ch12`. 종료 코드 0이어야 한다(쪽 넘침 없음). 두 PDF를 add해 `docs(ch12): build workbook PDFs`로 커밋한다.

- [ ] **Step 4: 보고 (멈추는 곳 3)** — SKILL.md `## 마무리 보고 형식` 표에 "묶음 수·병렬도"와 "교차 병합 충돌" 행을 더해 보고한다. 그다음 다음 셋을 따로 묻는다.
  - main 병합: MAIN이 `main`인지 확인한 뒤 `git -C MAIN merge --ff-only feat/ch12-problem-md`. main이 앞서 있으면 INT에서 `git rebase --rebase-merges main` 후 ff
  - push
  - worktree·브랜치 정리: `MAIN-ch12`, `MAIN-ch12-<B>…`, `feat/ch12-<B>…`
