# ec2-review-pack 무제한 병렬 RUN 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 병렬 RUN이 준비된 작업을 슬롯 제한 없이 가장 작은 검증 단위(날짜·섹션·문항)로 배정하게 한다. 원문 준비를 기계화하고, 작업자 읽을거리를 줄이고, 조각 결함을 인계 전에 잡는다.

**Architecture:** 기존 실행기(`pack_cli.py` → `pack_flow`/`pack_graph`/`pack_parallel`)를 유지하고 그래프의 작업 단위만 바꾼다. 새 동작은 `init`이 새 병렬 RUN에 기록하는 계약 필드(`source_contract`, `problem_contract`, `probe_contract`)로만 켜진다. 필드가 없는 RUN과 레거시 RUN은 현재 코드 경로를 그대로 탄다. PR 네 개로 나누며 Part마다 브랜치 하나다.

**Tech Stack:** Python 3.14, pytest, PyMuPDF(`pymupdf`), Playwright Chromium(`layout_probe.py`)

**Spec:** `docs/superpowers/specs/2026-11-26-ec2-review-pack-unbounded-parallel-design.md`

## Global Constraints

- 모든 경로는 저장소 루트 기준이다. `S` = `.claude/skills/ec2-review-pack`.
- 테스트 명령은 저장소 루트에서 `python -m pytest <S>/tests/<파일>::<이름> -q`로 실행한다. 전체는 `python -m pytest <S>/tests -q`.
- 계약 필드가 없는 RUN(기존 병렬 RUN)과 `workflow='legacy'` RUN의 동작·출력은 바꾸지 않는다.
- CLI 응답은 개행 포함 2,000자 이하를 유지한다(`pack_cli.format_result`).
- 작업자 반환 800자 제한, 원본 읽기 전용, "실제 검토 없이 pass 생성 금지"는 그대로다.
- PROFILE 전체 읽기는 `stt`, `selection`, `scope-final`만 면제한다. 나머지 역할은 `profile_read='전체 필수'`를 유지한다.
- `--browser-owner`/`--pdf-owner` CLI 기본값은 `workers`다. `pack_flow.init_run`의 파이썬 기본 인자(`main`)는 바꾸지 않는다(테스트 픽스처가 의존).
- 커밋 메시지는 Conventional Commits, 끝에 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- `docs/` 문서는 문서 문구를 고정하는 `<S>/tests/test_skill_files.py`와 함께 고친다.

## Review Focus

1. **열리지 않는 강의 PDF**(손상·암호) — `source-prep` 작업 전체가 실패하지 않아야 한다. 그 PDF는 `missing`에 남기고 나머지로 진행한다. → Task B1 `test_source_prep_skips_unreadable_pdf`
2. **문항 0개 + `problem_contract`** — `explain-*`·`child-coordinator` 작업이 생기지 않아야 한다. → Task C1 `test_problem_contract_zero_problems_has_no_explain_tasks`
3. **20문항 RUN의 `next`** — 작업자 40개 ID가 2,000자 응답 안에 빠짐없이 들어가야 한다. → Task C1 `test_twenty_problem_dispatch_fits_cli_envelope`
4. **한 에이전트가 p1 작성자이면서 p2 풀이자** — 허용되어야 한다. 같은 문항이면 거부된다. → Task C2 `test_cross_problem_agent_allowed_same_problem_rejected`
5. **업그레이드 전에 시작한 병렬 RUN** — 단일 `explain-author`/`explain-blind`와 LLM `source-prep`를 유지해야 한다. → Task B1 `test_source_prep_stays_worker_without_contract`, Task C1 `test_existing_run_keeps_single_explain_tasks`

---

# Part A — PR 1: 슬롯 제거·명령 표기·읽을거리 (브랜치 `feat/review-pack-unbounded-slots`)

### Task A1: `--slots` 선택화와 `advance` 정지 조건

**Files:**
- Modify: `<S>/scripts/pack_cli.py:71`, `:166`
- Modify: `<S>/scripts/pack_actions.py:749-768` (`advance_actions`)
- Test: `<S>/tests/test_pack_cli.py`, `<S>/tests/test_pack_dispatch_resume.py`

**Interfaces:**
- Produces: `UNBOUNDED_SLOTS = 2**31` in `pack_flow.py`. `next` without `--slots` calls `next_work(run, slots=UNBOUNDED_SLOTS)`.
- `advance_actions(run, *, max_actions) -> dict`는 형태 그대로다. `waiting_for`에는 `dispatch + review_locally`가 들어가고, 정지는 `dispatch`가 비어 있지 않을 때만 한다.

- [ ] **Step 1: 실패하는 테스트를 쓴다**

`test_pack_cli.py`:
```python
def test_next_without_slots_dispatches_every_ready_worker(tmp_path):
    repo, run = make_run(tmp_path)  # 기존 픽스처(legacy)는 쓰지 않고 병렬 init
    new = tmp_path / 'p'
    call('init', '--repo', repo, '--run', new, '--range', '0909', '--allow-tmp')
    p, data = call('next', '--run', new)
    assert p.returncode == 0
    assert data['next']['dispatch'] == ['source-prep']
```
`test_pack_dispatch_resume.py`의 `test_advance_stops_at_review_gate` 옆에:
```python
def test_advance_runs_actions_past_local_review(tmp_path):
    # browser_owner=main → browser-qa는 review_locally. convert-md는 그와 무관하게 실행되어야 한다.
    state = selected(tmp_path, [])
    state['capabilities']['browser_owner'] = 'main'
    state['concept_check_enabled'] = False
    seed(state, ['scope-final', 'author-why', 'assemble-note', 'structural-precheck',
                 'style-audit', 'content-review', 'precheck'])
    run = Path(state['run'])
    f.update_state(run, state['revision'], lambda _: f.refresh_tasks(state))
    advanced = invoke(run, 'advance', '--max-actions', '1')
    assert advanced['executed'] == ['convert-md']
    assert 'browser-qa' in advanced['waiting_for']
```
`convert-md`가 이 픽스처에서 실제 변환기를 돌릴 수 없으면 `monkeypatch.setattr('pack_actions.run_action', ...)`로 상태만 `done`으로 기록하는 가짜를 쓴다. 단언 두 개는 그대로 둔다.

- [ ] **Step 2: 실패 확인**

Run: `python -m pytest <S>/tests/test_pack_cli.py::test_next_without_slots_dispatches_every_ready_worker <S>/tests/test_pack_dispatch_resume.py::test_advance_runs_actions_past_local_review -q`
Expected: 첫 테스트는 `usage_error`로 FAIL(returncode 2), 둘째는 `executed == []`로 FAIL

