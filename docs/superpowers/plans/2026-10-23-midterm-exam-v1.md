# 중간고사 실전 대비 모의고사(v1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 아주대 전자회로2 기출문제 출제 방식을 철저히 반영하여, 100점 만점 기준의 실전 중간고사 예상 문제 패키지(`중간고사대비/v1/`)에 16:9 와이드스크린 문제지/답안지 PDF와 7구역 대화형 문제해설 HTML을 구축합니다.

**Architecture:** Razavi 교과서 장말문제 및 기출 연계 문항을 바탕으로 5개 문항(100점 만점)의 문제 md와 고화질 SVG 회로도를 저작하고, SymPy 독립 검산 스크립트로 수치 정합성을 증명합니다. 이후 `workbook/build_workbook.py` 및 Playwright 엔진으로 16:9 와이드스크린 PDF(문제/답안)를 렌더링하고, `ec2-problem-explain` 일곱 구역 표준을 적용한 반응형 해설 HTML을 조립합니다.

**Tech Stack:** Python 3.10+, Playwright, KaTeX, Pretendard, SVG, SymPy, Pytest

**Spec:** `docs/superpowers/specs/2026-10-23-midterm-exam-v1-spec.md`

## Global Constraints

- **시험 범위**: 9장(캐스코드/전류거울), 10장(차동증폭기), 11장 전반부(밀러정리/고주파소신호모델) [STT/1016 전회2.md:5,315].
- **배점 체계**: 5문항 각 20점 균등 배점 (총 100점 만점). Q1은 20점 서술형 고정.
- **계산 및 근사 규칙**: 독립 식은 한 행에 하나의 식 display 블록 원칙, $g_m r_o \gg 1, g_m R_S \gg 1$ 근사 주항 보존, 전압 이득 전개는 $G_m \to R_{out} \to A_v = -G_m R_{out}$ 표준 준수.
- **PDF 판형**: 16:9 와이드스크린 (`1920×1080`, `workbook/templates/video-16x9.css` 적용).
- **회로도 규격**: NOTATION-01, CIRCUIT-02 준수 (Pretendard 폰트, 첨자 tspan 78%, 입력 좌측/출력 우측, 좌향 유입 $i_t$).

## Review Focus

1. **소자 수치 및 이득 계산 오차**: 트랜지스터 바이어스 전류, $g_m, r_o, R_{out}, A_v$의 유효숫자 및 대수 계산이 SymPy 독립 검증 결과와 100% 일치해야 함.
2. **$A_v = -G_m R_{out}$ 부호 및 위상 반전**: 모든 증폭기 해석에서 단락 트랜스컨덕턴스 $G_m$ 방향과 부호 있는 이득 정의가 정확해야 함.
3. **16:9 와이드스크린 PDF 페이지 넘침(OVERFLOW)**: 문제지와 답안지 렌더링 시 문항별 박스가 규격 높이(1080px)를 초과하여 다음 페이지로 잘리거나 텍스트가 겹치지 않아야 함.
4. **SVG 회로도 글리프 클리핑 및 전압-노드 색상 일치**: viewBox 상단 여백 부족으로 라벨($V_{out}$ 등)이 잘리거나 노드 점과 전압 라벨의 색상이 불일치하지 않아야 함.
5. **문제해설 HTML 7구역 무결성**: 5개 문항 전부에 걸쳐 일곱 구역(understand, recall, start, solve, verify, pitfall, retry)이 누락 없이 렌더링되어야 함.

---

### Task 1: 스캐폴딩 및 메타데이터 구축

**Files:**
- Create: `중간고사대비/v1/README.md`
- Create: `중간고사대비/v1/.assets/display-titles.json`
- Create: `중간고사대비/v1/.assets/selection.json`
- Test: `tests/test_midterm_v1_scaffold.py`

**Interfaces:**
- Consumes: 없음
- Produces: `중간고사대비/v1/` 디렉터리 트리, 문항 ID 매핑(`MIDTERM-V1-Q1` ~ `Q5`) 및 표시 제목, 배점 메타데이터

- [ ] **Step 1: Write the failing test**

```python
# tests/test_midterm_v1_scaffold.py
import json
from pathlib import Path

def test_midterm_v1_scaffold_structure():
    base = Path("중간고사대비/v1")
    assert base.is_dir()
    assert (base / "README.md").is_file()
    assert (base / ".assets/display-titles.json").is_file()
    assert (base / ".assets/selection.json").is_file()

    titles = json.loads((base / ".assets/display-titles.json").read_text(encoding="utf-8"))
    assert len(titles) == 5
    for i in range(1, 6):
        assert f"MIDTERM-V1-Q{i}" in titles

    selection = json.loads((base / ".assets/selection.json").read_text(encoding="utf-8"))
    assert selection["total_score"] == 100
    assert len(selection["problems"]) == 5
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_midterm_v1_scaffold.py -v`
Expected: FAIL with FileNotFoundError or AssertionError

