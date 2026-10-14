# Themed Scrollbar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 정리노트·문제설명 템플릿 2개와 기존 노트 HTML 11개에 ML/bio 저장소와 같은 테마 스크롤바(토큰 3블록 + 규칙 5줄)를 넣는다.

**Architecture:** 공통 CSS 파일 없이 텍스트 삽입만 한다. scratchpad의 삽입 스크립트 하나가 앵커 4개를 파일마다 정확히 1번씩 찾아 줄을 덧붙이며, 템플릿과 결과물에 같은 스크립트를 쓴다. 템플릿 쪽은 스킬별 문자열 테스트로 고정한다.

**Tech Stack:** Python 3 (표준 라이브러리), unittest(pytest로 실행), 내장 브라우저 확인.

**Spec:** 이 세션의 `/grill-yourself` 설계 "전자회로2 노트 템플릿에 테마 스크롤바 적용"(2026-10-13). 결정 #1–#9와 Needs-you #A(이미 실패 중인 `test_template_is_identical_to_ml` 그대로 둠), #B(브랜치 커밋까지만, 병합·push 없음)는 확정됨. 필요한 값은 아래에 모두 옮겨 둠.

## Global Constraints

- 라이트 토큰: `--scroll: #c9d0db; --scroll-hover: #9aa3b2;` / 다크 토큰: `--scroll: #3f414b; --scroll-hover: #5b5e6a;`
- 규칙 5줄(4칸 들여쓰기, 원문 그대로):
  ```css
      .content::-webkit-scrollbar, .panel-inner::-webkit-scrollbar { width: 8px; }
      .content::-webkit-scrollbar-track, .panel-inner::-webkit-scrollbar-track { background: transparent; }
      .content::-webkit-scrollbar-thumb, .panel-inner::-webkit-scrollbar-thumb { background: var(--scroll); border-radius: 8px; border: 2px solid var(--bg); }
      .content::-webkit-scrollbar-thumb:hover, .panel-inner::-webkit-scrollbar-thumb:hover { background: var(--scroll-hover); }
      @supports (scrollbar-color: auto) { .content, .panel-inner { scrollbar-width: thin; scrollbar-color: var(--scroll) transparent; } }
  ```
- 앵커와 삽입 위치(모두 파일마다 정확히 1회, 13파일 사전 확인 완료):
  | 앵커 | 뒤에 붙일 줄 |
  |---|---|
  | `\n      color-scheme: light;\n` | `      --scroll: #c9d0db; --scroll-hover: #9aa3b2;\n` |
  | `\n        color-scheme: dark;\n` | `        --scroll: #3f414b; --scroll-hover: #5b5e6a;\n` |
  | `\n      color-scheme: dark;\n` | `      --scroll: #3f414b; --scroll-hover: #5b5e6a;\n` |
  | `\n    .panel-inner { flex: 1 1 auto; min-height: 0; overflow-y: auto; overscroll-behavior: contain; padding: var(--s4) var(--s4) var(--s6); }\n` | 규칙 5줄 |
- `--scrollbar: 16px;`(패널 폭 계산용)는 그대로 둔다.
- 편집은 `.claude/skills/...` 원본 경로에서만 한다. `.agents/skills/*`는 심볼릭 링크다.
- 제외: `scripts/ec2_report/templates/cover.html`, `workbook/templates/*.html`, `ec2-review-video`, `ec2-solution-video`, `복습영상/**/성능시험/**` 스냅샷, `.katex-display`/`.table-wrap`/`table`/`math-pan`.
- 작업 트리에 다른 작업의 미커밋 변경(`scripts/ec2_report/*`, `tests/ec2_report/*`, `설계과제/*`, `docs/notion-probe.md`, `.claude/skills/ec2-sync-notion/*`, `.claude/skills/ec2-write-design-report/*`)이 있다. 건드리지 말고 `git add`는 경로를 지정한다.
- pytest 실행: `uv run -q --no-project --with pytest python -m pytest -q <tests dir>`
- 수정 후 `ec2-problem-explain/assets/note-template.html` sha256은 ML 현재 템플릿과 같은 `8fb9b290d05141cee8389c393e20a94babbca73e51ce07992a123ab615e756d9`여야 한다.
- 커밋 trailer: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

