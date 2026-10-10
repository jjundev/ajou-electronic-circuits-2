# EC2 Report Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 설계과제 보고서를 "본문 md → 노션(텍스트만) → 사용자 PDF 내보내기 → 표지 병합" 으로 제출하는 공용 패키지 1개와 스킬 3개를 만든다.

**Architecture:** 루트 패키지 `scripts/ec2_report/` 가 과목정보·경로·검사·노션·표지·병합을 담고, 스킬 3개(`ec2-merge-report`, `ec2-sync-notion`, `ec2-write-design-report`)는 이 패키지의 CLI 를 부르는 절차서다. 노션·Chrome·pypdf 코드는 `../논회실/scripts/lab/` 의 검증된 모듈을 옮겨 온다.

**Tech Stack:** Python 3 표준 라이브러리 + PyYAML 6.0.3 + pypdf 6.14.2 (둘 다 설치됨), Chrome 헤드리스, unittest, Notion API `2026-03-11`.

**Spec:** `docs/superpowers/specs/2026-10-10-ec2-report-skills-design.md`. 모든 경로는 REPO `/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2` 기준. 시작 HEAD `345a88e`. 이식 원본 `LAB=/Users/hyunjun_macbook_pro/Documents/Univ/논회실`.

## Global Constraints

- 학번 `202220953`, 성명 `신현준`, 교수 `권익진 교수님`, 분반 `C024`, 과목 `전자회로2`, 과목코드 `ECE305`, 학부 `전자공학과`, 학기 `2026-2`, 날짜 형식 `%Y.%m.%d` — 코드에 박지 않고 `.claude/과목정보.md` 에서만 읽는다.
- 노션 토큰은 환경변수 `NOTION_TOKEN` 에서만 읽고 어떤 파일·로그·출력에도 쓰지 않는다.
- 노션 페이지는 항상 새로 만든다. 덮어쓰기·삭제 함수를 만들지 않는다.
- 노션 페이지 제목: `전자회로2 설계과제{n} 보고서 v{N}`. 업로드 기록의 kind 는 `"보고서"`.
- 최종본 경로: `설계과제/과제{n}/전자회로2_설계과제{n}_{student_id}_{student_name}.pdf`.
- 보고서 md·표지·최종 PDF 메타데이터에 AI 관련 언급이 없어야 한다 (검사 정규식은 Task 2).
- 보고서 md: 산문 문단은 한 줄, 표는 11열 이하, 열 0 원시 HTML 금지, h5 이상 헤딩 금지.
- 새 스킬은 `.claude/skills/<name>/` 에 두고 `.agents/skills/<name>` 에 상대 심링크(`../../.claude/skills/<name>`)를 건다 (기존 `ec2-review-pack` 과 같은 방식).
- 테스트 실행: `python3 -m unittest discover -s tests/ec2_report -v` (REPO 루트에서).

## Review Focus

1. macOS 다운로드 파일명은 NFD 다 — `find_body` 가 NFC 로 정규화하지 않으면 `설계과제1 보고서` 를 못 찾는다. (Task 4 `test_find_body_nfd_name`)
2. 같은 판본을 두 번 내려받으면 `… v2.pdf` 와 `… v2 (1).pdf` 가 생긴다 — 오류가 아니라 수정시각이 최신인 쪽을 고른다. (Task 4 `test_find_body_duplicate_download_picks_newest`)
3. 보고서 md 첫 줄이 빈 줄이거나 제목 헤딩이 없을 때 — 제목 제거가 본문 첫 대절을 지우면 안 된다. (Task 5 `test_strip_title_only_leading_h1`)
4. 한 줄 안의 `$$x$$` 와 이스케이프된 `\$` — 수식 짝 검사가 오탐하면 업로드가 막힌다. (Task 2 `test_math_single_line_block_and_escaped_dollar`)
5. `NOTION_TOKEN` 이 비었거나 부모 페이지 id 가 `~` 일 때 — 네트워크 호출 전에 고칠 방법을 담은 오류로 멈추고 `notion.json` 을 만들지 않는다. (Task 5 `test_push_without_parent_id_writes_no_record`)

---

### Task 1: 공용 기반 — 패키지·과목정보·config

**Files:**
- Create: `.claude/과목정보.md`
- Create: `scripts/__init__.py`, `scripts/ec2_report/__init__.py` (빈 파일)
- Create: `scripts/ec2_report/config.py`
- Create: `tests/ec2_report/_util.py`, `tests/ec2_report/test_config.py`

