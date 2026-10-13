# ec2-problem-explain Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 복습팩 problems.txt의 workbook 문제마다 일곱 구역 입문 설명 HTML+MD를 만들고, 네 실제 검토를 통과해야만 `복습노트/<range>/`에 발행하는 로컬 스킬 `ec2-problem-explain`을 만든다.

**Architecture:** 머신러닝기초 `ml-problem-explain`(`~/Documents/Univ/머신러닝기초/.claude/skills/ml-problem-explain/`, 이하 ML)을 포크한다. 계약·라벨·렌더·CLI는 거의 그대로 옮기고, 소스 어댑터만 HTML 카드 대신 problems.txt → 문제 md(`workbook/problem.py`)로 교체한다. 전자회로2에 없는 발행 계층(잠금·백업·교체·복구)은 ML `ml-review-pack/scripts/review_pdf_publish.py`에서 이식한다.

**Tech Stack:** Python 3.10+(stdlib + 저장소가 이미 쓰는 PyYAML), unittest, 로컬 KaTeX/Pretendard. 독립 검산용 SymPy는 스킬 실행 시에만 필요.

**Spec:** `docs/superpowers/specs/2026-10-13-ec2-problem-explain-design.md`

## Global Constraints

- 스킬 루트 `.claude/skills/ec2-problem-explain/`, 모듈 접두사 `epe_`, 등록은 `.agents/skills/ec2-problem-explain` → `../../.claude/skills/ec2-problem-explain` 상대 심볼릭 링크.
- 테스트는 unittest(전자회로2에 pytest 없음): `python3 -m unittest discover -s .claude/skills/ec2-problem-explain/tests`.
- 대상 인자는 `MMDD`, `MMDD-MMDD`, 없음뿐. 기출 회차·id 목록·HTML 경로는 받지 않는다.
- 산출 이름: `문제설명_<range>_<slug>.html/.md`, `figures_문제설명_<range>_<slug>/`, `자료_문제설명_<range>_<slug>/`. 읽음 키 `ec2-problem-explain-review-<range>-<slug>`. profile 값은 `'review'` 하나.
- 일곱 구역 순서 `understand → recall → start → solve → verify → pitfall → retry`, recall 제목 "이 문제를 봤을 때 떠올릴 개념과 공식", 우측 요약 그룹 "떠올릴 개념·공식".
- 원 md·PDF·정리노트·그림을 쓰거나 지우지 않는다. 설명 소유 파일만 백업 후 교체.
- 파일명·폴더명 비교는 모두 NFC(macOS NFD 혼재).
- 문구는 `~해요` 체, 영어 전문용어 병기.
- SKILL.md frontmatter `description`은 따옴표로 감싼다(커밋 `986a3b7`의 YAML 파싱 오류 재발 방지).
- 커밋 메시지 끝: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. NFD로 저장된 `복습노트/<range>` 폴더·파일명 → NFC 인자로 찾아져야 한다. (Task 2 `test_nfd_folder_resolves`)
2. problems.txt의 빈 줄·뒤 공백·`|` 없는 줄 → 빈 줄은 무시, 형식 오류 줄은 줄 번호와 함께 ExplainError. (Task 2 `test_problems_txt_blank_and_malformed_lines`)
3. 한국어 기출 md처럼 `## 원문`이 없는 문항 → 원문 블록 없이 조립되고 check가 원문 누락으로 실패하지 않아야 한다. (Task 3 `test_exam_without_original_builds`)
4. build 후 문제 그림 PNG나 md가 바뀐 경우 → publish가 "입력 변경"으로 거부하고 기존 파일 유지. (Task 4 `test_changed_figure_or_md_refuses_publish`)
5. 범위 인자 안에 problems.txt 없는 날짜 폴더가 섞인 경우 → 그 폴더는 건너뛰고 나머지 팩만 대상. 전부 없으면 "문제 없는 팩" 오류. (Task 2 `test_range_skips_packs_without_problems`)

---

### Task 1: 스킬 골격, 계약, 라벨, 테스트 도우미

