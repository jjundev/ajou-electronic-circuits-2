---
name: textbook-to-md
description: 교과서/마이크로전자회로의 새 장 PDF(스캔본) 문제를 문제 1개당 md 1개로 변환한다. 0단계 조사, opus 작성과 독립 리뷰 파이프라인, 리뷰 반영, 인덱스, 장 단위 검증까지 한 번에 진행한다. 12장 문제 md로 변환해줘, N장 교과서 문제 변환, /textbook-to-md N 같은 요청에 쓴다.
---

# 교과서 문제 → MD 변환 (`textbook-to-md`)

Razavi 마이크로전자회로 `N장.pdf`의 예제, 연습문제, 장말문제를 FORMAT.md 형식의 md로 옮긴다. 9–11장(377문제)에서 검증한 절차다.

## 고정 규칙
- 형식과 판독 관례의 기준은 `교과서/마이크로전자회로/FORMAT.md` 하나다. 이 스킬은 형식을 다시 정의하지 않는다.
- 모든 서브에이전트는 **opus**로 띄운다(`model: opus`). 렌더링 검증(md → PNG)은 하지 않는다.
- 작성 에이전트는 한 번에 하나만 돌린다. git 인덱스와 figures.yaml을 공유하기 때문이다. 리뷰는 한 묶음 늦게 병렬로 돌린다.
- 추적하지 않는 파일(PDF, `STT/`, `강의노트/`)은 add하지 않는다. add할 때는 항상 경로를 명시한다.
- push, main 병합, worktree 삭제는 사용자에게 묻고 나서 한다.
- SPICE Problems는 범위 밖이다.

## 멈추고 묻는 경우 (이 셋뿐)
1. 0단계 조사에서 FORMAT이 다루지 않는 새 그림 유형이 나왔을 때. 표기 방법을 제안하고, 확인을 받으면 FORMAT.md의 해당 절(그림 유형이면 `## 본문 절` 5)에 먼저 추가해 커밋한다.
2. 마무리 검증이 실패했을 때. 오류 목록을 보여 주고 완료를 선언하지 않는다.
3. 병합, push, worktree 정리.

그 밖에는 묻지 않고 진행한다. 묶음마다 한 줄씩 진행 상황을 알린다.

## 절차

### 1. 입력과 전제
- 장 번호 `N`. 메인 checkout 루트를 `MAIN`이라 한다.
- `MAIN/교과서/마이크로전자회로/N장.pdf`가 없으면 중단하고 알린다.
- `git -C MAIN status --short | grep -v '^??'`가 비어 있어야 한다.
- 장마다 worktree를 하나씩 쓴다. 다른 장과 병렬로 진행할 수 있다. PDF는 심볼릭 링크로 넣고 절대 add하지 않는다.
  ```bash
  git -C MAIN worktree add "$(dirname MAIN)/$(basename MAIN)-chN" -b feat/chN-problem-md main
  ln -s MAIN/교과서/마이크로전자회로/N장.pdf "$(dirname MAIN)/$(basename MAIN)-chN/교과서/마이크로전자회로/N장.pdf"
  ```
  이후 모든 에이전트의 작업 루트(`<<REPO>>`)는 이 worktree(`WT`)다.

### 2. 재개 판단
`WT/교과서/마이크로전자회로/chN/`가 이미 있으면 처음부터 하지 않는다.
```bash
git -C WT log --oneline main.. --grep="chN"
ls WT/docs/superpowers/reports/chN/
```
세 가지로 어디까지 끝났는지 판단하고 그다음부터 잇는다.
- `add chN …` 커밋이 있으면 그 작성 묶음은 끝났다.
- `review-<묶음>.md`가 있으면 그 리뷰는 끝났다(추적 여부와 무관).
- `apply review fixes` / `record review` 커밋이 있으면 그 반영은 끝났다.

조사 결과가 scratchpad에 없으면 0단계를 다시 한다. 파일을 건드리지 않는 조사라서 안전하다.