**Interfaces:**
- Produces:
  - `find_root(start: Path | None = None) -> Path` — `start`(기본 이 파일 위치)에서 위로 올라가며 `.claude/과목정보.md` 가 있는 첫 디렉토리. 없으면 `FileNotFoundError`.
  - `load_course_info(root: Path) -> dict` — frontmatter 를 `yaml.safe_load`. `REQUIRED = ("department", "course", "course_code", "professor", "class_section", "student_id", "student_name", "date_format", "chrome")` 중 키가 없으면 `ValueError("과목정보.md 에 <key> 가 없습니다")`. `notion_parent_page_id` 기본 `None`.
  - `missing_identity(info: dict) -> list[str]` — `("professor", "class_section", "student_id", "student_name")` 중 값이 비었거나 `None` 인 키, 순서 유지.
  - `assignment_dir(n: int, root: Path) -> Path` — `root/설계과제/과제{n}`, 없으면 `FileNotFoundError`.
  - `document_title(n: int) -> str` — `f"전자회로2 설계과제{n} 보고서"`.
  - `KIND = "보고서"`
  - `@dataclass(frozen=True) ReportPaths`: `report_md`, `notion_dir`, `cover_html`, `cover_pdf`, `final_pdf` (모두 `Path`), 메서드 `baseline(v: int) -> Path` (`notion_dir/f"baseline_v{v}.md"`), `pulled(v: int) -> Path` (`notion_dir/f"pulled_v{v}.md"`).
  - `paths(n: int, root: Path, info: dict) -> ReportPaths` — `report_md = A/report/설계과제{n}_보고서.md`, `notion_dir = A/report/notion`, `cover_html/pdf = A/report/설계과제{n} 표지.html|.pdf`, `final_pdf = A/전자회로2_설계과제{n}_{student_id}_{student_name}.pdf` (`A = assignment_dir(n, root)`).

- [ ] **Step 1: `.claude/과목정보.md` 작성**

frontmatter 값: `department: 전자공학과`, `course: 전자회로2`, `course_code: ECE305`, `professor: 권익진 교수님`, `class_section: C024`, `semester: 2026-2`, `student_id: "202220953"`, `student_name: 신현준`, `date_format: "%Y.%m.%d"`, `chrome:` 목록 2줄(`/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`, `C:\Program Files\Google\Chrome\Application\chrome.exe`), `notion_parent_page_id: ~`. 본문에 "단일 메타데이터 소스, 토큰은 `NOTION_TOKEN` 환경변수(`~/.zshenv`)에만, 부모 페이지에 integration Connect 필요" 세 줄.

- [ ] **Step 2: 실패하는 테스트 작성** (`tests/ec2_report/_util.py` 는 REPO 를 `sys.path` 앞에 넣고 `REPO` 를 export)

```python
class ConfigTests(unittest.TestCase):
    def test_load_real_course_info(self):
        info = config.load_course_info(REPO)
        self.assertEqual(info["student_id"], "202220953")
        self.assertEqual(info["class_section"], "C024")
        self.assertIsInstance(info["chrome"], list)

    def test_missing_required_key_names_it(self):  # tmp root, frontmatter 에서 course_code 삭제
        with self.assertRaisesRegex(ValueError, "course_code"):
            config.load_course_info(tmp_root)

    def test_missing_identity_reports_none_values(self):
        self.assertEqual(config.missing_identity({"professor": "x", "class_section": None,
                         "student_id": "", "student_name": "y"}), ["class_section", "student_id"])

    def test_paths_for_assignment_1(self):
        p = config.paths(1, REPO, config.load_course_info(REPO))
        self.assertEqual(p.final_pdf.name, "전자회로2_설계과제1_202220953_신현준.pdf")
        self.assertEqual(p.report_md.relative_to(REPO).as_posix(), "설계과제/과제1/report/설계과제1_보고서.md")
        self.assertEqual(p.baseline(3).name, "baseline_v3.md")

    def test_assignment_dir_missing(self):
        with self.assertRaises(FileNotFoundError):
            config.assignment_dir(99, REPO)

    def test_document_title(self):
        self.assertEqual(config.document_title(2), "전자회로2 설계과제2 보고서")
```

- [ ] **Step 3: 실패 확인** — `python3 -m unittest discover -s tests/ec2_report -v` → `ModuleNotFoundError: scripts.ec2_report.config`

- [ ] **Step 4: `scripts/ec2_report/config.py` 구현** (frontmatter 는 첫 줄 `---` 부터 다음 `---` 까지)

- [ ] **Step 5: 통과 확인** — 같은 명령, 6 tests OK

- [ ] **Step 6: Commit**

```bash
git add .claude/과목정보.md scripts/__init__.py scripts/ec2_report tests/ec2_report
git commit -m "feat(ec2-report): add course info and shared config"
```

---

### Task 2: 검사기 — check.py