- [ ] **Step 3: 구현**

`pack_cli.py:71`에서 `--slots`를 `required=False, type=int, default=None`으로 바꾸고, `:166`에서 `None`이면 `f.UNBOUNDED_SLOTS`를 쓴다. `pack_actions.py:756`의 `2**31`도 `f.UNBOUNDED_SLOTS`로 바꾼다. `advance_actions`의 정지 조건은 `nxt['dispatch'] or blockers or not actions or len(executed) == max_actions`로 하고, 반환의 `waiting_for`는 `dispatch + review_locally or blockers or active`로 한다.

- [ ] **Step 4: 통과 확인**

Run: Step 2 명령 + `python -m pytest <S>/tests/test_pack_dispatch_resume.py <S>/tests/test_pack_cli.py -q`
Expected: 모두 PASS(기존 `test_advance_stops_at_review_gate` 포함)

- [ ] **Step 5: 커밋**

`git commit -m "feat(review-pack): make next slots optional and run actions past local reviews"`

### Task A2: 브리프 `python` 필드와 owner 기본값

**Files:**
- Modify: `<S>/scripts/pack_parallel.py:173-177` (`claim_worker`의 `data`)
- Modify: `<S>/scripts/pack_flow.py:807-818` (`write_briefs`의 `data`)
- Modify: `<S>/scripts/pack_cli.py:68`
- Test: `<S>/tests/test_pack_graph.py`, `<S>/tests/test_pack_flow.py`, `<S>/tests/test_pack_cli.py`

**Interfaces:**
- Produces: 모든 생성 브리프(병렬·레거시)에 `"python": sys.executable` 문자열 필드가 생긴다. Task A4 문서가 이 이름을 쓴다.

- [ ] **Step 1: 실패하는 테스트를 쓴다**

```python
# test_pack_graph.py
def test_parallel_brief_names_runner_python(tmp_path):
    _, run, _ = parallel(tmp_path)
    brief = json.loads(Path(flow.claim_task(run, 'source-prep')['brief']).read_text())
    assert brief['python'] == sys.executable

# test_pack_flow.py
def test_legacy_brief_names_runner_python(tmp_path):
    _, run = make_run(tmp_path)
    brief = json.loads(Path(flow.load_state(run)['tasks']['source-prep']['brief']).read_text())
    assert brief['python'] == sys.executable

# test_pack_cli.py
def test_init_defaults_inspection_owners_to_workers(tmp_path):
    repo = _repo_only(tmp_path)
    call('init', '--repo', repo, '--run', tmp_path / 'r', '--range', '0909', '--allow-tmp')
    caps = json.loads((tmp_path / 'r/run-status.json').read_text())['capabilities']
    assert caps == {'browser_owner': 'workers', 'pdf_owner': 'workers'}
```
B1 이후에는 `source-prep`가 기계 작업이 되어 claim할 수 없다. 그때 첫 테스트를 `Trial`로 옮긴다: `trial.action('candidate-index'); trial.action('source-prep'); assert trial.worker('stt-0909')['python'] == sys.executable` (Task B1 Step 5).

- [ ] **Step 2: 실패 확인** — 세 테스트가 `KeyError: 'python'`과 `'main' != 'workers'`로 FAIL

- [ ] **Step 3: 구현** — 두 `data` dict에 `python=sys.executable`을 넣는다(`pack_parallel.py`에 `import sys`는 이미 있다). `pack_cli.py:68`의 `default='main'`을 `default='workers'`로 바꾼다.

- [ ] **Step 4: 통과 확인** — `python -m pytest <S>/tests -q`. owner 기본값에 의존하던 CLI 테스트가 깨지면 그 테스트에 `--browser-owner main`을 명시한다.

- [ ] **Step 5: 커밋** — `feat(review-pack): name the runner python in briefs and default owners to workers`

### Task A3: `reference_sections`와 PROFILE 면제

**Files:**
- Modify: `<S>/scripts/pack_parallel.py:90-143` (`worker_inputs`), `:183-188` (`claim_worker` else 분기)
- Modify: `<S>/scripts/pack_flow.py:736-752` (`_REFERENCES`, `_COMMON_SECTIONS`)
- Test: `<S>/tests/test_parallel_pack_integration.py`

**Interfaces:**
- Produces: `pack_flow.PROFILE_EXEMPT = ('stt', 'selection', 'scope-final')`.
- Produces: 병렬 브리프 필드 `reference_sections: dict[str, list[str]]`. 키는 `references`의 각 절대 경로이고 값은 `_REFERENCES[role]`의 절 제목 목록이다. `author`·`style-audit`·`content-review`는 `execution-guide.md` 키에 `_COMMON_SECTIONS`를 합친다(경로가 없으면 `references`에도 추가). `'전체'`는 파일 전체를 뜻한다.
- `references`(경로 목록)의 형태는 바꾸지 않는다. `pack_approvals.resource_paths`가 이것을 읽는다.

- [ ] **Step 1: 실패하는 테스트를 쓴다**

브리프 생성에는 앞 작업의 실제 artifacts가 필요하다(`seed`는 artifacts를 만들지 않는다). 그래서 `test_parallel_pack_integration.py`의 `Trial`로 쓴다. `Trial.worker`는 claim한 브리프를 반환한다.
```python
def test_profile_exempt_roles_omit_profile(tmp_path):
    trial = Trial(tmp_path)
    trial.action('candidate-index')
    trial.worker('source-prep')
    brief = trial.worker('stt-0909')
    assert 'profile' not in brief and 'profile_read' not in brief
    assert not any(p.endswith('solution-style.md') for p in brief['input_paths'])

def test_author_brief_lists_sections_to_read(tmp_path):
    trial = Trial(tmp_path)
    trial.action('candidate-index')
    for tid in ('source-prep', 'stt-0909', 'scope-draft'):
        trial.worker(tid)
    brief = trial.worker('author-why')
    guide = next(p for p in brief['references'] if p.endswith('execution-guide.md'))
    assert brief['reference_sections'][guide] == ['3. 작성', *COMMON_SECTIONS]
    assert brief['profile_read'] == '전체 필수'
```
`COMMON_SECTIONS`는 `from pack_flow import _COMMON_SECTIONS as COMMON_SECTIONS`로 가져온다. Part B 이후에는 두 테스트의 `trial.worker('source-prep')`를 `trial.action('source-prep')`로 바꾼다(Task B1 Step 5).

- [ ] **Step 2: 실패 확인** — `KeyError`/단언 실패로 FAIL

- [ ] **Step 3: 구현**

