# 정리노트 "왜 이런 회로를 쓸까" 페이지 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 전자회로2 정리노트 맨 앞에 "왜 이런 회로를 쓸까" 토픽 1장을 넣는다. 새 팩에는 스킬이 항상 만들고, 기존 10개 팩에는 덧붙인다.

**Architecture:** manifest에 고정 첫 섹션 `why`(토픽 `why-circuit`)를 넣고 `manifest.py`가 이를 강제한다. `assemble.py`는 그대로 둔다. 기존 팩은 새 스크립트 `insert_why.py`로 조각을 HTML에 끼워넣고, 기존 `check_html.py`와 `html2md.py`로 검증한다.

**Tech Stack:** Python 3 표준 라이브러리, unittest, 기존 스킬 스크립트(`.claude/skills/ec2-review-pack/scripts/`).

**Spec:** `docs/superpowers/specs/2026-10-11-why-circuit-page-design.md`

## Global Constraints

- 섹션 id `why`, 토픽 id `why-circuit`. 섹션 title `들어가며: 왜 이런 회로를 쓸까`, short `왜 쓸까`, 토픽 h3 `왜 이런 회로를 쓸까`.
- 기존 팩의 토픽·섹션 id(`s0-…`)는 바꾸지 않는다.
- why 토픽에는 레이어 `eli5`, `formal`이 반드시 있고, 맨 끝에 `<div class="sum" hidden>`이 있다. 위젯과 `<script>`는 넣지 않는다.
- 레이어 제목 글자, 수식 표기, SVG 클래스, 이모지 금지 같은 기존 `references/content-rules.md` 규칙을 그대로 따른다.
- 저장소의 `STT/`, `강의노트/`, `교과서/`, `workbook/`에는 쓰지 않는다. 작성자 에이전트는 scratchpad에만 쓴다.
- 커밋에는 이 작업 파일만 넣는다. 작업 트리에 이미 있는 `scripts/ec2_report/*`, `tests/ec2_report/*`, `설계과제/…/pulled_v3.md` 변경은 넣지 않는다. push는 사용자 확인 후에만 한다.
- 기준선: `test_assemble.TestAssemble.test_template_is_identical_to_ml`은 이 작업 전부터 실패한다(ML 템플릿과 차이). 이 실패는 고치지 않고, 그 밖의 실패만 0이어야 한다.

테스트 명령(저장소 루트에서): `python3 -m unittest discover -s .claude/skills/ec2-review-pack/tests`
아래에서 `T`는 이 명령을 가리킨다.

## Review Focus

- 같은 노트에 `insert_why.py`를 두 번 실행해도 why 섹션과 목차 링크가 하나씩만 있어야 한다 → Task 2 `test_idempotent`.
- why 조각의 `href="#…"`가 노트에 없는 토픽을 가리키면 실패해야 한다 → Task 4 Step 4(`check_html.py` broken-link). Task 2는 조각 구조만 검증한다.
- 조각에 `<section>`, `<h2>`, `<script>`가 있거나 `why-circuit` article, `.sum`, eli5·formal 레이어가 빠지면 아무것도 쓰지 않고 실패해야 한다 → Task 2 `test_rejects_bad_fragment`.
- NFD 파일명(macOS) 노트 경로도 그대로 처리해야 한다 → Task 4는 경로를 `os.listdir` + NFC 비교로 찾는다(기존 스킬 관례).
- manifest에서 why를 예고 토픽으로 지정하거나 두 번째 섹션에 두면 검증이 실패해야 한다 → Task 1 테스트.

---

### Task 1: manifest 계약 — 첫 섹션 `why` 강제

**Files:**
- Modify: `.claude/skills/ec2-review-pack/scripts/manifest.py` (상수 추가, `validate()`의 sections 루프 뒤 `:139` 앞)
- Modify: `.claude/skills/ec2-review-pack/tests/fixtures/mini-run/manifest.json`
- Create: `.claude/skills/ec2-review-pack/tests/fixtures/mini-run/sections/why.html`
- Test: `.claude/skills/ec2-review-pack/tests/test_manifest.py`, `tests/test_assemble.py:35-39`