## Review Focus

1. 6칸 다크 앵커가 8칸 줄 안에서 잡히는 경우: 파일마다 LIGHT가 1번, DARK가 2번이어야 한다. Task 1의 테스트와 Task 2 Step 3의 검사가 이를 확인한다.
2. 스크립트를 다시 돌리는 경우: 이미 `--scroll:`이 있으면 바이트 변경 없이 건너뛰어야 한다. Task 1 Step 4에서 두 번 실행해 확인한다.
3. 문제설명 HTML만 고치고 manifest를 그대로 두는 경우: `check_artifacts`가 "생성 파일 변경"으로 거부한다. Task 2 Step 4에서 해시가 일치하는지 확인한다.
4. 템플릿이 ML 원본과 바이트까지 같아졌는지: provenance가 틀린 해시를 기록하면 안 된다. Task 1 Step 6에서 sha가 일치하는지 확인한다.
5. 다른 작업의 미커밋 변경이 커밋에 섞이는 경우: 각 커밋 뒤 `git show --stat HEAD`에 허용된 경로만 있어야 한다.

---

### Task 1: 템플릿 2개 + 스크롤바 테스트 + provenance

**Files:**
- Create: `/private/tmp/claude-501/-Users-hyunjun-macbook-pro-Documents-Univ-----2/943bcd1f-fcf5-4a07-9463-823c586314a3/scratchpad/insert_scrollbar.py`(이하 `$SCRATCH/insert_scrollbar.py`)
- Create: `.claude/skills/ec2-review-pack/tests/test_scrollbar_theme.py`
- Create: `.claude/skills/ec2-problem-explain/tests/test_scrollbar_theme.py`
- Modify: `.claude/skills/ec2-review-pack/assets/note-template.html:17,32,39,226`
- Modify: `.claude/skills/ec2-problem-explain/assets/note-template.html:17,32,39,235`
- Modify: `.claude/skills/ec2-problem-explain/assets/template-provenance.json`(`source_sha256`, `token_source_sha256`)

**Interfaces:**
- Produces: `insert_scrollbar.py FILE...` CLI. 파일마다 `patched` 또는 `skipped`를 출력한다. 앵커 수가 1이 아니면 `AssertionError`로 멈추고 그 파일은 쓰지 않는다. 내부 함수는 `patch(path: Path) -> bool`(바꿨으면 True)이다. Task 2에서 그대로 쓴다.

- [ ] **Step 1: 브랜치와 기준선**

```bash
git switch -c feat/themed-scrollbar
git worktree add --detach "$SCRATCH/base" HEAD
uv run -q --no-project --with pytest python -m pytest -q "$SCRATCH/base/.claude/skills/ec2-review-pack/tests" "$SCRATCH/base/.claude/skills/ec2-problem-explain/tests" 2>&1 | tail -15 > "$SCRATCH/baseline.txt"
```
Expected: `baseline.txt`에 실패 목록이 기록된다. `test_template_is_identical_to_ml`은 ML 저장소가 있으면 FAIL이고, 이 실패는 정상이다.

- [ ] **Step 2: 실패하는 테스트 작성(두 스킬 동일 내용, unittest)**

`TEMPLATE = Path(__file__).resolve().parents[1] / 'assets' / 'note-template.html'`

`class TestScrollbarTheme(unittest.TestCase)`:
- `test_tokens_in_every_theme_block`
  - `len(re.findall(r'--scroll: #[0-9a-f]{6}; --scroll-hover: #[0-9a-f]{6};', text)) == 3`
  - `text.count(LIGHT) == 1`
  - `text.count(DARK) == 2`
- `test_rules_cover_both_scroll_containers`: 다음 4개 문자열을 subTest로 확인한다.
  - `'.content::-webkit-scrollbar, .panel-inner::-webkit-scrollbar { width: 8px; }'`
  - `'.content::-webkit-scrollbar-thumb, .panel-inner::-webkit-scrollbar-thumb { background: var(--scroll);'`
  - `'.content::-webkit-scrollbar-thumb:hover, .panel-inner::-webkit-scrollbar-thumb:hover { background: var(--scroll-hover); }'`
  - `'scrollbar-color: var(--scroll) transparent;'`