- `claim_worker`: role이 `PROFILE_EXEMPT`에 있으면 `profile`, `profile_read`, `snapshot`을 넣지 않는다. `reference_sections`는 모든 역할에 넣는다.
- `worker_inputs:96-97`: 면제 역할이면 `paths`를 `snapshot`과 PROFILE 없이 시작한다. `state['hashes']` 기반 stale 감지는 RUN 전역이라 그대로 동작한다.
- `selection`은 `content-review`처럼 `problem-selection.md`의 `'전체'`를 유지한다.

- [ ] **Step 4: 통과 확인** — 위 테스트 + `python -m pytest <S>/tests/test_pack_graph.py <S>/tests/test_parallel_pack_integration.py -q` PASS

- [ ] **Step 5: 커밋** — `feat(review-pack): scope worker reading to referenced sections`

### Task A4: 문서에서 슬롯 상한·`python3` 제거

**Files:**
- Modify: `<S>/references/delegation.md:9-10`, `:60-61`, `:68`
- Modify: `<S>/references/problem-explain-integration.md:32-33`
- Modify: `<S>/references/runner-contract.md:15`, `:23`
- Modify: `<S>/references/worker-prompt.md:7`, `:23-26`, `:35`, `:42`
- Modify: `<S>/references/execution-guide.md`, `browser-check.md`, `manifest-guide.md`, `problem-selection.md`의 `python3` 사용처(`grep -n python3 <S>/references/*.md`로 19곳)
- Test: `<S>/tests/test_skill_files.py`

**Interfaces:** Consumes A1(`--slots` 선택), A2(`brief.python`), A3(`reference_sections`).

- [ ] **Step 1: 실패하는 테스트를 쓴다** — `test_skill_files.py`에 추가:
```python
def test_docs_have_no_slot_caps_or_python3():
    refs = SKILL / 'references'
    text = '\n'.join(p.read_text(encoding='utf-8') for p in refs.glob('*.md'))
    for banned in ('전체 슬롯 최대 4', '메인+직접 작업자 최대 3명', '예상 종료 시각으로 슬롯을 재배정하지 않는다', 'python3 '):
        assert banned not in text, banned
    assert '준비된 독립 작업은 한 메시지에서 모두 띄운다' in (refs / 'delegation.md').read_text(encoding='utf-8')
    assert 'reference_sections' in (refs / 'worker-prompt.md').read_text(encoding='utf-8')
```
`SKILL` 상수 이름은 파일에 이미 있는 것을 따른다.

- [ ] **Step 2: 실패 확인** — banned 문구로 FAIL

- [ ] **Step 3: 문서 수정** (정확한 문구)
- `delegation.md:9`를 다음으로 교체한다: "준비된 독립 작업은 한 메시지에서 모두 띄운다. `next`의 `dispatch`에 나온 작업자를 전부 claim·bind한 뒤 같은 메시지에서 실행한다. 순서 의존 단계는 병렬화하지 않는다."
- `delegation.md:10`에서 "예상 종료 시각으로 슬롯을 재배정하지 않는다." 문장을 삭제한다.
- `problem-explain-integration.md:32`의 "전체 슬롯 최대 4: … 다음 묶음을 시작한다." 세 문장을 다음으로 교체한다: "조정자는 leaf 작업자를 필요한 만큼 동시에 띄운다." 나머지 독립성 문장은 유지한다. 33행의 "자리가 없으면"/"자리가 반환되면" 표현은 "중첩 실행이 불가능하면"/"leaf가 끝나면"으로 바꾼다.
- `runner-contract.md:15`와 `:23`: `--slots <현재 가용 수>`를 `[--slots <n>]`으로 바꾸고 "생략하면 준비된 작업자를 모두 낸다"를 덧붙인다. 23행의 "메인과 자식 조정자가 쓴 슬롯을 먼저 빼고 남은 슬롯을 직접 작업자에 배정한다." 문장은 삭제한다.
- `python3 <SKILL>/scripts/…` → `<python> <SKILL>/scripts/…`로 바꾸고, 처음 나오는 곳(`worker-prompt.md:23`, `delegation.md:60`)에 "`<python>`은 브리프의 `python` 값"을 적는다. 메인이 직접 치는 `python3 -c …`(`execution-guide.md:46`, `:52`)는 `python -c …`로 바꾸고, "macOS에서 `python`이 없으면 `python3`"을 한 번 적는다.
- `worker-prompt.md:7`과 `:35`의 "references 절·inputs·PROFILE 전체를 읽는다"를 다음으로 교체한다: "`reference_sections`에 적힌 절과 inputs를 읽는다. 브리프에 `profile`이 있으면 PROFILE 전체를 읽는다."

- [ ] **Step 4: 통과 확인** — `python -m pytest <S>/tests/test_skill_files.py -q` PASS(기존 고정 문구 단언이 깨지면 새 문구로 같이 갱신)

- [ ] **Step 5: 커밋 후 PR** — `docs(review-pack): drop slot caps and python3 from worker contracts`. PR 1을 연다.

---

# Part B — PR 2: 원문 준비 기계화 (브랜치 `feat/review-pack-source-action`)

### Task B1: `source-prep` 기계 작업

**Files:**
- Create: `<S>/scripts/pack_sources.py`
- Modify: `<S>/scripts/pack_flow.py:378-385` (`init_run` 병렬 블록)
- Modify: `<S>/scripts/pack_graph.py:32` (`task_specs`)
- Modify: `<S>/scripts/pack_parallel.py:1071-1118` (`execute_action`)
- Modify: `<S>/scripts/pack_cli.py:13-15` (`ACTIONS`)
- Test: Create `<S>/tests/test_pack_sources.py`; Modify `<S>/tests/test_pack_graph.py`, `<S>/tests/test_parallel_pack_integration.py`, `<S>/tests/test_pack_cli.py`

**Interfaces:**
- Produces: `prepare_sources(repo: Path, sessions: list[str], stt: dict[str, Path], root: Path) -> dict[str, Path]`. 반환은 `{'source-map.json': Path, 'slides.txt': Path}`다.
- `source-map.json`의 스키마는 기존과 같다: `{schema_version:1, sessions:[{date, stt, pdfs, status:'ready', missing}]}`. 모든 세션의 `pdfs`에 읽은 PDF 전체 목록을 넣는다. PDF가 없거나 못 읽은 경우는 `missing`에 `"<파일명>: <이유>"` 또는 `"강의노트 PDF 없음"`을 기록하고, `status`는 항상 `ready`다.
- `slides.txt`는 쪽마다 `=== LNN sK ===` 머리줄 뒤에 그 쪽 텍스트가 온다. `NN`은 파일명 `2026F_Lec(\d+)_`의 번호를 두 자리로, `K`는 1부터다. PDF는 `NN` 순서다.
- 상태 필드: 새 병렬 RUN의 `state['source_contract'] = 1`. 없으면 `source-prep`는 지금처럼 worker다.