**Interfaces:**
- Produces (in `manifest.py`): `WHY_SECTION_ID = "why"`, `WHY_TOPIC_ID = "why-circuit"`, `WHY_TITLE = "들어가며: 왜 이런 회로를 쓸까"`, `WHY_SHORT = "왜 쓸까"`, `WHY_TOPIC_TITLE = "왜 이런 회로를 쓸까"`, `WHY_REQUIRED_LAYERS = ("eli5", "formal")`.

- [ ] **Step 1: 픽스처를 새 계약에 맞춘다.** `manifest.json`의 `sections` 맨 앞에 다음 항목을 넣는다.
  `{"id": "why", "title": "들어가며: 왜 이런 회로를 쓸까", "short": "왜 쓸까", "topics": [{"id": "why-circuit", "title": "왜 이런 회로를 쓸까", "required_terms": ["대푯값", "평균", "분산"], "layers": ["eli5", "formal"], "supp": false}]}`
  `sections/why.html`에는 `<article class="topic" id="why-circuit"><h3>왜 이런 회로를 쓸까</h3>`를 쓴다. 안에는 eli5 레이어(`쉽게 말하면`, `대푯값` 포함), formal 레이어(`평균`, `분산`, `<a href="#s1-mean">평균</a>` 포함), 맨 끝의 `<div class="sum" hidden><p class="sum-lead">…</p></div>`가 들어간다. 이모지와 `$`는 쓰지 않는다.

- [ ] **Step 2: 실패하는 테스트를 쓴다.** `test_manifest.py`의 `TestManifest`에 추가한다(`mini()` 사용).

```python
def test_first_section_must_be_why(self):
    m = mini(); m["sections"] = m["sections"][1:]
    self.assertIn("sections[0].id: 첫 섹션은 why여야 함", manifest.validate(m))

def test_why_must_have_single_why_circuit_topic(self):
    m = mini(); m["sections"][0]["topics"].append(dict(m["sections"][0]["topics"][0], id="why-extra"))
    self.assertIn("sections[0].topics: why 섹션의 토픽은 why-circuit 하나여야 함", manifest.validate(m))

def test_why_needs_eli5_and_formal(self):
    m = mini(); m["sections"][0]["topics"][0]["layers"] = ["eli5"]
    self.assertIn("sections[0].topics[0].layers: why-circuit에는 eli5와 formal이 필요함", manifest.validate(m))

def test_why_cannot_be_preview(self):
    m = mini(); m["preview_topic"] = "why-circuit"
    self.assertIn("preview_topic: why-circuit은 예고 토픽이 될 수 없음", manifest.validate(m))
```

  `test_assemble.py`의 `test_sections_toc_and_titles`에서 기대 목차를 `<nav class="toc" aria-label="목차"><a href="#why">왜 쓸까</a><a href="#s1">1 기초</a><a href="#s2">2 요약·예고</a></nav>`로 바꾼다. `self.assertLess(self.html.index('<section id="why">'), self.html.index('<section id="s1">'))`도 추가한다.

- [ ] **Step 3: 실패를 확인한다.** Run: `T`
  Expected: 위 4개 manifest 테스트가 FAIL한다. 기준선 실패 1개는 그대로다. 나머지는 PASS한다(픽스처가 이미 why를 갖고 있으므로 assemble·check_html·html2md 테스트는 통과).

- [ ] **Step 4: `validate()`에 why 규칙을 구현한다.** 오류 문자열은 Step 2와 글자 그대로 같아야 한다. 검사는 4가지다.
  - `sections`가 비어 있지 않은데 `sections[0]["id"] != WHY_SECTION_ID`이면 오류를 낸다.
  - 첫 섹션이 why면 `topics`의 id 목록이 정확히 `[WHY_TOPIC_ID]`인지 본다.
  - 그 토픽의 `layers`가 `WHY_REQUIRED_LAYERS`를 모두 포함하는지 본다.
  - `preview_topic == WHY_TOPIC_ID`이면 오류를 낸다.
  필드 누락이나 타입 오류가 이미 보고된 경우에는 예외 없이 건너뛴다(`_need`와 같은 방식).

- [ ] **Step 5: 통과를 확인한다.** Run: `T`
  Expected: 기준선 1개를 뺀 전부 PASS.