**Files:**
- Create: `scripts/ec2_report/check.py`
- Create: `tests/ec2_report/test_check.py`, `tests/ec2_report/fixtures/probe_roundtrip.md` (논회실 probe 결과의 되읽기 형태: `<table header-row="true">…</table>` 와 ``$`x`$``)

**Interfaces:**
- Produces:
  - `@dataclass(frozen=True) Finding(level: str, where: str, msg: str)`; `level ∈ {"error", "info"}`; `__str__` → `f"{level} {where}: {msg}"`.
  - `check_markdown(path: Path) -> list[Finding]`
  - `shape(text: str) -> dict[str, int]` — 키 `headings`, `tables`, `math_blocks`, `inline_math`, `images`.
  - `roundtrip(src: str, baseline: str) -> list[Finding]` — `shape` 의 각 키에서 baseline 이 src 보다 작으면 error 1건씩 ("표가 5개에서 3개로 줄었다" 형식).
  - `check_pulled_images(text: str) -> list[Finding]` — `![alt](대상)` 의 대상이 비었거나 `http(s)://` 가 아니면 error `f"그림 빈자리: {alt}"`.
  - `AI_WORDS = re.compile(r"Claude|ChatGPT|GPT-\d|Gemini|생성형|LLM|(?<![A-Za-z])AI(?![A-Za-z])")`

규칙 (`check_markdown`, `$$` 블록 안의 줄은 수식 외 규칙에서 제외):
- error: `^#{5,}\s` 헤딩 / 각주 `[^x]` / 열 0 `<태그` / 표 행 셀 수 ≠ 헤더 / 헤더 12열 이상 / 헤딩 안 백틱 / `$$` 단독 줄 개수 홀수 / 한 줄의 이스케이프 안 된 `$` 개수 홀수 (`$$…$$` 한 줄 블록은 짝으로 셈) / `AI_WORDS` 일치 (줄 번호 포함).
- error 1건 요약: 산문 줄 바로 다음 줄도 산문이면 "산문 줄이 N곳에서 접혀 있다". 산문 줄 = 비어 있지 않고 `#`, `|`, `-`, `*`, `>`, `!`, `<`, `$$`, `\d+\.` 로 시작하지 않는 줄.
- info: 로컬 그림 목록 `f"노션에서 직접 넣을 그림 {k}장: a.png, b.png"`.
- `shape`: 헤딩 `^#{1,4}\s`, 표 = 파이프 표 구분행 `^\|[\s:|-]+\|$` 개수 + `<table` 개수, `math_blocks` = 단독 `$$` 줄 수 // 2, `inline_math` = `\$`?[^$\n]+?`?\$` (백틱 변형 허용, `$$` 제외), 그림 `!\[`.

- [ ] **Step 1: 실패하는 테스트 작성** — 규칙마다 tmp md 를 써서 검사

```python
def test_clean_report_has_no_errors(self):   # 대절 #, 표, $$ 블록, 인라인 $g_m$, 그림 1장
    f = check.check_markdown(p); self.assertEqual([x for x in f if x.level == "error"], [])
    self.assertIn("1장", [x for x in f if x.level == "info"][0].msg)
def test_wrapped_prose_is_one_error(self): ...        # 3줄 연속 산문 → error 1건, msg 에 "2곳"
def test_table_cell_mismatch(self): ...
def test_table_12_columns(self): ...
def test_raw_html_col0(self): ...                      # "<div>x</div>"
def test_h5_heading(self): ...
def test_odd_block_math(self): ...                     # $$ 줄 3개
def test_math_single_line_block_and_escaped_dollar(self):  # "$$x$$" 와 "가격 \$5" → error 0
def test_ai_words_blocked(self):                       # "Claude 로 검산" → error, msg 에 줄 번호
def test_ai_inside_word_allowed(self):                 # "MAIN", "RAIL" → error 0
def test_shape_counts_html_tables_and_backtick_math(self):
    s = check.shape(FIXTURE.read_text()); self.assertEqual((s["tables"], s["inline_math"]), (1, 1))
def test_roundtrip_reports_only_losses(self):          # src 표2·수식블록1 vs baseline 표1·블록1 → error 1건 "표"
def test_pulled_images_empty_target(self):             # "![회로도]()" 와 "![x](figs/a.png)" → error 2, https 는 0
```

- [ ] **Step 2: 실패 확인** — `python3 -m unittest discover -s tests/ec2_report -v` → `ModuleNotFoundError: scripts.ec2_report.check`
- [ ] **Step 3: `check.py` 구현** (규칙 출처: `LAB/scripts/lab/validate.py:1057` `_NFM_LOSSY`, `:1130` `check_report_wrapping`, `:1368` `check_notion_markdown`)
- [ ] **Step 4: 통과 확인** — 전체 OK
- [ ] **Step 5: Commit** — `git commit -m "feat(ec2-report): add markdown and roundtrip checks"`