- [ ] **Step 1: 실패하는 테스트를 쓴다** — `test_pack_sources.py`:
```python
def test_source_prep_extracts_every_lecture_pdf(tmp_path):
    repo = tmp_path/'repo'; (repo/'강의노트').mkdir(parents=True); (repo/'STT').mkdir()
    stt = repo/'STT/0909 전회2.md'; stt.write_text('x', encoding='utf-8')
    for n, text in ((2, 'second'), (1, 'first')):
        with pymupdf.open() as d:
            d.new_page().insert_text((72, 72), text); d.save(repo/f'강의노트/2026F_Lec{n}_T.pdf')
    files = prepare_sources(repo, ['0909'], {'0909': stt}, tmp_path/'out')
    slides = files['slides.txt'].read_text(encoding='utf-8')
    assert slides.index('=== L01 s1 ===') < slides.index('=== L02 s1 ===') and 'first' in slides
    session, = json.loads(files['source-map.json'].read_text())['sessions']
    assert session['status'] == 'ready' and len(session['pdfs']) == 2 and session['missing'] == []

def test_source_prep_skips_unreadable_pdf(tmp_path):
    # Review Focus 1: 손상 PDF 하나가 전체를 실패시키지 않는다
    ...  # 위 픽스처 + (repo/'강의노트/2026F_Lec3_Bad.pdf').write_bytes(b'not a pdf')
    assert session['missing'] == ['2026F_Lec3_Bad.pdf: unreadable'] and len(session['pdfs']) == 2

def test_source_prep_without_pdfs_is_stt_only(tmp_path):
    ...  # 강의노트 비어 있음
    assert session['pdfs'] == [] and session['missing'] == ['강의노트 PDF 없음']
```
`test_pack_graph.py`:
```python
def test_source_prep_is_machine_action_under_contract(tmp_path):
    _, run, state = parallel(tmp_path)
    assert state['source_contract'] == 1
    nxt = flow.next_work(run, slots=1)
    assert set(nxt['actions']) == {'source-prep', 'candidate-index', 'render-preflight'}
    assert nxt['dispatch'] == []

def test_source_prep_stays_worker_without_contract(tmp_path):
    # Review Focus 5
    _, run, state = parallel(tmp_path)
    flow.update_state(run, state['revision'], lambda s: {k: v for k, v in s.items() if k != 'source_contract'} | {'tasks': {}, 'actions': {}})
    state = flow.load_state(run)
    flow.update_state(run, state['revision'], lambda s: flow.refresh_tasks(s))
    assert flow.next_work(run, slots=1)['dispatch'] == ['source-prep']
```

- [ ] **Step 2: 실패 확인** — `ImportError: pack_sources` 등으로 FAIL

- [ ] **Step 3: 구현**
- `pack_sources.prepare_sources`: `sorted(repo.glob('강의노트/2026F_Lec*_*.pdf'))`를 NFC 이름 기준으로 모으고 Lec 번호로 정렬한다. `pymupdf.open` 실패나 `is_encrypted`면 `missing`에 `'<name>: unreadable'`을 넣는다. 출력은 `pack_flow._atomic_json`(JSON)과 `newline='\n'` UTF-8(텍스트)로 쓴다. `stt` 값은 `str(nfc_path(path))`다.
- `init_run`의 병렬 블록에 `state['source_contract'] = 1`을 추가한다.
- `task_specs:32`: `state.get('source_contract')`이면 `action('source-prep', outputs=('source-map.json', 'slides.txt'))`, 아니면 기존 `worker(...)`.
- `execute_action`: `tid == 'source-prep'` 분기에서 `prepare_sources`를 호출하고, `files`로 반환하고, `extras['source_inputs']`에 읽은 STT·PDF의 `file_records`를 넣는다(현재 receipt `verified_files`가 하던 고정을 대신한다).
- `ACTIONS`에 `'source-prep'`를 추가한다.

- [ ] **Step 4: 통과 확인**

Run: `python -m pytest <S>/tests/test_pack_sources.py <S>/tests/test_pack_graph.py -q`
Expected: PASS

- [ ] **Step 5: 기존 테스트를 새 계약에 맞춘다**
- `test_parallel_pack_integration.py`: `Trial.__init__`에서 `slides.pdf`를 `repo/강의노트/2026F_Lec1_Synthetic.pdf`로 옮긴다. `prepare_note`는 `self.action('source-prep')`로 바꾸고 worker 튜플에서 `'source-prep'`를 뺀다. `produce`의 `source-map.json` 분기는 삭제한다.
- `test_pack_graph.py::test_source_and_render_preflight_are_independent`, `::test_opt_in_cli_runs_candidate_action_and_isolates_worker_attempts`: claim 대상을 `stt-0909` 전제로 바꾸거나, 레거시 동작을 검증하는 테스트는 `source_contract`를 제거한 상태로 검증한다.
- Task A2의 `test_parallel_brief_names_runner_python`: Task A2에 적은 `Trial` 형태로 옮긴다.
- Task A3의 두 테스트: `trial.worker('source-prep')`를 `trial.action('source-prep')`로 바꾼다.
- Task A1의 `test_next_without_slots_dispatches_every_ready_worker`: 기대값을 `data['next']['dispatch'] == []`와 `'source-prep' in data['next']['actions']`로 바꾼다.

Run: `python -m pytest <S>/tests -q`
Expected: 모두 PASS

- [ ] **Step 6: 커밋** — `feat(review-pack): extract lecture sources as a machine action`

### Task B2: 요약자·역할 문서 갱신

**Files:**
- Modify: `<S>/references/stt-summary-prompt.md`
- Modify: `<S>/references/delegation.md:36` (역할 표의 자료 준비자 행)
- Modify: `<S>/references/execution-guide.md:69-75` (`1. 범위 파악`의 1·2)
- Modify: `<S>/references/runner-contract.md:24` (시작 행동)
- Test: `<S>/tests/test_skill_files.py`

- [ ] **Step 1: 테스트** — `test_skill_files.py`에 다음 두 단언을 추가한다.
  - `stt-summary-prompt.md`에 `"slides.txt 전체에서 이 날짜 STT가 다룬 강의 블록을 찾아"`가 있다.
  - `delegation.md`의 역할 표에 `"자료 준비자"` 행이 없다.
