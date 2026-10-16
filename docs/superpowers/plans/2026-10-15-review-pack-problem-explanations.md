# 복습팩 문제설명 통합 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 앞으로 생성하는 복습팩에 검토를 통과한 문제설명 HTML·MD를 포함하고, 기존 문제 있는 팩 9개에도 같은 기준으로 설명을 보충한다.

**Architecture:** `ec2-review-pack`은 정리노트와 문제 목록을 확정한 뒤 형제 스킬 `ec2-problem-explain`의 전체 워크플로를 호출한다. 별도 LLM 실행기나 새 문제 생성 기능은 만들지 않는다. 기존 CLI의 extract → 저작·독립 검산 → build/check → 실제 검토 → publish를 재사용하고 팩별 상태를 최종 보고에 합친다.

**Tech Stack:** Markdown 스킬, Python 3.10+, unittest, 기존 workbook 모듈, SymPy, Playwright/Chromium, 로컬 HTTP 서버, PowerShell.

**Spec:** 이 문서의 [고정 설계](#고정-설계). 2026-10-15 대화에서 제시한 grill-yourself 설계를 아래에 함께 보존했다. 세부 저작·검토 계약은 `.claude/skills/ec2-problem-explain/references/authoring.md`, `references/verification.md`를 함께 읽는다.

## Global Constraints

- 문제설명은 기존 `problems.txt`의 문항과 순서를 그대로 사용합니다.
- `lite`에서도 문제설명 검토 기준은 유지합니다.
- 검산이나 검토가 실패하면 해당 팩의 설명만 발행을 보류하고, 전체 완료로 보고하지 않습니다.
- 문제가 없는 팩은 설명 생성을 건너뜁니다.
- 원본 문제 풀이 수정은 하지 않는다. 독립 검산과 다르면 `disputed`로 보고한다.
- 기존 팩 보충 작업에서 정리노트 HTML·MD, 문제/답안 PDF, `problems.txt`, 원본 문제 md·그림은 변경하지 않는다.
- 원본 스킬은 `.claude/skills/`에서 수정한다. `.agents/skills/`는 심볼릭 링크이므로 이중 편집하지 않는다.
- 설명 HTML은 팩 최상위, 설명 MD·그림·검토 자료는 `.assets/`에 둔다.
- Python 최소 버전은 3.10이다. `build` 뒤에는 네 검토를 실제로 수행한다. `pass` 값을 일괄 주입하지 않는다.
- 커밋은 이 계획의 선택적 검토 경계다. 현재 스킬의 '커밋은 제안만 한다' 규칙에 따라 실제 커밋은 별도 사용자 지시가 있을 때만 한다.
- Windows에서는 백그라운드 프로세스를 `Start-Process -WindowStyle Hidden`으로 실행한다. 경로를 확인하지 않은 재귀 삭제·이동은 하지 않는다.

## Review Focus

1. 문제 목록 변경·slug 변경·문제 0개 전환: 이전 설명을 최신 설명처럼 남기지 않는다. Task 1의 임시 팩 재생성 시나리오로 확인한다.
2. 기존 설명이 있으나 원본·해시·검토 기록이 불완전함: 파일 존재만으로 재사용하지 않는다. Task 2의 변조/누락 대조로 확인한다.
3. 하위 검토 실패 또는 `disputed`: 기본 팩은 유지하고 설명은 보류하며 후속 팩은 계속한다. Task 1의 실패 시나리오와 Task 3의 팩별 상태 기록으로 확인한다.
4. 최신 날짜·통합/개별 범위 중복: 부모가 의도한 팩을 명시적으로 선택한다. Task 1의 범위 대조와 기존 source 테스트로 확인한다.
5. 설명 생성 중 참고 정리노트 재조립 또는 원본 변경: 과거 검토를 재활용하지 않는다. Task 2의 입력 변경 대조와 기존 CLI/publish 테스트로 확인한다.

---

## 고정 설계

이 작업은 기존 흐름의 확장이다. 새 팩에서 정리노트·MD가 확정된 뒤 문제 수가 1 이상이면 문제설명 스킬을 실행한다. CLI만 돌려서는 풀이가 저작되지 않는다. 문항별 작성자와 별도 검산자, 팩별 내용 리뷰어가 필요하다. GPT 환경의 opus는 sol로 해석하되 실제로 사용 가능한 모델 ID를 확인한다. 스킬 지정 모델을 사용할 수 없다면 그 사실을 보고하고 검토를 생략해서 완료 처리하지 않는다.

정리노트에 설명 링크를 삽입하는 기능은 이번 범위에서 추가하지 않는다. 기존 문제설명 스킬의 원본 보존 규칙을 유지한다. 새 PDF·새 문제·영상·원본 풀이 수정도 범위 밖이다.

기존 팩 조사 결과(2026-10-15):

| 팩 | 문제 수 | 작업 |
|---|---:|---|
| 0902 | 0 | 건너뜀 |
| 0904 | 0 | 건너뜀 |
| 0909 | 8 | 신규 설명 |
| 0911 | 10 | 신규 설명 |
| 0916 | 10 | 신규 설명 |
| 0918 | 10 | 신규 설명 |
| 0923 | 10 | 신규 설명 |
| 0930 | 11 | 신규 설명 |
| 1002 | 10 | 신규 설명 |
| 1007 | 10 | 기존 발행 검증, 입증 불가 시 재생성 |
| 1014 | 10 | 신규 설명 |

합계는 문제 있는 팩 9개·89문항이다. 신규 설명은 기본 8개 팩·79문항이며, 1007 재사용이 성립하지 않으면 재생성이 추가된다. 1014의 다른 `validation.json`은 인터랙티브 자료의 기록으로 문제설명 발행 증거가 아니다. 실행 시 다시 조사하고 차이가 있으면 실제 목록을 보고한다.

## 파일 구조와 책임

| 파일 | 변경 | 책임 |
|---|---|---|
| `.claude/skills/ec2-review-pack/SKILL.md` | 수정 | 산출물·호출 순서·lite·재실행·실패·보고 규칙 |
| `.claude/skills/ec2-review-pack/references/problem-explain-integration.md` | 생성 | 호출 계약·기존 팩 보충·백업/보류 절차 |
| `.claude/skills/ec2-problem-explain/SKILL.md` | 수정 | 부모 호출 모드와 독립 호출 모드의 보고 차이 |
| `docs/superpowers/reports/2026-10-15-review-pack-problem-explanations.md` | 생성 | 팩별 처리·RUN·검토·보류·보존 결과 |
| `복습노트/<range>/문제설명_<range>_<slug>.html` | 생성/검증 | 독자가 읽는 설명 |
| `복습노트/<range>/.assets/문제설명_<range>_<slug>.md` | 생성/검증 | MD 버전 |
| `복습노트/<range>/.assets/figures_문제설명_<range>_<slug>/` | 생성/검증 | 설명 소유 그림 |
| `복습노트/<range>/.assets/자료_문제설명_<range>_<slug>/` | 생성/검증 | 조각·증거·manifest·vendor·validation |

기존 `epe_cli.py`, `epe_publish.py`, `assemble.py`의 의미를 바꾸거나 새 실행기를 만들 필요는 없다. 검토 중 기존 구현 결함이 확인되면 해당 결함을 재현하고 계획 범위를 먼저 갱신한다. 문서 문자열을 그대로 검사하는 테스트는 추가하지 않는다. 기존 회귀 테스트와 실제 임시 팩 실험, 실제 자료의 검토로 확인한다.

## Task 1: 복습팩에서 문제설명 스킬을 실행하는 계약 연결

**Files:**
- Modify: `.claude/skills/ec2-review-pack/SKILL.md:3` (설명·산출물·lite), `:177` 이후(기존 MD 변환과 보고 사이), 오류 처리·재실행 규칙.
- Create: `.claude/skills/ec2-review-pack/references/problem-explain-integration.md`
- Modify: `.claude/skills/ec2-problem-explain/SKILL.md:14` (호출 모드), `:97` (보고).
- Verify: 두 스킬의 기존 `tests/`.

**Interfaces:**
- Consumes: 부모의 확정된 `range: str`, `slug: str`, `problems: list`, `RUN: absolute Path`.
- Produces: 문제 0개면 `skipped-no-problems`; 성공이면 `published`; 검토 실패면 `withheld`; 기존 팩 감사 통과면 `reused-verified`. 이는 보고용 상태이며 CLI에 새 인자를 추가하지 않는다.
- Calls: `epe_cli.py extract --repo REPO --target RANGE --run EXPLAIN_RUN` 후 형제 스킬의 저작·검산·build/check·검토·publish 전체 절차. `EXPLAIN_RUN`은 부모 `RUN/problem-explain` 아래의 새 비어 있는 실행 디렉터리.

- [ ] **Step 1: 기존 테스트로 변경 전 기준 확보**

```powershell
python -m unittest discover -s .claude/skills/ec2-review-pack/tests -v
python -m unittest discover -s .claude/skills/ec2-problem-explain/tests -v
```

프로세스를 따로 실행한다. 두 테스트 폴더 모두 `_util`을 쓰므로 한 프로세스의 통합 discovery로 섞지 않는다. 실패가 있으면 변경 전 실패로 기록한다.

- [ ] **Step 2: 통합 참조 문서에 아래 호출 계약 작성**

```markdown
## 부모 복습팩에서 호출
1. 정리노트의 기계·내용·브라우저 검토와 MD 변환을 끝낸다.
2. 문제가 0개이면 skipped-no-problems로 기록하고 설명 스킬을 실행하지 않는다.
3. manifest 문제 순서와 .assets/problems.txt가 같은지 확인한다. 다르면 부모 조립을 고친다.
4. 형제 ec2-problem-explain/SKILL.md를 읽는다. 부모 range를 명시적으로 넘기며 최신 팩 자동 선택을 사용하지 않는다.
5. 부모 RUN/problem-explain 아래 새 실행 디렉터리를 정한다. extract는 비어 있는 RUN만 받는다.
6. extract → 자료 읽기 → 문항별 저작 → 별도 독립 검산 → build/check → 네 검토 → publish를 끝까지 실행한다.
7. lite는 부모 정리노트에만 적용한다. 설명의 작성자 모델과 네 검토를 낮추거나 생략하지 않는다.
8. 부모 호출에서는 중간 단계 진행만 표시하고 최종 결과를 부모 보고에 합친다. 단독 호출은 기존 보고 형식을 유지한다.
9. source_visual/content/independent/browser 중 하나라도 통과하지 못하면 withheld다. disputed는 보류 이유로 함께 적는다.
10. 기본 팩이 남아 있어도 설명 withheld이면 전체 완료라고 쓰지 않는다. 다른 팩은 계속한다.
11. 설명 extract 이후 정리노트·문제 목록·참고 자료가 바뀌면 새 RUN에서 재시작한다.
12. 정리노트 링크 자동 삽입, 원본 수정, PDF 재빌드는 하지 않는다.
```

- [ ] **Step 3: 재실행 수명주기와 기존 팩 보충 규칙 작성**

같은 참조 문서에 다음 규칙을 넣는다. 부모의 첫 조립보다 먼저 실행하며, 재조립마다 반복 백업하지 않는다.

```markdown
## 재생성 전에 기존 설명 다루기
- 기존 설명이 있으면 최상위 문제설명_<range>_*.html, .assets/문제설명_<range>_*.md, .assets/figures_문제설명_<range>_*, .assets/자료_문제설명_<range>_*만 목록화한다.
- 목록은 정확한 range 접두사와 NFC 이름으로 비교한다. 다른 날짜나 인터랙티브 산출물은 포함하지 않는다.
- 전용 RUN/previous-explanations-<고유ID>/에 상대 경로대로 복사하고 모든 파일의 SHA-256이 일치하는지 확인한다.
- 복사가 검증된 뒤에만 해당 설명 소유 파일을 팩에서 제거한다. 실패하면 원본을 유지하고 부모의 첫 조립을 중단한다.
- 부모가 입력을 변경하기 전에 설명을 치우므로 새 설명이 보류되거나 문제가 0개가 되어도 이전 설명이 최신 파일처럼 남지 않는다.
- 기본 팩 자체의 재생성이 실패하면 기본 팩 백업을 먼저 복원한 다음 그 팩과 대응되는 설명 백업을 복원한다. 입력 대응이 확인되지 않으면 설명은 백업에 유지하고 보고한다.
- 기존 팩 보충은 입력을 바꾸지 않으므로 선제 제거하지 않는다. publish의 백업·복구를 사용한다. 기존 파일의 재사용 검증이 실패하면 기존 설명을 백업에 보존하고 발행 경로에서 치운 뒤 재생성한다.
## 기존 팩 보충
- 실제 날짜 폴더별로 problems.txt를 조사한다. 없는 팩은 skipped-no-problems로 기록한다.
- 부모 복습팩 전체를 다시 만들지 않는다. 각 팩에 설명 스킬만 실행한다.
- 기존 설명은 검토 기록·현재 입력·참조·산출 해시·조각·문항/소문항 대응이 모두 입증되는 경우에만 reused-verified다.
- 원래 저작 조각과 RUN이 없어서 input_hash를 재현할 수 없으면 추측하지 말고 재생성한다.
- 한 팩의 실패는 그 팩만 보류한다. 나머지 팩과 원본은 유지한다.
```

- [ ] **Step 4: 두 SKILL.md의 연결 지점 수정**

부모 설명과 산출물 목록에 `문제설명_<range>_<slug>.html`, `.assets/문제설명_<range>_<slug>.md`, 설명 소유 그림·자료 폴더를 추가한다. 기존 8단계(MD 변환) 뒤에 아래 단계를 추가하고 보고를 10단계로 바꾼다. 진행 표시·재진입 단계 범위·오류 표도 일치시킨다.

```markdown
### 9. 문제설명
`references/problem-explain-integration.md`의 부모 호출 계약을 따른다.
문제가 1개 이상이면 형제 `ec2-problem-explain/SKILL.md` 전체 절차를 실행한다.
문제가 0개이면 skipped-no-problems다. lite여도 설명 검토는 생략하지 않는다.
```

자식에는 부모 호출 시 range 명시·새 RUN·최종 보고 합치기만 추가한다. 보호 대상, 검토 게이트, CLI 옵션은 유지한다. 부모 최종 보고는 기본 팩 상태와 설명 상태를 따로 적고 `withheld`인 경우 '일부 완료'로 표시한다.

- [ ] **Step 5: 임시 팩 시나리오로 계약을 검토하고 결과 기록**

기존 `test_cli.py`, `test_source.py`, `test_publish.py`, 부모 `test_skill_files.py`의 fixture/경로를 읽는다. 실제 복습노트 대신 `TemporaryDirectory`의 팩을 사용한다. 기존 fixture를 호출하는 테스트가 아닌 문서 변경이므로 새 문자열 단위 테스트를 만들지 않는다. 실행자가 아래 다섯 시나리오의 실제 파일 상태를 확인해 보고서에 기록한다.

| 시나리오 | 관찰할 결과 |
|---|---|
| 문제 1개 → 0개 | 설명 호출 생략, 이전 설명은 백업에만 존재 |
| 같은 날짜 slug 변경 | 옛 slug HTML/MD/자원은 백업, 새 이름만 발행 대상 |
| 같은 날짜 문항 순서 변경 | 옛 검토 재사용 금지, 새 extract 순서 반영 |
| 통합 팩과 개별 팩 공존 | extract의 후보 모호성은 오류로 보고, 임의 선택 금지 |
| 자식 검토 not_run/disputed | publish 실패, 기본 팩 보존, 후속 팩 진행 |

백업/정리의 실제 실행은 원본 스킬에 기존처럼 검증 가능한 Python 스니펫을 넣을 경우에만 해당 스니펫을 임시 폴더에서 실행한다. 수동 워크플로로 문서화했다면 동일 파일 작업을 임시 폴더에 수행해 검증한다. 검증하지 않은 삭제 절차를 실제 팩에서 처음 실행하지 않는다.

- [ ] **Step 6: Step 1의 두 테스트 명령을 다시 실행**

추가 실패 0개. 기존 문서 스니펫 테스트의 정규식을 깨뜨리지 않는다. 의도적으로 바꾼 백업 대상이 있다면 해당 동작 테스트의 기대 파일 목록을 실제 정책과 맞춘다.

- [ ] **Step 7: 변경 diff 검토 및 커밋 제안**

```powershell
git diff --check
git diff -- .claude/skills/ec2-review-pack .claude/skills/ec2-problem-explain/SKILL.md
```

제안 메시지: `feat(skills): include problem explanations in review packs`.

## Task 2: 기존 1007 설명 감사와 원본 보존 기준 확보

**Files:**
- Read: `복습노트/1007/문제설명_1007_Differential_Amplifiers.html`
- Read: `복습노트/1007/.assets/자료_문제설명_1007_Differential_Amplifiers/`
- Create: `docs/superpowers/reports/2026-10-15-review-pack-problem-explanations.md`
- Scratch: 저장소 밖의 고유 실행 디렉터리와 원본 파일 해시 목록.

**Interfaces:**
- Consumes: Task 1 상태 규칙, 현재 팩의 `problems.txt`, 기존 설명의 manifest/validation 및 원래 저작 RUN.
- Produces: 팩별 원본 파일 SHA-256 목록; 1007의 `reused-verified` 또는 `needs-regeneration` 판정; 모든 팩의 처리 장부.

- [ ] **Step 1: 원본 보존 목록 생성**

작업 시작 시 저장소 루트를 `$repoRoot`, 저장소 밖 새 실행 디렉터리를 `$auditRun`으로 정한다. 아래 Python을 `$auditRun/snapshot.py`에 저장하고 실행한다. 이후 같은 코드로 비교할 수 있도록 JSON 파일은 덮어쓰지 않는다.

```python
import hashlib, json, re, sys
from pathlib import Path
repo, output = Path(sys.argv[1]).resolve(), Path(sys.argv[2])
if output.exists():
    raise SystemExit('기존 snapshot 덮어쓰기 금지')
paths = set()
for folder in (repo / '복습노트').iterdir():
    if not folder.is_dir() or not re.fullmatch(r'\d{4}(?:-\d{4})?', folder.name):
        continue
    paths.update(folder.glob('정리노트_*.html'))
    paths.update(folder.glob('복습문제_*.pdf'))
    paths.update((folder / '.assets').glob('정리노트_*.md'))
    paths.update((folder / '.assets').glob('problems.txt'))
for root in ('교과서/마이크로전자회로', 'from_the_past/md'):
    paths.update(p for p in (repo / root).rglob('*') if p.is_file())
data = {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(paths) if p.is_file()}
output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
print('protected files:', len(data))
```

```powershell
python "$auditRun/snapshot.py" "$repoRoot" "$auditRun/protected-before.json"
```

- [ ] **Step 2: 기존 1007 발행 자료를 읽고 원래 저작 RUN 확인**

`validation.json`, `manifest.json`, `fragments/`, `evidence/`를 읽는다. `manifest.source_sha256`을 `load_source(...).sha256`과 비교하고, `manifest.problems`의 문항/소문항 순서를 현재 source와 비교한다. `manifest.files`의 모든 상대 경로가 실제로 존재하며 SHA-256이 같은지 확인한다. 원래 RUN은 기존 대화/실행 기록에서 찾되 경로가 없거나 확인되지 않으면 `needs-regeneration`이다.

- [ ] **Step 3: 원래 RUN이 있으면 기존 API로 전체 일치 검증**

원래 RUN 경로를 실제 확인한 뒤 아래를 `$auditRun/verify-existing.py`로 저장한다. 명령 인자는 repo, 원래 RUN, 대상 range 순서다. 함수 시그니처는 현재 `epe_cli.py`/`epe_render.py`/`epe_contract.py`를 사용한다.

```python
import json, sys
from pathlib import Path
repo, run, target = Path(sys.argv[1]).resolve(), Path(sys.argv[2]), sys.argv[3]
sys.path.insert(0, str(repo / '.claude/skills/ec2-problem-explain/scripts'))
from epe_cli import load_run, load_fragments
from epe_contract import validate_reviews
from epe_render import check_artifacts, artifact_hashes, names
from epe_source import sha256, inside
from epe_types import Artifacts
items = [item for item in load_run(run) if item['pack'].range == target]
assert len(items) == 1, '원래 RUN에서 팩을 유일하게 찾을 수 없음'
item = items[0]
pack, fragments = item['pack'], load_fragments(item)
stem, fig, data = names(pack)
root = pack.folder
manifest_path = root / '.assets' / data / 'manifest.json'
review = json.loads((manifest_path.parent / 'validation.json').read_text(encoding='utf-8'))
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
files = tuple(inside(root / name, root) for name in manifest['files']) + (manifest_path,)
artifacts = Artifacts(root / (stem + '.html'), root / '.assets' / (stem + '.md'), manifest_path, files)
errors = check_artifacts(pack, artifacts) + validate_reviews(pack, fragments, review)
assert not errors, errors
assert review['artifact_hashes'] == artifact_hashes(artifacts)
assert review.get('references'), '참조 기록 없음'
for ref in review['references']:
    path = inside(Path(ref['path']), repo)
    assert path.is_file() and sha256(path) == ref['sha256'], str(path)
print(target, 'existing publication integrity PASS')
```

스크립트 실패는 `needs-regeneration`이다. 파일을 고쳐 해시를 맞추지 않는다. 통과해도 실제 evidence가 판정을 뒷받침하는지 읽고, 현재 발행 HTML의 브라우저 검사를 Task 3의 절차로 수행해야 `reused-verified`다.

- [ ] **Step 4: 검사 자체의 실패 감지 확인**

1007 실파일을 변경하지 않는다. 임시 복사본에서 manifest가 추적하는 HTML 한 바이트 변경·파일 하나 누락을 각각 만들어 `check_artifacts`가 오류를 반환하는지 확인한다. 원래 RUN의 문제 목록 변경 감지는 기존 `test_cli.py`의 추출 데이터 변경 테스트를 실행해 확인한다.

- [ ] **Step 5: 보고서 장부 초기화**

```markdown
# 기존 복습팩 문제설명 보충 결과
기준 날짜: 2026-10-15
원본 해시 목록: 실제 audit RUN 경로
| 팩 | 문항 | 상태 | RUN | 검토/보류 근거 | HTML |
|---|---:|---|---|---|---|
```

11개 팩의 행을 추가한다. 실행 전 행은 `pending`, 문제 없는 두 팩은 `skipped-no-problems`로 기록한다. 1007 판정과 근거를 적는다. 계획 시점 예상 수를 실제 결과로 위장하지 않는다.

## Task 3: 기존 팩별 설명 저작·검산·발행

**Files:**
- Create/Verify: 파일 구조 표의 각 팩 설명 HTML·MD·그림·자료.
- Update: `docs/superpowers/reports/2026-10-15-review-pack-problem-explanations.md`
- Read-only: 원본 문제·정리노트·PDF·`problems.txt`.

**Interfaces:**
- Consumes: Task 1의 호출/보충 계약과 Task 2의 원본 해시·1007 감사 결과.
- Produces: 각 팩의 `published | reused-verified | withheld`; 실패 시 `disputed` 상세와 stage 경로. 팩끼리 RUN·pN 임시 경로를 공유하지 않는다.

이 Task는 아래 날짜별 반복을 각각 독립된 리뷰 경계로 실행한다. 한 문항 저작·한 검산·한 evidence 저장을 별도 체크 항목으로 장부에 펼친다. 89문항을 한 번의 거대한 작성/검토 작업으로 묶지 않는다. 동시 에이전트 수는 실행 환경 한도를 따른다.

- [ ] 0909: 8문항, 아래 팩별 실행 절차 전체 수행.
- [ ] 0911: 10문항, 아래 팩별 실행 절차 전체 수행.
- [ ] 0916: 10문항, 아래 팩별 실행 절차 전체 수행.
- [ ] 0918: 10문항, 아래 팩별 실행 절차 전체 수행.
- [ ] 0923: 10문항, 아래 팩별 실행 절차 전체 수행.
- [ ] 0930: 11문항, 아래 팩별 실행 절차 전체 수행.
- [ ] 1002: 10문항, 아래 팩별 실행 절차 전체 수행.
- [ ] 1007: 감사 통과 시 브라우저 재확인 후 재사용, 아니면 10문항 재생성.
- [ ] 1014: 10문항, 아래 팩별 실행 절차 전체 수행.

### 팩별 실행 절차

다음 명령은 PowerShell에서 실행한다. `$repoRoot`는 실제 저장소 절대 경로, `$scratchRoot`는 저장소 밖 작업 폴더, `$range`는 위 체크 항목의 네 자리 날짜다. 모델 저작 단계를 명령으로 대체하지 않는다.

- [ ] **Step 1: 새 RUN에서 extract**

```powershell
$explainSkill = Join-Path $repoRoot '.claude/skills/ec2-problem-explain'
$explainRun = Join-Path $scratchRoot ("epe-" + $range + "-" + [guid]::NewGuid().ToString('N'))
python "$explainSkill/scripts/epe_cli.py" extract --repo "$repoRoot" --target "$range" --run "$explainRun"
```

종료 코드 0과 `source.json`을 확인한다. 실패한 팩은 이유를 기록하고 다음 팩으로 간다. 범위가 아닌 정확한 날짜별 명시 호출이므로 다른 팩이 선택되면 중단해 원인을 확인한다.

- [ ] **Step 2: 문항별 자료 배정 및 작성자 작업 생성**

`source.json`에서 문항/소문항을 열거한다. 각 문항에 문제 md, 관련 교과서 절·쪽, 강의자료·정리노트 anchor를 배정한다. 작성자에게 실제 경로로 채운 다음 브리프를 준다.

```text
ec2-problem-explain/references/authoring.md를 먼저 읽는다.
배정받은 source.json과 문항 id의 조건·구할 것·소문항을 읽고,
배정된 교과서·강의자료·정리노트를 실제로 읽는다.
source의 원문·조건·그림은 다시 쓰지 않는다.
단서→개념과 공식→실제 첫 줄→이유를 포함한 풀이→완성 답→검산→함정→다시 풀기를 작성한다.
solve와 verify에 source의 모든 subpart를 각각 한 번 포함한다.
출력은 배정된 BUCKET/explanations/pN.html 하나이며 임시는 고유 RUN/work/pN에만 쓴다.
원본 문제 md·정리노트·PDF는 수정하지 않는다.
```

이 브리프와 함께 실행자는 source 경로·문항 id·출력 경로·참고 쪽을 도구의 실제 인자로 제공한다. 문항마다 HTML 수식·차원·근사 조건·완성 답이 있어야 한다.

- [ ] **Step 3: 작성자와 다른 에이전트로 문항별 독립 검산**

처음에는 원래 문제 조건·그림·구할 것만 제공하고 답을 먼저 구하게 한다. 그 뒤 md 답·저작 조각과 대조한다. `verification.md`대로 `pN-sympy.py`와 실행 출력 `pN-result.txt`를 evidence에 남긴다. 정성·증명 문항은 해당 method와 실제 논증을 사용한다. 조각 오류는 수정 후 재검산, 원본 답 불일치는 `disputed`로 보류한다.

- [ ] **Step 4: 모든 조각과 evidence가 모인 뒤 build/check**

```powershell
python "$explainSkill/scripts/epe_cli.py" build --run "$explainRun"
python "$explainSkill/scripts/epe_cli.py" check --run "$explainRun"
```

`check: machine PASS`가 필요하다. 최대 2회 수정하며, 재build 시 review가 초기화된다는 사실을 유지한다.

- [ ] **Step 5: source_visual 검토**

`workbook/source_pages.py render`로 실제 문항 md의 원본 쪽을 렌더하고 이미지를 연다. 조건 수치·회로 연결·소문항·구할 것을 source와 stage HTML에 대조한다. 사용한 md 절대 경로 목록을 Python subprocess 인자 리스트로 넘겨 공백 경로를 보존한다. 원본 차이는 해당 팩을 보류한다.

- [ ] **Step 6: 작성자가 아닌 리뷰어에게 모든 소문항의 내용 검토 요청**

`verification.md`와 `authoring.md`, stage, source, 읽은 참고 자료를 제공한다. recall/start/solve/verify/sum의 실제 내용과 모든 소문항 답을 검토한다. 검토 결과를 실제 reviewer/evidence와 함께 기록한다.

- [ ] **Step 7: stage를 HTTP로 열고 브라우저 검사**

`stage.json`에서 실제 stage HTML 경로를 얻는다. 빈 포트를 선택해 서버를 시작한다. PowerShell에서는 `Start-Process -WindowStyle Hidden -PassThru`로 PID를 보관한다. 측정 명령은 아래와 같으며 `$stageUrl`, `$topicCount`, `$shotsDir`는 방금 확인한 실제 값이다.

```powershell
python "$explainSkill/scripts/epe_browser_check.py" --url "$stageUrl" --topics $topicCount --shots "$shotsDir"
```

네 화면 조합에서 오류가 없어야 한다. `flaky_rerun`이면 서버를 확인하고 재측정한다. 보이는 내장 브라우저에서는 목차·pager·테마 토글을 실제로 눌러 확인한다. 서버는 `finally`에서 보관한 PID만 종료한다. 수정 시 build부터 네 검토를 다시 한다.

- [ ] **Step 8: 검토 기록 완성 후 publish**

`review.json`에 실제 수행한 source_visual/content/independent/browser 결과와 읽은 references SHA-256을 기록한다. machine PASS를 수학 검토로 복사하지 않는다.

```powershell
python "$explainSkill/scripts/epe_cli.py" publish --run "$explainRun"
```

`publish:` 출력과 HTML·MD·validation 파일을 확인한다. 보류라면 stage와 이유를 보고하고 다음 팩으로 간다. 발행 뒤 설명 파일을 손으로 고치지 않는다.

- [ ] **Step 9: 팩 단위 결과 검토·장부 기록·커밋 제안**

팩의 문항/소문항 수, 상태, HTML/MD, RUN, 백업, disputed 식·수치, 브라우저 evidence를 장부에 기록한다. 재사용 팩은 Task 2 검사와 브라우저 결과를 함께 연결한다. 각 팩의 변경 파일만 `git diff --stat`으로 확인한다. 제안 메시지는 `docs(notes): add problem explanations <실제 날짜>`다.

## Task 4: 전체 보존·발행 범위 검증과 결과 보고

**Files:**
- Read: 모든 처리 팩과 Task 2 원본 해시 목록.
- Update: `docs/superpowers/reports/2026-10-15-review-pack-problem-explanations.md`

**Interfaces:**
- Consumes: Task 3 팩별 결과와 original snapshot.
- Produces: 전체 완료 또는 일부 완료의 근거 있는 최종 보고. withheld가 하나라도 있으면 전체 완료 조건은 충족되지 않는다.

- [ ] **Step 1: 원본 파일 바이트 보존 검사**

다음 스크립트를 audit RUN에 저장하고 repo와 `protected-before.json`을 인자로 실행한다.

```python
import hashlib, json, sys
from pathlib import Path
repo = Path(sys.argv[1]).resolve()
before = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
changed = []
for name, digest in before.items():
    path = repo / name
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        changed.append(name)
assert not changed, changed
print('original preservation PASS:', len(before))
```

원본 변경이 있으면 설명 발행 완료로 보고하기 전에 원인을 확인한다. 사용자가 동시에 수정한 파일이면 임의로 되돌리지 않고 별도 표시한다.

- [ ] **Step 2: 실제 발행 범위 검사**

9개 문제 있는 팩 각각 HTML·MD·설명 전용 validation 존재와 문항 수를 확인한다. 0902·0904에는 설명이 추가되지 않았는지 확인한다. 모든 `validation.json`을 넓게 찾는 대신 현재 slug의 `자료_문제설명_.../validation.json`만 검사한다. Task 2의 검사 스크립트를 각 발행 RUN에 적용한다. `reused-verified`에는 검증한 원래 RUN을 적용한다.

- [ ] **Step 3: 회귀 테스트와 diff 검사**

```powershell
python -m unittest discover -s .claude/skills/ec2-review-pack/tests -v
python -m unittest discover -s .claude/skills/ec2-problem-explain/tests -v
git diff --check
git status --short
```

문제 설명의 증거·자료가 폴더 규칙에 맞고 임시 RUN이 저장소에 섞이지 않았는지 확인한다. 보호 대상 파일이 diff에 나타나면 Step 1 결과와 대조한다.

- [ ] **Step 4: 보고서를 실제 결과로 마무리**

성공/재사용/보류/문제 없음 팩 수, 신규·재작성 문항 수, 원본 보존 결과, 실행한 검사와 실패, 팩별 RUN·백업·HTML 링크를 적는다. `withheld`가 있으면 보류 원인과 재개 지점을 적는다. 사용자 최종 답변에는 변경된 스킬과 보고서 링크, 실제 발행 수, 미해결만 간단히 전한다.

## 계획 자체 검토

- 설계 요구 대응: 자동 통합·lite·문제 0개·실패 분리·재생성 수명주기는 Task 1, 기존 설명 재사용과 원본 보존은 Task 2, 실제 모든 팩 보충은 Task 3, 전체 검증은 Task 4에 배정했다.
- 인터페이스: CLI 옵션은 기존 extract/build/check/publish만 사용하며, 보고 상태를 CLI의 새 반환 타입으로 오해하지 않도록 구분했다.
- 검토 근거: machine PASS와 네 의미/화면 검토를 분리했다. 내용이 없는 승인 기록이나 불완전한 원래 RUN으로 기존 설명을 재사용하지 않는다.
- 계획 실행 방법은 아직 선택되지 않았다. 구현 전 사용자의 계획 검토와 실행 방법 선택을 기다린다.
