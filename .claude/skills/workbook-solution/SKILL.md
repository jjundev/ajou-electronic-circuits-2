---
name: workbook-solution
description: 문제집 md(교과서 ch09–11, 기출)의 `## 풀이`를 작성자·리뷰어 배치로 쓰고 독립 풀이로 검산한다. "풀이 써줘", "chNN 풀이 채워", 특정 문제 풀이 다시 쓰기, /workbook-solution <라벨> 같은 요청에 쓴다.
---

# 문제집 풀이 (`workbook-solution`)

문제 md 끝에 `## 풀이`를 쓴다. 작성자가 풀고 모든 수치를 **검산**해서 쓰고, 리뷰어가 **독립 풀이**로 다시 풀어 대조한다.

## 고정 규칙
- 풀이 내용의 기준은 `references/rules.md` 하나다. 모양(`### 소절`, 마지막 `### 답`)은 `교과서/마이크로전자회로/FORMAT.md` '문제집용 절'과 `check_md.py`가 정한다.
- 서브에이전트는 모두 `Agent`(subagent_type `general-purpose`, model `opus`)로 띄운다. 프롬프트는 템플릿을 채운 파일을 `SCRATCH/sol/<라벨>/`에 쓰고 "이 파일을 읽고 그대로 따르라"로 준다.
- 워크트리 하나에 작성자는 한 번에 한 명이다(git index 공유). 리뷰어는 배치마다 background로 띄우고 기다리지 않는다.
- 스킬 파일은 `<<SKILL>>` 경로(병합 뒤에는 main checkout)에서 읽게 한다. 스킬 수정은 오케스트레이터만 하고 main에서 커밋한다.
- `git add`는 경로를 명시한다. 커밋 끝에 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. push, main 병합, 워크트리 삭제는 사용자에게 묻는다.
- 작업 중 빌드는 `--pdf-dir workbook/build/pdf`. `workbook/pdf/`는 모든 라벨을 모은 뒤 한 번만 다시 만든다.

## 멈추고 묻는 경우 (이 셋뿐)
1. 리뷰가 `rules.md` 자체를 바꿔야 할 문제를 찾았을 때. 바꿀 문장과 이미 쓴 풀이에 소급할지를 함께 묻는다.
2. 완료 검사가 실패했을 때.
3. 병합, push, 워크트리 정리.

그 밖에는 묻지 않고 진행하고, 배치마다 한 줄씩 알린다(작성 커밋, 리뷰 [높음] 수, 반영 커밋).

## 절차

### 1. 입력과 워크트리
- 라벨 `L`: `ch09` | `ch10` | `ch11` | `exams`. 특정 id만 다시 쓸 때는 그 id 목록이 대상이고 배치 하나로 끝낸다.
- 폴더 순서 `F…`
  - 교과서: `교과서/마이크로전자회로/L/예제` → `…/연습문제` → `…/장말문제`
  - 기출: `from_the_past/md/2021-1_중간` → `2021-1_기말` → `2023-1_중간` → `2023-1_기말` (폴더 하나가 배치 하나)
  - 2013–2019 중간고사(라벨 `exams-2013-2019`): `2013-1_중간` → `2014-1_중간` → `2015-1_중간` → `2015-2_중간` → `2016-1_중간` → `2017-1_중간_D반` → `2017-1_중간_C030` → `2018-2_중간` → `2019-1_중간`. 원본이 모범답안이므로, 독립 풀이를 쓴 뒤 리뷰어가 손글씨 모범답안 값과 대조해 다른 곳을 보고서에 적는다(모범답안이 틀릴 수도 있다)
- 워크트리 `WT` = `MAIN/.claude/worktrees/sol-L`, 브랜치 `claude/sol-L`. 없으면 만든다.
  ```bash
  git -C MAIN worktree add .claude/worktrees/sol-L -b claude/sol-L main
  ```
- 완료 기준: `git -C WT status --short`가 비어 있다(재개라면 2로).

### 2. 재개 판단
- 남은 문제: 폴더마다 `python3 workbook/source_pages.py missing <F> --section 풀이`.
- 끝난 리뷰: `docs/superpowers/reports/L/sol-<X>.md`. `.part`만 있으면 끊긴 리뷰다. `.part`를 지우고 그 배치 리뷰를 다시 띄운다.
- 반영 안 된 리뷰: `git -C WT log --oneline -1 -- <보고서>`가 비어 있는 보고서.
- 다음 배치 글자: `git -C WT log --oneline main.. --grep="solutions batch"`의 마지막 글자 다음.