- [ ] **Step 2: 실패 확인**
- [ ] **Step 3: 문서 수정**
  - `stt-summary-prompt.md`에 다음 문단을 추가한다: "`slides.txt`에는 모든 Lec PDF가 들어 있다. slides.txt 전체에서 이 날짜 STT가 다룬 강의 블록을 찾아 그 블록만 읽는다(`=== LNN` 머리줄로 검색). 이 날짜가 다룬 슬라이드가 없으면 `## 슬라이드 대조표` 대신 `## 교과서 절 대조`만 쓴다."
  - `delegation.md` 역할 표에서 자료 준비자 행을 삭제하고, 표 아래에 "원문 준비는 `source-prep` 기계 작업이다(`source_contract` RUN)."를 적는다.
  - `execution-guide.md:69-72`를 "실행기의 `source-prep`가 모든 Lec PDF를 `RUN/slides.txt`로 뽑는다. 관련 PDF 선택과 슬라이드 없는 날짜 판단은 요약자가 한다."로 줄인다. 계약 필드가 없는 RUN용 기존 절차는 "기존 RUN" 소제목 아래로 옮겨 보존한다.
  - `runner-contract.md:24`: "source-prep, candidate-index, render-preflight를 함께 연다"를 "세 기계 작업 source-prep·candidate-index·render-preflight를 `advance`로 실행한다"로 바꾼다.
- [ ] **Step 4: 통과 확인** — `python -m pytest <S>/tests/test_skill_files.py -q`
- [ ] **Step 5: 커밋 후 PR** — `docs(review-pack): hand slide matching to summarizers`. PR 2를 연다.

---

# Part C — PR 3: 문항 단위 작성·독립 풀이 (브랜치 `feat/review-pack-per-problem`)

### Task C1: 그래프·봉인·브리프를 문항 단위로

**Files:**
- Modify: `<S>/scripts/pack_graph.py:23-122` (`task_specs`, `targets`, `refresh`)
- Modify: `<S>/scripts/pack_parallel.py:74-95` (`original_worker_inputs`, `worker_inputs`), `:178-182` (`claim_worker` 문항 브리프), `:815-855` (`seal_questions`), `:1132-1136` (`execute_action`의 stage 분기)
- Modify: `<S>/scripts/pack_flow.py` (`init_run` 병렬 블록에 `problem_contract`)
- Test: `<S>/tests/test_pack_graph.py`

**Interfaces:**
- Produces (`pack_graph.py`):
  - `problem_keys(state: dict) -> list[str]` → `['p1', …, f'p{len(selected_ids)}']`
  - `explain_ids(state: dict, role: str) -> list[str]` → `role`이 `'explain-author'` 또는 `'explain-blind'`다. `problem_contract`가 없으면 `[role]`, 있으면 `[f'{role}-{k}' for k in problem_keys(state)]`.
  - `role_of(task_id: str) -> str` → `author-*`→`author`, `stt-*`→`stt`, `explain-author-pN`→`explain-author`, `explain-blind-pN`→`explain-blind`, 그 외는 ID 그대로.
  - `problem_key(task_id: str) -> str | None` → `-p(\d+)$` 접미사의 `'pN'`, 없으면 `None`.
- 작업 명세(`problem_contract`): 각 `k`에 대해 `worker(f'explain-author-{k}', ('stage-problem-index',), (f'explanations/{k}.html',))`, `worker(f'explain-blind-{k}', ('stage-problem-index',), ('independent.json',))`. `child-coordinator`의 직접 입력은 `('stage-problem-index', *explain_ids(state,'explain-author'), *explain_ids(state,'explain-blind'))`다.
- `targets(state, 'explain-*-pN')` → `[state['selected_ids'][N-1]]`.
- stage 행 필드: 기존 `questions`(전체 파일 목록)에 더해 `problem_questions: dict[str, list[str]]`(키 `pN`, 값은 `sealed/pN/` 아래 파일 경로)을 기록한다. `sealed/pN/questions.json`은 그 문항 하나만 담은 `{problems:[…]}`이고 그림은 같은 폴더에 둔다.
- 브리프: `explain-*-pN`의 `questions`는 `sealed/pN/questions.json`이고, `inputs`는 `problem_questions['pN']`이다.

- [ ] **Step 1: 실패하는 테스트를 쓴다** (`test_pack_graph.py`, 픽스처 `selected`에 `problem_contract=1`을 켠다)
```python
def test_problem_contract_opens_one_author_and_solver_per_problem(tmp_path):
    from pack_graph import ready_work
    state = selected(tmp_path, ['P10.01', 'P10.02', 'P10.03'])
    state['problem_contract'] = 1
    seed(state, ['stage-problem-index'])
    nxt = ready_work(state, slots=2**31)
    expected = {f'explain-{r}-p{i}' for r in ('author', 'blind') for i in (1, 2, 3)}
    assert expected <= set(nxt['dispatch'])
    assert 'explain-author' not in nxt['dispatch']

def test_problem_contract_zero_problems_has_no_explain_tasks(tmp_path):      # Review Focus 2
    from pack_graph import task_specs
    state = selected(tmp_path, []); state['problem_contract'] = 1
    assert not {s.id for s in task_specs(state)} & {'child-coordinator'} and \
        not any(s.id.startswith('explain-') for s in task_specs(state))

def test_existing_run_keeps_single_explain_tasks(tmp_path):                  # Review Focus 5
    from pack_graph import ready_work
    state = selected(tmp_path, ['P10.01', 'P10.02'])
    state.pop('problem_contract', None)
    seed(state, ['stage-problem-index'])
    assert {'explain-author', 'explain-blind'} <= set(ready_work(state, slots=6)['dispatch'])

def test_twenty_problem_dispatch_fits_cli_envelope(tmp_path):                # Review Focus 3
    from pack_cli import format_result
    from pack_graph import ready_work
    state = selected(tmp_path, [f'P10.{i:02}' for i in range(1, 21)]); state['problem_contract'] = 1
    seed(state, ['stage-problem-index'])
    nxt = ready_work(state, slots=2**31)
    out = json.loads(format_result(dict(next=nxt)))
    assert len([t for t in out['next']['dispatch'] if t.startswith('explain-')]) == 40
```
`test_early_index_seals_real_questions_for_independent_attempts`를 본떠 추가:
```python
def test_problem_contract_seals_each_question_separately(tmp_path):
    ...  # 같은 픽스처, state['problem_contract']=1, stage 실행 후
    blind = json.loads(Path(flow.claim_task(run, 'explain-blind-p1')['brief']).read_text())
    assert Path(blind['questions']).parent.name == 'p1'
    assert {Path(p).parent.name for p in blind['input_paths'] if 'sealed' in p} == {'p1'}
```
`input_paths`에는 참조 문서도 있으므로 `sealed` 경로만 거른다.