**Files:**
- Create: `.claude/skills/ec2-problem-explain/scripts/epe_types.py` (ML `mpe_types.py` 복사, `SourcePack`에 필드 추가)
- Create: `.claude/skills/ec2-problem-explain/scripts/epe_shared.py`
- Create: `.claude/skills/ec2-problem-explain/scripts/epe_contract.py` (ML `mpe_contract.py` 복사, import만 `epe_*`)
- Create: `.claude/skills/ec2-problem-explain/scripts/epe_labels.py` (ML `mpe_labels.py` 복사 후 수정)
- Create: `.claude/skills/ec2-problem-explain/assets/` (ML `assets/` 전체 복사, `note-template.html`의 `:root`·다크모드 색 토큰 블록만 `.claude/skills/ec2-review-pack/assets/note-template.html`의 것으로 교체, `template-provenance.json`에 두 원본 경로·SHA-256 기록)
- Create: `.agents/skills/ec2-problem-explain` (심볼릭 링크)
- Create: `.claude/skills/ec2-problem-explain/tests/_util.py`
- Test: `.claude/skills/ec2-problem-explain/tests/test_contract.py`, `tests/test_labels.py`

**Interfaces:**
- Produces:
  - `Problem(id: str, number: int, title: str, source: str, original_html: str, conditions_html: str, ask_html: str, figures_html: tuple[str, ...], reference_steps: tuple[str, ...], reference_answer: str, subparts: tuple[str, ...])` — `id`는 `p1, p2, …`(위치 기반, 파일명·anchor 안전), `source`는 workbook id 포함 표시 문자열.
  - `SourcePack(profile: str, range: str, slug: str, path: Path, sha256: str, problems: tuple[Problem, ...], inputs: tuple[str, ...])` — `path`는 problems.txt 절대 경로, `inputs`는 해시에 묶인 파일 절대 경로 문자열(problems.txt, md, 그림 순).
  - `ExplainError(ValueError)`, `Artifacts(html, md, manifest, files)`.
  - `epe_shared`: `REPO: Path`(= 스킬 `parents[2]`), 그리고 `load_problem, html_fields, problem_figures, solution, ProblemError`(workbook/problem.py), `TEXTBOOK_ID_RE, EXAM_ID_RE, KIND_DIR`(workbook/assemble.py), `textbook_figure_filename, exam_figure_filename`, `Node, Ctx, convert, check_md, parse, inner, outer`(html2md), `math_delimiter_errors`(ec2-review-pack check_html), `compact(s: str) -> str`.
  - `epe_contract`: `KEYS`, `payload_hash(pack, fragments) -> str`, `markup_errors(root, allow_summary=False) -> list[str]`, `validate_fragment(problem, fragment) -> list[str]`, `initial_reviews(pack, fragments) -> dict`, `validate_reviews(pack, fragments, reviews) -> list[str]` — ML과 동일 의미.
  - `epe_labels.normalize_subpart_labels(markup: str) -> str` — 라벨 `[a-z]`와 `[1-9]\d*` 모두 처리.
  - `tests/_util.py`: `make_repo(tmp: Path, *, range_='1007', slug='Diff_Amp', ids=('P10.02', '2023-1_중간-Q4'), nfd=False) -> Path` — 실제 저장소에서 해당 md, 그 장/회차의 `figures.yaml`·`exam.yaml`·참조 PNG(기출은 `redrawn/` 포함)를 tmp 저장소의 같은 상대 경로로 복사하고, `복습노트/<range>/problems.txt`(`id | 설명` 줄), `정리노트_<range>_<slug>.html`(`<article class="topic" id="s1-diff">` 포함 최소 HTML), `복습문제_<range>_<slug>-문제.pdf`(더미 바이트)를 만든다. `fragment(problem) -> str`, `approved(pack, fragments, artifacts=None) -> dict`은 ML `tests/helpers.py`와 같은 의미.

`compact`는 html2md에 없으면 ML `review_pdf_cards.compact`와 같은 의미(공백 정규화)로 `epe_shared`에 정의한다. `epe_shared`는 `REPO/workbook`, `REPO/.claude/skills/ec2-review-pack/scripts`를 `sys.path`에 넣는다(`workbook/paths.py` import가 교과서·기출 `_tools`를 추가함).