### 3. 0단계 조사
1. `references/survey.md`의 자리표시자를 채워 `SCRATCH/survey-prompt-chN.md`로 쓴다. opus 에이전트 하나에 "이 파일을 읽고 그대로 따르라"고 맡긴다(포그라운드).
2. 결과 `SCRATCH/survey-chN.md`를 읽는다.
   - 새 그림 유형이 있으면 여기서 멈추고 묻는다(위 1번).
   - 묶음 계획을 확정한다. 12–18개씩, 예제와 연습문제를 먼저 예제 순으로, 장말문제는 PDF 페이지 경계로 나눈다. 이름은 A, B, C …
   - `WT/교과서/마이크로전자회로/chN/figures/figures.yaml`의 머리를 만든다. 첫 작성 에이전트가 함께 커밋한다.
     ```yaml
     # 그림 id → PDF 페이지(1부터)와 bbox [x0, y0, x1, y1] (PDF pt, 왼쪽 위 원점)
     # id 는 반드시 따옴표로 감싼다 ("N.30" 이 숫자 N.3 으로 바뀌는 것 방지)
     pdf: ../../N장.pdf
     dpi: 144
     figures:
     ```
3. 사용자에게 장 제목, 문제 수, 묶음 계획을 한 번 보여 주고, 묻지 않고 진행한다.

### 4. 공통 지침 파일
`references/common.md`를 채워 `SCRATCH/COMMON-chN.md`로 쓴다. `<<PAGE_MAP>>`에는 조사 결과의 쪽 대응 표, 예제 표, 장말문제 표와 목록을 그대로 붙인다.

### 5. 파이프라인
에이전트는 모두 opus로, 백그라운드로 띄운다. 프롬프트는 템플릿을 채운 파일을 `SCRATCH/`에 쓰고 "이 파일을 읽고 따르라"로 준다.

작성 k가 끝나면(첫 묶음은 바로) 다음 둘을 **동시에** 띄운다.
- **리뷰 k:** `references/reviewer.md`를 쓴다. 채울 값은 다음과 같다.
  - `<<TARGETS>>`: 묶음 k의 대상
  - `<<COMMIT>>`: 작성 k가 보고한 add 커밋
  - `<<FLAGS>>`: 작성 k가 보고한 "판독이 애매했던 곳"을 그대로 붙인다
  - `<<REPORT>>`: `docs/superpowers/reports/chN/review-<k>.md`
  - `<<PREV_FIX_COMMIT>>`: 작성 k의 1단계 커밋, 없으면 "없음"
- **작성 k+1:** `references/writer.md`를 쓴다.
  - 1단계는 리뷰 k−1의 보고서를 반영한다. 리뷰 k−1이 아직 안 끝났으면 끝날 때까지 기다렸다가 띄운다. 첫 두 묶음은 `<<PREV_REVIEW>>` = "없음"이다.
  - `<<BUSY_FILES>>`에는 리뷰 k의 대상 파일과 `<<PREV_FIX_COMMIT>>`이 고친 파일을 적는다.

마지막 작성 묶음 n이 끝나면 다음 순서로 마무리한다.
1. 리뷰 n과 **반영 n−1**을 동시에 띄운다. 반영 n−1은 `writer.md`에서 `<<TARGETS>>` = "없음", `<<PREV_BATCH>>` = n−1로 채운다.
2. 리뷰 n이 끝나면 **반영 n**을 띄운다(같은 방식).

묶음마다 사용자에게 한 줄씩 알린다. 내용은 작성 커밋, 리뷰 결과(사실 오류 수), 반영 커밋이다.

### 6. 마무리
1. 인덱스를 만들고 `docs: add chN problem index README`로 커밋한다.
   ```bash
   python3 교과서/마이크로전자회로/_tools/make_index.py 교과서/마이크로전자회로/chN "N장 <조사에서 읽은 장 제목>"
   ```