- [ ] **Step 2: 실패 확인** — `explain-author-p1`가 없어 FAIL

- [ ] **Step 3: 구현**
- `init_run` 병렬 블록에 `state['problem_contract'] = 1`을 추가한다.
- `task_specs`의 `if ids:` 블록에서 contract가 있으면 위 명세대로 만들고, 없으면 기존 세 줄을 유지한다.
- `refresh`의 role 계산(`:117`)을 `role_of(spec.id)`로 바꾼다.
- `seal_questions`: contract가 있으면 문항마다 `sealed/pN/`을 만들어 그 문항의 `questions.json`과 그림을 쓴다. 기존 `sealed/questions.json`도 계속 쓴다(조정자·기존 경로용). 반환은 `(sealed, inputs, per_problem: dict[str, list[Path]])`로 한다.
- `execute_action` stage 분기: `extras['problem_questions'] = {k: [str(p) for p in v] …}`를 추가하고, 모든 문항별 파일을 `evidence`에 넣는다.
- `worker_inputs:94-95`와 `original_worker_inputs:76-77`: `spec.id` 비교를 `role_of(spec.id) in (...)`로 바꾼다. contract가 있으면 `problem_questions[problem_key(spec.id)]`를 쓴다.
- `claim_worker:179`: contract가 있으면 `questions = sealed/<pN>/questions.json`.

- [ ] **Step 4: 통과 확인** — `python -m pytest <S>/tests/test_pack_graph.py -q` PASS

- [ ] **Step 5: 커밋** — `feat(review-pack): schedule explanation author and solver per problem`

### Task C2: 문항별 신원 검증·독립 풀이 결합

**Files:**
- Modify: `<S>/scripts/pack_parallel.py:146-151` (`explanation_digest`), `:419-432` (`check_leaf_join`), `:529-553` (`validate_worker`), `:261-268` (`claim_worker`의 조정자 분기)
- Modify: `<S>/scripts/pack_approvals.py:458-463` (`make_plan`)
- Modify: `<S>/scripts/pack_findings.py:395-406` (`check_reviewer`)
- Modify: `<S>/tests/pack_support.py:122-139` (`genuine_child_run`)
- Test: `<S>/tests/test_pack_approvals.py`, `<S>/tests/test_parallel_pack_integration.py`

**Interfaces:**
- Consumes: C1의 `explain_ids`, `problem_key`, `role_of`.
- Produces (`pack_parallel.py`):
  - `counterpart(task_id: str) -> str` → `explain-author-pN`↔`explain-blind-pN`(접미사 없는 ID에도 동작)
  - `blind_items(state: dict) -> dict` → 모든 `explain_ids(state,'explain-blind')`의 채택된 `independent.json` `items`를 합친다. 키가 겹치면 `FlowError('duplicate independent item')`.
  - 조정자 claim 시(contract) 합친 결과를 `RUN/adopted/blind-join/<uuid>/independent.json`(읽기 전용)으로 쓰고, `brief['independent']`에 경로를 넣고, `inputs`에 추가한다.
- 규칙:
  - 같은 `pN`의 작성자 agent ≠ 풀이자 agent.
  - 조정자 agent ∉ {모든 `explain-author*`의 agent와 history agent}.
  - 조정자 영수증 `reviewers.authors[pN]` == `explain-author-pN`의 agent.
  - `explanation_digest`는 모든 작성자 작업의 출력 이름→해시 dict 하나로 계산한다.

- [ ] **Step 1: 실패하는 테스트를 쓴다** — `test_pack_approvals.py`의 `compact` 헬퍼를 문항 ID로 확장해서:
```python
def test_cross_problem_agent_allowed_same_problem_rejected(tmp_path):          # Review Focus 4
    run = two_problem_blind_run(tmp_path)          # problem_contract=1, P10.01·P10.02, stage 완료
    accept_author(run, 'explain-author-p1', agent='agent-A')
    accept_blind(run, 'explain-blind-p2', agent='agent-A')                     # 다른 문항: 통과
    with pytest.raises(flow.FlowError, match='independent solver must differ from author'):
        accept_blind(run, 'explain-blind-p1', agent='agent-A')                 # 같은 문항: 거부
```
`two_problem_blind_run`, `accept_author`, `accept_blind`는 같은 파일의 기존 `blind_run`/`compact` 패턴으로 만든다. 이름은 이대로 쓴다.
```python
def test_coordinator_receives_joined_blind_items(tmp_path):
    ...  # 두 풀이 채택 후
    brief = json.loads(Path(flow.claim_task(run, 'child-coordinator')['brief']).read_text())
    items = json.loads(Path(brief['independent']).read_text())['items']
    assert {k.split(':')[0] for k in items} == {'p1', 'p2'}
```

- [ ] **Step 2: 실패 확인**

- [ ] **Step 3: 구현**
- `validate_worker:529-553`: `other = state['tasks'][counterpart(task['id'])]`. `:534`의 풀이자 목록은 `output(state, counterpart(...), 'independent.json')`. `:540` 문항 키는 contract면 `f._read(brief['questions'])`. `:550`의 작성자 agent는 `state['tasks'][counterpart(task['id'])]`.
- `make_plan:459`: `state['tasks'][counterpart(brief['task_id'])].get('agent_id')`.
- `check_reviewer:402-405`: 작성자 집합을 `explain_ids(state,'explain-author')` 전부의 agent와 history로 넓힌다.
- `check_leaf_join`: 작성자 조각 비교는 작업별로(`output(state, f'explain-author-{k}', f'explanations/{k}.html')`) 한다. 독립 풀이는 `blind_items(state)`와 대조한다. 작성자 신원은 `reviewers.authors[k] == state['tasks'][f'explain-author-{k}']['agent_id']`.
- contract가 없으면 위 모든 함수가 기존 단일 ID로 동작한다(`explain_ids`가 `[role]`을 반환하므로 대부분 자동). 남는 리터럴은 Step 4의 grep으로 확인한다.
- `genuine_child_run:126`: `state['tasks'].get(f'explain-author-{p.id}') or state['tasks']['explain-author']`의 artifacts를 복사한다. `:139`의 `authors`는 contract면 `{p.id: 'synthetic-explain-author-' + p.id}`.

- [ ] **Step 4: 통과 확인과 리터럴 점검**

Run: `python -m pytest <S>/tests/test_pack_approvals.py <S>/tests/test_parallel_pack_integration.py -q`
Expected: PASS