- [ ] **Step 1: 테스트 작성** — ML `tests/test_contract.py`, `tests/test_labels.py`를 unittest로 옮기고(`import _util` 먼저), 다음을 추가:

```python
def test_numeric_subparts_required_in_solve_and_verify(self):
    p = replace(problem(), subparts=('1', '2'))
    self.assertEqual(validate_fragment(p, fragment(p)), [])
    broken = fragment(p).replace('data-subpart="2"', 'data-subpart="3"', 1)
    self.assertTrue(any('모든 소문항' in e for e in validate_fragment(p, broken)))

def test_numeric_label_prefix_removed_under_heading(self):
    src = ('<div data-explanation="solve"><div data-subpart="1"><h4>(1)</h4>'
           '<p>(1) 이득을 구해요.</p></div></div>')
    self.assertIn('<p>이득을 구해요.</p>', normalize_subpart_labels(src))
```

- [ ] **Step 2: 실패 확인** — Run: `python3 -m unittest discover -s .claude/skills/ec2-problem-explain/tests -v` / Expected: `ModuleNotFoundError: No module named 'epe_contract'`
- [ ] **Step 3: 구현** — 위 파일을 복사·수정한다. `epe_labels`에서 `re.fullmatch('[a-z]', label)`를 `re.fullmatch(r'[a-z]|[1-9]\d*', label)`로 바꾸고 정규식에 `re.escape(label)`을 쓴다. 심볼릭 링크: `ln -s ../../.claude/skills/ec2-problem-explain .agents/skills/ec2-problem-explain`.
- [ ] **Step 4: 통과 확인** — 같은 명령 / Expected: `OK`
- [ ] **Step 5: 커밋**

```bash
git add .claude/skills/ec2-problem-explain .agents/skills/ec2-problem-explain
git commit -m "feat(ec2-problem-explain): add contract, labels and assets"
```

### Task 2: problems.txt → 문제 md 소스 어댑터

**Files:**
- Create: `.claude/skills/ec2-problem-explain/scripts/epe_source.py`
- Test: `.claude/skills/ec2-problem-explain/tests/test_source.py`

**Interfaces:**
- Consumes: Task 1 `Problem`, `SourcePack`, `ExplainError`, `epe_shared` 재수출.
- Produces:
  - `nfc(value) -> str`, `sha256(path: Path) -> str`, `inside(path: Path, repo: Path) -> Path`, `existing_path(path: Path) -> Path` — ML `mpe_source`와 같은 의미.
  - `resolve_sources(repo: Path, target: str | None) -> tuple[Path, ...]` — problems.txt 절대 경로들, 이름순.
  - `md_path(repo: Path, pid: str) -> Path` — `TEXTBOOK_ID_RE` → `교과서/마이크로전자회로/chNN/<KIND_DIR>/<id>.md`, `EXAM_ID_RE` → `from_the_past/md/<회차>/Q<n>.md`. 형식 오류·파일 없음은 ExplainError.
  - `figure_paths(p) -> list[Path]` — `problem_figures(p)` 순서. 교과서는 `p.figures_dir / textbook_figure_filename(id, crop)`, 기출은 `figures/redrawn/fig-<id>.png`가 있으면 그것, 없으면 `figures/fig-<id>.png`.
  - `subparts(ask_html: str) -> tuple[str, ...]`
  - `load_source(path: Path, repo: Path) -> SourcePack`

`resolve_sources` 규칙: `복습노트/` 아래 폴더명을 NFC로 비교하고, problems.txt가 있는 폴더만 후보.
- `target is None` → 폴더명 끝 날짜(`split('-')[-1]`)가 가장 늦은 후보, 같은 끝 날짜 후보가 둘 이상이면 `'여러 후보'` 오류.
- `MMDD` → 그 폴더. 폴더는 있는데 problems.txt가 없으면 `'문제 없는 팩'` 오류.
- `MMDD-MMDD` → 같은 이름 폴더가 있으면 그것. 범위 안의 개별 날짜 후보도 함께 있으면 `'여러 후보'` 오류. 같은 이름이 없으면 범위 안 개별 후보 전부(없으면 `'문제 없는 팩'`).
- 날짜 형식은 ML `date_key`로 검증, 범위 역순은 `'날짜 범위 순서 오류'`.