---

### Task 3: 표지 — html2pdf·cover

**Files:**
- Create: `scripts/ec2_report/html2pdf.py` (`LAB/scripts/lab/html2pdf.py` 그대로 복사, 오류 문구의 경로만 `.claude/과목정보.md`)
- Create: `scripts/ec2_report/templates/cover.html` (`LAB/.claude/skills/make-lab-report-cover/template.html` 복사 후: `<dt>조</dt><dd>{{TEAM}}</dd>` 행 삭제, `{{STUDENT_IDS}}`→`{{STUDENT_ID}}`, `{{STUDENT_NAMES}}`→`{{STUDENT_NAME}}`)
- Create: `scripts/ec2_report/cover.py`
- Create: `tests/ec2_report/test_cover.py`

**Interfaces:**
- Consumes: `config.load_course_info`, `config.missing_identity`, `config.paths`, `config.find_root`
- Produces:
  - `PLACEHOLDERS = ("TITLE", "COURSE", "CLASS_SECTION", "DEPARTMENT", "SUBMIT_DATE", "PROFESSOR", "STUDENT_ID", "STUDENT_NAME")`
  - `cover_title(n: int) -> str` → `f"설계과제 {n} 보고서"`
  - `render_cover_html(title: str, info: dict, submit_date: str) -> str` — 치환 후 `{{` 가 남으면 `ValueError`.
  - `make_cover(n: int, submit_date: str | None = None, root: Path | None = None) -> Path` — `missing_identity` 가 비어 있지 않으면 `ValueError("과목정보.md 신원 미확정: …")` (파일 안 만듦). 날짜 기본 `datetime.now().strftime(info["date_format"])`. HTML → `html_to_pdf(..., chrome=info["chrome"])` → 1쪽·A4(가로 205–215mm, 세로 290–302mm) 아니면 `ValueError`. PDF 경로 반환. 실패 시 HTML 은 남긴다.

- [ ] **Step 1: 실패하는 테스트 작성**

```python
def test_render_fills_all_placeholders(self):
    html = cover.render_cover_html("설계과제 1 보고서", INFO, "2026.10.30")
    self.assertNotIn("{{", html); self.assertIn("202220953", html); self.assertIn("C024", html)
    self.assertNotIn("조</dt>", html); self.assertIn("윤리", html)
def test_missing_identity_blocks_cover(self):   # info student_id=None → ValueError, cover_pdf 없음
@unittest.skipUnless(chrome_available(), "Chrome 없음")
def test_make_cover_is_one_a4_page(self):       # tmp root 에 과목정보 + 설계과제/과제1 → pypdf 1쪽, 210±5 x 297±5
```

- [ ] **Step 2: 실패 확인** → `ModuleNotFoundError`
- [ ] **Step 3: 구현** (html2pdf 복사, 템플릿 수정, cover.py)
- [ ] **Step 4: 통과 확인** — 전체 OK (Chrome 있으면 skip 0)
- [ ] **Step 5: Commit** — `git commit -m "feat(ec2-report): add cover generation"`

---

### Task 4: 병합 — merge.py + `ec2-merge-report` 스킬

**Files:**
- Create: `scripts/ec2_report/merge.py`
- Create: `tests/ec2_report/test_merge.py`
- Create: `.claude/skills/ec2-merge-report/SKILL.md`, 심링크 `.agents/skills/ec2-merge-report`

**Interfaces:**
- Consumes: `config.*`, `cover.make_cover(n, submit_date, root) -> Path`
- Produces:
  - `@dataclass BodySource(path: Path, origin: Path)` — zip 이면 `path` 는 임시 해제본, `origin` 은 zip.
  - `find_body(n: int, root: Path, search_dirs: list[Path] | None = None) -> BodySource` — 기본 `[paths.report_md.parent, Path.home()/"Downloads"]`. 파일명을 NFC 정규화해 `f"설계과제{n} 보고서"` 포함 + 확장자 `.pdf`/`.zip`. 표지·최종본 파일명 제외. 버전 `v(\d+)` (없으면 0) 최댓값 → 동률이면 수정시각 최신. 0개 `FileNotFoundError`(찾은 폴더 나열). zip 안 PDF 가 1개가 아니면 `ValueError`.
  - `verify_merged(pdf: Path, expected_pages: int) -> dict` — 키 `pages`, `page1_mm`; 쪽수 불일치·1쪽 비 A4 면 `ValueError`.
  - `merge(n: int, body: Path | None = None, date: str | None = None, keep_body: bool = False, root: Path | None = None) -> dict` — 키 `output`, `pages`, `cover`, `body_origin`, `deleted`. 순서: 본문 확정 → `make_cover` (매번 새로 생성) → `pypdf.PdfWriter.append` 표지·본문 → 메타데이터를 `{"/Title": document_title(n), "/Author": student_name}` 만 남김 → `verify_merged(out, 1 + 본문쪽수)` → 통과하고 `keep_body` 가 거짓이며 `origin != output` 이면 `origin` 삭제(실패 시 stderr `경고: 본문 원본을 지우지 못했습니다`, `deleted=False`).
  - CLI `main(argv: list[str] | None = None) -> int`: `python3 -m scripts.ec2_report.merge --n 1 [--body P] [--date 2026.10.30] [--keep-body]` → 성공 시 최종 경로·쪽수 출력, 0 반환.