- `test_panel_width_variable_kept`: `'--scrollbar: 16px;' in text`
- `test_math_pan_still_hidden`: problem-explain 파일에만 둔다. `'.math-row.math-pan::-webkit-scrollbar { display:none; }' in text`

- [ ] **Step 3: 실패 확인**

Run: `uv run -q --no-project --with pytest python -m pytest -q .claude/skills/ec2-review-pack/tests/test_scrollbar_theme.py .claude/skills/ec2-problem-explain/tests/test_scrollbar_theme.py`
Expected: `test_tokens_in_every_theme_block`, `test_rules_cover_both_scroll_containers`가 두 스킬에서 FAIL(4 failed). 나머지는 PASS.

- [ ] **Step 4: 삽입 스크립트 작성 후 템플릿에 실행**

`patch(path)`는 다음 순서로 동작한다.
1. 텍스트를 읽는다.
2. `'--scroll:'`이 이미 있으면 False를 반환한다.
3. Global Constraints 표의 4개 `(anchor, insert)` 쌍마다 `assert text.count(anchor) == 1`을 확인하고 `text.replace(anchor, anchor + insert, 1)`로 바꾼다. 앵커가 `\n`으로 시작하고 끝나므로 `anchor + insert`는 줄 단위로 삽입된다.
4. 모든 assert가 통과한 뒤에만 쓴다. 읽을 때와 쓸 때 모두 `newline=''`을 지정해 바이트를 보존한다.

```bash
python3 "$SCRATCH/insert_scrollbar.py" .claude/skills/ec2-review-pack/assets/note-template.html .claude/skills/ec2-problem-explain/assets/note-template.html
python3 "$SCRATCH/insert_scrollbar.py" .claude/skills/ec2-review-pack/assets/note-template.html .claude/skills/ec2-problem-explain/assets/note-template.html
git diff --numstat -- .claude/skills/*/assets/note-template.html
```
Expected:
- 첫 실행: `patched` 2개
- 두 번째 실행: `skipped` 2개
- numstat: 두 파일 모두 `8	0`

- [ ] **Step 5: 테스트 통과 확인**

Run: Step 3과 같은 명령
Expected: 모두 PASS

- [ ] **Step 6: provenance 갱신**

```bash
shasum -a 256 .claude/skills/ec2-problem-explain/assets/note-template.html .claude/skills/ec2-review-pack/assets/note-template.html
```
- Expected: problem-explain 템플릿 해시가 `8fb9b290…756d9`와 같다. 다르면 멈추고 `diff ../머신러닝기초/.claude/skills/ml-problem-explain/assets/note-template.html …`로 원인을 확인한다.
- `template-provenance.json`의 `source_sha256`을 problem-explain 템플릿 해시로, `token_source_sha256`을 review-pack 템플릿 해시로 바꾼다. 다른 필드와 포맷(2칸 들여쓰기, 끝 개행)은 그대로 둔다.

- [ ] **Step 7: 전체 스킬 테스트를 기준선과 비교**

Run: `uv run -q --no-project --with pytest python -m pytest -q .claude/skills/ec2-review-pack/tests .claude/skills/ec2-problem-explain/tests 2>&1 | tail -15`
Expected: 실패 목록이 `baseline.txt`와 같거나 그 부분집합이다. 새 테스트 7개(review-pack 3, problem-explain 4)가 추가로 PASS한다.

- [ ] **Step 8: 커밋**

```bash
git add .claude/skills/ec2-review-pack/assets/note-template.html .claude/skills/ec2-problem-explain/assets/note-template.html .claude/skills/ec2-problem-explain/assets/template-provenance.json .claude/skills/ec2-review-pack/tests/test_scrollbar_theme.py .claude/skills/ec2-problem-explain/tests/test_scrollbar_theme.py
git commit -m "feat(skills): themed panel scrollbar in note templates" -m "Add --scroll/--scroll-hover tokens to the three theme blocks and thin themed scrollbar rules for .content/.panel-inner in the review-pack and problem-explain note templates (byte-aligned with ML). Refresh template provenance hashes and add string-level tests." -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git show --stat HEAD
```
Expected: stat에 위 5개 경로만 있다.