- [ ] **Step 3: Implement scaffolding and metadata**

`중간고사대비/v1/README.md`에 모의고사 개요 및 시험 규칙(Closed-book, 75분, 풀이과정 필수) 작성.
`중간고사대비/v1/.assets/display-titles.json`에 문항별 간결한 제목 정의:
- `MIDTERM-V1-Q1`: "서술형: 전압 바이어스 한계, 차동쌍 CM 제거, Miller 효과"
- `MIDTERM-V1-Q2`: "축퇴 저항 전류 거울 복사비 설계 및 복합 바이어스 CE 단"
- `MIDTERM-V1-Q3`: "기생 저항 Rp 캐스코드 및 Folded Cascode 증폭기"
- `MIDTERM-V1-Q4`: "소스 축퇴 차동쌍 반회로 해석 및 능동 전류 거울 부하 차동쌍"
- `MIDTERM-V1-Q5`: "부하 저항 불일치 ΔRD 차동 증폭기의 Vin,CM 범위, ACM-DM, CMRR"
`중간고사대비/v1/.assets/selection.json`에 5개 문항 배점(각 20점) 및 단원 태그 작성.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_midterm_v1_scaffold.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add 중간고사대비/v1/README.md 중간고사대비/v1/.assets/*.json tests/test_midterm_v1_scaffold.py
git commit -m "feat(midterm): scaffold midterm v1 directories and metadata"
```

---

### Task 2: 5개 문항 마크다운 저작 (`Q1.md` ~ `Q5.md`)

**Files:**
- Create: `중간고사대비/v1/.assets/md/Q1.md`
- Create: `중간고사대비/v1/.assets/md/Q2.md`
- Create: `중간고사대비/v1/.assets/md/Q3.md`
- Create: `중간고사대비/v1/.assets/md/Q4.md`
- Create: `중간고사대비/v1/.assets/md/Q5.md`
- Test: `tests/test_midterm_v1_md.py`

**Interfaces:**
- Consumes: Task 1의 문항 메타데이터 및 배점 규칙
- Produces: `Q1.md` ~ `Q5.md` 원문, 조건, 배점, 수치 파라미터, 표준 풀이(`## 풀이`) 마크다운

- [ ] **Step 1: Write the failing test**

```python
# tests/test_midterm_v1_md.py
from pathlib import Path
import re

def test_midterm_v1_md_files_exist_and_valid():
    md_dir = Path("중간고사대비/v1/.assets/md")
    for i in range(1, 6):
        path = md_dir / f"Q{i}.md"
        assert path.is_file(), f"Q{i}.md missing"
        text = path.read_text(encoding="utf-8")
        assert "## 문제" in text
        assert "## 풀이" in text
        assert "20점" in text or "배점: 20" in text or "20" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_midterm_v1_md.py -v`
Expected: FAIL with missing md files

- [ ] **Step 3: Implement 5 problem markdown files**

- `Q1.md`: 서술형 3문항 (a) 전압 바이어스 문제점 및 전류 거울의 온도/공정 독립성 (7점), (b) 차동쌍 공통모드 제거 원리와 2가지 제한 요인 (7점), (c) 밀러 정리 및 피드백 $C_F$에 의한 대역폭 감소 원리 (6점).
- `Q2.md`: (a) MOS 전류 거울에서 $I_{REF}=1\text{mA}$로부터 $I_{out}=0.5\text{mA}$ 설계를 위한 $R_S$ 및 $R_{out}$ (10점), (b) BJT 복합 전류 거울 바이어스 CE 증폭기의 바이어스 전류 및 소신호 $A_v$ 계산 (10점).
- `Q3.md`: (a) $M_2$ 양단 기생 저항 $R_P$가 연결된 MOS 캐스코드 증폭기 $R_{out}$ 및 $A_v$ (10점), (b) PMOS 입력 + NMOS 캐스코드 구조의 Folded Cascode $G_m, R_{out}, A_v$ (10점).
- `Q4.md`: (a) 소스 축퇴 $R_{SS}$가 있는 MOS 차동쌍의 반회로 모델링 및 차동 이득 $A_d$ 계산 (10점), (b) 능동 전류 거울 부하 차동 증폭기의 신호 합성, $G_m, R_{out}, A_v$ 계산 (10점).
- `Q5.md`: 부하 불일치 $\Delta R_D$와 테일 저항 $R_{SS}$가 있는 차동 증폭기의 (1) $V_{in,CM}$ 범위, (2) $A_d, A_{CM}$, (3) $A_{CM-DM}$, (4) CMRR 수치 계산 (20점).

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_midterm_v1_md.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add 중간고사대비/v1/.assets/md/*.md tests/test_midterm_v1_md.py
git commit -m "feat(midterm): draft 5 exam problems markdown with detailed solutions"
```

---

### Task 3: SymPy 독립 검산 스크립트 작성 및 수학적 정합성 검증

**Files:**
- Create: `중간고사대비/v1/.assets/evidence/Q2-sympy.py`
- Create: `중간고사대비/v1/.assets/evidence/Q3-sympy.py`
- Create: `중간고사대비/v1/.assets/evidence/Q4-sympy.py`
- Create: `중간고사대비/v1/.assets/evidence/Q5-sympy.py`
- Create: `tests/test_midterm_v1_math.py`

**Interfaces:**
- Consumes: Task 2의 소자 수치 조건 및 대수 수식
- Produces: `.assets/evidence/Q*-result.txt` 검산 증빙, 기호식/수치 계산 자동 테스트 PASS

- [ ] **Step 1: Write the failing test**

```python
# tests/test_midterm_v1_math.py
import subprocess
import sys
from pathlib import Path

def test_sympy_verifications():
    ev_dir = Path("중간고사대비/v1/.assets/evidence")
    for i in range(2, 6):
        script = ev_dir / f"Q{i}-sympy.py"
        assert script.is_file(), f"Missing {script}"
        res = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
        assert res.returncode == 0, f"Q{i}-sympy.py failed: {res.stderr}"
        assert "VERIFIED: PASS" in res.stdout
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_midterm_v1_math.py -v`
Expected: FAIL with missing scripts

- [ ] **Step 3: Implement SymPy verification scripts**

`Q2-sympy.py` ~ `Q5-sympy.py` 작성:
- SymPy 기호 연산으로 소신호 파라미터($g_m, r_o$), 노드 방정식 KCL/KVL, 근사식 오차 비교($g_m r_o \gg 1$), 최종 수치 계산 수행.
- 스크립트 실행 시 결과를 `Q*-result.txt`에 저장하고 표준 출력에 "VERIFIED: PASS" 출력.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_midterm_v1_math.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add 중간고사대비/v1/.assets/evidence/ tests/test_midterm_v1_math.py
git commit -m "feat(midterm): add SymPy independent verification scripts and proof"
```

---

### Task 4: 회로도 SVG 저작 (`fig-Q2.svg` ~ `fig-Q5.svg`)

**Files:**
- Create: `중간고사대비/v1/.assets/figures/fig-Q2a.svg`
- Create: `중간고사대비/v1/.assets/figures/fig-Q2b.svg`
- Create: `중간고사대비/v1/.assets/figures/fig-Q3a.svg`
- Create: `중간고사대비/v1/.assets/figures/fig-Q3b.svg`
- Create: `중간고사대비/v1/.assets/figures/fig-Q4a.svg`
- Create: `중간고사대비/v1/.assets/figures/fig-Q4b.svg`
- Create: `중간고사대비/v1/.assets/figures/fig-Q5.svg`
- Test: `tests/test_midterm_v1_figures.py`

**Interfaces:**
- Consumes: Task 2 회로 토폴로지 및 소자 기호
- Produces: 고화질 표준 SVG 파일 (Pretendard 글꼴, 첨자 tspan, 입력 좌/출력 우 배치)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_midterm_v1_figures.py
from pathlib import Path
import xml.etree.ElementTree as ET

def test_midterm_v1_svg_standards():
    fig_dir = Path("중간고사대비/v1/.assets/figures")
    svgs = list(fig_dir.glob("*.svg"))
    assert len(svgs) >= 5
    for svg in svgs:
        tree = ET.parse(svg)
        root = tree.getroot()
        assert "viewBox" in root.attrib or ("width" in root.attrib and "height" in root.attrib)
        text = svg.read_text(encoding="utf-8")
        assert "font-family" in text or "Pretendard" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_midterm_v1_figures.py -v`
Expected: FAIL with missing svg files

- [ ] **Step 3: Implement standard SVG circuit figures**

- `fig-Q2a.svg`: 소스 축퇴 저항 $R_S$가 달린 NMOS 전류 거울 회로도.
- `fig-Q2b.svg`: NPN/PNP 복합 바이어스 CE 증폭기 회로도.
- `fig-Q3a.svg`: 기생 저항 $R_P$가 연결된 MOS 캐스코드 회로도.
- `fig-Q3b.svg`: PMOS 입력 Folded Cascode 회로도.
- `fig-Q4a.svg`: 소스 축퇴 저항 $R_{SS}$ 차동 증폭기 및 반회로 등가 회로도.
- `fig-Q4b.svg`: 능동 전류 거울 부하 차동 증폭기 회로도.
- `fig-Q5.svg`: 부하 불일치 $\Delta R_D$ 차동 증폭기 회로도.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_midterm_v1_figures.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add 중간고사대비/v1/.assets/figures/*.svg tests/test_midterm_v1_figures.py
git commit -m "feat(midterm): create standard SVG circuit diagrams for exam questions"
```

---

### Task 5: 16:9 와이드스크린 문제지/답안지 PDF 렌더링

**Files:**
- Create: `중간고사대비/v1/build_exam_pdf.py` (또는 `workbook/build_workbook.py` 래퍼)
- Create: `중간고사대비/v1/중간고사대비_v1-문제.pdf`
- Create: `중간고사대비/v1/중간고사대비_v1-답안.pdf`
- Test: `tests/test_midterm_v1_pdf.py`

**Interfaces:**
- Consumes: Task 1, 2, 4의 md, json, svg
- Produces: 16:9 규격 인쇄/필기용 PDF 문서 2종

- [ ] **Step 1: Write the failing test**

```python
# tests/test_midterm_v1_pdf.py
from pathlib import Path
from pypdf import PdfReader

def test_midterm_v1_pdfs():
    base = Path("중간고사대비/v1")
    prob_pdf = base / "중간고사대비_v1-문제.pdf"
    ans_pdf = base / "중간고사대비_v1-답안.pdf"
    assert prob_pdf.is_file()
    assert ans_pdf.is_file()

    reader_p = PdfReader(prob_pdf)
    assert len(reader_p.pages) >= 5
    # 16:9 와이드스크린 비율 검증 (1920x1080 approx ratio 1.77)
    box = reader_p.pages[0].mediabox
    ratio = float(box.width) / float(box.height)
    assert 1.7 <= ratio <= 1.85
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_midterm_v1_pdf.py -v`
Expected: FAIL with missing pdf files

- [ ] **Step 3: Implement PDF generator and render 16:9 PDFs**

- `build_exam_pdf.py`: Task 1, 2, 4 자원을 취합하여 `workbook/render.py` 및 `workbook/templates/video-16x9.css`를 사용하여 문제지와 답안지 HTML 생성 후 Playwright로 16:9 PDF 출력.
- overflow 검증을 거쳐 문항 분할 및 레이아웃 조정.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_midterm_v1_pdf.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add 중간고사대비/v1/*.py 중간고사대비/v1/*.pdf tests/test_midterm_v1_pdf.py
git commit -m "feat(midterm): render 16:9 widescreen exam problem and answer PDFs"
```

---

### Task 6: 7구역 대화형 문제해설 HTML 저작 및 최종 검증

**Files:**
- Create: `중간고사대비/v1/문제해설_중간고사대비_v1.html`
- Test: `tests/test_midterm_v1_html.py`

**Interfaces:**
- Consumes: Task 2 md 풀이, Task 3 검산 결과, Task 4 회로도
- Produces: Pretendard, KaTeX, 라이트/다크 테마, 7구역(understand $\to$ retry) 대화형 문제해설 단일 독립 HTML

- [ ] **Step 1: Write the failing test**

```python
# tests/test_midterm_v1_html.py
from pathlib import Path
from bs4 import BeautifulSoup

def test_midterm_v1_explanation_html():
    html_path = Path("중간고사대비/v1/문제해설_중간고사대비_v1.html")
    assert html_path.is_file()
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")

    # 5개 문항 topic section 존재 확인
    topics = soup.find_all("section", class_="topic")
    assert len(topics) == 5

    # 7개 레이어 키워드 확인
    required_layers = [
        "문제를 읽어요",
        "이 개념과 공식을 떠올려요",
        "종이에 쓸 첫 줄",
        "이렇게 풀어요",
        "완성 답과 검산",
        "주의할 점",
        "조건을 바꾸어 생각해요"
    ]
    first_topic_text = topics[0].get_text()
    for layer in required_layers:
        assert layer in first_topic_text or any(layer in t.get_text() for t in topics)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_midterm_v1_html.py -v`
Expected: FAIL with missing HTML

- [ ] **Step 3: Implement 7-stage explanation HTML**

`문제해설_중간고사대비_v1.html` 작성:
- 상단 고정 헤더(진행률 바, 라이트/다크 테마 토글 버튼, 문항 바로가기 nav).
- Pretendard 글꼴 및 KaTeX 수식 인라인/디스플레이 스타일링.
- 5개 문항별 일곱 구역(`<div class="layer">`) 체계적인 배치 및 고화질 SVG 인라인/참조 결합.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_midterm_v1_html.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add 중간고사대비/v1/문제해설_중간고사대비_v1.html tests/test_midterm_v1_html.py
git commit -m "feat(midterm): complete 7-stage interactive explanation HTML"
```