`load_source` 규칙:
- problems.txt 줄: 빈 줄 무시, 나머지는 `^\s*(\S+)\s*\|\s*(.*\S)\s*$`. 안 맞으면 `f'problems.txt {n}행 형식 오류'`.
- slug: 같은 폴더 `정리노트_<range>_(.+)\.html`(NFC) 정확히 하나, 아니면 오류.
- 문항 i(1부터): `load_problem(md_path(...))`, `fields = html_fields(p)`.
  - `Problem(id=f'p{i}', number=i, title=p.title, source=f"{p.id} · {p.meta['kind']} {p.meta['number']}", original_html=fields.get('original', ''), conditions_html=fields['conditions'], ask_html=fields['ask'], figures_html=tuple(f'<figure><img src="{rel}" alt="그림 {p.id}"></figure>' …), reference_steps=…, reference_answer=…, subparts=subparts(fields['ask']))`
  - `rel`은 problems.txt 폴더 기준 상대 경로(`os.path.relpath`, `/` 구분, `quote(…, safe='/')`).
  - reference는 `solution(p)`가 None이면 `((), '')`, 아니면 `(tuple(s['html'] for s in steps), answer)`.
- `subparts`: 최상위 `<ul>/<ol>`의 직계 `li` 텍스트가 `^\s*\((\d+|[a-z])\)`로 시작하는지 본다. 하나도 없으면 `('main',)`, 전부면 그 라벨들(중복 시 오류), 섞이면 `'소문항 표지 불일치'` 오류.
- `sha256` 필드: problems.txt, md들, 그림들의 바이트를 순서대로 `hashlib.sha256`에 각각 `sha256(file).encode()`로 update한 hexdigest. `inputs`는 같은 순서의 경로 문자열.
- `ProblemError`, `OSError`는 문항 id를 붙여 ExplainError로 바꾼다.

- [ ] **Step 1: 테스트 작성** (`make_repo` 사용)

```python
def test_latest_pack_with_problems_is_default(self):        # 0904(problems 없음)·1007 → 1007
def test_pack_without_problems_txt_is_refused(self):         # resolve_sources(repo,'0904') → '문제 없는 팩'
def test_range_skips_packs_without_problems(self):           # 0902(없음)+0909+0911, '0902-0911' → 두 경로
def test_combined_and_individual_range_is_ambiguous(self):   # '0909-0911' 폴더 + 0909 폴더 → '여러 후보'
def test_nfd_folder_resolves(self):                          # make_repo(nfd=True), '1007' → 찾음
def test_problems_txt_blank_and_malformed_lines(self):       # 빈 줄 OK, 'P10.02' 단독 줄 → '2행 형식 오류'
def test_load_source_order_ids_and_subparts(self):
    pack = load_source(path, repo)
    self.assertEqual([p.id for p in pack.problems], ['p1', 'p2'])
    self.assertTrue(pack.problems[0].source.startswith('P10.02 · 장말문제'))
    self.assertEqual(pack.problems[0].subparts, ('main',))
    self.assertEqual(pack.problems[1].subparts, ('1', '2', '3'))
    self.assertEqual(pack.slug, 'Diff_Amp')
def test_figure_src_is_relative_repo_file(self):             # img src를 problems.txt 폴더에서 풀면 존재하는 PNG
def test_exam_prefers_redrawn_figure(self):                  # redrawn/fig-Q4.png 경로가 선택됨
def test_digest_changes_when_figure_changes(self):           # PNG 1바이트 추가 후 load_source().sha256 다름
def test_unknown_id_reports_id(self):                        # 'P99.99 | x' → 메시지에 'P99.99'
```

- [ ] **Step 2: 실패 확인** — Run: `python3 -m unittest .claude/skills/ec2-problem-explain/tests/test_source.py -v` (tests 폴더에서 discover로 실행해도 됨) / Expected: `No module named 'epe_source'`
- [ ] **Step 3: 구현** — 위 Interfaces대로 `epe_source.py` 작성. `inside`·`existing_path`·`date_key`는 ML 코드 그대로.
- [ ] **Step 4: 통과 확인** — Expected: `OK`
- [ ] **Step 5: 커밋** — `git commit -m "feat(ec2-problem-explain): read review pack problems from workbook md"`