### 3. 배치 루프
1. 대상: WT에서 `python3 workbook/source_pages.py next <현재 F> --section 풀이 --size 10`(기출은 `--size 20`). 비었으면 다음 폴더로, 모든 폴더가 비었으면 4로.
2. 작성자: `references/writer.md`를 채워 띄운다. `<<REPORTS>>`에는 끝났고(`.part` 아님) 아직 반영 안 된 보고서를 모두 넣는다. 끝나면 최종 메시지에서 커밋 해시, 애매한 곳, 조건 문제를 받는다.
3. 리뷰어: `references/reviewer.md`를 채워 background로 띄운다. `<<FLAGS>>`에는 작성자의 애매한 곳과 조건 문제를 그대로 붙인다. 작성자의 답 요약은 넣지 않는다(독립 풀이를 흐리지 않게).
4. 배치 글자를 올리고 1로.
5. 교훈: 리뷰에 [높음]이 있거나 같은 지적이 두 배치 이상 나오면, 그 교훈 한 줄을 `references/lessons.md`에 더해 main에서 `docs(skill): add solution lesson`으로 커밋한다. 규칙 자체를 바꿔야 하면 멈추고 묻는다.

### 4. 마무리
1. 모든 리뷰어가 끝나기를 기다린다. 반영 안 된 보고서가 있으면 작성자를 "반영만" 모드(`<<TARGETS>>` = 없음)로 띄운다.
2. 완료 검사. 모두 통과해야 완료다.
   ```bash
   cd WT
   for f in <F…>; do python3 workbook/source_pages.py missing "$f" --section 풀이 >/dev/null || echo "남음 $f"; done
   <<CHECK_CMD>>                                   # 교과서는 장 폴더, 기출은 시험 폴더마다. 오류 0
   python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests 2>&1 | tail -1
   python3 -m unittest discover -s from_the_past/md/_tools/tests 2>&1 | tail -1
   python3 -m unittest discover -s workbook/tests 2>&1 | tail -1
   python3 workbook/build_workbook.py <L 또는 시험 폴더 이름> --pdf-dir workbook/build/pdf 2>&1 | grep -E "OVERFLOW|ERROR"   # 비어야 함
   ls docs/superpowers/reports/L/*.part 2>/dev/null                                                                     # 비어야 함
   for r in docs/superpowers/reports/L/sol-*.md; do git log --oneline -1 -- "$r" | grep -q . || echo "미반영 $r"; done  # 비어야 함
   ```
3. 보고하고 병합을 묻는다. 병합은 WT에서 `git rebase main` 뒤 `git -C MAIN merge --ff-only claude/sol-L`. 먼저 `git -C MAIN branch --show-current`가 `main`인지 확인한다.

## 마무리 보고 형식
| 항목 | 결과 |
|---|---|
| 풀이 수 | 예제 a, 연습문제 b, 장말문제 c (기출은 시험별) |
| 검사 | check 오류 0, 테스트 3묶음 OK, OVERFLOW 0 |
| 리뷰 | 배치 수, [높음] 지적 수와 유형, 반영하지 않은 지적과 이유 |
| 예제 대조 | 교재 값과 다른 예제 목록과 이유 |
| 조건 수정 | 고친 문제 목록 |
| 브랜치 | 워크트리, main 대비 커밋 수, push 안 함 |

## 자리표시자
경로는 절대 경로로 넣는다.

| 자리표시자 | 템플릿 | 값 |
|---|---|---|
| `<<LABEL>>` | writer, reviewer | `ch09` · `ch10` · `ch11` · `exams` |
| `<<BATCH>>` | writer, reviewer | 배치 글자 (A, B, …) |
| `<<WT>>` | writer, reviewer | 워크트리 절대 경로 |
| `<<SKILL>>` | writer, reviewer | 스킬 폴더 절대 경로. 파일럿 병합 전에는 `WT09/.claude/skills/workbook-solution`, 뒤에는 `MAIN/.claude/skills/workbook-solution` |
| `<<REPORTS>>` | writer | 반영할 보고서 경로들 또는 "없음" |
| `<<TARGETS>>` | writer, reviewer | 대상 md 경로들 또는 "없음"(반영만) |
| `<<PAGES>>` | writer, reviewer | `SCRATCH/sol/<라벨>/<배치>` |
| `<<CHECK_CMD>>` | writer, reviewer | 교과서 `python3 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/<장>`, 기출 `python3 from_the_past/md/_tools/check_exam.py <시험 폴더>` |
| `<<COMMIT>>` | reviewer | 작성자의 `add … solutions batch` 커밋 해시 |
| `<<FLAGS>>` | reviewer | 작성자가 보고한 애매한 곳과 조건 문제 |
| `<<REPORT>>` | reviewer | `docs/superpowers/reports/<라벨>/sol-<배치>.md` |