- [ ] **Step 1: 실패하는 테스트 작성** (pypdf `PdfWriter.add_blank_page(595, 842)` 로 합성 본문, `cover.make_cover` 는 `unittest.mock.patch` 로 1쪽 A4 합성 PDF 반환)

```python
def test_find_body_picks_highest_version(self):        # v1.pdf, v2.pdf → v2
def test_find_body_nfd_name(self):                      # unicodedata.normalize("NFD", "…설계과제1 보고서 v1.pdf") → 찾음
def test_find_body_duplicate_download_picks_newest(self):  # "v2.pdf" 과거 mtime, "v2 (1).pdf" 최신 → (1)
def test_find_body_ignores_problem_pdf_and_final(self): # "2026-2_전자회로2_설계과제1_v3.pdf", 최종본 → FileNotFoundError
def test_find_body_zip_single_pdf(self):                # zip 안 pdf 1개 → path.suffix==".pdf", origin.suffix==".zip"
def test_find_body_zip_two_pdfs_rejected(self):
def test_merge_pages_metadata_and_delete(self):         # 본문 3쪽 → pages 4, deleted True, 원본 없음,
    meta = PdfReader(out).metadata                       # meta.title == "전자회로2 설계과제1 보고서", producer 에 AI_WORDS 없음
def test_merge_keep_body(self):                          # keep_body=True → 원본 존재, deleted False
def test_verify_rejects_page_mismatch(self):
```

- [ ] **Step 2: 실패 확인** → `ModuleNotFoundError: scripts.ec2_report.merge`
- [ ] **Step 3: `merge.py` 구현** (병합·검증 골격은 `LAB/scripts/lab/merge_report.py:171-219`)
- [ ] **Step 4: 통과 확인** — 전체 OK
- [ ] **Step 5: `SKILL.md` 작성** — frontmatter `name: ec2-merge-report`, description 은 "전자회로2 설계과제 보고서 본문 PDF(노션 내보내기)에 IEEE 윤리강령 표지를 붙여 BB 제출본을 만든다. '과제1 표지랑 합쳐줘', '제출본 만들어줘', '설계과제 표지만 만들어줘', /ec2-merge-report <n> [--date …]" 를 담는다. 절차: ① 과제 번호 확정 ② `missing_identity` 게이트 ③ (표지만이면 `python3 -c "from scripts.ec2_report.cover import make_cover; print(make_cover(<n>))"` 후 종료) ④ `python3 -m scripts.ec2_report.merge --n <n>` ⑤ 출력의 최종 경로·쪽수를 마크다운 링크로 안내. 비-목표: 노션 API 로 PDF 받기, 본문 재압축.
- [ ] **Step 6: 심링크와 수동 확인**

```bash
ln -s ../../.claude/skills/ec2-merge-report .agents/skills/ec2-merge-report
python3 -c "from scripts.ec2_report.cover import make_cover; print(make_cover(1))"
```
Expected: `설계과제/과제1/report/설계과제1 표지.pdf` 경로 출력, 열어서 윤리강령·학번·이름·C024 확인.

- [ ] **Step 7: Commit** — `git add scripts/ec2_report/merge.py tests/ec2_report/test_merge.py .claude/skills/ec2-merge-report .agents/skills/ec2-merge-report && git commit -m "feat(ec2-report): add merge pipeline and ec2-merge-report skill"`

---

### Task 5: 노션 클라이언트와 sync 모듈

**Files:**
- Create: `scripts/ec2_report/notion.py` (`LAB/scripts/lab/notion.py` 복사. 바꾸는 것: 부모 id 오류 문구의 경로 `.claude/과목정보.md`)
- Create: `scripts/ec2_report/sync.py`
- Create: `tests/ec2_report/test_notion.py`, `tests/ec2_report/test_sync.py`