- [ ] **Step 6: Commit**
```bash
git add .claude/skills/ec2-review-pack/scripts/manifest.py .claude/skills/ec2-review-pack/tests
git commit -m "feat(ec2-review-pack): require leading why-circuit section in manifest"
```

### Task 2: `insert_why.py` — 기존 노트에 why 섹션 끼워넣기

**Files:**
- Create: `.claude/skills/ec2-review-pack/scripts/insert_why.py`
- Test: `.claude/skills/ec2-review-pack/tests/test_insert_why.py`

**Interfaces:**
- Consumes: `manifest.WHY_SECTION_ID`, `WHY_TOPIC_ID`, `WHY_TITLE`, `WHY_SHORT`, `WHY_REQUIRED_LAYERS` (Task 1). `assemble.esc`.
- Produces:
  - `class InsertError(RuntimeError)`
  - `insert_why(note_html: str, fragment: str, title: str = WHY_TITLE, short: str = WHY_SHORT) -> str`
  - `main(argv: list[str] | None = None) -> int`. CLI는 `insert_why.py --note PATH --fragment PATH [--title T] [--short S]`이고, 노트를 그 자리에서 고친다. 성공하면 노트 경로를 출력하고 0을 반환한다. `InsertError`이면 `insert_why 실패: …`를 stderr에 쓰고 1을 반환하며, 파일은 그대로 둔다.

- [ ] **Step 1: 실패하는 테스트를 쓴다.** 노트는 Task 1 픽스처로 `assemble.assemble(MINI_RUN, tmp)`해서 만든 HTML에서 `<section id="why">…</section>`과 목차 링크 `<a href="#why">왜 쓸까</a>`를 지운 것을 쓴다(헬퍼 `bare_note()`). 조각은 `MINI_RUN/sections/why.html`(헬퍼 `frag()`).

```python
def test_inserts_section_before_first_section_and_toc_first(self):
    out = insert_why.insert_why(bare_note(), frag())
    self.assertLess(out.index('<section id="why"><h2>들어가며: 왜 이런 회로를 쓸까</h2>'), out.index('<section id="s1">'))
    self.assertIn('<nav class="toc" aria-label="목차"><a href="#why">왜 쓸까</a><a href="#s1">', out)

def test_idempotent(self):
    once = insert_why.insert_why(bare_note(), frag())
    self.assertEqual(insert_why.insert_why(once, frag()), once)
    self.assertEqual(once.count('id="why"'), 1); self.assertEqual(once.count('href="#why"'), 1)

def test_replaces_existing_why(self):
    once = insert_why.insert_why(bare_note(), frag())
    out = insert_why.insert_why(once, frag().replace("대푯값", "대표값X"))
    self.assertIn("대표값X", out); self.assertEqual(out.count('<section id="why">'), 1)

def test_rejects_bad_fragment(self):
    bad = {"section": frag().replace("<h3>", "<section><h3>", 1),
           "h2": frag().replace("<h3>", "<h2>x</h2><h3>", 1),
           "script": frag() + "<script>1</script>",
           "no-article": frag().replace('id="why-circuit"', 'id="other"'),
           "no-sum": frag().replace('class="sum"', 'class="summary"'),
           "no-formal": frag().replace("layer formal", "layer other")}
    for name, f in bad.items():
        with self.subTest(name=name), self.assertRaises(insert_why.InsertError):
            insert_why.insert_why(bare_note(), f)

def test_rejects_note_without_toc_or_section(self):
    for broken in (bare_note().replace('<nav class="toc" aria-label="목차">', "<nav>"),
                   bare_note().replace("<section id=", "<div id=")):
        with self.subTest(), self.assertRaises(insert_why.InsertError):
            insert_why.insert_why(broken, frag())

def test_cli_leaves_file_untouched_on_error(self):
    note = self.tmp / "n.html"; note.write_text(bare_note(), encoding="utf-8")
    bad = self.tmp / "f.html"; bad.write_text("<p>x</p>", encoding="utf-8")
    before = note.read_bytes()
    self.assertEqual(insert_why.main(["--note", str(note), "--fragment", str(bad)]), 1)
    self.assertEqual(note.read_bytes(), before)

def test_result_passes_check_html(self):
    for pdf in ("문제", "답안"):  # 노트가 링크하는 복습문제 PDF를 만들어 broken-link를 피한다
        (self.tmp / f"복습문제_0101-0102_Mini_Test-{pdf}.pdf").write_bytes(b"%PDF")
    note = self.tmp / "n.html"
    note.write_text(insert_why.insert_why(bare_note(), frag()), encoding="utf-8")
    self.assertEqual(check_html.check_file(note), [])
```