2. 검증을 돌린다. 모두 통과해야 완료다.
   ```bash
   python3 교과서/마이크로전자회로/_tools/verify_chapter.py 교과서/마이크로전자회로/chN --recrop
   for c in 교과서/마이크로전자회로/ch*/; do python3 교과서/마이크로전자회로/_tools/check_md.py "$c" | grep -c WARN; python3 교과서/마이크로전자회로/_tools/check_md.py "$c" | tail -1; done
   python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests
   ls docs/superpowers/reports/chN/
   git log --oneline main.. --grep="record review\|apply review fixes"
   ```
   - verify: 오류 0이어야 한다. INFO(연습문제가 없는 예제)는 원본에서 직접 확인해 보고에 적는다.
   - check_md: 모든 장이 오류 0, WARN 0이어야 한다.
   - 묶음마다 `review-<묶음>.md`가 있고, 그 보고서를 커밋한 반영 또는 기록 커밋이 있어야 한다.
3. 보고하고 병합·push·worktree 정리를 묻는다. 병합을 고르면 `git -C MAIN merge --ff-only feat/chN-problem-md`로 한다. main이 앞서 있으면 worktree에서 `git rebase main`을 한 뒤 fast-forward한다. worktree 삭제(`git worktree remove`)와 push는 따로 묻는다.

## 마무리 보고 형식
| 항목 | 결과 |
|---|---|
| 파일 수 | 예제 a, 연습문제 b, 장말문제 c, 합계 |
| 형식 검사 | `N개 파일, 오류 0개`, WARN 0 |
| 장 단위 검사 | 오류 0, INFO와 원본 확인 결과 |
| 그림 | 등록 수, 다시 크롭 일치 |
| 리뷰 | 묶음 수, 사실 오류 수와 반영 내용, 반영하지 않은 제안과 이유 |
| 원문 오식 | 인쇄대로 적은 곳 목록 |
| 브랜치 | worktree 경로, main 대비 커밋 수, push 안 함 |

## 자리표시자
템플릿의 `<<이름>>`을 아래 값으로 바꾼다. 경로는 절대 경로로 넣는다.

| 자리표시자 | 템플릿 | 값 |
|---|---|---|
| `<<N>>` | 전부 | 장 번호 (예: 12) |
| `<<REPO>>` | survey, common | worktree 절대 경로 |
| `<<PDF>>` | survey, common | `교과서/마이크로전자회로/N장.pdf` |
| `<<CH>>` | common | `교과서/마이크로전자회로/chN` |
| `<<SCRATCH>>` | survey, common | 세션 scratchpad 절대 경로 |
| `<<PAGE_MAP>>` | common | 조사 결과의 쪽 대응 표, 예제 표, 장말문제 표와 목록 |
| `<<COMMON>>` | writer, reviewer | `SCRATCH/COMMON-chN.md` 절대 경로 |
| `<<BATCH>>` | writer, reviewer | 이번 묶음 이름 |
| `<<TARGETS>>` | writer, reviewer | 대상 id 범위. 마무리 반영에서는 "없음" |
| `<<LOCATIONS>>` | writer | 조사 결과 중 이번 묶음의 위치 행 |
| `<<EXPECTED_TOTAL>>` | writer | 이 묶음을 마친 뒤 chN의 md 총수 |
| `<<BUSY_FILES>>` | writer | 지금 리뷰 중인 파일 |
| `<<PREV_BATCH>>` | writer | 반영할 리뷰의 묶음 이름 |
| `<<PREV_TARGETS>>` | writer | 그 묶음의 대상 id 범위 |
| `<<PREV_REVIEW>>` | writer | 그 보고서 경로 `docs/superpowers/reports/chN/review-<묶음>.md` 또는 "없음" |
| `<<COMMIT>>` | reviewer | 리뷰 대상 add 커밋 해시 |
| `<<FLAGS>>` | reviewer | 작성자가 보고한 판독이 애매했던 곳 |
| `<<REPORT>>` | reviewer | `docs/superpowers/reports/chN/review-<묶음>.md` |
| `<<PREV_FIX_COMMIT>>` | reviewer | 확인할 반영 커밋 해시 또는 "없음" |