### Task 3: 조립·기계 검사

**Files:**
- Create: `.claude/skills/ec2-problem-explain/scripts/epe_render.py` (ML `mpe_render.py` 기반)
- Test: `.claude/skills/ec2-problem-explain/tests/test_render.py`, `tests/test_layout.py` (ML 것을 unittest로 이식)

**Interfaces:**
- Consumes: Task 1 계약·라벨·shared, Task 2 `load_source`, `inside`, `existing_path`, `sha256`.
- Produces: `names(pack) -> tuple[str, str, str]`, `dump(path, value)`, `artifact_hashes(artifacts) -> dict[str, str]`, `build_explanation(pack, fragments, stage: Path, repo: Path) -> Artifacts`, `check_artifacts(pack, artifacts) -> list[str]` — ML과 같은 의미.

ML 대비 변경점만:
- `names`: profile 분기 제거. `('문제설명_<range>_<slug>', 'figures_문제설명_<range>_<slug>', '자료_문제설명_<range>_<slug>')`.
- 원문 블록: `original_html`이 비어 있지 않을 때만 `<div class="layer formal" data-original-problem="{id}"><h4>원문</h4>…</div>`를 조건 블록 앞에 넣는다. `check_artifacts`도 비어 있지 않을 때만 원문 보존을 검사한다.
- "원 문제 보기" 링크: 같은 폴더의 `복습문제_<range>_<slug>-문제.pdf`가 있으면 그 파일(anchor 없음), 없으면 링크를 생략한다.
- 템플릿 값: `title = f'전자회로2 복습 {range} 문제설명'`, `RANGE = f'ec2-problem-explain-review-{range}-{slug}'`. 나머지 문구는 ML과 같다.
- manifest `source_sha256`·입력 비교는 `pack.sha256`(Task 2 묶음 해시)를 쓴다. `manifest['inputs'] = list(pack.inputs)`를 추가한다.

- [ ] **Step 1: 테스트 작성** — ML `test_render.py`·`test_layout.py` 이식(`make_repo`+`load_source` 사용), 그리고 다음을 추가:

```python
def test_output_names_and_reading_key(self):     # html.name == '문제설명_1007_Diff_Amp.html', 본문에 'ec2-problem-explain-review-1007-Diff_Amp'
def test_figures_copied_into_owned_dir(self):    # img src가 'figures_문제설명_1007_Diff_Amp/'로 시작, 파일 존재
def test_exam_without_original_builds(self):     # 2023-1_중간-Q4(원문 없음) → check_artifacts == []
def test_problem_pdf_link_when_present(self):    # href가 '복습문제_1007_Diff_Amp-문제.pdf'
def test_tampered_conditions_detected(self):     # 생성 HTML의 조건 텍스트를 바꾸면 'conditions 원문 보존 실패'
```

- [ ] **Step 2: 실패 확인** — Expected: `No module named 'epe_render'`
- [ ] **Step 3: 구현**
- [ ] **Step 4: 통과 확인** — `python3 -m unittest discover -s .claude/skills/ec2-problem-explain/tests -v` / Expected: `OK`
- [ ] **Step 5: 커밋** — `git commit -m "feat(ec2-problem-explain): assemble explanation note with local assets"`

### Task 4: 검토 게이트와 발행

**Files:**
- Create: `.claude/skills/ec2-problem-explain/scripts/epe_files.py` (ML `ml-review-pack/scripts/review_pdf_publish.py`의 `_try_lock`, `publication_lock`, `_replace_copy`, `publish_files` 이식, 예외는 `ExplainError`)
- Create: `.claude/skills/ec2-problem-explain/scripts/epe_publish.py` (ML `mpe_publish.py` 기반)
- Test: `.claude/skills/ec2-problem-explain/tests/test_publish.py` (ML 이식)

**Interfaces:**
- Consumes: Task 1 계약, Task 2 `load_source`·`inside`·`sha256`, Task 3 `names`·`check_artifacts`·`artifact_hashes`·`dump`.
- Produces: `publish_files(staged: dict[Path, Path], backup_dir: Path) -> None`; `publish_explanation(pack, artifacts, fragments, reviews, destination, backup_dir) -> tuple[Path, ...]`.