- [ ] **Step 2: 실패를 확인한다.** Run: `T`. Expected: `ModuleNotFoundError: insert_why`.

- [ ] **Step 3: `insert_why()`를 구현한다.** 순서:
  1. 조각을 검증한다. `<section`, `<h2`, `<script`가 있으면 안 된다. `<article class="topic" id="why-circuit">`가 있어야 한다. `class="layer eli5"`, `class="layer formal"`, `<div class="sum" hidden>`이 있어야 한다. 하나라도 어기면 무엇이 틀렸는지 담은 `InsertError`를 낸다.
  2. 노트에 `<section id="why">…</section>`이 이미 있으면 비탐욕 정규식(`re.S`)으로 지운다. 목차의 `<a href="#why">…</a>`도 지운다.
  3. 첫 `<section id="`를 찾아 그 앞에 `    <section id="why"><h2>{esc(title)}</h2>\n{fragment.strip()}\n    </section>\n`을 넣는다. 형식은 assemble과 같다. 섹션이 없으면 `InsertError`를 낸다.
  4. `<nav class="toc" aria-label="목차">` 바로 뒤에 `<a href="#why">{esc(short)}</a>`를 넣는다. 목차가 없으면 `InsertError`를 낸다.
  `main()`은 결과 문자열을 모두 만든 뒤에만 파일에 쓴다.

- [ ] **Step 4: 통과를 확인한다.** Run: `T`. Expected: 기준선 1개를 뺀 전부 PASS.

- [ ] **Step 5: Commit**
```bash
git add .claude/skills/ec2-review-pack/scripts/insert_why.py .claude/skills/ec2-review-pack/tests/test_insert_why.py
git commit -m "feat(ec2-review-pack): add insert_why.py to retrofit why page into existing notes"
```

### Task 3: 스킬 문서 — 새 팩 절차에 why 페이지 반영

**Files:**
- Modify: `.claude/skills/ec2-review-pack/references/manifest-guide.md` (`## sections / topics`, `:19`)
- Modify: `.claude/skills/ec2-review-pack/references/content-rules.md` (`## 페이지 요약` 앞에 새 절)
- Modify: `.claude/skills/ec2-review-pack/references/stt-summary-prompt.md` (출력 형식 6과 7 사이)
- Modify: `.claude/skills/ec2-review-pack/references/review-prompt.md` (확인할 것 7번)
- Modify: `.claude/skills/ec2-review-pack/SKILL.md` (2단계, 3단계, 9단계 뒤 새 `##` 절, 오류 처리 표)
- Test: `.claude/skills/ec2-review-pack/tests/test_skill_files.py`

**Interfaces:**
- Consumes: Task 1 상수 값(문서에 글자 그대로), Task 2 CLI.

- [ ] **Step 1: 실패하는 테스트를 쓴다.** `test_skill_files.py`에 `TestWhyPageDocs`를 추가한다.

```python
class TestWhyPageDocs(unittest.TestCase):
    def read(self, rel): return (SKILL / rel).read_text(encoding="utf-8")
    def test_manifest_guide_fixes_why_section(self):
        t = self.read("references/manifest-guide.md")
        for s in ('"why"', "why-circuit", "들어가며: 왜 이런 회로를 쓸까", "왜 쓸까"): self.assertIn(s, t)
    def test_content_rules_has_why_section(self):
        self.assertIn("## 왜 쓰는가 페이지 (`why-circuit`)", self.read("references/content-rules.md"))
    def test_summary_prompt_collects_motivation(self):
        self.assertIn("## 동기 발언", self.read("references/stt-summary-prompt.md"))
    def test_review_prompt_checks_why(self):
        self.assertIn("why-circuit", self.read("references/review-prompt.md"))
    def test_skill_md_mentions_retrofit(self):
        t = self.read("SKILL.md")
        self.assertIn("scripts/insert_why.py", t); self.assertIn("## 기존 팩에 왜 페이지 붙이기", t)
```