**Interfaces:**
- Consumes: `config.*`, `check.check_markdown`, `check.roundtrip`, `check.check_pulled_images`, `check.Finding`
- Produces (notion.py, 원본과 동일 시그니처): `load_token() -> str`, `push_markdown(md_text, parent_page_id, token, title=None, timeout=120) -> dict{page_id,url}`, `pull_markdown(page_id, token, timeout=120) -> str`, `next_version(output_dir, kind) -> int`, `append_record(output_dir, kind, page_id, url, source, when) -> dict`, `load_records(output_dir) -> list`, `NotionError`.
- Produces (sync.py):
  - `class SyncBlocked(Exception)` — `.findings: list[Finding]`
  - `strip_title(text: str, title: str) -> str` — 앞쪽 빈 줄을 건너뛴 첫 줄이 `# ` 헤딩이면 그 줄(과 뒤따르는 빈 줄)만 제거. 아니면 원문 그대로.
  - `push(n: int, root: Path | None = None, token: str | None = None, now: str | None = None) -> dict` — 키 `title`, `version`, `url`, `page_id`, `baseline`, `info`, `roundtrip`. 순서: `check_markdown` error 있으면 `SyncBlocked` → `parent = info["notion_parent_page_id"]` 없으면 `NotionError` (토큰보다 먼저 확인) → `token or load_token()` → 제목 `f"{document_title(n)} v{next_version(notion_dir, KIND)}"` → `push_markdown(strip_title(...), …, title=…)` → `append_record(notion_dir, KIND, …, source=report_md.name, when=now or 현재 "%Y-%m-%d %H:%M")` → `baseline(v)` 에 `pull_markdown` 저장 → `roundtrip(원문, baseline)`.
  - `recover_baselines(n: int, root=None, token=None) -> list[Path]` — 기록은 있는데 baseline 이 없는 버전만 재-pull (논회실 sync 4b-A).
  - `check_images(n: int, root=None, token=None) -> list[Finding]` — 최신 기록 → `pull_markdown` → `pulled(v)` 저장 → `check_pulled_images`.
  - CLI `main(argv) -> int`: `python3 -m scripts.ec2_report.sync push --n 1` / `check-images --n 1` / `recover --n 1`. `SyncBlocked` 면 finding 을 줄마다 출력하고 2 반환, `NotionError` 면 메시지 출력 후 3 반환.

- [ ] **Step 1: 실패하는 테스트 작성** (`notion._request` 를 mock — 실제 네트워크 호출 금지)

```python
# test_notion.py
def test_load_token_missing_mentions_zshenv(self):     # env 비움 → NotionError, msg 에 "~/.zshenv"
def test_push_markdown_sends_title_property(self):      # mock 이 받은 payload["properties"]["title"][0]["text"]["content"] == "T v1"
def test_pull_truncated_raises(self):                   # {"truncated": True, "markdown": "x"} → NotionError
def test_pull_strips_presigned_query(self):             # "…/a.png?X-Amz-Signature=abc" → "…/a.png"
def test_versions_count_per_kind(self):                 # append 2회 → next_version == 3, notion.json schema "notion-uploads/v1"
# test_sync.py  (tmp root: 과목정보 + 과제1/report/설계과제1_보고서.md)
def test_strip_title_only_leading_h1(self):             # "\n\n# 제목\n\n# 1. Design\n" → "# 1. Design\n"; 제목 없는 문서는 그대로
def test_push_blocked_on_errors(self):                  # 본문에 "Claude" → SyncBlocked, mock _request 호출 0회
def test_push_without_parent_id_writes_no_record(self): # parent ~ → NotionError, notion.json 없음, _request 0회
def test_push_happy_path(self):                         # mock: POST → {"id":"p1","url":"u"}, GET → {"markdown": 같은 본문}
    r = sync.push(1, root, token="t", now="2026-10-10 12:00")
    self.assertEqual((r["version"], r["title"]), (1, "전자회로2 설계과제1 보고서 v1"))
    self.assertTrue(r["baseline"].exists()); self.assertEqual(r["roundtrip"], [])
def test_recover_baselines_repulls_missing_only(self):
def test_check_images_flags_empty(self):                # GET → "![회로도]()" → error 1건, pulled_v1.md 저장
```

- [ ] **Step 2: 실패 확인** → `ModuleNotFoundError`
- [ ] **Step 3: notion.py 복사·수정, sync.py 구현**
- [ ] **Step 4: 통과 확인** — 전체 OK
- [ ] **Step 5: Commit** — `git commit -m "feat(ec2-report): add notion client and sync module"`

---

### Task 6: 노션 프로브 + `ec2-sync-notion` 스킬