Run: `grep -n "'explain-author'\|'explain-blind'" <S>/scripts/*.py`
Expected: 남은 줄은 역할 비교(`role ==`, `ROLES`, `ROLE_OUTPUTS`, `_REFERENCES`)이거나 `explain_ids`·`counterpart` 정의뿐이다.

- [ ] **Step 5: 커밋** — `feat(review-pack): bind independence per problem and join blind solutions`

### Task C3: 조정자 결함의 문항별 담당

**Files:**
- Modify: `<S>/scripts/pack_findings.py:77-81`, `:170-200` (`record_findings`)
- Test: `<S>/tests/test_parallel_pack_integration.py`

**Interfaces:**
- Produces: `coordinator_owner(state: dict, target: str) -> str`. contract가 없으면 `'explain-author'`다. 있으면 `target`이 `selected_ids`의 workbook ID이거나 `pN`, `pN:<소문항>`일 때 `f'explain-author-p{i}'`를 반환한다. 그 밖은 `FlowError('coordinator finding target is not a selected problem')`.
- `record_findings`는 `review_id == COORDINATOR`이면, 작업자가 쓴 `owner_task`가 `'explain-author'` 또는 계산값과 같을 때 계산값으로 정규화한다. 다르면 기존 오류를 낸다.

- [ ] **Step 1: 실패하는 테스트를 쓴다** — `Trial(problem=True)`를 두 문항 픽스처로 확장한 `two_problem_coordinator_trial`을 만들고:
```python
def test_coordinator_finding_reopens_only_that_problem_author(tmp_path):
    trial = two_problem_coordinator_trial(tmp_path)   # P10.01, P10.02 / author·blind p1·p2 채택
    coordinator_judgment(trial, unresolved=[dict(COORDINATOR_DEFECT, target='P10.02')])
    row, = read(trial.run/'run-status.json')['findings'].values()
    assert row['owner_task'] == 'explain-author-p2'
    fix_coordinator_findings(trial, 'fix-p2')
    tasks = read(trial.run/'run-status.json')['tasks']
    assert tasks['explain-author-p2']['status'] == 'stale'
    assert tasks['explain-author-p1']['status'] == 'done'
    assert {t for t in trial.next()['dispatch'] if t.startswith('explain-')} == {'explain-author-p2'}
```
기존 `test_coordinator_findings_reopen_only_explain_author` 등 단일 문항 테스트의 기대 ID는 `explain-author-p1`/`explain-blind-p1`로 바꾼다. `Trial.produce`의 `tid in ('explain-author','explain-blind')` 분기는 `role_of(tid)`로 판정하고, 풀이 키 `p1:`은 `problem_key(tid)`로 만든다.

- [ ] **Step 2: 실패 확인**
- [ ] **Step 3: 구현** — 위 명세대로 한다. `COORDINATOR_OWNER` 상수는 contract 없는 경로의 기본값으로 남긴다.
- [ ] **Step 4: 통과 확인** — `python -m pytest <S>/tests -q` 전체 PASS
- [ ] **Step 5: 커밋** — `feat(review-pack): route coordinator findings to the problem's author`

### Task C4: 문항 단위 문서

**Files:**
- Modify: `<S>/references/problem-explain-integration.md:7`, `:32`
- Modify: `<S>/references/runner-contract.md:24`, `:111`
- Modify: `<S>/references/worker-prompt.md:7`
- Test: `<S>/tests/test_skill_files.py`

- [ ] **Step 1: 테스트** — `runner-contract.md`에 `"explain-author-pN"`과 `"같은 문항"`이 있다는 단언을 추가한다.
- [ ] **Step 2: 실패 확인**
- [ ] **Step 3: 문서 수정**
  - `problem-explain-integration.md:7`: "explain-author와 explain-blind를 서로 다른 시도로 배정한다"를 "문항마다 `explain-author-pN`과 `explain-blind-pN`을 동시에 배정한다(`problem_contract` RUN). 같은 문항의 작성자와 풀이자는 다른 에이전트여야 한다"로 바꾼다.
  - `runner-contract.md:111`: "`owner_task`는 항상 `explain-author`다"를 "`owner_task`는 결함 `target` 문항의 `explain-author-pN`이다(`explain-author`로 적으면 실행기가 정규화한다)"로 바꾼다.
  - `worker-prompt.md:7`: "봉인된 문제·그림만 연다"에 "자기 문항 폴더(`sealed/pN/`)"를 덧붙인다.
- [ ] **Step 4: 통과 확인** — `python -m pytest <S>/tests/test_skill_files.py -q`
- [ ] **Step 5: 커밋 후 PR** — `docs(review-pack): describe per-problem explanation work`. PR 3을 연다.

---

# Part D — PR 4: 조각 사전 검사 (브랜치 `feat/review-pack-fragment-probe`)

### Task D1: `task probe` 명령

**Files:**
- Create: `<S>/scripts/pack_probe.py`
- Modify: `<S>/scripts/pack_cli.py:76-85` (task 하위 명령에 `probe`), `:167-184` (`execute`)
- Modify: `<S>/scripts/pack_flow.py` (`init_run` 병렬 블록에 `probe_contract`)
- Test: Create `<S>/tests/test_pack_probe.py`

**Interfaces:**
- Produces: `fragment_probe(run: Path, task_id: str, attempt: str, *, layout=None) -> dict`
  - `author-<sid>`의 현재 시도에서 `<attempt_dir>/sections/<sid>.html`을 읽는다.
  - 브리프의 `manifest`에서 `sections`를 그 섹션 하나로 줄인 사본으로 `assemble.build_note(m_slice, attempt_dir)`를 호출해 `<attempt_dir>/probe/preview.html`을 쓴다.
  - 진단은 `pack_parallel.common_diagnostics(source, preview, None)` 결과다. 단 `broken-link` 중 `detail`이 `manifest.problem_pdf_name/answer_pdf_name/note_name`인 것은 뺀다.
  - 화면은 `layout(preview, out) -> (exit_code, report)`로 `layout_probe.main([preview, '--widths','1280,375','--themes','light,dark','--out', out])`를 호출한다(테스트에서 주입 가능).
  - 결과 `<attempt_dir>/probe/probe.json`을 쓰고 반환한다: `{schema_version:1, task_id, attempt, fragment_sha256, problems:[{code,where,detail}], layout:{status:'pass'|'defects'|'unavailable', defects:int, report:<path|null>}, status:'pass'|'defects'}`.
  - `status`는 `problems`가 비고 `layout.status`가 `'pass'` 또는 `'unavailable'`이면 `pass`다. layout 종료 코드 2(브라우저 없음 등)는 `unavailable`이다.