- [ ] **Step 2: 실패를 확인한다.** Run: `T`. Expected: `TestWhyPageDocs` 5개 FAIL.

- [ ] **Step 3: 문서를 고친다.** 내용은 스펙 "Implementation spec 1"을 옮긴다. 문서별 요점:
  - `manifest-guide.md`
    - `:19`를 바꾼다. 첫 섹션은 항상 why이고, 이어서 `s0`, `s1`, … 순서다.
    - why 섹션 JSON 예시(Task 1 픽스처 형태)를 싣는다.
    - why-circuit의 `layers`, `supp`, `required_terms` 3~6개 규칙을 쓴다. 대표 회로 이름, 푸는 문제, 대가를 각각 1개 이상 넣는다.
    - "s0 안에 별도 '왜 필요한가' 토픽을 만들지 않는다"를 쓴다.
  - `content-rules.md`의 새 절 `## 왜 쓰는가 페이지 (`why-circuit`)`
    - formal은 4단계로 쓴다(문제 / 단순 해법과 한계(식 1~2줄) / 핵심 아이디어 한 문장 / 대가와 쓰이는 곳). 각 단계 끝에 `<a href="#토픽id">`를 건다.
    - 유도, `ol.steps`, 소신호 등가회로는 쓰지 않는다.
    - eli5는 비유 1개와 문제→해결 흐름도 SVG(id `fig-why`)로 쓴다.
    - 근거 우선순위는 요약의 `## 동기 발언` > 슬라이드 첫 장 > Razavi 장 도입부이고, 수업 밖 근거는 supp 레이어에 둔다.
    - 위젯은 넣지 않는다.
    - 작성자 브리프에 `<뒤 섹션 토픽 id·제목 목록>` 자리를 추가한다(why 작성자에게만 채운다).
  - `stt-summary-prompt.md`: 출력 형식에 `## 동기 발언`을 추가한다. "왜 이 회로를 쓰는가"에 대한 교수님 발언을 원문 인용 + `(MM:SS)`로 모으고, 없으면 "없음"이라고 쓴다.
  - `review-prompt.md`: 7번 항목을 추가한다. `why-circuit`이 뒤 토픽의 유도를 반복하지 않는지, 링크 대상이 실제 토픽인지, 4단계를 모두 갖췄는지 본다.
  - `SKILL.md`
    - 2단계에 "첫 섹션은 `why`/`why-circuit`(`references/manifest-guide.md`)"을 추가한다.
    - 3단계에 "why 섹션 작성자도 함께 병렬로 띄우고 `<뒤 섹션 토픽 id·제목 목록>`을 채운다"를 추가한다.
    - 9단계 다음에 `## 기존 팩에 왜 페이지 붙이기` 절을 둔다. 내용은 Task 4 절차(백업 → 작성자 → `python3 "$SKILL/scripts/insert_why.py" --note … --fragment …` → `check_html.py` → `html2md.py --check` → 브라우저 검사)다. `### 10.` 같은 번호 헤딩은 쓰지 않는다(`test_steps_present`가 0~9를 본다).
    - 오류 처리 표에 `insert_why.py` 실패 행을 추가한다(파일은 그대로, 조각을 고쳐 다시 실행).

- [ ] **Step 4: 통과를 확인한다.** Run: `T`. Expected: 기준선 1개를 뺀 전부 PASS(`test_referenced_files_exist`가 `scripts/insert_why.py` 존재도 확인한다).

- [ ] **Step 5: Commit**
```bash
git add .claude/skills/ec2-review-pack/SKILL.md .claude/skills/ec2-review-pack/references .claude/skills/ec2-review-pack/tests/test_skill_files.py
git commit -m "docs(ec2-review-pack): add why-circuit page to pack procedure"
```

### Task 4: 기존 10개 팩에 why 페이지 덧붙이기