**선행 조건:** 사용자가 노션에 전자회로2 페이지를 만들고 integration 을 Connect 한 뒤 페이지 id 를 준다. 받으면 `.claude/과목정보.md` 의 `notion_parent_page_id` 에 적는다. 없으면 이 Task 에서 멈추고 요청한다.

**Files:**
- Modify: `.claude/과목정보.md` (`notion_parent_page_id`)
- Create: `docs/notion-probe.md`
- Modify: `tests/ec2_report/fixtures/probe_roundtrip.md` (실측 되읽기로 교체), `tests/ec2_report/test_check.py` (블록 수식 실측 형태 테스트 추가)
- Modify (실측에 따라서만): `scripts/ec2_report/check.py` `shape()`
- Create: `.claude/skills/ec2-sync-notion/SKILL.md`, 심링크 `.agents/skills/ec2-sync-notion`

- [ ] **Step 1: 프로브 업로드** — 프로브 md (제목 `전자회로2 노션 프로브`) 를 `notion.push_markdown` 으로 올리고 `pull_markdown` 으로 되읽는다. 내용: 단독 줄 `$$`/`A_v = g_m R_{out}`/`$$` 블록, 표 셀 안 `$\lvert V_{DS}\rvert$`, `**(a) 굵은 문단**`, `▶ 풀이 문단`, `![그림](figs/a.png)`.

Expected: 페이지 URL 에 제목 슬러그 존재, 되읽기 문자열 확보.

- [ ] **Step 2: `docs/notion-probe.md` 기록** — 항목별 "올린 것 / 되읽은 것 / 노션 화면 렌더(사용자 확인)" 표. 블록 수식의 되읽기 형태를 그대로 적는다.
- [ ] **Step 3: fixture 교체와 테스트 추가** — `test_shape_counts_probe_block_math`: 실측 되읽기에서 `math_blocks == 1`, `inline_math == 1`, `tables == 1`.
- [ ] **Step 4: 실패 확인 → `shape()` 를 실측 형태에 맞게 수정 → 통과 확인** (이미 통과하면 수정하지 않는다). 블록 수식이 노션에서 렌더되지 않으면 사용자에게 알리고 Task 7 양식 규칙을 "블록 수식 대신 인라인 수식 단독 문단" 으로 바꾼다.
- [ ] **Step 5: `SKILL.md` 작성** — frontmatter `name: ec2-sync-notion`, description: "전자회로2 설계과제 보고서 md 를 노션에 새 페이지로 올리고(텍스트만), 그림 빈자리를 확인한다. '과제1 노션에 올려줘', '그림 다 넣었어 확인해줘', /ec2-sync-notion <n> [check-images]". 절대 규칙: 덮어쓰기 금지, 토큰 비노출, 그림 자동 업로드 금지. push 절차: `python3 -m scripts.ec2_report.sync push --n <n>` → 종료 코드 2 면 finding 보고 후 멈춤 → 성공 시 URL·버전·그림 목록·왕복 결과 안내, "그림 넣고 '확인해줘'" 요청. 중간 실패 복구: baseline 만 없으면 `recover`, 기록 없이 페이지만 생겼을 수 있으면 재업로드하지 말고 부모 페이지 id 를 알려 사용자 판단을 받는다 (`LAB/.claude/skills/sync-report-to-notion/SKILL.md` 4b). check-images 절차: `… sync check-images --n <n>` → ✗ 있으면 목록 안내하고 멈춤, 없으면 "노션에서 ⋯ → Export → PDF(A4) 후 ec2-merge-report" 안내.
- [ ] **Step 6: 심링크** — `ln -s ../../.claude/skills/ec2-sync-notion .agents/skills/ec2-sync-notion`
- [ ] **Step 7: Commit** — `git add .claude/과목정보.md docs/notion-probe.md tests/ec2_report scripts/ec2_report/check.py .claude/skills/ec2-sync-notion .agents/skills/ec2-sync-notion && git commit -m "feat(ec2-report): probe notion math and add ec2-sync-notion skill"`

---

### Task 7: `ec2-write-design-report` 스킬 + 설계과제1 본문 재작성

**Files:**
- Create: `.claude/skills/ec2-write-design-report/SKILL.md`, `references/양식.md`, `references/감점체크리스트.md`, 심링크 `.agents/skills/ec2-write-design-report`
- Modify: `설계과제/과제1/sim/diffamp.cir` (AC 에 위상 저장), `설계과제/과제1/sim/post.py` (`figs/ac_bode.png` 크기·위상 2단 생성)
- Modify: `설계과제/과제1/report/설계과제1_보고서.md` (새 양식으로 전면 재작성)
- Create: `설계과제/과제1/report/LTspice_작성메모.md` (기존 본문의 부록 A 이동)