- 읽기 전용 명령이다. `run-status.json`을 쓰지 않는다(`pack_cli.main`의 `read_only` 집합에 `probe`를 추가). 단 시도 폴더에는 쓴다.

- [ ] **Step 1: 실패하는 테스트를 쓴다** (`tests/fixtures/mini-run`의 `manifest.json`과 `sections/s1.html` 사용)
```python
def test_probe_passes_clean_fragment(tmp_path):
    run, tid, attempt = claimed_author(tmp_path, fragment=FIXTURE/'sections/s1.html')
    result = fragment_probe(run, tid, attempt, layout=lambda html, out: (0, {'checks': []}))
    assert result['status'] == 'pass' and result['problems'] == []
    assert result['fragment_sha256'] == flow._sha(attempt_dir(run, tid)/'sections/s1.html')

def test_probe_reports_fragment_defect(tmp_path):
    bad = '<article class="topic" id="dup"></article><article class="topic" id="dup"></article>'
    run, tid, attempt = claimed_author(tmp_path, text=bad)
    result = fragment_probe(run, tid, attempt, layout=lambda h, o: (0, {'checks': []}))
    assert result['status'] == 'defects' and any(p['code'] == 'duplicate-id' for p in result['problems'])

def test_probe_treats_missing_browser_as_unavailable(tmp_path):
    run, tid, attempt = claimed_author(tmp_path, fragment=FIXTURE/'sections/s1.html')
    result = fragment_probe(run, tid, attempt, layout=lambda h, o: (2, None))
    assert result['layout']['status'] == 'unavailable' and result['status'] == 'pass'

def test_probe_real_layout(tmp_path):
    pytest.importorskip('playwright')
    run, tid, attempt = claimed_author(tmp_path, fragment=FIXTURE/'sections/s1.html')
    assert fragment_probe(run, tid, attempt)['layout']['status'] in ('pass', 'defects')
```
`claimed_author(tmp_path, *, fragment=None, text=None) -> (run, task_id, attempt)`는 `selected(...)`로 `scope-final`까지 seed한 뒤 `author-<sid>`를 claim하고 조각을 시도 폴더에 쓴다. 이 파일 안에 정의한다. `sid`·manifest는 mini-run 픽스처의 것을 쓴다.

- [ ] **Step 2: 실패 확인** — `ImportError: pack_probe`
- [ ] **Step 3: 구현** — 위 명세대로 한다. `init_run` 병렬 블록에 `state['probe_contract'] = 1`. CLI는 `task probe --run --task --attempt`이고, 응답은 `dict(status=result['status'], details_path=<probe.json>)`, exit는 `int(result['status'] != 'pass')`.
- [ ] **Step 4: 통과 확인** — `python -m pytest <S>/tests/test_pack_probe.py -q` PASS(브라우저 없으면 마지막 테스트 skip)
- [ ] **Step 5: 커밋** — `feat(review-pack): probe a single section before handoff`

### Task D2: 작성자 receipt 게이트와 문서

**Files:**
- Modify: `<S>/scripts/pack_parallel.py:500-525` (`validate_worker`의 done 경로)
- Modify: `<S>/references/delegation.md:60` (화면 탐침)
- Modify: `<S>/references/worker-prompt.md:21-28`
- Modify: `<S>/tests/test_parallel_pack_integration.py` (`Trial.worker`가 author 작업에 probe를 실행)
- Test: `<S>/tests/test_pack_probe.py`

**Interfaces:**
- Consumes: D1 `fragment_probe`, `probe.json` 스키마.
- 규칙: `probe_contract` RUN에서 `role == 'author'`이고 상태가 `done`이면, `<attempt_dir>/probe/probe.json`이 있어야 한다. 그 `fragment_sha256`이 현재 조각 해시와 같고 `status == 'pass'`여야 한다. 실패 사유는 `'fragment probe missing, stale or failing'`이다. probe.json은 `verified_files`에 추가한다.

- [ ] **Step 1: 실패하는 테스트를 쓴다**
```python
def test_author_receipt_requires_current_passing_probe(tmp_path):
    run, tid, attempt = claimed_author(tmp_path, fragment=FIXTURE/'sections/s1.html')
    receipt = submit_author(run, tid, attempt)                # build-receipt까지
    assert flow.check_task(run, tid, attempt, receipt)['reason'] == 'fragment probe missing, stale or failing'
    fragment_probe(run, tid, attempt, layout=lambda h, o: (0, {'checks': []}))
    assert flow.check_task(run, tid, attempt, receipt)['status'] == 'ok'
    (attempt_dir(run, tid)/'sections/s1.html').write_text('changed', encoding='utf-8')
    receipt = submit_author(run, tid, attempt)
    assert flow.check_task(run, tid, attempt, receipt)['status'] == 'failed'
```
`submit_author`는 `pack_support.parallel_worker`의 submission/build-receipt 부분을 떼어 같은 파일에 정의한다.

- [ ] **Step 2: 실패 확인**
- [ ] **Step 3: 구현**
  - `validate_worker`에 위 규칙을 넣는다.
  - `Trial.worker`: `tid.startswith('author-')`이고 상태에 `probe_contract`가 있으면, build-receipt 전에 `self.cli('task','probe',*task)`를 부른다. 통합 테스트 환경에 브라우저가 없으면 `unavailable`로 통과한다.
  - `delegation.md:60`의 "작성자와 browser-qa는 인계 전에 `python3 <SKILL>/scripts/layout_probe.py …`를 실행한다"에서 작성자 부분을 "작성자는 인계 전에 `<python> <SKILL>/scripts/pack_cli.py task probe --run <RUN> --task <id> --attempt <UUID>`를 실행해 status pass를 확인한다"로 바꾼다. browser-qa의 기존 문장은 유지한다.
  - `worker-prompt.md`의 반환 전 명령 목록에 author 전용으로 같은 `task probe` 줄을 `build-receipt` 앞에 넣는다.
- [ ] **Step 4: 통과 확인** — `python -m pytest <S>/tests -q` 전체 PASS
- [ ] **Step 5: 커밋 후 PR** — `feat(review-pack): require a passing fragment probe for author handoff`. PR 4를 연다.

---

## 완료 확인 (각 PR 머지 전)

- `python -m pytest <S>/tests -q` 전체 PASS
- `python -m pytest .claude/skills/ec2-problem-explain/tests -q` PASS(Part C는 자식 픽스처를 건드림)
- `grep -rn "python3 " <S>/references` 결과 없음(Part A 이후)
- 기존 병렬 RUN 호환: 계약 필드를 지운 상태에서 `test_existing_run_keeps_single_explain_tasks`와 `test_source_prep_stays_worker_without_contract`가 PASS