**Files:**
- Modify: `복습노트/{0902,0904,0909,0911,0916,0918,0923,0930,1002,1007}/정리노트_*.html`과 같은 이름의 `.md`
- Scratch: `<scratchpad>/why-retrofit/<range>/why.html`, `<scratchpad>/why-retrofit/backup/<range>/`

**Interfaces:**
- Consumes: Task 2 CLI, Task 3의 `content-rules.md` "왜 쓰는가 페이지" 절, 기존 `scripts/check_html.py FILE…`, `scripts/html2md.py NOTE --check`.

- [ ] **Step 1: 백업한다.** 각 팩의 `정리노트_*.html`과 `.md`를 `<scratchpad>/why-retrofit/backup/<range>/`에 복사한다. 경로는 `os.listdir` + NFC 비교로 찾는다. Expected: 20개 파일이 복사된다.

- [ ] **Step 2: 작성자 10명을 한 메시지에서 병렬로 띄운다(model: opus).** 브리프에는 다음을 넣는다.
  - 읽을 것: `content-rules.md` 전체(특히 "왜 쓰는가 페이지" 절).
  - 근거:
    - 그 팩의 기존 정리노트 HTML(읽기 전용)
    - 그 날짜의 `STT/<MMDD> 전회2.md`(노트 부제의 날짜들)
    - 노트 `tags`에 나온 `강의노트/2026F_Lec*.pdf`
    - Razavi `교과서/마이크로전자회로/<N>장.pdf` 도입부
  - 링크 대상: 노트 안 `article.topic` id 목록. 메인이 `grep -o 'article class="topic" id="[^"]*"'`로 뽑아서 넘긴다.
  - 대표 회로: 노트의 섹션 제목으로 판단한다. 범위의 회로를 모두 1페이지에 담는다(#10). 0902는 "MOSFET 회로를 왜 쓰는가"로 잡고, 기존 `s0-why`(왜 전자회로를 배울까)를 링크한다. 0904는 "소신호 모델이라는 도구를 왜 쓰는가"로 잡는다.
  - 출력: `<scratchpad>/why-retrofit/<range>/why.html` 한 파일. Task 2의 조각 검증 규칙을 지킨다.
  - 자기 검사: content-rules 브리프의 자기 검사 목록.
  - 보고: 경로와 근거로 쓴 STT 타임스탬프와 교과서 쪽.
  Expected: 10개 조각.

- [ ] **Step 3: 끼워넣는다.** 각 팩에 다음을 실행한다.
  `python3 .claude/skills/ec2-review-pack/scripts/insert_why.py --note <노트> --fragment <scratchpad>/why-retrofit/<range>/why.html`
  Expected: 10번 모두 종료 코드 0. 실패하면 오류를 작성자에게 보내 조각을 고친 뒤 다시 실행한다(최대 2회).

- [ ] **Step 4: 기계 검사를 한다.**
  Run: `python3 .claude/skills/ec2-review-pack/scripts/check_html.py 복습노트/*/정리노트_*.html`. Expected: `OK`.
  각 노트에 `python3 .claude/skills/ec2-review-pack/scripts/html2md.py <노트> --check`를 실행한다. Expected: 10개 모두 `OK`(md가 다시 생성된다).
  `git diff --stat 복습노트`의 바뀐 파일이 html 10개와 md 10개뿐이어야 한다.

- [ ] **Step 5: 브라우저로 검사한다.** `references/browser-check.md` 절차대로 빈 포트에 http.server를 띄운다. 팩마다 다음을 확인한다.
  - "시작하기" 다음 첫 화면이 why 토픽이다.
  - KaTeX 오류가 0개다.
  - 375px에서 가로 스크롤이 없다.
  - 다크모드에서 SVG가 보인다.
  - 오른쪽 패널에 why의 요약이 나온다.
  - 콘솔 오류가 0개다.
  - why 안의 링크를 누르면 해당 토픽으로 이동한다.
  결함이 있으면 Step 3처럼 되돌려 고친다. 끝나면 서버를 종료한다.

- [ ] **Step 6: Commit** (push는 사용자 확인 뒤)
```bash
git add 복습노트/*/정리노트_*.html 복습노트/*/정리노트_*.md
git commit -m "docs(notes): add why-circuit intro page to review packs 0902-1007"
```