ML 대비 변경점: 입력 확인은 `sha256(pack.path) != pack.sha256` 대신 `load_source(pack.path, repo) != pack`이면 `'입력 변경: 설명을 다시 검증하세요'`. 소유 경로 검사에서 `pack.inputs`의 어떤 파일도 목적지와 같으면 `'원본 덮어쓰기 금지'`.

- [ ] **Step 1: 테스트 작성** — ML `test_publish.py` 전부 이식(no review, stale 매개변수 7종, 백업·롤백, 잠금 거부), 그리고 다음을 추가:

```python
def test_changed_figure_or_md_refuses_publish(self):
    for target in ('figure', 'md'):
        ...  # build·approved 뒤 PNG 또는 md에 바이트 추가
        with self.assertRaisesRegex(ExplainError, '입력 변경'):
            publish_explanation(...)
        self.assertFalse((dest / artifacts.html.name).exists())

def test_publish_preserves_note_pdf_and_problems_txt(self):  # 발행 전후 정리노트·문제 PDF·problems.txt 바이트 동일
def test_republish_backs_up_previous_explanation(self):       # 두 번째 발행 뒤 backup 폴더에 이전 html 존재
```

- [ ] **Step 2: 실패 확인** — Expected: `No module named 'epe_publish'`
- [ ] **Step 3: 구현**
- [ ] **Step 4: 통과 확인** — 전체 discover / Expected: `OK`
- [ ] **Step 5: 커밋** — `git commit -m "feat(ec2-problem-explain): gate publication on reviews with backup and rollback"`

### Task 5: CLI

**Files:**
- Create: `.claude/skills/ec2-problem-explain/scripts/epe_cli.py` (ML `mpe_cli.py` 기반)
- Test: `.claude/skills/ec2-problem-explain/tests/test_cli.py` (ML `test_cli.py`·`test_delivery.py` 중 CLI 경로 이식)

**Interfaces:**
- Consumes: Tasks 1–4 전부.
- Produces: `main(argv: list[str] | None = None) -> int`. 하위 명령 `extract --repo --target --run`, `build --run`, `check --run`, `publish --run`.

ML 대비 변경점: 버킷 이름은 `f'review-{range}-{slug}'`. `load_run`은 `source.json`의 `path`(problems.txt)를 다시 `load_source` 해서 직렬화 비교한다(md·그림 변경 감지). 발행 위치는 `pack.path.parent`.

- [ ] **Step 1: 테스트 작성** — ML `test_cli.py` 이식, 그리고 다음을 추가:

```python
def test_range_extract_creates_bucket_per_pack(self):   # '0909-0911' → run.json targets 두 개
def test_one_failing_pack_does_not_block_other(self):  # 한 팩 problems.txt에 없는 id → exit 1, 다른 팩 source.json 존재
def test_end_to_end_publish(self):                      # extract → fragment 작성 → build → check → approved review.json → publish → 복습노트/1007/문제설명_1007_Diff_Amp.html·.md 존재
```

- [ ] **Step 2: 실패 확인** — Expected: `No module named 'epe_cli'`
- [ ] **Step 3: 구현**
- [ ] **Step 4: 통과 확인** — 전체 discover / Expected: `OK`
- [ ] **Step 5: 커밋** — `git commit -m "feat(ec2-problem-explain): add extract/build/check/publish CLI"`

### Task 6: SKILL.md와 저작·검토 참조

**Files:**
- Create: `.claude/skills/ec2-problem-explain/SKILL.md`
- Create: `.claude/skills/ec2-problem-explain/references/authoring.md`
- Create: `.claude/skills/ec2-problem-explain/references/verification.md`
- Test: `.claude/skills/ec2-problem-explain/tests/test_skill_files.py`

**Interfaces:**
- Consumes: Task 5 CLI 명령 형식.