---

### Task 2: 기존 노트 HTML 11개 + 1007 manifest + 브라우저 확인

**Files:**
- Modify: `복습노트/{0902,0904,0909,0911,0916,0918,0923,0930,1002,1007}/정리노트_*.html`(10개)
- Modify: `복습노트/1007/문제설명_1007_Differential_Amplifiers.html`
- Modify: `복습노트/1007/자료_문제설명_1007_Differential_Amplifiers/manifest.json:111`

**Interfaces:**
- Consumes: Task 1의 `$SCRATCH/insert_scrollbar.py FILE...`

- [ ] **Step 1: 결과물에 삽입**

```bash
python3 "$SCRATCH/insert_scrollbar.py" 복습노트/*/정리노트_*.html 복습노트/1007/문제설명_1007_Differential_Amplifiers.html
```
Expected: `patched` 11개. AssertionError가 나면 해당 파일은 쓰지 않았으므로, 그 파일의 앵커를 확인한 뒤 보고한다.

- [ ] **Step 2: diff 형태 확인**

Run: `git -c core.quotepath=off diff --numstat -- 복습노트/`
Expected: 11줄 모두 `8	0`이고 다른 파일은 없다.

- [ ] **Step 3: 파일별 토큰 수 확인**

Run: `for f in 복습노트/*/정리노트_*.html 복습노트/1007/문제설명_*.html; do echo "$(grep -c -- '--scroll: #c9d0db' "$f") $(grep -c -- '--scroll: #3f414b' "$f") $(grep -c 'scrollbar-color: var(--scroll) transparent' "$f") $f"; done`
Expected: 모든 줄이 `1 2 1 …`이다.

- [ ] **Step 4: manifest 해시 갱신**

- `manifest.json`의 `"문제설명_1007_Differential_Amplifiers.html"` 값을 새 `shasum -a 256` 값으로 바꾼다. 다른 줄은 바꾸지 않는다.
- Run: `python3 -c "import json,hashlib,pathlib as p; d=p.Path('복습노트/1007'); m=json.loads((d/'자료_문제설명_1007_Differential_Amplifiers/manifest.json').read_text()); bad=[k for k,v in m['files'].items() if hashlib.sha256((d/k).read_bytes()).hexdigest()!=v]; print(bad or 'OK')"`
- Expected: `OK`

- [ ] **Step 5: 브라우저 확인**

- 내장 브라우저로 `file://…/복습노트/1007/정리노트_1007_Differential_Amplifiers.html`을 연다.
- `javascript_tool`로 `document.documentElement.dataset.theme='light'`을 설정한 뒤 다음 값을 읽는다.
  - `getComputedStyle(document.querySelector('.content')).scrollbarColor`
  - `.panel-inner` 하나의 같은 값
- `'dark'`로 바꿔 같은 값을 다시 읽는다.
- Expected:
  - light: `rgb(201, 208, 219) rgba(0, 0, 0, 0)`
  - dark: `rgb(63, 65, 75) rgba(0, 0, 0, 0)`
  - `.content`와 `.panel-inner`가 같은 값이다.
- 다크 상태에서 스크린샷 1장을 남긴다. 문제설명 HTML도 dark 값을 한 번 확인한다.

- [ ] **Step 6: 커밋과 정리**

```bash
git add 복습노트/*/정리노트_*.html 복습노트/1007/문제설명_1007_Differential_Amplifiers.html 복습노트/1007/자료_문제설명_1007_Differential_Amplifiers/manifest.json
git commit -m "docs(notes): themed scrollbar in existing note HTML" -m "Insert the same scrollbar tokens and rules into the 11 committed note HTML files and refresh the problem-explain manifest hash." -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git show --stat HEAD
git worktree remove "$SCRATCH/base"
git status --short
```
Expected:
- stat에 위 12개 경로만 있다.
- `git status`에는 작업 시작 전부터 있던 다른 작업의 변경만 남는다.
- 병합과 push는 하지 않는다(#B).