**Interfaces:**
- Consumes: `check.check_markdown` (`python3 -c "from scripts.ec2_report.check import check_markdown; [print(f) for f in check_markdown('<md>')]"`)

- [ ] **Step 1: `references/양식.md` 작성** — spec §보고서 양식을 규칙 목록으로: 제목 줄 `# 설계 과제 N: <회로>` (업로드 때 떼어짐), 문제 조건 + `![그림 1](../figures/…)`, 대절 `# 1. Design Problem (설계과정 필수)` / `# 2. Spice Problem`, 소문항은 `**(a) <문제 문장 원문>**` 다음 줄 `▶ …`, W 계산식 표(열: MOSFET·식(숫자 대입)·W/L·W), 요약 표, saturation 부등식 표, 2)-(a) 회로도 그림 자리 `![LTspice 회로도 (.op 라벨, 학번·이름 표기)](figs/schematic.png)`, (d) 오차 % 와 번호 원인. 서식: 산문 한 줄, 표 11열 이하, 헤딩 `#` 만, 신호·수식에 백틱 금지, AI 관련 언급 금지.
- [ ] **Step 2: `references/감점체크리스트.md` 작성** — 각 항목을 "본문에서 찾을 것" 으로: Gm 정확식이 1-(a) 에 유도됨 / 주파수 응답 크기·위상 그림 존재 / 모든 MOSFET saturation 부등식 / 전력 계산 / 오차 % 와 10% 판정 / 회로도에 노드 전압·전류 라벨 / 손계산 표와 SPICE 표가 같은 MOSFET 순서.
- [ ] **Step 3: `SKILL.md` 작성** — name `ec2-write-design-report`, description: "전자회로2 설계과제 보고서 본문 md 를 선배 제출 양식과 감점 이력에 맞춰 쓴다. '설계과제1 보고서 써줘', '보고서 양식대로 다시 써', /ec2-write-design-report <n>". 절차: ① `설계과제/과제<n>/설계과제<n>.md` 와 `sim/` 산출물(op.txt, 그림) 읽기 ② 양식.md 대로 작성 ③ `check_markdown` error 0 ④ 감점체크리스트 항목별 ✔ 표 출력 ⑤ "ec2-sync-notion 으로 올린다" 안내. 비-목표: 시뮬레이션 수치 지어내기(모든 수치는 sim 산출물에서), PDF 생성.
- [ ] **Step 4: Bode 그림 추가** — `diffamp.cir` 의 `wrdata ac.txt av` 를 `wrdata ac.txt av ph` 로 (`let ph = 180/pi*cph(v(op)-v(on))`), `post.py` 가 `figs/ac_bode.png` 를 만든다. 실행: `cd 설계과제/과제1/sim && ngspice -b diffamp.cir && python3 post.py` → Expected: `av_1k = 1.51247e+02` 유지, `report/figs/ac_bode.png` 생성.
- [ ] **Step 5: 본문 재작성** — 스킬 절차대로 `설계과제1_보고서.md` 를 새 양식으로. 수치는 기존 본문·`sim/op.txt` 값 그대로(이득 150.1/151.2, 오차 +0.8 %, P 0.4503 mW, Vb1 0.5966 V, W 65.48/8.53/17.56/16.22/16.07 µm). Gm 정확식 `G_m = g_{m1} r_{o1}(g_{m3}+g_{ds3}) / (1 + r_{o1}(g_{m3}+g_{ds3}))` 을 1-(a) 로 옮긴다. 부록 A 는 `LTspice_작성메모.md` 로.
- [ ] **Step 6: 검사** — `python3 -c "from scripts.ec2_report.check import check_markdown; [print(f) for f in check_markdown('설계과제/과제1/report/설계과제1_보고서.md')]"` → Expected: error 0, info 1줄(그림 4장: 그림1·회로도·tran·bode)
- [ ] **Step 7: 심링크 + Commit**

```bash
ln -s ../../.claude/skills/ec2-write-design-report .agents/skills/ec2-write-design-report
git add .claude/skills/ec2-write-design-report .agents/skills/ec2-write-design-report 설계과제/과제1/sim 설계과제/과제1/report
git commit -m "feat(ec2-report): add ec2-write-design-report skill and rewrite assignment 1 report"
```

---

## 실행 후 사용자 흐름 (검증 시나리오)

1. "과제1 노션에 올려줘" → `ec2-sync-notion` push → v1 URL, 그림 4장 목록
2. 노션에서 그림 4장 첨부 → "확인해줘" → check-images ✗ 0
3. 노션 `Export → PDF (A4)` → "과제1 표지랑 합쳐줘" → `ec2-merge-report` → `설계과제/과제1/전자회로2_설계과제1_202220953_신현준.pdf`, 표지 1 + 본문 N 쪽