내용(ML 같은 파일을 기준으로, 아래만 전자회로2로 바꾼다):
- SKILL.md frontmatter `name: ec2-problem-explain`. `description`은 따옴표로 감싸고, 트리거 문구 "문제설명", "복습문제 풀이 설명", "/ec2-problem-explain [MMDD|MMDD-MMDD]"와 "새 출제·정리노트·PDF·영상은 별도 스킬"을 넣는다.
- 본문: 대상 규칙(Task 2), RUN은 `<scratchpad>/ec2-problem-explain/<실행ID>`, 명령은 `python3 "$SKILL/scripts/epe_cli.py" …`(셸 상태 비유지·`cd` 금지 규칙은 ec2-review-pack과 같은 문구), 참고 자료(Razavi 장 md·`강의노트/` PDF·같은 날 정리노트·STT 보조), 저작은 문항마다 opus 작성자 병렬(GPT면 sol), 독립 검산은 다른 에이전트, 산출 위치, 보고 형식(팩별 published/withheld·문항/소문항 수·링크·RUN·백업).
- authoring.md: 회로 문제 지침. recall은 단서 → 개념 → 기호($g_m$, $r_o$, $R_{SS}$ 등)의 뜻 → 근사 조건($\lambda\to0$, $r_o\gg R_D$) → 선택 이유. start는 소신호 등가회로·하프 서킷·KCL 첫 식. verify는 극한 대입·단위·차수·대칭 특수값. 소문항 표지는 `(1)`/`(a)`를 원문 그대로.
- verification.md: `source_visual`은 `python3 workbook/source_pages.py render <md…> --out <RUN>/pages`로 원본 쪽을 렌더해 대조, `independent`는 SymPy 스크립트를 `evidence/`에 저장(`pip3 install --user --break-system-packages sympy`가 필요하면 설치), md `## 풀이`와 다르면 disputed.

- [ ] **Step 1: 테스트 작성**

```python
def test_frontmatter_parses_and_names_skill(self):     # yaml.safe_load → name == 'ec2-problem-explain', description 비어 있지 않음
def test_referenced_files_exist(self):                  # SKILL.md의 references/*.md, scripts/epe_cli.py 링크가 실제 파일
def test_cli_commands_in_skill_match_parser(self):      # SKILL.md에 나온 하위 명령 집합 == {'extract','build','check','publish'}
def test_agents_symlink_points_to_skill(self):          # REPO/.agents/skills/ec2-problem-explain resolve == 스킬 루트
```

- [ ] **Step 2: 실패 확인** — Expected: FAIL (SKILL.md 없음)
- [ ] **Step 3: 문서 작성**
- [ ] **Step 4: 통과 확인** — 전체 discover / Expected: `OK`
- [ ] **Step 5: 커밋** — `git commit -m "docs(ec2-problem-explain): add skill instructions and authoring rules"`

### Task 7: 실제 팩 1007 수용 실행

**Files:**
- Create (스킬 산출): `복습노트/1007/문제설명_1007_Differential_Amplifiers.html`, `.md`, `figures_문제설명_1007_Differential_Amplifiers/`, `자료_문제설명_1007_Differential_Amplifiers/`
- Modify (발견 시만): Tasks 1–6 파일

- [ ] **Step 1:** SKILL.md 절차대로 `/ec2-problem-explain 1007` 실행: extract → 10문항 저작 → 독립 검산 → build → check → 네 검토 → publish.
- [ ] **Step 2: 확인** — `check` 출력 `machine PASS`. `자료_…/validation.json`의 네 검토가 모두 `pass`. `git status`에서 `복습노트/1007`의 기존 파일(정리노트·PDF·problems.txt·figures_1007) 변경이 없음.
- [ ] **Step 3: 브라우저 확인** — 1280×900·375×812, light/dark에서 콘솔·KaTeX 오류 0, 가로 넘침 0, 외부 요청 0.
- [ ] **Step 4:** 스킬 결함을 고쳤다면 해당 Task 테스트를 추가하고 전체 discover `OK`.
- [ ] **Step 5: 커밋**

```bash
git add 복습노트/1007/문제설명_1007_* "복습노트/1007/figures_문제설명_1007_Differential_Amplifiers" "복습노트/1007/자료_문제설명_1007_Differential_Amplifiers"
git commit -m "docs(notes): add problem explanations for 1007"
```
